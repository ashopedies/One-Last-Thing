local _,A=...
local function finite(n) return type(n)=='number' and n==n and n~=math.huge and n~=-math.huge end
local function number(v,default,lo,hi)
    v=tonumber(v);if not finite(v) then return default end
    return math.max(lo,math.min(hi,v))
end
local function ensure(t,key) if type(t[key])~='table' then t[key]={} end;return t[key] end
local function stringMap(t,kind)
    for k,v in pairs(t) do if type(k)~='string' or (kind and type(v)~=kind) then t[k]=nil end end
end
local function locations(t)
    for k,v in pairs(t) do
        if type(v)~='table' or not finite(v.map) or type(v.name)~='string' or not finite(v.x) or not finite(v.y) or v.x<0 or v.x>100 or v.y<0 or v.y>100 then t[k]=nil end
    end
end
function A.ValidateSavedData()
    if type(OneLastThingDB)~='table' then OneLastThingDB={} end
    local d=OneLastThingDB
    -- Retired global override: existing category/item choices and targets remain authoritative.
    d.reagentEconomy=nil
    for _,key in ipairs({'sources','filters','filterExpanded','settingsSections','dismissed','snoozed','trash','supplies','vendors','trainers','flightKnown','supplyPrices','repairVendors','supplyOverrides','retiredClassSupplies','petFoodByDiet','vendorPoisons'}) do ensure(d,key) end
    -- Older caches also trusted unreliable map flags. Reconfirm only this cache;
    -- character preferences, ignored reminders and supply targets are preserved.
    if d.flightKnowledgeVersion~=2 then d.flightKnown={};d.flightKnowledgeVersion=2 end
    for _,key in ipairs({'sources','filters','filterExpanded','settingsSections','dismissed'}) do stringMap(d[key],'boolean') end
    for k,v in pairs(d.snoozed) do if type(k)~='string' or not finite(v) then d.snoozed[k]=nil end end
    for k,v in pairs(d.trash) do
        if type(k)~='string' or (v~=true and type(v)~='table') then d.trash[k]=nil
        elseif type(v)=='table' then
            local valid=true
            for field,value in pairs(v) do
                local numeric=field=='quest' or field=='spell' or field=='professionID' or field=='map' or field=='x' or field=='y' or field=='cost' or field=='rank' or field=='capMax' or field=='buyItem' or field=='questLevel' or field=='hiddenAt'
                if type(field)~='string' or (numeric and not finite(value)) or (not numeric and type(value)~='string' and type(value)~='boolean') then valid=false end
            end
            if not valid then d.trash[k]=nil end
        end
    end
    for _,key in ipairs({'supplies','retiredClassSupplies'}) do
        for id,rule in pairs(d[key]) do
            if not finite(id) or id<1 or id%1~=0 or type(rule)~='table' or not finite(tonumber(rule.target)) then d[key][id]=nil
            else rule.target=math.floor(number(rule.target,3,1,10000));rule.minLevel=math.floor(number(rule.minLevel,1,1,100));rule.classDefault=rule.classDefault==true;rule.classUtility=rule.classUtility==true end
        end
    end
    for id,byMap in pairs(d.vendors) do
        if not finite(id) or type(byMap)~='table' then d.vendors[id]=nil
        else for map,v in pairs(byMap) do
            if not finite(map) or type(v)~='table' or type(v.name)~='string' or not finite(v.x) or not finite(v.y) or v.x<0 or v.x>100 or v.y<0 or v.y>100 then byMap[map]=nil end
        end end
    end
    for id,p in pairs(d.supplyPrices) do if not finite(id) or type(p)~='table' or not finite(p.price) or p.price<0 or not finite(p.bundle) or p.bundle<1 then d.supplyPrices[id]=nil end end
    locations(d.repairVendors)
    for key,t in pairs(d.trainers) do
        if type(key)~='string' or type(t)~='table' or not finite(t.map) or type(t.name)~='string' or type(t.services)~='table' then d.trainers[key]=nil
        else
            if not finite(t.x) or not finite(t.y) then t.x=nil;t.y=nil end
            for id,s in pairs(t.services) do
                if type(id)~='string' or type(s)~='table' or type(s.name)~='string' or not finite(s.cost) or (s.spell~=nil and not finite(s.spell)) or (s.rank~=nil and type(s.rank)~='string') or (s.professionID~=nil and not finite(s.professionID)) or (s.profession~=nil and type(s.profession)~='string') then t.services[id]=nil end
            end
        end
    end
    for _,key in ipairs({'flightKnown','supplyOverrides'}) do for id,v in pairs(d[key]) do if not finite(id) or type(v)~='boolean' then d[key][id]=nil end end end
    for key,id in pairs(d.petFoodByDiet) do if type(key)~='string' or (id~=false and not finite(id)) then d.petFoodByDiet[key]=nil end end
    for key,id in pairs(d.vendorPoisons) do if type(key)~='string' or not finite(id) then d.vendorPoisons[key]=nil end end
    for key,spec in pairs({scale={1,.65,1.5},opacity={0,0,1},nearbyRadius={850,250,2000},completionDelay={10,5,60},fontScale={1,.8,1.3},repairThreshold={40,10,90},bagSlots={4,0,20}}) do d[key]=number(d[key],unpack(spec)) end
    for _,key in ipairs({'showCapWarnings','auto','arrival','travel','showEmpty','collapsed','attuneAllChains','nearbyOnly','importantVendorBuys','categoryMigration','trashMigration','supplyControlsV2'}) do if d[key]~=nil and type(d[key])~='boolean' then d[key]=nil end end
    for _,key in ipairs({'theme','headerPosition','fontFace','fontShadow','fontOutline','rowMode','collapseMode'}) do if d[key]~=nil and type(d[key])~='string' then d[key]=nil end end
    local size=ensure(d,'size');size.width=number(size.width,440,360,950);size.height=number(size.height,320,230,850)
    local anchors={CENTER=true,TOP=true,BOTTOM=true,LEFT=true,RIGHT=true,TOPLEFT=true,TOPRIGHT=true,BOTTOMLEFT=true,BOTTOMRIGHT=true}
    local p=d.position
    if p~=nil and (type(p)~='table' or not anchors[p.point] or not anchors[p.relativePoint] or not finite(p.x) or not finite(p.y)) then d.position=nil end
    if type(d.compactSize)~='table' or not finite(d.compactSize.width) or not finite(d.compactSize.height) then d.compactSize=nil end
    if type(d.pin)~='table' or type(d.pin.key)~='string' or not finite(d.pin.map) or not finite(d.pin.x) or not finite(d.pin.y) then d.pin=nil end
    if d.pin then
        local numeric={map=true,x=true,y=true,quest=true,spell=true,buyItem=true,flightID=true,professionID=true,capMax=true,skill=true,buyTarget=true,ammoItem=true,supply=true,target=true}
        for key,value in pairs(d.pin) do
            if numeric[key] and not finite(value) then d.pin=nil;break end
            if (key=='key' or key=='hyperlink' or key=='ammoKind') and type(value)~='string' then d.pin=nil;break end
        end
    end
    if d.headerPosition~='top' and d.headerPosition~='bottom' then d.headerPosition='top' end
    if d.fontShadow~='none' and d.fontShadow~='soft' and d.fontShadow~='strong' then d.fontShadow='soft' end
    if d.fontOutline~='none' and d.fontOutline~='thin' and d.fontOutline~='thick' then d.fontOutline='none' end
    local ammo=ensure(d,'hunterAmmo');ammo.target=math.floor(number(ammo.target,400,1,100000));ensure(ammo,'last')
    for k,id in pairs(ammo.last) do if (k~='arrow' and k~='bullet') or not finite(id) then ammo.last[k]=nil end end
    if ammo.enabled~=nil and type(ammo.enabled)~='boolean' then ammo.enabled=nil end
end
