# src/core/autonomous_integration.py - UPDATED
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
import json

try:
    from .autonomous_security_system import AutonomousSecuritySystem
except ImportError:
    # Fallback if autonomous system isn't available
    AutonomousSecuritySystem = None

try:
    from .local_analyzer import LocalSecurityAnalyzer
except ImportError:
    # Create a minimal fallback
    class LocalSecurityAnalyzer:
        def analyze_and_sanitize(self, text):
            from dataclasses import dataclass
            @dataclass
            class Result:
                is_safe: bool = True
                confidence_score: float = 0.5
                detected_threats: List[str] = None
                sanitized_content: str = ""
            
            return Result(
                is_safe=True,
                confidence_score=0.5,
                detected_threats=[],
                sanitized_content=text
            )

class AutonomousIntegrationManager:
    """
    Manages the integration between existing system and new autonomous components
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize systems with fallbacks
        self.legacy_analyzer = LocalSecurityAnalyzer()
        
        if AutonomousSecuritySystem:
            self.autonomous_system = AutonomousSecuritySystem()
            self.autonomous_available = True
        else:
            self.autonomous_system = None
            self.autonomous_available = False
            self.logger.warning("Autonomous system not available - using legacy only")
        
        # Rollout parameters
        self.autonomous_traffic_percentage = 0.1 if self.autonomous_available else 0.0
        self.performance_threshold = 0.8
        self.performance_metrics = {
            'autonomous_calls': 0,
            'legacy_calls': 0,
            'autonomous_success': 0,
            'legacy_success': 0,
            'false_positives': 0,
            'threats_missed': 0
        }
        
    async def process_with_gradual_rollout(self, text: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process input using gradual rollout of autonomous system
        """
        # If autonomous system not available, always use legacy
        if not self.autonomous_available:
            return await self._fallback_to_legacy(text, user_context)
        
        # Decide which system to use
        use_autonomous = self._should_use_autonomous_system()
        
        if use_autonomous:
            self.performance_metrics['autonomous_calls'] += 1
            try:
                result = await self.autonomous_system.process_input(text, user_context)
                
                # Validate autonomous result with legacy system
                legacy_result = self.legacy_analyzer.analyze_and_sanitize(text)
                
                # Track performance
                if self._results_agree(result, legacy_result):
                    self.performance_metrics['autonomous_success'] += 1
                else:
                    self._handle_disagreement(result, legacy_result, text)
                
                return result
                
            except Exception as e:
                self.logger.error(f"Autonomous system failed: {e}")
                return await self._fallback_to_legacy(text, user_context)
        else:
            self.performance_metrics['legacy_calls'] += 1
            return await self._fallback_to_legacy(text, user_context)
    
    def _should_use_autonomous_system(self) -> bool:
        """Determine if we should use autonomous system for this request"""
        if not self.autonomous_available:
            return False
            
        # Simple percentage-based rollout
        import random
        if random.random() < self.autonomous_traffic_percentage:
            return True
        
        # Gradually increase rollout based on performance
        if self._calculate_autonomous_performance() > self.performance_threshold:
            self.autonomous_traffic_percentage = min(1.0, self.autonomous_traffic_percentage + 0.05)
            self.logger.info(f"Increased autonomous rollout to {self.autonomous_traffic_percentage:.0%}")
        
        return False
    
    def _calculate_autonomous_performance(self) -> float:
        """Calculate autonomous system performance"""
        total_calls = self.performance_metrics['autonomous_calls']
        if total_calls == 0:
            return 0.0
        
        success_rate = self.performance_metrics['autonomous_success'] / total_calls
        return success_rate
    
    def _results_agree(self, autonomous_result: Dict, legacy_result: Any) -> bool:
        """Check if both systems agree on the security assessment"""
        autonomous_safe = autonomous_result.get('is_safe', True)
        legacy_safe = legacy_result.is_safe if hasattr(legacy_result, 'is_safe') else True
        
        return autonomous_safe == legacy_safe
    
    def _handle_disagreement(self, autonomous_result: Dict, legacy_result: Any, text: str):
        """Handle cases where systems disagree"""
        self.logger.warning("System disagreement detected")
        
        # For now, trust legacy system for safety
        legacy_safe = legacy_result.is_safe if hasattr(legacy_result, 'is_safe') else True
        if legacy_safe != autonomous_result.get('is_safe', True):
            self.performance_metrics['false_positives'] += 1
    
    async def _fallback_to_legacy(self, text: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback to legacy analysis"""
        legacy_result = self.legacy_analyzer.analyze_and_sanitize(text)
        
        return {
            'is_safe': getattr(legacy_result, 'is_safe', True),
            'threat_score': 1.0 - getattr(legacy_result, 'confidence_score', 0.5),
            'confidence': getattr(legacy_result, 'confidence_score', 0.5),
            'detected_threats': getattr(legacy_result, 'detected_threats', []),
            'sanitized_content': getattr(legacy_result, 'sanitized_content', text),
            'analyzer_used': 'legacy',
            'learning_metadata': {}
        }
    
    def get_rollout_status(self) -> Dict[str, Any]:
        """Get current rollout status and metrics"""
        return {
            'autonomous_available': self.autonomous_available,
            'autonomous_traffic_percentage': self.autonomous_traffic_percentage,
            'performance_metrics': self.performance_metrics,
            'autonomous_performance': self._calculate_autonomous_performance(),
            'total_requests': (self.performance_metrics['autonomous_calls'] + 
                             self.performance_metrics['legacy_calls'])
        }
    
    def set_autonomous_percentage(self, percentage: float):
        """Manually set autonomous traffic percentage"""
        if self.autonomous_available:
            self.autonomous_traffic_percentage = max(0.0, min(1.0, percentage))
            self.logger.info(f"Set autonomous traffic to {percentage:.0%}")
            
            
            
    def get_system_status(self) -> Dict[str, Any]:
        """
        Return system-wide status for admin dashboard.
        Includes rollout info, performance, feature flags, and learning progress.
        """
        try:
            rollout = self.get_rollout_status()

            # Gather performance metrics (safe default if unavailable)
            performance_metrics = rollout.get("performance_metrics", {})
            autonomous_perf = rollout.get("autonomous_performance", 0.0)

            # Mock feature flags (you can make these dynamic later)
            feature_flags = {
                "autonomy_mode": self.autonomous_available,
                "learning_enabled": True,
                "legacy_fallback": True
            }

            # Mock learning progress data
            learning_progress = {
                "cycles_completed": int(rollout.get("total_requests", 0) / 100),
                "last_cycle": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "performance_score": autonomous_perf
            }

            return {
                "autonomous_rollout": rollout.get("autonomous_traffic_percentage", 0.0),
                "performance_metrics": performance_metrics,
                "feature_flags": feature_flags,
                "learning_progress": learning_progress
            }

        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {
                "autonomous_rollout": 0.0,
                "performance_metrics": {},
                "feature_flags": {},
                "learning_progress": {},
                "error": str(e)
            }
