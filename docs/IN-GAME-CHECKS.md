# Live-client checks for 0.14.4

New in 0.14.4: with Neav Express selected, confirm distance labels show ~ and the row menu shows ... without squares. Collapse a nonempty checklist and portal into a capital; it should expand. Collapse it again and walk into another district of that city; it should stay collapsed.

Automated behavior checks pass against simulated Lua 5.1 APIs. The current Forever build, protected execution and live databases still require in-game verification.

New in 0.14.3: turn off the outside-city range filter and confirm every located reminder still belongs to the current map. Hover a reminder or open its ⋯ menu while a bag/quest update happens; the row and menu should stay put until you finish interacting. Skip, Hide and Ignore should affect the selected task immediately. On a hunter without selected ammunition, open Settings and check that no error appears. Repeat these checks in English or German as available.

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
