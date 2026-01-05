"""
State machine for the web agent.
States: IDLE → OBSERVE → DECIDE → ACT → EVALUATE → STOP
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class AgentState(Enum):
    """Agent states following a simple FSM"""
    IDLE = "idle"
    OBSERVE = "observe"
    DECIDE = "decide"
    ACT = "act"
    EVALUATE = "evaluate"
    STOP = "stop"


@dataclass
class StateContext:
    """Context shared across states"""
    current_state: AgentState
    page_data: Optional[Dict[str, Any]] = None
    chosen_action: Optional[Dict[str, Any]] = None
    action_result: Optional[Dict[str, Any]] = None
    action_count: int = 0
    action_history: list = None
    
    def __post_init__(self):
        if self.action_history is None:
            self.action_history = []
    
    def transition_to(self, new_state: AgentState):
        """Transition to a new state"""
        print(f"[STATE] {self.current_state.value} → {new_state.value}")
        self.current_state = new_state
    
    def log_action(self, action: Dict[str, Any]):
        """Record an action in history"""
        self.action_history.append(action)
        self.action_count += 1
    
    def should_stop(self) -> bool:
        """Determine if agent should stop"""
        # Simple: Stop after 6 actions
        if self.action_count >= 6:
            return True
        
        return False
