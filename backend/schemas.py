from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    raw_email: str = Field(min_length=10)


class LeadCreate(BaseModel):
    raw_email: str
    extracted: dict[str, Any]
    source_channel: str = "manual"


class ReviewRequest(BaseModel):
    action: str = Field(pattern="^(confirmed|rejected)$")
    updates: dict[str, Any] = Field(default_factory=dict)
    reviewer_note: str = ""


class EmailWebhookRequest(BaseModel):
    subject: str = ""
    sender: str = ""
    body: str = Field(min_length=10)
    source: str = "n8n"
    channel: str = "email"


class WechatExtractRequest(BaseModel):
    chat_text: str = Field(min_length=10)
    source: str = "manual"
    channel: str = "wechat"


class BatchEmailItem(BaseModel):
    filename: str = "email.txt"
    content: str = Field(min_length=10)


class BatchImportRequest(BaseModel):
    emails: list[BatchEmailItem]
