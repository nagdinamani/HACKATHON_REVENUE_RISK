"""
DEMO VARIANT -- same UI building blocks as the real ui_common.py, with the
Snowflake-connecting get_connection() removed since the demo pages use
hardcoded mock data and never open a real connection. Everything else
(design tokens, CSS, charts, cards) is unchanged, so the demo looks
identical to the real app.
"""

import json
import re

import streamlit as st

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
SNOWFLAKE_BLUE = "#29B5E8"
SNOWFLAKE_BLUE_DEEP = "#0E7EB0"
CLAUDE_CLAY = "#D97757"
BG = "#0A0E17"
SURFACE = "#121826"
SURFACE_RAISED = "#161D2C"
BORDER = "#222B3D"
TEXT_PRIMARY = "#ECEFF4"
TEXT_SECONDARY = "#9BA4BA"
GRADIENT = f"linear-gradient(90deg, {SNOWFLAKE_BLUE} 0%, {CLAUDE_CLAY} 100%)"


def fmt_money(value) -> str:
    """$125,000,000 reads as a wall of digits and wraps mid-number in a
    narrow card ("$125,000,0" / "00"). Executives read $125.0M -- abbreviate
    everywhere a dollar figure appears, in cards, charts and hero numbers."""
    if not isinstance(value, (int, float)):
        return "--"
    sign = "-" if value < 0 else ""
    v = abs(value)
    if v >= 1_000_000_000:
        return f"{sign}${v / 1_000_000_000:,.1f}B"
    if v >= 1_000_000:
        return f"{sign}${v / 1_000_000:,.1f}M"
    if v >= 1_000:
        return f"{sign}${v / 1_000:,.1f}K"
    return f"{sign}${v:,.0f}"

# The one recurring mark used everywhere the brand appears: a hexagonal
# crystal (Snowflake's own facets) with a single four-point spark at its
# center (Claude) -- own geometry, drawn once, reused at every size instead
# of a different logo treatment per spot.
_BRAND_MARK_BODY = (
    '<path d="M12 2 L20.5 7 V17 L12 22 L3.5 17 V7 Z" stroke="%s" stroke-width="1.4" fill="none" stroke-linejoin="round"/>'
    '<path d="M12 2 V22 M3.5 7 L20.5 17 M20.5 7 L3.5 17" stroke="%s" stroke-width="0.9" opacity="0.55"/>'
    '<path d="M12 9.3 L13.3 11.7 L15.7 12 L13.3 12.3 L12 14.7 L10.7 12.3 L8.3 12 L10.7 11.7 Z" fill="%s" stroke="none"/>'
)


def md_html(html: str) -> str:
    """Collapse a multi-line HTML f-string to one line before handing it to
    st.markdown. Streamlit's markdown pass runs CommonMark rules even with
    unsafe_allow_html=True: a whitespace-only line in the middle of a
    multi-line block (easy to produce by accident -- an f-string expression
    that evaluates to '' leaves just the source indentation on that line)
    ends CommonMark's raw-HTML-block parsing early, and everything after
    reverts to normal Markdown, where a 4-space-indented closing tag then
    renders as a literal code block instead of closing the div. Collapsing
    to one line sidesteps both the blank-line and indentation failure modes
    regardless of what any embedded conditional evaluates to."""
    return " ".join(line.strip() for line in html.strip("\n").split("\n") if line.strip())


def brand_mark_svg(size: int = 28) -> str:
    body = _BRAND_MARK_BODY % (SNOWFLAKE_BLUE, SNOWFLAKE_BLUE, CLAUDE_CLAY)
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">{body}</svg>'
    )


def sidebar_brand():
    """Puts the Snowflake x Claude lockup at the top of the sidebar, above
    the auto-generated page nav -- call once from app.py before st.navigation
    renders, so this ends up first."""
    st.sidebar.markdown(
        md_html(f"""
        <div class="raa-sidebar-brand">
            {brand_mark_svg(30)}
            <div class="raa-sidebar-brand-text">
                <div class="name"><span class="sf">Snowflake</span> <span class="x">&times;</span> <span class="cl">Claude</span></div>
                <div class="tag">Revenue-at-Risk Agent</div>
            </div>
        </div>
        <div class="raa-sidebar-rule"></div>
        """),
        unsafe_allow_html=True,
    )


def hero_metric(label: str, value, accent_from: str = SNOWFLAKE_BLUE, accent_to: str = CLAUDE_CLAY, sub: str = ""):
    """The one bold visual moment on a page -- a large gradient-text headline
    number, used sparingly (currently just the Dashboard's at-risk figure)
    so it stays meaningful instead of competing with the KPI row."""
    text = fmt_money(value)
    sub_html = f"<div class='raa-hero-sub'>{sub}</div>" if sub else ""
    st.markdown(
        md_html(f"""<div class="raa-hero">
                <div class="raa-hero-label">{label}</div>
                <div class="raa-hero-value" style="background-image: linear-gradient(90deg, {accent_from}, {accent_to});">{text}</div>
                {sub_html}
            </div>"""),
        unsafe_allow_html=True,
    )

CATEGORY_META = {
    "opportunities": {"color": "#29B5E8", "icon": "opportunity"},
    "opportunity": {"color": "#29B5E8", "icon": "opportunity"},
    "orders": {"color": "#8A6FD6", "icon": "order"},
    "order": {"color": "#8A6FD6", "icon": "order"},
    "renewals": {"color": "#D97757", "icon": "renewal"},
    "renewal": {"color": "#D97757", "icon": "renewal"},
    "customer renewal": {"color": "#D97757", "icon": "renewal"},
    "billing": {"color": "#5FB89B", "icon": "billing"},
}
DEFAULT_CATEGORY = {"color": "#6B7384", "icon": "default"}

# Small hand-drawn line-icon set (own geometry, not lifted from any icon
# font/library) -- one per risk category, reused everywhere that category
# shows up so color + icon always mean the same thing.
_ICONS = {
    "opportunity": '<path d="M4 16 L10 9 L14 12 L20 5" stroke-linecap="round" stroke-linejoin="round"/><path d="M15 5 H20 V10" stroke-linecap="round" stroke-linejoin="round"/>',
    "order": '<path d="M4 7 L12 3 L20 7 L12 11 Z" stroke-linejoin="round"/><path d="M4 7 V17 L12 21 L20 17 V7" stroke-linejoin="round"/><path d="M12 11 V21" />',
    "renewal": '<path d="M4 12 a8 8 0 0 1 14 -5.5 M18 3 v4 h-4" stroke-linecap="round" stroke-linejoin="round"/><path d="M20 12 a8 8 0 0 1 -14 5.5 M6 21 v-4 h4" stroke-linecap="round" stroke-linejoin="round"/>',
    "billing": '<rect x="5" y="3" width="14" height="18" rx="1.5"/><path d="M8 8 H16 M8 12 H16 M8 16 H12" stroke-linecap="round"/>',
    "default": '<circle cx="12" cy="12" r="8"/>',
}


def icon_svg(category: str, size: int = 20, color: str | None = None) -> str:
    key = (category or "").strip().lower()
    meta = CATEGORY_META.get(key, DEFAULT_CATEGORY)
    icon_key = meta["icon"]
    stroke = color or meta["color"]
    body = _ICONS.get(icon_key, _ICONS["default"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{stroke}" stroke-width="1.6" xmlns="http://www.w3.org/2000/svg">{body}</svg>'
    )


def category_color(category: str) -> str:
    return CATEGORY_META.get((category or "").strip().lower(), DEFAULT_CATEGORY)["color"]


def inject_css():
    # NOTE: Streamlit-in-Snowflake blocks loading *external stylesheets*
    # (an @import of a Google Fonts CSS file counts as one), but explicitly
    # allows fonts/images/media from any HTTPS domain -- so we load the
    # font FILE directly via @font-face instead of @import-ing a stylesheet.
    # See docs.snowflake.com/developer-guide/streamlit/limitations.
    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: 'Inter';
            src: url('https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiA.woff2') format('woff2');
            font-weight: 400 700;
        }}
        html, body, [class*="css"] {{ font-family: 'Inter', -apple-system, sans-serif; font-size: 16px; color: {TEXT_PRIMARY}; }}
        .stApp {{ background-color: {BG}; }}

        /* Streamlit's own top toolbar (Deploy button / menu) -- only exists
           when run locally via `streamlit run` (Snowflake embeds the app in
           Snowsight's own chrome and has no such bar), but when it IS there
           it was rendering stark white against this dark theme. */
        header[data-testid="stHeader"] {{ background: {BG} !important; }}
        div[data-testid="stToolbar"] {{ color: {TEXT_SECONDARY}; }}
        [data-testid="stDecoration"] {{ background: {GRADIENT}; }}

        /* Explicit text color everywhere -- belt-and-suspenders alongside the
           native [theme] config in .streamlit/config.toml. Unstyled markdown
           (plain **bold** headers, captions) was inheriting a washed-out
           default instead of our palette and reading as barely visible. */
        .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown strong, .stMarkdown span,
        div[data-testid="stText"], h1, h2, h3, h4, h5, h6 {{ color: {TEXT_PRIMARY}; }}
        .raa-card, .raa-card * {{ color: {TEXT_PRIMARY}; }}

        /* Base body/markdown text -- was reading too small/basic throughout */
        .stMarkdown p, .stMarkdown li, div[data-testid="stText"] {{ font-size: 1rem; line-height: 1.55; }}
        h1 {{ font-size: 2rem !important; }}
        h2 {{ font-size: 1.5rem !important; }}
        h3, .stMarkdown h3 {{ font-size: 1.2rem !important; }}

        /* Sidebar -- pinned to one width regardless of content, so the font-size
           bump below can never force it wider (that's what blew it up before) */
        section[data-testid="stSidebar"] {{
            background-color: {SURFACE_RAISED}; border-right: 1px solid {BORDER};
            width: 272px !important; min-width: 272px !important; max-width: 272px !important;
        }}
        section[data-testid="stSidebar"] > div {{ width: 272px !important; }}

        .raa-sidebar-brand {{ display: flex; align-items: center; gap: 10px; padding: 18px 20px 14px 20px; }}
        .raa-sidebar-brand-text .name {{ font-weight: 700; font-size: 1.08rem; color: {TEXT_PRIMARY}; }}
        .raa-sidebar-brand-text .name .sf {{ color: {SNOWFLAKE_BLUE}; }}
        .raa-sidebar-brand-text .name .cl {{ color: {CLAUDE_CLAY}; }}
        .raa-sidebar-brand-text .name .x {{ color: {TEXT_SECONDARY}; font-weight: 400; }}
        .raa-sidebar-brand-text .tag {{ font-size: 0.78rem; color: {TEXT_SECONDARY}; margin-top: 1px; }}
        .raa-sidebar-rule {{ height: 2px; margin: 0 20px 10px 20px; background: {GRADIENT}; opacity: 0.6; border-radius: 2px; }}

        /* Nav links -- readable size without resizing the rail, icons tinted
           Snowflake blue at rest and Claude clay on the active page, so the
           two brand colors double as the "where am I" signal */
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {{
            font-size: 1rem !important; font-weight: 500; border-radius: 10px;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] span {{ font-size: 1rem !important; }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {{
            color: {SNOWFLAKE_BLUE} !important; font-size: 1.25rem !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {{
            background: rgba(217, 119, 87, 0.12);
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] [data-testid="stIconMaterial"] {{
            color: {CLAUDE_CLAY} !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] span {{
            color: {TEXT_PRIMARY} !important; font-weight: 600;
        }}

        .raa-card {{
            background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px;
            padding: 18px 20px; font-size: 1rem; line-height: 1.55;
        }}
        .raa-stat {{
            background: {SURFACE}; border: 1px solid {BORDER}; border-left: 3px solid var(--accent, {SNOWFLAKE_BLUE});
            border-radius: 12px; padding: 16px 18px;
        }}
        .raa-stat .label {{ color: {TEXT_SECONDARY}; font-size: 0.85rem; }}
        .raa-stat .value {{ color: {TEXT_PRIMARY}; font-size: 1.75rem; font-weight: 700; margin-top: 3px; }}

        /* The one bold moment per page -- a large gradient headline number */
        .raa-hero {{ padding: 6px 2px 18px 2px; }}
        .raa-hero-label {{ color: {TEXT_SECONDARY}; font-size: 0.95rem; }}
        .raa-hero-value {{
            font-size: 3.2rem; font-weight: 700; line-height: 1.1; margin-top: 2px;
            background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent; color: {SNOWFLAKE_BLUE};
            display: inline-block;
        }}
        .raa-hero-sub {{ color: {TEXT_SECONDARY}; font-size: 0.95rem; margin-top: 4px; }}

        .raa-brand {{
            display: flex; align-items: center; gap: 12px; padding: 8px 2px 16px 2px;
            margin-bottom: 16px;
        }}
        .raa-brand .name {{ font-weight: 700; font-size: 1.3rem; color: {TEXT_PRIMARY}; }}
        .raa-brand .name span.sf {{ color: {SNOWFLAKE_BLUE}; }}
        .raa-brand .name span.cl {{ color: {CLAUDE_CLAY}; }}
        .raa-brand .tag {{ font-size: 0.88rem; color: {TEXT_SECONDARY}; margin-top: 2px; }}
        .raa-brand-rule {{ height: 3px; background: {GRADIENT}; border-radius: 2px; margin: -4px 0 18px 0; opacity: 0.85; }}

        /* Accessibility -- a visible focus ring on every interactive element,
           in the brand blue, since Streamlit's default focus state is faint
           and easy to lose against a dark theme. Keyboard users need this. */
        button:focus-visible, a:focus-visible, textarea:focus-visible, input:focus-visible,
        [data-testid="stSidebarNavLink"]:focus-visible {{
            outline: 2px solid {SNOWFLAKE_BLUE} !important; outline-offset: 2px !important;
            border-radius: 8px;
        }}

        /* Buttons -- one consistent brand treatment instead of Streamlit's
           plain grey default. Primary = filled Snowflake blue (main actions
           like Refresh / Ask); secondary = outline (example-prompt chips). */
        .stButton button {{
            border-radius: 10px; font-weight: 600; font-size: 0.95rem;
            border: 1px solid {BORDER}; background: {SURFACE}; color: {TEXT_PRIMARY};
            transition: border-color 0.15s ease, background 0.15s ease;
        }}
        .stButton button:hover {{ border-color: {SNOWFLAKE_BLUE}; color: {SNOWFLAKE_BLUE}; }}
        .stButton button[kind="primary"] {{
            background: {SNOWFLAKE_BLUE}; border-color: {SNOWFLAKE_BLUE}; color: #04202C;
        }}
        .stButton button[kind="primary"]:hover {{ background: {SNOWFLAKE_BLUE_DEEP}; color: #04202C; }}

        /* Radio-as-tabs (chart-type switcher) -- make it read as a segmented
           control, not a loose row of dots */
        div[role="radiogroup"] {{ gap: 6px; }}
        div[role="radiogroup"] label {{
            background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px;
            padding: 4px 12px; font-size: 0.9rem;
        }}

        /* Links inherit the brand blue instead of Streamlit's default red */
        a {{ color: {SNOWFLAKE_BLUE}; }}

        /* Code blocks (Reasoning Trace SQL) -- align radius/border with the
           rest of the card system instead of Streamlit's square default */
        div[data-testid="stCodeBlock"] {{ border-radius: 10px; border: 1px solid {BORDER}; }}

        /* Headline KPI row — equal-height cards even when one value is longer */
        .raa-stat {{ height: 100%; }}

        .raa-row {{ display: flex; align-items: center; gap: 10px; padding: 8px 0; font-size: 1rem; }}
        .raa-pill {{ display:inline-block; padding:3px 12px; border-radius:999px; font-size:0.82rem; font-weight:600; }}

        /* Messages / alerts -- Streamlit's default st.error/st.info/st.success boxes,
           sized and spaced to match the rest of the UI instead of looking bolted-on */
        div[data-testid="stAlert"] {{ font-size: 1rem; border-radius: 12px; padding: 14px 16px; }}
        div[data-testid="stCaptionContainer"], .stCaption {{ font-size: 0.9rem !important; }}

        /* Chat bubbles (Ask the Agent) -- Claude-style: user bubble right-aligned tint,
           assistant bubble uses the card surface, both bigger and more legible */
        div[data-testid="stChatMessage"] {{
            background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 16px;
            padding: 14px 18px; margin-bottom: 14px; font-size: 1.02rem; line-height: 1.6;
        }}
        div[data-testid="stChatMessage"] p {{ font-size: 1.02rem; }}

        /* Fixed-at-bottom question bar (st.chat_input), Claude-style docked composer */
        div[data-testid="stChatInput"] {{
            background: {BG}; border-top: 1px solid {BORDER}; padding-top: 10px;
        }}
        div[data-testid="stChatInput"] textarea {{
            background: {SURFACE} !important; border: 1px solid {BORDER} !important;
            color: {TEXT_PRIMARY} !important; font-size: 1.05rem !important; border-radius: 14px !important;
        }}

        div[data-testid="stTextArea"] textarea {{ background: {SURFACE}; border: 1px solid {BORDER}; color: {TEXT_PRIMARY}; font-size: 1rem; }}
        .stButton button {{ font-size: 0.95rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def brand_header(title: str, subtitle: str):
    st.markdown(
        md_html(f"""
        <div class="raa-brand">
            {brand_mark_svg(32)}
            <div>
                <div class="name"><span class="sf">Snowflake</span> &times; <span class="cl">Claude</span> -- {title}</div>
                <div class="tag">{subtitle}</div>
            </div>
        </div>
        <div class="raa-brand-rule"></div>
        """),
        unsafe_allow_html=True,
    )


def stat_card(label: str, value, accent: str = SNOWFLAKE_BLUE, column=None):
    target = column if column is not None else st
    text = fmt_money(value)
    title_attr = f' title="${value:,.0f}"' if isinstance(value, (int, float)) else ""
    target.markdown(
        md_html(f"""<div class="raa-stat" style="--accent:{accent}">
                <div class="label">{label}</div>
                <div class="value"{title_attr}>{text}</div>
            </div>"""),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Agent-run plumbing (get_connection() omitted in this demo variant -- the
# demo pages never open a real Snowflake connection, see dashboard_page.py /
# ask_agent_page.py in this folder)
# ---------------------------------------------------------------------------
STAGES = [
    ("schema", "Reading live Snowflake schema"),
    ("semantic", "Loading semantic model (business logic)"),
    ("reasoning", "Agent reasoning -- writing & running SQL"),
    ("synthesis", "Synthesizing final answer"),
]


class Stepper:
    """Renders the live 'agent at work' progress panel, updated in place via
    orchestrator.run_conversation's on_event callback."""

    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.status = {key: "pending" for key, _ in STAGES}
        self.query_count = 0
        self.last_sql = ""
        self.render()

    def render(self):
        rows = []
        n = len(STAGES)
        for i, (key, label) in enumerate(STAGES):
            state = self.status[key]
            if state == "done":
                marker = (
                    f"<span style='width:20px;height:20px;border-radius:50%;background:#3ecf8e;"
                    f"display:inline-flex;align-items:center;justify-content:center;flex:0 0 20px;'>"
                    f"<svg width='11' height='11' viewBox='0 0 24 24' fill='none' stroke='#04231a' "
                    f"stroke-width='3' stroke-linecap='round' stroke-linejoin='round'>"
                    f"<path d='M5 13 L10 18 L19 7'/></svg></span>"
                )
            elif state == "active":
                marker = (
                    f"<span style='width:20px;height:20px;border-radius:50%;border:2px solid {SNOWFLAKE_BLUE};"
                    f"display:inline-flex;align-items:center;justify-content:center;flex:0 0 20px;'>"
                    f"<span style='width:7px;height:7px;border-radius:50%;background:{SNOWFLAKE_BLUE};"
                    f"display:inline-block;'></span></span>"
                )
            else:
                marker = (
                    f"<span style='width:20px;height:20px;border-radius:50%;border:2px solid {BORDER};"
                    f"display:inline-flex;flex:0 0 20px;'></span>"
                )
            connector = ""
            if i < n - 1:
                line_color = "#3ecf8e" if state == "done" else BORDER
                connector = f"<div style='width:2px;height:16px;background:{line_color};margin-left:9px;'></div>"
            extra = ""
            if key == "reasoning" and self.query_count:
                extra = f" &nbsp;<span class='raa-pill' style='background:{SURFACE_RAISED};color:{TEXT_SECONDARY}'>{self.query_count} quer{'y' if self.query_count == 1 else 'ies'} run</span>"
            spin = " &middot; working" if state == "active" else ""
            rows.append(
                f"<div style='display:flex;align-items:center;gap:12px;'>{marker}"
                f"<span style='color:{TEXT_PRIMARY if state != 'pending' else TEXT_SECONDARY};font-size:1rem;'>{label}{spin}</span>{extra}</div>"
                f"{connector}"
            )
        sql_block = ""
        if self.last_sql:
            short = " ".join(self.last_sql.strip().split())
            short = short[:170] + ("..." if len(short) > 170 else "")
            sql_block = f"<div style='margin-top:6px;color:{TEXT_SECONDARY};font-size:0.82rem;padding-left:32px;'>last query: <code>{short}</code></div>"
        self.placeholder.markdown(
            f"<div class='raa-card'>{''.join(rows)}{sql_block}</div>",
            unsafe_allow_html=True,
        )

    def on_event(self, name, payload):
        if name == "loading_schema":
            self.status["schema"] = "active"
        elif name == "schema_loaded":
            self.status["schema"] = "done"
        elif name == "loading_semantic_model":
            self.status["semantic"] = "active"
        elif name == "semantic_model_loaded":
            self.status["semantic"] = "done"
        elif name == "thinking":
            self.status["reasoning"] = "active"
        elif name == "tool_call":
            self.query_count += 1
            self.last_sql = payload.get("sql", "")
        elif name == "final_answer":
            self.status["reasoning"] = "done"
            self.status["synthesis"] = "done"
        self.render()


def render_comparison_chart(labels: list[str], values: list[float], colors: list[str], height: int = 260):
    """Horizontal bar comparison (target/forecast/gap, or category breakdown).
    Tries Plotly first (nicer, gradient-capable) and falls back to Streamlit's
    own built-in bar_chart (zero extra dependency -- guaranteed to work even
    if plotly isn't available in a given Streamlit-in-Snowflake environment,
    since SiS warehouse runtimes only install packages from the Snowflake
    Anaconda channel, not arbitrary PyPI packages)."""
    try:
        import plotly.graph_objects as go
        fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=colors,
                                text=[fmt_money(v) for v in values], textposition="outside",
                                textfont=dict(color=TEXT_PRIMARY)))
        fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10),
                           paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TEXT_PRIMARY, family="Inter, sans-serif"),
                           xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except ImportError:
        import pandas as pd
        st.bar_chart(pd.DataFrame({"amount": values}, index=labels), height=height)


def render_donut_chart(labels: list[str], values: list[float], colors: list[str], height: int = 300):
    try:
        import plotly.graph_objects as go
        # label+percent inside a narrow donut forces Plotly to rotate text to
        # fit the slice, which overlaps neighboring slices at this size --
        # percent only inside, full names in a legend below instead.
        fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.58, marker_colors=colors,
                                textinfo="percent", insidetextorientation="horizontal",
                                textfont=dict(color=TEXT_PRIMARY)))
        fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=40),
                           paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TEXT_PRIMARY, family="Inter, sans-serif"),
                           showlegend=True,
                           legend=dict(orientation="h", yanchor="top", y=-0.08, x=0.5, xanchor="center",
                                       font=dict(size=11, color=TEXT_SECONDARY)))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        return True
    except ImportError:
        return False


def parse_answer(text: str):
    """The model is asked for strict JSON but doesn't always comply --
    extract it if present, return None (never raise) if it can't be found."""
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if not candidate:
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        candidate = brace.group(0) if brace else None
    if candidate:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None
    return None
