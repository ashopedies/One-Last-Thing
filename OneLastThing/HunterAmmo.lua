local _,A=...
-- No upgrade ladder: the IDs below only identify ordinary vendor ammo types.
local excluded={[19082]=true,[2514]=true,[3029]=true,[3031]=true}
local ordinary={
 [2512]='arrow',[2515]='arrow',[3030]='arrow',[11285]='arrow',
 [2516]='bullet',[2519]='bullet',[3033]='bullet',[11284]='bullet',
}
function A.IsHunter()
    local _,class=UnitClass('player');return class=='HUNTER'
end
local function state()
    A.db.hunterAmmo=A.db.hunterAmmo or {target=400,last={}}
    local s=A.db.hunterAmmo;s.target=s.target or 400;s.last=s.last or {}
    return s
end
local function itemInfo(id)
    if not id then return end
    local fn=(C_Item and C_Item.GetItemInfoInstant) or GetItemInfoInstant
    if not fn then return end
    local ok,_,_,_,_,_,class,subclass=pcall(fn,id)
    if ok then return class,subclass end
end
local function ammoKind(id)
    if ordinary[id] then return ordinary[id] end
    local class,subclass=itemInfo(id)
    local projectile=Enum and Enum.ItemClass and Enum.ItemClass.Projectile or 6
    local kinds=Enum and Enum.ItemProjectileSubclass or {}
    if class==projectile then
        if subclass==(kinds.Arrow or 2) then return 'arrow' end
        if subclass==(kinds.Bullet or 3) then return 'bullet' end
    end
end
local function slot(name,fallback)
    return (GetInventorySlotInfo and A.Safe('ammo slot '..name,GetInventorySlotInfo,name)) or fallback
end
function A.HunterWeaponKind()
    if not A.IsHunter() then return end
    local id=A.Safe('ranged weapon',GetInventoryItemID,'player',slot('RangedSlot',INVSLOT_RANGED or 18))
    local class,subclass=itemInfo(id)
    local weapon=Enum and Enum.ItemClass and Enum.ItemClass.Weapon or 2
    local kinds=Enum and Enum.ItemWeaponSubclass or {}
    if class~=weapon then return end
    if subclass==(kinds.Bows or 2) or subclass==(kinds.Crossbow or 18) then return 'arrow' end
    if subclass==(kinds.Guns or 3) then return 'bullet' end
end
local function vendorAmmo(id)
    if excluded[id] then return false end
    if ordinary[id] then return true end
    if A.db.vendors[id] and next(A.db.vendors[id]) then return true end
    local lib=LibQuestieDB
    local vendors=lib and lib.Item and A.Safe('ammo vendors',lib.Item.Get,id,'vendors')
    -- Non-standard ammo is eligible only with a real vendor relation, not a drop/craft source.
    return type(vendors)=='table' and next(vendors)~=nil
end
function A.HunterAmmoSelection()
    if not A.IsHunter() then return end
    local s=state();local kind=A.HunterWeaponKind()
    if not kind then return end
    local equipped=A.Safe('equipped ammo',GetInventoryItemID,'player',slot('AmmoSlot',INVSLOT_AMMO or 0))
    if ammoKind(equipped)==kind then
        -- Remember equipped ammo even when not sold: never silently replace a
        -- player's crafted/drop selection with a different tier.
        s.last[kind]=equipped
        return equipped,kind,vendorAmmo(equipped)
    end
    local last=s.last[kind]
    if last then return last,kind,vendorAmmo(last) end
    -- No history: choose the first matching vendor ammo in bag order, not the
    -- highest DPS/most expensive type. Keep that choice until the player equips another.
    if C_Container and C_Container.GetContainerNumSlots and C_Container.GetContainerItemID then
        for bag=0,(NUM_TOTAL_EQUIPPED_BAG_SLOTS or NUM_BAG_SLOTS or 4) do
            for index=1,(A.Safe('ammo bag size',C_Container.GetContainerNumSlots,bag) or 0) do
                local id=A.Safe('ammo bag item',C_Container.GetContainerItemID,bag,index)
                if ammoKind(id)==kind and vendorAmmo(id) then s.last[kind]=id;return id,kind,true end
            end
        end
    end
    return nil,kind
end
function A.HunterAmmoStatus()
    local id,kind,vendor=A.HunterAmmoSelection()
    if not kind then return 'No bow, crossbow or gun equipped' end
    if not id then return 'No ammo selected yet' end
    if A.db.supplies[id] then return 'Managed in Custom supplies' end
    if not vendor then return 'Selected ammo has no known vendor' end
    return A.ItemName(id)..': '..A.ItemCount(id)..' in bags'
end
function A.HunterAmmoTarget()
    return state().target
end
function A.SetHunterAmmoTarget(target)
    if not A.IsHunter() or type(target)~='number' or target<1 or target>100000 then return false end
    state().target=math.floor(target)
    A.EnableHunterAmmo(true);return true
end
function A.EnableHunterAmmo(enabled)
    state().enabled=enabled
    if enabled then
        A.db.filters.supplies=true;A.db.filters['supplies/ammo']=true
        A.db.sources.HunterAmmoRows=nil
        for _,kind in ipairs({'arrow','bullet'}) do
            local key='ammo:'..kind;A.db.dismissed[key]=nil;A.db.snoozed[key]=nil;A.db.trash[key]=nil
        end
    end
    A.Refresh('Updated',false)
end
function A.HunterAmmoEnabled()
    return state().enabled~=false and A.CategoryEnabled('supplies','ammo')
end
function A.HunterAmmoRows(out,map,travel)
    if not A.IsHunter() then return end
    local id,kind,vendor=A.HunterAmmoSelection()
    if not id or not vendor or not A.HunterAmmoEnabled() or A.db.supplies[id] then return end
    A.AddSupplyReminder(out,id,{target=state().target,minLevel=1},map,travel,
        {key='ammo:'..kind,ammoItem=id,ammoKind=kind,subcategory='ammo'})
end
