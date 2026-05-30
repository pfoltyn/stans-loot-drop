// ============================================================
// STAN'S LOOT DROP — catalog
// ============================================================
// One product (the keychain), two icon catalogs (Rivals, Blox Fruits).
// Customer picks one icon for FRONT and one for BACK.
//
// To change the price, edit KEYCHAIN.price below.
// To hook up Stripe, replace KEYCHAIN.paymentLink with a real Stripe
// Payment Link. Front/back choices are sent to Stripe via
// client_reference_id so Stan can see what to make. (See README.md.)
// ============================================================

const CURRENCY = "£";

const KEYCHAIN = {
  name: "Custom 2-Sided Keychain",
  price: 4,
  paymentLink: "https://buy.stripe.com/REPLACE_ME_keychain",
};

const SECTIONS = [
  {
    id: "rv",
    title: "Rivals",
    logo: "logos/rivals.webp",
    blurb:
      "Real keychains from the Rivals arena. Twelve weapons, all hangable.",
    icons: [
      { name: "Assault Rifle", image: "done/Rivals/Assault Rifle.webp", tier: "EPIC" },
      { name: "Crossbow",      image: "done/Rivals/Crossbow.webp",      tier: "RARE" },
      { name: "Flamethrower",  image: "done/Rivals/Flamethrower.webp",  tier: "LEGENDARY" },
      { name: "Grenade",       image: "done/Rivals/Grenade.webp",       tier: "COMMON" },
      { name: "Katana",        image: "done/Rivals/Katana.webp",        tier: "EPIC" },
      { name: "Knife",         image: "done/Rivals/Knife.webp",         tier: "COMMON" },
      { name: "RPG",           image: "done/Rivals/RPG.webp",           tier: "LEGENDARY" },
      { name: "Scythe",        image: "done/Rivals/Scythe.webp",        tier: "LEGENDARY" },
      { name: "Shorty",        image: "done/Rivals/Shorty.webp",        tier: "RARE" },
      { name: "Snatchel",      image: "done/Rivals/Snatchel.webp",      tier: "MYTHIC" },
      { name: "Sniper",        image: "done/Rivals/Sniper.webp",        tier: "EPIC" },
      { name: "War Horn",      image: "done/Rivals/War Horn.webp",      tier: "MYTHIC" },
    ],
  },
  {
    id: "bf",
    title: "Blox Fruits",
    logo: "logos/bloxfruits.webp",
    blurb:
      "Forty-one devil fruits. Eat them with your eyes only — they're plastic.",
    icons: [
      { name: "Blade Fruit",     image: "done/BloxFruits/Blade_Fruit.webp",     tier: "COMMON" },
      { name: "Blizzard Fruit",  image: "done/BloxFruits/Blizzard_Fruit.webp",  tier: "LEGENDARY" },
      { name: "Bomb Fruit",      image: "done/BloxFruits/Bomb_Fruit.webp",      tier: "COMMON" },
      { name: "Buddha Fruit",    image: "done/BloxFruits/Buddha_Fruit.webp",    tier: "LEGENDARY" },
      { name: "Control Fruit",   image: "done/BloxFruits/Control_Fruit.webp",   tier: "MYTHIC" },
      { name: "Creation Fruit",  image: "done/BloxFruits/Creation_Fruit.webp",  tier: "LEGENDARY" },
      { name: "Dark Fruit",      image: "done/BloxFruits/Dark_Fruit.webp",      tier: "EPIC" },
      { name: "Diamond Fruit",   image: "done/BloxFruits/Diamond_Fruit.webp",   tier: "RARE" },
      { name: "Dough Fruit",     image: "done/BloxFruits/Dough_Fruit.webp",     tier: "MYTHIC" },
      { name: "Dragon Fruit",    image: "done/BloxFruits/Dragon_Fruit.webp",    tier: "MYTHIC" },
      { name: "Eagle Fruit",     image: "done/BloxFruits/Eagle_Fruit.webp",     tier: "RARE" },
      { name: "Flame Fruit",     image: "done/BloxFruits/Flame_Fruit.webp",     tier: "RARE" },
      { name: "Gas Fruit",       image: "done/BloxFruits/Gas_Fruit.webp",       tier: "RARE" },
      { name: "Ghost Fruit",     image: "done/BloxFruits/Ghost_Fruit.webp",     tier: "RARE" },
      { name: "Gravity Fruit",   image: "done/BloxFruits/Gravity_Fruit.webp",   tier: "LEGENDARY" },
      { name: "Ice Fruit",       image: "done/BloxFruits/Ice_Fruit.webp",       tier: "RARE" },
      { name: "Kitsune Fruit",   image: "done/BloxFruits/Kitsune_Fruit.webp",   tier: "MYTHIC" },
      { name: "Light Fruit",     image: "done/BloxFruits/Light_Fruit.webp",     tier: "EPIC" },
      { name: "Lightning Fruit", image: "done/BloxFruits/Lightning_Fruit.webp", tier: "EPIC" },
      { name: "Love Fruit",      image: "done/BloxFruits/Love_Fruit.webp",      tier: "RARE" },
      { name: "Magma Fruit",     image: "done/BloxFruits/Magma_Fruit.webp",     tier: "EPIC" },
      { name: "Mammoth Fruit",   image: "done/BloxFruits/Mammoth_Fruit.webp",   tier: "LEGENDARY" },
      { name: "Pain Fruit",      image: "done/BloxFruits/Pain_Fruit.webp",      tier: "RARE" },
      { name: "Phoenix Fruit",   image: "done/BloxFruits/Phoenix_Fruit.webp",   tier: "LEGENDARY" },
      { name: "Portal Fruit",    image: "done/BloxFruits/Portal_Fruit.webp",    tier: "LEGENDARY" },
      { name: "Quake Fruit",     image: "done/BloxFruits/Quake_Fruit.webp",     tier: "EPIC" },
      { name: "Rocket Fruit",    image: "done/BloxFruits/Rocket_Fruit.webp",    tier: "COMMON" },
      { name: "Rubber Fruit",    image: "done/BloxFruits/Rubber_Fruit.webp",    tier: "RARE" },
      { name: "Sand Fruit",      image: "done/BloxFruits/Sand_Fruit.webp",      tier: "RARE" },
      { name: "Shadow Fruit",    image: "done/BloxFruits/Shadow_Fruit.webp",    tier: "LEGENDARY" },
      { name: "Smoke Fruit",     image: "done/BloxFruits/Smoke_Fruit.webp",     tier: "COMMON" },
      { name: "Sound Fruit",     image: "done/BloxFruits/Sound_Fruit.webp",     tier: "RARE" },
      { name: "Spider Fruit",    image: "done/BloxFruits/Spider_Fruit.webp",    tier: "RARE" },
      { name: "Spike Fruit",     image: "done/BloxFruits/Spike_Fruit.webp",     tier: "COMMON" },
      { name: "Spin Fruit",      image: "done/BloxFruits/Spin_Fruit.webp",      tier: "COMMON" },
      { name: "Spirit Fruit",    image: "done/BloxFruits/Spirit_Fruit.webp",    tier: "MYTHIC" },
      { name: "Spring Fruit",    image: "done/BloxFruits/Spring_Fruit.webp",    tier: "RARE" },
      { name: "T-Rex Fruit",     image: "done/BloxFruits/T-Rex_Fruit.webp",     tier: "MYTHIC" },
      { name: "Tiger Fruit",     image: "done/BloxFruits/Tiger_Fruit.webp",     tier: "RARE" },
      { name: "Venom Fruit",     image: "done/BloxFruits/Venom_Fruit.webp",     tier: "LEGENDARY" },
      { name: "Yeti Fruit",      image: "done/BloxFruits/Yeti_Fruit.webp",      tier: "EPIC" },
    ],
  },
];
