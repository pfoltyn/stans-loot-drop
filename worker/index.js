// ============================================================
// STAN'S LOOT DROP — Cloudflare Worker
// ============================================================
// Receives Stripe `checkout.session.completed` webhooks at /webhook,
// verifies the signature, parses the buyer's choices from
// client_reference_id, and emails Stan via Resend.
//
// All other requests fall through to the static-asset handler.
//
// Required secrets (set via Cloudflare dashboard → Workers → Settings →
// Variables and Secrets, or `wrangler secret put`):
//   STRIPE_WEBHOOK_SECRET — from Stripe → Developers → Webhooks → your endpoint
//   RESEND_API_KEY        — from resend.com → API Keys
//   NOTIFICATION_FROM     — e.g. "Stan's Shop <onboarding@resend.dev>"
//   NOTIFICATION_TO       — your email address
// ============================================================

import { SECTIONS } from "../catalog.js";

export default {
  async fetch(request, env) {
    try {
      const url = new URL(request.url);
      if (url.pathname === "/webhook" && request.method === "POST") {
        return await handleWebhook(request, env);
      }
      if (!env.ASSETS) {
        // Helpful diagnostic if the [assets] binding isn't wired up.
        return new Response(
          "Worker misconfigured: env.ASSETS is undefined. " +
            "Check wrangler.toml [assets] block has binding = \"ASSETS\".",
          { status: 500, headers: { "content-type": "text/plain" } }
        );
      }
      // Anything else: serve static assets.
      return env.ASSETS.fetch(request);
    } catch (e) {
      console.error("Worker error:", e?.stack || e);
      return new Response("Worker error: " + (e?.message || e), {
        status: 500,
        headers: { "content-type": "text/plain" },
      });
    }
  },
};

async function handleWebhook(request, env) {
  const sigHeader = request.headers.get("stripe-signature");
  if (!sigHeader) return new Response("Missing signature", { status: 400 });

  const rawBody = await request.text();

  const valid = await verifyStripeSignature(
    rawBody,
    sigHeader,
    env.STRIPE_WEBHOOK_SECRET
  );
  if (!valid) return new Response("Invalid signature", { status: 400 });

  const event = JSON.parse(rawBody);
  if (event.type !== "checkout.session.completed") {
    // Acknowledge but do nothing for other event types.
    return new Response("Ignored", { status: 200 });
  }

  const session = event.data.object;
  const choices = parseChoices(session.client_reference_id || "");
  const { subject, html, text } = renderEmail(session, choices, event.livemode);

  await sendEmail(env, { subject, html, text });
  return new Response("OK", { status: 200 });
}

// ---------- choice lookup ----------

function iconSlug(sectionId, name) {
  return (
    sectionId +
    "_" +
    name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "")
  );
}

function lookupSlug(slug) {
  for (const sec of SECTIONS) {
    for (const ic of sec.icons) {
      if (iconSlug(sec.id, ic.name) === slug) {
        return { name: ic.name, game: sec.title, tier: ic.tier };
      }
    }
  }
  return { name: slug, game: "?", tier: "?" };
}

function parseChoices(ref) {
  // Format: "front_<slug>__back_<slug>"
  const m = ref.match(/^front_(.+?)__back_(.+)$/);
  if (!m) return { front: null, back: null, ref };
  return {
    front: lookupSlug(m[1]),
    back: lookupSlug(m[2]),
    ref,
  };
}

// ---------- email ----------

function renderEmail(session, choices, livemode) {
  const cust = session.customer_details || {};
  const amount =
    session.amount_total != null
      ? (session.amount_total / 100).toFixed(2)
      : "?";
  const currency = (session.currency || "GBP").toUpperCase();

  const customFields = (session.custom_fields || []).reduce((m, f) => {
    m[f.key] = f.text?.value || f.numeric?.value || f.dropdown?.value || "";
    return m;
  }, {});

  const front = choices.front || { name: "?", game: "?", tier: "?" };
  const back = choices.back || { name: "?", game: "?", tier: "?" };

  const dashboardBase = livemode
    ? "https://dashboard.stripe.com"
    : "https://dashboard.stripe.com/test";
  const sessionUrl = `${dashboardBase}/payments/${session.payment_intent || session.id}`;

  const tag = livemode ? "" : "[TEST] ";
  const subject = `${tag}🔑 New keychain: ${front.name} / ${back.name}`;

  const text = [
    `Stan just sold a keychain!${livemode ? "" : " (test mode)"}`,
    ``,
    `Customer:  ${cust.name || "—"}${cust.email ? " <" + cust.email + ">" : ""}`,
    ...Object.entries(customFields).map(
      ([k, v]) => `${k.padEnd(10)} ${v}`
    ),
    ``,
    `Front:     ${front.name} (${front.game}) — ${front.tier}`,
    `Back:      ${back.name} (${back.game}) — ${back.tier}`,
    `Total:     ${currency} ${amount}`,
    ``,
    `Reference: ${choices.ref || "—"}`,
    `Stripe:    ${sessionUrl}`,
  ].join("\n");

  const html = `
    <div style="font-family:-apple-system,system-ui,Segoe UI,Roboto,sans-serif;max-width:560px;margin:0 auto;padding:24px;background:#0b0b14;color:#f7f7ff;border-radius:18px;border:2px solid #ffcc00">
      <h2 style="margin:0 0 8px;font-size:20px">🎉 Stan just sold a keychain!${livemode ? "" : " <span style=\"color:#ffcc00\">(test)</span>"}</h2>
      <table style="width:100%;border-collapse:collapse;margin-top:16px">
        <tr><td style="padding:6px 0;color:#a8a8c4;width:90px">Customer</td><td><b>${escapeHtml(cust.name || "—")}</b>${cust.email ? " &lt;" + escapeHtml(cust.email) + "&gt;" : ""}</td></tr>
        ${Object.entries(customFields)
          .map(
            ([k, v]) =>
              `<tr><td style="padding:6px 0;color:#a8a8c4">${escapeHtml(k)}</td><td>${escapeHtml(v)}</td></tr>`
          )
          .join("")}
        <tr><td style="padding:6px 0;color:#a8a8c4">Front</td><td><b>${escapeHtml(front.name)}</b> <span style="color:#a8a8c4">(${escapeHtml(front.game)} — ${escapeHtml(front.tier)})</span></td></tr>
        <tr><td style="padding:6px 0;color:#a8a8c4">Back</td><td><b>${escapeHtml(back.name)}</b> <span style="color:#a8a8c4">(${escapeHtml(back.game)} — ${escapeHtml(back.tier)})</span></td></tr>
        <tr><td style="padding:6px 0;color:#a8a8c4">Total</td><td style="font-size:18px;color:#ffcc00"><b>${currency} ${amount}</b></td></tr>
      </table>
      <p style="margin:24px 0 6px;color:#a8a8c4;font-size:12px">Ref: <code>${escapeHtml(choices.ref || "—")}</code></p>
      <p style="margin:0">
        <a href="${sessionUrl}" style="display:inline-block;background:#ffcc00;color:#000;padding:10px 18px;border-radius:10px;text-decoration:none;font-weight:700">View in Stripe →</a>
      </p>
    </div>
  `;

  return { subject, html, text };
}

function escapeHtml(s) {
  return String(s).replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[c]
  );
}

async function sendEmail(env, { subject, html, text }) {
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: env.NOTIFICATION_FROM,
      to: [env.NOTIFICATION_TO],
      subject,
      html,
      text,
    }),
  });
  if (!r.ok) {
    const body = await r.text();
    throw new Error(`Resend ${r.status}: ${body}`);
  }
}

// ---------- Stripe signature verification (Web Crypto) ----------

async function verifyStripeSignature(rawBody, sigHeader, secret) {
  if (!secret) return false;
  const parts = {};
  for (const kv of sigHeader.split(",")) {
    const i = kv.indexOf("=");
    if (i < 0) continue;
    const k = kv.slice(0, i);
    const v = kv.slice(i + 1);
    (parts[k] = parts[k] || []).push(v);
  }
  const timestamp = parts.t?.[0];
  const signatures = parts.v1 || [];
  if (!timestamp || signatures.length === 0) return false;

  // Replay protection (5 min tolerance).
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - parseInt(timestamp, 10)) > 300) return false;

  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign(
    "HMAC",
    key,
    enc.encode(`${timestamp}.${rawBody}`)
  );
  const expected = Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");

  for (const s of signatures) {
    if (s.length === expected.length) {
      let mismatch = 0;
      for (let i = 0; i < s.length; i++) {
        mismatch |= s.charCodeAt(i) ^ expected.charCodeAt(i);
      }
      if (mismatch === 0) return true;
    }
  }
  return false;
}
