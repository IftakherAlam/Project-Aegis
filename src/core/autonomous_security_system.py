# src/core/autonomous_security_system.py - FIXED VERSION
import asyncio
import logging
from typing import Dict, Any
import time

class AutonomousSecuritySystem:
    """
    Complete self-learning security system that continuously improves
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components with error handling
        try:
            from .autonomous_analyzer import AutonomousSecurityAnalyzer
            self.analyzer = AutonomousSecurityAnalyzer()
            self.analyzer_available = True
        except ImportError as e:
            self.logger.error(f"Autonomous analyzer not available: {e}")
            self.analyzer_available = False
            self.analyzer = None
        
        try:
            from .reinforcement_learner import ReinforcementSecurityLearner
            self.reinforcement_learner = ReinforcementSecurityLearner()
            self.reinforcement_available = True
        except ImportError as e:
            self.logger.error(f"Reinforcement learner not available: {e}")
            self.reinforcement_available = False
            self.reinforcement_learner = None
        
        try:
            from .evolutionary_optimizer import EvolutionaryPatternOptimizer
            self.evolutionary_optimizer = EvolutionaryPatternOptimizer(population_size=20)  # Smaller for testing
            self.evolutionary_available = True
        except ImportError as e:
            self.logger.error(f"Evolutionary optimizer not available: {e}")
            self.evolutionary_available = False
            self.evolutionary_optimizer = None
        
        # Learning schedule
        self.learning_interval = 100  # Learn every 100 analyses (reduced for testing)
        self.analysis_count = 0
        
        self.logger.info(f"Autonomous system initialized - "
                        f"Analyzer: {self.analyzer_available}, "
                        f"Reinforcement: {self.reinforcement_available}, "
                        f"Evolutionary: {self.evolutionary_available}")
    
    async def process_input(self, text: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process input with continuous learning"""
        self.analysis_count += 1
        
        # If analyzer is not available, return basic result
        if not self.analyzer_available:
            return {
                'is_safe': True,
                'threat_score': 0.0,
                'confidence': 0.5,
                'detected_patterns': [],
                'analyzer_used': 'fallback',
                'learning_metadata': {'error': 'analyzer_not_available'}
            }
        
        try:
            # Analyze with current knowledge
            result = self.analyzer.analyze_and_learn(text, user_context)
            
            # Simple reinforcement learning decision (if available)
            if self.reinforcement_available:
                state = self._get_state_representation(text, result)
                action = self.reinforcement_learner.choose_action(state)
                # For now, just log the action
                self.logger.debug(f"Reinforcement learning action: {action}")
            
            # Periodic deep learning
            if self.analysis_count % self.learning_interval == 0:
                await self._deep_learning_cycle()
            
            return {
                'is_safe': result['is_safe'],
                'threat_score': result['threat_score'],
                'confidence': result['confidence'],
                'detected_patterns': result['detected_patterns'],
                'analyzer_used': 'autonomous',
                'learning_metadata': {
                    'learned_new_patterns': result.get('learned_new_patterns', 0),
                    'analysis_count': self.analysis_count
                }
            }
            
        except Exception as e:
            self.logger.error(f"Autonomous processing failed: {e}")
            return {
                'is_safe': True,  # Fail-safe: allow when system fails
                'threat_score': 0.0,
                'confidence': 0.3,
                'detected_patterns': [],
                'analyzer_used': 'error_fallback',
                'learning_metadata': {'error': str(e)}
            }
    
    def _get_state_representation(self, text: str, result: Dict[str, Any]) -> tuple:
        """Create state representation for reinforcement learning"""
        # Simple state representation based on text features and analysis result
        text_length = len(text)
        threat_score = result.get('threat_score', 0.0)
        confidence = result.get('confidence', 0.5)
        
        # Discretize values for state representation
        length_state = 'short' if text_length < 50 else 'medium' if text_length < 200 else 'long'
        threat_state = 'low' if threat_score < 0.3 else 'medium' if threat_score < 0.7 else 'high'
        confidence_state = 'low' if confidence < 0.3 else 'medium' if confidence < 0.7 else 'high'
        
        return (length_state, threat_state, confidence_state)
    
    async def _deep_learning_cycle(self):
        """Perform comprehensive learning and optimization"""
        self.logger.info("Starting deep learning cycle")
        
        try:
            # Get performance data from analyzer
            if self.analyzer_available:
                performance_data = self.analyzer.get_learning_report()
                self.logger.info(f"Learning report: {performance_data}")
            
            # Evolve pattern population if evolutionary optimizer is available
            if self.evolutionary_available and self.analyzer_available:
                fitness_scores = self._calculate_pattern_fitness()
                if fitness_scores:
                    self.evolutionary_optimizer.evolve_population(fitness_scores)
                    
                    # Get evolved patterns and integrate them
                    evolved_stats = self.evolutionary_optimizer.get_population_stats()
                    self.logger.info(f"Evolved population: {evolved_stats}")
                    
                    # Integrate top patterns into analyzer
                    self._integrate_evolved_patterns()
            
            self.logger.info("Deep learning cycle completed")
            
        except Exception as e:
            self.logger.error(f"Deep learning cycle failed: {e}")
    
    def _calculate_pattern_fitness(self) -> Dict[str, float]:
        """Calculate fitness scores for patterns"""
        # For now, use a simple fitness calculation
        # In a real system, this would use actual performance data
        fitness_scores = {}
        
        if not self.analyzer_available:
            return fitness_scores
            
        try:
            # Get patterns from analyzer
            patterns = list(self.analyzer.pattern_weights.keys())
            
            # Simple fitness: higher weight = higher fitness
            for pattern in patterns[:50]:  # Limit to first 50 patterns
                weight = self.analyzer.pattern_weights.get(pattern, 0.5)
                fitness_scores[pattern] = weight
                
        except Exception as e:
            self.logger.warning(f"Fitness calculation failed: {e}")
            
        return fitness_scores
    
    def _integrate_evolved_patterns(self):
        """Integrate evolved patterns into the main analyzer"""
        if not self.evolutionary_available or not self.analyzer_available:
            return
            
        try:
            evolved_patterns = self.evolutionary_optimizer.pattern_population
            
            for pattern in evolved_patterns:
                if pattern not in self.analyzer.pattern_weights:
                    # New pattern - start with medium confidence
                    self.analyzer.pattern_weights[pattern] = 0.5
                    
            self.logger.info(f"Integrated {len(evolved_patterns)} evolved patterns")
            
        except Exception as e:
            self.logger.error(f"Pattern integration failed: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        status = {
            'analysis_count': self.analysis_count,
            'analyzer_available': self.analyzer_available,
            'reinforcement_available': self.reinforcement_available,
            'evolutionary_available': self.evolutionary_available,
            'learning_interval': self.learning_interval
        }
        
        if self.analyzer_available:
            try:
                learning_report = self.analyzer.get_learning_report()
                status['learning_report'] = learning_report
            except Exception as e:
                status['learning_report_error'] = str(e)
        
        if self.evolutionary_available:
            try:
                pop_stats = self.evolutionary_optimizer.get_population_stats()
                status['evolutionary_stats'] = pop_stats
            except Exception as e:
                status['evolutionary_stats_error'] = str(e)
                
        return status