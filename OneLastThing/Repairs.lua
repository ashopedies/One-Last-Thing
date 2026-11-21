local _,A=...
local capitals={[1637]=1454,[1497]=1458,[1638]=1456,[1519]=1453,[1537]=1455,[1657]=1457}
local function module(name)
    return QuestieLoader and A.Safe('repair '..name,QuestieLoader.ImportModule,QuestieLoader,name)
end
function A.EquipmentDurability()
    local lowest
    for slot=1,19 do
        local current,maximum=A.Safe('equipment durability',GetInventoryItemDurability,slot)
        if type(current)=='number' and type(maximum)=='number' and maximum>0 then
            local ratio=current/maximum
            lowest=lowest and math.min(lowest,ratio) or ratio
        end
    end
    return lowest
end
local function read(id,key)
    return LibQuestieDB and LibQuestieDB.Npc and A.Safe('repair NPC '..key,LibQuestieDB.Npc.Get,id,key)
end
local function buildIndex()
    local lib=LibQuestieDB
    if not (lib and lib.Npc and lib.Npc.GetAllIds) then return end
    if A.repairIndexSource==lib then return end
    local mask=lib.Enum and lib.Enum.npcFlags and lib.Enum.npcFlags.REPAIR
    local band=(bit and bit.band) or (bit32 and bit32.band)
    if not mask or not band then return end
    local ids=A.Safe('repair NPC IDs',lib.Npc.GetAllIds)
    if type(ids)~='table' then return end
    A.repairIndexSource=lib;A.repairIndex={}
    local index=1
    local function batch()
        if A.repairIndexSource~=lib then return end
        local last=math.min(#ids,index+249)
        for i=index,last do
            local flags=read(ids[i],'npcFlags')
            if type(flags)=='number' and band(flags,mask)==mask then A.repairIndex[#A.repairIndex+1]=ids[i] end
        end
        index=last+1
        if index<=#ids then C_Timer.After(.05,batch)
        else A.Refresh('Repair vendors ready',true) end
    end
    C_Timer.After(0,batch)
end
function A.FindRepairVendor(map)
    local candidates={}
    local live=A.liveRepairVendor
    if live and live.map==map and A.Nearby(map,live.x,live.y) then return live end
    local function add(v)
        if v.map==map and v.x and v.y and A.Nearby(v.map,v.x,v.y) then candidates[#candidates+1]=v end
    end
    for _,v in pairs(A.db.repairVendors or {}) do add(v) end
    local town=module('Townsfolk')
    local ids=town and town.townsfolk and town.townsfolk.Repair
    if not ids then buildIndex();ids=A.repairIndex or {} end
    local side=UnitFactionGroup('player')=='Horde' and 'H' or 'A'
    local zones=module('ZoneDB')
    for _,id in ipairs(ids) do
        local friendly=read(id,'friendlyToFaction')
        local name=read(id,'name')
        if type(friendly)=='string' and friendly:find(side,1,true) and name and name:sub(1,5)~='[DND]' then
            for area,points in pairs(read(id,'spawns') or {}) do
                local m=capitals[area] or (zones and A.Safe('repair area map',zones.GetUiMapIdByAreaId,zones,area))
                if m==map then
                    for _,p in ipairs(points) do add({map=m,x=p[1],y=p[2],name=name,npc=id}) end
                end
            end
        end
    end
    local scope=A.scope or {};local x,y=scope.x or .5,scope.y or .5
    table.sort(candidates,function(a,b)
        local da=(a.x/100-x)^2+(a.y/100-y)^2
        local db=(b.x/100-x)^2+(b.y/100-y)^2
        if da==db then return a.name<b.name end
        return da<db
    end)
    return candidates[1]
end
function A.ObserveRepairMerchant()
    A.liveRepairCost=nil;A.liveRepairVendor=nil
    if A.Safe('repair available',CanMerchantRepair)~=true then return end
    local map=A.Map()
    local pos=map and C_Map.GetPlayerMapPosition and C_Map.GetPlayerMapPosition(map,'player')
    local x,y;if pos then x,y=pos:GetXY() end
    if map and x and y then
        local name=UnitName('npc') or 'Repair vendor'
        local key=tostring(map)..':'..name
        A.db.repairVendors[key]={name=name,map=map,x=x*100,y=y*100}
        A.liveRepairVendor=A.db.repairVendors[key]
    end
    local price,needed=A.Safe('repair cost',GetRepairAllCost)
    if needed and type(price)=='number' then A.liveRepairCost=price end
end
function A.RepairRows(out,map)
    if not A.CategoryEnabled('errands','repairs') then return end
    local lowest=A.EquipmentDurability()
    if not lowest or lowest*100>=(A.db.repairThreshold or 40) then return end
    local vendor=A.FindRepairVendor(map)
    if not vendor then A.status.Repairs='Low durability; no known nearby repair vendor'
        if A.CheckUnavailable and not (LibQuestieDB and LibQuestieDB.Npc) and not next(A.db.repairVendors) then A.CheckUnavailable('Repair-vendor data unavailable') end
        return end
    local detail=vendor.name
    if A.liveRepairCost then detail=detail..' | '..A.FormatMoney(A.liveRepairCost)..' to repair all'
    else detail=detail..' | Cost shown at the repair vendor' end
    A.Add(out,{key='repair:equipment',repair=true,title='Repair gear: lowest item '..math.floor(lowest*100+.5)..'%',
        detail=detail..'\nEquipped gear below '..(A.db.repairThreshold or 40)..'% durability. Repair manually at the vendor.',
        locationSource=vendor.npc and 'QuestieDB' or 'Your vendor observations',cost=A.liveRepairCost,priceConfidence=A.liveRepairCost and 'observed' or 'unknown',map=vendor.map,x=vendor.x,y=vendor.y,priority=7,brokenGear=lowest==0})
    A.status.Repairs='Nearby repair vendor found'
end
