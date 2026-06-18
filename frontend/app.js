const sampleEmails = {
  complete: `Subject: Inquiry for office chairs

Hello,

This is Anna from Bright Home GmbH in Germany. We are interested in ergonomic office chairs for our new distribution channel.

Could you send quotation for 500 units and share lead time? Our budget is around $18,000 and we hope to confirm supplier this week.

Best regards,
Anna Keller
anna.keller@brighthome.de
+49 30 1234 7788`,
  missing: `Subject: Product catalog request

Dear Sales Team,

I am Marco from CasaNova Trading in Italy. We are looking for outdoor dining tables for our retail stores.

Please send your product catalog, MOQ, and available colors. We are still checking the quantity and budget internally.

Regards,
Marco Bianchi
marco@casanova-trading.it`,
  urgent: `Subject: Urgent quotation needed

Hi,

This is Daniel at NorthPeak Supplies from Canada. We need 1200 sets of metal storage racks for a warehouse project.

Please quote as soon as possible. Our deadline is within 3 days because the client wants to confirm supplier immediately.

Thanks,
Daniel Smith
daniel.smith@northpeak.ca
+1 416 555 9088`,
};

const state = {
  extracted: null,
  rawEmail: "",
  selectedLeadId: null,
};

const fields = [
  ["name", "客户姓名"],
  ["email", "邮箱"],
  ["company", "公司"],
  ["country", "国家"],
  ["phone", "电话"],
  ["product_need", "产品需求"],
  ["budget", "预算"],
  ["quantity", "数量"],
  ["urgency", "紧急程度"],
  ["priority", "优先级"],
  ["follow_up_time", "适合跟进时间"],
  ["follow_up_suggestion", "跟进建议"],
  ["reply_draft", "英文回复草稿"],
];

const editableFields = fields.map(([key]) => key);

const emailInput = document.querySelector("#emailInput");
const batchInput = document.querySelector("#batchInput");
const extractBtn = document.querySelector("#extractBtn");
const saveBtn = document.querySelector("#saveBtn");
const batchImportBtn = document.querySelector("#batchImportBtn");
const sampleButtons = document.querySelectorAll(".sample-btn");
const exportBtn = document.querySelector("#exportBtn");
const refreshBtn = document.querySelector("#refreshBtn");
const statusText = document.querySelector("#statusText");
const resultGrid = document.querySelector("#resultGrid");
const evidenceList = document.querySelector("#evidenceList");
const scoreSummary = document.querySelector("#scoreSummary");
const scoreBreakdownList = document.querySelector("#scoreBreakdownList");
const replyDraftText = document.querySelector("#replyDraftText");
const qualificationQuestionList = document.querySelector("#qualificationQuestionList");
const confidenceBadge = document.querySelector("#confidenceBadge");
const leadList = document.querySelector("#leadList");
const statusFilter = document.querySelector("#statusFilter");
const reviewForm = document.querySelector("#reviewForm");
const detailStatus = document.querySelector("#detailStatus");
const rawEmailText = document.querySelector("#rawEmailText");
const timelineList = document.querySelector("#timelineList");
const confirmBtn = document.querySelector("#confirmBtn");
const rejectBtn = document.querySelector("#rejectBtn");
const syncFeishuBtn = document.querySelector("#syncFeishuBtn");

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.style.color = isError ? "#9a2f2f" : "#65757b";
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

function scoreLabel(score) {
  if (score >= 80) return "hot";
  if (score >= 60) return "warm";
  if (score >= 40) return "nurture";
  return "qualify first";
}

function parseJson(value, fallback = {}) {
  if (!value) return fallback;
  if (typeof value === "object") return value;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function clearChildren(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function appendText(parent, tagName, text, className = "") {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  node.textContent = text;
  parent.appendChild(node);
  return node;
}

function renderExtracted(data) {
  clearChildren(resultGrid);
  fields.forEach(([key, label]) => {
    const isLongField = ["reply_draft", "follow_up_suggestion"].includes(key);
    const evidence = data.field_evidence?.[key] || {};
    const card = document.createElement("article");
    card.className = isLongField ? "field-card field-card-wide field-card-long" : "field-card";
    const head = document.createElement("div");
    head.className = "field-card-head";
    appendText(head, "strong", label);
    appendText(head, "span", `${Math.round((evidence.confidence ?? data.confidence ?? 0) * 100)}%`);
    card.appendChild(head);
    appendText(card, "p", data[key] || "unknown", isLongField ? "field-card-text" : "");
    appendText(card, "small", evidence.source_snippet || "No direct source snippet; inferred from email context.");
    resultGrid.appendChild(card);
  });

  clearChildren(evidenceList);
  (data.next_actions || data.evidence || []).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    evidenceList.appendChild(li);
  });

  const priority = data.priority || "medium";
  const score = Number(data.lead_score || 0);
  confidenceBadge.className = `badge ${priority}`;
  confidenceBadge.textContent = `评分 ${score} · ${scoreLabel(score)}`;

  clearChildren(scoreSummary);
  const scoreHead = document.createElement("div");
  appendText(scoreHead, "span", "Lead Score");
  appendText(scoreHead, "strong", String(score));
  scoreSummary.appendChild(scoreHead);
  appendText(
    scoreSummary,
    "p",
    `${scoreLabel(score)} · ${data.follow_up_time || "unknown"} · confidence ${data.confidence ?? "unknown"}`
  );

  clearChildren(scoreBreakdownList);
  Object.entries(data.score_breakdown || {}).forEach(([key, value]) => {
    const li = document.createElement("li");
    li.textContent = `${key}: ${value}`;
    scoreBreakdownList.appendChild(li);
  });
  replyDraftText.textContent = data.reply_draft || "未生成。";

  clearChildren(qualificationQuestionList);
  const questions = data.qualification_questions || [];
  if (!questions.length) {
    const li = document.createElement("li");
    li.textContent = "关键字段较完整，暂无必须追问。";
    qualificationQuestionList.appendChild(li);
  }
  questions.forEach((question) => {
    const li = document.createElement("li");
    li.textContent = question;
    qualificationQuestionList.appendChild(li);
  });
}

async function extractLead() {
  const rawEmail = emailInput.value.trim();
  if (!rawEmail) {
    setStatus("请先粘贴客户邮件。", true);
    return;
  }
  extractBtn.disabled = true;
  setStatus("正在抽取客户线索...");
  try {
    const data = await api("/api/leads/extract", {
      method: "POST",
      body: JSON.stringify({ raw_email: rawEmail }),
    });
    state.rawEmail = rawEmail;
    state.extracted = data;
    renderExtracted(data);
    saveBtn.disabled = false;
    setStatus("抽取完成，请检查字段后保存。");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    extractBtn.disabled = false;
  }
}

async function saveLead() {
  if (!state.extracted || !state.rawEmail) return;
  saveBtn.disabled = true;
  setStatus("正在保存线索...");
  try {
    const lead = await api("/api/leads", {
      method: "POST",
      body: JSON.stringify({ raw_email: state.rawEmail, extracted: state.extracted }),
    });
    setStatus(`已保存线索 #${lead.id}，状态为待审核。`);
    await loadLeads();
    await selectLead(lead.id);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    saveBtn.disabled = false;
  }
}

function statusLabel(status) {
  return {
    pending_review: "待审核",
    confirmed: "已确认",
    rejected: "已拒绝",
  }[status] || status;
}

async function loadLeads() {
  const status = statusFilter.value;
  const leads = await api(status ? `/api/leads?status=${encodeURIComponent(status)}` : "/api/leads");
  clearChildren(leadList);
  if (!leads.length) {
    appendText(leadList, "p", "暂无线索。", "status-text");
    return;
  }
  leads.forEach((lead) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "lead-card";
    const score = Number(lead.lead_score || 0);
    appendText(card, "strong", `#${lead.id} ${lead.name} · ${lead.company}`);
    appendText(card, "span", `${lead.country} / ${lead.product_need} / ${lead.priority}`, "lead-meta");
    appendText(card, "span", `来源 ${lead.source_channel || "manual"} / 同步 ${lead.sync_status || "not_synced"}`, "lead-meta");
    const footer = document.createElement("span");
    footer.className = "lead-card-footer";
    appendText(footer, "span", `评分 ${score}`, `badge ${lead.priority}`);
    appendText(
      footer,
      "span",
      statusLabel(lead.status),
      `badge ${lead.status === "confirmed" ? "confirmed" : lead.status === "rejected" ? "rejected" : "muted"}`
    );
    card.appendChild(footer);
    card.addEventListener("click", () => selectLead(lead.id));
    leadList.appendChild(card);
  });
}

function fillReviewForm(lead) {
  fields.forEach(([key]) => {
    const input = reviewForm.elements[key];
    if (input) input.value = lead[key] || "";
  });
  if (reviewForm.elements.lead_score) reviewForm.elements.lead_score.value = lead.lead_score ?? 0;
  reviewForm.elements.reviewer_note.value = "";
  rawEmailText.textContent = lead.original_email || "";
  detailStatus.className = `badge ${lead.status === "confirmed" ? "confirmed" : lead.status === "rejected" ? "rejected" : "muted"}`;
  detailStatus.textContent = statusLabel(lead.status);
  confirmBtn.disabled = false;
  rejectBtn.disabled = false;
  syncFeishuBtn.disabled = false;
}

function renderTimeline(logs) {
  const timeline = logs.timeline || [];
  if (!timeline.length) {
    timelineList.textContent = "暂无时间线。";
    return;
  }
  clearChildren(timelineList);
  timeline.forEach((item) => {
    const node = document.createElement("article");
    node.className = "timeline-item";
    appendText(node, "span", item.at || "");
    appendText(node, "strong", item.title || item.type);
    appendText(node, "p", item.detail || "");
    timelineList.appendChild(node);
  });
}

async function selectLead(id) {
  state.selectedLeadId = id;
  const lead = await api(`/api/leads/${id}`);
  fillReviewForm(lead);
  const logs = await api(`/api/leads/${id}/logs`);
  renderTimeline(logs);

  const latestExtraction = parseJson(logs.ai_logs?.[0]?.extracted_json, null);
  if (latestExtraction) {
    renderExtracted({ ...latestExtraction, lead_score: lead.lead_score });
  }
}

function collectUpdates() {
  const updates = {};
  editableFields.forEach((key) => {
    const input = reviewForm.elements[key];
    if (input) updates[key] = input.value.trim() || "unknown";
  });
  return updates;
}

async function review(action) {
  if (!state.selectedLeadId) return;
  const payload = {
    action,
    updates: collectUpdates(),
    reviewer_note: reviewForm.elements.reviewer_note.value.trim(),
  };
  await api(`/api/leads/${state.selectedLeadId}/review`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  setStatus(action === "confirmed" ? "线索已确认，审核记录已保存。" : "线索已拒绝，审核记录已保存。");
  await loadLeads();
  await selectLead(state.selectedLeadId);
}

async function importBatch() {
  const files = Array.from(batchInput.files || []);
  if (!files.length) {
    setStatus("请先选择 txt 或 eml 邮件文件。", true);
    return;
  }
  batchImportBtn.disabled = true;
  setStatus("正在批量导入邮件...");
  try {
    const emails = await Promise.all(
      files.map(async (file) => ({
        filename: file.name,
        content: await file.text(),
      }))
    );
    const result = await api("/api/leads/import-batch", {
      method: "POST",
      body: JSON.stringify({ emails }),
    });
    setStatus(`批量导入完成：成功 ${result.imported_count} 条，失败 ${result.error_count} 条。`);
    await loadLeads();
    const firstLead = result.imported?.[0]?.lead;
    if (firstLead) await selectLead(firstLead.id);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    batchImportBtn.disabled = false;
  }
}

async function syncFeishu() {
  if (!state.selectedLeadId) return;
  syncFeishuBtn.disabled = true;
  setStatus("正在同步到飞书 Mock...");
  try {
    const result = await api(`/api/leads/${state.selectedLeadId}/sync/feishu`, {
      method: "POST",
    });
    setStatus(
      result.status === "failed"
        ? `同步失败：${result.detail || "请检查飞书配置后重试。"}`
        : `已同步到 ${result.target}，状态：${result.status}。`,
      result.status === "failed"
    );
    await loadLeads();
    await selectLead(state.selectedLeadId);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    syncFeishuBtn.disabled = false;
  }
}

async function exportCsv() {
  setStatus("正在生成 CSV...");
  try {
    const response = await fetch("/api/leads/export.csv");
    if (!response.ok) throw new Error(`CSV export failed: ${response.status}`);
    const csvText = await response.text();
    const blob = new Blob([csvText], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "foreign_trade_leads.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setStatus("CSV 已生成。如果当前浏览器没有下载提示，请直接打开 /api/leads/export.csv。");
  } catch (error) {
    setStatus(error.message, true);
  }
}

sampleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const sample = sampleEmails[button.dataset.sample];
    emailInput.value = sample;
    state.extracted = null;
    state.rawEmail = "";
    saveBtn.disabled = true;
    setStatus(`已填入${button.textContent}示例邮件。`);
  });
});
extractBtn.addEventListener("click", extractLead);
saveBtn.addEventListener("click", saveLead);
batchImportBtn.addEventListener("click", importBatch);
exportBtn.addEventListener("click", exportCsv);
refreshBtn.addEventListener("click", loadLeads);
statusFilter.addEventListener("change", loadLeads);
confirmBtn.addEventListener("click", () => review("confirmed"));
rejectBtn.addEventListener("click", () => review("rejected"));
syncFeishuBtn.addEventListener("click", syncFeishu);

loadLeads().catch((error) => setStatus(error.message, true));
