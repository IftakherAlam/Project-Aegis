# src/core/security_proxy.py - UPDATED VERSION
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
import asyncio
from .rule_engine import RuleEngine

@dataclass
class SecurityResult:
    content: str
    is_safe: bool
    confidence_score: float
    detected_threats: List[str]
    sanitized_content: str
    analyzer_used: str = "legacy"
    learning_metadata: Dict[str, Any] = None

class AegisSecurityProxy:
    """
    Main security proxy now with autonomous learning capabilities
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.rule_engine = RuleEngine(config)
        
        # Initialize autonomous integration
        from .autonomous_integration import AutonomousIntegrationManager
        self.autonomous_manager = AutonomousIntegrationManager(config)
        
        # Track usage for learning
        self.analysis_count = 0
        
    async def process_input(self, raw_input: str, source_type: str) -> SecurityResult:
        """
        Main entry point with autonomous learning capabilities
        """
        self.analysis_count += 1
        self.logger.info(f"Processing input from {source_type} (request #{self.analysis_count})")
        
        # Layer 1: Rule-based pre-filtering (always fast and free)
        rule_result = self.rule_engine.analyze(raw_input)
        if not rule_result.is_safe:
            self.logger.warning(f"Rule engine blocked input: {rule_result.detected_threats}")
            return SecurityResult(
                content=raw_input,
                is_safe=False,
                confidence_score=0.0,
                detected_threats=rule_result.detected_threats,
                sanitized_content="[BLOCKED BY RULE ENGINE]",
                analyzer_used="rule_engine"
            )
        
        # Layer 2: Autonomous analysis with gradual rollout
        user_context = {"source_type": source_type, "request_id": self.analysis_count}
        autonomous_result = await self.autonomous_manager.process_with_gradual_rollout(
            raw_input, user_context
        )
        
        # Convert to SecurityResult
        return SecurityResult(
            content=raw_input,
            is_safe=autonomous_result['is_safe'],
            confidence_score=autonomous_result['confidence'],
            detected_threats=autonomous_result.get('detected_threats', []),
            sanitized_content=autonomous_result.get('sanitized_content', raw_input),
            analyzer_used=autonomous_result.get('analyzer_used', 'unknown'),
            learning_metadata=autonomous_result.get('learning_metadata', {})
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and learning progress"""
        rollout_status = self.autonomous_manager.get_rollout_status()
        
        return {
            "total_analyses": self.analysis_count,
            "autonomous_rollout": rollout_status,
            "system_health": "optimal",
            "learning_active": True
        }
    
    def set_autonomous_percentage(self, percentage: float):
        """Control autonomous system rollout"""
        self.autonomous_manager.set_autonomous_percentage(percentage)
    
    def enable_autonomous_feature(self, feature_name: str):
        """Enable specific autonomous features"""
        self.autonomous_manager.enable_feature(feature_name)