"""
Perception module: Observe the current page state.
Extracts: URL, title, buttons, links, error keywords.
No screenshots. No vision models.
"""

from typing import Dict, List, Any
from playwright.sync_api import Page


ERROR_KEYWORDS = ["error", "invalid", "failed", "wrong", "incorrect", "required"]


def observe_page(page: Page) -> Dict[str, Any]:
    """
    Extract simple page state information.
    
    Returns:
        {
            "url": str,
            "title": str,
            "buttons": List[str],
            "links": List[Dict[str, str]],
            "input_fields": List[str],
            "errors": List[str]
        }
    """
    page_data = {
        "url": page.url,
        "title": page.title(),
        "buttons": [],
        "links": [],
        "input_fields": [],
        "errors": []
    }
    
    # Extract visible buttons
    try:
        buttons = page.locator("button, input[type='submit'], a.btn").all()
        for btn in buttons:
            if btn.is_visible():
                text = btn.inner_text().strip()
                if text:
                    page_data["buttons"].append(text)
    except Exception as e:
        print(f"[PERCEPTION] Error extracting buttons: {e}")
    
    # Extract visible links (limit to navigation links)
    try:
        links = page.locator("a[href]").all()
        for link in links[:20]:  # Limit to first 20 to avoid noise
            if link.is_visible():
                text = link.inner_text().strip()
                href = link.get_attribute("href")
                if text and href:
                    page_data["links"].append({"text": text, "href": href})
    except Exception as e:
        print(f"[PERCEPTION] Error extracting links: {e}")
    
    # Extract input fields
    try:
        inputs = page.locator("input:visible, textarea:visible").all()
        for inp in inputs:
            field_type = inp.get_attribute("type") or "text"
            placeholder = inp.get_attribute("placeholder") or ""
            name = inp.get_attribute("name") or ""
            page_data["input_fields"].append({
                "type": field_type,
                "name": name,
                "placeholder": placeholder
            })
    except Exception as e:
        print(f"[PERCEPTION] Error extracting input fields: {e}")
    
    # Detect errors on page
    try:
        body_text = page.locator("body").inner_text().lower()
        for keyword in ERROR_KEYWORDS:
            if keyword in body_text:
                # Find the actual error message
                error_elements = page.locator(f"text=/{keyword}/i").all()
                for elem in error_elements[:3]:  # Max 3 error messages
                    if elem.is_visible():
                        page_data["errors"].append(elem.inner_text().strip())
                break
    except Exception as e:
        print(f"[PERCEPTION] Error detecting errors: {e}")
    
    return page_data


def summarize_page_state(page_data: Dict[str, Any]) -> str:
    """Create a text summary of page state for LLM"""
    summary = f"URL: {page_data['url']}\n"
    summary += f"Title: {page_data['title']}\n\n"
    
    if page_data["buttons"]:
        summary += f"Visible Buttons: {', '.join(page_data['buttons'][:5])}\n"
    
    if page_data["links"]:
        # Handle both string links and dict links
        if isinstance(page_data["links"][0], str):
            link_texts = page_data["links"][:5]
        else:
            link_texts = [link["text"] for link in page_data["links"][:5]]
        summary += f"Visible Links: {', '.join(link_texts)}\n"
    
    if page_data.get("input_fields"):
        if isinstance(page_data["input_fields"][0], dict):
            field_info = [f"{f['type']}({f['name'] or f['placeholder']})" 
                          for f in page_data["input_fields"][:5]]
        else:
            field_info = page_data["input_fields"][:5]
        summary += f"Input Fields: {', '.join(field_info)}\n"
    
    if page_data["errors"]:
        summary += f"⚠️ Errors Detected: {', '.join(page_data['errors'])}\n"
    
    return summary
