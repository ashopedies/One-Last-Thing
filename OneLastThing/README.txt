ONE LAST THING — 0.14.22
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

OPTIONAL DUNGEONJOURNAL
Settings > Quests & chains > DungeonJournal dungeon quests (optional).
Off by default, saved per character. Supplements Attune with local dungeon
pickups and required prerequisite steps. Questie verifies availability; IDs
prevent duplicates. Distance, level, faction, class/profession, completion,
Skip/Ignore and restore apply. Item-start tasks, repeatables and unfinished
hub placeholders are excluded. Gray prerequisites need a relevant later quest.
Requires installed DungeonJournal data; no database/assets are bundled or
modified. Tested with DungeonJournal 2.1.2. Missing/unsupported data is reported
only when enabled. Automatic instance suppression is unchanged.

PROFESSION PROGRESSION
Routine profession recipes are excluded, including remembered trainer offers.
Rank upgrades, key books and progression quests remain. Two First Aid bandage
manuals are a curated exception, grouped into one optional vendor stop. Class spells retain
individual Skip/Ignore controls for gold decisions.
All twelve professions use the shared rank-reminder path; only professions
learned by this character are shown. Eligible local trainer ranks are checked
independently of the next recipe steps. SkillUp supplies profession plans; native
profession state includes gathering skills omitted by crafting plans. Installed
TrainerSpells data supplies friendly, rank-capable trainer locations, with small
fallbacks for missing Rogvar and Drakk Stonehand. Outdoor distance limits apply.
Important First Aid, Cooking and Fishing rank books can be bought ahead of
their use requirements. Required/current skill and level are shown, with
ownership/bank, learned-cap, affordability, stock and category checks retained.
At most two book/vendor offers are shown. From First Aid 125, Heavy Silk and
Mageweave Bandage manuals form one vendor entry; owned/banked and learned
manuals are excluded. Skip/Ignore applies to the whole entry.
Triage, Clamlette Surprise and Nat Pagle rank quests have independent checks.
At Enchanting 200/225 and character level 35+, an Annora reminder can appear
near either Uldaman approach. Its pin marks the entrance, not the indoor trainer.
Automatic instance suppression remains enabled.
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

SUPPLY CONTROLS
Use the Supplies parent checkbox and individual item checkboxes. Amounts stay
saved when unchecked. Quest settings use the same parent checkbox followed
by their child controls.

Map * marks the active task pin. Right-click Map to clear that pin.
Map * kennzeichnet den aktiven Aufgabenpin. Rechtsklick auf Karte entfernt ihn.

NEAV COLOR THEMES
/olt settings > Appearance > Color theme: Neav: Current / Neav: Muted Moss.
Moss follows NeavFlare 0.6.56 green/gold hues, brightened for readable text.
Current reads the active FlareUI cast/friendly colors; choose Current in NeavFlare
for the matching pair. Without FlareUI it uses a green/gold fallback.
Both themes work without NeavFlare and do not change its settings.
DE: /olt settings > Darstellung > Farbschema: Neav: Current / Neav: Muted Moss.
Die Farbtöne werden für lesbaren Text aufgehellt. Current nutzt die aktiven
FlareUI-Farben; dort ebenfalls Current auswählen. Ohne FlareUI gilt eine
grün-goldene Ersatzpalette. Bestehende Auswahl und andere Addons bleiben unverändert.

DESTINATIONS AND DISTANCE
When a quest has several valid locations, OLT selects the nearest current-map
giver/spawn and updates that choice as you move without a full catalogue rescan.
Approximate range means world-coordinate conversion was unavailable, so the
configured yard radius is estimated using map coordinates. It is not an exact
yard measurement. Native profession rank/cap take precedence over planner data.
DE: Bei mehreren gültigen Questorten wird der nächstgelegene Ort auf der
aktuellen Karte gewählt. Ungefährer Umkreis bedeutet eine Schätzung aus
Kartenkoordinaten, keine genaue Entfernungsmessung. Unbekannte Preise bleiben
als unbekannt gekennzeichnet; kostenlose Ausbildung wird weiterhin als 0c angezeigt.

REMINDER EXPLANATIONS / INFORMATIONAL ADVICE
Hover a reminder for Why this reminder?: source, reason, requirements, location
evidence and price confidence. Database coordinates do not prove a live NPC
check. Recorded prices can change; catalogue prices may have different discounts.
Settings > Professions > Show informational profession-cap warnings controls
generic near-cap advice (on by default, per character). Turning it off keeps
local rank trainers, rank quests and buy-ahead books enabled.
DE: Mit der Maus über einen Hinweis fahren: Warum dieser Hinweis? erklärt
Quelle, Grund, Voraussetzungen, Ortsangaben und Preisart.
Unter Einstellungen > Berufe kannst du allgemeine Hinweise zur Berufsgrenze
ausblenden. Lehrer, Berufsquests und Bücher bleiben weiterhin aktiviert.

MUTED MOSS ACCENTS
Moss headers, ivory regular quest/training text and gold actions/Settings
provide clearer separation while retaining the three-color palette.
DE: Moosgrüne Überschriften, elfenbeinfarbener Quest-/Ausbildungstext und
goldene Aktionen/Einstellungen sorgen für deutlichere Akzente.
