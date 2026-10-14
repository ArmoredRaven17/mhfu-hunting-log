"""Build docs/data.js and the icon folders from the MHFU Lookup app's data.

    python scripts/build_data.py "C:\\Coding Repos\\MHFU App"

Unlike the 3U and 4U logs, nothing here reads the game directly. The quest list is the MHFU
Lookup app's (web/public/data/quests.json), which is where the MHFU quest work already lives:
its fee, reward, time limit and description fields were checked against the game's f5xxx quest
bundles (that repo's docs/rom-quest-params.md), the rest is community data. This script only
reshapes it into the hunting log's quest shape and copies the icons the log needs.

INPUTS (under <MHFU App>/web/public)
  data/quests.json   [{ slug, category, ranks: [{ stars, label, quests: [...] }] }]
                     A quest: name, objective, area, time ("50min"), fee ("750z"), reward,
                     monsters (every monster in the quest, small ones and intruders included),
                     key, urgent, description ("Client: text"), environment, and sometimes
                     unlock, notes, danger (Training), loadouts (Training).
  data/weapons.json  [{ type, name, sort_order, ... }] — weapon names, for autocomplete only.
  data/items.json    [{ name, icon }] — the icon for a delivery quest's item.
  assets/Monsters/   <slug>.png monster icons, 65x65.
  assets/Items/      <icon>.png item icons.
  assets/WeaponTypes/<Class>.png weapon class icons.

OUTPUT QUEST SHAPE
  Id         "<category slug>/<stars>/<name>". The source has no quest numbers, and names repeat
             across boards and stars ("Absolute Power" is a Guild 3★ and a Village Elder quest),
             so the key is the quest's place in the app's own list. Unique; the script checks.
  Type       Elder | Nekoht | Guild | Training
  Level      Elder 1-6, Nekoht 7-9, Guild 1-8 then G1-G3 stored as 9-11, Training 1-6 by
             course (Basic, Weapon Mastery, Battle, Special, G Lv, Group).
  Monsters   the targets: monsters named in the objective, in objective order. "Hunt all of
             the Large Monsters" takes the quest's large monsters. Deliveries (Khezu Whelps,
             Popo Tongues…) have none: the monster is the item's source, not the target.
  Icon       first target, else the delivered item (Paw Pass Ticket for gathering quests).
  Hunt / Capture / SmMonsters / Repel / Delivery / Gathering — from the objective's verb.
  Arena      fought in an arena locale (Arena, Great Arena, Moat Arena).
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# Category slug -> (Type, level of its first rank). Guild LR/HR stars are already 1-8; G rank's
# own 1-3 are shifted to 9-11. Training courses each have one rank and become levels 1-6.
CATEGORY = {
    "village_low_rank_elder": "Elder",
    "village_high_rank_nekoht": "Nekoht",
    "guild_low_rank": "Guild",
    "guild_high_rank": "Guild",
    "guild_g_rank": "Guild",
}
TRAINING = ["training_basic", "training_weapon_mastery", "training_battle",
            "training_special", "training_g_lv", "training_group"]

# Monsters that are never the point of a "Hunt all of the Large Monsters" quest. Everything
# in quests.json's monster lists that isn't here is a large monster.
SMALL = {
    "Felyne", "Melynx", "Shakalaka", "Vespoid", "Hornetaur", "Great Thunderbug",
    "Anteka", "Popo", "Kelbi", "Mosswine", "Aptonoth", "Apceros",
    "Giaprey", "Velociprey", "Genprey", "Ioprey", "Remobra", "Cephalos",
    "Conga", "Blango", "Bullfango", "Hermitaur", "Ceanataur",
}
# Spellings in the source that name a monster differently from its monster list.
ALIASES = {"Ashen Lao-Shan Lung": "Ash Lao-Shan Lung"}
# Monster name -> icon file stem in assets/Monsters, where the plain slug isn't it.
ICON_SLUG = {
    "Furious Rajang": "golden_rajang",
    "Ash Lao-Shan Lung": "ashen_lao-shan_lung",
    "Question Mark": "_unknown",
}
# Item name -> items.json name, where the objective's wording isn't an item in the list.
ITEM_ALIAS = {}

LOCALE_FIX = {
    "Desert(Day)": "Desert (Day)",
    "Desert(Night)": "Desert (Night)",
    "Snowy Mountain (Day)": "Snowy Mountains (Day)",
}
ARENAS = {"Arena", "Great Arena", "Moat Arena"}

WEAPON_ORDER = ["Great Sword", "Long Sword", "Sword and Shield", "Dual Blades", "Hammer",
                "Hunting Horn", "Lance", "Gunlance", "Light Bowgun", "Heavy Bowgun", "Bow"]
WEAPON_SOURCE = {"Sword and Shield": "Sword & Shield"}


def slug(name):
    """The MHFU app's monster icon file stem: lowercase, words joined by _, hyphens kept
    except in Kut-Ku (blue_yian_kut_ku) — matched by trying both."""
    s = name.lower().replace("'", "")
    return re.sub(r"[^a-z0-9-]+", "_", s).strip("_")


def stem(name):
    """File stem the app derives from a display name: spaces become underscores."""
    return name.replace(" ", "_")


def number(text):
    m = re.search(r"\d+", text or "")
    return int(m.group()) if m else 0


def find_targets(objective, monsters):
    """Monsters named in the objective, longest name first so "Pink Rathian" isn't also read as
    "Rathian", returned in objective order."""
    text = objective.lower()
    for a, b in ALIASES.items():
        text = text.replace(a.lower(), b.lower())
    found = []
    for m in sorted(monsters, key=len, reverse=True):
        for hit in re.finditer(re.escape(m.lower()), text):
            found.append((hit.start(), m))
            text = text[:hit.start()] + "#" * len(m) + text[hit.end():]
    return [m for _, m in sorted(found)]


def find_item(objective, items):
    """The delivered item's name, tolerating plurals ("3 Goldenfish", "20 Special Mushrooms",
    "15 Pieces of Coal")."""
    text = objective.lower()
    for a, b in ITEM_ALIAS.items():
        text = text.replace(a.lower(), b.lower())
    best = None
    for name in items:
        if re.search(r"\b" + re.escape(name.lower()) + r"(s|es)?\b", text):
            if best is None or len(name) > len(best):
                best = name
    return best


def main(app_dir):
    pub = Path(app_dir) / "web" / "public"
    groups = json.loads((pub / "data" / "quests.json").read_text(encoding="utf-8"))
    weapons = json.loads((pub / "data" / "weapons.json").read_text(encoding="utf-8"))
    items = json.loads((pub / "data" / "items.json").read_text(encoding="utf-8"))
    item_icon = {i["name"]: i["icon"] for i in items if i.get("icon")}

    # Every monster any quest lists, with "Yian Kut-Ku?" (At Birds' Hill…, which hides its
    # target behind a "?") read as the monster it is.
    all_monsters = sorted({m.rstrip("?") for g in groups for r in g["ranks"]
                           for q in r["quests"] for m in q["monsters"]})
    known = set(all_monsters) | set(ALIASES.values())

    quests, ids = [], set()
    icons_needed = {}   # stem -> source file
    warnings = []

    for g in groups:
        sl = g["slug"]
        if sl in TRAINING:
            typ = "Training"
        elif sl in CATEGORY:
            typ = CATEGORY[sl]
        else:
            sys.exit(f"Unknown quest category {sl!r} — add it to CATEGORY or TRAINING.")
        for r in g["ranks"]:
            if typ == "Training":
                level = TRAINING.index(sl) + 1
            elif sl == "guild_g_rank":
                level = 8 + r["stars"]
            else:
                level = r["stars"]
            for q in r["quests"]:
                qid = f"{sl}/{r['stars']}/{q['name']}"
                if qid in ids:
                    sys.exit(f"Duplicate quest id {qid!r}")
                ids.add(qid)

                listed = [m.rstrip("?") for m in q["monsters"]]
                obj = q["objective"].strip().rstrip(".!").strip()
                verb = obj.split()[0].lower()
                delivery = verb == "deliver"
                gathering = verb == "survive"
                repel = verb in ("defend", "kill") or "repel" in obj.lower()
                capture = verb == "capture"

                if delivery or gathering:
                    targets = []
                elif re.search(r"\ball (of the )?large monsters\b", obj, re.I):
                    targets = [m for m in dict.fromkeys(listed) if m not in SMALL]
                else:
                    # The objective can name the base monster where the quest holds a variant
                    # ("Hunt a Rajang" in Rajang Training, which is Furious Rajang).
                    targets = [next((m for m in listed if m != t and m.endswith(" " + t)), t)
                               if t not in listed else t
                               for t in find_targets(obj, known)]
                    if not targets:
                        warnings.append(f"no target in {qid}: {obj!r}")
                    for t in targets:
                        if t not in listed and t not in ALIASES.values():
                            warnings.append(f"target {t} not in {qid}'s monster list {listed}")

                small_only = bool(targets) and all(t in SMALL for t in targets)

                icon = None
                if targets:
                    icon = targets[0]
                else:
                    item = find_item(obj, item_icon)
                    if item:
                        icon = item
                        icons_needed[stem(item)] = pub / "assets" / "Items" / (item_icon[item] + ".png")
                    else:
                        warnings.append(f"no icon for {qid}: {obj!r}")
                        icon = "Question Mark"

                desc = (q.get("description") or "").strip()
                client = desc.split(":", 1)[0].strip() if ":" in desc[:40] else ""
                area = LOCALE_FIX.get(q["area"], q["area"])

                quests.append({
                    "Id": qid,
                    "Type": typ,
                    "Level": level,
                    "Name": q["name"],
                    "Main": obj,
                    "Locale": area,
                    "Monsters": targets,
                    "Icon": icon,
                    "Urgent": bool(q.get("urgent")),
                    "Key": bool(q.get("key")),
                    "Hunt": bool(targets) and not small_only and not capture and not repel,
                    "Capture": capture,
                    "SmMonsters": small_only,
                    "Repel": repel,
                    "Delivery": delivery,
                    "Gathering": gathering,
                    "Arena": area in ARENAS,
                    "Unstable": q.get("environment") == "Unstable",
                    "Minutes": number(q.get("time")),
                    "Fee": number(q.get("fee")),
                    "Reward": number(q.get("reward")),
                    "Client": client,
                    "Unlock": (q.get("unlock") or "").strip(),
                    "Notes": (q.get("notes") or "").strip(),
                })

    # Monster icons: every target, every theme swatch, and the "?" fallback.
    mon_dir = pub / "assets" / "Monsters"
    theme = ["Teostra", "Rathalos", "Cephadrome", "Daimyo Hermitaur", "Tigrex", "Rajang",
             "Emerald Congalala", "Gendrome", "Green Plesioth", "Rathian", "Basarios",
             "Blue Yian Kut-Ku", "Azure Rathalos", "Kirin", "Shogun Ceanataur", "Plesioth",
             "Black Diablos", "Velocidrome", "Purple Gypceros", "Lunastra", "Yian Garuga",
             "Chameleos", "Pink Rathian", "Congalala", "Akantor", "Diablos", "Gravios",
             "Bulldrome", "Kushala Daora", "Silver Rathalos", "Question Mark"]
    for name in sorted({t for q in quests for t in q["Monsters"]} | set(theme) | {"Question Mark"}):
        cands = [ICON_SLUG.get(name), slug(name), slug(name).replace("-", "_")]
        src = next((mon_dir / (c + ".png") for c in cands if c and (mon_dir / (c + ".png")).exists()), None)
        if not src:
            sys.exit(f"No icon for monster {name!r} in {mon_dir}")
        icons_needed[stem(name)] = src

    out_icons = DOCS / "assets" / "MonsterIcons"
    if out_icons.exists():
        shutil.rmtree(out_icons)
    out_icons.mkdir(parents=True)
    for st, src in sorted(icons_needed.items()):
        shutil.copyfile(src, out_icons / f"MHFU-{st}_Icon.png")

    # Weapons: names in the app's tree order, de-duplicated, under the log's class labels.
    names = {}
    for w in sorted(weapons, key=lambda w: (w["type"], w.get("sort_order", 0))):
        names.setdefault(w["type"], [])
        if w["name"] not in names[w["type"]]:
            names[w["type"]].append(w["name"])
    weapon_names, weapon_icons = {}, {}
    out_w = DOCS / "assets" / "WeaponIcons"
    if out_w.exists():
        shutil.rmtree(out_w)
    out_w.mkdir(parents=True)
    for cls in WEAPON_ORDER:
        src_cls = WEAPON_SOURCE.get(cls, cls)
        if src_cls not in names:
            sys.exit(f"weapons.json has no {src_cls!r}")
        weapon_names[cls] = names[src_cls]
        key = cls.lower().replace(" ", "_")
        weapon_icons[cls] = key
        shutil.copyfile(pub / "assets" / "WeaponTypes" / (src_cls.replace(" & ", "_and_").replace(" ", "_") + ".png"),
                        out_w / f"icon_{key}.png")

    data = {
        "quests": quests,
        "weapons": weapon_names,
        "weaponIcons": weapon_icons,
        "icons": sorted(icons_needed),
    }
    js = ("// Generated by scripts/build_data.py from the MHFU Lookup app's data. Do not edit by hand.\n"
          "// Quest and weapon data: CC BY-SA 4.0, from the Monster Hunter community wikis (see NOTICE.md).\n"
          "window.MHFU_LOG_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    (DOCS / "data.js").write_text(js, encoding="utf-8", newline="\n")

    for w in warnings:
        print("warning:", w)
    by_type = {}
    for q in quests:
        by_type[q["Type"]] = by_type.get(q["Type"], 0) + 1
    print(f"{len(quests)} quests {by_type}, {len(icons_needed)} icons, "
          f"{sum(map(len, weapon_names.values()))} weapon names")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
