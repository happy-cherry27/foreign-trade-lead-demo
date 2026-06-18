from __future__ import annotations

import re
from typing import Any

from .followup import build_qualification_questions, build_reply_draft
from .scoring import build_score


def first_match(patterns: list[str], text: str, default: str = "unknown") -> str:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1) if match.groups() else match.group(0)
            return value.strip(" .,:;")
    return default


def source_snippet(value: str, text: str) -> str:
    if value == "unknown":
        return ""
    index = text.lower().find(value.lower())
    if index < 0:
        return value
    start = max(0, index - 42)
    end = min(len(text), index + len(value) + 42)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def normalize_name(value: str) -> str:
    parts = [part for part in value.split() if "@" not in part]
    return " ".join(parts[:3]) or "unknown"


def normalize_company(value: str) -> str:
    cleaned = re.sub(
        r"\s+(?:in|from)\s+(Germany|United States|USA|Canada|Australia|United Kingdom|UK|France|Italy|Spain|Brazil|India|UAE|Saudi Arabia|Mexico|Netherlands)\b.*$",
        "",
        value,
        flags=re.IGNORECASE,
    )
    return cleaned.strip(" .,:;") or "unknown"


def infer_country(text: str) -> str:
    countries = [
        "Germany",
        "United States",
        "USA",
        "Canada",
        "Australia",
        "United Kingdom",
        "UK",
        "France",
        "Italy",
        "Spain",
        "Brazil",
        "India",
        "UAE",
        "Saudi Arabia",
        "Mexico",
        "Netherlands",
    ]
    for country in countries:
        if re.search(rf"\b{re.escape(country)}\b", text, re.IGNORECASE):
            return "United States" if country == "USA" else "United Kingdom" if country == "UK" else country
    return "unknown"


def infer_priority(text: str) -> tuple[str, str]:
    lowered = text.lower()
    high_signals = ["urgent", "asap", "immediately", "this week", "deadline", "within 3 days"]
    medium_signals = ["quotation", "quote", "price", "catalog", "sample", "lead time"]
    if any(signal in lowered for signal in high_signals):
        return "high", "Email contains urgent timing signals such as ASAP, deadline, or this week."
    if any(signal in lowered for signal in medium_signals):
        return "medium", "Email asks for quote, price, sample, catalog, or lead time."
    return "low", "Email has limited buying intent signals."


def infer_follow_up_time(priority: str, text: str) -> tuple[str, str]:
    lowered = text.lower()
    if priority == "high":
        if "within 3 days" in lowered or "immediately" in lowered or "asap" in lowered:
            return "same day", "Urgent words indicate the sales team should reply today."
        return "within 24 hours", "High-priority inquiry should be handled within 24 hours."
    if priority == "medium":
        return "within 2 business days", "Buying intent exists, but timing is not critical."
    return "within 3-5 business days", "Inquiry needs qualification before sales invests urgent effort."


def build_field_evidence(data: dict[str, Any], text: str) -> dict[str, dict[str, Any]]:
    confidence_by_field = {
        "email": 0.95 if data["email"] != "unknown" else 0.15,
        "phone": 0.9 if data["phone"] != "unknown" else 0.15,
        "name": 0.82 if data["name"] != "unknown" else 0.2,
        "company": 0.78 if data["company"] != "unknown" else 0.2,
        "country": 0.75 if data["country"] != "unknown" else 0.2,
        "product_need": 0.72 if data["product_need"] != "unknown" else 0.2,
        "budget": 0.85 if data["budget"] != "unknown" else 0.2,
        "quantity": 0.88 if data["quantity"] != "unknown" else 0.2,
        "priority": 0.78,
        "follow_up_time": 0.74,
    }
    return {
        field: {
            "value": data[field],
            "confidence": confidence,
            "source_snippet": source_snippet(str(data[field]), text)
            if field not in {"priority", "follow_up_time"}
            else "Inferred from urgency, quote, timing, and buying-intent signals.",
        }
        for field, confidence in confidence_by_field.items()
    }


def extract_lead(raw_email: str) -> dict[str, Any]:
    text = raw_email.strip()
    email = first_match([r"[\w.+-]+@[\w-]+\.[\w.-]+"], text)
    phone = first_match([r"(\+?\d[\d\s().-]{7,}\d)"], text)
    name = first_match(
        [
            r"(?:Best regards|Regards|Sincerely|Thanks|Thank you),?\s*\n\s*([A-Z][A-Za-z .'-]{1,40})",
            r"(?:I am|I'm|This is)\s+([A-Z][A-Za-z .'-]{1,40})(?:\s+(?:from|at)\b|[,.]|\n)",
            r"Name:\s*([^\n]+)",
        ],
        text,
    )
    name = normalize_name(name) if name != "unknown" else name
    company = first_match(
        [
            r"(?:from|at)\s+([A-Z][A-Za-z0-9&.,\- ]{2,60}?)(?:\s+(?:in|from)\s+[A-Z][A-Za-z ]+|\.|,|\n)",
            r"Company:\s*([^\n]+)",
        ],
        text,
    )
    company = normalize_company(company) if company != "unknown" else company
    product_need = first_match(
        [
            r"(?:interested in|looking for|need|purchase|buy)\s+([A-Za-z0-9,\-\s]{3,80})(?:\.|,|\n)",
            r"(?:quotation for|quote for|price for)\s+([A-Za-z0-9,\-\s]{3,80})(?:\.|,|\n)",
        ],
        text,
    )
    quantity = first_match([r"(\d{2,6}\s*(?:pcs|pieces|units|sets|containers|cartons))"], text)
    budget = first_match(
        [
            r"(?:budget is|budget around|budget:)\s*(\$?[0-9,]+(?:\s*-\s*\$?[0-9,]+)?)",
            r"(\$[0-9,]+(?:\s*-\s*\$[0-9,]+)?)",
        ],
        text,
    )
    country = infer_country(text)
    priority, priority_evidence = infer_priority(text)
    follow_up_time, follow_up_time_evidence = infer_follow_up_time(priority, text)
    urgency = "urgent" if priority == "high" else "normal" if priority == "medium" else "low"

    known_fields = [email, phone, name, company, product_need, quantity, budget, country]
    known_count = sum(1 for value in known_fields if value != "unknown")
    confidence = round(0.35 + known_count / len(known_fields) * 0.55, 2)
    follow_up = (
        "Reply within 24 hours with quotation, lead time, and two clarifying questions."
        if priority == "high"
        else "Send product catalog, price range, and ask for quantity/use case."
        if priority == "medium"
        else "Ask for product details and confirm whether there is a purchase timeline."
    )

    extracted = {
        "name": name,
        "email": email,
        "company": company,
        "country": country,
        "phone": phone,
        "product_need": product_need,
        "budget": budget,
        "quantity": quantity,
        "urgency": urgency,
        "priority": priority,
        "follow_up_time": follow_up_time,
        "follow_up_suggestion": follow_up,
        "confidence": confidence,
        "evidence": [
            priority_evidence,
            follow_up_time_evidence,
            f"Detected email: {email}" if email != "unknown" else "Email address is missing.",
            f"Detected country: {country}" if country != "unknown" else "Country is missing or implicit.",
            f"Detected product need: {product_need}" if product_need != "unknown" else "Product need is unclear.",
        ],
        "model_name": "rule-based-mock-extractor-v0.1",
    }
    lead_score, score_breakdown = build_score(extracted, text)
    extracted["lead_score"] = lead_score
    extracted["score_breakdown"] = score_breakdown
    extracted["reply_draft"] = build_reply_draft(extracted)
    extracted["qualification_questions"] = build_qualification_questions(extracted)
    extracted["field_evidence"] = build_field_evidence(extracted, text)
    extracted["next_actions"] = [
        f"Handle as {score_breakdown['label']} lead.",
        follow_up,
        "Human reviewer should confirm missing or low-confidence fields before CRM sync.",
    ]
    return extracted
