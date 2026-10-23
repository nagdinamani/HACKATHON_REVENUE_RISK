"""
DEMO VARIANT of ask_agent_page.py -- identical to the real one except it
calls mock_data.mock_run_conversation() instead of orchestrator's
run_conversation(), and skips get_connection(). Same chat UI, same
rendering logic, same Stepper -- only the data source is fake.
"""

import streamlit as st

from mock_data import mock_run_conversation
from ui_common import (
    brand_header, stat_card, parse_answer, category_color, icon_svg, fmt_money,
    Stepper, render_comparison_chart, render_donut_chart,
    TEXT_SECONDARY,
)

brand_header("Ask the Agent", "One question in -- DEMO MODE, sample data out")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # [{"role": "user"/"assistant", "content": str or dict}]


def _render_assistant_content(content: dict):
    parsed = parse_answer(content["text"])
    if not parsed:
        st.markdown(content["text"])
        return

    st.markdown(
        f"<div class='raa-card' style='margin-bottom:12px;'>{parsed.get('executive_summary', '')}</div>",
        unsafe_allow_html=True,
    )

    metrics = parsed.get("metrics") or {}
    kpi_cols = st.columns(5)
    kpi_defs = [
        ("target", "Target", "#29B5E8"), ("forecast", "Forecast", "#8A6FD6"),
        ("gap", "Gap", "#D97757"), ("at_risk", "At risk", "#E0556F"),
        ("recoverable", "Recoverable", "#3ecf8e"),
    ]
    for col, (key, label, accent) in zip(kpi_cols, kpi_defs):
        stat_card(label, metrics.get(key), accent=accent, column=col)

    metric_labels, metric_values, metric_colors = [], [], []
    for key, label, accent in kpi_defs:
        v = metrics.get(key)
        if isinstance(v, (int, float)):
            metric_labels.append(label)
            metric_values.append(v)
            metric_colors.append(accent)

    root_causes = parsed.get("root_causes") or []

    if root_causes:
        chart_col, donut_col = st.columns([3, 2])

        with chart_col:
            if metric_values:
                st.markdown("**Target vs. forecast vs. at risk**")
                render_comparison_chart(metric_labels, metric_values, metric_colors, height=260)

        names = [rc.get("category", "?") for rc in root_causes]
        amounts = [rc.get("at_risk_amount", 0) or 0 for rc in root_causes]
        colors = [category_color(n) for n in names]
        with donut_col:
            st.markdown("**Risk by category**")
            if not render_donut_chart(names, amounts, colors, height=260):
                st.table({"Category": names, "At-risk amount": [fmt_money(a) for a in amounts]})
    elif metric_values:
        st.markdown("**Target vs. forecast vs. at risk**")
        render_comparison_chart(metric_labels, metric_values, metric_colors, height=260)

    ranked_actions = parsed.get("ranked_actions") or []
    if ranked_actions:
        st.markdown("**Ranked actions**")
        for action in ranked_actions:
            label = action.get("category", action.get("action", "?")) if isinstance(action, dict) else action
            detail = action if isinstance(action, str) else action.get("action", "")
            st.markdown(
                f"<div class='raa-card' style='margin-bottom:8px;padding:12px 16px;'>"
                f"<b>{label}</b><br><span style='color:{TEXT_SECONDARY}'>{detail}</span></div>",
                unsafe_allow_html=True,
            )

    st.caption(f"Full SQL + results: see **Reasoning Trace** ({len(content['call_log'])} queries).")


def _run_question(question: str):
    st.session_state.chat_history.append({"role": "user", "content": question})
    stepper_placeholder = st.empty()
    stepper = Stepper(stepper_placeholder)
    final_text, call_log = mock_run_conversation(question, on_event=stepper.on_event)
    stepper_placeholder.empty()
    content = {"text": final_text, "call_log": call_log}
    st.session_state.chat_history.append({"role": "assistant", "content": content})
    st.session_state["last_result"] = {"text": final_text, "call_log": call_log, "question": question}


# Suggested-prompt chips -- only before the first message, Claude-style
clicked_example = None
if not st.session_state.chat_history:
    st.markdown(
        f"<p style='color:{TEXT_SECONDARY};font-size:0.95rem;margin-bottom:6px;'>Try asking:</p>",
        unsafe_allow_html=True,
    )
    examples = [
        "Give me the overall revenue-at-risk picture for this quarter.",
        "Which category is the biggest driver of at-risk revenue?",
        "What's recoverable if we act now?",
    ]
    chip_cols = st.columns(len(examples))
    for col, ex in zip(chip_cols, examples):
        label = ex if len(ex) <= 44 else ex[:41] + "..."
        if col.button(label, key=f"chip_{hash(ex)}", use_container_width=True):
            clicked_example = ex

# Render chat history
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑‍💼"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant", avatar="❄️"):
            _render_assistant_content(msg["content"])

# Fixed-at-bottom composer, pinned to the viewport the same way Claude's is
typed_question = st.chat_input("Ask about revenue at risk...")
question = typed_question or clicked_example

if question:
    with st.chat_message("user", avatar="🧑‍💼"):
        st.write(question)
    with st.chat_message("assistant", avatar="❄️"):
        _run_question(question)
        _render_assistant_content(st.session_state.chat_history[-1]["content"])
