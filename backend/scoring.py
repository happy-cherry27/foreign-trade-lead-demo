from __future__ import annotations

from typing import Any
import re


def build_score(data: dict[str, Any], text: str) -> tuple[int, dict[str, int | str]]:
    lowered = text.lower()
    urgency_score = 25 if data["priority"] == "high" else 15 if data["priority"] == "medium" else 5

    commercial_value_score = 0
    if data["budget"] != "unknown":
        commercial_value_score += 12
    if data["quantity"] != "unknown":
        commercial_value_score += 8
    if any(term in lowered for term in ["confirm supplier", "purchase", "buy", "quotation", "quote"]):
        commercial_value_score += 5
    commercial_value_score = min(commercial_value_score, 25)

    contactability_score = 0
    for field, weight in {"email": 7, "phone": 5, "company": 4, "country": 4}.items():
        if data[field] != "unknown":
            contactability_score += weight

    product_clarity_score = 15 if data["product_need"] != "unknown" else 4
    market_fit_score = 10 if data["country"] != "unknown" else 3

    risk_penalty = 0
    if data["email"] != "unknown" and re.search(r"@(gmail|hotmail|yahoo|outlook)\.", data["email"], re.IGNORECASE):
        risk_penalty += 5
    missing_fields = sum(
        1
        for field in ["email", "company", "country", "product_need", "budget", "quantity"]
        if data[field] == "unknown"
    )
    risk_penalty += min(15, missing_fields * 2)

    score = max(
        0,
        min(
            100,
            urgency_score
            + commercial_value_score
            + contactability_score
            + product_clarity_score
            + market_fit_score
            - risk_penalty,
        ),
    )
    label = "hot" if score >= 80 else "warm" if score >= 60 else "nurture" if score >= 40 else "qualify first"
    return score, {
        "urgency": urgency_score,
        "commercial_value": commercial_value_score,
        "contactability": contactability_score,
        "product_clarity": product_clarity_score,
        "market_fit": market_fit_score,
        "risk_penalty": risk_penalty,
        "label": label,
    }
