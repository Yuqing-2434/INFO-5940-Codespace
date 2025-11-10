# app.py
"""
Multi-Agent Travel Planner

Highlights:
- Clear separation of concerns (tools, agents, orchestration, UI)
- Simple global logger to display tool calls live in the sidebar
- Planner → Reviewer pipeline enforced before rendering any answer
- Minimal dependencies and straightforward control flow
"""

from __future__ import annotations

import os

import asyncio
import time
from typing import Callable, Dict, List, Optional, Any

import streamlit as st
from dotenv import load_dotenv
from tavily import TavilyClient


# ──────────────────────────────────────────────────────────────────────────────
# Environment & Globals
# ──────────────────────────────────────────────────────────────────────────────

load_dotenv()  # Loads variables from a local .env if present

os.environ.setdefault("OPENAI_LOG", "error")
os.environ.setdefault("OPENAI_TRACING", "false")

# Tool call logger: the UI sets this per request. The tool checks it and logs.
# Using a simple global makes this easy to teach and reason about.
TOOL_LOGGER: Optional[Callable[[Dict[str, Any]], None]] = None


def set_tool_logger(logger: Optional[Callable[[Dict[str, Any]], None]]) -> None:
    """Install or remove the UI logger used by tools to report activity."""
    global TOOL_LOGGER
    TOOL_LOGGER = logger


def log_tool_event(event: Dict[str, Any]) -> None:
    """If a logger is installed, send the event to the UI."""
    if TOOL_LOGGER is not None:
        try:
            TOOL_LOGGER(event)
        except Exception:
            # Logging should never break the app or the tool itself
            pass


def redact_for_logs(value: Any) -> Any:
    """
    Make sure we don't leak secrets and keep logs small.
    This is deliberately simple for teaching.
    """
    if isinstance(value, str):
        low = value.lower()
        if any(k in low for k in ("api_key", "token", "secret", "password")):
            return "[redacted]"
        return value if len(value) <= 300 else value[:120] + "… [truncated]"
    if isinstance(value, dict):
        return {k: ("[redacted]" if any(s in k.lower() for s in ("key", "token", "secret", "password"))
                    else redact_for_logs(v))
                for k, v in value.items()}
    if isinstance(value, list):
        return [redact_for_logs(v) for v in value]
    return value


# ──────────────────────────────────────────────────────────────────────────────
# Agent Framework Imports (provided by you)
# ──────────────────────────────────────────────────────────────────────────────
# These come from your own framework. We assume:
# - Agent: defines a model + instructions + optional tools
# - Runner.run(agent, input): executes an agent and returns an object with text
from agents import Agent, Runner, function_tool  # type: ignore


# ──────────────────────────────────────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────────────────────────────────────

@function_tool
def internet_search(query: str) -> str:
    """
    Internet search backed by Tavily.
    - Reads TAVILY_API_KEY from environment.
    - Sends simple log events before/after the call so the UI can show activity.
    """
    log_tool_event({"type": "call", "tool": "internet_search", "args": {"query": redact_for_logs(query)}})

    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            msg = "missing TAVILY_API_KEY in environment."
            log_tool_event({"type": "error", "tool": "internet_search", "error": msg})
            return f"Search error: {msg}"

        client = TavilyClient(api_key=api_key)
        response = client.search(query, max_results=3)

        items = response.get("results", [])
        lines = [f"- {it.get('title', 'N/A')}: {it.get('content', 'N/A')}" for it in items]
        output = "\n".join(lines) if lines else "No results found."

        log_tool_event({
            "type": "result",
            "tool": "internet_search",
            "preview": redact_for_logs(output[:400] + ("…" if len(output) > 400 else "")),
        })
        return output

    except Exception as e:
        log_tool_event({"type": "error", "tool": "internet_search", "error": str(e)})
        return f"Search error: {e}"

    finally:
        log_tool_event({"type": "end", "tool": "internet_search"})


# ──────────────────────────────────────────────────────────────────────────────
# Agents
# ──────────────────────────────────────────────────────────────────────────────

# BEGIN SOLUTION
REVIEWER_INSTRUCTIONS = """
You are the Reviewer Agent. Your role is to critically validate the Planner’s itinerary and suggest
concrete fixes before the plan is shown to the user.

TOOLS
- You MAY and SHOULD use the provided internet_search tool for real-time fact-checking of opening hours,
  typical ticket prices/availability, intercity travel times, reservation requirements, seasonal closures,
  and feasibility of sequences (e.g., back-to-back activities that are too far apart).
- Prefer official or authoritative sources (official site, Google Maps/Business, transit operators, museum sites,
  city tourism boards). Cross-check at least two sources when a fact is crucial.

REVIEW SCOPE
- Opening hours by day and time windows listed in the itinerary (watch for typical weekly closures).
- Ticket prices and whether student/child discounts exist; whether pre-booking is needed.
- Intercity travel feasibility (mode, typical durations, first/last departures if critical).
- Intra-city travel time realism; detect unrealistic chaining of distant locations without transit time.
- Budget sanity (spot check large items against typical prices).
- Pacing realism (too many timed items; insufficient buffers; meals at odd hours).
- Seasonal factors (off-season closures or limited hours).

HOW TO WORK
1) Parse the plan and the “Checks Needed for Reviewer” list.
2) For each check, run targeted internet_search queries (include city, venue, weekday, and month/season if known).
   Example queries:
   - "Louvre Museum hours Tuesday ticket price official site"
   - "Train CityA to CityB duration weekday afternoon"
   - "Sagrada Familia student ticket reservation required"
3) Log each check’s result succinctly (source name + key fact + URL if available).
4) Identify issues: impossible/closed, sold-out/reservation required, under/over-estimated times,
   large price mismatches, transfers that are too long for the day’s schedule, etc.
5) Produce a **Delta List** of concrete fixes. Each item must include:
   - Day number
   - Original item (what to change)
   - Proposed change (specific new time/place/sequence/cost)
   - Reason (from your fact-check)
   - Source(s) used
6) Apply the deltas to create a **Revised Itinerary** that is feasible. Keep the Planner’s style/structure.
7) If the plan is feasible as-is, state that explicitly and still include a short validation summary.

OUTPUT FORMAT (Markdown)
Use this structure:

## Validation Summary
- Checks run: N
- Issues found: K (Critical: C / Minor: M)
- Notes: brief overview

## Sources Consulted
- Source 1 – key fact (URL)
- Source 2 – key fact (URL)
- ...

## Delta List (Concrete Changes)
1) Day X — Original: "..."; Change: "..."; Reason: "..."; Source(s): ...
2) Day Y — ...

## Revised Itinerary
(If changes were needed, present the updated day-by-day sections. Otherwise write: “No changes required.
Plan appears feasible based on sources above.”)

REVIEWER MINDSET
- Be precise and surgical: change only what must change; keep the user’s constraints sacred.
- When in doubt, add small buffers rather than deleting highlights the user cares about.
- If information is conflicting online, choose the more conservative/safer option and note the ambiguity.

"""

PLANNER_INSTRUCTIONS = """
You are the Planner Agent in a two-agent Streamlit travel app.
Your job: transform a vague user prompt into a detailed, feasible day-by-day itinerary.

CRITICAL RULES
- DO NOT use the internet or any tools. Rely only on general world knowledge.
- Respect user constraints: dates/duration, total budget, interests, pace, traveler type.
- If details are missing, make reasonable assumptions and list them explicitly.
- Keep a clean, consistent structure so the Reviewer can validate item-by-item.

PLANNING METHOD (follow in order)
1) Extract Constraints
   - Trip length / dates (or infer), total budget (assume USD unless specified), interests (e.g., history/food),
     traveler profile (student/family/solo), pace (relaxed/medium/fast), and any hard constraints (must-see, exclusions).
2) City Cluster Selection
   - Choose a compact set of cities/regions that minimize backtracking and serve the interests/budget.
   - For each chosen city/region, include a 1–2 sentence justification.
3) Day-by-Day Itinerary
   For each day, include:
   - City/Area (with neighborhood when relevant)
   - Activities by period with approximate times:
        Morning (e.g., 09:00–11:30)
        Lunch (time window + neighborhood)
        Afternoon (time window)
        Evening (time window)
   - Locations: specific venues/neighborhoods where reasonable (e.g., “Gothic Quarter”, “Louvre area”).
   - Intra-city logistics: typical mode (walk/metro/bus/rideshare) + rough travel times between activities.
   - Estimated day cost (exclude lodging OR explicitly state your lodging assumption here).
   - Running budget total and affordability flag: On track / Tight / Over.
   - If an intercity transfer occurs this day, clearly mark: mode, typical duration, when it happens.
4) Intercity Transfers (if any)
   - Single concise section listing each move (e.g., Day 3 afternoon: Paris → Lyon by TGV, ~2h).
5) End-of-Trip Summaries
   - Budget Breakdown: Lodging, Intercity transport, In-city transport, Activities/Attractions, Food, and Total.
   - Logistics Notes: typical closures (e.g., many museums closed Mon/Tue), likely reservation points,
     useful passes/cards, seasonal cautions.
   - Assumptions: list all material assumptions (lodging per night, local transit costs, opening-hour norms, etc.).
   - Checks Needed for Reviewer: enumerate concrete fact-checks (opening hours for specific venues on the scheduled day,
     typical ticket prices/discounts, transfer durations, pass/reservation requirements, etc.).

OUTPUT FORMAT (Markdown ONLY; keep headings exactly as below)

## Extracted Constraints
- ...

## City Cluster Plan (with Justifications)
- City A — why it fits (1–2 sentences)
- City B — ...

## Day-by-Day Itinerary
**Day 1 – City A**
- Morning (09:00–11:30): Activity @ Location — brief rationale
- Lunch (12:00–13:00): Place/Area — brief note
- Afternoon (13:30–17:00): Activity @ Location — brief rationale
- Evening (18:30–21:30): Activity @ Location — brief rationale
- Intra-city logistics: (e.g., metro + 15 min) Activity1 → Activity2; (walk 10 min) Activity2 → Dinner
- Est. day cost (excl. lodging if handled separately): $...
- Running budget total: $... (Status: On track/Tight/Over)

(repeat for all days; include intercity transfer blocks on the days they occur)

## Intercity Transfers
- Day X: City A → City B by (train/coach/flight), ~Duration, window: HH:MM–HH:MM

## Budget Breakdown (Totals)
- Lodging (assumption: $X/night × N nights): $...
- Intercity transport: $...
- In-city transport: $...
- Activities/attractions: $...
- Food: $...
- Total: $... (vs. budget $... → On track/Tight/Over)

## Logistics Notes
- ...

## Assumptions
- ...

## Checks Needed for Reviewer
- [ ] Example: “Museum M opening hours on Day 2 (Tuesday) 10:00–13:00; typical ticket price; student discount”
- [ ] Example: “Train duration City A → City B on Day 4 afternoon; need to pre-book?”
- [ ] Example: “Whether Night Market N runs on Sundays in month/season S”
"""

reviewer_agent = Agent(
    name="Reviewer Agent",
    model="openai.gpt-4o",
    instructions=REVIEWER_INSTRUCTIONS.strip(),
    tools=[internet_search]
)

planner_agent = Agent(
    name="Planner Agent",
    model="openai.gpt-4o",
    instructions=PLANNER_INSTRUCTIONS.strip(),
)

# END SOLUTION


# ──────────────────────────────────────────────────────────────────────────────
# Orchestration Helpers
# ──────────────────────────────────────────────────────────────────────────────

def extract_text(result_obj: Any) -> str:
    """
    Pull a usable string from the Runner result in a tolerant way.
    Your Runner may expose final_output, text, or __str__.
    """
    return (
        getattr(result_obj, "final_output", None)
        or getattr(result_obj, "text", None)
        or str(result_obj)
    )


def run_planner(user_text: str) -> str:
    """Run the Planner and return its itinerary text."""
    result = asyncio.run(Runner.run(planner_agent, user_text))
    return extract_text(result)


def run_reviewer(plan_text: str) -> str:
    """Run the Reviewer on the planner’s output and return validated text."""
    result = asyncio.run(Runner.run(reviewer_agent, plan_text))
    return extract_text(result)


# ──────────────────────────────────────────────────────────────────────────────
# Streamlit UI
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Travel Planner", page_icon="✈️")

st.title("✈️ Multi-Agent Travel Planner")
st.caption("Planner → Reviewer (with live tool calls in the sidebar)")

# Sidebar: session controls + examples + dev panel
with st.sidebar:
    st.header("Session")
    if st.button("🔄 Reset conversation"):
        st.session_state.clear()
        st.rerun()

    st.subheader("Try these prompts")
    st.code("Plan a week-long Europe trip for a student on a $1,500 budget who loves history and food")
    st.code("3-day Paris trip for art lovers with $800 budget")

    st.subheader("Developer view")
    show_tools = st.toggle("Show tool activity (live)", value=True)
    if show_tools:
        tool_expander = st.expander("🔧 Tool activity", expanded=True)
        tool_panel = tool_expander.container()
    else:
        tool_panel = st.container()  # inert sink

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []  # list[dict(role, content)]
if "meta" not in st.session_state:
    st.session_state.meta = []      # list[dict(trace)]

# Render history
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and i < len(st.session_state.meta):
            meta = st.session_state.meta[i]
            if meta:
                st.caption(meta.get("trace", ""))

# Chat input
user_input = st.chat_input("Describe your travel (destination, duration, budget, interests)…")

if user_input:
    # Add user message to history and render it
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.meta.append(None)
    with st.chat_message("user"):
        st.markdown(user_input)

    # Assistant output block
    with st.chat_message("assistant"):
        # Live “working…” text and progress bar
        live_msg = st.empty()
        progress = st.progress(0)

        # Per-request tool log (shown in the sidebar)
        tool_events: List[Dict[str, Any]] = []

        def ui_tool_logger(event: Dict[str, Any]) -> None:
            """Append an event and re-render the sidebar log."""
            tool_events.append(event)
            with tool_panel:
                st.markdown("**Recent tool calls**")
                for ev in tool_events[-60:]:  # last N entries
                    t = ev.get("tool", "unknown")
                    et = ev.get("type", "event")
                    if et == "call":
                        st.write(f"• **{t}** called with `{ev.get('args')}`")
                    elif et == "result":
                        st.write(f"• **{t}** result preview:\n\n> {ev.get('preview')}")
                    elif et == "error":
                        st.error(f"• **{t}** error: {ev.get('error')}")
                    elif et == "end":
                        st.write(f"• **{t}** finished")

        # Install the logger so tools can report to the sidebar
        set_tool_logger(ui_tool_logger)

        try:
            # Optional: clear sidebar panel on each run
            with tool_panel:
                st.empty()

            # Step 1: Planner
            with st.status("🧭 Planner Agent: generating itinerary…", expanded=True) as status:
                live_msg.markdown("🧭 Planner Agent is creating your itinerary…")
                plan_text = run_planner(user_input)
                progress.progress(40)
                status.update(label="🔎 Reviewer Agent: validating with live searches…", state="running")

            # Step 2: Reviewer (tool calls will appear live in sidebar)
            live_msg.markdown("🔎 Reviewer Agent is validating the plan with live searches…")
            review_text = run_reviewer(plan_text)
            progress.progress(90)

            # Completed
            live_msg.markdown("✅ Validation complete. Rendering results…")
            time.sleep(0.2)
            progress.progress(100)

            # Final render: show only the validated result, with the raw plan expandable
            st.info("🤖 **Reviewer Agent** (validated)")
            st.markdown(review_text)
            with st.expander("See raw plan from Planner Agent"):
                st.markdown(plan_text)

            # Save only the validated result to history
            st.session_state.messages.append({"role": "assistant", "content": review_text})
            st.session_state.meta.append({"trace": "Planner Agent → Reviewer Agent"})
            st.caption("Planner Agent → Reviewer Agent")

        except Exception as e:
            # Friendly error box
            live_msg.markdown("❌ Something went wrong.")
            err = f"⚠️ Error while processing your request:\n\n```\n{e}\n```"
            st.markdown(err)
            st.session_state.messages.append({"role": "assistant", "content": err})
            st.session_state.meta.append({"trace": "Runtime error."})

        finally:
            # Always remove the logger so it doesn't leak into the next request
            set_tool_logger(None)
