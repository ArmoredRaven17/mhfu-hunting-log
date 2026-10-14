# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

A static single-page web app: a hunting logbook for Monster Hunter Freedom Unite, ported from the
[MH3U Hunting Log](../mh3u-hunting-log) (itself a port of the
[MHGU Hunting Log](../MHGU%20Hunting%20Log)). The user picks a quest and records what they were
after, what they wore, who came along and how it went; entries accumulate into a running log they
can copy out as plain text.

No build step for the app, no framework, no modules. `docs/app.js` is one IIFE, `docs/styles.css`
is hand-written, `docs/data.js` is generated.

GitHub Pages serves `docs/` through the "Deploy Pages" Actions workflow on push to `master`, like
the other MH apps.

## Relationship to the 3U Hunting Log

A port, not a fork that tracks it. The editor, logbook, farming/timestamp modes, drafts, save
files and copy format are the GU app's, and its CLAUDE.md explains the reasoning behind each
(resetEditor vs exitEditMode, the dirty gate, why Locale survives a quest switch, the clear-time
mask). What changed for MHFU:

- **Quest data** comes from the [MHFU Lookup](../MHFU%20App) app's `quests.json`, not from the
  game. See Data.
- **Boards**: Village Elder 1-6★, Nekoht 7-9★, Guild Hall 1-8★ then G1-G3★ (stored as levels
  9-11), and the Training School's six courses (levels 1-6: Basic, Weapon Mastery, Battle,
  Special, G Lv, Group). Shown as "Village Elder 3★", "Nekoht 8★", "Guild G2★",
  "Training: Battle".
- **Quest key** is `"q:" + Id`, where `Id` is `<category slug>/<stars>/<name>` from the source
  list. The source has no quest numbers and names repeat across boards ("Absolute Power" is a
  Guild and a Village Elder quest). A renamed quest falls back to the entry's snapshot.
- **Unlock and notes**: the quest head shows the source's `unlock` text and its special
  conditions (`notes`) on two lines under the details, where 3U derived an unlock rule.
  "Unstable" in the details line is the quest's environment (intruders can show up).
- **Pills**: Hunt, Small Monsters, Capture, Repel (Defend / Kill or Repel), Delivery,
  Gathering (Survive until Time Over), Arena (any arena locale), plus Urgent and Key.
- 11 weapon classes (no Switch Axe). Locales keep the time of day ("Jungle (Night)").
- Storage keys are `mhfu-log-*`; save files are `{ app: "mhfu-hunting-log", version: 1, entries }`.
- The theme palette is the family's 31 hexes and LEGACY_HEX, named for MHFU monsters (GU's name
  where MHFU has the monster, else the MH4U apps' pick).

## Data

`python scripts/build_data.py "C:\Coding Repos\MHFU App"` rewrites `docs/data.js`
(`window.MHFU_LOG_DATA = { quests, weapons, weaponIcons, icons }`) and the icon folders. It reads
`web/public/data/quests.json`, `weapons.json`, `items.json` and the app's monster, item and
weapon-class icons. The script header documents the output shape. Worth knowing:

- 458 quests: 95 Village Elder, 61 Nekoht, 255 Guild, 47 Training. No Event (DLC) or Treasure
  quests: they aren't in the source list.
- The source's `monsters` is every monster in the quest, small ones and intruders included, so
  targets are read from the objective (longest name first, so "Pink Rathian" isn't also
  "Rathian"). "Hunt all of the Large Monsters" takes the listed monsters minus `SMALL`.
  Deliveries have no targets: the Khezu in "Deliver 5 Khezu Whelps" is the item's source.
- Where the objective names the base monster and the list holds a variant, the variant wins
  (Rajang Training is Furious Rajang).
- Two source quirks are left as warnings, not fixed: The Cherry Blossom Rathian's objective says
  Pink Rathian but its list says Rathian (the objective is used), and The Ruler of the Snow has
  an empty monster list (Blangonga comes from the objective).
- A quest with no target takes the delivered item's icon (`items.json`), the Paw Pass Ticket for
  gathering quests. The item icons are the MHFU Lookup app's 4G-style set.
- Fixes to quest data belong in the MHFU Lookup app; rebuild here afterwards.
- The source data is **CC BY-SA 4.0** (community wikis, see NOTICE.md), so `data.js` is too.
  Keep the attribution in NOTICE.md, the README and the About dialog.

## Critical: cache busting

Bump the `?v=N` on `styles.css`, `app.js` or `data.js` in `docs/index.html` whenever that file
changes.

## Conventions

All user text goes into the DOM via `textContent`/`.value` through `el()` — never `innerHTML`.
An entry's `quest` snapshot is read back from save files as untrusted shape (`questTargets` and
`liveQuest` guard it).
