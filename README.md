# Stan's Loot Drop 🔑

A funny little shop site for Stan (10) to sell his handmade Roblox-themed
keychains to friends at school. Static HTML — no backend — payments handled by
**Stripe Payment Links**.

## How to run it locally

The simplest way:

```bash
cd /Users/pfoltyn/pzf_keychain
python3 -m http.server 8000
```

Then open <http://localhost:8000> in a browser.

(You can also just double-click `index.html`, but a local server is friendlier
to lazy-loaded images.)

## How to set up real Stripe payments

The site is wired up — every "BUY" button is ready to point at a Stripe
Payment Link. You just need to create the links in Stripe and paste them in.

### 1. Make a Stripe account

Go to <https://dashboard.stripe.com/register>. You'll need a parent's details
(Stan is too young to own the account — it should be in your name).

### 2. Create ONE Payment Link for "Custom 2-Sided Keychain"

Stan now sells a single product: a custom keychain. Buyers pick a FRONT icon
and a BACK icon on the website, and those choices ride along to Stripe so Stan
knows what to make.

1. In the Stripe dashboard, go to **Product catalogue → Add product**.
2. Name it `Custom 2-Sided Keychain`, set the price (e.g. £4 GBP).
3. Save, then on the product page click **Create payment link**.
4. Important settings:
   - ✅ **Collect customer's name** (so Stan knows who to give it to).
   - ✅ Add a custom field: **"School class / year"**.
   - ❌ Do NOT collect a shipping address (school pickup only).
   - Set quantity limits if you like (e.g. max 5 per order).
5. Copy the link — it'll look like `https://buy.stripe.com/abc123xyz`.

The website appends the buyer's choices to that link as
`?client_reference_id=front_rv_knife__back_bf_dragon_fruit`. You'll see this
ID on every Stripe payment in the dashboard under **Payments → (the payment) →
Client reference ID** — that tells you exactly which two icons to make.

### 3. Paste the link into `products.js`

Open `products.js` and replace the placeholder URL in `KEYCHAIN.paymentLink`:

```js
const KEYCHAIN = {
  name: "Custom 2-Sided Keychain",
  price: 4,
  paymentLink: "https://buy.stripe.com/abc123xyz",   // ← paste here
};
```

Reload the page — done. Until you replace the link, the BUY button shows a
friendly "Stan is still setting up payments" message instead of breaking.

## Email notifications on every sale

A small Cloudflare Worker (`worker/index.js`) listens for Stripe's
`checkout.session.completed` webhook, looks up the buyer's two icon choices
from the catalog, and sends Stan a nicely-formatted email.

### One-time setup

#### 1. Sign up for Resend (free email API)

<https://resend.com/signup> → free tier is 3000 emails/month, plenty.

For testing, you can use Resend's default sender `onboarding@resend.dev`. To
send from your own domain (nicer-looking emails), follow Resend's domain
verification flow.

Get an **API key** under **API Keys → Create API Key**. Save it somewhere safe —
you'll only see it once.

#### 2. Set the Worker secrets in Cloudflare

Cloudflare dashboard → **Workers & Pages → stans-loot-drop → Settings →
Variables and Secrets → Add variable**. Add four (each as type **Encrypted**):

| Name                    | Value                                                |
| ----------------------- | ---------------------------------------------------- |
| `RESEND_API_KEY`        | The API key from step 1                              |
| `NOTIFICATION_FROM`     | `Stan's Shop <onboarding@resend.dev>` (or your own)  |
| `NOTIFICATION_TO`       | Your email address                                   |
| `STRIPE_WEBHOOK_SECRET` | (filled in step 4)                                   |

Save. The Worker auto-redeploys.

#### 3. Add a Stripe webhook endpoint

Stripe dashboard → **Developers → Webhooks → Add endpoint** (make sure you're
in **Test mode** while you're still testing).

- **Endpoint URL:** `https://stans-loot-drop.piotr-foltyn.workers.dev/webhook`
- **Events to listen to:** select `checkout.session.completed`
- Click **Add endpoint**.

#### 4. Copy the webhook signing secret

On the new endpoint's page, click **Reveal** under **Signing secret**. Copy the
value (starts with `whsec_`). Paste it into the Cloudflare dashboard as the
`STRIPE_WEBHOOK_SECRET` from step 2.

#### 5. Test it

Make a fake purchase on the site with Stripe test card `4242 4242 4242 4242`.
Within ~5 seconds, an email should arrive with the buyer name, school class,
front icon, back icon, and a "View in Stripe →" button.

If nothing arrives:

- **Stripe → Developers → Webhooks → your endpoint → Recent deliveries** shows
  whether the webhook fired and what the Worker responded with.
- **Cloudflare → Workers & Pages → stans-loot-drop → Logs** shows any errors
  the Worker threw.

### Going live

When you switch the Payment Link from Test to Live mode, repeat steps 3 + 4
in **Live mode** (test and live webhooks are separate). The Worker handles both
identically; the email subject is prefixed with `[TEST]` for test-mode events
so you can tell them apart at a glance.

### 4. (Optional) Test mode first

While you're trying things out, toggle to **Test mode** in the Stripe
dashboard (top-right). Test-mode Payment Links accept test card
`4242 4242 4242 4242` so you can pretend-buy without spending real money.

## Editing the shop

| Want to…                                | Edit this file       |
| --------------------------------------- | -------------------- |
| Change the keychain price               | `catalog.js` (`KEYCHAIN.price`) |
| Add/remove an icon from a game          | `catalog.js` (the `icons` array in the section) |
| Add a whole new game                    | `catalog.js` (push a new entry to `SECTIONS`) |
| Change a tier or icon name              | `catalog.js`        |
| Change colours / fonts                  | `styles.css`         |
| Change page text (hero / about / ideas) | `index.html`         |

### Adding a new icon to an existing game

1. Run `make_icon_card.py` on the source icon (puts both `.png` print-master
   and `.webp` web copy in the same folder):
   ```bash
   python3 make_icon_card.py orig/Rivals/NewWeapon.webp "New Weapon"
   ```
2. Move the resulting `.png` and `.webp` into `done/Rivals/` (or `done/BloxFruits/`).
3. Add a new entry to the relevant section's `icons` array in `products.js`:
   ```js
   { name: "New Weapon", image: "done/Rivals/New Weapon.webp", tier: "EPIC" },
   ```

### Adding a whole new game

1. Drop the framed WebPs into a new `done/<GameName>/` directory.
2. Drop a logo into `logos/<gamename>.webp`.
3. Add a new entry at the end of the `SECTIONS` array in `products.js`.

That's it.

## Ideas for more keychains (suggested for Stan)

Already mentioned on the site, but here's the full brain-dump:

- **Blox Fruits** — Dragon, Dough, Buddha, Leopard, Soul fruits
- **Doors** — Rush, Ambush, Seek, Screech, Figure
- **Murder Mystery 2** — Chroma Lightbringer, classic knives
- **Forsaken** — survivor + killer character icons
- **Steal a Brainrot** — top brainrot characters
- **Adopt Me** — Shadow Dragon, Frost Dragon, Bee, Unicorn
- **Pet Simulator 99** — Huge pets, Titanic pets
- **Skibidi Toilet** — yep
- **Grow a Garden** — rare seeds, mythic plants
- **Anime Defenders / Anime Adventures** — favourite units
- **Tower Defense Simulator** — Commander, Accelerator
- **Brookhaven** — house key, car key (literally a key on a keychain — meta)

## Files

```
pzf_keychain/
├── index.html       # the page
├── styles.css       # all styling
├── app.js           # renders product cards
├── products.js      # ⭐ edit me — name, price, image, Stripe link
├── README.md        # this file
└── done/            # the keychain photos
```

Made with ❤️ and a glue gun.
