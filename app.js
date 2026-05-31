// ============================================================
// STAN'S LOOT DROP — UI logic
// ============================================================
// Renders two game sections, manages front/back selection state,
// and builds a Stripe Payment Link URL with the choices encoded as
// client_reference_id (e.g. "front_rv_knife__back_bf_dragon_fruit").
// ============================================================

const sectionsRoot = document.getElementById("sections");
const builderEl = document.getElementById("builder");
const toast = document.getElementById("toast");
const toastText = document.getElementById("toast-text");

const state = { front: null, back: null };

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

function findIcon(slug) {
  for (const sec of SECTIONS) {
    for (const ic of sec.icons) {
      if (iconSlug(sec.id, ic.name) === slug) return { ...ic, sectionId: sec.id };
    }
  }
  return null;
}

function formatPrice(p) {
  return `${CURRENCY}${Number.isInteger(p) ? p : p.toFixed(2)}`;
}

function iconCardHTML(sectionId, ic) {
  const slug = iconSlug(sectionId, ic.name);
  return `
    <article class="card" data-slug="${slug}">
      <div class="card-img">
        <span class="tier tier-${ic.tier}">${ic.tier}</span>
        <img src="${ic.image}" alt="${ic.name}" loading="lazy" />
      </div>
      <h3 class="card-name">${ic.name}</h3>
      <div class="card-actions">
        <button class="pick-btn pick-front" data-side="front">FRONT</button>
        <button class="pick-btn pick-back" data-side="back">BACK</button>
      </div>
    </article>
  `;
}

function renderSections() {
  sectionsRoot.innerHTML = SECTIONS.map(
    (sec) => `
    <section class="game" id="game-${sec.id}">
      <div class="game-header">
        <img class="game-logo" src="${sec.logo}" alt="${sec.title} logo" />
        <p class="game-blurb">${sec.blurb}</p>
        <span class="game-count">${sec.icons.length} icons</span>
      </div>
      <div class="grid">
        ${sec.icons.map((ic) => iconCardHTML(sec.id, ic)).join("")}
      </div>
    </section>
  `
  ).join("");
}

function slotHTML(side, ic) {
  const label = side === "front" ? "FRONT" : "BACK";
  if (!ic) {
    return `
      <div class="slot" data-side="${side}">
        <span class="slot-label">${label}</span>
        <span class="slot-empty">+</span>
      </div>
    `;
  }
  return `
    <div class="slot filled" data-side="${side}">
      <span class="slot-label">${label}</span>
      <img src="${ic.image}" alt="${ic.name}" />
      <span class="slot-name">${ic.name}</span>
      <button class="slot-clear" data-side="${side}" aria-label="clear ${side}">×</button>
    </div>
  `;
}

function renderBuilder() {
  const { front, back } = state;
  const ready = front && back;
  const linkSetUp =
    KEYCHAIN.paymentLink && !KEYCHAIN.paymentLink.includes("REPLACE_ME");

  let cta;
  if (!ready) {
    cta = `<button class="buy-keychain" disabled>PICK BOTH SIDES</button>`;
  } else if (!linkSetUp) {
    cta = `<button class="buy-keychain not-ready">BUY (PAYMENTS COMING)</button>`;
  } else {
    cta = `<button class="buy-keychain">BUY THIS KEYCHAIN →</button>`;
  }

  let hint;
  if (!front && !back) hint = "Pick a FRONT and a BACK from the icons below.";
  else if (!front) hint = "Now pick a FRONT.";
  else if (!back) hint = "Now pick a BACK.";
  else hint = "Looking sharp. Hit BUY when you're ready.";

  builderEl.innerHTML = `
    <div class="builder-inner">
      ${slotHTML("front", front)}
      ${slotHTML("back", back)}
      <div class="builder-cta">
        <span class="builder-price">${formatPrice(KEYCHAIN.price)}</span>
        ${cta}
      </div>
    </div>
    <p class="builder-hint">${hint}</p>
  `;

  document.querySelectorAll(".card").forEach((c) => {
    c.classList.remove("selected-front", "selected-back");
    const slug = c.dataset.slug;
    if (front && iconSlug(front.sectionId, front.name) === slug)
      c.classList.add("selected-front");
    if (back && iconSlug(back.sectionId, back.name) === slug)
      c.classList.add("selected-back");
  });
}

function iconLabel(ic) {
  const sec = SECTIONS.find((s) => s.id === ic.sectionId);
  return sec ? `${ic.name} (${sec.title})` : ic.name;
}

function buyURL() {
  if (!state.front || !state.back) return null;
  if (
    !KEYCHAIN.paymentLink ||
    KEYCHAIN.paymentLink.includes("REPLACE_ME")
  )
    return null;
  const ref = `front_${iconSlug(
    state.front.sectionId,
    state.front.name
  )}__back_${iconSlug(state.back.sectionId, state.back.name)}`;
  try {
    const u = new URL(KEYCHAIN.paymentLink);
    u.searchParams.set("client_reference_id", ref);
    // Prefill the Stripe Payment Link's custom fields so the choices show up
    // on the checkout page and as line items in the order email/dashboard.
    // The keys must match the auto-generated keys Stripe assigned (it strips
    // spaces from the label rather than replacing them with underscores).
    u.searchParams.set("prefilled_fronticon", iconLabel(state.front));
    u.searchParams.set("prefilled_backicon", iconLabel(state.back));
    return u.toString();
  } catch {
    return null;
  }
}

document.addEventListener("click", (e) => {
  const pick = e.target.closest(".pick-btn");
  if (pick) {
    const card = pick.closest(".card");
    const ic = findIcon(card.dataset.slug);
    if (!ic) return;
    state[pick.dataset.side] = ic;
    renderBuilder();
    return;
  }

  const clear = e.target.closest(".slot-clear");
  if (clear) {
    state[clear.dataset.side] = null;
    renderBuilder();
    return;
  }

  const buy = e.target.closest(".buy-keychain");
  if (buy && !buy.disabled) {
    if (buy.classList.contains("not-ready")) {
      showToast("⏳ Stan is still setting up payments — try again soon!");
      return;
    }
    const url = buyURL();
    if (url) window.open(url, "_blank", "noopener");
    return;
  }
});

let toastTimer;
function showToast(msg) {
  toastText.textContent = msg;
  toast.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add("hidden"), 3200);
}

renderSections();
renderBuilder();

// Easter egg
let titleTaps = 0;
document.querySelector(".hero h1").addEventListener("click", () => {
  titleTaps++;
  if (titleTaps === 5) {
    showToast("🎉 SECRET UNLOCKED — STAN APPROVES");
    document.body.style.animation = "wobble 0.6s ease-in-out 2";
    setTimeout(() => (document.body.style.animation = ""), 1300);
    titleTaps = 0;
  }
});
