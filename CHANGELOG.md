# Changelog

## 0.14.4 — 2026-11-17

- Replaced the distance approximation glyph with ASCII ~ and the row overflow glyph with three ordinary periods (...), avoiding missing-symbol squares in Neav Express. Expanded section controls use an ordinary hyphen; the ignored-reminders help uses >. German letters and localization are preserved.
- Automatically expand pending reminders on arrival in a capital city, including portals, loading transitions and flight arrivals. The existing automatic-popup/arrival preferences remain in control. Walking between districts within the same capital preserves a manual collapse, and empty lists remain collapsed.
- Added arrival regressions for capitals, portals, combat recovery, same-city district changes, outdoor visits, empty lists and disabled automatic arrivals. Updated existing English/German label checks for font-compatible punctuation.

## 0.14.3 — 2026-11-17

- Kept destination-map filtering active when the outside-city range limit is disabled or player-position APIs are unavailable. Remote supply sellers no longer pass through the location check when resting or preparing to travel.
- Kept reminder rows and their overflow menu stable during background updates while the pointer is over a row or its menu is open. Updates are coalesced and recollected after the interaction; Skip, Hide, Ignore and manual checks still apply immediately. Closing the popup cancels pending display work, and a location change clears the old interaction.
- Added 72 independent Lua 5.1 startup cases across all nine classes and English/German, with missing data addons, malformed saved data and preserved preferences. Added combat-startup recovery and targeted map/interaction regressions to the standard test command.
- Fixed a fresh-hunter settings error when no ammunition has been selected yet, found by the isolated startup tests.

## 0.14.2 — 2026-11-17

- Fixed settings dropdown dismissal: clicking outside closes the list, and clicking the current picker toggles it closed. Clicking another picker switches menus normally without a blocking mouse overlay.
- Registered the dropdown for native Escape-close handling and tied it to the settings parent. Hiding settings, dragging it, or scrolling its main contents closes the dropdown instead of leaving an orphaned list.
- Registered GLOBAL_MOUSE_DOWN only while the dropdown is visible and unregistered it on hide. Clicks inside the list remain available for selection and scrolling. Repeated openings reuse the same menu and item controls.
- Expanded the UI fixtures to exercise OnShow/OnHide lifecycle and event registration. Added checks for initially shown native frame creation, outside/anchor clicks, picker switching, selection, parent cleanup, Escape registration and pooled reuse.

## 0.14.1 — 2026-11-17

- Fixed settings-pool handler resets: ordinary Frames no longer receive unsupported OnClick/edit/slider script assignments, even when clearing a handler. Each pooled widget resets only handlers supported by its native type.
- Tightened the UI test host to reject button, slider and edit-box handlers on incorrect widget types. This reproduces the reported settings error in the previous code and passes with the fix, including pooled rebuilds across alt classes.
- Changed the bottom − / + buttons from window resizing to font sizing, in five-percentage-point steps within the existing 80–130% range. The font preference remains per character and synchronizes with the appearance slider.
- Kept window resizing on the draggable bottom-corner grip. Added English/German tooltips for both font buttons and the window-size grip, without adding explanatory text to the popup.
- Added checks for unchanged expanded window dimensions, font updates, settings synchronization, limits, persistence, bilingual tooltips and repeated alt settings rebuilds.

## 0.14.0 — 2026-11-17

- Added buy-ahead reminders for the existing essential First Aid, Cooking and Fishing Expert books, even below their use requirements. Rows clearly show required/current profession skill and character level; ready-to-use books are preferred when limiting the list to two offers.
- Kept book checks limited to learned professions with a lower cap. Owned/banked copies, learned caps, unaffordable offers, unavailable stock, extended costs and disabled categories remain excluded. No ordinary recipe/material shopping was added.
- Applied the shared profession rank-location and explanation path to all twelve professions: Alchemy, Blacksmithing, Enchanting, Engineering, Herbalism, Leatherworking, Mining, Skinning, Tailoring, First Aid, Cooking and Fishing. Only professions learned by the current character are considered through SkillUp's public API.
- Used installed TrainerSpells profession-trainer data to resolve rank-capable, friendly local trainers, including gathering professions. No trainer database is copied into this addon. Books remain book-based and quest ranks remain quest-based.
- Preserved known character-level gates for profession quest pickups and used the actual hand-in destination when a profession rank quest is ready for turn-in.
- Added concise reasons for dungeon preparation, class progression, raid/access progression, profession ranks and rank books. Existing specific grey-prerequisite explanations take precedence. Tooltips retain full reasons, requirements and destination details; buy-ahead rows reserve visible detail space for requirements and price.
- Completing an early book purchase also clears its owned map pin if the book has moved to the bank. English and German wording are included.
- Added tests for buy-ahead requirements, all twelve profession paths, availability/ownership filters, character-specific relevance, map/faction/rank filtering, quest levels/turn-ins, pin cleanup and explanations.

## 0.13.2 — 2026-11-17

- Turned ordinary completed quest turn-in reminders off by default to avoid duplicating quest trackers and leveling guides. The default also applies to existing characters that have not explicitly chosen this subcategory.
- Kept important Attune-chain and profession-related reminders independent of the ordinary turn-in setting. Explicit opt-in/opt-out choices remain saved per character.
- Always listed Other completed quests under Filter > Quests & chains and in settings, even when disabled, so players can opt in without first seeing a matching reminder.
- Added checks for fresh/existing defaults, saved opt-in/out, discoverability, important-chain turn-ins and unchanged supply settings.

## 0.13.1 — 2026-11-17

- Removed the retired PitStop addon folder from install ZIPs and from future source packaging; version checks no longer require its old stub TOCs. Existing OneLastThing character settings remain unchanged.
- Added an English/German tooltip explaining that Check refreshes the current-location checklist without restoring hidden tasks or automating purchases/training.
- Fixed a visibility-recovery path: a same-locality zone/control event or temporarily unavailable position could hide a visible popup and never reopen it because the locality key had not changed. The addon now restores it once location data stabilizes, without clearing Skip this visit choices or starting a new visit.
- Kept deliberate closure respected, including while recovery is pending. Previously manual checklists can recover with automatic opening disabled. Loading, taxi and instance suppression remain separate.
- Removed the main checklist from Escape-close windows, so Escape can close menus/settings without making the OLT marker disappear. The x button still closes the main popup deliberately.
- Added checks for visibility recovery, visit-state preservation, manual closure, auto-off behavior, idle-marker persistence, tooltip languages and archive contents.

## 0.13.0 — 2026-11-17

- Added global importance sorting: dungeon quest pickups first; empty Ankhs/ammunition and broken gear next; class/access quests and important prerequisites; profession rank books/rank training and flight paths; other pickups and turn-ins; weapon training; routine class training, supplies, repairs and general warnings. Distance breaks ties inside the same priority and confidence level. Dungeon classification uses installed Attune metadata, including group size/type/localized dungeon group; no quest names are guessed.
- Removed the visual category regrouping that previously overrode collection order. Filter categories and small row labels remain available in all layouts.
- Added approximate straight-line yard distances beside tasks and in tooltips, using current-map world coordinates. Unknown distances are explicitly labelled; the map-percentage fallback is never presented as a measured distance. Duplicate destinations share coordinate conversion work.
- Marked unverified eligibility, catalogue/previously observed training, unknown flight status and database-only book availability as checks. Compact/Minimal titles retain visible check wording; tooltips and Default details explain availability still needs confirmation.
- Added live supply-target cost previews in settings, including Hunter ammunition. Estimates honor partial stock and purchase bundle sizes; exact current merchant quotes are distinguished from remembered/fallback estimates. Typing previews cost without committing the target or making purchases.
- Reused the same bundle-aware estimate for reminder rows and settings. Existing target-save behavior, controls, map pins, filters and English/German support remain intact.
- Expanded visible checklists refresh every five seconds using provider caches, while collapsed checklists retain a twenty-second cadence. Periodic refresh waits while a reminder or Filter menu is open.
- Added tests for semantic priority, real Attune metadata, global rendering order, distance ties/unknowns, shared coordinate conversion, bundle costs, live previews and German wording.

## 0.12.0 — 2026-11-17

- Moved category and subcategory checkboxes out of the reminder list into a Filter menu beside the header. Disabled categories remain recoverable there, with independent child choices preserved.
- Removed full-line category/subcategory headings from all three reminder layouts. Small category labels share the title line where space permits; hovering a reminder shows its full category/subcategory and details.
- Kept the existing bottom controls and reminder actions. The header now shows the addon name, with locality and reminder count below it; removing heading lines frees more space for tasks.
- Added collapsible filter sections with pooled controls and wheel scrolling for long lists. Explicit expansion choices and existing filters save per character.
- Kept the filter menu open when its last visible task is disabled, so it can be restored immediately. Normal empty-list collapse resumes when the menu closes. Menus close when the popup collapses or hides, and support both header positions.
- Added English/German wording and tests for filtering, recovery, empty-menu behavior, layout modes, header positions, saved preferences and control reuse.

## 0.11.3 — 2026-11-17

- Removed the redundant resize explanation from the popup in English and German. The − / + buttons and drag-to-resize grip remain available.

## 0.11.2 — 2026-11-17

- Extended city-wide filtering from supply warnings to all located reminder types in Orgrimmar, Undercity, Thunder Bluff, Stormwind, Ironforge and Darnassus. Only the current capital's map qualifies; adjacent zones and other cities stay excluded.
- Kept distance filtering outside those six capitals, including Ratchet and Booty Bay. General warnings without a destination retain their existing behavior; unknown task coordinates do not bypass the radius.
- Clarified General & location settings: Use distance filtering outside capital cities, and Outside-city range (yards). The per-character slider defaults to 850 yards and offers 250–2,000 yards in 50-yard steps. Existing saved ranges are preserved.
- Added checks for all six city maps, outside-zone exclusions, world-coordinate/fallback distances, adjustable ranges and saved slider values.

## 0.11.1 — 2026-11-17

- Reused settings frames, labels and slider textures across rebuilds. Repeated supply edits no longer accumulate another settings interface each time.
- Validated saved-data types, bounds and nested records before migrations; valid character preferences and amounts remain intact.
- Invalidated stale location content when the map/position is unavailable or the world is loading.
- Suppressed automatic popup opening in dungeons, raids, battlegrounds and arenas. `/olt` still opens a manual checklist, including with automatic popups off; combat requests wait until combat ends.
- Distinguished failed/unavailable enabled checks from a successful empty result. Incomplete checks show a warning instead of “All done” and do not fade to the idle marker. Expand the checklist for provider details.
- Cached quest-chain, quest-log, class/weapon and flight results with selective event invalidation and a bounded lifetime. Hidden checklists with automatic popups off skip ordinary collections. Merchant/trainer updates are coalesced before scanning.
- Used native `C_PetInfo.GetPetFoodTypes()` table data for Hunter food selection, retaining conservative database fallbacks.
- Clearly labelled training suggestions whose prerequisites cannot be verified; retained positive known-spell and available legacy talent checks. No unverified modern talent-tree adapter is claimed.
- Fitted action buttons to the available row width and measured localized text. Narrow rows use M / S / 30m / ⋯ with explanatory tooltips; full labels return when they fit. Layout recalculates after font changes.
- Added behavior checks for settings object reuse, malformed saved data, partial/nested provider failures, selective caching, loading/instance transitions, manual combat reopening, merchant coalescing, native German pet diets and localized action widths.

## 0.11.0 — 2026-11-17

- Renamed PitStop to **One Last Thing**, including addon folders, files, commands and internal names. Use `/olt` or `/onelastthing`. The idle marker is now **OLT**.
- Added a one-time importer for old per-character settings, without running the old checklist.
- Restricted shopping reminders to vendor purchases with a known seller location. A vendor sell price is not evidence that an item can be bought.
- Corrected the Shaman default to Ankhs. Quest totems, dropped fish materials and non-vendor feathers/powders are not automatic shopping tasks. A separately verified vendor may qualify a relevant reagent.
- Kept vendor class reagents, appropriate Druid ranks and Rogue Thieves' Tools. Reagent Economy suppresses reagents without hiding useful tools.
- Added conservative vendor-only extras: previously carried finished Rogue poisons with a proven seller; usable Hunter pet food with a saved choice; a basic matching quiver/pouch only if none is owned. No automatic ammo-tier upgrade.
- Archived removed automatic supplies while preserving their saved amounts for a subsequently verified vendor. Custom entries remain editable.
- Added GitHub-ready source, beginner upload instructions, automated checks and tagged release packaging. Both source and install ZIPs include this changelog.

## 0.10.0

- Added German UI and localized profession detection; supply amount is called Sollbestand.
- Added weapon-aware Hunter ammunition reminders with separate remembered arrow and bullet choices.
- Kept manual ammo-tier choice, saved amounts and bundle-aware g/s/c prices.

## 0.9.5

- Removed changing SkillUp recipe-material and recipe-training errands. Kept profession ranks and important rank books.
- Made built-in Arial Narrow the initial font, preserving existing font selections.

## 0.9.4

- Added recommended quest levels to reminders, tooltips and ignored-reminder entries.

## 0.9.3

- Removed manual notes and their commands, keeping location-related automatic reminders.

## 0.9.2

- Organized settings into collapsible sections with addon connection status at the bottom.

## 0.9.1

- Added Default, Compact and Minimal layouts and a scrollable SharedMedia font picker.

## 0.9.0

- Clarified actions: Skip this visit, Hide for 30m, and Don't remind again.
- Added nearby repair reminders and settings-only recovery of ignored reminders.

## 0.8.x and earlier

- Added per-character supplies, targets and categories; class and weapon training; flight-path checks; important profession books; and local quest-chain reminders.
- Added map navigation and ownership-aware pin cleanup, g/s/c costs, adjustable appearance, header placement and completion fading.
- Fixed arrival locality, quest completion and turn-in destinations, including Chief Engineer Scooty.

Earlier versions were distributed as PitStop; the first prototypes used Before You Go. Older entries summarize the development history rather than reproduce every change.
