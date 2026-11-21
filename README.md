# One Last Thing

**[Download One Last Thing](https://github.com/ashopedies/One-Last-Thing/releases)**

A small, location-aware checklist for **WoW Forever**. Arrive somewhere and see useful things to do before leaving: unfinished quest-chain pickups, class and profession training, vendor supplies, flight paths and repairs.

English and German clients are supported. Settings and supply amounts are saved **per character**. No purchases or training happen automatically. Automatic opening is suppressed inside instances and battlegrounds; `/olt` still works manually.

## Install

Open [Releases](https://github.com/ashopedies/One-Last-Thing/releases), choose a version and expand **Assets**. Download **OneLastThing-VERSION-forever.zip**; the automatically generated Source code archives are for development.

Extract the install ZIP into your Forever client's `Interface/AddOns` folder. You should have `Interface/AddOns/OneLastThing/OneLastThing.toc`, without an extra enclosing folder. Restart the game.

For updates through WowUp, use the **GitHub repository URL**, rather than a direct ZIP download link. Enable automatic updates in your chosen client. Publishing a new tagged release supplies the next update; editing repository files alone does not.

## Use

- `/olt` or `/onelastthing`: open the checklist.
- `/olt settings`: configure categories, supplies, appearance and ignored reminders.
- `/olt supply ITEM_ID AMOUNT`: set a custom supply amount; zero removes it.
- `/olt restore`: show reminders skipped this visit.
- `/olt status`: show data connections and compatibility diagnostics.

Drag the header to move the window. Click it to collapse; pending work stays visible as a count. Once the enabled checks finish successfully and the list is clear, the header fades to **OLT**. Missing or failed checks show **Some checks unavailable**; expand the checklist for details. Scroll with the mouse wheel and resize the window by dragging its bottom corner. The − / + buttons adjust font size in 5% steps (80–130%), saved per character. Category and subcategory checkboxes are in **Filter** beside the header. Disabled groups remain available there; expand a category with + to manage its children. Small category labels share reminder title lines where space permits, and hovering reveals full details. Default, Compact and Minimal layouts are available, with built-in Arial Narrow and optional SharedMedia fonts.

**Skip** returns next visit/reload. All districts within a capital share one visit. **Ignore** stays hidden until restored individually in Settings > Ignored reminders. Map, Skip and Ignore are directly available on rows in all three layouts; narrow and Minimal rows abbreviate Map/Skip to M/S. Completed tasks clear their own map pins; a waypoint you set afterward is preserved.

## Data addons

There are no hard addon dependencies. Coverage depends on the data providers installed and enabled:

| Addon | Used for |
| --- | --- |
| Attune | Unfinished quest chains, including class, dungeon and access chains |
| Questie / QuestieDB | Quest prerequisites, NPC locations, vendors and repair locations |
| DungeonJournal | Optional extra dungeon quest pickups and prerequisite steps; off by default |
| SkillUp Forever | Profession state and rank/cap reminders; not changing recipe shopping lists |
| TrainerSpells | Class spell ranks, city-specific Mage portal trainers, weapon skills and profession rank-trainer locations |
| NeavMedia | Optional fonts/media |
| LibSharedMedia-3.0 | Optional registered fonts, including embedded library copies |

The bottom settings section shows the actual loaded/available status. No other addon's settings are changed and no third-party database or media files are bundled.

Ordinary quest turn-ins are **off by default**, leaving regular questing to your quest tracker. To opt in, enable **Filter > Quests & chains > Other completed quests**. Turn-ins belonging to tracked important chains remain available independently. Explicit character choices are preserved across updates.

## Optional DungeonJournal support

In **Settings > Quests & chains**, enable **DungeonJournal dungeon quests (optional)**.
This character-specific option defaults off and supplements Attune. It requires the installed
DungeonJournal addon and Questie's quest eligibility data. Available local pickups and required
prerequisite steps are deduplicated with Attune by quest ID and follow the usual range,
class/profession/faction, level, completion and Skip/Ignore rules. Ordinary gray quests,
item-start tasks and unfinished hub placeholders are excluded. A gray prerequisite is shown
only when it leads to a relevant non-gray dungeon quest, with an explanation.

The adapter reads the installed data without changing DungeonJournal preferences or bundling
its database/assets. Tested against DungeonJournal 2.1.2 (Interface 16001). Unsupported/missing
data is reported when this source is enabled. Automatic instance suppression is unchanged.

## Profession progression

Routine profession recipes are not checklist tasks, including recipes offered by trainers you have visited. Rank upgrades, key books and progression quests remain available. The two First Aid bandage manuals are a curated exception, grouped as one vendor stop. Class spells still have individual Skip/Ignore controls for gold decisions.

The shared rank-reminder path supports all twelve professions: Alchemy, Blacksmithing, Enchanting, Engineering, Herbalism, Leatherworking, Mining, Skinning, Tailoring, First Aid, Cooking and Fishing. Reminders follow professions currently learned by your character. Native character data fills professions absent from SkillUp's crafting routes. Rank upgrades, the three Artisan progression quests and Expert books are checked independently of the next recipe steps; SkillUp remains an optional source of route information. Installed TrainerSpells data supplies rank-capable local trainers.

The three curated Expert rank books (First Aid, Cooking and Fishing) can be suggested before you can use them, with required/current skill and character level clearly shown. Only affordable known local offers are suggested; owned/banked copies and learned caps are excluded. At most two book/vendor reminders appear. Heavy Silk and Mageweave Bandage manuals form one additional eligible group from First Aid 125, excluding owned/banked or learned manuals. This is optional for the bandage route; it can be skipped or ignored as a group. Other professions do not get invented book purchases.

Eligible Enchanters (skill 200/225, character level 35+) get an Annora reminder near Uldaman's exterior approaches. Its pin marks the entrance; automatic checklists remain suppressed inside instances.

Dungeon, class, raid/access and profession progression reminders explain their purpose. The explanation follows installed data and does not promise an unrecorded reward. Hover any reminder for its full reason and destination details.

## Task order, distance and confidence

Dungeon pickups come first. Location-specific progression comes ahead of routine services available in many places; empty Ankhs/ammunition and broken gear receive an urgent position below dungeon pickups. Within the same priority and confidence level, nearer tasks come first. Existing quest eligibility and grey-quest filtering still apply.

Distances are approximate straight-line yards, not walking routes. If the client cannot provide world-coordinate geometry, the task says Distance unknown. Unverified suggestions use Check wording and availability details, rather than claiming live confirmation. Supply settings preview the cost of the entered target, including merchant bundles; amounts still save on Enter or focus loss.

## Reminder range

Orgrimmar, Undercity, Thunder Bluff, Stormwind, Ironforge and Darnassus show located reminders across the current city map. The exception never extends into adjacent zones or another capital. District changes keep the checklist visible while coordinates refresh, preserving visit skips, scroll position and filters.

Everywhere else, distance filtering defaults to **850 yards**. Change it under **Settings > General & location > Outside-city range (yards)**, from 250 to 2,000 yards in 50-yard steps. The value is saved per character and does not restrict capital reminders. Existing saved ranges are preserved. General profession-cap warnings have no physical destination and remain visible independently of distance.

## Supplies

Only items sold by vendors produce shopping reminders, and a usable seller location is needed. Spell relevance, class, bag stock and editable amounts are checked. Dropped materials, crafted ingredients, quest totems and Auction House errands are excluded. Extra candidates require a positive vendor record; a sell price alone does not qualify.

Hunters follow their equipped/last-used vendor ammunition, separately for arrows and bullets. The addon does not choose a more expensive tier. Vendor pet food follows the pet's diet and usable food level, with an explicit choice in settings. Existing matching ammunition bags prevent needless bag reminders.

See [the class checklist](OneLastThing/CLASS-SUPPLIES.md), [German wording](OneLastThing/TRANSLATIONS-deDE.md), and [CHANGELOG.md](CHANGELOG.md).

See [IN-GAME-CHECKS.md](docs/IN-GAME-CHECKS.md) for the short live-client checklist.

## Sharing and development

New to GitHub? Start with [GITHUB-START.md](docs/GITHUB-START.md). This project includes a release workflow, packaging script and Lua 5.1 behavior checks.

```sh
python3 -m pip install -r requirements-dev.txt
python3 tests/test_addon.py
python3 tools/package.py --version 0.14.18
```

The install ZIP is written to `dist/`. It contains the addon and readable changelog. Tests simulate WoW APIs; they do not replace testing in the game. For a bug report, include client language, location, `/olt status`, reproduction steps and any BugSack error.


Supply reminders use the **Supplies** parent checkbox and individual item
checkboxes beside their saved targets. Unchecking an item keeps its target for
later. Quest settings follow the same parent then child layout, including the
optional DungeonJournal source.
