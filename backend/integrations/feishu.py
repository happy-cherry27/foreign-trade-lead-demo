from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request

from fastapi import HTTPException


def feishu_configured() -> bool:
    required = [
        "FEISHU_APP_ID",
        "FEISHU_APP_SECRET",
        "FEISHU_BITABLE_APP_TOKEN",
        "FEISHU_BITABLE_TABLE_ID",
    ]
    return all(os.getenv(key) for key in required)


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.URLError as exc:
        raise HTTPException(status_code=502, detail=f"Feishu request failed: {exc}") from exc


def sync_to_feishu_bitable(lead: dict[str, Any]) -> dict[str, str]:
    if not feishu_configured():
        return {
            "target": "feishu_bitable_demo_fallback",
            "status": "synced",
            "detail": "Feishu environment variables are not configured; recorded as a local demo fallback sync.",
        }

    token_response = post_json(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        {
            "app_id": os.environ["FEISHU_APP_ID"],
            "app_secret": os.environ["FEISHU_APP_SECRET"],
        },
    )
    tenant_token = token_response.get("tenant_access_token")
    if not tenant_token:
        raise HTTPException(status_code=502, detail=f"Feishu token response missing tenant_access_token: {token_response}")

    app_token = os.environ["FEISHU_BITABLE_APP_TOKEN"]
    table_id = os.environ["FEISHU_BITABLE_TABLE_ID"]
    record_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    post_json(
        record_url,
        {
            "fields": {
                "客户姓名": lead.get("name", "unknown"),
                "邮箱": lead.get("email", "unknown"),
                "公司": lead.get("company", "unknown"),
                "国家": lead.get("country", "unknown"),
                "产品需求": lead.get("product_need", "unknown"),
                "预算": lead.get("budget", "unknown"),
                "数量": lead.get("quantity", "unknown"),
                "优先级": lead.get("priority", "medium"),
                "线索评分": lead.get("lead_score", 0),
                "跟进时间": lead.get("follow_up_time", "unknown"),
                "审核状态": lead.get("status", "pending_review"),
            }
        },
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    return {"target": "feishu_bitable", "status": "synced", "detail": "Synced through Feishu Bitable OpenAPI."}
