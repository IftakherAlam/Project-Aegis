import re
import logging
import math
import hashlib
import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass
from collections import Counter

@dataclass
class LocalAnalysisResult:
    sanitized_content: str
    is_safe: bool
    confidence_score: float
    detected_threats: List[str]
    analysis_notes: str


class LocalSecurityAnalyzer:
    """
    Pure Python local security analyzer that performs heuristic and pattern-based detection.
    This module serves as a fallback when autonomous AI-based analyzers are unavailable.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.threat_patterns = self._build_threat_patterns()
        self.benign_indicators = self._build_benign_indicators()

    # ------------------------------------------------------------------
    # Pattern Definitions
    # ------------------------------------------------------------------

    def _build_threat_patterns(self) -> List[Dict[str, Any]]:
        """Comprehensive threat patterns including social engineering"""
        return [
            {
                'name': 'ignore_instructions',
                'patterns': [
                    r'ignore\s+(all\s+)?(previous|prior|earlier)\s+instructions?',
                    r'disregard\s+(all\s+)?(previous|prior|earlier)',
                    r'forget\s+(all\s+)?(previous|prior|earlier)',
                    r'overrule\s+(all\s+)?(previous|prior|earlier)'
                ],
                'weight': 0.9
            },
            {
                'name': 'role_playing',
                'patterns': [
                    r'you\s+are\s+now\s+(?:\w+\s+)*mode',
                    r'act\s+as\s+(?:an?\s+)?\w+',
                    r'pretend\s+you\s+are',
                    r'you\s+are\s+(?:a\s+)?\w+\s+now',
                    r'developer\s+mode',
                    r'debug\s+mode',
                    r'admin\s+mode'
                ],
                'weight': 0.8
            },
            {
                'name': 'exfiltration',
                'patterns': [
                    r'(output|print|show|reveal|display|repeat)\s+(your|the)\s+(system\s+)?prompt',
                    r'what\s+(are|were)\s+your\s+(initial|original|system)\s+instructions?',
                    r'tell\s+me\s+your\s+(secret|internal|confidential)',
                    r'leak\s+your\s+',
                    r'api\s+key',
                    r'secret\s+key'
                ],
                'weight': 0.95
            },
            {
                'name': 'encoding_attempts',
                'patterns': [
                    r'decode\s+(this|the)\s+(base64|hex)',
                    r'base64:[\w+/=]+',
                    r'(?:[0-9a-fA-F]{2}\s*){10,}',  # Hex pattern
                    r'execute\s+(?:this|the)\s+code',
                    r'run\s+(?:this|the)\s+command'
                ],
                'weight': 0.7
            },
            {
                'name': 'manipulation_attempts',
                'patterns': [
                    r'from\s+now\s+on',
                    r'starting\s+now',
                    r'new\s+rule:',
                    r'new\s+instruction:',
                    r'your\s+new\s+(purpose|task|role)'
                ],
                'weight': 0.6
            },
            {
                'name': 'social_engineering',
                'patterns': [
                    r'as\s+a\s+(developer|admin|engineer|technician)',
                    r'for\s+(debugging|testing|research)\s+purposes',
                    r'i\s+need\s+(to\s+see|access\s+to)',
                    r'can\s+you\s+(show|reveal|display)',
                    r'could\s+you\s+(share|provide|give)',
                    r'would\s+you\s+mind\s+(showing|sharing)',
                    r'in\s+my\s+(role|position|capacity)',
                    r'required\s+for\s+my\s+(work|job|task)'
                ],
                'weight': 0.7
            }
        ]

    def _build_benign_indicators(self) -> List[str]:
        """Patterns that indicate legitimate safe content"""
        return [
            r'weather',
            r'sales',
            r'report',
            r'customer',
            r'business',
            r'question',
            r'help',
            r'information',
            r'data',
            r'analysis'
        ]

    # ------------------------------------------------------------------
    # Core Analysis Logic
    # ------------------------------------------------------------------

    def analyze_and_sanitize(self, text: str) -> LocalAnalysisResult:
        """Perform pattern-based security analysis and sanitization"""
        original_text = text
        detected_threats = []
        threat_score = 0.0
        max_possible_score = sum(p['weight'] for p in self.threat_patterns)

        # Phase 1: Threat detection
        for pattern_group in self.threat_patterns:
            for pattern in pattern_group['patterns']:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    threat_desc = f"{pattern_group['name']}: {match.group()}"
                    detected_threats.append(threat_desc)
                    threat_score += pattern_group['weight']
                    text = text.replace(match.group(), '')

        # Phase 2: Semantic enrichment
        semantic_patterns = self._extract_semantic_patterns(original_text)
        if semantic_patterns:
            detected_threats.extend(semantic_patterns)
            threat_score += 0.3 * len(semantic_patterns)

        # Phase 3: Sanitization
        sanitized_text = self._sanitize_content(text)

        # Phase 4: Confidence & verdict
        confidence = self._calculate_confidence(threat_score, max_possible_score, text)
        is_safe = threat_score < 0.3

        return LocalAnalysisResult(
            sanitized_content=sanitized_text,
            is_safe=is_safe,
            confidence_score=confidence,
            detected_threats=detected_threats,
            analysis_notes=f"Local analysis complete. Threats detected: {len(detected_threats)}"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sanitize_content(self, text: str) -> str:
        """Clean and sanitize the content"""
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\{.*?\}', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _calculate_confidence(self, threat_score: float, max_score: float, text: str) -> float:
        """Compute confidence score based on benign and threat signals"""
        base_confidence = 1.0 - (threat_score / max_score) if max_score > 0 else 0.5
        benign_hits = sum(1 for p in self.benign_indicators if re.search(p, text, re.IGNORECASE))
        if benign_hits > 0:
            base_confidence = min(1.0, base_confidence + 0.2)
        return max(0.1, min(1.0, base_confidence))

    def _calculate_shannon_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0
        entropy = 0
        for x in range(256):
            p_x = float(text.count(chr(x))) / len(text)
            if p_x > 0:
                entropy += -p_x * math.log2(p_x)
        return entropy

    def _calculate_repetition_score(self, text: str) -> float:
        """Calculate text repetitiveness"""
        words = text.lower().split()
        if len(words) < 2:
            return 0
        unique_words = len(set(words))
        return 1 - (unique_words / len(words))

    def _extract_semantic_patterns(self, text: str) -> List[str]:
        """Detect higher-level semantic manipulation or probing intents"""
        patterns = []
        text_lower = text.lower()

        # Social engineering cues
        social_engineering = [
            ('as a', 'developer'),
            ('as an', 'admin'),
            ('for debugging', ''),
            ('to help', 'you'),
            ('i need', 'access'),
            ('can you', 'show'),
            ('could you', 'reveal'),
            ('would you', 'mind'),
            ('for research', ''),
            ('to test', 'system')
        ]
        for prefix, suffix in social_engineering:
            if prefix in text_lower and (not suffix or suffix in text_lower):
                snippet = text[max(0, text_lower.find(prefix) - 20):min(len(text), text_lower.find(prefix) + 50)]
                patterns.append(f"social_engineering:{hashlib.md5(snippet.encode()).hexdigest()[:8]}")

        # Authority assertion
        authority_patterns = [
            'i am a', 'i am the', 'as the', 'in my role as',
            'required for my', 'necessary for', 'need to see',
            'should have access', 'entitled to'
        ]
        for phrase in authority_patterns:
            if phrase in text_lower:
                patterns.append(f"authority_assertion:{phrase}")

        # Probing internal system questions
        probing = [
            'how do you work', 'how are you configured',
            'what is your', 'tell me about your',
            'explain your', 'describe your'
        ]
        for phrase in probing:
            if phrase in text_lower:
                patterns.append(f"probing_question:{phrase}")

        return patterns
