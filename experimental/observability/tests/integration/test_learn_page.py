from __future__ import annotations


def test_learn_page_returns_200_and_contains_required_sections(client):
    r = client.get("/learn")
    assert r.status_code == 200
    text = r.text

    required = [
        "WHAT IS STATELOCK",
        "WHAT PROBLEM IT SOLVES",
        "HOW IT WORKS",
        "QUICK START",
        "KEY CONCEPTS",
        "TELEMETRY EXPLANATION",
        "METRICS EXPLANATION",
        "ALARM EXPLANATIONS",
    ]
    for marker in required:
        assert marker in text
