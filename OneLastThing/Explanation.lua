local _,A=...
local sources={
    AttuneRows='Attune',DungeonJournalRows='DungeonJournal',TurnInRows='WoW quest log',
    ProfessionRows='Profession data and OLT rank rules',ImportantVendorRows='OLT profession progression rules',
    SupplyRows='Bag counts and saved supply amounts',HunterAmmoRows='Equipped ammunition and bag counts',
    ClassSpellRows='TrainerSpells',WeaponRows='TrainerSpells',TrainerRows='Your trainer observations',
    FlightRows='WoW taxi data and your flight observations',RepairRows='WoW equipment durability',BagRows='Bag counts and your threshold',
}
local prices={
    observed='Observed price; check the current offer.',
    catalogue='Catalogue price; discounts may differ.',
    estimate='Estimated price; verify at the merchant.',
    unknown='price unknown',
}
local function kind(row)
    local key=row.key or ''
    if row.informational or key:match('^cap:') then return 'ProfessionRows','Near your profession cap; general advice, not a confirmed local task.' end
    if row.firstAidManuals or row.criticalBook then
        return 'ImportantVendorRows',row.buyAhead and 'Missing progression book; you can buy it before meeting its use requirements.' or 'Missing profession progression book or manual.'
    end
    if row.professionRank then return 'ProfessionRows','A local opportunity to unlock your next profession rank.' end
    if row.attuneStep then return 'AttuneRows',row.finish and 'Quest was ready to turn in when last checked.' or 'A step in an unfinished quest chain.' end
    if row.dungeonJournal then return 'DungeonJournalRows','An eligible dungeon quest or its prerequisite pickup.' end
    if row.quest then return 'TurnInRows','Quest was ready to turn in when last checked.' end
    if row.ammoItem then return 'HunterAmmoRows','Selected ammunition is below your saved supply amount.' end
    if key:match('^supply:') then return 'SupplyRows','Bag count is below your saved supply amount.' end
    if row.weapon then return 'WeaponRows','An unlearned weapon skill for your class.' end
    if row.classSpell then return 'ClassSpellRows','An unlearned class spell at a matching trainer.' end
    if key:match('^train:') then return 'TrainerRows','An unlearned service recorded during a trainer visit.' end
    if row.flight then return 'FlightRows','Flight-path knowledge needs confirmation at a flight master.' end
    if row.repair then return 'RepairRows','Equipped gear is below your saved repair threshold.' end
    if key=='bags' then return 'BagRows','Free bag space is below your saved threshold.' end
    return nil,'Matches your enabled reminder filters.'
end
-- Explain recorded evidence only. A working provider or a coordinate in a
-- database is not proof of current NPC availability, prices or server state.
function A.ReminderExplanation(row)
    local inferred,reason=kind(row)
    local provider=row.provider or inferred
    local lines={}
    local function add(label,value)
        if value and value~='' then lines[#lines+1]=A.Translate(label)..': '..A.Translate(value) end
    end
    add('Source',sources[provider] or 'One Last Thing')
    add('Reason',reason)
    if row.requiredLevel and row.requiredLevel>0 then lines[#lines+1]=A.Translate('Requires level '..row.requiredLevel) end
    if row.requiredSkill and row.profession then lines[#lines+1]=A.Translate('Requires')..' '..A.Translate(row.profession)..' '..row.requiredSkill end
    if row.verify then lines[#lines+1]=A.Translate('Some details need checking at the indicated NPC.') end
    if row.map and row.x and row.y then
        local source=row.locationSource
        if source=='Your vendor observations' or source=='Observed by you' or source=='Your trainer observations' then
            add('Location','Recorded during an earlier visit; not a live NPC check.')
        elseif source=='WoW taxi map' then add('Location','Client taxi-map coordinates.')
        else add('Location','Recorded coordinates; not a live NPC check.') end
        if source then add('Location source',source) end
    else add('Location','No confirmed local destination.') end
    local confidence=row.priceConfidence
    if not confidence and row.cost~=nil then confidence='estimate' end
    if confidence then add('Price',prices[confidence] or prices.unknown)
    elseif row.spell or row.professionRank or row.criticalBook or row.repair or row.ammoItem or (row.key or ''):match('^supply:') then add('Price',prices.unknown) end
    return lines
end
