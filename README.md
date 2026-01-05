# Semi-Autonomous Web Interaction Agent

## Problem

Websites behave unpredictably and change frequently. Traditional scripted tests break easily because they rely on hard-coded selectors and fixed execution paths. When a button moves, a field is renamed, or validation logic changes, scripts fail silently or produce false positives.

**The core challenge:** How do we build an agent that can observe, reason, and adapt to what it actually sees on a page, rather than blindly following a script?

## Approach

I built a **semi-autonomous agent** using a perception → decision → evaluation loop. The agent:

1. **Observes** the current page state (buttons, links, errors)
2. **Decides** what action to take next using a combination of LLM proposals and deterministic rules
3. **Acts** by performing the chosen interaction
4. **Evaluates** the outcome to detect changes, errors, or unexpected behavior
5. **Stops** when the exploration reaches a natural endpoint

**Target Website:** https://docs.python.org  
**Focus:** Documentation exploration and navigation testing

## Architecture

### State Machine
```
IDLE → OBSERVE → DECIDE → ACT → EVALUATE → STOP                                   
          |-----------------------|      

```

The agent progresses through these states with minimal backtracking (max 3-5 actions total). This is intentionally **not** an infinite autonomous loop.

### Modules

```
web_agent/
│
├── agent/
│   ├── state.py          # State machine and state definitions
│   ├── orchestrator.py   # Main control loop
│   ├── perception.py     # Page observation (DOM scraping)
│   ├── decision.py       # Action selection logic
│   ├── evaluator.py      # Outcome evaluation
│
├── browser/
│   ├── driver.py         # Playwright/Selenium wrapper
│
├── logs/
│   └── run_log.json      # Execution trace with reasoning
│
├── main.py               # Entry point
└── README.md
```

### Module Responsibilities

- **Perception**: Extracts page title, visible buttons, links, and error keywords (no screenshots/vision)
- **Decision**: LLM proposes actions → deterministic rules filter → system selects one with reasoning
- **Evaluator**: Checks if URL changed, new content appeared, or errors were triggered
- **Orchestrator**: Coordinates state transitions and maintains execution history

## Decision Making

**This is the core intelligence of the system.**

### Step 1: Propose Actions (LLM-assisted)
The LLM receives the current page state and suggests 2-3 reasonable next actions:
```
Prompt: "Given this page state, suggest up to 3 reasonable next actions a human might try."
Output: ["Click 'Signup / Login'", "Scroll to footer", "Click logo"]
```

### Step 2: Filter Actions (Deterministic Rules)
The system applies hard rules:
- ❌ Don't repeat the same action twice
- ❌ Don't click if no clickable elements exist
- ❌ Stop if no meaningful action remains
- ✅ Prioritize actions that advance the flow (e.g., form submission over navigation)

### Step 3: Select ONE Action
The system picks the best action and logs the reasoning:
```json
{
  "action": "click_button",
  "target": "Signup / Login",
  "reason": "Primary CTA to access signup flow"
}
```

**Critical Design Choice:**  
> **The LLM only proposes actions. The system decides.**

This hybrid approach balances flexibility (LLM creativity) with reliability (deterministic control).

## Insights Produced

The agent generates insights by comparing expected vs. actual behavior:

### Example Insights:
1. **No-feedback submission**: "Submit button clicked on empty form, but no error message appeared"
2. **Silent redirects**: "Login succeeded but no confirmation message shown"
3. **Unexpected validation**: "Email field accepts invalid format"
4. **Navigation loops**: "Signup link leads back to same page"

### Output Format:
```json
{
  "action": "click_button",
  "target": "Submit",
  "result": "no_feedback",
  "observation": "Form submitted with empty fields but page shows no error",
  "insight": "Missing client-side validation"
}
```

## Limitations

This is a **minimal proof-of-concept**, not a production testing system.

**What this agent does NOT do:**
- ❌ Visual understanding (no screenshots, no OCR, no computer vision)
- ❌ Deep UX analysis (no accessibility checks, no performance metrics)
- ❌ Exhaustive coverage (explores 1 flow, not entire site)
- ❌ Infinite exploration (stops after 3-5 actions)
- ❌ Handle dynamic content (SPAs with heavy JavaScript)

**Known Constraints:**
- Perception is limited to simple DOM scraping (text only)
- No retry logic if elements are slow to load
- No memory of previous sessions
- LLM proposals are not validated for feasibility

## What I'd Do Next

If given more time, I would add:

1. **Memory System**: Track visited pages and actions across runs to avoid redundant exploration
2. **Smarter Heuristics**: Use element attributes (aria-labels, roles) to better identify important actions
3. **Retry Logic**: Handle loading delays and asynchronous content updates
4. **Comparative Analysis**: Run the same flow multiple times to detect flaky behavior
5. **Visual Diffing**: Capture screenshots to detect visual regressions
6. **Multi-flow Support**: Explore multiple independent flows (signup, checkout, search)
7. **Assertion Framework**: Let users define expected outcomes to turn insights into automated tests

## Running the Agent

```bash
# Install dependencies
pip install -r requirements.txt

# Run the agent
python main.py
```

The agent will:
1. Open https://docs.python.org
2. Explore the documentation structure
3. Generate a run log in `logs/run_log.json`
4. Output insights to console

## Demo Video

[LINK]

---

**Time spent:** [To be filled after completion]  
**Lines of code:** [To be filled after completion]  
**Key learning:** Building intelligence is about knowing when NOT to automate, not just how to automate.
