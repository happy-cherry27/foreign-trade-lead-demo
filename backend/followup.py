from __future__ import annotations

from typing import Any


def build_reply_draft(data: dict[str, Any]) -> str:
    name = data["name"] if data["name"] != "unknown" else "there"
    product = data["product_need"] if data["product_need"] != "unknown" else "the products you are interested in"
    quantity = data["quantity"] if data["quantity"] != "unknown" else "your expected quantity"

    if data["priority"] == "high":
        return (
            f"Dear {name},\n\n"
            f"Thank you for your urgent inquiry about {product}. We have received your request for {quantity} "
            "and will prioritize the quotation today.\n\n"
            "To prepare an accurate offer, could you please confirm the required specifications, destination port, "
            "and whether you need samples before the bulk order?\n\n"
            "Best regards,\nSales Team"
        )
    if data["priority"] == "medium":
        return (
            f"Dear {name},\n\n"
            f"Thank you for your inquiry about {product}. We can share our catalog, MOQ, price range, and lead time "
            "for your review.\n\n"
            "Could you please confirm your target quantity, budget range, and expected delivery schedule so we can "
            "recommend the most suitable option?\n\n"
            "Best regards,\nSales Team"
        )
    return (
        f"Dear {name},\n\n"
        f"Thank you for contacting us. To better understand your request for {product}, could you please share the "
        "target quantity, application scenario, budget range, and expected purchase timeline?\n\n"
        "Best regards,\nSales Team"
    )


def build_qualification_questions(data: dict[str, Any]) -> list[str]:
    questions: list[str] = []
    if data["quantity"] == "unknown":
        questions.append("Could you confirm the estimated order quantity for this inquiry?")
    if data["budget"] == "unknown":
        questions.append("Could you share your target budget range or acceptable price level?")
    if data["phone"] == "unknown":
        questions.append("Could you provide a phone or WhatsApp number for faster coordination?")
    if data["product_need"] == "unknown":
        questions.append("Could you clarify the exact product model, specification, or use case you need?")
    if data["country"] == "unknown":
        questions.append("Could you confirm the destination country or delivery market?")
    if data["follow_up_time"] in {"unknown", "within 3-5 business days"}:
        questions.append("Do you have an expected delivery timeline or supplier confirmation deadline?")
    return questions[:4]
