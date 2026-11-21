local _, A = ...
local events=CreateFrame('Frame');A.eventFrame=events
local queued=false
local merchantDirty,trainerDirty,settingsDirty
local ready=false
local function schedule(reason,show)
    if show or not A.scheduledShow then A.scheduledReason=reason end
    A.scheduledShow=show or A.scheduledShow
    if queued then return end
    queued=true
    C_Timer.After(0.6,function()
        queued=false
        if merchantDirty then
            merchantDirty=nil
            A.Safe('observe merchant',A.ObserveMerchant);A.Safe('observe repair vendor',A.ObserveRepairMerchant);A.Safe('important vendor offers',A.ObserveImportantMerchant)
        end
        if trainerDirty then trainerDirty=nil;A.Safe('observe trainer',A.ObserveTrainer) end
        if settingsDirty then
            settingsDirty=nil
            if A.settings and A.settings:IsShown() then A.Safe('item settings',A.BuildSettings) end
        end
        local r,s=A.scheduledReason,A.scheduledShow
        A.scheduledReason,A.scheduledShow=nil,nil
        A.Safe('refresh',A.Refresh,r,s)
    end)
end
local currentLocation,pendingLocation,currentMap
local zone
zone=function()
    if A.loadingWorld then A.ClearLocation();return end
    if A.AutomaticSuppressed() then A.cityVisitMap=nil;if not A.manualInstance then A.ClearLocation() end;return end
    if A.InTransit() then
        A.cityVisitMap=nil
        A.travelPending=true;pendingLocation=nil;A.scopeRecovery=nil
        if A.frame then A.frame:Hide() end
        return
    end
    local scope=A.RequireScope();if not scope then pendingLocation=nil;return end
    if scope.key~=currentLocation or A.travelPending or A.scopeRecovery then
        if pendingLocation==scope.key then return end
        local key=scope.key;pendingLocation=key
        -- Confirm stable local position/name after flight or loading changes.
        C_Timer.After(.8,function()
            if pendingLocation~=key then return end
            pendingLocation=nil
            local confirmed=A.RequireScope()
            if not confirmed or A.InTransit() then return end
            if confirmed.key~=key then zone();return end
            local newVisit=key~=currentLocation or A.travelPending
            local recovery=A.scopeRecovery;A.scopeRecovery=nil
            if newVisit then
                A.capitalArrivalMap=A.IsCapitalMap(confirmed.map) and
                    (currentMap~=confirmed.map or A.travelPending or A.capitalArrivalMap==confirmed.map) and confirmed.map or nil
            end
            currentMap=confirmed.map
            currentLocation=key;A.travelPending=nil
            if newVisit then
                A.InvalidateProviders()
                -- Loading within the same capital is still the same visit.
                if not (A.IsCapitalMap(confirmed.map) and A.cityVisitMap==confirmed.map) then A.BeginVisit() end
                A.cityVisitMap=A.IsCapitalMap(confirmed.map) and confirmed.map or nil
                schedule('Entering '..confirmed.name,true)
            elseif recovery then
                A.Safe('restore location checklist',A.Refresh,'Location restored',true,recovery.manual)
            end
        end)
    end
end
local travelSpells={[8690]=true,[556]=true,[3561]=true,[3562]=true,[3563]=true,[3565]=true,[3566]=true,[3567]=true}
events:SetScript('OnEvent',function(_,event,...)
    if event=='ADDON_LOADED' then
        local name=...
        if name=='OneLastThing' then A.Init() end
        if ready then A.InvalidateProviders();if A.ApplyFonts then A.ApplyFonts() end;if A.settings and A.settings:IsShown() then A.BuildSettings() end;schedule('Data updated',false) end
        return
    end
    if not A.db then return end
    A.InvalidateForEvent(event)
    if event=='PLAYER_LOGIN' then
        ready=true
        C_Timer.After(3,function()
            if A.db.theme=='neavCurrent' then A.ApplyTheme() end -- native palette may initialize after our files
            zone()
        end)
        if not A.zoneTicker then A.zoneTicker=C_Timer.NewTicker(2,zone) end
        if not A.refreshTicker then A.refreshTicker=C_Timer.NewTicker(5,function()
            A.refreshTick=(A.refreshTick or 0)+1
            local menuOpen=A.filterMenu and A.filterMenu:IsShown()
            if ready and A.frame and A.frame:IsShown() and not menuOpen and (not A.db.collapsed or A.refreshTick%4==0) then schedule('Updated',false) end
        end) end
    elseif event=='PLAYER_LEAVING_WORLD' then
        A.loadingWorld=true;A.manualInstance=nil;pendingLocation=nil;currentLocation=nil;currentMap=nil;A.capitalArrivalMap=nil
        A.ClearLocation()
    elseif event=='ZONE_CHANGED_NEW_AREA' or event=='ZONE_CHANGED' or event=='ZONE_CHANGED_INDOORS' or event=='PLAYER_ENTERING_WORLD' or event=='PLAYER_CONTROL_GAINED' then
        A.loadingWorld=nil;A.manualInstance=nil;A.ClearLocation(true)
        if ready then C_Timer.After(1,zone) end
    elseif event=='PLAYER_REGEN_ENABLED' then
        if A.pending then local p=A.pending;A.pending=nil;if p.manual then A.Safe('manual refresh',A.Refresh,p.reason,p.show,true) else schedule(p.reason,p.show) end end
    elseif event=='TAXIMAP_OPENED' or event=='BANKFRAME_OPENED' then
        if event=='TAXIMAP_OPENED' then A.Safe('observe known flights',A.ObserveFlights) end
        schedule(event=='TAXIMAP_OPENED' and 'Before travel' or 'Bank',true)
    elseif event=='MERCHANT_SHOW' or event=='MERCHANT_UPDATE' then
        merchantDirty=true;schedule('Merchant',event=='MERCHANT_SHOW')
    elseif event=='MERCHANT_CLOSED' then
        merchantDirty=nil;A.importantOffers=nil;A.liveSupplyPrices=nil;A.liveRepairCost=nil;A.liveRepairVendor=nil;schedule('Updated',false)
    elseif event=='TRAINER_SHOW' or event=='TRAINER_UPDATE' then
        trainerDirty=true;schedule('Trainer',event=='TRAINER_SHOW')
    elseif event=='TRAINER_CLOSED' then
        trainerDirty=nil;schedule('Updated',false)
    elseif event=='UNIT_SPELLCAST_SENT' then
        local unit,_,_,spell=...
        if unit=='player' and travelSpells[spell] then schedule('Before travel',true) end
    elseif event=='GET_ITEM_INFO_RECEIVED' or event=='ITEM_DATA_LOAD_RESULT' then
        local id=...
        local selected=A.IsHunter() and A.HunterAmmoSelection()
        if A.db.supplies[id] or selected==id or (A.IsCriticalBook and A.IsCriticalBook(id)) then
            if A.settings then A.settings.signature=nil;settingsDirty=true end
            schedule('Updated',false)
        end
    elseif event=='QUEST_DATA_LOAD_RESULT' then
        local id=...
        if A.questRequests and A.questRequests[id] then schedule('Updated',false) end
    elseif event=='QUEST_TURNED_IN' then
        local id=...;if type(id)=='number' then A.sessionCompleted=A.sessionCompleted or {};A.sessionCompleted[id]=true end
        schedule('Updated',false)
    else schedule('Updated',false) end
end)
for _,event in ipairs({'ADDON_LOADED','PLAYER_LOGIN','PLAYER_ENTERING_WORLD','PLAYER_LEAVING_WORLD','ZONE_CHANGED_NEW_AREA','ZONE_CHANGED','ZONE_CHANGED_INDOORS','PLAYER_REGEN_ENABLED','PLAYER_CONTROL_GAINED','TAXIMAP_OPENED','BANKFRAME_OPENED','MERCHANT_SHOW','MERCHANT_UPDATE','MERCHANT_CLOSED','TRAINER_SHOW','TRAINER_UPDATE','TRAINER_CLOSED','UNIT_PET','PET_UI_UPDATE','PET_BAR_UPDATE','UNIT_SPELLCAST_SENT','QUEST_LOG_UPDATE','QUEST_TURNED_IN','BAG_UPDATE_DELAYED','SKILL_LINES_CHANGED','PLAYER_LEVEL_UP','SPELLS_CHANGED','PLAYER_MONEY','UPDATE_INVENTORY_DURABILITY','PLAYER_EQUIPMENT_CHANGED','GET_ITEM_INFO_RECEIVED','ITEM_DATA_LOAD_RESULT','QUEST_DATA_LOAD_RESULT'}) do
    A.Safe('event '..event,events.RegisterEvent,events,event)
end
SLASH_ONELASTTHING1='/olt'
SLASH_ONELASTTHING2='/onelastthing'
SlashCmdList.ONELASTTHING=function(text)
    if not A.db then return end
    local cmd,arg=text:match('^(%S*)%s*(.-)%s*$');cmd=(cmd or ''):lower()
    if cmd=='' or cmd=='check' then
        A.Refresh('Manual check',true,true)
    elseif cmd=='settings' then A.ShowSettings()
    elseif cmd=='supply' then
        local id,n=arg:match('^(%d+)%s+(%d+)$');id,n=tonumber(id),tonumber(n)
        if not id or not n or n>10000 then A.Print('Use /olt supply ITEM_ID TARGET (0 removes it).');return end
        A.Print(A.SetSupplyTarget(id,n))
    elseif cmd=='restore' then A.db.dismissed={};A.db.snoozed={};A.Refresh('Restored',true)
    elseif cmd=='auto' then A.db.auto=not A.db.auto;A.Print('Automatic popups: '..tostring(A.db.auto))
    elseif cmd=='status' then
        A.Refresh('Diagnostics',false)
        if A.ChecksIncomplete() then A.Print(A.CheckHealthText()) end
        A.Print('Version '..A.version..'; map '..tostring(A.Map()))
        for k,v in pairs(A.status) do A.Print(k..': '..v) end
        for k,v in pairs(A.errors) do A.Print('Compatibility issue ['..k..']: '..v) end
        if not next(A.errors) then A.Print('No compatibility errors recorded this session.') end
    else
        A.Print('/olt - check | /olt settings | /olt supply ITEM_ID TARGET | /olt restore | /olt auto | /olt status')
    end
end
