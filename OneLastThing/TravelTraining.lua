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
            for _,npc in ipairs(skill.trainers and skill.trainers[faction] or {}) do
                local t=data.trainers[npc];local zone=t and data.zones[t.zoneID]
                if name and zone and zone.uiMapID==map then
                    local cost=skill.cost or 0
                    A.Add(out,{key='train:spell:'..id,spell=id,weapon=true,
                        title='Weapon skill: '..name,
                        detail=((t.names or {})[locale] or (t.names or {}).enUS or 'Weapon master')..' | '..(A.FormatMoney(cost)),
                        map=map,x=t.x,y=t.y,priority=24})
                end
            end
        end
    end
    A.status.Weapons='TrainerSpells weapon data connected; learned/class/level/faction filtered'
end
function A.ObserveFlights()
    if not (C_TaxiMap and C_TaxiMap.GetAllTaxiNodes) then return end
    local nodes=A.Safe('open flight map nodes',C_TaxiMap.GetAllTaxiNodes,A.Map()) or {}
    local enum=Enum and Enum.FlightPathState
    local current=enum and enum.Current or 0
    local reachable=enum and enum.Reachable or 1
    for _,node in ipairs(nodes) do
        if node.nodeID and (node.state==current or node.state==reachable) then A.db.flightKnown[node.nodeID]=true end
    end
end
function A.FlightRows(out,map)
    if not (C_TaxiMap and C_TaxiMap.GetTaxiNodesForMap) then A.status.Flights='Client flight-path map API unavailable';return end
    local nodes=A.Safe('local flight nodes',C_TaxiMap.GetTaxiNodesForMap,map)
    if type(nodes)~='table' then if A.CheckUnavailable then A.CheckUnavailable('Flight-path data unavailable') end;return end
    local side=UnitFactionGroup('player')=='Horde' and 1 or 2
    for _,node in ipairs(nodes) do
        if node.nodeID and node.position and (node.faction==nil or node.faction==0 or node.faction==side) then
            local undiscovered=node.isUndiscovered
            if undiscovered==false then A.db.flightKnown[node.nodeID]=true
            elseif undiscovered==true then A.db.flightKnown[node.nodeID]=nil end
            if undiscovered==true or not A.db.flightKnown[node.nodeID] then
                local x,y=node.position:GetXY()
                A.Add(out,{key='flight:'..node.nodeID,flight=true,flightID=node.nodeID,
                    title=(undiscovered==true and 'Learn flight path: ' or 'Check flight path: ')..(node.name or 'Flight master'),
                    detail=undiscovered==true and 'The game marks this flight path undiscovered. Speak to its flight master.'
                        or 'Learned status is not reported. Open the flight map once to confirm.',
                    map=map,x=x*100,y=y*100,priority=6,verify=undiscovered~=true})
            end
        end
    end
    A.status.Flights='Client flight nodes connected; learned paths hidden'
end
