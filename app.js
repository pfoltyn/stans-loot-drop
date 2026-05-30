// ============================================================
// STAN'S LOOT DROP — renderer
// ============================================================

const grid = document.getElementById("grid");
const toast = document.getElementById("toast");
const toastText = document.getElementById("toast-text");

function formatPrice(p) {
  return `${CURRENCY}${Number.isInteger(p) ? p : p.toFixed(2)}`;
}

function cardHTML(p) {
  const linkSetUp = p.paymentLink && !p.paymentLink.includes("REPLACE_ME");
  const buyAttrs = linkSetUp
    ? `href="${p.paymentLink}" target="_blank" rel="noopener"`
    : `href="#" data-not-ready="1"`;
  return `
    <article class="card">
      <div class="card-img">
        <span class="tier tier-${p.tier}">${p.tier}</span>
        <img src="${p.image}" alt="${p.name} keychain" loading="lazy" />
      </div>
      <h3 class="card-name">${p.name}</h3>
      <p class="card-desc">${p.desc}</p>
      <div class="card-row">
        <span class="price">${formatPrice(p.price)}</span>
        <a class="buy-btn" ${buyAttrs}>BUY →</a>
      </div>
    </article>
  `;
}

grid.innerHTML = PRODUCTS.map(cardHTML).join("");

// Funny fallback: if Stripe links aren't set up yet, tell the buyer.
grid.addEventListener("click", (e) => {
  const a = e.target.closest("a[data-not-ready]");
  if (!a) return;
  e.preventDefault();
  showToast("⏳ Stan is still setting up payments — try again soon!");
});

let toastTimer;
function showToast(msg) {
  toastText.textContent = msg;
  toast.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add("hidden"), 3200);
}

// Tiny easter egg: tap the title 5x for extra silliness
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
