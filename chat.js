// =========================================================
// STAN'S LOOT DROP — chat / suggestions box
// =========================================================
// Approved messages are public. A sender's own pending messages are stored
// locally and merged into their view so they see them straight away, but other
// visitors don't see anything until Stan approves it.

const OWN_STORAGE_KEY = "stan_chat_own";
const NAME_STORAGE_KEY = "stan_chat_name";
const POLL_MS = 12_000;

function $(sel, root = document) {
  return root.querySelector(sel);
}

function loadOwn() {
  try {
    return JSON.parse(localStorage.getItem(OWN_STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveOwn(ids) {
  // Keep at most the last 50 sent IDs; older pending entries will have been
  // approved or deleted, so there's no point asking the server about them.
  localStorage.setItem(OWN_STORAGE_KEY, JSON.stringify(ids.slice(-50)));
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

function formatTime(ts) {
  const d = new Date(ts);
  const today = new Date();
  const sameDay =
    d.getFullYear() === today.getFullYear() &&
    d.getMonth() === today.getMonth() &&
    d.getDate() === today.getDate();
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  if (sameDay) return `${hh}:${mm}`;
  return `${d.toLocaleDateString()} ${hh}:${mm}`;
}

function renderMessages(feed, approved, ownPending) {
  // Merge and de-dupe (a pending message can flip to approved between polls).
  const seen = new Set(approved.map((m) => m.id));
  const merged = approved.concat(ownPending.filter((m) => !seen.has(m.id)));
  merged.sort((a, b) => a.ts - b.ts);

  if (!merged.length) {
    feed.innerHTML = `<div class="chat-empty">No suggestions yet — be the first!</div>`;
    return;
  }

  feed.innerHTML = merged
    .map((m) => {
      const pending = !seen.has(m.id);
      return `
        <div class="chat-msg${pending ? " chat-msg--pending" : ""}">
          <div class="chat-msg-head">
            <span class="chat-msg-name">${escapeHtml(m.name)}</span>
            <span class="chat-msg-time">${formatTime(m.ts)}</span>
            ${pending ? `<span class="chat-msg-pending">waiting for Stan…</span>` : ""}
          </div>
          <div class="chat-msg-body">${escapeHtml(m.message)}</div>
        </div>
      `;
    })
    .join("");
  feed.scrollTop = feed.scrollHeight;
}

async function fetchApproved() {
  const r = await fetch("/api/chat", { cache: "no-store" });
  if (!r.ok) throw new Error(`approved fetch: ${r.status}`);
  const j = await r.json();
  return j.messages || [];
}

async function fetchOwnPending(ids) {
  if (!ids.length) return [];
  const r = await fetch("/api/chat/own?ids=" + encodeURIComponent(ids.join(",")), {
    cache: "no-store",
  });
  if (!r.ok) return [];
  const j = await r.json();
  return j.messages || [];
}

async function refresh(feed) {
  let approved = [];
  try {
    approved = await fetchApproved();
  } catch (e) {
    console.warn("chat refresh failed", e);
  }
  const ownIds = loadOwn();
  const approvedIds = new Set(approved.map((m) => m.id));
  const stillPendingIds = ownIds.filter((id) => !approvedIds.has(id));
  const ownPending = await fetchOwnPending(stillPendingIds);
  // Prune local list to ones that still exist somewhere.
  const knownIds = new Set([...approvedIds, ...ownPending.map((m) => m.id)]);
  saveOwn(ownIds.filter((id) => knownIds.has(id)));
  renderMessages(feed, approved, ownPending);
}

function init() {
  const form = $("#chat-form");
  if (!form) return;
  const nameInput = $("#chat-name");
  const msgInput = $("#chat-message");
  const status = $("#chat-status");
  const feed = $("#chat-feed");
  const button = $("#chat-send");

  // Remember the name across visits.
  const savedName = localStorage.getItem(NAME_STORAGE_KEY);
  if (savedName) nameInput.value = savedName;

  refresh(feed);
  setInterval(() => refresh(feed), POLL_MS);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = nameInput.value.trim();
    const message = msgInput.value.trim();
    if (!name || !message) {
      status.textContent = "Add your name and a message.";
      return;
    }
    button.disabled = true;
    status.textContent = "Sending…";
    try {
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name, message }),
      });
      const j = await r.json();
      if (!r.ok || !j.ok) throw new Error(j.error || `HTTP ${r.status}`);
      localStorage.setItem(NAME_STORAGE_KEY, name);
      const own = loadOwn();
      own.push(j.id);
      saveOwn(own);
      msgInput.value = "";
      status.textContent = "Sent — waiting for Stan to approve.";
      await refresh(feed);
    } catch (err) {
      status.textContent = "Couldn't send: " + (err.message || err);
    } finally {
      button.disabled = false;
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
