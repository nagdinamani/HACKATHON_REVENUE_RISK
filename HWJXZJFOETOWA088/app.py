"""
Entry point for the Streamlit UI. Run with:  streamlit run app.py

This file only sets up page config, global styling, and the sidebar
navigation -- the actual pages live in dashboard_page.py, ask_agent_page.py,
trace_page.py, architecture_page.py (all flat in this same folder, no
subfolders). All of them share state via st.session_state["last_result"],
set whenever the agent is run on the Ask Agent page.
"""

import streamlit as st

from ui_common import inject_css, sidebar_brand

st.set_page_config(page_title="Revenue-at-Risk Agent", layout="wide", page_icon="❄️")
inject_css()
sidebar_brand()

pages = [
    st.Page("dashboard_page.py", title="Dashboard", icon=":material/space_dashboard:", default=True),
    st.Page("ask_agent_page.py", title="Ask the Agent", icon=":material/forum:"),
    st.Page("trace_page.py", title="Reasoning Trace", icon=":material/data_object:"),
    st.Page("architecture_page.py", title="Architecture", icon=":material/account_tree:"),
]

nav = st.navigation(pages)
nav.run()
