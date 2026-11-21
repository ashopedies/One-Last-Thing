local _,A=...
-- Optional, read-only adapter for Exehn's installed DungeonJournal namespace.
-- No journal database/assets are bundled and its display preferences are untouched.
function A.DungeonJournalData()
    local d=ForeverDungeonJournal_NS
    if type(d)=='table' and type(d.DB)=='table' and type(d.QUEST_PREREQ_CHAINS)=='table'
        and type(d.QUEST_PREREQ_DETAILS)=='table' then return d end
end
local professionIDs={ALCHEMY=171,BLACKSMITHING=164,COOKING=185,ENCHANTING=333,ENGINEERING=202,
    FIRSTAID=129,FISHING=356,HERBALISM=182,LEATHERWORKING=165,MINING=186,SKINNING=393,TAILORING=197}
local function factionAndClass(q,side,class,professions)
    if q.faction and q.faction~='Both' and q.faction~='Neutral' and q.faction~=side then return false end
    if q.classOnly then
        local matches=false
        if type(q.classOnly)=='table' then
            for _,c in ipairs(q.classOnly) do if c==class then matches=true end end
        else matches=q.classOnly==class end
        if not matches then return false end
    end
    if q.profession and not professions[professionIDs[tostring(q.profession):upper():gsub('[%s_]','')]] then return false end
    return true
end
local function gray(id,q)
    local value=A.IsGrayQuest(id)
    if value~=nil then return value end
    local range=A.Safe('dungeon quest trivial range',C_QuestLog and C_QuestLog.GetTrivialRange or GetQuestGreenRange)
    local level=tonumber(q.level)
    if type(range)=='number' and level and level>0 then return level<UnitLevel('player')-range end
end
local function title(id,q)
    local name=C_QuestLog and A.Safe('dungeon quest title',C_QuestLog.GetTitleForQuestID,id)
    if not name and C_QuestLog and C_QuestLog.RequestLoadQuestByID then
        A.questRequests=A.questRequests or {}
        if not A.questRequests[id] then A.questRequests[id]=true;A.Safe('load dungeon quest title',C_QuestLog.RequestLoadQuestByID,id) end
    end
    return name or q.name or ('Quest '..id)
end
local function location(id,q,d,map)
    local m,x,y,npc,known,points,source=A.QuestLocation(id,false,map)
    if m or known then return m,x,y,npc,known,points,source end
    local point=q.startMap or (d.QUEST_START_MAPS and d.QUEST_START_MAPS[id]) or q.map
    if type(point)=='table' and point.mapID==map and type(point.x)=='number' and type(point.y)=='number'
        and point.x>=0 and point.x<=1 and point.y>=0 and point.y<=1 then
        return map,point.x*100,point.y*100,point.targetName or point.label,false,nil,'DungeonJournal'
    end
end
function A.DungeonJournalRows(out,map)
    local d=A.DungeonJournalData()
    if not d then if A.CheckUnavailable then A.CheckUnavailable('DungeonJournal data unavailable or unsupported') end;return end
    local side=UnitFactionGroup('player');local _,class=UnitClass('player');local level=UnitLevel('player')
    local professions={}
    for _,p in ipairs(A.ProfessionPlans() or {}) do professions[p.skillLineID]=true end
    local count=0
    for dungeonName,dungeon in pairs(d.DB) do
        for _,q in ipairs(type(dungeon)=='table' and dungeon.quests or {}) do
            local finalID=type(q)=='table' and tonumber(q.id)
            if finalID and not q.hubPlaceholder and not q.repeatable and factionAndClass(q,side,class,professions)
                and not A.QuestDone(finalID) and not A.QuestActive(finalID)
                and (not tonumber(q.requires) or tonumber(q.requires)<=level) and gray(finalID,q)~=true then
                local candidate=q;local id=finalID;local blocked=false
                local chain=not (d.QUEST_GUIDE_CHAINS and d.QUEST_GUIDE_CHAINS[finalID]) and d.QUEST_PREREQ_CHAINS[finalID]
                if type(chain)=='table' then
                    -- Later progress proves earlier prerequisites obsolete even if native
                    -- history lacks an old breadcrumb. Never skip an active unfinished step.
                    local progress=0
                    for i,step in ipairs(chain) do
                        if type(step)=='table' and step.id and (A.QuestDone(step.id) or A.QuestActive(step.id)) then progress=i end
                    end
                    if progress>0 and A.QuestActive(chain[progress].id) and not A.QuestDone(chain[progress].id) then blocked=true end
                    for i=progress+1,#chain do
                        local step=chain[i]
                        if type(step)~='table' or not tonumber(step.id) then blocked=true;break end
                        if step.id~=finalID and not A.QuestDone(step.id) then
                            id=tonumber(step.id)
                            local details=id and d.QUEST_PREREQ_DETAILS[id]
                            candidate={};for k,v in pairs(type(details)=='table' and details or {}) do candidate[k]=v end
                            candidate.name=candidate.name or step.name
                            candidate.requires=candidate.requires or step.requires
                            candidate.level=candidate.level or step.level
                            candidate.itemStep=step.itemStep or candidate.itemStep
                            break
                        end
                    end
                end
                if not blocked and id and not candidate.itemStep and not candidate.startItem and not candidate.hubPlaceholder
                    and not candidate.repeatable and not A.QuestDone(id) and not A.QuestActive(id)
                    and factionAndClass(candidate,side,class,professions)
                    and (not tonumber(candidate.requires) or tonumber(candidate.requires)<=level) then
                    local m,x,y,npc,verified,destinations,locationSource=location(id,candidate,d,map)
                    if m and x and y then
                        local available=A.QuestEligible and A.QuestEligible(id)
                        if available==nil then
                            if A.CheckUnavailable then A.CheckUnavailable('Quest eligibility/location data incomplete') end
                        elseif available then
                            local isGray=gray(id,candidate)
                            local important=isGray and id~=finalID and gray(finalID,q)==false
                            if not isGray or important then
                                local name=title(id,candidate)
                                A.Add(out,{key='quest:'..id..':start',quest=id,title='Pick up: '..name,
                                    detail=(npc or candidate.pickup or 'Quest giver')..' | '..dungeonName..'\nDungeonJournal',
                                    locationSource=locationSource,destinations=destinations,destinationName=candidate.pickup or 'Quest giver',destinationSuffix=' | '..dungeonName..'\nDungeonJournal',
                                    map=m,x=x,y=y,questLevel=tonumber(candidate.level),dungeonJournal=true,dungeonPickup=true,verify=not verified,
                                    gray=isGray,importantReason=important and ('Grey prerequisite — leads to level '..tostring(q.level or '?')..' '..title(finalID,q)) or nil,
                                    why='Pick up before entering the dungeon: '..dungeonName,priority=20})
                                count=count+1
                            end
                        end
                    end
                end
            end
        end
    end
    A.status.DungeonJournal=tostring(count)..' local dungeon pickup candidates'
end
