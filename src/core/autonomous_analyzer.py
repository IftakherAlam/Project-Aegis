# src/core/autonomous_analyzer.py
import json
import pickle
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple
import hashlib
from dataclasses import dataclass, asdict
import sqlite3
import logging

@dataclass
class LearningMetrics:
    total_analyzed: int = 0
    threats_detected: int = 0
    false_positives: int = 0
    new_patterns_learned: int = 0
    confidence_improvement: float = 0.0
    last_learning_cycle: datetime = None

class AutonomousSecurityAnalyzer:
    """
    Self-learning security system that continuously improves from real-world data
    """
    
    def __init__(self, knowledge_base_path: str = "knowledge_base.db"):
        self.knowledge_base_path = knowledge_base_path
        self.learning_metrics = LearningMetrics()
        self.pattern_weights = defaultdict(float)
        self.behavioral_profiles = {}
        self.threat_intelligence = self._load_knowledge_base()
        
        # Learning parameters
        self.learning_rate = 0.1
        self.pattern_decay = 0.99  # Forget unused patterns slowly
        self.confidence_threshold = 0.7
        self.min_pattern_occurrence = 3
        
        # Initialize with baseline knowledge
        self._initialize_baseline_knowledge()
        
    def _initialize_baseline_knowledge(self):
        """Start with fundamental security patterns"""
        baseline_patterns = {
            "ignore_previous": 0.9,
            "disregard_instructions": 0.85,
            "developer_mode": 0.8,
            "output_system_prompt": 0.95,
            "role_playing": 0.75,
            "encoding_attempts": 0.7
        }
        self.pattern_weights.update(baseline_patterns)
        
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load existing knowledge from persistent storage"""
        try:
            conn = sqlite3.connect(self.knowledge_base_path)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS threat_patterns (
                    pattern_hash TEXT PRIMARY KEY,
                    pattern_text TEXT,
                    weight REAL,
                    occurrences INTEGER,
                    first_seen TIMESTAMP,
                    last_seen TIMESTAMP,
                    confirmed_malicious INTEGER
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_metrics (
                    date TEXT PRIMARY KEY,
                    total_analyzed INTEGER,
                    threats_detected INTEGER,
                    false_positives INTEGER,
                    accuracy REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS behavioral_patterns (
                    user_hash TEXT,
                    pattern_type TEXT,
                    risk_score REAL,
                    first_observed TIMESTAMP,
                    last_observed TIMESTAMP,
                    PRIMARY KEY (user_hash, pattern_type)
                )
            ''')
            
            conn.commit()
            
            # Load existing patterns
            cursor.execute("SELECT pattern_text, weight FROM threat_patterns")
            patterns = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            return {"patterns": patterns}
            
        except Exception as e:
            logging.warning(f"Could not load knowledge base: {e}")
            return {"patterns": {}}
    
    def _save_knowledge_base(self):
        """Persist learned knowledge"""
        try:
            conn = sqlite3.connect(self.knowledge_base_path)
            cursor = conn.cursor()
            
            # Save threat patterns
            for pattern, weight in self.pattern_weights.items():
                pattern_hash = hashlib.md5(pattern.encode()).hexdigest()
                cursor.execute('''
                    INSERT OR REPLACE INTO threat_patterns 
                    (pattern_hash, pattern_text, weight, occurrences, last_seen)
                    VALUES (?, ?, ?, COALESCE((SELECT occurrences FROM threat_patterns WHERE pattern_hash = ?), 0) + 1, ?)
                ''', (pattern_hash, pattern, weight, pattern_hash, datetime.now()))
            
            # Save learning metrics
            today = datetime.now().date().isoformat()
            accuracy = (self.learning_metrics.threats_detected / 
                       max(self.learning_metrics.total_analyzed, 1))
            
            cursor.execute('''
                INSERT OR REPLACE INTO learning_metrics 
                (date, total_analyzed, threats_detected, false_positives, accuracy)
                VALUES (?, ?, ?, ?, ?)
            ''', (today, self.learning_metrics.total_analyzed, 
                  self.learning_metrics.threats_detected, 
                  self.learning_metrics.false_positives, accuracy))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to save knowledge base: {e}")
    
    def analyze_and_learn(self, text: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze text for threats while simultaneously learning from it
        """
        self.learning_metrics.total_analyzed += 1
        
        # Extract features and patterns
        features = self._extract_detailed_features(text)
        patterns = self._extract_patterns(text)
        
        # Calculate threat score using current knowledge
        threat_score = self._calculate_threat_score(patterns, features, user_context)
        
        # Determine if content is safe
        is_safe = threat_score < self.confidence_threshold
        
        # Learn from this analysis
        self._learn_from_analysis(text, patterns, features, threat_score, user_context)
        
        # Update pattern weights based on this interaction
        self._update_pattern_weights(patterns, threat_score)
        
        # Periodic knowledge base saving
        if self.learning_metrics.total_analyzed % 100 == 0:
            self._save_knowledge_base()
            self._prune_ineffective_patterns()
        
        return {
            "is_safe": is_safe,
            "threat_score": threat_score,
            "detected_patterns": patterns,
            "confidence": min(0.99, threat_score * 1.2),  # Calibrated confidence
            "learned_new_patterns": self.learning_metrics.new_patterns_learned
        }
    
    def _extract_detailed_features(self, text: str) -> Dict[str, Any]:
        """Extract comprehensive features for analysis and learning"""
        words = text.lower().split()
        word_count = len(words)
        
        return {
            "length": len(text),
            "word_count": word_count,
            "avg_word_length": sum(len(word) for word in words) / word_count if word_count > 0 else 0,
            "question_density": text.count('?') / max(word_count, 1),
            "exclamation_density": text.count('!') / max(word_count, 1),
            "uppercase_ratio": sum(1 for c in text if c.isupper()) / len(text),
            "special_char_ratio": sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text),
            "entropy": self._calculate_shannon_entropy(text),
            "repetition_score": self._calculate_repetition_score(text),
            "url_count": len([word for word in words if word.startswith(('http://', 'https://'))]),
            "suspicious_sequences": self._find_suspicious_sequences(text)
        }
    
    def _extract_patterns(self, text: str) -> List[Tuple[str, float]]:
        """Extract potential threat patterns from text"""
        patterns = []
        words = text.lower().split()
        
        # N-gram patterns (1, 2, 3 words)
        for n in range(1, 4):
            for i in range(len(words) - n + 1):
                ngram = ' '.join(words[i:i+n])
                if self._is_meaningful_pattern(ngram):
                    patterns.append(ngram)
        
        # Semantic patterns
        semantic_patterns = self._extract_semantic_patterns(text)
        patterns.extend(semantic_patterns)
        
        # Structural patterns
        structural_patterns = self._extract_structural_patterns(text)
        patterns.extend(structural_patterns)
        
        return [(p, self.pattern_weights.get(p, 0.5)) for p in patterns]
    
    def _extract_semantic_patterns(self, text: str) -> List[str]:
        """Extract semantic patterns that might indicate threats"""
        patterns = []
        
        # Instruction-like phrases
        instruction_indicators = ['please', 'could you', 'can you', 'would you', 'I need you to']
        for indicator in instruction_indicators:
            if indicator in text.lower():
                # Extract the context around the instruction
                start = text.lower().find(indicator)
                context = text[max(0, start-20):min(len(text), start+50)]
                patterns.append(f"instruction_context:{hashlib.md5(context.encode()).hexdigest()[:8]}")
        
        # Role-playing indicators
        role_indicators = ['you are', 'act as', 'pretend you', 'you are now']
        for indicator in role_indicators:
            if indicator in text.lower():
                patterns.append(f"role_assertion:{indicator}")
        
        return patterns
    
    def _extract_structural_patterns(self, text: str) -> List[str]:
        """Extract structural patterns that might indicate attacks"""
        patterns = []
        
        # Encoding patterns
        if any(encoding in text.lower() for encoding in ['base64', 'decode this', 'hex:']):
            patterns.append("encoding_mention")
        
        # System reference patterns
        if any(ref in text.lower() for ref in ['system', 'prompt', 'instruction', 'configuration']):
            patterns.append("system_reference")
        
        # Urgency patterns
        if any(urgent in text.lower() for urgent in ['urgent', 'immediately', 'asap', 'important']):
            patterns.append("urgency_indicator")
        
        return patterns
    
    def _calculate_threat_score(self, patterns: List[Tuple[str, float]], 
                              features: Dict[str, Any], 
                              user_context: Dict[str, Any] = None) -> float:
        """Calculate comprehensive threat score using learned knowledge"""
        
        # Pattern-based scoring
        pattern_score = sum(weight for _, weight in patterns) / max(len(patterns), 1)
        
        # Feature-based scoring
        feature_score = self._calculate_feature_based_score(features)
        
        # Behavioral scoring (if user context available)
        behavioral_score = 0.0
        if user_context and 'user_id' in user_context:
            behavioral_score = self._get_behavioral_risk(user_context['user_id'])
        
        # Combine scores with learned weights
        combined_score = (
            pattern_score * 0.6 + 
            feature_score * 0.3 + 
            behavioral_score * 0.1
        )
        
        return min(1.0, combined_score)
    
    def _calculate_feature_based_score(self, features: Dict[str, Any]) -> float:
        """Calculate threat score based on textual features"""
        score = 0.0
        
        # High entropy might indicate encoded content
        if features["entropy"] > 4.0:
            score += 0.3
        
        # Unusual punctuation patterns
        if features["special_char_ratio"] > 0.2:
            score += 0.2
        
        # Very short or very long messages can be suspicious
        if features["length"] < 10 or features["length"] > 1000:
            score += 0.1
        
        # High question density might indicate probing
        if features["question_density"] > 0.3:
            score += 0.2
        
        # Repetition can indicate automated attacks
        if features["repetition_score"] > 0.8:
            score += 0.2
        
        return min(1.0, score)
    
    def _learn_from_analysis(self, text: str, patterns: List[Tuple[str, float]], 
                           features: Dict[str, Any], threat_score: float,
                           user_context: Dict[str, Any] = None):
        """Learn from the current analysis to improve future detection"""
        
        # If we have high confidence in threat detection, reinforce patterns
        if threat_score > 0.8:
            self.learning_metrics.threats_detected += 1
            self._reinforce_patterns(patterns, threat_score)
            
            # Extract new patterns from confirmed threats
            new_patterns = self._extract_novel_patterns(text)
            for pattern in new_patterns:
                if pattern not in self.pattern_weights:
                    self.pattern_weights[pattern] = 0.7  # Initial medium confidence
                    self.learning_metrics.new_patterns_learned += 1
        
        # If we have medium confidence, do cautious learning
        elif threat_score > 0.4:
            self._cautious_learning(patterns, threat_score)
        
        # Update behavioral profiles
        if user_context and 'user_id' in user_context:
            self._update_behavioral_profile(user_context['user_id'], patterns, threat_score)
    
    def _reinforce_patterns(self, patterns: List[Tuple[str, float]], threat_score: float):
        """Strengthen patterns associated with confirmed threats"""
        for pattern, current_weight in patterns:
            # Increase weight based on threat confidence
            weight_increase = self.learning_rate * threat_score
            new_weight = min(1.0, current_weight + weight_increase)
            self.pattern_weights[pattern] = new_weight
    
    def _cautious_learning(self, patterns: List[Tuple[str, float]], threat_score: float):
        """Learn cautiously from uncertain cases"""
        for pattern, current_weight in patterns:
            # Small adjustment for uncertain cases
            adjustment = self.learning_rate * 0.3 * (threat_score - 0.5)
            new_weight = max(0.1, min(1.0, current_weight + adjustment))
            self.pattern_weights[pattern] = new_weight
    
    def _extract_novel_patterns(self, text: str) -> List[str]:
        """Extract patterns we haven't seen before that might be threats"""
        novel_patterns = []
        words = text.lower().split()
        
        # Look for unusual word combinations
        for i in range(len(words) - 2):
            trigram = ' '.join(words[i:i+3])
            if (trigram not in self.pattern_weights and 
                self._is_potentially_malicious(trigram)):
                novel_patterns.append(trigram)
        
        return novel_patterns
    
    def _is_potentially_malicious(self, pattern: str) -> bool:
        """Heuristic to determine if a pattern might be malicious"""
        malicious_indicators = [
            'ignore', 'disregard', 'override', 'bypass', 'hack',
            'secret', 'confidential', 'system', 'prompt', 'instruction',
            'developer', 'admin', 'root', 'privilege', 'access'
        ]
        
        return any(indicator in pattern for indicator in malicious_indicators)
    
    def _update_behavioral_profile(self, user_id: str, patterns: List[Tuple[str, float]], 
                                 threat_score: float):
        """Update user behavioral profile based on current interaction"""
        if user_id not in self.behavioral_profiles:
            self.behavioral_profiles[user_id] = {
                'total_interactions': 0,
                'high_risk_interactions': 0,
                'pattern_frequency': Counter(),
                'risk_trend': [],
                'first_seen': datetime.now(),
                'last_seen': datetime.now()
            }
        
        profile = self.behavioral_profiles[user_id]
        profile['total_interactions'] += 1
        profile['last_seen'] = datetime.now()
        
        if threat_score > 0.7:
            profile['high_risk_interactions'] += 1
        
        # Update pattern frequency
        for pattern, _ in patterns:
            profile['pattern_frequency'][pattern] += 1
        
        # Maintain risk trend (last 10 interactions)
        profile['risk_trend'].append(threat_score)
        if len(profile['risk_trend']) > 10:
            profile['risk_trend'].pop(0)
    
    def _get_behavioral_risk(self, user_id: str) -> float:
        """Calculate behavioral risk score for a user"""
        if user_id not in self.behavioral_profiles:
            return 0.3  # Default medium risk for new users
        
        profile = self.behavioral_profiles[user_id]
        
        if profile['total_interactions'] < 3:
            return 0.3  # Not enough data
        
        # Calculate risk based on behavior
        high_risk_ratio = profile['high_risk_interactions'] / profile['total_interactions']
        
        # Recent risk trend (weight recent interactions more heavily)
        if profile['risk_trend']:
            recent_risk = sum(profile['risk_trend'][-3:]) / min(3, len(profile['risk_trend']))
        else:
            recent_risk = 0.3
        
        # Combined behavioral risk
        behavioral_risk = (high_risk_ratio * 0.6) + (recent_risk * 0.4)
        
        return min(1.0, behavioral_risk)
    
    def _prune_ineffective_patterns(self):
        """Remove patterns that haven't been effective"""
        patterns_to_remove = []
        
        for pattern, weight in self.pattern_weights.items():
            # Decay unused patterns
            if weight < 0.2:
                patterns_to_remove.append(pattern)
            else:
                # Apply gradual decay to all patterns
                self.pattern_weights[pattern] *= self.pattern_decay
        
        for pattern in patterns_to_remove:
            del self.pattern_weights[pattern]
    
    def get_learning_report(self) -> Dict[str, Any]:
        """Generate report on system learning progress"""
        total_patterns = len(self.pattern_weights)
        avg_confidence = sum(self.pattern_weights.values()) / max(total_patterns, 1)
        
        return {
            "total_patterns_learned": total_patterns,
            "average_pattern_confidence": avg_confidence,
            "total_analyzed": self.learning_metrics.total_analyzed,
            "threats_detected": self.learning_metrics.threats_detected,
            "detection_rate": self.learning_metrics.threats_detected / max(self.learning_metrics.total_analyzed, 1),
            "new_patterns_learned": self.learning_metrics.new_patterns_learned,
            "behavioral_profiles_tracked": len(self.behavioral_profiles)
        }
    
    # Utility methods
    def _calculate_shannon_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0
        entropy = 0
        for x in range(256):
            p_x = float(text.count(chr(x))) / len(text)
            if p_x > 0:
                entropy += - p_x * np.log2(p_x)
        return entropy
    
    def _calculate_repetition_score(self, text: str) -> float:
        """Calculate repetition score (higher = more repetitive)"""
        words = text.lower().split()
        if len(words) < 2:
            return 0
        unique_words = len(set(words))
        return 1 - (unique_words / len(words))
    
    def _find_suspicious_sequences(self, text: str) -> List[str]:
        """Find potentially suspicious character sequences"""
        suspicious = []
        # Look for encoded-like patterns
        if re.search(r'[A-Za-z0-9+/]{20,}={0,2}', text):  # Base64-like
            suspicious.append("base64_like_sequence")
        if re.search(r'(0x)?[0-9a-fA-F]{8,}', text):  # Hex-like
            suspicious.append("hex_like_sequence")
        return suspicious
    
    def _is_meaningful_pattern(self, ngram: str) -> bool:
        """Determine if an n-gram is meaningful for pattern learning"""
        # Filter out very common words alone
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = ngram.split()
        if len(words) == 1 and words[0] in common_words:
            return False
        return len(ngram) > 2  # Minimum meaningful length