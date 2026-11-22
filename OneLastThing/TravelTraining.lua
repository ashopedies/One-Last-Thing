local _,A=...
local function known(id)
    if A.SpellKnown(id) then return true end
    local bank=Enum and Enum.SpellBookSpellBank and Enum.SpellBookSpellBank.Player
    return bank and C_SpellBook and A.Safe('known weapon skill',C_SpellBook.IsSpellInSpellBook,id,bank,false)==true
end
function A.WeaponRows(out,map)
    local data=TrainerSpellsWeaponSkills
    if not (data and data.skills and data.trainers and data.zones) then A.status.Weapons='TrainerSpells weapon data unavailable';return end
    local _,class=UnitClass('player');local faction=UnitFactionGroup('player')
    local locale=GetLocale and GetLocale() or 'enUS'
    for id,skill in pairs(data.skills) do
        if skill.classes and skill.classes[class] and not known(id) and UnitLevel('player')>=(skill.level or 1) then
            local info=C_Spell and A.Safe('weapon skill name',C_Spell.GetSpellInfo,id)
            local name=info and info.name or A.Safe('weapon skill legacy name',GetSpellInfo,id)
            local destinations={}
            for _,npc in ipairs(skill.trainers and skill.trainers[faction] or {}) do
                local t=data.trainers[npc];local zone=t and data.zones[t.zoneID]
                if name and zone and zone.uiMapID==map then
                    destinations[#destinations+1]={map=map,x=t.x,y=t.y,locationSource='TrainerSpells',name=(t.names or {})[locale] or (t.names or {}).enUS or 'Weapon master'}
                end
            end
            local target=A.SelectDestination(destinations,map)
            if target then
                local cost=tonumber(skill.cost)
                local suffix=' | '..A.FormatMoney(cost)
                A.Add(out,{key='train:spell:'..id,spell=id,weapon=true,title='Weapon skill: '..name,
                    detail=target.name..suffix,cost=cost,locationSource='TrainerSpells',priceConfidence=cost and 'catalogue' or 'unknown',destinations=destinations,destinationSuffix=suffix,
                    map=map,x=target.x,y=target.y,priority=24})
            end
        end
    end
    A.status.Weapons='TrainerSpells weapon data connected; learned/class/level/faction filtered'
end
local function flightMapNodes(map)
    local seen,trace={},{}
    local continentType=Enum and Enum.UIMapType and Enum.UIMapType.Continent or 2
    local childNodes
    while map and map~=0 and not seen[map] do
        seen[map]=true
        local info=A.Safe('flight map parent',C_Map and C_Map.GetMapInfo,map)
        local shown=A.Safe('flight map coverage',C_TaxiMap.ShouldMapShowTaxiNodes,map)
        -- ShouldMapShowTaxiNodes controls map rendering, not data availability.
        -- Forever can return a continent's nodes for a zone where it is false.
        local nodes=A.Safe('local flight nodes',C_TaxiMap.GetTaxiNodesForMap,map)
        trace[#trace+1]=tostring(map)..':'..(type(nodes)=='table' and #nodes or '?')..'/'..tostring(shown)
        if type(nodes)=='table' and next(nodes) then
            if shown~=false or (info and info.mapType==continentType) then return map,nodes,table.concat(trace,', ') end
            childNodes=nodes
        end
        if info and info.mapType==continentType and childNodes then return map,childNodes,table.concat(trace,', ') end
        map=info and info.parentMapID
    end
    return nil,nil,table.concat(trace,', ')
end
local function projector(map,source)
    if map==source then return function(x,y) return x,y end end
    if C_Map and C_Map.GetMapRectOnMap then
        -- Safe forwards three results, so wrap the four map bounds in a table.
        local r=A.Safe('flight map bounds',function() return {C_Map.GetMapRectOnMap(map,source)} end)
        if r and type(r[1])=='number' and type(r[2])=='number' and type(r[3])=='number'
            and type(r[4])=='number' and r[2]>r[1] and r[4]>r[3] then
            return function(x,y) return (x-r[1])/(r[2]-r[1]),(y-r[3])/(r[4]-r[3]) end
        end
    end
    if C_Map and C_Map.GetWorldPosFromMapPos and C_Map.GetMapPosFromWorldPos and CreateVector2D then
        return function(x,y)
            local continent,world=A.Safe('flight world position',C_Map.GetWorldPosFromMapPos,source,CreateVector2D(x,y))
            if not continent or not world then return end
            local target,point=A.Safe('flight local position',C_Map.GetMapPosFromWorldPos,continent,world,map)
            if target==map and point then return point:GetXY() end
        end
    end
end
-- The client can expose retired development records alongside real routes.
-- Match the explicit technical prefix, never ordinary names such as Old Town.
function A.FlightNodeRelevant(node)
    if type(node)~='table' or not node.nodeID then return false end
    A.obsoleteFlightNodes=A.obsoleteFlightNodes or {}
    if type(node.name)=='string' and node.name:lower():match('^%s*zzold') then
        A.obsoleteFlightNodes[node.nodeID]=true
        return false
    end
    if type(node.name)=='string' and node.name~='' then A.obsoleteFlightNodes[node.nodeID]=nil end
    return not A.obsoleteFlightNodes[node.nodeID]
end
function A.ObserveFlights()
    if not (C_TaxiMap and C_TaxiMap.GetAllTaxiNodes) then return end
    local map=A.Safe('open flight map ID',GetTaxiMapID)
    if type(map)~='number' or map<=0 then map=flightMapNodes(A.Map()) end
    local nodes=map and A.Safe('open flight map nodes',C_TaxiMap.GetAllTaxiNodes,map) or {}
    local enum=Enum and Enum.FlightPathState
    local current=enum and enum.Current or 0
    local reachable=enum and enum.Reachable or 1
    for _,node in ipairs(nodes or {}) do
        if A.FlightNodeRelevant(node) and (node.state==current or node.state==reachable) then A.db.flightKnown[node.nodeID]=true end
    end
end
function A.FlightRows(out,map)
    if not (C_TaxiMap and C_TaxiMap.GetTaxiNodesForMap) then A.status.Flights='Client flight-path map API unavailable';return end
    local source,nodes,trace=flightMapNodes(map)
    A.status.Flights='Flight maps (map:nodes/display): '..(trace or 'none')
    if not nodes then if A.CheckUnavailable then A.CheckUnavailable('Flight-path data unavailable') end;return end
    local project=projector(map,source)
    if not project then
        A.status.Flights=A.status.Flights..'; cannot project '..tostring(source)..' onto '..tostring(map)
        if A.CheckUnavailable then A.CheckUnavailable('Flight-path data unavailable') end
        return
    end
    local factions=Enum and Enum.FlightPathFaction
    local side=UnitFactionGroup('player')=='Horde' and (factions and factions.Horde or 1) or (factions and factions.Alliance or 2)
    for _,node in ipairs(nodes) do
        if A.FlightNodeRelevant(node) and node.position and (node.faction==nil or node.faction==0 or node.faction==side) then
            local undiscovered=node.isUndiscovered
            -- Forever's map flag can claim unvisited routes are learned. Only
            -- Current/Reachable observations at a flight master prove knowledge.
            if not A.db.flightKnown[node.nodeID] then
                local x,y=project(node.position:GetXY())
                if x and y and x>=0 and x<=1 and y>=0 and y<=1 then
                    A.Add(out,{key='flight:'..node.nodeID,locationSource='WoW taxi map',flight=true,flightID=node.nodeID,
                        title=(undiscovered==true and 'Learn flight path: ' or 'Check flight path: ')..(node.name or 'Flight master'),
                        detail=undiscovered==true and 'The game marks this flight path undiscovered. Speak to its flight master.'
                            or 'Learned status is not reported. Open the flight map once to confirm.',
                        map=map,x=x*100,y=y*100,priority=6,verify=undiscovered~=true})
                end
            end
        end
    end
    A.status.Flights='Client flight nodes connected; '..#nodes..' nodes on map '..tostring(source)..'; flight-master observations confirm learned paths'
end
