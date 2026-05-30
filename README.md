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

### 2. Create one Payment Link per keychain

For each keychain in the shop:

1. In the Stripe dashboard, go to **Product catalogue → Add product**.
2. Name it (e.g. "Assault Rifle Keychain"), set the price (e.g. £3 GBP).
3. Save, then on the product page click **Create payment link**.
4. Important settings:
   - ✅ **Collect customer's name** (so Stan knows who to give it to)
   - ✅ Add a custom field: **"School class / year"**
   - ❌ Do NOT collect a shipping address (school pickup only)
   - Set quantity limits if you like (e.g. max 3 per order)
5. Copy the link — it'll look like `https://buy.stripe.com/abc123xyz`.

### 3. Paste each link into `products.js`

Open `products.js` and replace each `REPLACE_ME_...` URL with the real link:

```js
{
  name: "Assault Rifle",
  // ...
  paymentLink: "https://buy.stripe.com/abc123xyz",   // ← paste here
}
```

Reload the page — done. Until you replace a link, that item's BUY button
will show a friendly "Stan is still setting up payments" message instead of
breaking.

### 4. (Optional) Test mode first

While you're trying things out, toggle to **Test mode** in the Stripe
dashboard (top-right). Test-mode Payment Links accept test card
`4242 4242 4242 4242` so you can pretend-buy without spending real money.

## Editing the shop

| Want to…                          | Edit this file       |
| --------------------------------- | -------------------- |
| Change a price                    | `products.js`        |
| Add/remove a keychain             | `products.js`        |
| Change a description or rarity    | `products.js`        |
| Change colours / fonts            | `styles.css`         |
| Change page text (hero / about)   | `index.html`         |

### Adding a new keychain

1. Drop the photo into `done/` (square PNG, ~512×512 works great).
2. Add a new entry at the bottom of the `PRODUCTS` array in `products.js`:

```js
{
  name: "Dragon Fruit",
  image: "done/Dragon Fruit.png",
  tier: "MYTHIC",   // COMMON | RARE | EPIC | LEGENDARY | MYTHIC
  desc: "Breathes fire. Sort of. Not really.",
  price: 4,
  paymentLink: "https://buy.stripe.com/your_new_link",
},
```

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
