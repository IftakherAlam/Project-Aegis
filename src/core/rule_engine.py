# src/core/rule_engine.py
import re
import yaml
from typing import Dict, Any, List, Pattern
from dataclasses import dataclass
import logging

@dataclass
class RuleResult:
    is_safe: bool
    detected_threats: List[str]
    risk_level: str  # "low", "medium", "high"

class RuleEngine:
    """
    Rule-based security analyzer for fast, deterministic threat detection
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.rules = self._load_rules()
        self.compiled_patterns = self._compile_patterns()
        
    def _load_rules(self) -> Dict[str, Any]:
        """Load security rules from configuration"""
        # Load rules from config if available
        if 'rule_engine' in self.config and 'rules' in self.config['rule_engine']:
            return {'rules': self.config['rule_engine']['rules']}
        
        # Fallback to hardcoded rules
        return {
            'rules': [
                {
                    'name': 'ignore_previous_patterns',
                    'patterns': [
                        r'ignore\s+(your\s+)?previous\s+instructions?',
                        r'disregard\s+earlier',
                        r'forget\s+prior'
                    ]
                },
                {
                    'name': 'role_playing', 
                    'patterns': [
                        r'you\s+are\s+now\s+(a|in|operating)',
                        r'developer\s+mode',
                        r'admin\s+mode'
                    ]
                },
                {
                    'name': 'exfiltration',
                    'patterns': [
                        r'(output|print|show|reveal|display)\s+(your|the)\s+system\s+prompt',
                        r'what\s+(are|were)\s+your\s+(initial|original)\s+instructions',
                        r'API key'
                    ]
                },
                {
                    'name': 'direct_injection',
                    'patterns': [
                        r'ignore\s+all\s+prior',
                        r'disregard\s+all\s+previous'
                    ]
                },
                {
                    'name': 'encoding_attempts',
                    'patterns': [
                        r'[0-9a-fA-F]{20,}',
                        r'base64',
                        r'decode\s+this'
                    ]
                },
                {
                    'name': 'probing_question',
                    'patterns': [
                        r'tell me about your'
                    ]
                }
            ]
        }
    
    def _compile_patterns(self) -> List[Pattern]:
        """Compile regex patterns for efficient matching"""
        patterns = []
        for rule in self.rules['rules']:
            for pattern in rule.get('patterns', []):
                try:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    patterns.append((compiled, rule['name']))
                except re.error as e:
                    self.logger.warning(f"Failed to compile pattern {pattern}: {e}")
                    continue
        return patterns
    
    def analyze(self, text: str) -> RuleResult:
        """Analyze text against all security rules"""
        detected_threats = []
        
        # Check each pattern
        for pattern, rule_name in self.compiled_patterns:
            if pattern.search(text):
                detected_threats.append(f"{rule_name}: {pattern.pattern}")
        
        # Determine risk level
        risk_level = self._calculate_risk_level(detected_threats)
        
        return RuleResult(
            is_safe=len(detected_threats) == 0,
            detected_threats=detected_threats,
            risk_level=risk_level
        )
    
    def _calculate_risk_level(self, threats: List[str]) -> str:
        """Calculate overall risk level based on detected threats"""
        if not threats:
            return "low"
        
        high_risk_indicators = ["exfiltration", "ignore", "system", "prompt"]
        medium_risk_indicators = ["encoding", "role", "developer"]
        
        for threat in threats:
            if any(indicator in threat.lower() for indicator in high_risk_indicators):
                return "high"
            if any(indicator in threat.lower() for indicator in medium_risk_indicators):
                return "medium"
        
        return "low"