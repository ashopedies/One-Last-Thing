ONE LAST THING — 0.14.10
WoW Forever / interface 16001

INSTALL
Downloads: https://github.com/ashopedies/One-Last-Thing/releases
Choose a release, expand Assets and download the -forever.zip install package.
Extract the install ZIP into Interface/AddOns, allowing replacement when updating.
The addon must be Interface/AddOns/OneLastThing/OneLastThing.toc.
Restart WoW. /olt opens the checklist; /olt settings opens settings.
/onelastthing is an alternate command.

DATA SOURCES
Attune: quest chains. Questie / QuestieDB: quests, NPCs, vendors and repairs.
SkillUp Forever: profession state and ranks/books, not recipe shopping.
TrainerSpells: class ranks, city-specific Mage portal trainers and weapon skills.
NeavMedia / LibSharedMedia: optional media/fonts. Built-in Arial is available.
No hard dependencies; missing providers reduce the corresponding coverage.
Settings > Addon requirements shows connection status.

CONTROLS
Drag the header to move; click to collapse. Escape leaves the main popup
and OLT marker visible; use x to close it deliberately. Scroll with the mouse wheel.
Filter beside the header manages categories and subcategories. Expand a
category with + to show its children. Disabled groups can be restored there.
A small category label shares the title where space permits.
Hover a reminder for full details.
Resize the window by dragging its bottom corner. The - / + buttons change
font size in 5% steps (80-130%), saved per character. Choose Default, Compact
or Minimal rows in settings. Header placement, colors, font and opacity save
per character. The successfully completed header eventually fades to OLT.
Failed/missing enabled checks show an incomplete-check warning instead.
Expand the list to read which checks are unavailable. Narrow rows abbreviate
actions, with the full explanation on hover.

Automatic opening is suppressed inside dungeons, raids and battlegrounds.
/olt still opens a manual checklist there, even if automatic popups are off.
Real map/loading transitions hide old location content. Within a confirmed
capital, district-coordinate refreshes keep the checklist visible without
resetting visit skips, scroll position or the Filter menu.

Map, Skip and Ignore are directly available in every reminder layout.
Minimal/narrow rows use M/S for Map/Skip and keep Ignore visible.
Skip: returns next locality visit or reload.
All districts within a capital count as one visit.
Ignore: hidden until Settings > Ignored reminders > Remind me again.
Show hidden reminders restores visit skips; old timed hides remain compatible.

ORDINARY QUEST TURN-INS
Off by default to avoid duplicate reminders from quest trackers. Opt in under
Filter > Quests & chains > Other completed quests. Important tracked-chain
turn-ins remain independent. Explicit choices save per character.

PROFESSION PROGRESSION
All twelve professions use the shared rank-reminder path; only professions
learned by this character are shown. SkillUp supplies rank steps and installed
TrainerSpells data supplies friendly, rank-capable trainer locations.
Important First Aid, Cooking and Fishing rank books can be bought ahead of
their use requirements. Required/current skill and level are shown, with
ownership/bank, learned-cap, affordability, stock and category checks retained.
At most two key rank-book offers are shown.
Dungeon, class, access and profession reminders include short purpose text;
hover for full explanations, requirements and destination details.

TASK ORDER AND COSTS
Dungeon quest pickups come first. Empty Ankhs/ammunition and broken gear
follow, then location-specific progression; routine services rank lower.
Distance breaks ties within equal importance and confidence. Displayed yards
are straight-line approximations from world coordinates, not walking routes.
Unknown distances are labelled. Check wording identifies unverified offers.
Supply targets preview refill costs as you type, including bundle sizes.
Targets still save on Enter or focus loss; no purchases are automated.

REMINDER RANGE
All located reminders cover the current capital map in Orgrimmar, Undercity,
Thunder Bluff, Stormwind, Ironforge and Darnassus. Nearby zones are not included.
Elsewhere use Settings > General & location > Outside-city range (yards).
Default 850; slider 250-2000 in 50-yard steps, saved per character. Existing
saved ranges are retained. General destination-free warnings are unaffected.

SUPPLIES
Edit each amount beside its checkbox. Custom supplies are listed below and
can be removed. Only vendor items with usable seller locations create
shopping reminders. No AH, crafting-material, drop or quest-totem errands.
Hunter ammunition follows the current/last-used tier; it does not upgrade it.
See CLASS-SUPPLIES.md for class coverage. Native map pins clear when their
task is completed/hidden, without clearing a subsequent player waypoint.

CHECK BUTTON
Check refreshes the checklist for your current location. It does not restore
hidden reminders, buy items or learn spells. Its tooltip explains this in
English or German.

COMMANDS
/olt                         Open checklist
/olt settings                Settings
/olt supply ITEM_ID AMOUNT   Custom supply; zero removes it
/olt restore                 Show visit-skipped and timed-hidden reminders
/olt auto                    Toggle automatic popup
/olt status                  Provider/compatibility diagnostics

CHANGELOG.md lists what changed in each version. German wording is listed
in TRANSLATIONS-deDE.md. Behavior checks use Lua 5.1 API fixtures; live client
verification is still needed. For errors, include location, language,
/olt status and the BugSack message.
