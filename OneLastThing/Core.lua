local _, A = ...
OneLastThing = A
A.version = '0.14.7'
A.name = 'One Last Thing'
A.status = {}
A.errors = {}
A.rows = {}
function A.Safe(label, fn, ...)
    if type(fn) ~= 'function' then return nil end
    local ok, a, b, c = pcall(fn, ...)
    if ok then A.errors[label]=nil;return a, b, c end
    if A.activeProvider then A.providerFailure=label..': '..tostring(a) end
    A.errors[label] = tostring(a)
    return nil
end
function A.Print(text) print(A.name..': '..tostring(A.Translate(text))) end
function A.Init()
    if A.ImportLegacySettings then A.ImportLegacySettings() end
    if A.ValidateSavedData then A.ValidateSavedData() end
    OneLastThingDB = OneLastThingDB or {}
    A.db = OneLastThingDB
    local d = A.db
    d.notes=nil
    -- Retire only custom-note choices; automatic reminders retain their state.
    for _,field in ipairs({'dismissed','snoozed','trash'}) do
        for key in pairs(d[field] or {}) do
            if type(key)=='string' and key:match('^note:') then d[field][key]=nil end
        end
    end
    d.sources = d.sources or {}
    if d.arrival == nil then d.arrival=true end
    if d.travel == nil then d.travel=true end
    if d.showEmpty == nil then d.showEmpty=true end
    d.scale = d.scale or 1
    if d.collapsed==nil then d.collapsed=false end
    d.rowMode=d.rowMode or (d.compactRows and 'compact' or 'default')
    if d.rowMode~='default' and d.rowMode~='compact' and d.rowMode~='minimal' then d.rowMode='default' end
    d.compactRows=nil
    if d.attuneAllChains==nil then d.attuneAllChains=true end
    if d.nearbyOnly==nil then d.nearbyOnly=true end
    d.nearbyRadius=d.nearbyRadius or 850
    if d.importantVendorBuys==nil then d.importantVendorBuys=true end
    d.filters = d.filters or {}
    -- Ordinary turn-ins duplicate quest trackers; explicit character choices win.
    if d.filters['quests/turnins']==nil then d.filters['quests/turnins']=false end
    d.settingsSections=d.settingsSections or {}
    d.filters['errands/notes']=nil
    d.sources.NoteRows=nil
    if d.opacity==nil then d.opacity=0 end
    d.borders=nil
    if d.showBorders==nil then d.showBorders=false end
    if d.locked==nil then d.locked=false end
    d.theme=d.theme or 'blizzard'
    d.headerPosition=d.headerPosition or 'top'
    d.completionDelay=d.completionDelay or 10
    d.fontFace=d.fontFace or 'arial'
    d.fontScale=d.fontScale or 1
    d.fontShadow=d.fontShadow or 'soft'
    d.fontOutline=d.fontOutline or 'none'
    d.size = d.size or {width=440,height=320}
    if not d.categoryMigration then
        local map={AttuneRows='quests',TurnInRows='quests',ProfessionRows='professions',SupplyRows='supplies',TrainerRows='training',BagRows='errands/bags'}
        for source,cat in pairs(map) do if d.sources[source]==false then d.filters[cat]=false end end
        d.sources={};d.categoryMigration=true
    end
    d.trash=d.trash or {}
    if not d.trashMigration then
        -- Old Dismiss was permanent. Preserve those intentional choices as Trash.
        for key,value in pairs(d.dismissed or {}) do
            if value then
                local quest=key:match('^quest:(%d+):')
                d.trash[quest and ('quest:'..quest) or key]=true
            end
        end
        d.trashMigration=true
    end
    d.dismissed={}
    d.trainers = d.trainers or {}
    d.flightKnown=d.flightKnown or {}
    d.snoozed = d.snoozed or {}
    d.vendors = d.vendors or {}
    d.supplies = d.supplies or {}
    d.supplyPrices=d.supplyPrices or {}
    d.repairVendors=d.repairVendors or {}
    d.repairThreshold=d.repairThreshold or 40
    d.seeded=true
    if A.SyncClassSupplies then A.SyncClassSupplies() end
    -- Repair the reported Ankh state once when upgrading the supply controls.
    if not d.supplyControlsV2 then
        local _,class=UnitClass('player')
        if class=='SHAMAN' then
            local r=d.supplies[17030]
            if not r then d.supplies[17030]={target=3,minLevel=30,classDefault=true} end
            d.filters.supplies=true;d.filters['supplies/17030']=true;d.sources.SupplyRows=nil
            d.dismissed['supply:17030']=nil;d.snoozed['supply:17030']=nil;d.trash['supply:17030']=nil
        end
        d.supplyControlsV2=true
    end
    if d.auto == nil then d.auto = true end
    if d.bagSlots == nil then d.bagSlots = 4 end
    A.providerHealth={};if A.InvalidateProviders then A.InvalidateProviders() end
    if A.ApplyTheme then A.ApplyTheme() end
    if A.ApplyBindingLabels then A.ApplyBindingLabels() end
end
function A.Map()
    return C_Map and A.Safe('current map', C_Map.GetBestMapForUnit, 'player')
end
function A.MapName(map)
    local info = map and C_Map and A.Safe('map info', C_Map.GetMapInfo, map)
    return info and info.name or GetZoneText()
end
function A.ItemCount(id)
    local fn = C_Item and C_Item.GetItemCount or GetItemCount
    return A.Safe('item count', fn, id, false, false) or 0
end
function A.ItemName(id)
    local name=A.Safe('item name',C_Item and C_Item.GetItemNameByID,id) or A.Safe('item info',GetItemInfo,id)
    if name then return name end
    A.itemRequests=A.itemRequests or {}
    if C_Item and C_Item.RequestLoadItemDataByID and not A.itemRequests[id] then
        A.itemRequests[id]=true;A.Safe('load item name',C_Item.RequestLoadItemDataByID,id)
    end
    return 'Item '..id
end
function A.SpellKnown(id)
    if type(id)~='number' then return false end
    for _,fn in ipairs({IsPlayerSpell or false,IsSpellKnownOrOverridesKnown or false,
        IsSpellKnown or false,(C_SpellBook and C_SpellBook.IsSpellKnown) or false}) do
        if type(fn)=='function' and A.Safe('known player spell',fn,id)==true then return true end
    end
    return false
end
function A.QuestDone(id)
    if A.sessionCompleted and A.sessionCompleted[id] then return true end
    if C_QuestLog and A.Safe('quest done',C_QuestLog.IsQuestFlaggedCompleted,id)==true then return true end
    if A.Safe('legacy quest done',IsQuestFlaggedCompleted,id)==true then return true end
    -- This is Questie's character completion history, NOT its IsComplete()
    -- helper, which only means a quest in the log is ready for hand-in.
    local history=Questie and Questie.db and Questie.db.char and Questie.db.char.complete
    return history and (history[id]==true or history[id]==1) or false
end
function A.QuestActive(id)
    return C_QuestLog and A.Safe('quest active', C_QuestLog.IsOnQuest, id) == true
end
function A.QuestReady(id)
    return not A.QuestDone(id) and A.QuestActive(id) and C_QuestLog and A.Safe('quest ready', C_QuestLog.IsComplete, id) == true
end
function A.ReminderHidden(row)
    return A.db.trash[A.TrashKey(row)] or A.db.trash[row.key] or A.db.dismissed[row.key]
        or (A.db.snoozed[row.key] or 0)>time()
end
function A.Add(out, row)
    if not row or not row.key then return end
    if A.captureProvider then
        row.priority=row.priority or 50
        for _,old in ipairs(out) do if old.key==row.key then return end end
        out[#out+1]=row;return
    end
    if A.Category then local cat,sub=A.Category(row);if not A.CategoryEnabled(cat,sub) then return end end
    if A.ReminderHidden(row) then return end
    if A.ScopeAllows and not A.ScopeAllows(row) then return end
    for _, old in ipairs(out) do
        if old.key == row.key then return end
    end
    row.priority = row.priority or 50
    out[#out+1] = row
end
function A.Collect(map, travel, useCache)
    local out = {}
    if not A.db or not map then return out end
    if not useCache and A.InvalidateProviders then A.InvalidateProviders() end
    A.providerHealth={};A.coveredBooks={};A.collectClassList=nil;A.worldCoordCache={};A.collecting=true
    if A.SyncClassSupplies then A.SyncClassSupplies() end
    for _, name in ipairs({'AttuneRows','TurnInRows','BagQuestItemRows','ImportantVendorRows','ProfessionRows','SupplyRows','HunterAmmoRows','RepairRows','ClassSpellRows','WeaponRows','TalentRows','FlightRows','HearthstoneRows','PetMoodRows','TrainerRows','BagRows'}) do
        if A.RunProvider then A.RunProvider(name,out,map,travel,useCache)
        elseif A.db.sources[name]~=false then A.Safe(name, A[name], out, map, travel) end
    end
    A.collectClassList=nil;A.collecting=nil
    if A.SortReminders then A.SortReminders(out) else
        table.sort(out, function(a,b)
            if a.priority == b.priority then return a.key < b.key end
            return a.priority < b.priority
        end)
    end
    A.worldCoordCache=nil
    return out
end
function A.Refresh(reason, show, manual, forceDraw)
    if not A.db then return end
    if A.AutomaticSuppressed and A.AutomaticSuppressed() and not manual then
        if not A.manualInstance or not (A.frame and A.frame:IsShown()) then A.ClearLocation();return end
        show=false -- a manual checklist may update, but automatic events cannot reopen it
    end
    if manual then A.manualInstance=A.AutomaticSuppressed and A.AutomaticSuppressed() or false end
    if InCombatLockdown() then
        local p=A.pending
        A.pending = {reason=(p and p.show and not show) and p.reason or reason, show=show or (p and p.show),manual=manual or (p and p.manual)}
        return
    end
    if A.CleanupPin then A.CleanupPin() end
    if not manual and not A.db.auto and not (A.frame and A.frame:IsShown()) then return end
    if A.InTransit and A.InTransit() then if A.frame then A.frame:Hide() end;return end
    local scope=A.RequireScope and A.RequireScope()
    local map=scope and scope.map or A.Map()
    if not map or (A.RequireScope and not scope) then if A.ClearLocation then A.ClearLocation(true) end;return end
    local travel = reason == 'Before travel' or reason == 'Merchant' or reason == 'Bank'
    local rows = A.Collect(map, travel, not manual and reason~='Manual check')
    A.rows = rows
    if A.CleanupPin then A.CleanupPin() end
    if reason and reason:find('^Entering ') and not A.db.arrival then show=false end
    if travel and not A.db.travel then show=false end
    if #rows==0 and not A.db.showEmpty then show=false end
    local capitalArrival=A.capitalArrivalMap==map
    A.capitalArrivalMap=nil
    if capitalArrival and show and A.db.auto and A.db.arrival and #rows>0 then
        A.db.collapsed=false;A.db.collapseMode=nil
    end
    if A.Draw and ((A.frame and A.frame:IsShown()) or (show and (A.db.auto or manual))) then
        A.Draw(rows, reason or A.MapName(map),manual==true or forceDraw==true)
    end
    if A.trashFrame and A.trashFrame:IsShown() and A.DrawTrashBin then A.DrawTrashBin() end
end
function A.TrashKey(row)
    return row.quest and ('quest:'..row.quest) or row.key
end
function A.Dismiss(row)
    A.db.dismissed[row.key]=true;A.Refresh('Updated',false,nil,true)
end
function A.Trash(row)
    A.db.trash[A.TrashKey(row)]=A.MakeTrashRecord and A.MakeTrashRecord(row) or true
    A.db.dismissed[row.key]=nil;A.db.snoozed[row.key]=nil
    A.Refresh('Updated',false,nil,true)
end
function A.SetSupplyTarget(id,target)
    if type(id)~='number' or id<1 or type(target)~='number' or target<0 or target>10000 then return end
    id,target=math.floor(id),math.floor(target)
    if A.InvalidateProviders then A.InvalidateProviders({'AttuneRows'}) end
    local old=A.db.supplies[id]
    local rule=old or {minLevel=1}
    for _,preset in ipairs(A.ClassSupplyList and A.ClassSupplyList() or {}) do
        if preset[1]==id then rule.classDefault=true;rule.classUtility=preset.classUtility;rule.minLevel=preset[5] or 1 end
    end
    rule.target=target
    A.db.supplies[id]=target>0 and rule or nil
    if target==0 and A.db.retiredClassSupplies then A.db.retiredClassSupplies[id]=nil end
    A.db.supplyOverrides=A.db.supplyOverrides or {};A.db.supplyOverrides[id]=true
    A.db.filters.supplies=true;A.db.filters['supplies/'..id]=target>0
    A.db.sources.SupplyRows=nil
    local key='supply:'..id
    A.db.dismissed[key]=nil;A.db.snoozed[key]=nil;A.db.trash[key]=nil
    local have=A.ItemCount(id)
    local message=A.ItemName(id)..': '..(target==0 and 'target removed' or ('Target '..target..' · Have '..have..' · Need '..math.max(0,target-have)))
    if A.Draw and target>have and not InCombatLockdown() then
        A.Refresh('Supply target saved',true,true);if A.frame and A.frame:IsShown() then A.SetCollapsed(false,'manual') end
    else A.Refresh('Supply target saved',false) end
    return message
end
function A.EnableSupply(id,enabled)
    if enabled then
        local rule=A.db.supplies[id]
        local target=rule and rule.target or 3
        for _,p in ipairs(A.ClassSupplyList()) do if p[1]==id and not rule then target=p[3] end end
        return A.SetSupplyTarget(id,target)
    end
    A.db.filters['supplies/'..id]=false
    A.Refresh('Supply disabled',false)
end
function A.DeleteSupply(id)
    A.SetSupplyTarget(id,0)
    A.db.filters['supplies/'..id]=nil
    for _,cat in ipairs(A.categories) do if cat.id=='supplies' then cat.subs[tostring(id)]=nil end end
end
function A.SupplyStatus(id)
    local r=A.db.supplies[id];local have=A.ItemCount(id)
    local state
    if not r or not A.CategoryEnabled('supplies',tostring(id)) or A.db.sources.SupplyRows==false then state='Disabled'
    elseif A.db.reagentEconomy and r.classDefault and not r.classUtility then state='Reagent Economy enabled'
    elseif UnitLevel('player')<(r.minLevel or 1) then state='Requires level '..r.minLevel
    elseif A.SupplyRelevant and not A.SupplyRelevant(id,r) then state='Spell not learned / older rank'
    elseif A.db.trash['supply:'..id] then state='Ignored — re-enable to show'
    elseif (A.db.snoozed['supply:'..id] or 0)>time() then state='Hidden for 30m — re-enable to show'
    elseif A.db.dismissed['supply:'..id] then state='Skipped this visit — re-enable to show'
    elseif not A.HasVendorSource(id) then state='No known vendor — not a shopping reminder'
    elseif have>=r.target then state='Stocked'
    else state='Need '..(r.target-have)..' more' end
    return have..' in bags · '..state
end
function A.BeginVisit()
    A.db.dismissed={}
end
function A.Snooze(row, seconds)
    A.db.snoozed[row.key] = time() + (seconds or 1800)
    A.Refresh('Updated', false,nil,true)
end
function A.BagRows(out, map, travel)
    if not travel or not C_Container then return end
    local free = 0
    for bag=0,4 do
        local slots, family = A.Safe('bag slots', C_Container.GetContainerNumFreeSlots, bag)
        if family == 0 then free = free + (slots or 0) end
    end
    if free < A.db.bagSlots then
        A.Add(out, {key='bags', title='Only '..free..' general bag slots free', detail='Sell, bank or mail items before a long trip.', priority=40})
    end
end
function A.BagQuestItemRows(out)
    local numSlots = (C_Container and C_Container.GetContainerNumSlots) or GetContainerNumSlots
    local questInfo = (C_Container and C_Container.GetContainerItemQuestInfo) or GetContainerItemQuestInfo
    if type(numSlots)~='function' or type(questInfo)~='function' then return end
    for bag=0,4 do
        local slots = A.Safe('bag slot count', numSlots, bag) or 0
        for slot=1,slots do
            local a,b,c = A.Safe('bag quest item', questInfo, bag, slot)
            local questID,isActive
            if type(a)=='table' then questID,isActive=a.questID,a.isActive
            else questID,isActive=b,c end
            if type(questID)=='number' and questID>0 and not isActive and not A.QuestActive(questID) and not A.QuestDone(questID) then
                local name
                local itemInfo = C_Container and C_Container.GetContainerItemInfo and A.Safe('bag quest item info', C_Container.GetContainerItemInfo, bag, slot)
                if type(itemInfo)=='table' then
                    name = itemInfo.itemName or (itemInfo.itemID and A.ItemName(itemInfo.itemID))
                else
                    local idFn = (C_Container and C_Container.GetContainerItemID) or GetContainerItemID
                    local itemID = idFn and A.Safe('bag quest item ID', idFn, bag, slot)
                    if itemID then name = A.ItemName(itemID) end
                end
                A.Add(out, {key='bagquest:'..questID, quest=questID, bagQuest=true,
                    title='Start quest from bag: '..(name or ('Quest '..questID)),
                    detail='Right-click this item in your bags to accept the quest.', priority=18})
            end
        end
    end
end
function A.TalentRows(out)
    local points = (UnitCharacterPoints and A.Safe('unspent talent points', UnitCharacterPoints, 'player'))
        or (GetUnspentTalentPoints and A.Safe('unspent talent points', GetUnspentTalentPoints)) or 0
    if type(points)=='number' and points>0 then
        A.Add(out, {key='talents', talents=true,
            title=points==1 and 'Unspent talent point (1)' or ('Unspent talent points ('..points..')'),
            detail='Open your Talents window to spend available points.', priority=22})
    end
end
function A.HearthstoneRows(out)
    local numSlots = (C_Container and C_Container.GetContainerNumSlots) or GetContainerNumSlots
    local countFn = (C_Item and C_Item.GetItemCount) or GetItemCount
    if type(numSlots)~='function' or type(countFn)~='function' then return end
    local backpack = A.Safe('backpack slots', numSlots, 0) or 0
    if backpack<=0 then return end
    if (A.Safe('hearthstone bag count', countFn, 6948, false, false) or 0)>0 then return end
    local total = A.Safe('hearthstone bank count', countFn, 6948, true, false) or 0
    local bind = GetBindLocation and A.Safe('hearthstone bind location', GetBindLocation)
    local bindNote = (type(bind)=='string' and bind~='') and ('\nCurrent bind location: '..bind) or ''
    if total>0 then
        A.Add(out, {key='hearthstone', hearthstone=true, inventoryWarning=true,
            title='Hearthstone is in your bank',
            detail='Take your Hearthstone out of the bank before travelling.'..bindNote, priority=16})
    else
        A.Add(out, {key='hearthstone', hearthstone=true, inventoryWarning=true,
            title='Hearthstone missing from bags',
            detail='Speak to an innkeeper to get a replacement Hearthstone.'..bindNote, priority=16})
    end
end
function A.PetMoodRows(out)
    if not (A.IsHunter and A.IsHunter()) then return end
    if type(GetPetHappiness)~='function' then return end
    if UnitExists and not A.Safe('pet exists', UnitExists, 'pet') then return end
    local happiness = A.Safe('pet happiness', GetPetHappiness)
    if happiness==1 then
        A.Add(out, {key='petmood', petMood=true, emptyEssential=true,
            title='Hunter pet is unhappy',
            detail='Feed your pet before travelling (75% damage; risk of running away).', priority=10})
    end
end
function A.ApplyBindingLabels()
    BINDING_HEADER_ONELASTTHING = A.name
    BINDING_NAME_ONELASTTHING_TOGGLE = A.Translate('Toggle / check checklist')
    BINDING_NAME_ONELASTTHING_SETTINGS = A.Translate('Open settings')
end
function A.TogglePopup()
    if not A.db then return end
    if InCombatLockdown() then A.Print('Checklist will open after combat.');return end
    if A.frame and A.frame:IsShown() then A.scopeRecovery=nil;A.frame:Hide()
    else A.Refresh('Manual check',true,true) end
end
function A.ToggleSettings()
    if not A.db then return end
    if InCombatLockdown() then A.Print('Open settings after combat.');return end
    if A.settings and A.settings:IsShown() then A.settings:Hide()
    elseif A.ShowSettings then A.ShowSettings() end
end
A.ApplyBindingLabels()
function A.Navigate(row)
    if InCombatLockdown() then return end
    local native=row.map and row.x and row.y and C_Map and C_Map.SetUserWaypoint and UiMapPoint
        and (not C_Map.CanSetUserWaypointOnMap or A.Safe('waypoint supported',C_Map.CanSetUserWaypointOnMap,row.map))
    if not native and row.skill and SkillUpForever and SkillUpForever.API then
        local before=A.ReadWaypoint and A.ReadWaypoint()
        local placed=A.Safe('profession navigation',SkillUpForever.API.Navigate,row.skill,row.stepIndex)
        local after=A.ReadWaypoint and A.ReadWaypoint()
        if placed and after and A.TrackWaypoint and (not before or before.map~=after.map or before.x~=after.x or before.y~=after.y) then A.TrackWaypoint(row) end
        return
    end
    local attuneOpened=false
    if not native and row.attuneStep and not row.finish and Attune_ToggleView and Attune_Select and Attune_ShowQuestDetail then
        A.Safe('open Attune', Attune_ToggleView, true)
        A.Safe('select Attune chain', Attune_Select, row.attuneStep.ID_ATTUNE, true)
        A.Safe('Attune quest detail', Attune_ShowQuestDetail, row.attuneStep)
        attuneOpened=true
        -- Attune owns its own map view. The native waypoint below also works when
        -- its full-map setting is off, without modifying that setting.
    end
    local mapOpened=false
    if row.map and row.x and row.y and C_Map and C_Map.SetUserWaypoint and UiMapPoint then
        if native then
            local ok,result=pcall(C_Map.SetUserWaypoint,UiMapPoint.CreateFromCoordinates(row.map,row.x/100,row.y/100))
            if ok and result~=false then
                if A.TrackWaypoint then A.TrackWaypoint(row,row.map,row.x/100,row.y/100) end
                if C_SuperTrack then A.Safe('track waypoint', C_SuperTrack.SetSuperTrackedUserWaypoint,true) end
            elseif not ok then
                A.errors['set waypoint']=tostring(result)
            end
        end
        if OpenWorldMap then A.Safe('open world map', OpenWorldMap,row.map);mapOpened=true end
    elseif row.map and OpenWorldMap then
        A.Safe('open world map', OpenWorldMap,row.map);mapOpened=true
    end
    if not mapOpened and not attuneOpened then
        A.Print(row.detail or row.title)
    end
end
