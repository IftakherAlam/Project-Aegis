# src/core/reinforcement_learner.py
from typing import Tuple, Dict, Any
import random

class ReinforcementSecurityLearner:
    """
    Uses reinforcement learning to optimize detection strategies
    """
    
    def __init__(self):
        self.q_table = {}  # State-action values
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.1
        
    def choose_action(self, state: Tuple) -> str:
        """Choose action based on current state and learned policy"""
        if np.random.random() < self.exploration_rate:
            return np.random.choice(['block', 'allow', 'escalate'])
        else:
            return self._get_best_action(state)
    
    def update_q_value(self, state: Tuple, action: str, reward: float, next_state: Tuple):
        """Update Q-values based on experience"""
        current_q = self.q_table.get((state, action), 0)
        max_future_q = max([self.q_table.get((next_state, a), 0) for a in ['block', 'allow', 'escalate']])
        
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_future_q - current_q)
        self.q_table[(state, action)] = new_q
    
    def _get_best_action(self, state: Tuple) -> str:
        """Get the best action for a given state"""
        actions = ['block', 'allow', 'escalate']
        q_values = [self.q_table.get((state, action), 0) for action in actions]
        return actions[np.argmax(q_values)]