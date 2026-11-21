# Live-client checks for 0.14.14

New in 0.14.4: with Neav Express selected, confirm distance labels show ~ and the row actions show Map/Skip/Ignore without squares. Collapse a nonempty checklist and portal into a capital; it should expand. Collapse it again and walk into another district of that city; it should stay collapsed.

New in 0.14.5: hide a nearby Expert profession book and confirm its generic cap warning does not replace it. Revisit after a timed hide expires. Move between class trainers and check the destination follows the nearest suitable trainer, including special spell sources. Reopen Settings and check the range, completion delay and repair sliders match saved values. Let an empty checklist fade, then hover/expand it and check the usual behaviour remains.

New in 0.14.6: enter Rogmar or another settlement with an unlearned flight point while within the configured range. A Learn/Check flight path reminder should appear and its map action should point to the local master. Open a flight master map to confirm learned paths, then check the reminder and its pin disappear. Old flight knowledge is reconfirmed once; amounts, filters and ignored choices should remain intact. If it is still missing, capture /olt status before learning the route.

New in 0.14.7: in Riverglades/Rogmar, verify flight reminders can appear before interacting with a flight master, even when the map-display flag is false. If the warning remains, send /olt status; it now includes queried map IDs, node counts and map-projection failures.

New in 0.14.8: skip a reminder in a capital, then walk between districts and indoor areas. The district label should update while the skipped reminder stays hidden. Leave the city and return; the visit-skipped reminder should return. Timed hides and ignored reminders should remain hidden. Repeat in German if available.

New in 0.14.9: on a Mage, visit capitals with unlearned Teleport/Portal spells. Only that city's eligible spells should appear and Map should target the portal trainer. Learn/skip/ignore a spell and check its reminder clears. Test direct Map/Skip/Ignore in Default, Compact and Minimal at narrow widths and large fonts, in English/German. Ignore can be recovered in Settings; Show hidden reminders only restores temporary skips (and legacy timed hides).

New in 0.14.10: move between capital districts and indoor areas. The checklist should stay visible while its district label updates, with skips, collapse state and scroll preserved. Test with Filter open too. Leaving the city, taking a flight or entering an instance must still clear the previous location; closing the window yourself must keep it closed.

New in 0.14.14: open a profession trainer with many affordable/unaffordable recipes, then close it and refresh OLT. Individual recipes must not appear, including old remembered offers. Verify a class trainer still has individual spell reminders and important profession ranks/books/quests remain available. Supply targets and ignored choices should survive reload.

Automated behavior checks pass against simulated Lua 5.1 APIs. The current Forever build, protected execution and live databases still require in-game verification.

New in 0.14.3: turn off the outside-city range filter and confirm every located reminder still belongs to the current map. Hover a reminder while a bag/quest update happens; the row should stay put until you finish interacting. Skip and Ignore should affect the selected task immediately. On a hunter without selected ammunition, open Settings and check that no error appears. Repeat these checks in English or German as available.

1. **Settings and stock:** edit the Ankh target repeatedly, add/remove a custom item, change fonts and reload. Confirm amounts, disabled categories, ignored reminders and layout remain correct. If profiling, UI object count should stop increasing for equivalent settings rebuilds after the first construction.
2. **Location and instances:** fly or portal between localities and enter/leave an instance or battleground. Old locality content should disappear during loading. Instances should not open the popup automatically. `/olt` should open it manually, including with automatic popups disabled. After closing that manual instance popup, merchant or other automatic events must not reopen it.
3. **Provider status:** temporarily disable a needed database addon while leaving its reminder category enabled. The empty checklist should say some checks are unavailable, with details when expanded; it must not show “All done” or fade to OLT. Restore the provider and reopen/check. No addons are disabled by One Last Thing itself.
4. **German/Hunter/training:** verify native pet diets and the selected vendor food; narrow the popup and increase font size. Actions should fit, abbreviate when needed and explain themselves on hover. Unverified training prerequisites should be labelled as a check at the trainer, rather than a guarantee of availability.
5. **Combat and navigation:** request `/olt` during combat and confirm it opens afterward. Complete a pinned task; verify its pin clears. Set a different personal waypoint afterward and verify it is preserved.

For an issue, include the full `GetBuildInfo()` result, client language, locality, enabled providers, `/olt status`, steps to reproduce and any BugSack error. CPU/FPS impact and taint compatibility have not been measured in the live client by these automated checks.

6. **Capital and outdoor range:** verify a distant trainer/quest inside a capital remains listed. Leave the capital and verify distant destinations outside the saved radius disappear. Change General & location > Outside-city range (yards), then reload to confirm it persists. The city exception must not include a neighboring zone.

7. **Filter menu:** open Filter beside the header, disable a category and re-enable it. Then disable a child while keeping its parent enabled. Hide the last task and verify the menu stays open for recovery. Check long lists scroll, top/bottom header placement, and that collapsing or hiding the popup closes the menu. Choices should survive reload per character.

8. **Importance and estimates:** verify a known dungeon pickup appears before nearby routine errands. Compare two equally important tasks at different distances. Confirm distances say unknown when geometry is unavailable, and unverified tasks carry Check wording. Type a new supply target and verify its cost preview changes without saving until Enter/focus loss. Confirm ammunition estimates round up to actual merchant bundle sizes.

9. **Persistent visibility:** after login, wait for the empty header to become OLT, then use Escape to close another game window. OLT should remain. Walk across an indoor/subzone boundary and verify the checklist returns if briefly hidden while the position settles. Skip-this-visit choices must remain when the locality itself has not changed. The x button should still close it intentionally. Hover Check for its explanation.

10. **Ordinary turn-ins:** with Other completed quests disabled, an ordinary ready quest such as Battle of Hillsbrad should not appear, while an eligible important-chain turn-in still can. Enable the option in Filter and verify ordinary nearby turn-ins return. Reload and confirm your explicit choice remains.

11. **All professions and early books:** on characters with different professions, check only their learned professions appear. Visit a suitable rank trainer (including gathering trainers). At an essential book vendor below skill 125 and/or the required character level, verify a buy-ahead reminder shows the requirements and current values. Bought/banked or already learned books must stay absent. Hover a dungeon/class/access/rank reminder to read its reason and full destination details.

12. **Alt settings and font controls:** open/reopen settings on an alt, then change a supply target or wait for item data to load. No unsupported-script error should occur. Click − / + and verify the font changes while the expanded window dimensions stay fixed. Check the settings font percentage matches and survives reload. Drag the corner grip to resize the actual window.

13. **Settings dropdowns:** open Font and click elsewhere; it should close. Open it again and click the same picker; it should toggle closed. Switch directly to another picker, select a value, scroll/drag settings, close settings and press Escape while a list is open. No list should be left floating afterward.


Profession rank regression (0.14.14):
- Horde, level 35+, Alchemy 219/225: near Stonard, find one rank upgrade with Rogvar as the map destination, even with no rank in SkillUp's next three steps.
- Skip/Ignore that upgrade: no replacement generic cap warning during the same visit; restore through the existing controls.
- Learn Artisan: the rank reminder and its owned map pin disappear. Walking to the trainer alone does not complete it.
- Alliance Leatherworking 200+/225, level 35+: near Aerie Peak, check Drakk Stonehand.
- Check a learned gathering profession omitted by SkillUp's crafting routes; an eligible local rank should still appear and complete after training.
- Routine trainer recipes stay excluded. Distant/wrong-faction trainers stay hidden; EN/DE wording stays readable.


Profession progression checks (0.14.14):
- Fishing 125+/150 in Booty Bay: Expert book at Old Man Heming, including when Fishing is absent from SkillUp's route. Buying/banking it or learning Expert removes the reminder/pin.
- Skill 225 and character level 35: First Aid Triage at the correct faction's doctor, Cooking Clamlette Surprise in Gadgetzan, and Fishing Nat Pagle in Dustwallow. Verify no pickup after accepting/completing; a ready turn-in uses the finish location.
- First Aid 125+: at Deneb Walker (Alliance) or Balai Lok'Wein (Horde), see one optional manuals entry. Owned/banked/learned books must be omitted; buying one leaves the other, buying/learning both removes its pin. Skip/Ignore and restore apply to the group.
- Enchanting 200/225 and level 35+: near either Uldaman approach in Badlands, see the Annora reminder. Pin should mark the entrance. Entering the instance must not automatically open the checklist; arrival alone does not complete the task.
- Tailoring 200/225 below character level 35: no Artisan trainer task. Fishing 50/75 below level 10: no Journeyman trainer task. Existing Skinning requirement remains unchanged pending an in-game check.
- Verify EN/DE text, vendor estimates versus observed prices, insufficient gold, stock, filters, unchanged per-character settings and absence of routine recipe tasks.


Optional DungeonJournal checks (0.14.14):
- Verify the DungeonJournal checkbox is off on a fresh character. Enable it under Settings > Quests & chains; reload and verify the choice persists for that character only.
- At an appropriate level, visit a known dungeon quest giver and check a local pickup, destination pin and recommended level. A quest also covered by Attune must appear only once.
- Accept/complete a quest: remove its pickup reminder/pin. For a prerequisite chain, do not offer a later step before the current required step is handed in.
- Confirm wrong faction/class/profession, too-high requirements, ordinary gray quests, item-start tasks and unfinished hub placeholders stay absent.
- Move outside the outdoor radius or between capital districts; retain normal OLT location behaviour. Skip, Ignore and restore should behave normally.
- Disable the DungeonJournal checkbox: its extra reminders and owned pins disappear; Attune remains enabled. With DungeonJournal absent, leave the option off (no warning) or enable it (clear unavailable status).
- Check both EN/DE and the DungeonJournal loaded status at the bottom of settings. DungeonJournal's own display/RPG options must not change.


Supply control cleanup (0.14.14):
- Verify no Reagent Economy checkbox remains in EN/DE. Existing item targets, disabled items, custom supplies and ignored reminders should remain saved.
- Toggle Supplies off/on: individual choices must be retained. Toggle Ankhs off/on beside their target: only that item changes and its target stays saved.
- Verify Quests & chains appears before its indented Attune/DungeonJournal/turn-in controls. Toggling the parent retains those child choices.
- Reload and check an alt: controls and amounts remain character-specific. If the old override was enabled, check your individual reagent choices now.


Quest title distinction (0.14.15):
- An Attune chain hand-in should read "Chain turn-in:" in English or "Kettenquest abgeben:" in German, with its recommended quest level retained.
- Other completed quests remains independent: ordinary hand-ins still read "Turn in:" / "Abgeben:" when enabled. Chain filters, pickup wording and map pins behave as before.

UI polish (0.14.16):
- At 360px width, test English/German with a wide SharedMedia font and 130% size. Footer labels should fit, wrap when necessary and leave scrolling space.
- Compare Default/Compact/Minimal at normal and larger font sizes; check titles/details/actions do not overlap.
- Open Filter, click outside and drag the header: it should close. Hover the collapsed header for location/count/status.
- Click Map: the active row should show an asterisk. Right-click it to clear the pin. Place a manual replacement pin and confirm OLT leaves it alone.

Settings accent (0.14.17): switch through all four themes and confirm the popup Settings button stands out from Check/Show. Test your usual Neav font against the world background.

Profession requirements (0.14.18):
- Below character level 20 with Tailoring 140/150: the general warning should show level 20 and Tailoring 125, current cap 150, and no claimed local trainer.
- At level 20 near the appropriate trainer, verify the actionable next-rank reminder replaces the general warning. Check that learning the new cap removes it.
- Check another profession gate, an Expert book you cannot use yet, and a secondary-profession Artisan quest. Books may be bought ahead; unavailable quest pickups and training should stay hidden.
- Repeat in German. Professions without character-level gates should not claim a level requirement.
