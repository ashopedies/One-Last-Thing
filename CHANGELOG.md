# Changelog

## 0.14.24 — 2026-11-22 — Less squinting, fewer ghost flights

- Retired flight paths with the technical zzOLD prefix can stay retired. Real places such as Powderfuse Port and Old Town remain eligible.
- Flight maps get one brief follow-up check for late-arriving learned-route data, including a quick-close check. No endless polling, no guessing that every route is learned.
- Retired OLT flight pins clear without touching a replacement pin you placed yourself. Ignore remains the existing, recoverable way to hide a route you already know; it does not teach OLT that route.
- Supply item-ID and quantity captions now line up with their fields. German Sollbestand gets breathing room beside existing supply targets too.
- Appearance settings have three little signposts: Window & layout, Theme & style, and Text. Same controls, easier treasure hunt.
- Show hidden reminders displays how many temporary hides it can restore, counting duplicate skip/legacy-pause entries once and excluding expired pauses and ignored entries. Recovery settings and the button tooltip show the count too.
- German polish covers the new captions, skipped counts, map/spell fallbacks, diagnostics and translated chain details. English stays supported alongside it.
- Eric is unchanged and stays out of the public package. He has other calls to take.

## 0.14.23 — 2026-11-22 — Filter found its manners

- Clicking Filter again closes its menu and keeps a manually opened checklist in view, even when the list is empty. The menu has stopped taking the whole window with it.
- Hide every category? OLT stays open so you can find your way back to the switches.
- When the last reminder clears while the menu is open, normal auto-collapse still waits until you close it. New work cancels that pending collapse.
- Checked English/German, all three layouts, both header positions, outside clicks and Escape. Eric did not attend this meeting.

## 0.14.22 — 2026-11-21

- Give Neav: Muted Moss clearer gold, moss-green and ivory separation instead of similarly pale gold/green shades.
- Use moss green for the header, ivory for ordinary quest/class-training text, and gold for action/Settings accents and important warnings. Keep exactly three foreground colors.
- Preserve the selected theme and all other palettes, layouts and reminder behavior. Update existing theme regression coverage for the distinct color roles.

## 0.14.21 — 2026-11-21

- Add a Why this reminder? section to row-hover tooltips in all three layouts. Explain the reminder source, reason, known level/skill requirements, location evidence and price confidence without adding row buttons.
- Preserve quest-location provenance when cached destinations change. Identify recorded database/curated coordinates and past observations without implying a live NPC check; distinguish catalogue, observed, estimated and unknown prices.
- Add Show informational profession-cap warnings under Settings > Professions. It is saved per character and remains on by default for existing behavior. Disabling it hides generic cap advice only; local rank trainers, rank quests and buy-ahead books retain their own checks/settings.
- Add English/German strings and regression coverage for hover explanations, changing provenance, price evidence, actual settings interaction and character persistence.

## 0.14.20 — 2026-11-21

- Select the nearest valid current-map quest giver, object or spawn rather than stopping at the first database point. Preserve separate pickup/hand-in sources, known destinations on other maps and curated hand-in fallbacks.
- Keep candidate destinations in cached Attune, DungeonJournal, ordinary hand-in and weapon rows. Movement reselects a destination and NPC label without rescanning databases or mutating displayed/cached templates.
- Use the shared world-distance selection for class/profession trainers and weapon masters; retain faction, class, level, rank and radius restrictions.
- Prefer current native profession rank and cap together when SkillUp's cached values disagree, while retaining copied route metadata and leaving the source addon's data unchanged.
- Display unknown class/weapon training prices as unknown, preserving real zero-cost entries and safe affordability checks.
- Label map-coordinate radius fallback as Approximate range in English/German, with an explanation in reminder tooltips and diagnostics. Exact world-coordinate distances and city-wide behavior remain distinct.
- Add regression cases for multiple destinations, cached movement, source conflicts, unknown/free prices, fallback labels and real-world distance ranking.

## 0.14.19 — 2026-11-21

- Add Neav: Current and Neav: Muted Moss under Appearance > Color theme, alongside all existing choices. Existing character selections remain unchanged.
- Match the attached NeavFlare 0.6.56 moss/ochre hues using brighter versions for transparent checklist text. New themes retain three foreground colors, a distinct Settings accent and existing background controls.
- Neav: Current reads the active FlareUI cast/friendly palette without modifying it, with a green/gold fallback when absent. Choose Current in NeavFlare for that pairing; Current in the source addon deliberately inherits its native palette rather than defining fixed colors.
- Add optional load ordering for FlareUI/NeavFlare and a one-time Current-theme refresh after login readiness. Neither addon is required; no runtime palette polling or new reminder behavior.
- Verify English/German startup, theme switches, persistence, selected fonts, optional/malformed providers, source immutability and the three-color limit.

## 0.14.18 — 2026-11-21

- Show known character-level and profession-skill requirements in near-cap warnings across all twelve professions, including trainer ranks, Expert books and Artisan progression quests. Explain the current skill cap without claiming a local trainer exists.
- Keep character-level gates first so narrow rows expose the reason an upgrade is not yet available. Add matching requirement text to local rank reminder details/tooltips in English and German.
- Share Expert book requirement facts with the cap warning instead of guessing a universal level gate. Buy-ahead books remain purchasable reminders before their use requirements; actual training and quest pickup eligibility are unchanged.
- Add 72 bilingual profession-gate cases, level-up transitions, no-level/unknown-gate handling, skip behavior and learned-cap checks.

## 0.14.17 — 2026-11-21

- Make the popup Settings button stand out using an existing palette accent: Blizzard gold, the player's class color, Pop coral, or Original lavender.
- Keep the accent through live theme switches, font-size changes and responsive footer labels, without adding a fourth foreground color to the three-color themes.
- Add regression coverage for all four themes and live font/layout changes.

## 0.14.16 — 2026-11-21

- Measure footer controls using the selected font, shorten labels when needed and wrap them without clipping; keep font controls together and reserve checklist space.
- Increase Default and Compact row heights with larger fonts. Minimal remains dense.
- Close category filters on outside clicks and dragging. Add a collapsed-header tooltip with location, remaining count and unavailable checks.
- Mark the active task's Map button with an ASCII asterisk. Right-click Map to clear its owned pin; manual replacement pins are preserved.
- Coalesce item-data settings refreshes, reuse world coordinate conversions within one collection, defer ignored-spell rank scans until needed, and guard scroll forwarding.
- Complete English/German labels and localized settings sorting. Existing reminder sources, profession progression and character settings are preserved.

## 0.14.15 — 2026-11-21

- Label Attune chain hand-ins as "Chain turn-in:" (German: "Kettenquest abgeben:") so they are distinguishable from ordinary completed quests. Recommended levels, chain filters, completion checks and map destinations are unchanged.
- Ordinary hand-ins retain "Turn in:" / "Abgeben:" and remain controlled by Other completed quests. Profession rank quest wording is unchanged.

## 0.14.14 — 2026-11-21

- Removed the Reagent Economy checkbox and global reagent suppression. Reagents are controlled by the Supplies parent checkbox and individual item checkboxes beside their saved targets.
- Clear the retired override when saved data loads while preserving explicit item/category choices, targets, custom supplies and ignored reminders. A removed option can no longer silently suppress restock reminders.
- Made quest settings consistent with the supply hierarchy: the Quests & chains parent checkbox appears first, with the Attune and optional DungeonJournal controls underneath. Child choices remain saved when a parent is toggled.
- Removed obsolete EN/DE wording and updated regression tests for character-specific controls, existing settings, parent/child ordering and independent alt defaults.

## 0.14.13 — 2026-11-21

- Added optional DungeonJournal dungeon quest pickups under Settings > Quests & chains. The per-character checkbox defaults off and supplements Attune. The adapter reads installed DungeonJournal data without bundling or modifying it; Questie verifies availability and takes precedence for destinations.
- DungeonJournal pickups use level/faction/class/profession/completion/prerequisite checks, the current location/radius, and canonical quest IDs for deduplication with Attune. Important gray prerequisite steps are explained; ordinary gray quests, repeatables, item-start tasks and unfinished hub placeholders stay excluded. Unsupported/missing sources report health only when enabled.
- Cached DungeonJournal scans are invalidated by quest/skill/data changes. Movement reuses raw destinations for local distance checks; disabling the source clears an owned DungeonJournal pin. Added EN/DE controls and load status in addon requirements.
- Share profession state between rank and book checks, filling skills omitted by SkillUp's crafting plans from native character data. Expert Fishing books now work even when Fishing has no crafting route. Existing API results are copied rather than modified.
- Added independent, level/skill/faction-aware rank quest reminders for Triage, Clamlette Surprise and Nat Pagle, Angler Extreme. They respect accepted/completed quests, actual turn-in locations, distance, filters and hidden reminders. Canonical quest keys avoid duplicates with Attune; previous rank reminder hide states are still respected.
- Added one Annora rank reminder near either Uldaman approach for Enchanting 200/225 at character level 35+. The waypoint explicitly marks the entrance, not Annora's indoor position. Automatic instance suppression stays in place; learning the rank completes the reminder.
- Added the two curated First Aid bandage manuals as one vendor-stop entry from skill 125. Learned or owned/banked manuals are excluded; the group shrinks after a purchase and its owned pin clears once all manuals are owned/learned. Stock, price, budget, filters, Skip/Ignore and restore remain supported. Routine profession recipes stay excluded.
- Added small fallback locations for the three Expert rank books and manual vendors; live merchant prices take precedence over marked estimates. The shortlist remains at most two book/vendor reminders.
- Corrected Artisan Tailoring's character-level requirement to 35 and Journeyman Fishing's to 10. Artisan Enchanting uses the user's tested skill requirement of 200 at level 35. The disputed Skinning gate is unchanged pending verification; no speculative trainers were added.
- Added EN/DE regression coverage and a factual trainer snapshot across nine professions, plus native-only progression, rank quests, Annora entrances, grouped manuals, ownership, waypoint completion and requirement checks.

## 0.14.12 — 2026-11-21

- Check eligible local profession rank upgrades independently of SkillUp's next route steps. Alchemy at 219/225 now finds Rogvar near Stonard when the character meets the rank requirements, even with a recipe-only or empty plan.
- Added small location fallbacks for missing Rogvar (Alchemy, Swamp of Sorrows) and Drakk Stonehand (Leatherworking, The Hinterlands). Installed entries for these NPC IDs take precedence; no upstream addon data is modified. Meilosh's role remains unconfirmed and was not added.
- Request more rank-route steps and include learned native professions omitted by crafting plans. Preserve rank books/quests, faction/radius filters, Skip/Ignore, per-character settings and the exclusion of routine recipes.
- Avoid a duplicate cap warning when a specific local rank reminder covers it. Native profession rank completion also clears an owned pin when SkillUp omits that profession.
- Added English/German regression coverage for the reported case, 60 rank cases across twelve professions, eligibility boundaries, missing trainers, native gathering state, upstream precedence, hidden reminders and completion-only waypoint cleanup.

## 0.14.11 — 2026-11-20

- Removed routine profession recipe errands from observed trainer offers. Profession trainers are recognized natively and through installed trainer data; individual recipes are also filtered by profession metadata and installed recipe spell IDs.
- Retired recognized recipe offers already stored in the trainer cache, so old lists do not need to be skipped or ignored one by one. Obsolete owned recipe waypoints clear without affecting later player waypoints or saved preferences.
- Kept profession rank/cap progression, essential rank books and progression quests. Class and weapon spell training retains individual reminders for gold-based choices; no generic recipe-completion task replaces the removed recipe list.
- Added English/German regression coverage for 1,000-service trainers, legacy cache cleanup, localized trainer names, recipe IDs, pin cleanup and retained progression/class training.

## 0.14.10 — 2026-11-19

- Removed capital-district flicker: keep a visible checklist in place during same-city zone/indoor events and temporary coordinate gaps. Existing city-wide tasks remain visible while fresh scope data is pending; no collection runs with stale coordinates.
- Preserve scroll position when the same location recovers. Capital visit skips, manual collapse and open Filter menus remain intact, including manually opened checklists with automatic opening disabled.
- Continue clearing old content on actual map changes, unknown map identity, flights, instances and world-loading transitions. Explicitly closing the popup cancels recovery and does not reopen it.
- Added visibility/recovery checks across all six capitals and English/German, plus regressions for scroll/filter state, deferred scans and leaving the city safely.

## 0.14.9 — 2026-11-19

- Routed the twelve capital Teleport/Portal spells to their own city and the matching NPC from TrainerSpellsPortalTrainers. General class trainers no longer receive these reminders. Existing level, faction, learned/ignored-spell and cost handling remains in place; localized NPC names come from installed data.
- Kept cached portal destinations tied to their actual sources and invalidate when the installed portal table changes. A missing local portal record reports unavailable data instead of substituting an unrelated class trainer. Added 96 city/level/language cases plus cache, learning, faction, explicit-source and missing-data checks.
- Replaced the row overflow menu with a directly accessible Ignore button. Rows now offer Map, Skip and Ignore in Default, Compact and Minimal layouts; narrow/Minimal layouts use M/S where needed while reserving space for the title and Ignore label.
- Removed the 30-minute hide control. Older saved timed hides still expire or can be restored normally, without changing per-character preferences. Skip and Ignore have distinct English/German tooltips and Ignore remains recoverable only through Settings.
- Updated layout/interaction regressions for direct actions, narrow and wide windows, all density modes, English/German and the supported font-size range. Preserved the capital-visit and flight-path fixes from previous versions.

## 0.14.8 — 2026-11-18

- Treat each of the six capitals as one visit instead of starting a new visit at every district or indoor boundary. Skip this visit stays active across city districts; the header still shows the current district.
- Preserve capital visit skips through temporary position loss and same-city loading transitions. Leaving/re-entering the capital or reloading resets visit skips as before; timed hides, ignored reminders and outdoor locality visits keep their own behaviour.
- Clarified the Skip tooltip in English and German. Added regression coverage for all six capitals, district labels, collapsed state, loading recovery, city exit/re-entry and the other hide lifetimes.

## 0.14.7 — 2026-11-18

- Fixed a regression in 0.14.6: ShouldMapShowTaxiNodes is a rendering hint, not a data-availability check. Read returned nodes even when it is false, use the continent's coordinate space, and retain child-returned data if the continent request is empty.
- Added a regression based on the reported Rogmar diagnostic (current map 2548, parent 1415, display false, 36 nodes). It verifies a local reminder before any flight-master interaction, provider health, range/zone isolation and the parent/child fallback.
- Added map/node/display counts to /olt status when flight data is unavailable, including a separate note when map projection is missing. No additional flight-cache reset is required.

## 0.14.6 — 2026-11-18

- Corrected flight reminders for maps whose flight nodes are supplied in parent/continent coordinates. Follow native map coverage and hierarchy, project nodes onto the current zone, then apply faction and distance filtering. Do not guess local coordinates when conversion data is unavailable.
- Stopped treating the map's already-discovered flag as proof of a learned route on Forever. Confirm routes from Current/Reachable entries on an opened flight map; uncertain routes use Check flight path wording. Use the opened flight map's own map ID when available.
- Rebuilt the legacy flight-knowledge cache once because it could contain false learned flags. Character preferences, supply targets and ignored reminders remain intact. Previously learned paths may need one flight-map visit to be reconfirmed.
- Added tests for parent-map projection, distant/enemy/other-zone exclusion, unreliable discovery flags, observed route knowledge, pin removal on confirmed learning, missing geometry and cache migration.

## 0.14.5 — 2026-11-18

- Kept skipped, snoozed and ignored nearby profession books from resurfacing as duplicate generic cap warnings. Coverage is recalculated per collection; general warnings remain available elsewhere, outside the vendor range, or when the book provider is disabled.
- Reused eligible class-spell results while moving, refreshing the nearest suitable trainer and source-specific destinations separately. Cached templates do not mutate rows already on screen. Skill changes selectively invalidate weapon/class/progression caches while leaving unrelated flight results intact.
- Pruned higher-level spells before building training candidates or inspecting their prerequisites. Already learned higher ranks still suppress obsolete lower ranks when Forever's level requirements differ from the catalogue. Class/trainer table replacements invalidate cached results; events, manual checks and the existing 60-second expiry cover in-place changes.
- Synchronized range, completion-delay and repair sliders on the settings fast-path. Closed dropdowns before selection-triggered rebuilds, reused pooled button style handlers/backdrops, and retained font and hover-state updates.
- Attached the header's fade OnUpdate handler only while fading, clearing it on completion, hover, expansion and hiding. Kept styling, supply-zero semantics, map-opening behaviour and saved settings unchanged.
- Added isolated Lua 5.1 regression coverage for the above changes, including book-hide lifetimes, trainer relocation, future-spell pruning, higher ranks, cache expiry, settings pooling and fade cleanup.

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
