import random
import re

from burds import m_burds
from places import pm_places

# tweaking Settings
TIER_ORDER = ["F", "D", "C", "B", "A", "S"]

# chances (%), before luck
BASE = {"F": 55, "D": 25, "C": 12, "B": 5, "A": 2.5, "S": 0.5}

# luck for higher tiers (higher tiers = high luck, lower tiers = low luck)
LUCK_EXP = 0.5

# different tiers appear in that biome
BIOME_TIER = {
    "Urban Park": ["F", "D"],
    "Lowland Forest": ["F", "D", "C"],
    "Coastal Wetland": ["F", "D", "C", "A", "S"],
    "Island Forest": ["F", "D", "C", "A"],
    "Deep Jungle": ["D", "C", "A", "S"],
    "Montane": ["D", "C", "B", "A"],
}

# state
STATES = [
    "Perlis",
    "Kedah",
    "Penang",
    "Perak",
    "Kelantan",
    "Terengganu",
    "Pahang",
    "Selangor",
    "Kuala Lumpur",
    "Putrajaya",
    "Negeri Sembilan",
    "Melaka",
    "Johor",
]


# places
def build_place():
    place = []
    for p in pm_places:
        raw = p["name"]
        biome = p.get("biome", "").strip()
        if biome not in BIOME_TIER:
            raise ValueError(
                f"{raw!r} has biome {biome!r}; might be one of {list(BIOME_TIER)}"
            )
        if "(" in raw:
            pieces = raw.split("(")
            display = pieces[0].strip()
            state_txt = pieces[1].replace(")", "")
            states = [s.strip() for s in state_txt.split("/")]
        else:
            display = raw
            states = []
        states = [s for s in states if s in STATES]
        if not states:
            print("[warning]", raw, "has no known states in brackets :[")
        place.append({"name": display, "biome": biome, "states": states})
    return place


PLACE = build_place()
PLACE_BY_STATE = {}
for place in PLACE:
    for state in place["states"]:
        PLACE_BY_STATE.setdefault(state, []).append(place)


# Spawn
def spwn_burd(place, luck=1.0):
    biome = place["biome"]
    allow_tier = BIOME_TIER[biome]

    # burd tier that is allowed
    pool = [
        b
        for b in m_burds
        if b["rarity"] in allow_tier and biome in b.get("habitats", [biome])
    ]
    count = min(random.randint(4, 5), len(pool))
    chosen = []
    for _ in range(count):
        birds_ptier = {}
        for b in pool:
            birds_ptier[b["rarity"]] = birds_ptier.get(b["rarity"], 0) + 1

        weights = []
        for b in pool:
            tier = b["rarity"]
            t_index = TIER_ORDER.index(tier)
            t_weight = BASE[tier] * (luck ** (t_index * LUCK_EXP))
            weights.append(t_weight / birds_ptier[tier])

        pick = random.choices(pool, weights=weights, k=1)[0]
        chosen.append(pick)
        pool.remove(pick)
    return chosen


if __name__ == "__main__":
    print(f"Loaded {len(m_burds)} birds and {len(PLACE)} places \n")
    print("Place per state:")
    for state in STATES:
        names = [p["name"] for p in PLACE_BY_STATE.get(state, [])]
        print(f"{state:16s} {len(names)}  {','.join(names)}")

    test_place = PLACE_BY_STATE["Pahang"][0]
    print(f"\n5 sample hunts at {test_place['name']} ({test_place['biome']})")
    for _ in range(5):
        burds = spwn_burd(test_place)
        print(" " + ", ".join(f"{b['name']} [{b['rarity']}]" for b in burds))
    print(f"\nTier mix over 5000 hunts at {test_place['name']}:")
    for luck in {1.0, 2.0}:
        cts = {}
        total = 0
        for _ in range(5000):
            for b in spwn_burd(test_place, luck):
                cts[b["rarity"]] = cts.get(b["rarity"], 0) + 1
                total += 1
        mix = {t: f"{100 *cts[t]/total:.1f}%" for t in TIER_ORDER if t in cts}
        print(f" luck {luck}: {mix}")
    for b in m_burds:
        if not isinstance(b["points"], int):
            print("[warning] points is not a number for", b["name"], repr(b["points"]))
