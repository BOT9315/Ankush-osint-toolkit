const API = "/api";

const navItems = document.querySelectorAll(".nav-item");
const pages = document.querySelectorAll(".page");
const pageTitle = document.getElementById("pageTitle");
const pageEyebrow = document.getElementById("pageEyebrow");

const pageInfo = {
  dashboard: ["DASHBOARD", "Case overview"],
  username: ["FILE — USR", "Username Intelligence"],
  email: ["FILE — EML", "Email Intelligence"],
  ip: ["FILE — IP4", "IP Intelligence"],
  domain: ["FILE — DNS", "Domain & DNS Intelligence"],
  image: ["FILE — IMG", "Image OSINT"],
  history: ["FILE — LOG", "Investigation History"],
};

function openPage(name) {
  pages.forEach((p) => p.classList.remove("active-page"));
  document.getElementById(name)?.classList.add("active-page");
  navItems.forEach((i) => i.classList.toggle("active", i.dataset.page === name));
  const [eyebrow, title] = pageInfo[name];
  pageEyebrow.textContent = eyebrow;
  pageTitle.textContent = title;
  if (name === "history") loadHistory();
}

navItems.forEach((i) => (i.onclick = () => openPage(i.dataset.page)));
document.querySelectorAll(".tool-card").forEach((c) => (c.onclick = () => openPage(c.dataset.page)));

/* ---------- theme ---------- */
const themeButton = document.getElementById("themeButton");
function applyTheme(mode) {
  document.body.classList.toggle("light", mode === "light");
  themeButton.textContent = mode === "light" ? "☀" : "☾";
}
applyTheme(localStorage.getItem("ankush-theme") || "dark");
themeButton.onclick = () => {
  const next = document.body.classList.contains("light") ? "dark" : "light";
  applyTheme(next);
  localStorage.setItem("ankush-theme", next);
};

/* ---------- api helper ---------- */
async function apiRequest(endpoint, target) {
  const r = await fetch(API + endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target }),
  });
  if (!r.ok) {
    const x = await r.json().catch(() => ({}));
    throw new Error(x.detail || "Request failed");
  }
  return r.json();
}

/* ---------- username ---------- */
async function runUsername() {
  const v = document.getElementById("usernameInput").value.trim();
  const summary = document.getElementById("usernameSummary");
  const o = document.getElementById("usernameResults");
  if (!v) return showToast("Enter a username", "error");
  summary.innerHTML = "";
  o.innerHTML = loadingCard();
  try {
    const d = await apiRequest("/username", v);
    summary.innerHTML = `<div class="summary-bar">Checked <strong>${d.checked}</strong> platforms · <strong>${d.found_count}</strong> possible matches for <strong>${esc(d.username)}</strong></div>`;
    o.innerHTML = d.results
      .map(
        (x) => `<div class="result-card">
          <div class="result-header">
            <h3>${esc(x.platform)}</h3>
            <span class="stamp ${x.found ? "found" : "notfound"}">${x.found ? "MATCH" : "NO MATCH"}</span>
          </div>
          <div class="result-row"><span>http_status</span><span>${x.status ?? "unreachable"}</span></div>
          ${x.response_ms != null ? `<div class="result-row"><span>response_ms</span><span>${x.response_ms}</span></div>` : ""}
          <div class="result-row"><span>profile_url</span><span><a class="link" href="${x.url}" target="_blank" rel="noopener">${esc(x.url)}</a></span></div>
        </div>`
      )
      .join("");
    loadStats();
  } catch (e) {
    o.innerHTML = errorCard(e.message);
  }
}

/* ---------- simple tools ---------- */
async function runEmail() { await runSimple("email", "emailInput", "emailResults", "Email"); }
async function runIP() { await runSimple("ip", "ipInput", "ipResults", "IP address"); }
async function runDomain() { await runSimple("domain", "domainInput", "domainResults", "Domain"); }

async function runSimple(type, inputId, outId, label) {
  const v = document.getElementById(inputId).value.trim();
  const o = document.getElementById(outId);
  if (!v) return showToast(`Enter ${label.toLowerCase() === "email" ? "an" : "a"} ${label.toLowerCase()}`, "error");
  o.innerHTML = loadingCard();
  try {
    const d = await apiRequest("/" + type, v);
    o.innerHTML = createCard(label, d);
    loadStats();
  } catch (e) {
    o.innerHTML = errorCard(e.message);
  }
}

/* ---------- image ---------- */
const uploadArea = document.getElementById("uploadArea");
const imageInput = document.getElementById("imageInput");
imageInput.addEventListener("change", () => {
  if (imageInput.files.length) document.getElementById("uploadLabel").textContent = imageInput.files[0].name;
});
["dragover", "dragleave", "drop"].forEach((evt) =>
  uploadArea.addEventListener(evt, (e) => {
    e.preventDefault();
    uploadArea.classList.toggle("drag", evt === "dragover");
    if (evt === "drop" && e.dataTransfer.files.length) {
      imageInput.files = e.dataTransfer.files;
      document.getElementById("uploadLabel").textContent = e.dataTransfer.files[0].name;
    }
  })
);

async function runImage() {
  const o = document.getElementById("imageResults");
  if (!imageInput.files.length) return showToast("Select an image first", "error");
  const f = new FormData();
  f.append("file", imageInput.files[0]);
  o.innerHTML = loadingCard();
  try {
    const r = await fetch(API + "/image", { method: "POST", body: f });
    if (!r.ok) throw new Error("Image analysis failed");
    o.innerHTML = createCard("Image analysis", await r.json());
    loadStats();
  } catch (e) {
    o.innerHTML = errorCard(e.message);
  }
}

/* ---------- render helpers ---------- */
function createCard(title, d) {
  const ok = !d.error && d.valid !== false;
  let h = `<div class="result-card"><div class="result-header"><h3>${esc(title)}</h3><span class="stamp ${ok ? "success" : "danger"}">${ok ? "COMPLETE" : "ISSUE"}</span></div>`;
  for (const [k, v] of Object.entries(d)) {
    if (k === "type") continue;
    let x;
    if (Array.isArray(v)) x = v.length ? v.map(esc).join("<br>") : "none";
    else if (typeof v === "object" && v !== null) x = esc(JSON.stringify(v));
    else if (typeof v === "boolean") x = v ? "yes" : "no";
    else x = esc(String(v ?? "n/a"));
    h += `<div class="result-row"><span>${esc(k)}</span><span>${x}<button class="copy-btn" onclick="copyValue(this)" data-val="${escAttr(String(v ?? ""))}">copy</button></span></div>`;
  }
  return h + "</div>";
}

function loadingCard() {
  return `<div class="loading-card"><div class="redact-line"></div><div class="redact-line"></div><div class="redact-line"></div></div>`;
}
function errorCard(m) {
  return `<div class="result-card"><div class="result-header"><h3>Error</h3><span class="stamp danger">FAILED</span></div><div class="result-row"><span>message</span><span>${esc(m)}</span></div></div>`;
}
function esc(v) {
  return String(v).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
function escAttr(v) { return esc(v).replace(/`/g, "&#96;"); }
function copyValue(btn) {
  navigator.clipboard?.writeText(btn.dataset.val).then(() => {
    btn.textContent = "copied";
    setTimeout(() => (btn.textContent = "copy"), 1200);
  });
}

/* ---------- history ---------- */
async function loadHistory() {
  const o = document.getElementById("historyResults");
  const tool = document.getElementById("historyFilter").value;
  o.innerHTML = loadingCard();
  try {
    const d = await fetch(`${API}/history?tool=${tool}&limit=100`).then((r) => r.json());
    o.innerHTML = d.length
      ? d
          .map(
            (x) => `<div class="history-item">
              <div>
                <span class="htool">${esc(x.tool).toUpperCase()}</span>
                <strong>${esc(x.target)}</strong>
                <small>${new Date(x.created_at).toLocaleString()}</small>
              </div>
              <button class="del-btn" title="Delete entry" onclick="deleteHistoryEntry(${x.id})">✕</button>
            </div>`
          )
          .join("")
      : `<div class="empty-state">No investigations logged yet for this filter.</div>`;
  } catch (e) {
    o.innerHTML = errorCard(e.message);
  }
}

async function deleteHistoryEntry(id) {
  try {
    const r = await fetch(`${API}/history/${id}`, { method: "DELETE" });
    if (!r.ok) throw new Error("Could not delete entry");
    showToast("Entry deleted", "success");
    loadHistory();
    loadStats();
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function clearAllHistory() {
  if (!confirm("Clear the entire investigation history? This cannot be undone.")) return;
  try {
    await fetch(`${API}/history`, { method: "DELETE" });
    showToast("History cleared", "success");
    loadHistory();
    loadStats();
  } catch (e) {
    showToast(e.message, "error");
  }
}

function exportHistory(format) {
  window.open(`${API}/history/export?format=${format}`, "_blank");
}

/* ---------- stats + dashboard chart ---------- */
async function loadStats() {
  try {
    const d = await fetch(API + "/stats").then((r) => r.json());
    document.getElementById("totalStat").textContent = d.total;
    document.getElementById("usernameStat").textContent = d.usernames;
    document.getElementById("emailStat").textContent = d.emails;
    document.getElementById("ipStat").textContent = d.ips;
    document.getElementById("domainStat").textContent = d.domains;
    document.getElementById("imageStat").textContent = d.images;
    renderChart(d);
  } catch (e) {
    /* API not reachable yet */
  }
}

function renderChart(d) {
  const chart = document.getElementById("statsChart");
  const entries = [
    ["USR", d.usernames],
    ["EML", d.emails],
    ["IP4", d.ips],
    ["DNS", d.domains],
    ["IMG", d.images],
  ];
  const max = Math.max(1, ...entries.map((e) => e[1]));
  chart.innerHTML = entries
    .map(([label, val]) => `<div class="chart-bar"><strong>${val}</strong><div class="bar" style="height:${Math.max(4, (val / max) * 100)}%"></div><span>${label}</span></div>`)
    .join("");
}

/* ---------- toast ---------- */
function showToast(msg, kind = "") {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = "toast show" + (kind ? " " + kind : "");
  setTimeout(() => t.classList.remove("show"), 2600);
}

/* ---------- health check ---------- */
async function checkHealth() {
  const dot = document.getElementById("apiDot");
  const label = document.getElementById("apiLabel");
  try {
    const d = await fetch(API + "/health").then((r) => r.json());
    dot.className = "dot online";
    label.textContent = `API online · v${d.version || "2.1"}`;
  } catch (e) {
    dot.className = "dot offline";
    label.textContent = "API unreachable";
  }
}

checkHealth();
loadStats();
