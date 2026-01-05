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

**Why Python Docs?**
- Stable, well-structured site (avoids flaky JavaScript)
- Information-dense (tests meaningful navigation decisions)
- Version variants (tests agent's ability to detect redundant exploration)
- No authentication flow (focuses on pure exploration intelligence)

## Architecture

### State Machine
```
IDLE → OBSERVE → DECIDE → ACT → EVALUATE → TERMINATE
          ↑________________________|      
```

**Key Design Note:** The agent does not assume actions succeed. Evaluation feeds back into observation to confirm environmental change before continuing. This is systems thinking - the agent verifies state transitions rather than blindly advancing.

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
- ✅ Prioritize actions using intelligent heuristics

### Step 3: Select ONE Action with Heuristics
The system picks the best action using decision heuristics:

**Heuristics Applied:**
1. Prefer version-changing links (increases information diversity)
2. Prefer documentation navigation over repetitive sibling navigation
3. Prefer links that increase information density (index, modules, tutorials)

Example reasoning output:
```json
{
  "action": "click_link",
  "target": "Python 3.15 (in development)",
  "reason": "Version link selected to compare documentation variants across Python versions"
}
```

**Critical Design Choice:**  
> **The intelligence lies in how the system constrains and evaluates LLM suggestions, not in the model itself.**

This hybrid approach balances flexibility (LLM creativity) with reliability (deterministic control).

## Insights Produced

The agent generates insights by analyzing page type transitions and navigation patterns:

### Example Insights:
1. **Redundant navigation**: "Navigation changed version but not content type - exploring version variants"
2. **Meaningful exploration**: "Navigation changed page type from version_docs to module_index - meaningful exploration"
3. **Failed actions**: "No observable change detected - action may have failed or target was incorrect"
4. **Dynamic content**: "Page updated after 'click_button' - dynamic content loaded"

### Output Format:
```json
{
  "action": "click_link",
  "target": "modules",
  "result": "url_changed",
  "observation": "Page navigated from .../download.html to .../py-modindex.html",
  "insight": "Navigation changed page type from download_page to module_index - meaningful exploration"
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
