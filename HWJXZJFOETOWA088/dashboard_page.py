"""
DEMO VARIANT of dashboard_page.py -- identical to the real one except it
calls mock_data.mock_run_conversation() instead of orchestrator's
run_conversation(), and skips get_connection() since there's no real
connection to open. Everything else (Stepper, hero metric, KPI row,
charts, category cards) is the same code.
"""

import streamlit as st

from mock_data import OVERVIEW_QUESTION, mock_run_conversation
from ui_common import (
    brand_header, stat_card, hero_metric, parse_answer, category_color, icon_svg, fmt_money, md_html,
    Stepper, render_comparison_chart, render_donut_chart,
    TEXT_SECONDARY, TEXT_PRIMARY,
)

brand_header("Dashboard", "Standing overview -- DEMO MODE, sample data")

col_refresh, _ = st.columns([1, 6])
refresh_clicked = col_refresh.button("Refresh", icon=":material/refresh:", use_container_width=True)

need_run = refresh_clicked or "overview_result" not in st.session_state

if need_run:
    stepper_placeholder = st.empty()
    stepper = Stepper(stepper_placeholder)
    final_text, call_log = mock_run_conversation(OVERVIEW_QUESTION, on_event=stepper.on_event)
    st.session_state["overview_result"] = {"text": final_text, "call_log": call_log}
    st.session_state["last_result"] = {"text": final_text, "call_log": call_log, "question": OVERVIEW_QUESTION}
    stepper_placeholder.empty()

result = st.session_state.get("overview_result")
parsed = parse_answer(result["text"]) if result else None

if not parsed:
    st.markdown(
        f"<div class='raa-card'><span style='color:{TEXT_SECONDARY}'>"
        f"{'Couldn' + chr(39) + 't parse a structured answer this run -- raw text below.' if result else 'Loading...'}"
        f"</span></div>",
        unsafe_allow_html=True,
    )
    if result:
        st.markdown(f"<div class='raa-card'>{result['text']}</div>", unsafe_allow_html=True)
else:
    metrics = parsed.get("metrics") or {}

    at_risk_val = metrics.get("at_risk")
    if isinstance(at_risk_val, (int, float)):
        gap_val = metrics.get("gap")
        sub = f"against a {fmt_money(gap_val)} forecast gap this quarter" if isinstance(gap_val, (int, float)) else "this quarter"
        hero_metric("Revenue at risk", at_risk_val, sub=sub)

    st.markdown(f"<div class='raa-card'>{parsed.get('executive_summary', '')}</div>", unsafe_allow_html=True)
    st.write("")

    kpi_cols = st.columns(5)
    kpi_defs = [
        ("target", "Target", "#29B5E8"), ("forecast", "Forecast", "#8A6FD6"),
        ("gap", "Gap", "#D97757"), ("at_risk", "At risk", "#E0556F"),
        ("recoverable", "Recoverable", "#3ecf8e"),
    ]
    for col, (key, label, accent) in zip(kpi_cols, kpi_defs):
        stat_card(label, metrics.get(key), accent=accent, column=col)

    st.write("")
    chart_col, donut_col = st.columns([3, 2])

    with chart_col:
        st.markdown("##### Target vs. forecast vs. at risk")
        labels, values, colors = [], [], []
        for key, label, accent in [("target", "Target", "#29B5E8"), ("forecast", "Forecast", "#8A6FD6"),
                                    ("at_risk", "At risk", "#E0556F"), ("recoverable", "Recoverable", "#3ecf8e")]:
            v = metrics.get(key)
            if isinstance(v, (int, float)):
                labels.append(label)
                values.append(v)
                colors.append(accent)
        if values:
            render_comparison_chart(labels, values, colors, height=240)
        else:
            st.caption("No numeric metrics returned this run.")

    root_causes = parsed.get("root_causes") or []
    with donut_col:
        st.markdown("##### Risk by category")
        if root_causes:
            names = [rc.get("category", "?") for rc in root_causes]
            amounts = [rc.get("at_risk_amount", 0) or 0 for rc in root_causes]
            rc_colors = [category_color(n) for n in names]
            if not render_donut_chart(names, amounts, rc_colors, height=240):
                for n, a, c in zip(names, amounts, rc_colors):
                    st.markdown(
                        f"<div class='raa-row'>{icon_svg(n, size=16)}"
                        f"<span style='color:{TEXT_PRIMARY}'>{n}</span>"
                        f"<span style='margin-left:auto;color:{c};font-weight:700;'>{fmt_money(a)}</span></div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.caption("No category breakdown returned this run.")

    if root_causes:
        st.write("")
        st.markdown("##### Category detail")
        cols = st.columns(min(len(root_causes), 4))
        for col, rc in zip(cols, root_causes):
            name = rc.get("category", "?")
            amt = rc.get("at_risk_amount", 0) or 0
            color = category_color(name)
            col.markdown(
                md_html(f"""<div class="raa-card">
                        <div style="display:flex;align-items:center;gap:8px;">
                            {icon_svg(name, size=20)}
                            <span style="color:{TEXT_SECONDARY};font-size:0.8rem;">{name}</span>
                        </div>
                        <div style="font-size:1.2rem;font-weight:700;color:{color};margin-top:6px;">{fmt_money(amt)}</div>
                    </div>"""),
                unsafe_allow_html=True,
            )

st.caption("DEMO MODE -- sample data, no live Snowflake connection. Ask a question on **Ask the Agent** to see it too.")
