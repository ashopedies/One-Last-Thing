local _, A = ...
local function module(name)
    if QuestieLoader and QuestieLoader.ImportModule then
        return A.Safe('Questie '..name, QuestieLoader.ImportModule, QuestieLoader, name)
    end
end
local function db() return LibQuestieDB end
local function read(kind,id,key)
    local lib = db()
    return lib and lib[kind] and A.Safe('DB '..kind..'.'..key,lib[kind].Get,id,key)
end
local function questName(id)
    local native=C_QuestLog and A.Safe('quest title',C_QuestLog.GetTitleForQuestID,id)
    if native and native~='' then return native end
    if C_QuestLog and C_QuestLog.RequestLoadQuestByID then
        A.questRequests=A.questRequests or {}
        if not A.questRequests[id] then A.questRequests[id]=true;A.Safe('load quest title',C_QuestLog.RequestLoadQuestByID,id) end
    end
    return read('Quest',id,'name') or ('Quest '..id)
end
local function validQuestLevel(value)
    local level=tonumber(value)
    if level and level>0 then return math.floor(level) end
end
function A.QuestRecommendedLevel(id)
    if not id then return end
    local level=validQuestLevel(read('Quest',id,'questLevel'))
    if level then return level end
    -- Use the quest's displayed/log level, never its minimum acceptance level.
    local index=C_QuestLog and A.Safe('quest log index',C_QuestLog.GetLogIndexForQuestID,id)
    if index and index>0 then
        local info=A.Safe('quest log level',C_QuestLog.GetInfo,index)
        level=type(info)=='table' and validQuestLevel(info.level)
        if level then return level end
        local _,legacyLevel=A.Safe('legacy quest log level',GetQuestLogTitle,index)
        level=validQuestLevel(legacyLevel)
        if level then return level end
    end
    if C_QuestLog and C_QuestLog.GetInfo and C_QuestLog.GetNumQuestLogEntries then
        local count=A.Safe('quest log count',C_QuestLog.GetNumQuestLogEntries) or 0
        for i=1,count do
            local info=A.Safe('quest log entry level',C_QuestLog.GetInfo,i)
            if info and info.questID==id then return validQuestLevel(info.level) end
        end
    end
end
function A.ReminderTitle(row)
    if not row.quest then return row.title end
    local level=A.QuestRecommendedLevel(row.quest) or validQuestLevel(row.questLevel)
    return '[Lv '..(level or '?')..'] '..(row.title or '')
end
function A.AttuneToon()
    local first,last = UnitName('player')
    local key = first and (last and last ~= '' and (first..' '..last) or first)
    -- Forever's second UnitName return is a surname. Never select an arbitrary alt.
    return Attune_DB and Attune_DB.toons and Attune_DB.toons[key]
end
local function matchesMap(location,map)
    return type(location)=='string' and location~='' and location==A.MapName(map)
end
-- Confirmed destination for the reported cross-zone travel quest. This is
-- used only when no usable finishedBy location can be read from QuestieDB.
-- Pickup remains in Orgrimmar; hand-in is Scooty in Booty Bay (map 1434).
local turnInFallbacks={[2842]={1434,27.6,77.5,'Scooty'}}
function A.QuestLocation(id,finish,map)
    local pickupKnown=false
    if not finish then
        local p = Attune_Data and Attune_Data.questGivers and Attune_Data.questGivers[id]
        if p then pickupKnown=true;if p[1]==map then return p[1],p[2],p[3],p[4],true end end
    end
    local by = read('Quest',id,finish and 'finishedBy' or 'startedBy')
    local zones = module('ZoneDB')
    local hasDestination=false
    if type(by)=='table' and zones and zones.GetUiMapIdByAreaId then
        for index,kind in ipairs({'Npc','Object'}) do
            for _,giver in ipairs(by[index] or {}) do
                for area,points in pairs(read(kind,giver,'spawns') or {}) do
                    local ui = A.Safe('area to map',zones.GetUiMapIdByAreaId,zones,area)
                    if ui and points[1] then
                        hasDestination=true
                        if ui==map then return ui,points[1][1],points[1][2],read(kind,giver,'name'),true end
                    end
                end
            end
        end
    end
    if finish and not hasDestination then
        local p=turnInFallbacks[id]
        if p and p[1]==map then return p[1],p[2],p[3],p[4],true end
    end
    return nil,nil,nil,nil,hasDestination or pickupKnown
end
function A.IsGrayQuest(id)
    local level=tonumber(read('Quest',id,'questLevel'))
    if not level or level<=0 then return nil end
    local compat=module('QuestieCompat')
    local range=compat and A.Safe('quest green range',compat.GetQuestGreenRange)
        or (C_QuestLog and A.Safe('quest trivial range',C_QuestLog.GetTrivialRange))
        or A.Safe('legacy quest green range',GetQuestGreenRange)
    if type(range)~='number' then return nil end
    return level<UnitLevel('player')-range,level
end
function A.GrayChainReasons(data)
    local children={}
    for _,s in pairs(data.steps) do
        for id in tostring(s.FOLLOWS or ''):gmatch('%d+') do
            if id~='0' then
                local key=tostring(s.ID_ATTUNE)..'-'..id
                children[key]=children[key] or {};table.insert(children[key],s)
            end
        end
    end
    return function(step,chain)
        local queue={step};local seen={};local cursor=1;local reachesEnd=false;local later
        while queue[cursor] do
            local s=queue[cursor];cursor=cursor+1
            local key=tostring(s.ID_ATTUNE)..'-'..tostring(s.ID)
            if not seen[key] then
                seen[key]=true
                if s.TYPE=='End' then reachesEnd=true end
                if s.TYPE=='Quest' or s.TYPE=='Pick Up' or s.TYPE=='Turn In' then
                    for text in tostring(s.ID_WOWHEAD or ''):gmatch('%d+') do
                        local id=tonumber(text)
                        if not A.QuestDone(id) then
                            local reward=data.questRewards and data.questRewards[id]
                            for _,spell in ipairs(reward and reward.spells or {}) do
                                if not A.SpellKnown(spell) then
                                    local info=C_Spell and A.Safe('chain reward spell',C_Spell.GetSpellInfo,spell)
                                    local n=info and info.name or (data.rewardSpells and data.rewardSpells[spell] and data.rewardSpells[spell][1])
                                    return 'Grey prerequisite — unlocks '..(n or ('spell '..spell))..' via '..(chain.NAME or 'this chain')
                                end
                            end
                            for _,item in ipairs(reward and reward.fixed or {}) do
                                if read('Item',item[1],'class')==13 then
                                    return 'Grey prerequisite — key/access reward: '..A.ItemName(item[1])
                                end
                            end
                            local gray,level=A.IsGrayQuest(id)
                            if s~=step and gray==false then later='Grey prerequisite — leads to level '..level..' '..questName(id) end
                        end
                    end
                end
                for _,child in ipairs(children[key] or {}) do queue[#queue+1]=child end
            end
        end
        if reachesEnd and (chain.GROUPSIZE or 0)>=10 then return 'Grey prerequisite — raid/access chain: '..(chain.NAME or 'raid access') end
        local utility={['80']=true,['90']=true,['95']=true,['100']=true}
        if reachesEnd and utility[tostring(chain.ID)] then return 'Grey prerequisite — utility reward chain: '..(chain.NAME or 'utility unlock') end
        return later
    end
end
local function eligible(id)
    if A.QuestDone(id) or A.QuestActive(id) then return false end
    local level = UnitLevel('player')
    local required = read('Quest',id,'requiredLevel')
    local max = read('Quest',id,'requiredMaxLevel')
    if required and required>level then return false end
    if max and max>0 and level>max then return false end
    local qdb = module('QuestieDB')
    if qdb and qdb.IsDoable then
        local value = A.Safe('Questie eligibility',qdb.IsDoable,id)
        if value~=nil then return value==true end
    end
    return nil -- Attune's current-step state is a hint, not proven quest availability.
end
A.QuestEligible=eligible
-- A later quest proves its prerequisite steps are no longer pickups. This
-- also suppresses unused OR breadcrumbs when another route was taken.
function A.AttuneProgress(data,toon)
    local byKey,obsolete,complete,doneCache={},{},{},{}
    local function key(s) return tostring(s.ID_ATTUNE)..'-'..tostring(s.ID) end
    local function done(id)
        if doneCache[id]==nil then doneCache[id]=A.QuestDone(id) end
        return doneCache[id]
    end
    for _,s in pairs(data.steps) do byKey[key(s)]=s end
    local function ancestors(s,seen)
        seen=seen or {};local k=key(s);if seen[k] then return end;seen[k]=true
        for id in tostring(s.FOLLOWS or ''):gmatch('%d+') do
            if id~='0' then
                local previous=byKey[tostring(s.ID_ATTUNE)..'-'..id]
                if previous then obsolete[key(previous)]=true;ancestors(previous,seen) end
            end
        end
    end
    local progressedOR={}
    for _,s in pairs(data.steps) do
        local k=key(s);local progressed=toon.done and toon.done[k]
        if s.TYPE=='End' and progressed then complete[tostring(s.ID_ATTUNE)]=true end
        if s.TYPE=='Quest' or s.TYPE=='Pick Up' or s.TYPE=='Turn In' then
            for value in tostring(s.ID_WOWHEAD or ''):gmatch('%d+') do
                local id=tonumber(value)
                if done(id) then obsolete[k]=true;progressed=true end
                if A.QuestActive(id) then progressed=true end
            end
        end
        if progressed then
            ancestors(s)
            if s.OR then progressedOR[tostring(s.ID_ATTUNE)..':'..tostring(s.FOLLOWS)]=k end
        end
    end
    for _,s in pairs(data.steps) do
        if s.OR then
            local taken=progressedOR[tostring(s.ID_ATTUNE)..':'..tostring(s.FOLLOWS)]
            if taken and taken~=key(s) then obsolete[key(s)]=true end
        end
    end
    -- The Water Totem reward is explicit proof for this class chain, even
    -- when the client omits completion flags for its alternate breadcrumbs.
    local _,class=UnitClass('player')
    if class=='SHAMAN' then
        local fn=C_Item and C_Item.GetItemCount or GetItemCount
        if A.SpellKnown(5394) or (A.Safe('Water Totem reward',fn,5177,true,false) or 0)>0 then
            complete['5234']=true;complete['5244']=true
        end
    end
    for id,percent in pairs(toon.attuned or {}) do
        if type(percent)=='number' and percent>=100 then complete[tostring(id)]=true end
    end
    return obsolete,complete
end
-- Read prerequisites ourselves for unflagged starts. Questie remains the
-- authority when it can positively validate a pickup's actual availability.
function A.AttuneReadiness(data,toon,obsolete)
    local steps,memo,visiting={},{},{}
    for _,s in pairs(data.steps) do steps[tostring(s.ID_ATTUNE)..'-'..tostring(s.ID)]=s end
    local predecessors,stepDone
    predecessors=function(s)
        local follows=tostring(s.FOLLOWS or '0')
        local any=follows:find('|',1,true)~=nil
        local count,passed=0,0
        for id in follows:gmatch('%d+') do
            if id~='0' then
                count=count+1
                local key=tostring(s.ID_ATTUNE)..'-'..id
                if stepDone(key) then passed=passed+1 end
            end
        end
        return count==0 or (any and passed>0) or (not any and passed==count)
    end
    stepDone=function(key)
        if memo[key]~=nil then return memo[key] end
        if visiting[key] then return false end
        if (toon.done and toon.done[key]) or obsolete[key] then memo[key]=true;return true end
        local s=steps[key];if not s then return false end
        visiting[key]=true
        local done=false
        if s.TYPE=='Level' then done=UnitLevel('player')>=(tonumber(s.ID_WOWHEAD) or 999)
        elseif s.TYPE=='Spacer' then done=predecessors(s)
        elseif s.TYPE=='Item' then done=A.ItemCount(tonumber(s.ID_WOWHEAD) or 0)>=(tonumber(s.COUNT) or 1)
        elseif s.TYPE=='Quest' or s.TYPE=='Turn In' or s.TYPE=='Pick Up' then
            for text in tostring(s.ID_WOWHEAD or ''):gmatch('%d+') do
                local id=tonumber(text)
                if A.QuestDone(id) or (s.TYPE=='Pick Up' and A.QuestActive(id)) then done=true;break end
            end
        end
        visiting[key]=nil;memo[key]=done
        return done
    end
    return predecessors
end
function A.AttuneRows(out,map)
    local data,toon=Attune_Data,A.AttuneToon()
    if not (data and data.steps and data.attunes and toon) then
        A.status.Attune='Not ready: Attune data/current character unavailable';return
    end
    local all=A.db.attuneAllChains~=false
    A.status.Attune=all and 'Scanning all applicable unfinished quest chains' or 'Attune current steps only'
    local chains,hasQuests={},{}
    local _,class=UnitClass('player');local faction=UnitFactionGroup('player')
    for _,chain in pairs(data.attunes) do chains[tostring(chain.ID)]=chain end
    for _,s in pairs(data.steps) do
        if s.TYPE=='Pick Up' or s.TYPE=='Quest' or s.TYPE=='Turn In' then hasQuests[tostring(s.ID_ATTUNE)]=true end
    end
    local obsolete,finishedChains=A.AttuneProgress(data,toon)
    local predecessorsReady=A.AttuneReadiness(data,toon,obsolete)
    local grayReason=A.GrayChainReasons(data)
    local function applicable(chain,aid)
        return chain and hasQuests[aid] and not finishedChains[aid]
            and not (toon.skip and toon.skip[aid])
            and (not chain.CLASS or chain.CLASS=='' or chain.CLASS==class)
            and (not chain.FACTION or chain.FACTION=='Both' or chain.FACTION==faction)
            and (not chain.DEPRECATED or (Attune_DB and Attune_DB.showDeprecatedAttunes))
    end
    -- Make every applicable chain available as a settings subcategory, including
    -- chains whose next pickup is outside the current zone.
    for aid,chain in pairs(chains) do
        if applicable(chain,aid) then
            local name=chain.NAME or aid
            if chain.GROUP and chain.GROUP~='' then name=chain.GROUP..' · '..name end
            A.categories[1].subs['chain:'..aid]=name
        end
    end
    local count=0
    for _,step in pairs(data.steps) do
        local aid=tostring(step.ID_ATTUNE);local key=aid..'-'..tostring(step.ID)
        local chain=chains[aid];local kind=step.TYPE
        local current=toon.next and toon.next[key]
        if applicable(chain,aid) and (all or current) and (all or not step.SIDE)
            and not obsolete[key] and not (toon.done and toon.done[key])
            and (not Attune_StepShownForRace or A.Safe('Attune race gate',Attune_StepShownForRace,step,toon.race))
            and (kind=='Pick Up' or kind=='Quest' or kind=='Turn In') then
            local ready=current or predecessorsReady(step)
            for text in tostring(step.ID_WOWHEAD or ''):gmatch('%d+') do
                local id=tonumber(text)
                local finish=kind=='Turn In' or (kind=='Quest' and A.QuestReady(id))
                local allow=finish and A.QuestReady(id) or (not finish and eligible(id))
                local hint=not finish and allow==nil and ready and not A.QuestActive(id) and not A.QuestDone(id)
                local accepted=finish and allow or (not finish and (allow==true or hint))
                local m,x,y,npc,knownLocation=A.QuestLocation(id,finish,map)
                -- A chain's general LOCATION is only a weak pickup hint. Never
                -- override a known giver elsewhere, or use it for a hand-in.
                local localHint=not finish and not m and not knownLocation and matchesMap(step.LOCATION,map)
                local gray=not finish and A.IsGrayQuest(id)==true
                local importantReason=gray and grayReason(step,chain)
                if gray and not importantReason then accepted=false end
                if accepted and (m or localHint) then
                    count=count+1
                    A.Add(out,{key='quest:'..id..(finish and ':end' or ':start'),
                        title=(finish and 'Chain turn-in: ' or (hint and 'Check pickup: ' or 'Pick up: '))..questName(id),
                        detail=(chain.NAME or aid)..' | '..(npc or step.LOCATION or '')..'\nAttune chain'..(hint and '; availability not verified' or ''),
                        priority=chain.CLASS and 5 or (finish and 10 or 20),
                        map=m or map,x=x,y=y,quest=id,finish=finish,gray=gray,importantReason=importantReason,attuneStep=step,chainName=chain.NAME,
                        dungeonPickup=not finish and A.IsDungeonChain(chain),classQuest=chain.CLASS and chain.CLASS~='',
                        accessQuest=A.IsAccessChain(chain),verify=hint or localHint or false,why=A.ChainWhy(chain,finish)})
                end
            end
        end
    end
    A.status.AttuneLocal=tostring(count)..' local unfinished-chain candidates'
end
function A.TurnInRows(out,map)
    if not (C_QuestLog and C_QuestLog.GetNumQuestLogEntries and C_QuestLog.GetInfo) then return end
    local n=A.Safe('quest log count',C_QuestLog.GetNumQuestLogEntries) or 0
    for i=1,n do
        local info=A.Safe('quest log row',C_QuestLog.GetInfo,i)
        local id=info and info.questID
        if id and id>0 and A.QuestReady(id) then
            local m,x,y,npc=A.QuestLocation(id,true,map)
            if m then A.Add(out,{key='quest:'..id..':end',title='Turn in: '..(info.title or questName(id)),
                detail=(npc or 'Quest giver')..' | Completed quest in your log',map=m,x=x,y=y,quest=id,finish=true,priority=10}) end
        end
    end
end
-- Native state fills professions omitted by SkillUp's crafting plans. Copies only:
-- never mutate another addon's API results or interpret recipe routes as rank eligibility.
function A.ProfessionPlans()
    local api=SkillUpForever and SkillUpForever.API
    local plans=api and api.version==1 and api.Professions and A.Safe('SkillUp professions',api.Professions,{steps=25,recipes=1})
    if type(plans)~='table' then plans=nil end
    local list,byID={},{}
    for _,p in ipairs(plans or {}) do
        if type(p)=='table' and p.skillLineID then
            local copy={};for key,value in pairs(p) do copy[key]=value end
            list[#list+1]=copy;byID[p.skillLineID]=copy
        end
    end
    local native=false
    if GetProfessions and GetProfessionInfo then
        local ok,a,b,c,d,e,f=pcall(GetProfessions)
        if ok then
            native=true
            for _,index in pairs({a,b,c,d,e,f}) do
                local good,name,_,rank,cap,_,_,id=pcall(GetProfessionInfo,index)
                if good and id and name and type(rank)=='number' and type(cap)=='number' and cap>0 then
                    local p=byID[id]
                    if not p then
                        p={skillLineID=id,name=name,rank=rank,maxRank=cap};list[#list+1]=p;byID[id]=p
                    else
                        p.maxRank=cap -- native cap also completes a just-learned rank immediately
                    end
                elseif not good then native=false end
            end
        end
    end
    if plans or native then return list end
end
-- Eligibility facts mirror verified rank requirements. Books and quest ranks
-- use independent progression rules below. Skinning's disputed level gate is retained.
local trainerRankRequirements={
    [129]={{50,0}}, [185]={{50,10}}, [356]={{50,10}},
    [164]={{50,10},{125,20},{200,35}}, [165]={{50,10},{125,20},{200,35}},
    [171]={{50,10},{125,20},{200,35}}, [202]={{50,10},{125,20},{200,35}},
    [333]={{50,10},{125,20},{200,35}}, [197]={{50,10},{125,20},{200,35}},
    [182]={{50,0},{125,0},{200,0}}, [186]={{50,0},{125,0},{200,0}},
    [393]={{50,0},{125,0},{200,35}},
}
-- Two high-rank trainers missing from the installed Forever trainer table.
-- Rogvar: user-confirmed in Stonard; TrainerSpells Classic coordinates and
-- Wowhead Forever Alchemy overview (checked 2026-11-21). Drakk: Classic trainer
-- record, also listed by Forever guides; reminders remain marked for verification.
local rankTrainerFallbacks={
    Alchemy={{npcID=1386,rank=4,faction='H',names={enUS='Rogvar'},
        locations={{uiMapID=1435,x=48.53,y=55.85}}}},
    Leatherworking={{npcID=11097,rank=4,faction='A',names={enUS='Drakk Stonehand',deDE='Drakk Steinhand'},
        locations={{uiMapID=1425,x=13.39,y=43.49}}}},
}
local function availableRank(p)
    local ranks=trainerRankRequirements[p.skillLineID]
    local index=p.maxRank and p.maxRank/75
    local req=ranks and ranks[index]
    if req and (p.rank or 0)>=req[1] and (UnitLevel('player') or 0)>=req[2] then
        return p.maxRank+75
    end
end
function A.LocalProfessionTrainer(profession,map)
    if not profession.maxRank or profession.maxRank<=0 or profession.maxRank>=300 then return end
    local key
    for _,category in ipairs(A.categories) do if category.id=='professions' then key=category.subs[tostring(profession.skillLineID)];break end end
    local trainers=key and TrainerSpellsProfessionTrainers and TrainerSpellsProfessionTrainers[key]
    local fallback=key and rankTrainerFallbacks[key]
    if type(trainers)~='table' then trainers={} end
    local nextRank=math.floor(profession.maxRank/75)+1
    local side=UnitFactionGroup('player')=='Horde' and 'H' or 'A'
    local locale=GetLocale and GetLocale() or 'enUS'
    local scope=A.scope or {};local px,py=scope.x or .5,scope.y or .5
    local best,distance
    local candidates={}
    local seen={}
    for _,trainer in ipairs(trainers) do candidates[#candidates+1]=trainer;if trainer.npcID then seen[trainer.npcID]=true end end
    for _,trainer in ipairs(fallback or {}) do if not seen[trainer.npcID] then candidates[#candidates+1]=trainer end end
    for _,trainer in ipairs(candidates) do
        if (trainer.rank or 0)>=nextRank and type(trainer.faction)=='string' and trainer.faction:find(side,1,true) then
            for _,location in ipairs(trainer.locations or {}) do
                if location.uiMapID==map and location.x and location.y and A.Nearby(map,location.x,location.y) then
                    local d=(location.x/100-px)^2+(location.y/100-py)^2
                    if not distance or d<distance then
                        distance=d;best={map=map,x=location.x,y=location.y,name=(trainer.names or {})[locale] or (trainer.names or {}).enUS or 'Trainer'}
                    end
                end
            end
        end
    end
    return best
end
-- These rank quests are progression gates, independent of crafting routes.
-- Sources: Wowhead Forever and WoW-Professions guides, checked 2026-11-21.
local curatedRankQuestIDs={[6622]=true,[6624]=true,[6610]=true,[6607]=true}
local rankQuests={
    [129]={H={id=6622,map=1417,x=73.4,y=36.8,name='Doctor Gregory Victor'},
           A={id=6624,map=1445,x=67.6,y=48.8,name='Doctor Gustaf VanHowzen'}},
    [185]={id=6610,map=1446,x=52.6,y=28.0,name='Dirge Quikcleave'},
    [356]={id=6607,map=1445,x=58.6,y=60.0,name='Nat Pagle'},
}
-- Shared explanatory facts for every known progression gate. These do not
-- relax pickup/training eligibility or turn a general warning into a location.
function A.ProfessionRankRequirements(p)
    if not p or type(p.maxRank)~='number' then return end
    if p.maxRank==150 and A.ProfessionRankBookRequirement then
        local skill,level,cap=A.ProfessionRankBookRequirement(p.skillLineID)
        if skill then return skill,level,cap end
    end
    if p.maxRank==225 and rankQuests[p.skillLineID] then return 225,35,300 end
    local ranks=trainerRankRequirements[p.skillLineID]
    local req=ranks and ranks[p.maxRank/75]
    if req then return req[1],req[2],p.maxRank+75 end
end
function A.ProfessionRankRequirementText(p)
    local skill,level=A.ProfessionRankRequirements(p)
    if not skill then return end
    local text=A.Translate('Requires')..' '..A.Translate(p.name or 'Profession')..' '..skill
    -- Put the character gate first so it remains visible in a narrow row.
    if level>0 then text=A.Translate('Requires level '..level)..' | '..text end
    return text
end
local function capWarningDetail(p)
    local text=A.ProfessionRankRequirementText(p)
    if not text then return 'Near the current rank cap. Check the next rank in SkillUp before travelling. This is a general warning, not proof of a local trainer.' end
    return text..'\n'..A.Translate('Current skill cap')..': '..p.maxRank..'. '..A.Translate('Local trainer not confirmed.')
end
local function rankQuestRow(out,p,map)
    local q=rankQuests[p.skillLineID]
    if not q then return false end
    q=q.id and q or q[UnitFactionGroup('player')=='Horde' and 'H' or 'A']
    if p.maxRank~=225 or (p.rank or 0)<225 or UnitLevel('player')<35 or A.QuestDone(q.id) then return false end
    local finish=A.QuestReady(q.id)
    if A.QuestActive(q.id) and not finish then return false end
    if not finish and eligible(q.id)==false then return false end
    local m,x,y,npc,known=A.QuestLocation(q.id,finish,map)
    if not m and not known and q.map==map then m,x,y,npc=q.map,q.x,q.y,q.name end
    if not m or not A.Nearby(m,x,y) then return false end
    for _,row in ipairs(out) do if row.quest==q.id and not not row.finish==not not finish then return true end end
    if A.ReminderHidden({key='rank:'..p.skillLineID..':'..q.id,quest=q.id}) then return true end
    A.Add(out,{key='quest:'..q.id..(finish and ':end' or ':start'),quest=q.id,finish=finish,
        title=p.name..': '..A.Translate(finish and 'Turn in rank quest' or 'Pick up rank quest'),
        detail=(npc or q.name)..'\n'..A.Translate('Next skill cap')..': 300'..'\n'..(A.ProfessionRankRequirementText(p) or ''),
        map=m,x=x,y=y,professionID=p.skillLineID,profession=p.name,professionRank=true,capMax=225,
        priority=12,verify=true,why='Profession rank progression: '..p.name})
    return true -- covered even when skipped/ignored; never replace it with a cap warning
end
local function annoraRow(out,p,map)
    if p.skillLineID~=333 or p.maxRank~=225 or (p.rank or 0)<200 or UnitLevel('player')<35 or map~=1418 then return false end
    -- Approximate cave approaches, not Annora's indoor position. Both entrances
    -- are supported so players taking the shorter back route also get warned.
    local best,dist
    for _,point in ipairs({{44.2,12.2},{65.1,43.4}}) do
        if A.Nearby(map,point[1],point[2]) then
            local scope=A.scope or {};local d=((scope.x or .5)-point[1]/100)^2+((scope.y or .5)-point[2]/100)^2
            if not dist or d<dist then best,dist=point,d end
        end
    end
    if not best then return false end
    A.Add(out,{key='rank:333:225',title=p.name..': '..A.Translate('Train next profession rank'),
        detail=A.Translate('Annora is inside Uldaman. This pin marks the entrance, not the trainer.')..'\n'..A.Translate('Next skill cap')..': 300'..'\n'..(A.ProfessionRankRequirementText(p) or ''),
        why=A.Translate('Train Artisan Enchanting during this Uldaman visit.'),
        map=map,x=best[1],y=best[2],professionID=333,profession=p.name,professionRank=true,capMax=225,priority=12,verify=true})
    return true
end
function A.ProfessionRows(out,map,travel)
    local list=A.ProfessionPlans()
    if not list then
        A.status.SkillUp='Public API unavailable; no guessed trainer locations'
        if A.CheckUnavailable then A.CheckUnavailable('SkillUp profession data unavailable') end
        return
    end
    A.status.SkillUp='Ranks/books only; dynamic recipe shopping disabled'
    for _,p in ipairs(list) do
        local cap=availableRank(p)
        local localRank=cap and A.LocalProfessionTrainer(p,map)
        local covered=rankQuestRow(out,p,map) or annoraRow(out,p,map)
        local hasBook=A.coveredBooks and A.coveredBooks[p.skillLineID]
        for _,r in ipairs(out) do if r.criticalBook and r.professionID==p.skillLineID then hasBook=true end end
        if not hasBook and not localRank and not covered and p.rank and p.maxRank and p.maxRank>0 and p.maxRank<300 and p.rank>=p.maxRank-10 then
            A.Add(out,{key='cap:'..p.skillLineID,capMax=p.maxRank,professionID=p.skillLineID,profession=p.name,title=p.name..': '..p.rank..' / '..p.maxRank,
                detail=capWarningDetail(p),requiredSkill=select(1,A.ProfessionRankRequirements(p)),requiredLevel=select(2,A.ProfessionRankRequirements(p)),priority=30})
        end
        for i,step in ipairs(p.steps or {}) do
            if step.kind=='train' and not step.itemID and not step.spellID
                and not (rankQuests[p.skillLineID] and p.maxRank==225 and (not step.questID or curatedRankQuestIDs[step.questID]))
                and not (p.skillLineID==333 and covered)
                and (step.questID or (p.maxRank and p.maxRank<300 and (not trainerRankRequirements[p.skillLineID] or not trainerRankRequirements[p.skillLineID][p.maxRank/75] or cap))) then
                local m,x,y,npc
                local finish=step.questID and A.QuestReady(step.questID)
                if step.questID then m,x,y,npc=A.QuestLocation(step.questID,finish,map) end
                -- API detail is human-readable. Match a full zone-name token, not substrings.
                local detail=step.detail or ''
                local zone=A.MapName(map)
                local textMatch=false
                if zone and zone~='' then
                    local start=1
                    while true do
                        local a,b=detail:find(zone,start,true)
                        if not a then break end
                        local left,right=detail:sub(a-1,a-1),detail:sub(b+1,b+1)
                        if (a==1 or not left:match('[%w]')) and (b==#detail or not right:match('[%w]')) then textMatch=true;break end
                        start=b+1
                    end
                end
                if type(step.cost)=='number' then detail=detail:gsub('%s*·%s*.*$','')..' | '..A.FormatMoney(step.cost) end
                local trainer=not step.questID and A.LocalProfessionTrainer(p,map)
                if trainer then
                    m,x,y,npc=trainer.map,trainer.x,trainer.y,trainer.name
                    detail=trainer.name..' | '..(type(step.cost)=='number' and A.FormatMoney(step.cost) or A.Translate('price unknown'))
                end
                local questAllowed=not step.questID or finish or eligible(step.questID)~=false
                if questAllowed and (m or textMatch) then
                    A.Add(out,{key='rank:'..p.skillLineID..':'..(step.questID or p.maxRank or i),
                        title=p.name..': '..(finish and A.Translate('Turn in rank quest') or (step.text or 'Train next profession rank')),
                        detail=detail..'\nProfession rank'..(textMatch and not m and ' (zone matched from route text)' or '')..'\n'..(A.ProfessionRankRequirementText(p) or ''),
                        map=m,x=x,y=y,quest=step.questID,finish=finish,skill=p.skillLineID,professionID=p.skillLineID,profession=p.name,professionRank=true,capMax=p.maxRank,cost=step.cost,stepIndex=i,priority=12,verify=true,why='Profession rank progression: '..p.name})
                end
            end
        end
        if not hasBook and not covered and localRank then
            A.Add(out,{key='rank:'..p.skillLineID..':'..p.maxRank,
                title=p.name..': '..A.Translate('Train next profession rank'),
                detail=localRank.name..' | '..A.Translate('price unknown')..'\n'..A.Translate('Next skill cap')..': '..cap..'\n'..(A.ProfessionRankRequirementText(p) or ''),
                map=localRank.map,x=localRank.x,y=localRank.y,professionID=p.skillLineID,profession=p.name,
                professionRank=true,capMax=p.maxRank,priority=12,verify=true,why='Profession rank progression: '..p.name})
        end
    end
end
-- Small verified fallback for Ankhs. Runtime QuestieDB vendors and personal
-- merchant observations extend this to other supplies and locations.
-- Source: zephras.com/forever/enUS/item/17030 and linked NPC sightings,
-- checked 2026-11-16. Coordinates are approximate; Chepi patrols.
local ankhSellers={
    {npc=4562,name='Thomas Mordan',map=1458,x=69.5,y=39.1,faction='Horde'},
    {npc=3323,name='Horthus',map=1454,x=45.4,y=56.6,faction='Horde'},
    {npc=3335,name='Hagrus',map=1454,x=46.1,y=45.8,faction='Horde'},
    {npc=3351,name='Magenius',map=1454,x=45.7,y=40.9,faction='Horde'},
    {npc=8361,name='Chepi',map=1456,x=42.6,y=56.0,faction='Horde',roaming=true},
}
local capitalMaps={[1637]=1454,[1497]=1458,[1638]=1456,[1519]=1453,[1537]=1455,[1657]=1457}
-- Additional vendor names supplied by the user (Wowhead Forever listing).
local suppliedAnkhNames={"Deneb Walker","Balai Lok'Wein","Hagrus","Llana","Chepi","Keldric Boucher","Hula'mahi","Horthus","Owen Vaughn","Barim Jurgenstaad","Thomas Mordan","Kyra Boucher","Magenius","Alaindia","Jaysin Lanyda","Hannah Akeley","Charys Yserian","Dawn Brightstar","Ginny Longberry","Brother Cassius","Montarr","Jeeda","Reagent Bot","Marla Bell","Vi'el","Falkan Armonis","Cyroen","Repair Bot","Alyssa Eva","Frostwolf Quartermaster","Darahir","Mystic Yayo'jin","Hagatha Moorehead","Thultazor","Stormpike Quartermaster","Jadenvis Seawatcher","Tarhus","First Sergeant Hola'mahi","Lieutenant Jackspring","Kurdrum Barleybeard","Yaelika Farclaw","Khur Hornstriker"}
local namedAnkhIDs
function A.FindVendor(id,map)
    local candidates={}
    local faction=UnitFactionGroup('player')
    local side=faction=='Horde' and 'H' or 'A'
    for m,v in pairs(A.db.vendors[id] or {}) do
        candidates[#candidates+1]={map=m,name=v.name,x=v.x,y=v.y,source='Observed by you'}
    end
    local original=read('Item',id,'vendors')
    local ids,seen={},{}
    for _,npc in ipairs(type(original)=='table' and original or {}) do ids[#ids+1]=npc;seen[npc]=true end
    if id==17030 and db() and db().Npc and db().Npc.IdsByName then
        if not namedAnkhIDs then
            namedAnkhIDs={}
            for _,name in ipairs(suppliedAnkhNames) do
                local found=A.Safe('Ankh vendor name',db().Npc.IdsByName,name)
                for _,npc in ipairs(found or {}) do namedAnkhIDs[#namedAnkhIDs+1]=npc end
            end
            if #namedAnkhIDs==0 then namedAnkhIDs=nil end
        end
        for _,npc in ipairs(namedAnkhIDs or {}) do if not seen[npc] then ids[#ids+1]=npc;seen[npc]=true end end
    end
    local zones=#ids>0 and module('ZoneDB')
    for _,npc in ipairs(ids) do
        local friendly=read('Npc',npc,'friendlyToFaction')
        if type(friendly)=='string' and friendly:find(side,1,true) then
            for area,points in pairs(read('Npc',npc,'spawns') or {}) do
                local m=capitalMaps[area] or (zones and A.Safe('vendor area map',zones.GetUiMapIdByAreaId,zones,area))
                local enemyCapital=(side=='H' and (m==1453 or m==1455 or m==1457)) or (side=='A' and (m==1454 or m==1456 or m==1458))
                if m and not enemyCapital then
                    for _,p in ipairs(points) do
                        candidates[#candidates+1]={map=m,x=p[1],y=p[2],name=read('Npc',npc,'name') or ('NPC '..npc),source='QuestieDB'}
                    end
                end
            end
        end
    end
    if id==17030 then
        for _,v in ipairs(ankhSellers) do
            if v.faction==faction then
                candidates[#candidates+1]={map=v.map,x=v.x,y=v.y,name=read('Npc',v.npc,'name') or v.name,
                    source=v.roaming and 'Recorded seller (patrols nearby)' or 'Recorded Forever seller'}
            end
        end
    end
    local pos=C_Map.GetPlayerMapPosition and C_Map.GetPlayerMapPosition(map,'player')
    local px,py=.5,.5
    if pos then px,py=pos:GetXY() end
    local function score(v)
        if v.map~=map then return 100000+v.map end
        return ((v.x or 50)/100-px)^2+((v.y or 50)/100-py)^2
    end
    table.sort(candidates,function(a,b)
        local sa,sb=score(a),score(b)
        if sa==sb then return (a.name or '')<(b.name or '') end
        return sa<sb
    end)
    return candidates[1]
end
function A.AddSupplyReminder(out,id,rule,map,travel,ammo)
    local count=A.ItemCount(id)
    if count<rule.target and UnitLevel('player')>=(rule.minLevel or 1) and (not A.SupplyRelevant or A.SupplyRelevant(id,rule)) then
        local vendor=A.FindVendor(id,map)
        if vendor and (travel or vendor.map==map or IsResting()) then
            local detail='Seller location unavailable; check this item’s sources.'
            if vendor then
                local info=C_Map.GetMapInfo(vendor.map)
                local zone=info and info.name or ('Map '..vendor.map)
                detail=vendor.name..' — '..zone
                if vendor.x and vendor.y then detail=detail..string.format(' (%.1f, %.1f)',vendor.x,vendor.y) end
                detail=detail..'\n'..vendor.source
            end
            local estimate=A.SupplyEstimate(id,rule.target)
            local first=detail:match('^[^\n]*') or detail
            if estimate.cost then
                local unit=estimate.price%estimate.bundle==0 and (A.FormatMoney(estimate.price/estimate.bundle)..' each') or (A.FormatMoney(estimate.price)..' per '..estimate.bundle)
                detail=first..'\nBuy '..estimate.buy..' | '..(estimate.exact and '' or '~')..unit..' | '..(estimate.exact and '' or '~')..A.FormatMoney(estimate.cost)..' total'
            else detail=first..'\nNeed '..estimate.missing..' | Price unknown until a merchant visit' end
            A.Add(out,{key=ammo and ammo.key or ('supply:'..id),ammoItem=ammo and id,ammoKind=ammo and ammo.ammoKind,inventoryWarning=true,emptyEssential=count==0 and (ammo~=nil or (id==17030 and select(2,UnitClass('player'))=='SHAMAN')),title='Restock '..A.ItemName(id)..': '..count..' / '..rule.target,
                detail=detail,map=vendor and vendor.map,x=vendor and vendor.x,y=vendor and vendor.y,priority=8})
        end
    end
end
function A.SupplyRows(out,map,travel)
    for id,rule in pairs(A.db.supplies) do A.AddSupplyReminder(out,id,rule,map,travel) end
end

function A.ObserveMerchant()
    local map=A.Map()
    if not map or not GetMerchantNumItems or not GetMerchantItemLink then return end
    local pos=C_Map.GetPlayerMapPosition and C_Map.GetPlayerMapPosition(map,'player')
    local x,y
    if pos then x,y=pos:GetXY();x,y=x*100,y*100 end
    local ammo=A.IsHunter and A.IsHunter() and A.HunterAmmoSelection()
    for i=1,GetMerchantNumItems() do
        local link=GetMerchantItemLink(i)
        local id=link and tonumber(link:match('item:(%d+)'))
        if id and (A.db.supplies[id] or id==ammo or (A.IsClassVendorCandidate and A.IsClassVendorCandidate(id))) then
            A.db.vendors[id]=A.db.vendors[id] or {}
            A.db.vendors[id][map]={name=UnitName('npc') or 'Merchant',x=x,y=y}
            local info=A.MerchantInfo(i)
            if info and info.price and info.stackCount and info.stackCount>0 and not info.hasExtendedCost then
                local price={price=info.price,bundle=info.stackCount,name=UnitName('npc') or 'Merchant',map=map}
                A.db.supplyPrices[id]=price;A.liveSupplyPrices=A.liveSupplyPrices or {};A.liveSupplyPrices[id]=price
            end
        end
    end
end
local professionTrainingIndex
local function professionTrainingData()
    local npcs,builtin,observed=TrainerSpellsProfessionTrainers,TrainerSpellsBuiltin_Profession,TrainerSpells_ProfessionData
    local index=professionTrainingIndex
    if index and index.npcs==npcs and index.builtin==builtin and index.observed==observed then return index end
    index={npcs=npcs,builtin=builtin,observed=observed,ids={},names={},spells={}}
    for _,trainers in pairs(npcs or {}) do
        for _,trainer in ipairs(type(trainers)=='table' and trainers or {}) do
            if trainer.npcID then index.ids[trainer.npcID]=true end
            for _,name in pairs(trainer.names or {}) do index.names[name]=true end
        end
    end
    local function recipes(data)
        for _,levels in pairs(data or {}) do
            for _,spells in pairs(type(levels)=='table' and levels or {}) do
                for id,row in pairs(type(spells)=='table' and spells or {}) do
                    local spell=type(row)=='table' and row.spellID or nil
                    if type(spell or id)=='number' then index.spells[spell or id]=true end
                end
            end
        end
    end
    recipes(builtin);recipes(observed)
    professionTrainingIndex=index
    return index
end
function A.IsProfessionTraining(entry,service)
    if entry and entry.professionTrainer==true then return true end
    if service and (service.professionID or A.ProfessionID(service.profession)) then return true end
    local index=professionTrainingData()
    return (entry and ((entry.npcID and index.ids[entry.npcID]) or (not entry.npcID and index.names[entry.name])))
        or (service and service.spell and index.spells[service.spell]) or false
end
function A.ObserveTrainer()
    if not (GetNumTrainerServices and GetTrainerServiceInfo) then
        A.status.Trainer='Trainer listing API unavailable';return
    end
    local map=A.Map();if not map then return end
    local guid=UnitGUID and UnitGUID('npc')
    local name=UnitName('npc') or 'Trainer'
    local identity=guid and guid:match('^[^-]+%-[^-]*%-[^-]*%-[^-]*%-[^-]*%-(%d+)%-') or name
    local key=tostring(map)..':'..tostring(identity)
    local entry=A.db.trainers[key] or {map=map,name=name,services={}}
    A.db.trainers[key]=entry
    entry.npcID=tonumber(identity)
    entry.seen=time()
    local pos=C_Map.GetPlayerMapPosition and C_Map.GetPlayerMapPosition(map,'player')
    if pos then local x,y=pos:GetXY();entry.x,entry.y=x*100,y*100 end
    professionTrainingIndex=nil -- TrainerSpells can update captured tables in place.
    local tradeskill=A.Safe('profession trainer type',IsTradeskillTrainer)
    if tradeskill~=nil then entry.professionTrainer=tradeskill==true end
    if A.IsProfessionTraining(entry) then
        entry.professionTrainer=true;entry.services={}
        A.status.Trainer=A.Translate('Profession recipes excluded; rank upgrades use profession progression checks')
        return
    end
    for i=1,GetNumTrainerServices() do
        local service,second,third=GetTrainerServiceInfo(i)
        -- Forever uses name/category; older Classic builds use name/rank/category.
        local category=(second=='available' or second=='unavailable' or second=='used' or second=='header') and second or third
        if service and category~='header' then
            local tip=C_TooltipInfo and C_TooltipInfo.GetTrainerService and A.Safe('trainer tooltip',C_TooltipInfo.GetTrainerService,i)
            local spell=tip and tip.id
            if issecretvalue and issecretvalue(spell) then spell=nil end
            local cost=A.Safe('training cost',GetTrainerServiceCost,i) or 0
            local rank=category==third and second or ''
            local id=spell and ('spell:'..spell) or ('name:'..service..':'..(rank or '')..':'..cost)
            if category=='available' then
                local skillName=A.Safe('trainer skill name',GetTrainerServiceSkillReq,i)
                local professionID=A.ProfessionID(skillName)
                local offer={name=service,rank=rank,spell=spell,cost=cost,profession=skillName,professionID=professionID}
                if A.IsProfessionTraining(entry,offer) then entry.services[id]=nil
                else entry.services[id]=offer end
            elseif category=='used' then entry.services[id]=nil end
        end
    end
    A.status.Trainer='Observed trainer services; filtered/collapsed rows may be absent'
end
function A.TrainerRows(out,map)
    for _,entry in pairs(A.db.trainers) do
        if A.IsProfessionTraining(entry) then entry.services={}
        elseif entry.map==map then
            for key,service in pairs(entry.services) do
                local learned=service.spell and A.SpellKnown(service.spell)
                local spellInfo=service.spell and C_Spell and A.Safe('localized trainer spell',C_Spell.GetSpellInfo,service.spell)
                local serviceName=(spellInfo and spellInfo.name) or service.name
                local trainerName=(entry.npcID and read('Npc',entry.npcID,'name')) or entry.name
                if A.IsProfessionTraining(entry,service) then entry.services[key]=nil
                elseif not learned then
                    local price=A.FormatMoney(service.cost)
                    A.Add(out,{key='train:'..key,spell=service.spell,cost=service.cost,professionID=service.professionID,profession=service.profession,title='Training: '..serviceName..(service.rank~='' and (' '..(service.rank or '')) or ''),
                        detail=trainerName..' | '..price..'\nAvailable at last visit; revisit to verify current status.',map=map,x=entry.x,y=entry.y,priority=25,verify=true})
                end
            end
        end
    end
end
