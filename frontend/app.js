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
];

const emailInput = document.querySelector("#emailInput");
const extractBtn = document.querySelector("#extractBtn");
const saveBtn = document.querySelector("#saveBtn");
const sampleButtons = document.querySelectorAll(".sample-btn");
const exportBtn = document.querySelector("#exportBtn");
const refreshBtn = document.querySelector("#refreshBtn");
const statusText = document.querySelector("#statusText");
const resultGrid = document.querySelector("#resultGrid");
const evidenceList = document.querySelector("#evidenceList");
const confidenceBadge = document.querySelector("#confidenceBadge");
const leadList = document.querySelector("#leadList");
const statusFilter = document.querySelector("#statusFilter");
const reviewForm = document.querySelector("#reviewForm");
const detailStatus = document.querySelector("#detailStatus");
const rawEmailText = document.querySelector("#rawEmailText");
const logText = document.querySelector("#logText");
const confirmBtn = document.querySelector("#confirmBtn");
const rejectBtn = document.querySelector("#rejectBtn");

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

function renderExtracted(data) {
  resultGrid.innerHTML = "";
  fields.forEach(([key, label]) => {
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = label;
    dd.textContent = data[key] || "unknown";
    resultGrid.append(dt, dd);
  });

  evidenceList.innerHTML = "";
  (data.evidence || []).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    evidenceList.appendChild(li);
  });

  const priority = data.priority || "medium";
  confidenceBadge.className = `badge ${priority}`;
  confidenceBadge.textContent = `置信度 ${data.confidence ?? "unknown"} · ${priority}`;
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
  leadList.innerHTML = "";
  if (!leads.length) {
    leadList.innerHTML = '<p class="status-text">暂无线索。</p>';
    return;
  }
  leads.forEach((lead) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "lead-card";
    card.innerHTML = `
      <strong>#${lead.id} ${lead.name} · ${lead.company}</strong>
      <span class="lead-meta">${lead.country} / ${lead.product_need} / ${lead.priority}</span>
      <span class="badge ${lead.status === "confirmed" ? "confirmed" : lead.status === "rejected" ? "rejected" : "muted"}">${statusLabel(lead.status)}</span>
    `;
    card.addEventListener("click", () => selectLead(lead.id));
    leadList.appendChild(card);
  });
}

function fillReviewForm(lead) {
  fields.forEach(([key]) => {
    const input = reviewForm.elements[key];
    if (input) input.value = lead[key] || "";
  });
  reviewForm.elements.reviewer_note.value = "";
  rawEmailText.textContent = lead.original_email || "";
  detailStatus.className = `badge ${lead.status === "confirmed" ? "confirmed" : lead.status === "rejected" ? "rejected" : "muted"}`;
  detailStatus.textContent = statusLabel(lead.status);
  confirmBtn.disabled = false;
  rejectBtn.disabled = false;
}

async function selectLead(id) {
  state.selectedLeadId = id;
  const lead = await api(`/api/leads/${id}`);
  fillReviewForm(lead);
  const logs = await api(`/api/leads/${id}/logs`);
  logText.textContent = JSON.stringify(logs, null, 2);
}

function collectUpdates() {
  const updates = {};
  fields.forEach(([key]) => {
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
exportBtn.addEventListener("click", exportCsv);
refreshBtn.addEventListener("click", loadLeads);
statusFilter.addEventListener("change", loadLeads);
confirmBtn.addEventListener("click", () => review("confirmed"));
rejectBtn.addEventListener("click", () => review("rejected"));

loadLeads().catch((error) => setStatus(error.message, true));
