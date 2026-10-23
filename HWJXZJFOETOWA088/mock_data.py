"""
DEMO VARIANT -- stands in for orchestrator.run_conversation(). Returns the
exact same shape the real agent returns -- (final_text, call_log) where
final_text is a JSON string ui_common.parse_answer() can parse, and
call_log is a list of {"tool", "input", "result"} entries exactly like
tools.run_sql()'s real output -- so dashboard_page.py, ask_agent_page.py,
and trace_page.py (unmodified, copied as-is from the real app) all work
against this without knowing it's fake.

Swap this module out for the real orchestrator once the backend is ready --
nothing in ui_common.py or trace_page.py needs to change either way.
"""

import time

OVERVIEW_QUESTION = (
    "Give me the overall revenue-at-risk picture for this quarter: target, "
    "forecast, the gap, total at risk, total recoverable, and the breakdown "
    "by category (opportunities, orders, renewals, billing)."
)

_OVERVIEW_TEXT = """```json
{
  "executive_summary": "About $420K is at risk this quarter against a $1.25M target, with roughly $265K of that estimated recoverable through timely intervention. Opportunities and Renewals together account for over two-thirds of total exposure.",
  "metrics": {"target": 1250000, "forecast": 1050000, "gap": 200000, "at_risk": 420000, "recoverable": 265000},
  "root_causes": [
    {"category": "Opportunities", "at_risk_amount": 180000},
    {"category": "Orders", "at_risk_amount": 95000},
    {"category": "Renewals", "at_risk_amount": 110000},
    {"category": "Billing", "at_risk_amount": 35000}
  ],
  "ranked_actions": [
    {"category": "Opportunities", "action": "Escalate stalled legal-review deals -- $95K tied up, oldest 40+ days in stage."},
    {"category": "Renewals", "action": "Prioritize outreach to accounts with declining usage and no recurring-deposit-style engagement signal."}
  ]
}
```"""

_OVERVIEW_CALL_LOG = [
    {
        "tool": "run_sql",
        "input": {"sql": (
            "SELECT SUM(target_revenue) AS target, SUM(forecast_revenue) AS forecast,\n"
            "       SUM(target_revenue) - SUM(forecast_revenue) AS gap\n"
            "FROM FACT_REVENUE_PLAN\n"
            "WHERE period_month BETWEEN '2026-10-01' AND '2026-12-31';"
        )},
        "result": {"row_count": 1, "rows": [{"TARGET": 1250000, "FORECAST": 1050000, "GAP": 200000}]},
    },
    {
        "tool": "run_sql",
        "input": {"sql": (
            "SELECT risk_reason, SUM(opportunity_amount) AS at_risk\n"
            "FROM FACT_OPPORTUNITY\n"
            "WHERE opportunity_status = 'Open' AND risk_reason IS NOT NULL\n"
            "GROUP BY risk_reason\n"
            "ORDER BY at_risk DESC;"
        )},
        "result": {"row_count": 3, "rows": [
            {"RISK_REASON": "Legal review stalled", "AT_RISK": 95000},
            {"RISK_REASON": "Executive approval pending", "AT_RISK": 60000},
            {"RISK_REASON": "Stakeholder engagement stalled", "AT_RISK": 25000},
        ]},
    },
]

_CATEGORY_TEXT = """```json
{
  "executive_summary": "Opportunities is the single biggest driver of at-risk revenue at $180K, mostly stalled in legal review -- followed by Renewals at $110K, largely accounts with declining usage.",
  "metrics": {"at_risk": 420000, "recoverable": 265000},
  "root_causes": [
    {"category": "Opportunities", "at_risk_amount": 180000},
    {"category": "Renewals", "at_risk_amount": 110000},
    {"category": "Orders", "at_risk_amount": 95000},
    {"category": "Billing", "at_risk_amount": 35000}
  ]
}
```"""

_CATEGORY_CALL_LOG = [
    {
        "tool": "run_sql",
        "input": {"sql": (
            "SELECT 'Opportunities' AS category, SUM(opportunity_amount) AS at_risk FROM FACT_OPPORTUNITY WHERE risk_reason IS NOT NULL\n"
            "UNION ALL\n"
            "SELECT 'Renewals', SUM(renewal_arr * (1 - COALESCE(renewal_probability, 0))) FROM FACT_CUSTOMER_HEALTH\n"
            "UNION ALL\n"
            "SELECT 'Orders', SUM(booked_value) FROM FACT_ORDER WHERE risk_reason IS NOT NULL\n"
            "UNION ALL\n"
            "SELECT 'Billing', SUM(amount) FROM FACT_BILLING WHERE billing_status = 'Exception';"
        )},
        "result": {"row_count": 4, "rows": [
            {"CATEGORY": "Opportunities", "AT_RISK": 180000},
            {"CATEGORY": "Renewals", "AT_RISK": 110000},
            {"CATEGORY": "Orders", "AT_RISK": 95000},
            {"CATEGORY": "Billing", "AT_RISK": 35000},
        ]},
    },
]


def mock_run_conversation(question: str, on_event=None):
    """Drop-in stand-in for orchestrator.run_conversation(conn, question,
    on_event). Fires the same on_event sequence the real Stepper expects, so
    the live 'agent at work' UI animates exactly like the real run, then
    returns canned (final_text, call_log). No real connection is opened."""
    on_event = on_event or (lambda *a, **k: None)

    on_event("loading_schema", None)
    time.sleep(0.25)
    on_event("schema_loaded", None)

    on_event("loading_semantic_model", None)
    time.sleep(0.2)
    on_event("semantic_model_loaded", None)

    on_event("thinking", None)
    time.sleep(0.3)

    is_category_question = "categor" in question.lower() or "driver" in question.lower() or "biggest" in question.lower()
    text, call_log = (_CATEGORY_TEXT, _CATEGORY_CALL_LOG) if is_category_question else (_OVERVIEW_TEXT, _OVERVIEW_CALL_LOG)

    for entry in call_log:
        on_event("tool_call", {"tool": entry["tool"], "sql": entry["input"]["sql"]})
        time.sleep(0.15)

    on_event("final_answer", text)
    return text, call_log
