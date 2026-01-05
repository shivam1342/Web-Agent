"""
Orchestrator: Main control loop.
Coordinates state transitions and manages execution flow.
"""

from agent.state import AgentState, StateContext
from agent.perception import observe_page
from agent.decision import decide_next_action
from agent.evaluator import evaluate_action_outcome, generate_insight
from browser.driver import BrowserDriver
import json
import os


class Orchestrator:
    """Main control loop for the agent"""
    
    def __init__(self, start_url: str, headless: bool = False):
        self.start_url = start_url
        self.headless = headless
        self.driver = BrowserDriver(headless=headless)
        self.context = StateContext(current_state=AgentState.IDLE)
        self.insights = []
    
    def run(self):
        """Execute the main agent loop"""
        try:
            # Start browser
            self.driver.open(self.start_url)
            self.context.transition_to(AgentState.OBSERVE)
            
            # Main loop: OBSERVE → DECIDE → ACT → EVALUATE → (back to OBSERVE)
            while self.context.current_state != AgentState.STOP:
                
                if self.context.current_state == AgentState.OBSERVE:
                    self._observe()
                
                elif self.context.current_state == AgentState.DECIDE:
                    self._decide()
                
                elif self.context.current_state == AgentState.ACT:
                    self._act()
                
                elif self.context.current_state == AgentState.EVALUATE:
                    self._evaluate()
            
            print("\n[ORCHESTRATOR] Exploration complete.")
            self._save_logs()
            
        finally:
            self.driver.close()
    
    def _observe(self):
        """OBSERVE state: Extract page information"""
        print("\n[OBSERVE] Reading page state...")
        self.context.page_data = self.driver.get_page_state()
        print(f"[OBSERVE] URL: {self.context.page_data['url']}")
        print(f"[OBSERVE] Buttons: {self.context.page_data['buttons'][:5]}")
        print(f"[OBSERVE] Links: {len(self.context.page_data['links'])} found")
        
        self.context.transition_to(AgentState.DECIDE)
    
    def _decide(self):
        """DECIDE state: Choose next action"""
        print("\n[DECIDE] Determining next action...")
        
        action = decide_next_action(
            self.context.page_data,
            self.context.action_history
        )
        
        if action is None:
            print("[DECIDE] No valid actions. Stopping.")
            self.context.transition_to(AgentState.STOP)
        else:
            self.context.chosen_action = action
            self.context.transition_to(AgentState.ACT)
    
    def _act(self):
        """ACT state: Execute chosen action"""
        print("\n[ACT] Executing action...")
        action = self.context.chosen_action
        
        # Store page state before action
        before_state = self.context.page_data.copy()
        
        # Execute action based on type
        action_type = action.get("action", "")
        target = action.get("target", "")
        success = False
        
        if action_type == "click_button":
            success = self.driver.click_button(target)
        elif action_type == "click_link":
            success = self.driver.click_link(target)
        else:
            print(f"[ACT] Unknown action type: {action_type}")
        
        if not success:
            print("[ACT] Action failed. Moving to next observation.")
            # Don't stop, just continue
        
        # Observe new state
        after_state = self.driver.get_page_state()
        
        # Store for evaluation
        self.context.page_data = after_state
        self.context.action_result = {
            "before": before_state,
            "after": after_state,
            "success": success
        }
        
        # Log action
        self.context.log_action(action)
        
        self.context.transition_to(AgentState.EVALUATE)
    
    def _evaluate(self):
        """EVALUATE state: Check outcome"""
        print("\n[EVALUATE] Analyzing outcome...")
        
        evaluation = evaluate_action_outcome(
            self.context.action_result["before"],
            self.context.action_result["after"],
            self.context.chosen_action
        )
        
        # Generate insight
        insight = generate_insight(evaluation, self.context.chosen_action)
        print(insight)
        self.insights.append({
            "action": self.context.chosen_action,
            "evaluation": evaluation,
            "step": self.context.action_count
        })
        
        # Store result for stop check
        self.context.action_result = evaluation
        
        # Check if should stop
        if self.context.should_stop():
            print(f"[EVALUATE] Reached {self.context.action_count} actions. Stopping.")
            self.context.transition_to(AgentState.STOP)
        else:
            # Continue: Loop back to OBSERVE
            self.context.transition_to(AgentState.OBSERVE)
    
    def _save_logs(self):
        """Save execution logs"""
        log_path = "logs/run_log.json"
        os.makedirs("logs", exist_ok=True)
        
        log_data = {
            "start_url": self.start_url,
            "total_actions": self.context.action_count,
            "final_url": self.context.page_data.get("url") if self.context.page_data else None,
            "action_history": self.context.action_history,
            "insights": self.insights
        }
        
        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)
        
        print(f"\n[ORCHESTRATOR] Logs saved to {log_path}")
