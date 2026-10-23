"""
Reasoning Trace page -- every SQL query the agent wrote and ran for the
most recent question, in a fixed-height scrollable panel (not a page-length
scroll). This is the "prove it's not hardcoded" page for judges, so the
actual returned rows need to be legible, not a collapsed debug blob.
"""

import streamlit as st

from ui_common import brand_header, md_html, TEXT_SECONDARY, TEXT_PRIMARY, SNOWFLAKE_BLUE, BORDER

brand_header("Reasoning Trace", "Every query the agent wrote and ran against live Snowflake data")

result = st.session_state.get("last_result")

if not result:
    st.markdown(
        f"<div class='raa-card'><span style='color:{TEXT_SECONDARY}'>"
        f"No run yet -- ask something on <b>Ask the Agent</b> first.</span></div>",
        unsafe_allow_html=True,
    )
else:
    call_log = result["call_log"]
    total_rows = sum(e["result"].get("row_count", 0) for e in call_log if "error" not in e["result"])
    error_count = sum(1 for e in call_log if "error" in e["result"])

    st.markdown(
        md_html(f"""<div class="raa-card" style="margin-bottom:16px;">
                <div style="color:{TEXT_SECONDARY};font-size:0.9rem;">Question</div>
                <div style="font-size:1.05rem;font-weight:600;margin-top:2px;">"{result["question"]}"</div>
                <div style="display:flex;gap:28px;margin-top:14px;">
                    <div><div style="font-size:1.4rem;font-weight:700;color:{SNOWFLAKE_BLUE};">{len(call_log)}</div>
                         <div style="color:{TEXT_SECONDARY};font-size:0.85rem;">quer{"y" if len(call_log) == 1 else "ies"} run</div></div>
                    <div><div style="font-size:1.4rem;font-weight:700;color:#3ecf8e;">{total_rows}</div>
                         <div style="color:{TEXT_SECONDARY};font-size:0.85rem;">row(s) returned</div></div>
                    {f'<div><div style="font-size:1.4rem;font-weight:700;color:#E0556F;">{error_count}</div><div style="color:{TEXT_SECONDARY};font-size:0.85rem;">failed</div></div>' if error_count else ''}
                </div>
            </div>"""),
        unsafe_allow_html=True,
    )

    with st.container(height=640):
        if not call_log:
            st.markdown(
                f"<div class='raa-card'><span style='color:{TEXT_SECONDARY}'>"
                f"The agent answered without running any SQL.</span></div>",
                unsafe_allow_html=True,
            )
        n = len(call_log)
        for i, entry in enumerate(call_log, 1):
            # Native bordered container -- actually groups the code/table/error
            # widgets inside one visual card (raw HTML divs can't span across
            # separate st.* calls the way they can within a single markdown call).
            with st.container(border=True):
                res = entry["result"]
                status_color = "#E0556F" if "error" in res else "#3ecf8e"
                status_text = "failed" if "error" in res else f"{res.get('row_count', 0)} row(s)"
                st.markdown(
                    md_html(f"""<div style="display:flex;align-items:center;justify-content:space-between;">
                            <div style="font-weight:600;color:{TEXT_PRIMARY};">Query {i} of {n}</div>
                            <span class="raa-pill" style="background:{status_color}22;color:{status_color};">{status_text}</span>
                        </div>"""),
                    unsafe_allow_html=True,
                )
                st.code(entry["input"].get("sql", ""), language="sql")

                if "error" in res:
                    st.error(res["error"])
                else:
                    rows = res.get("rows") or []
                    if rows:
                        st.dataframe(rows, use_container_width=True, height=min(38 * (len(rows) + 1), 280))
                    else:
                        st.caption("Query ran successfully and returned no rows.")
            st.write("")
