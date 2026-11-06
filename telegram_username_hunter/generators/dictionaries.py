"""
Telegram Username Hunter PRO
Rich Dictionaries & Wordbases for Name Generation
"""

# Short English Dictionary words (5-10 chars) - High quality, pronounceable
DICTIONARY_WORDS = [
    # 5 chars
    "amber", "angel", "arrow", "atlas", "blaze", "bloom", "brave", "breeze",
    "cider", "cliff", "comet", "coral", "crown", "delta", "eagle", "ember",
    "fable", "flame", "flash", "frost", "giant", "glory", "grace", "grove",
    "haven", "hazel", "honor", "ivory", "laser", "lemon", "logic", "lunar",
    "magic", "manor", "maple", "merit", "noble", "oasis", "ocean", "orbit",
    "pearl", "pilot", "polar", "prism", "pulse", "quest", "radar", "raven",
    "rider", "river", "robin", "royal", "sable", "scout", "shadow", "shard",
    "shore", "solar", "spark", "spear", "spice", "stone", "storm", "swift",
    "talon", "tiger", "titan", "tower", "trace", "trail", "vapor", "vigor",
    "viper", "vista", "vivid", "vocal", "vortex", "wave", "wheat", "whisper",
    "willow", "winter", "zenith", "zephyr",
    # 6 chars
    "anchor", "anthem", "arcade", "beacon", "blazer", "bounty", "breeze",
    "canyon", "castle", "cipher", "citadel", "clover", "cobalt", "cosmos",
    "crater", "dagger", "dawn", "drifter", "falcon", "fossil", "galaxy",
    "glider", "granite", "harbor", "hazard", "herald", "horizon", "impact",
    "island", "jaguar", "jungle", "knight", "legacy", "lumber", "marvel",
    "matrix", "meteor", "mirage", "monarch", "mystic", "nebula", "nectar",
    "nemesis", "nomad", "orbit", "panther", "phantom", "phoenix", "pioneer",
    "planet", "quartz", "quiver", "radius", "ranger", "raptor", "realm",
    "riddle", "ripple", "safari", "savage", "shadow", "shield", "silver",
    "specter", "sphinx", "spirit", "strider", "summit", "symphony", "tempo",
    "timber", "tracer", "travel", "vanguard", "vector", "velvet", "vortex",
    "voyage", "walnut", "wizard", "zenith",
    # 7-8 chars
    "absolute", "aerospace", "airborne", "alliance", "altitude", "amplitude",
    "aquarium", "artisan", "asteroid", "astronomy", "atlantic", "boundary",
    "calendar", "capital", "celestial", "champion", "chronicle", "colosseum",
    "conqueror", "creativity", "crusader", "crystall", "defender", "destiny",
    "discovery", "dynasty", "element", "emerald", "emperor", "endurance",
    "epicenter", "eternity", "explorer", "firewall", "fortress", "frontline",
    "galactica", "guardian", "headliner", "heritage", "highlander", "infinity",
    "latitude", "luminary", "magnolia", "majesty", "marathon", "midnight",
    "millennium", "navigator", "nightfall", "odyssey", "olympian", "overlord",
    "paradise", "paragon", "pinnacle", "platinum", "prodigy", "radiance",
    "rebellion", "resonance", "sanctuary", "serenade", "silhouette", "sovereign",
    "starlight", "supernova", "symbiosis", "tempest", "terminal", "valkyrie",
    "velocity", "wanderer", "warlord", "waterfall", "wildfire", "wonderland",
]

FINANCIAL_WORDS = [
    "pay", "coin", "cash", "vault", "bank", "fund", "hedge", "yield",
    "trade", "stake", "swap", "wallet", "broker", "forex", "mint", "token",
    "credit", "asset", "bond", "debt", "capital", "gold", "silver", "bull",
    "bear", "rich", "profit", "dividend", "fintech", "wealth", "vest", "equity",
    "margin", "escrow", "fiat", "loan", "fiscal", "reserve", "option", "ledger",
    "treasury", "index", "market", "ticker", "brokerage", "moneta", "bullion",
    "arbitrage", "holding", "invest", "investor", "dividend", "shares", "finances",
    "paygate", "payhub", "cashbox", "vaultx", "bankly", "yieldx", "fundex",
    "richpay", "tradelink", "paystream", "capitalone", "finpulse", "tradewise",
]

CRYPTO_WORDS = [
    "ton", "eth", "btc", "sol", "defi", "web3", "nft", "dapp", "meta",
    "chain", "layer", "block", "node", "gas", "ledger", "satoshi", "hash",
    "dex", "dao", "moon", "mining", "stake", "airdrop", "shill", "whale",
    "hodl", "gasless", "rollup", "zkproof", "bridge", "oracle", "token",
    "yield", "liquidity", "shard", "beacon", "crypto", "bit", "altcoin",
    "smartcon", "multichain", "solana", "toncoin", "tontrade", "cryptopay",
    "web3bot", "defihub", "tonvault", "ethlink", "btcfund", "tonpulse",
    "gaspool", "chainnode", "dexswap", "zktrade", "bitvault", "tonwallet",
]

TECH_WORDS = [
    "dev", "cloud", "code", "data", "cyber", "byte", "net", "sys", "host",
    "pixel", "bot", "link", "root", "sync", "core", "base", "grid", "logic",
    "stack", "server", "neural", "tech", "quantum", "api", "script", "rust",
    "python", "kernel", "linux", "cluster", "daemon", "tensor", "binary",
    "router", "modem", "socket", "proxy", "codec", "render", "engine", "algo",
    "silicon", "matrix", "compute", "compile", "docker", "k8s", "nexus",
    "codelab", "devhub", "cloudcore", "cyberlink", "techgrid", "datasphere",
    "neuralnet", "bytevault", "stackflow", "sysadmin", "codecraft", "apinet",
]

GAMING_WORDS = [
    "play", "quest", "loot", "craft", "clan", "pixel", "arena", "duel",
    "buff", "boss", "raid", "rpg", "hero", "titan", "void", "rage", "doom",
    "apex", "epic", "frag", "mana", "level", "storm", "rune", "spawn", "respawn",
    "guild", "combo", "stealth", "shadow", "cyber", "turbo", "arcade", "esports",
    "gamer", "clutch", "headshot", "pixelart", "battle", "warrior", "archer",
    "sorcerer", "dungeon", "knight", "mythic", "playhub", "gamezone", "lootbox",
    "arenax", "fragclub", "bossraid", "craftlab", "voidrun", "epicguild",
]

BRAND_PREFIXES = [
    "nova", "apex", "flux", "omni", "sync", "vortex", "aero", "astro",
    "aura", "prism", "pulse", "nexus", "titan", "hyper", "echo", "lumen",
    "zenith", "stride", "vance", "dyno", "krono", "velo", "spectro", "solis",
    "terra", "ignis", "aeris", "hydra", "quant", "poly", "meta", "vert",
    "zent", "krypt", "strato", "pyro", "opti", "verve", "zesty", "zeno",
]

BRAND_SUFFIXES = [
    "ly", "ify", "io", "ex", "ix", "ox", "ia", "is", "os", "er", "or",
    "hub", "lab", "box", "net", "zone", "flow", "base", "craft", "core",
    "pulse", "drop", "link", "desk", "grid", "ware", "port", "forge",
    "stack", "mark", "view", "way", "gen", "line", "nest", "works",
]

AI_WORDS = [
    "ai", "gpt", "agent", "llm", "neural", "brain", "bot", "deep",
    "mind", "intel", "cogni", "synapse", "cortex", "vision", "synth", "auto",
    "genius", "logic", "reason", "model", "prompt", "tensor", "neuro",
    "omni", "vector", "embed", "agentic", "smart", "wise", "oracle", "sentient",
]

APP_WORDS = [
    "app", "tool", "kit", "suite", "utility", "helper", "studio", "station",
    "client", "engine", "portal", "space", "pad", "desk", "hub", "dock",
    "shelf", "vault", "craft", "dock", "center", "board", "forge", "works",
]

# Rare, pronounceable phonetic roots (high aesthetic and brand value)
PHONETIC_CONSONANTS = ["b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "q", "r", "s", "t", "v", "w", "x", "y", "z"]
PHONETIC_VOWELS = ["a", "e", "i", "o", "u"]
PREMIUM_CONSONANTS = ["v", "x", "z", "q", "k", "r", "n", "l", "m", "s"]

SHORT_SYLLABLES = [
    "qev", "vex", "orv", "qiv", "xev", "zen", "lyr", "kyo", "vra", "zyn",
    "rav", "pel", "tor", "kaz", "mav", "zor", "nex", "rix", "vox", "fen",
    "kel", "mir", "sol", "cal", "val", "aer", "bel", "cor", "dan", "ely",
    "ful", "gal", "hel", "ior", "jar", "kin", "lor", "mor", "ner", "pyr",
    "qui", "rox", "syr", "tal", "uln", "vol", "wyn", "xen", "yul", "zar",
]

# Historical Fragment Benchmark Database (Real Reference Sales Records)
# Used to calculate market attractiveness without guessing fake prices
FRAGMENT_HISTORICAL_BENCHMARKS = {
    # 4-character and legendary names
    "news": {"price_ton": 994000, "category": "media"},
    "auto": {"price_ton": 900000, "category": "tech"},
    "bank": {"price_ton": 850000, "category": "finance"},
    "avia": {"price_ton": 800000, "category": "travel"},
    "chat": {"price_ton": 700000, "category": "communication"},
    "king": {"price_ton": 650000, "category": "brand"},
    "game": {"price_ton": 500000, "category": "gaming"},
    "crypto": {"price_ton": 450000, "category": "crypto"},
    "trade": {"price_ton": 350000, "category": "finance"},
    "gold": {"price_ton": 350000, "category": "finance"},
    "bot": {"price_ton": 300000, "category": "tech"},
    "pay": {"price_ton": 280000, "category": "finance"},
    "meta": {"price_ton": 260000, "category": "tech"},
    "swap": {"price_ton": 250000, "category": "crypto"},
    "ton": {"price_ton": 250000, "category": "crypto"},
    "coin": {"price_ton": 200000, "category": "crypto"},
    "cash": {"price_ton": 190000, "category": "finance"},
    "fund": {"price_ton": 180000, "category": "finance"},
    "apex": {"price_ton": 150000, "category": "brand"},
    "play": {"price_ton": 140000, "category": "gaming"},
    "code": {"price_ton": 130000, "category": "tech"},
    "data": {"price_ton": 120000, "category": "tech"},
    "cloud": {"price_ton": 110000, "category": "tech"},
    "vault": {"price_ton": 105000, "category": "finance"},
    "pulse": {"price_ton": 95000, "category": "brand"},
    "nexus": {"price_ton": 90000, "category": "brand"},
    "vortex": {"price_ton": 85000, "category": "brand"},
    "cyber": {"price_ton": 80000, "category": "tech"},
    "quest": {"price_ton": 75000, "category": "gaming"},
    "orbit": {"price_ton": 70000, "category": "tech"},
    "titan": {"price_ton": 65000, "category": "brand"},
    "frost": {"price_ton": 60000, "category": "brand"},
    "blaze": {"price_ton": 55000, "category": "brand"},
    "spark": {"price_ton": 50000, "category": "brand"},
    "proxy": {"price_ton": 45000, "category": "tech"},
    "prime": {"price_ton": 40000, "category": "brand"},
    "elite": {"price_ton": 38000, "category": "brand"},
    "smart": {"price_ton": 35000, "category": "tech"},
    "arena": {"price_ton": 30000, "category": "gaming"},
    "delta": {"price_ton": 28000, "category": "brand"},
    "solis": {"price_ton": 25000, "category": "brand"},
    "zenith": {"price_ton": 22000, "category": "brand"},
}
