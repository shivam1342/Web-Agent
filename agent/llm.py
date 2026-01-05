"""
LLM integration using Groq API (fast inference platform).
Provides intelligent decision-making and form filling.
"""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GrokLLM:
    """Wrapper for Groq LLM API (fast inference)"""
    
    def __init__(self):
        api_key = os.getenv("llm_key") or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("llm_key not found in .env file")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = "llama-3.3-70b-versatile"  # Groq's fast model
    
    def propose_actions(self, page_summary: str, action_history: List[Dict]) -> List[str]:
        """
        Ask Groq to propose 2-3 reasonable next actions for exploring documentation.
        """
        history_summary = "\n".join([
            f"- {a.get('action')} on '{a.get('target')}'"
            for a in action_history[-3:]  # Last 3 actions
        ]) if action_history else "No actions yet"
        
        prompt = f"""You are a web exploration agent browsing Python documentation to learn about different topics.

Current Page State:
{page_summary}

Actions Already Taken:
{history_summary}

Your goal: Explore the Python documentation by clicking on interesting links or buttons.

RULES:
1. Click on links that lead to interesting documentation topics
2. Explore different Python versions, tutorials, or library docs
3. Navigate through the documentation structure
4. Avoid repeating the same action

Available actions:
- click_link:<exact_link_text> (choose from visible links above)
- click_button:<exact_button_text> (choose from visible buttons above)

Suggest 2-3 diverse exploration actions as a simple list:
- click_link:Tutorial
- click_link:Library Reference"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that suggests web exploration actions for learning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            content = response.choices[0].message.content.strip()
            print(f"[GROQ LLM] Raw response: {content[:200]}")
            
            # Parse response into action list
            actions = []
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    action = line[1:].strip()
                    if ':' in action:
                        # Clean up spaces around colon
                        parts = action.split(':', 1)
                        action = f"{parts[0].strip()}:{parts[1].strip()}"
                        actions.append(action)
            
            print(f"[GROQ LLM] Proposed: {actions}")
            return actions[:3]
            
        except Exception as e:
            print(f"[GROQ LLM] Error: {e}")
            # Fallback to rule-based
            return self._fallback_proposals(page_summary, action_history)
    
    def generate_form_data(self, form_fields: List[Dict]) -> Dict[str, str]:
        """
        Ask Grok to generate appropriate test data for form fields.
        """
        fields_description = "\n".join([
            f"- {f.get('name', 'unknown')} (type: {f.get('type', 'text')}, placeholder: {f.get('placeholder', 'N/A')})"
            for f in form_fields[:15]  # Limit to avoid token overflow
        ])
        
        prompt = f"""You are filling out a test registration form. Generate realistic dummy data for these fields:

{fields_description}

Requirements:
- Use realistic but obviously fake test data
- For names: Use "Test" prefix (e.g., "Test User")
- For emails: Use format test[timestamp]@example.com
- For passwords: Use "TestPass123!"
- For dates: Use reasonable values (e.g., birthdate: 1990-01-01)
- For dropdowns/selects: Suggest a reasonable value
- For checkboxes: Suggest "true" or "false"

Respond ONLY with a JSON object mapping field names to values. Example:
{{
  "first_name": "Test",
  "last_name": "User",
  "password": "TestPass123!",
  "day": "1",
  "month": "1",
  "year": "1990"
}}

Do not include any explanation, only the JSON object."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You generate realistic test data for forms. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            import json
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            form_data = json.loads(content)
            print(f"[GROK LLM] Generated data for {len(form_data)} fields")
            return form_data
            
        except Exception as e:
            print(f"[GROK LLM] Error generating form data: {e}")
            # Fallback to basic data
            return self._fallback_form_data(form_fields)
    
    def _fallback_proposals(self, page_summary: str, action_history: List[Dict]) -> List[str]:
        """Fallback rule-based proposals if LLM fails"""
        proposals = []
        
        # For documentation sites, suggest exploring common sections
        if "Tutorial" in page_summary:
            proposals.append("click_link:Tutorial")
        elif "Library Reference" in page_summary:
            proposals.append("click_link:Library Reference")
        elif "What's New" in page_summary:
            proposals.append("click_link:What's New")
        
        # If no specific suggestions, just pick a visible link
        if not proposals:
            proposals.append("click_link:Download")
        
        return proposals
    
    def _fallback_form_data(self, form_fields: List[Dict]) -> Dict[str, str]:
        """Fallback form data if LLM fails"""
        import time
        data = {}
        timestamp = int(time.time())
        
        for field in form_fields:
            name = field.get("name", "")
            field_type = field.get("type", "text")
            
            if "email" in name.lower():
                data[name] = f"test{timestamp}@example.com"
            elif "password" in name.lower():
                data[name] = "TestPass123!"
            elif "name" in name.lower():
                data[name] = "TestUser"
            elif field_type == "text":
                data[name] = "Test"
            
        return data


# Global LLM instance
_llm_instance: Optional[GrokLLM] = None

def get_llm() -> GrokLLM:
    """Get or create LLM instance"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = GrokLLM()
    return _llm_instance
