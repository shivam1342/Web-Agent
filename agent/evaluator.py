"""
Evaluator module: Evaluate the outcome of an action.
Checks: URL change, new content, errors, nothing happened.
"""

from typing import Dict, Any


def evaluate_action_outcome(
    before_state: Dict[str, Any],
    after_state: Dict[str, Any],
    action: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate what happened after an action was performed.
    
    Returns:
        {
            "result": str,  # "url_changed", "content_changed", "error_appeared", "no_change"
            "observation": str,
            "insight": Optional[str]
        }
    """
    result = {
        "result": "no_change",
        "observation": "",
        "insight": None
    }
    
    # Check 1: URL changed?
    if before_state["url"] != after_state["url"]:
        result["result"] = "url_changed"
        result["observation"] = f"Page navigated from {before_state['url']} to {after_state['url']}"
        result["insight"] = f"Action '{action['action']}' triggered navigation"
        return result
    
    # Check 2: Errors appeared?
    if after_state["errors"] and not before_state["errors"]:
        result["result"] = "error_appeared"
        result["observation"] = f"Error message appeared: {after_state['errors']}"
        
        # Specific insight for login errors
        if "login" in action.get("action", "").lower():
            result["insight"] = f"⚠️ Login failed with error - credentials don't exist. Need to signup first!"
        else:
            result["insight"] = f"Action '{action['action']}' triggered validation error"
        return result
    
    # Check 3: New content appeared?
    before_buttons = set(before_state.get("buttons", []))
    after_buttons = set(after_state.get("buttons", []))
    new_buttons = after_buttons - before_buttons
    
    if new_buttons:
        result["result"] = "content_changed"
        result["observation"] = f"New buttons appeared: {new_buttons}"
        result["insight"] = f"Page updated after '{action['action']}'"
        return result
    
    # Check 4: Nothing happened (potential issue)
    result["result"] = "no_change"
    result["observation"] = f"Action '{action['action']}' on '{action['target']}' produced no visible effect"
    result["insight"] = "⚠️ Possible issue: No feedback after interaction (missing validation or broken behavior)"
    
    return result


def generate_insight(evaluation: Dict[str, Any], action: Dict[str, Any]) -> str:
    """
    Generate a human-readable insight about the interaction.
    """
    insight_text = f"\n{'='*60}\n"
    insight_text += f"ACTION: {action['action']} → {action['target']}\n"
    insight_text += f"REASON: {action['reason']}\n"
    insight_text += f"RESULT: {evaluation['result']}\n"
    insight_text += f"OBSERVATION: {evaluation['observation']}\n"
    
    if evaluation.get("insight"):
        insight_text += f"💡 INSIGHT: {evaluation['insight']}\n"
    
    insight_text += f"{'='*60}\n"
    
    return insight_text
