local _,A=...
local definitions={
 DungeonJournalRows={category='quests',sub='dungeonjournal',label='DungeonJournal dungeon quests'},
 AttuneRows={category='quests',label='Quest chains'},TurnInRows={category='quests',sub='turnins',label='Quest turn-ins'},
 ImportantVendorRows={category='professions',label='Profession books'},ProfessionRows={category='professions',label='Profession ranks'},
 SupplyRows={category='supplies',label='Supplies'},HunterAmmoRows={category='supplies',sub='ammo',label='Hunter ammunition'},
 RepairRows={category='errands',sub='repairs',label='Repairs'},ClassSpellRows={category='training',sub='class',label='Class spells'},
 WeaponRows={category='training',sub='weapons',label='Weapon skills'},FlightRows={category='errands',sub='flights',label='Flight paths'},
 TrainerRows={category='training',label='Observed training'},BagRows={category='errands',sub='bags',label='Bag space'},
}
local cached={DungeonJournalRows=true,AttuneRows=true,TurnInRows=true,ClassSpellRows=true,WeaponRows=true,FlightRows=true}
function A.InvalidateProviders(names)
    if not names then A.providerCache={};return end
    for _,name in ipairs(names) do if A.providerCache then A.providerCache[name]=nil end end
end
function A.InvalidateForEvent(event)
    local affected={
      BAG_UPDATE_DELAYED={'AttuneRows','DungeonJournalRows'},PLAYER_MONEY={'ClassSpellRows'},
      QUEST_LOG_UPDATE={'AttuneRows','TurnInRows','DungeonJournalRows'},QUEST_TURNED_IN={'AttuneRows','TurnInRows','DungeonJournalRows'},
      QUEST_DATA_LOAD_RESULT={'AttuneRows','TurnInRows','DungeonJournalRows'},
      SPELLS_CHANGED={'AttuneRows','ClassSpellRows','WeaponRows','DungeonJournalRows'},
      SKILL_LINES_CHANGED={'AttuneRows','ClassSpellRows','WeaponRows','DungeonJournalRows'},
      TAXIMAP_OPENED={'FlightRows'},
      UPDATE_INVENTORY_DURABILITY={},MERCHANT_UPDATE={},MERCHANT_SHOW={},MERCHANT_CLOSED={},
      TRAINER_UPDATE={'ClassSpellRows','WeaponRows'},TRAINER_SHOW={'ClassSpellRows','WeaponRows'},
      GET_ITEM_INFO_RECEIVED={'AttuneRows','DungeonJournalRows'},ITEM_DATA_LOAD_RESULT={'AttuneRows','DungeonJournalRows'},
      UNIT_SPELLCAST_SENT={},UNIT_PET={},PET_UI_UPDATE={},PET_BAR_UPDATE={},PLAYER_EQUIPMENT_CHANGED={},
    }
    A.InvalidateProviders(affected[event])
end
function A.ProviderEnabled(name)
    local d=definitions[name]
    if A.db.sources[name]==false or (d and not A.CategoryEnabled(d.category,d.sub)) then return false end
    if name=='ImportantVendorRows' and A.db.importantVendorBuys==false then return false end
    if name=='HunterAmmoRows' and not A.IsHunter() then return false end
    return true
end
local function readiness(name)
    if name=='AttuneRows' then
        if not (Attune_Data and Attune_Data.steps and Attune_Data.attunes and A.AttuneToon()) then return 'Attune character data unavailable' end
        if not (LibQuestieDB and LibQuestieDB.Quest) then return 'Quest eligibility/location data incomplete' end
    elseif name=='DungeonJournalRows' then
        if not (A.DungeonJournalData and A.DungeonJournalData()) then return 'DungeonJournal data unavailable or unsupported' end
        if not (LibQuestieDB and LibQuestieDB.Quest) then return 'Quest eligibility/location data incomplete' end
    elseif name=='TurnInRows' then
        if not (C_QuestLog and C_QuestLog.GetNumQuestLogEntries and C_QuestLog.GetInfo and LibQuestieDB and LibQuestieDB.Quest) then return 'Quest turn-in data unavailable' end
    elseif name=='ProfessionRows' or name=='ImportantVendorRows' then
        local api=SkillUpForever and SkillUpForever.API
        if not (api and api.version==1 and api.Professions) and not (GetProfessions and GetProfessionInfo) then return 'SkillUp profession data unavailable' end
    elseif name=='ClassSpellRows' then
        local _,class=UnitClass('player')
        local data=(TrainerSpells_Data and TrainerSpells_Data[class])
        if not (type(data)=='table' and next(data)) then data=TrainerSpellsBuiltin and TrainerSpellsBuiltin[class] end
        if not (type(data)=='table' and type(TrainerSpellsClassTrainers)=='table') then return 'TrainerSpells class data unavailable' end
    elseif name=='WeaponRows' then
        local d=TrainerSpellsWeaponSkills
        if not (d and d.skills and d.trainers and d.zones) then return 'TrainerSpells weapon data unavailable' end
    elseif name=='FlightRows' and not (C_TaxiMap and C_TaxiMap.GetTaxiNodesForMap) then return 'Flight-path data unavailable' end
end
function A.CheckUnavailable(reason)
    if A.activeProvider then A.providerUnavailable=reason end
end
function A.ChecksIncomplete() return A.providerHealth and next(A.providerHealth)~=nil or false end
function A.CheckHealthText()
    local lines={}
    for name,issue in pairs(A.providerHealth or {}) do
        local d=definitions[name]
        lines[#lines+1]=A.Translate(d and d.label or name)..': '..A.Translate(issue)
    end
    table.sort(lines);return table.concat(lines,'\n')
end
function A.RunProvider(name,out,map,travel,useCache)
    if not A.ProviderEnabled(name) then return end
    local ready,warning=pcall(readiness,name)
    if not ready then A.errors[name]=tostring(warning);A.providerHealth[name]='Check failed; try again';return end
    local fn=A[name]
    if type(fn)~='function' then A.providerHealth[name]='Check unavailable';return end
    local key=tostring(map)..':'..tostring(travel)..':'..tostring(UnitLevel('player'))
    local classData,classTrainers,classPortals
    if name=='ClassSpellRows' then
        if A.ClassSpellData then classData,classTrainers,classPortals=A.ClassSpellData() end
    elseif name=='DungeonJournalRows' then
        local d=A.DungeonJournalData and A.DungeonJournalData()
        if d then key=key..':'..tostring(d.DB)..':'..tostring(d.QUEST_PREREQ_CHAINS)..':'..tostring(d.QUEST_PREREQ_DETAILS)..':'..tostring(d.QUEST_START_MAPS) end
    elseif name=='AttuneRows' then key=key..':'..tostring(Attune_Data)..':'..tostring(A.db.attuneAllChains) end
    local cache=A.providerCache and A.providerCache[name]
    if useCache and cached[name] and not warning and cache and cache.fn==fn and cache.key==key
        and cache.data==classData and cache.trainers==classTrainers and cache.portals==classPortals and time()-cache.when<60 then
        for _,row in ipairs(cache.rows) do
            if row.classSpell and A.PlaceClassSpell then row=A.PlaceClassSpell(row,map) end
            if row then A.Add(out,row) end
        end
        return
    end
    local raw={}
    -- ProfessionRows uses the previously collected book reminders to avoid a duplicate cap warning.
    if name=='ProfessionRows' then for _,row in ipairs(out) do if row.criticalBook then raw[#raw+1]=row end end end
    local seeded=#raw
    A.captureProvider=cached[name] or nil;A.activeProvider=name;A.providerFailure=nil;A.providerUnavailable=nil
    local ok,err=pcall(fn,raw,map,travel)
    A.captureProvider=nil;A.activeProvider=nil
    local failure=A.providerFailure;A.providerFailure=nil
    warning=A.providerUnavailable or warning;A.providerUnavailable=nil
    if not ok or failure then
        A.errors[name]=tostring(not ok and err or failure);A.providerHealth[name]='Check failed; try again'
        if A.providerCache then A.providerCache[name]=nil end
        return
    end
    A.errors[name]=nil
    if warning then A.providerHealth[name]=warning end
    if useCache and cached[name] and not warning then
        A.providerCache=A.providerCache or {};A.providerCache[name]={fn=fn,key=key,when=time(),rows=raw,data=classData,trainers=classTrainers,portals=classPortals}
    end
    for i=seeded+1,#raw do A.Add(out,raw[i]) end
end
