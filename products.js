// ============================================================
// STAN'S KEYCHAIN SHOP — PRODUCT LIST
// ============================================================
// To change a price, edit the `price` field below.
// To hook up Stripe, replace each `paymentLink` with the
// real Stripe Payment Link from https://dashboard.stripe.com
// (See README.md for step-by-step instructions.)
// ============================================================

const CURRENCY = "£";
const DEFAULT_PRICE = 3;

const PRODUCTS = [
  {
    name: "Assault Rifle",
    image: "done/Assault Rifle.webp",
    tier: "EPIC",
    desc: "Spray and pray, but make it hangable.",
    price: DEFAULT_PRICE,
    paymentLink: "https://buy.stripe.com/REPLACE_ME_assault_rifle",
  },
  {
    name: "Crossbow",
    image: "done/Crossbow.webp",
    tier: "RARE",
    desc: "Silent. Deadly. Dangles from your bag.",
    price: DEFAULT_PRICE,
    paymentLink: "https://buy.stripe.com/REPLACE_ME_crossbow",
  },
  {
    name: "Flamethrower",
    image: "done/Flamethrower.webp",
    tier: "LEGENDARY",
    desc: "Toasty vibes. Does NOT actually shoot fire (sorry mum).",
    price: DEFAULT_PRICE,
    paymentLink: "https://buy.stripe.com/REPLACE_ME_flamethrower",
  },
  {
    name: "Grenade",
    image: "done/Grenade.webp",
    tier: "COMMON",
    desc: "Pull the pin… actually don't, this one's plastic.",
    price: DEFAULT_PRICE,
    paymentLink: "https://buy.stripe.com/REPLACE_ME_grenade",
  },
  {
    name: "Katana",
    image: "done/Katana.webp",
    tier: "EPIC",
    desc: "Ninja drip. Cuts through absolutely nothing.",
    price: DEFAULT_PRICE,
    paymentLink: "https://buy.stripe.com/REPLACE_ME_katana",
  },
  {
    name: "Knife",
    image: "done/Knife.webp",
    tier: "COMMON",
    desc: "Sharp-looking. (It is not actually sharp.)",
    price: DEFAULT_PRICE,
    paymentLink: "https://buy.stripe.com/REPLACE_ME_knife",
  },
  {
    name: "RPG",
    image: "done/RPG.webp",
    tier: "LEGENDARY",
    desc: "Big boom energy. Zero actual booms.",
    price: DEFAULT_PRICE,
    paymentLink: "https://buy.stripe.com/REPLACE_ME_rpg",
  },
  {
    name: "Scythe",
    image: "done/Scythe.webp",
    tier: "LEGENDARY",
    desc: "For when you want to look extra spooky in maths.",
    price: DEFAULT_PRICE,
    paymentLink: "https://buy.stripe.com/REPLACE_ME_scythe",
  },
  {
    name: "Shorty",
    image: "done/Shorty.webp",
    tier: "RARE",
    desc: "Tiny gun. Massive drip.",
    price: DEFAULT_PRICE,
    paymentLink: "https://buy.stripe.com/REPLACE_ME_shorty",
  },
  {
    name: "Snatchel",
    image: "done/Snatchel.webp",
    tier: "MYTHIC",
    desc: "If you know, you know. (If you don't, ask a Rivals main.)",
    price: DEFAULT_PRICE,
    paymentLink: "https://buy.stripe.com/REPLACE_ME_snatchel",
  },
  {
    name: "Sniper",
    image: "done/Sniper.webp",
    tier: "EPIC",
    desc: "Headshots from across the playground. (Don't actually.)",
    price: DEFAULT_PRICE,
    paymentLink: "https://buy.stripe.com/REPLACE_ME_sniper",
  },
  {
    name: "War Horn",
    image: "done/War Horn.webp",
    tier: "MYTHIC",
    desc: "TOOOOOT. (It does not actually toot. Use your mouth.)",
    price: DEFAULT_PRICE,
    paymentLink: "https://buy.stripe.com/REPLACE_ME_war_horn",
  },
];
