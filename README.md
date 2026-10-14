# MHFU Hunting Log

A logbook for **Monster Hunter Freedom Unite**. Pick a quest, record what you were after, what
you wore, who came along and how it went, and build up a running record of your hunts. A port of
the [MH3U Hunting Log](https://github.com/ArmoredRaven17/mh3u-hunting-log) and the
[MHGU Hunting Log](https://github.com/ArmoredRaven17/MHGU-Hunting-Log), with its quest data taken
from the same author's MHFU LookUp app.

```
Quest: Guild G3★ / The Final Invitation / Rajang
Locale: Great Arena
Weapon: Hidden Saber
Hunting Party: Raven
Carts: 0
Outcome: Success
Clear Time: 18'32"42
```

That's what **Copy Selected** produces, ready to paste into Discord.

## Features

- **Quest browser**: 458 quests (95 Village Elder, 61 Nekoht, 255 Guild Hall up to G3★, 47
  Training School), grouped by board and star in the game's order, searchable by name, monster
  or locale. Picking one fills in its locale and shows its objective, time limit, fee, reward and
  client, with Urgent, Key, Hunt, Capture, Delivery, Gathering and Arena pills, and any unlock
  condition or special rule the quest has.
- **Per-entry fields**: date, locale, your own objective, armor, weapon (with a class picker that
  supplies the class icon and every weapon name as autocomplete), a party of up to four, carts,
  outcome, clear time and notes.
- **Farming** and **Timestamp** switches, autosave, `.json` save files, and the monster-icon
  themes shared with the other apps, all as in the GU log.

Downloadable Event Quests and the Treasure quests aren't in the quest list, so they aren't here.

## Where the data comes from

[scripts/build_data.py](scripts/build_data.py) reads the MHFU LookUp app's data
(`web/public/data/quests.json`, `weapons.json`, `items.json`) and its icons. That data comes from
the Monster Hunter community wikis (Monster Hunter Wiki on Fandom, monsterhunterwiki.org and the
MHP2G @wiki) under CC BY-SA 4.0, with the quests' fee, reward, time limit and description checked
against the game's own quest files. The script reshapes it: board and star, the quest's targets
(read from its objective), and an icon (the first target, or the item delivered).

## Running it

No build step for the app. Open `docs/index.html`, or serve `docs/`:

```
python -m http.server 5621 --directory docs
```

## Regenerating data

Needs a checkout of the MHFU LookUp app and Python 3.10+:

```
python scripts/build_data.py "C:\Coding Repos\MHFU App"
```

This rewrites `docs/data.js`, `docs/assets/MonsterIcons/` and `docs/assets/WeaponIcons/`.

## Cache busting

GitHub Pages caches assets by full URL. When you change `styles.css`, `app.js` or `data.js`, bump
the `?v=N` query string on its tag in `docs/index.html`.

## AI assistance

Most of this project (the port, the data script and this README) was written with
[Claude Code](https://claude.com/claude-code), Anthropic's AI coding tool, working from the author's
direction and reviewed before landing.

## Licensing

Code is MIT (see [LICENSE](LICENSE)). The quest and weapon data in `docs/data.js` is CC BY-SA 4.0,
from the community wikis above; the game itself and its icons are Capcom's. See
[NOTICE.md](NOTICE.md).
Monster Hunter Freedom Unite is © Capcom Co., Ltd.; this is an unofficial fan project.
