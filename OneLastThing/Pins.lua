local _,A=...
function A.ReadWaypoint()
    local p=C_Map and A.Safe('read task waypoint',C_Map.GetUserWaypoint)
    if not p then return nil,C_Map and type(C_Map.GetUserWaypoint)=='function' end
    local pos=p.position
    local x,y
    if pos and type(pos.GetXY)=='function' then x,y=pos:GetXY()
    elseif pos then x,y=pos.x,pos.y end
    if type(p.uiMapID)~='number' or type(x)~='number' or type(y)~='number' then return end
    return {map=p.uiMapID,x=x,y=y}
end
local function link()
    return C_Map and A.Safe('read task waypoint link',C_Map.GetUserWaypointHyperlink)
end
function A.TrackWaypoint(row,map,x,y)
    local p=A.ReadWaypoint() or (map and {map=map,x=x,y=y})
    if not p then return end
    p.hyperlink=link()
    p.key=row.key
    for _,key in ipairs({'quest','finish','spell','buyItem','flightID','professionID','criticalBook','capMax','skill','buyTarget','repair','professionRank','ammoItem','ammoKind'}) do p[key]=row[key] end
    p.supply=tonumber((row.key or ''):match('^supply:(%d+)'))
    if p.supply and A.db.supplies[p.supply] then p.target=A.db.supplies[p.supply].target end
    A.db.pin=p
end
local function same(a,b)
    return a and b and a.map==b.map and math.abs(a.x-b.x)<.00001 and math.abs(a.y-b.y)<.00001
end
local function finished(p)
    if A.db.trash[A.TrashKey(p)] or A.db.dismissed[p.key] or (A.db.snoozed[p.key] or 0)>time() then return true end
    if p.repair then
        local durability=A.EquipmentDurability()
        if not A.CategoryEnabled('errands','repairs') or (durability and durability*100>=(A.db.repairThreshold or 40)) then return true end
    end
    if p.ammoItem then
        local selected,kind=A.HunterAmmoSelection()
        if not A.HunterAmmoEnabled() or selected~=p.ammoItem or kind~=p.ammoKind or A.ItemCount(p.ammoItem)>=A.HunterAmmoTarget() then return true end
    end
    if p.quest then
        if A.QuestDone(p.quest) then return true end
        if not p.finish and A.QuestActive(p.quest) then return true end
    end
    if p.spell then
        if A.SpellKnown(p.spell) then return true end
        local info=C_TradeSkillUI and A.Safe('pinned recipe learned',C_TradeSkillUI.GetRecipeInfo,p.spell)
        if info and info.learned then return true end
    end
    if (p.key or ''):match('^buyrecipe:') or (p.skill and not p.professionRank) then return true end -- removed route-dependent reminder
    if (p.key or ''):match('^note:') then return true end -- retire an owned pin from the removed feature
    if p.criticalBook and p.buyItem and A.CriticalBookOwned and A.CriticalBookOwned(p.buyItem) then return true end
    if p.buyItem and A.ItemCount(p.buyItem)>=(p.buyTarget or 1) then return true end
    if p.flightID and A.db.flightKnown[p.flightID] then return true end
    if p.professionID and p.capMax then
        local api=SkillUpForever and SkillUpForever.API
        for _,profession in ipairs((api and A.Safe('pinned profession cap',api.Professions)) or {}) do
            local cap=profession.maxRank or 0
            if profession.skillLineID==p.professionID and ((p.criticalBook and cap>=p.capMax) or (not p.criticalBook and cap>p.capMax)) then return true end
        end
    end
    if p.supply and (not A.db.supplies[p.supply] or A.ItemCount(p.supply)>=A.db.supplies[p.supply].target) then return true end
    if p.supply and (not A.CategoryEnabled('supplies',tostring(p.supply)) or not A.SupplyRelevant(p.supply,A.db.supplies[p.supply])) then return true end
    return false
end
function A.CleanupPin()
    local p=A.db and A.db.pin
    if not p then return end
    if not C_Map then return end
    local live,removed=A.ReadWaypoint()
    local liveLink=link()
    local owned=same(p,live) or (p.hyperlink and liveLink==p.hyperlink)
    if not owned then
        -- Drop ownership only when a replacement or removal is observable.
        if live or liveLink or removed then A.db.pin=nil end
        return
    end
    if finished(p) and C_Map.ClearUserWaypoint then
        local ok,err=pcall(C_Map.ClearUserWaypoint)
        if not ok then A.errors['clear completed task waypoint']=tostring(err);return end
        A.errors['clear completed task waypoint']=nil
        -- Keep ownership on a failed/no-op clear so a later event retries.
        local remaining=A.ReadWaypoint()
        if same(p,remaining) or (p.hyperlink and link()==p.hyperlink) then return end
        if C_SuperTrack and C_SuperTrack.SetSuperTrackedUserWaypoint then
            A.Safe('untrack completed task waypoint',C_SuperTrack.SetSuperTrackedUserWaypoint,false)
        end
        A.db.pin=nil
    end
end
