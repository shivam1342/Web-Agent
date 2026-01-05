"""
Decision module: Decide what action to take next.
Step 1: LLM proposes actions
Step 2: Deterministic rules filter
Step 3: Choose ONE action with reasoning
"""

from typing import Dict, List, Any, Optional
import os


def propose_actions_llm(page_summary: str, action_history: List[Dict]) -> List[str]:
    """
    Use Grok LLM to propose 2-3 reasonable next actions.
    Falls back to rule-based if LLM unavailable.
    """
    try:
        from agent.llm import get_llm
        llm = get_llm()
        return llm.propose_actions(page_summary, action_history)
    except Exception as e:
        print(f"[DECISION] LLM unavailable, using rule-based: {e}")
        return _fallback_proposals(page_summary, action_history)


def _fallback_proposals(page_summary: str, action_history: List[Dict]) -> List[str]:
    """Simple rule-based proposals for login testing"""
    proposals = []
    
    # Check if login failed - try correct credentials
    login_failed = any("error" in str(a).lower() for a in action_history[-2:])
    tried_wrong_login = any("try_wrong_login" in str(a) for a in action_history)
    tried_correct_login = any("try_correct_login" in str(a) for a in action_history)
    
    # On login page
    if "practice-test-login" in page_summary or "/login" in page_summary:
        if not tried_wrong_login:
            # First: try wrong credentials to test validation
            proposals.append("try_wrong_login:test_validation")
        elif not tried_correct_login:
            # Then: try correct credentials
            proposals.append("try_correct_login:test_success")
        else:
            proposals.append("observe_page:done")
    
    # On success page
    if "successfully" in page_summary.lower() or "logged in" in page_summary.lower():
        proposals.append("observe_page:success_verified")
    
    # Default
    if len(proposals) == 0:
        proposals.append("observe_page:no_action")
    
    return proposals[:3]


def filter_actions(proposals: List[str], action_history: List[Dict], page_data: Dict) -> List[str]:
    """
    Apply deterministic rules to filter proposals.
    
    Rules:
    - Don't repeat the same action twice
    - Don't click if no clickable elements exist
    - Stop if no meaningful action remains
    """
    filtered = []
    
    # Get previously executed action+target combinations
    previous_combos = [f"{a.get('action')}:{a.get('target')}" for a in action_history]
    
    for proposal in proposals:
        # Rule 1: No repeats (check action+target combo)
        if proposal in previous_combos:
            print(f"[DECISION] Filtered: {proposal} (already executed)")
            continue
        
        # Rule 2: Check if action is feasible
        if proposal.startswith("click_button:"):
            button_name = proposal.split(":", 1)[1]
            if button_name not in page_data.get("buttons", []):
                print(f"[DECISION] Filtered: {proposal} (button not found)")
                continue
        
        if proposal.startswith("click_link:"):
            link_name = proposal.split(":", 1)[1]
            # Handle both string links and dict links
            links = page_data.get("links", [])
            if links and isinstance(links[0], str):
                link_texts = links
            else:
                link_texts = [link["text"] for link in links]
            if link_name not in link_texts:
                print(f"[DECISION] Filtered: {proposal} (link not found)")
                continue
        
        filtered.append(proposal)
    
    return filtered


def choose_action(filtered_proposals: List[str], page_data: Dict) -> Optional[Dict[str, Any]]:
    """
    Choose ONE action from filtered proposals.
    
    Returns:
        {
            "action": str,
            "target": str,
            "reason": str
        }
    """
    if not filtered_proposals:
        return None
    
    # First priority: Navigate to signup/login if not there yet
    current_url = page_data.get("url", "")
    if "/login" not in current_url and "/signup" not in current_url:
        for proposal in filtered_proposals:
            if proposal.startswith("click_link:Signup"):
                return {
                    "action": "click_link",
                    "target": "Signup / Login",
                    "reason": "Navigate to signup/login page first"
                }
    
    # Second priority: Initial signup form (on /login page)
    for proposal in filtered_proposals:
        if proposal.startswith("fill_signup_form:"):
            return {
                "action": "fill_signup_form",
                "target": "new_account",
                "reason": "Create initial account with name and email"
            }
    
    # Third: Detailed registration form (on /signup page after initial signup)
    for proposal in filtered_proposals:
        if proposal.startswith("fill_registration_form:"):
            return {
                "action": "fill_registration_form",
                "target": "complete_profile",
                "reason": "LLM-assisted intelligent form filling for detailed registration"
            }
        
        if proposal.startswith("fill_login_form:"):
            return {
                "action": "fill_login_form",
                "target": "existing_account",
                "reason": "Testing login flow with stored credentials"
            }
        
        if proposal.startswith("try_empty_login:"):
            return {
                "action": "try_empty_login",
                "target": "validation_test",
                "reason": "Testing form validation with empty submission"
            }
    
    # Next: Navigate to login after signup
    for proposal in filtered_proposals:
        if proposal.startswith("navigate_to_login:"):
            return {
                "action": "navigate_to_login",
                "target": "test_login",
                "reason": "Navigate to login to test created account"
            }
    
    # Next: click important buttons
    for proposal in filtered_proposals:
        if proposal.startswith("click_button:"):
            button_name = proposal.split(":", 1)[1]
            return {
                "action": "click_button",
                "target": button_name,
                "reason": f"Button '{button_name}' appears to be a primary CTA"
            }
    
    # Next: click important links
    for proposal in filtered_proposals:
        if proposal.startswith("click_link:"):
            link_name = proposal.split(":", 1)[1]
            return {
                "action": "click_link",
                "target": link_name,
                "reason": f"Link '{link_name}' likely leads to target flow"
            }
    
    # Fallback: observe
    if filtered_proposals[0].startswith("observe_page:"):
        return None
    
    # Fallback: first proposal
    return {
        "action": filtered_proposals[0],
        "target": "unknown",
        "reason": "Default action from proposals"
    }


def decide_next_action(page_data: Dict[str, Any], action_history: List[Dict]) -> Optional[Dict[str, Any]]:
    """
    Main decision pipeline.
    
    Returns chosen action with reasoning, or None if should stop.
    """
    from agent.perception import summarize_page_state
    
    # Step 1: Generate page summary for LLM
    page_summary = summarize_page_state(page_data)
    print(f"\n[DECISION] Current page state:\n{page_summary}")
    
    # Step 2: LLM proposes actions
    proposals = propose_actions_llm(page_summary, action_history)
    print(f"[DECISION] LLM proposals: {proposals}")
    
    # Step 3: Filter with deterministic rules
    filtered = filter_actions(proposals, action_history, page_data)
    print(f"[DECISION] Filtered proposals: {filtered}")
    
    # Step 4: Choose ONE action
    chosen = choose_action(filtered, page_data)
    
    if chosen:
        print(f"[DECISION] ✓ Chosen: {chosen['action']} → {chosen['target']}")
        print(f"[DECISION] Reason: {chosen['reason']}")
    else:
        print("[DECISION] No valid action remaining. Should stop.")
    
    return chosen
