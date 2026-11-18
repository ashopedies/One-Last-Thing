local _,A=...
-- Read-only adapter for TrainerSpells 1.1.15 globals. No namespace extraction,
-- training, ignore-list writes or bundled third-party spell database.
local function spellName(id)
    local info=C_Spell and A.Safe('class spell info',C_Spell.GetSpellInfo,id)
    return info and info.name or A.Safe('class spell name',GetSpellInfo,id)
end
local function raceMatches(required,race)
    if not required then return true end
    if type(required)=='table' then
        for _,r in ipairs(required) do if r==race then return true end end
        return false
    end
    return required==race
end
local function factionMatches(required,faction)
    if not required or required=='' or required=='AH' or required=='Both' then return true end
    return required==faction or required==(faction=='Horde' and 'H' or 'A')
end
function A.LocalClassTrainer(map,locations)
    local _,class=UnitClass('player');local faction=UnitFactionGroup('player')
    local locale=GetLocale and GetLocale() or 'enUS'
    local position=C_Map.GetPlayerMapPosition and C_Map.GetPlayerMapPosition(map,'player')
    local px,py=.5,.5;if position then px,py=position:GetXY() end
    local found,best
    local function consider(location,name)
        if location.uiMapID~=map or not location.x or not location.y then return end
        if not factionMatches(location.faction,faction) then return end
        local distance=(location.x/100-px)^2+(location.y/100-py)^2
        if not best or distance<best then
            found={map=map,x=location.x,y=location.y,name=name};best=distance
        end
    end
    if type(locations)=='table' then
        for _,loc in ipairs(locations) do consider(loc,loc.name or 'Spell trainer') end
        return found
    end
    for _,trainer in ipairs((TrainerSpellsClassTrainers and TrainerSpellsClassTrainers[class]) or {}) do
        if factionMatches(trainer.faction,faction) and (not trainer.starter or UnitLevel('player')<8) then
            local names=trainer.names or {}
            local name=names[locale] or names.enUS or ('Trainer '..tostring(trainer.npcID))
            for _,location in ipairs(trainer.locations or {}) do consider(location,name) end
        end
    end
    return found
end
local function talentState()
    local all,learned={},{}
    if GetNumTalentTabs and GetNumTalents and GetTalentInfo then
        for tab=1,(A.Safe('talent tabs',GetNumTalentTabs) or 0) do
            for i=1,(A.Safe('talent count',GetNumTalents,tab) or 0) do
                -- TalentInfo has more returns than Safe deliberately forwards.
                local ok,name,_,_,_,rank=pcall(GetTalentInfo,tab,i)
                if ok and name then all[name]=true;if (rank or 0)>0 then learned[name]=true end end
            end
        end
    end
    return all,learned,GetNumTalentTabs and GetNumTalents and GetTalentInfo and true or false
end
function A.ClassSpellData()
    local _,class=UnitClass('player')
    local data=TrainerSpells_Data and TrainerSpells_Data[class]
    if type(data)~='table' or not next(data) then data=TrainerSpellsBuiltin and TrainerSpellsBuiltin[class] end
    return data,TrainerSpellsClassTrainers and TrainerSpellsClassTrainers[class]
end
function A.PlaceClassSpell(row,map)
    local target=A.LocalClassTrainer(map,row.trainerLocations)
    if not target then return end
    -- Cached templates must not mutate a row currently being clicked or displayed.
    local placed={};for key,value in pairs(row) do placed[key]=value end
    placed.map,placed.x,placed.y=target.map,target.x,target.y
    placed.detail=target.name..row.trainerDetail
    return placed
end
function A.ClassSpellRows(out,map)
    local data=A.ClassSpellData()
    if type(data)~='table' then
        A.status.ClassSpells='TrainerSpells class catalogue unavailable; visit a trainer for observed entries'
        return
    end
    local trainer=A.LocalClassTrainer(map)
    if not trainer then A.status.ClassSpells='TrainerSpells connected; no suitable class trainer in this zone';return end
    local level=UnitLevel('player');local faction=UnitFactionGroup('player')
    local race;if UnitRace then local _,token=UnitRace('player');race=token end
    local knownRanks,entries={},{}
    for requiredLevel,spells in pairs(data) do
        local bracket=tonumber(requiredLevel) or 999
        for key,value in pairs(type(spells)=='table' and spells or {}) do
            local row=type(value)=='table' and value or {cost=value}
            local id=row.spellID or (type(key)=='number' and key)
            if id then
                local rank=tonumber(row.rank) or tonumber(tostring(row.rank or ''):match('%d+'))
                if bracket<=level and (not row.levelReq or row.levelReq<=level) then
                    local name=spellName(id);local known=A.SpellKnown(id)
                    if name and rank and known then knownRanks[name]=math.max(knownRanks[name] or 0,rank) end
                    entries[#entries+1]={id=id,name=name,rank=rank,data=row,level=bracket,known=known}
                elseif rank and A.SpellKnown(id) then
                    -- Forever can change level requirements. An already learned higher
                    -- rank still suppresses obsolete offers, regardless of catalogue level.
                    local name=spellName(id)
                    if name then knownRanks[name]=math.max(knownRanks[name] or 0,rank) end
                end
            end
        end
    end
    local talents,learnedTalents,talentsVerified=talentState()
    local count=0
    for _,entry in ipairs(entries) do
        local d,id,name=entry.data,entry.id,entry.name
        local gated=name and talents[name] and not learnedTalents[name]
        for _,required in ipairs(d.requires or {}) do
            local n=spellName(required)
            if n and talents[n] and not learnedTalents[n] and not A.SpellKnown(required) then gated=true end
        end
        local uncertain=not talentsVerified and (d.talent or d.talentID or d.source=='talent') and true or false
        for _,required in ipairs(d.requires or {}) do if required~=id and not A.SpellKnown(required) then uncertain=true end end
        local ignored=A.Safe('TrainerSpells ignore',TrainerSpells_IsIgnored,id,name)==true
        local unknown=not entry.known and not (entry.rank and name and entry.rank<=(knownRanks[name] or 0))
        local questReward=d.questReward or d.questStart or d.source=='quest'
        if name and unknown and not ignored and not gated and not questReward and d.status~='missing'
            and entry.level<=level and (not d.levelReq or d.levelReq<=level)
            and factionMatches(d.faction,faction) and raceMatches(d.race,race) then
            local target=trainer
            -- Explicit sources must match this zone, not any class trainer.
            if d.sourceLocations then target=A.LocalClassTrainer(map,d.sourceLocations) end
            if target then
                local cost=tonumber(d.cost) or 0
                local price=A.FormatMoney(cost)
                local shortage=GetMoney and cost>GetMoney()
                local detail=' | '..price..(shortage and ' (short on gold)' or '')..(uncertain and '\nRequirements not verified; check availability at the trainer.' or '\nTrainerSpells catalogue; dismiss a rank to save it for later.')
                A.Add(out,{key='train:spell:'..id,title=(uncertain and 'Check training: ' or 'Train: ')..name..(entry.rank and (' — Rank '..entry.rank) or ''),
                    detail=target.name..detail,
                    classSpell=true,trainerLocations=d.sourceLocations,
                    trainerDetail=detail,
                    map=target.map,x=target.x,y=target.y,priority=25,spell=id,cost=cost,rank=entry.rank,spellName=name,verify=true})
                count=count+1
            end
        end
    end
    A.status.ClassSpells='TrainerSpells 1.1.15 catalogue: '..count..' unlearned ranks at local class trainers (prices may vary)'
end
