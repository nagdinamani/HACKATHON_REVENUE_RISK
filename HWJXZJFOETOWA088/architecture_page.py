"""
Architecture page -- a static one-pager explaining the pipeline, for anyone
who walks up without you narrating. No agent calls happen here.
"""

import streamlit as st

from ui_common import brand_header, md_html, TEXT_SECONDARY, SURFACE, BORDER, SNOWFLAKE_BLUE, CLAUDE_CLAY

brand_header("Architecture", "How a question turns into a grounded, cited answer")

STEPS = [
    ("1", "Live schema introspection", SNOWFLAKE_BLUE,
     "On every question, INFORMATION_SCHEMA.COLUMNS is queried live in Snowflake -- the agent always sees the real table/column names, never a stale reference doc."),
    ("2", "Semantic model", CLAUDE_CLAY,
     "A generated semantic-model YAML is the single source of what 'at risk' means per category -- every measure, filter, and threshold. Nothing about business logic is hardcoded in this app."),
    ("3", "Agent reasoning (Claude / Gemini on Vertex AI)", "#8A6FD6",
     "Given the live schema + semantic model, the model plans, writes its own SQL, and decides what to query -- no fixed query file per question."),
    ("4", "run_sql tool -> Snowflake", "#3ecf8e",
     "Every SQL statement actually executes against Snowflake through one guarded, read-only tool. Every dollar figure in the final answer traces back to a real query result."),
    ("5", "Grounded answer", "#E0556F",
     "The model synthesizes an executive answer -- summary, KPIs, root causes, ranked actions, evidence -- citing which query produced each figure."),
]

for num, title, color, desc in STEPS:
    st.markdown(
        md_html(f"""<div class="raa-card" style="display:flex; gap:16px; align-items:flex-start; margin-bottom:10px;">
                <div style="min-width:34px;height:34px;border-radius:50%;background:{color}22;
                            color:{color};font-weight:700;display:flex;align-items:center;justify-content:center;">{num}</div>
                <div>
                    <div style="font-weight:600;color:#E8EAED;">{title}</div>
                    <div style="color:{TEXT_SECONDARY};font-size:0.9rem;margin-top:2px;">{desc}</div>
                </div>
            </div>"""),
        unsafe_allow_html=True,
    )

st.write("")
st.markdown(
    md_html(f"""<div class="raa-card" style="background:{SURFACE};border:1px dashed {BORDER};">
            <b>Why no fixed SQL file per question?</b><br>
            <span style="color:{TEXT_SECONDARY};">
            Earlier versions had one pre-written query per risk category, checked against the kit's
            reference schema. That reference schema didn't match what was actually loaded in
            Snowflake -- wrong database, then wrong column names, more than once. Instead of
            maintaining fixed queries against documentation that kept turning out wrong, the agent
            now reads the real schema and the semantic model live, every run, and writes its own SQL.
            </span>
        </div>"""),
    unsafe_allow_html=True,
)
