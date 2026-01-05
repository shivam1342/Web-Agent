"""
Evaluator module: Evaluate the outcome of an action.
Checks: URL change, new content, errors, page type analysis.
"""

from typing import Dict, Any


def detect_page_type(url: str) -> str:
    """
    Detect page type based on URL patterns.
    Used to determine if navigation was meaningful or redundant.
    """
    url_lower = url.lower()
    
    if "/download" in url_lower:
        return "download_page"
    elif "/genindex" in url_lower:
        return "general_index"
    elif "/py-modindex" in url_lower:
        return "module_index"
    elif "/tutorial" in url_lower:
        return "tutorial"
    elif "/library" in url_lower:
        return "library_reference"
    elif url_lower.count("/3.") >= 2:  # e.g., /3.14/ or /3.15/
        return "version_docs"
    else:
        return "general_page"


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
        
        # Enhanced insight: Compare page types to detect redundancy
        before_type = detect_page_type(before_state["url"])
        after_type = detect_page_type(after_state["url"])
        
        if before_type == after_type and before_type == "version_docs":
            result["insight"] = "Navigation changed version but not content type - exploring version variants"
        elif before_type != after_type:
            result["insight"] = f"Navigation changed page type from {before_type} to {after_type} - meaningful exploration"
        else:
            result["insight"] = "Navigation within same page type - may indicate redundant exploration"
        
        return result
    
    # Check 2: Errors appeared?
    if after_state["errors"] and not before_state["errors"]:
        result["result"] = "error_appeared"
        result["observation"] = f"Error message appeared: {after_state['errors']}"
        result["insight"] = f"Action '{action['action']}' triggered validation error - feedback mechanism working"
        return result
    
    # Check 3: New content appeared?
    before_buttons = set(before_state.get("buttons", []))
    after_buttons = set(after_state.get("buttons", []))
    new_buttons = after_buttons - before_buttons
    
    if new_buttons:
        result["result"] = "content_changed"
        result["observation"] = f"New buttons appeared: {new_buttons}"
        result["insight"] = f"Page updated after '{action['action']}' - dynamic content loaded"
        return result
    
    # Check 4: Nothing happened (potential issue)
    result["result"] = "no_change"
    result["observation"] = f"Action '{action['action']}' on '{action['target']}' produced no visible effect"
    result["insight"] = "⚠️ No observable change detected - action may have failed or target was incorrect"
    
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
