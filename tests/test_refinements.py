"""Focused regressions for provider caching, rank books and pooled UI lifecycle."""
from test_startup import fresh_client


def run():
    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing
        local x=.2
        C_Map.GetPlayerMapPosition=function() return {GetXY=function() return x,.5 end} end
        TrainerSpells_Data={SHAMAN={
            [1]={[101]={rank=1},[102]={rank=1},[103]={rank=1,
                sourceLocations={{uiMapID=1458,x=10,y=50,name='Specialist'}}}},
            [60]={[201]={rank=1,requires={999}},[202]={},[301]={rank=3}}}}
        TrainerSpellsClassTrainers={SHAMAN={
            {names={enUS='West'},locations={{uiMapID=1458,x=20,y=50}}},
            {names={enUS='East'},locations={{uiMapID=1458,x=80,y=50}}}}}
        local names={[101]='Ranked',[102]='Train me',[103]='Special',[301]='Ranked'}
        local namesRead,knownRead={},{}
        C_Spell={GetSpellInfo=function(id)
            namesRead[id]=(namesRead[id] or 0)+1;return {name=names[id] or 'Future'}
        end}
        A.SpellKnown=function(id) knownRead[id]=(knownRead[id] or 0)+1;return id==301 end
        A.InvalidateProviders()
        local function collect()
            local out={};A.RunProvider('ClassSpellRows',out,1458,false,true);return out
        end
        local rows=collect();assert(#rows==2)
        local first=rows[1].spell==102 and rows[1] or rows[2]
        assert(first.x==20 and first.detail:find('West',1,true))
        assert(not namesRead[201] and not namesRead[202] and not knownRead[202] and not knownRead[999])
        assert(namesRead[301]==1 and knownRead[301]==1) -- learned future rank suppresses 101
        local scans=namesRead[102]
        x=.8;A.scope.x=x
        rows=collect();assert(namesRead[102]==scans)
        for _,r in ipairs(rows) do
            if r.spell==102 then assert(r.x==80 and r.detail:find('East',1,true)) end
            if r.spell==103 then assert(r.x==10 and r.detail:find('Specialist',1,true)) end
        end
        assert(first.x==20) -- relocation never mutates an old displayed row
        A.providerCache.WeaponRows={sentinel=true};local flight={};A.providerCache.FlightRows=flight
        A.InvalidateForEvent('SKILL_LINES_CHANGED')
        assert(not A.providerCache.WeaponRows and not A.providerCache.ClassSpellRows)
        assert(A.providerCache.FlightRows==flight)
        collect();assert(namesRead[102]==scans+1)
        -- Replacing the class data table invalidates immediately; in-place changes
        -- are also picked up by explicit invalidation or the existing 60s TTL.
        TrainerSpells_Data.SHAMAN={[1]={[102]={rank=1},[104]={rank=1}}}
        rows=collect();assert(#rows==2 and namesRead[104]==1)
        TrainerSpells_Data.SHAMAN[1][105]={rank=1};now=now+61
        rows=collect();assert(#rows==3 and namesRead[105]==1)
    ''')
    print('PASS: selective skill invalidation, movement-only trainer relocation, source-specific trainers, '
          'future spell pruning, learned higher ranks, immutable cached templates, data replacement and TTL')

    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing
        GetMoney=function() return 20000 end
        SkillUpForever={API={version=1,Professions=function()
            return {{skillLineID=129,name='First Aid',rank=145,maxRank=150,steps={}}}
        end}}
        A.FindVendor=function() return {map=1458,x=50,y=50,name='Book vendor'} end
        A.db.sources={}
        for _,name in ipairs({'AttuneRows','TurnInRows','SupplyRows','HunterAmmoRows','RepairRows',
            'ClassSpellRows','WeaponRows','FlightRows','TrainerRows','BagRows'}) do A.db.sources[name]=false end
        local key='buybook:16084'
        local rows=A.Collect(1458,false);assert(#rows==1 and rows[1].criticalBook)
        A.db.dismissed[key]=true;assert(#A.Collect(1458,false)==0)
        A.db.dismissed={};A.db.snoozed[key]=now+30;assert(#A.Collect(1458,false)==0)
        now=now+31;rows=A.Collect(1458,false);assert(#rows==1 and rows[1].criticalBook)
        A.db.snoozed={};A.db.trash[key]=true;assert(#A.Collect(1458,false)==0)
        A.scope={map=1454,x=.5,y=.5};rows=A.Collect(1454,false)
        assert(#rows==1 and rows[1].key=='cap:129') -- warning remains useful elsewhere
        A.scope={map=1458,x=.5,y=.5};A.db.sources.ImportantVendorRows=false
        rows=A.Collect(1458,false);assert(#rows==1 and rows[1].key=='cap:129')
        A.db.sources.ImportantVendorRows=nil;A.db.trash={};A.BeginVisit()
        rows=A.Collect(1458,false);assert(#rows==1 and rows[1].criticalBook)
        A.db.dismissed[key]=true;A.FindVendor=function() return {map=1413,x=90,y=90,name='Far seller'} end
        A.scope={map=1413,x=.1,y=.1};rows=A.Collect(1413,false)
        assert(#rows==1 and rows[1].key=='cap:129') -- out-of-range book is not coverage
    ''')
    print('PASS: skipped/timed/ignored local books suppress duplicate cap warnings, expiry/restore, '
          'other maps, distant vendors and disabled book provider preserve generic warnings')

    vm = fresh_client('HUNTER')
    vm.execute('''
        local A=OneLastThing
        A.ShowSettings();local f=A.settings
        local values={}
        for _,key in ipairs({'range','fadeDelay','repairs'}) do
            local slot=key;f[key].SetValue=function(_,v) values[slot]=v end
        end
        local pool=f.pool;local b=f.fontPicker
        local enter=b:GetScript('OnEnter');local down=b:GetScript('OnMouseDown')
        A.db.nearbyRadius=1300;A.db.completionDelay=23;A.db.repairThreshold=55
        A.BuildSettings()
        assert(f.pool==pool and values.range==1300 and values.fadeDelay==23 and values.repairs==55)
        local backdrops=0;b.SetBackdrop=function() backdrops=backdrops+1 end
        b:GetScript('OnEnter')(b);f.signature=nil;A.BuildSettings()
        assert(b:GetScript('OnEnter')==enter and b:GetScript('OnMouseDown')==down and backdrops==0)
        assert(A.panels[b].r==.09 and A.fonts[b:GetFontString()]) -- reset hover and retain font registration
        -- Locate the actual pet-food picker via its label, then inspect rebuild entry.
        local picker
        A.VendorPetFoodChoices=function() return {{0,'Fixture food'},{123,'Other food'}} end
        A.VendorPetFoodSelection=function() return 0 end
        A.SelectVendorPetFood=function(id) A.db.petFoodID=id end
        f.signature=nil;A.BuildSettings()
        for _,control in ipairs(f.controls) do
            if control.kind=='Button' and control:GetText()=='Fixture food  v' then picker=control end
        end
        assert(picker);picker:GetScript('OnClick')()
        local rebuild=A.BuildSettings;local sawClosed=false
        A.BuildSettings=function()
            sawClosed=not f.menu:IsShown();return rebuild()
        end
        f.menu.items[2]:GetScript('OnClick')()
        assert(sawClosed and not f.menu:IsShown())
    ''')
    print('PASS: range/fade/repair slider fast-path, stable pooled style handlers, hover reset, '
          'font registration and pet-food dropdown closure before rebuild')

    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing;local f=A.frame
        A.providerHealth={};A.Collect=function() return {} end
        f.previousCount=1;A.Draw({},'Updated')
        assert(f.header:GetScript('OnUpdate')==nil)
        for i=1,3 do timerStep() end
        assert(f.header:GetScript('OnUpdate'))
        f.header:GetScript('OnUpdate')(f.header,.4)
        assert(f.idleBadge and f.header:GetScript('OnUpdate')==nil)
        f.header:GetScript('OnEnter')();f.header:GetScript('OnLeave')()
        for i=1,3 do timerStep() end
        assert(f.header:GetScript('OnUpdate'))
        f.header:GetScript('OnEnter')();assert(f.header:GetScript('OnUpdate')==nil)
        f.header:GetScript('OnLeave')();timerStep()
        A.SetCollapsed(false,'manual');assert(f.header:GetScript('OnUpdate')==nil)
        A.SetCollapsed(true,'manual');timerStep()
        f:Hide();assert(f.header:GetScript('OnUpdate')==nil)
        for i=1,3 do timerStep() end
        assert(f.header:GetScript('OnUpdate')==nil)
    ''')
    print('PASS: header OnUpdate exists only during fade and clears on completion, hover, expansion and hide')

    vm = fresh_client(locale='deDE')
    vm.execute('''
        local A=OneLastThing
        -- Subzone and indoor transitions keep a visible checklist steady without flicker.
        local origCollect=A.Collect
        A.Collect=function() return {{key='test:steady',title='Task',map=1458,x=50,y=50}} end
        A.Refresh('Manual check',true,true)
        assert(A.frame:IsShown())
        GetMinimapZoneText=function() return 'Apothecarium' end
        event(nil,'ZONE_CHANGED')
        assert(A.frame:IsShown())
        event(nil,'ZONE_CHANGED_INDOORS')
        assert(A.frame:IsShown())
        for i=1,4 do timerStep() end
        assert(A.frame:IsShown() and A.scope.name=='Apothecarium')
        -- Crossing to another map clears stale reminders immediately before settling.
        local origGetMap=C_Map.GetBestMapForUnit
        C_Map.GetBestMapForUnit=function() return 1411 end
        GetMinimapZoneText=function() return 'Durotar' end
        event(nil,'ZONE_CHANGED_NEW_AREA')
        assert(not A.frame:IsShown())
        for i=1,4 do timerStep() end
        assert(A.frame:IsShown() and A.scope.map==1411)
        C_Map.GetBestMapForUnit=origGetMap
        GetMinimapZoneText=function() return 'Undercity' end
        event(nil,'PLAYER_LEAVING_WORLD');event(nil,'PLAYER_ENTERING_WORLD')
        for i=1,4 do timerStep() end

        -- Async item-load bursts coalesce Settings rebuilds rather than rebuilding synchronously.
        A.ShowSettings()
        local rebuilds=0
        local origBuild=A.BuildSettings
        A.BuildSettings=function() rebuilds=rebuilds+1;return origBuild() end
        A.db.supplies={[17030]={target=3,minLevel=30}}
        event(nil,'GET_ITEM_INFO_RECEIVED',17030)
        event(nil,'ITEM_DATA_LOAD_RESULT',17030)
        assert(rebuilds==0)
        timerStep()
        assert(rebuilds==1)
        A.BuildSettings=origBuild

        -- Navigation still opens the destination map when waypoint placement is unavailable or fails.
        local opened,openedMap,printed=0,nil,nil
        local origPrint=A.Print;A.Print=function(msg) printed=msg end
        UiMapPoint={CreateFromCoordinates=function(m,x,y) return {map=m,x=x,y=y} end}
        OpenWorldMap=function(m) opened=opened+1;openedMap=m end
        C_Map.CanSetUserWaypointOnMap=function() return false end
        C_Map.SetUserWaypoint=function() error('should not place') end
        A.Navigate({key='n:1',title='No pin',detail='Fallback detail',map=1458,x=50,y=50})
        assert(opened==1 and openedMap==1458 and printed==nil)
        C_Map.CanSetUserWaypointOnMap=function() return true end
        C_Map.SetUserWaypoint=function() return false end
        A.db.pin=nil
        A.Navigate({key='n:2',title='Rejected pin',detail='Pin rejected',map=1458,x=50,y=50})
        assert(opened==2 and openedMap==1458 and not A.db.pin and printed==nil)
        OpenWorldMap=nil
        A.Navigate({key='n:3',title='No map UI',detail='Print detail',map=1458,x=50,y=50})
        assert(printed=='Print detail')
        A.Print=origPrint

        -- Nil-safe mouse-wheel forwarding across checklist, filter, settings and dropdown.
        A.db.collapsed=false
        local origWheel=A.frame.scroll:GetScript('OnMouseWheel')
        A.frame.scroll:SetScript('OnMouseWheel',nil)
        A.frame:GetScript('OnMouseWheel')(A.frame,-1)
        A.frame.scroll:SetScript('OnMouseWheel',origWheel)
        A.ShowFilters(A.frame.filterButton)
        local origFilterWheel=A.filterMenu.scroll:GetScript('OnMouseWheel')
        A.filterMenu.scroll:SetScript('OnMouseWheel',nil)
        A.filterMenu:GetScript('OnMouseWheel')(A.filterMenu,-1)
        A.filterMenu.scroll:SetScript('OnMouseWheel',origFilterWheel)
        A.CloseFilters()
        local origSettingsWheel=A.settings.scroll:GetScript('OnMouseWheel')
        A.settings.scroll:SetScript('OnMouseWheel',nil)
        A.settings:GetScript('OnMouseWheel')(A.settings,-1)
        A.settings.scroll:SetScript('OnMouseWheel',origSettingsWheel)

        -- Shared world-coordinate conversions across Nearby and SortReminders during Collect.
        local oldWorld,oldVec=C_Map.GetWorldPosFromMapPos,CreateVector2D
        CreateVector2D=function(x,y) return {x=x,y=y} end
        local conversions=0
        C_Map.GetWorldPosFromMapPos=function(m,p) conversions=conversions+1;return 1,{GetXY=function() return p.x*10000,p.y*10000 end} end
        A.scope={map=1413,x=.5,y=.5,key='1413:Ratchet'}
        A.db.nearbyOnly=true;A.db.nearbyRadius=850
        A.Collect=origCollect
        local origTurnIn=A.TurnInRows
        A.TurnInRows=function(out,map)
            A.Add(out,{key='q:1:end',quest=1,title='Turn in: One',map=1413,x=52,y=50})
            A.Add(out,{key='q:2:end',quest=2,title='Turn in: Two',map=1413,x=52,y=50})
        end
        local savedFilters=A.db.filters;A.db.filters={}
        for _,name in ipairs({'AttuneRows','ImportantVendorRows','ProfessionRows','SupplyRows','HunterAmmoRows','RepairRows','ClassSpellRows','WeaponRows','FlightRows','TrainerRows','BagRows'}) do
            A.db.sources[name]=false
        end
        A.db.sources.TurnInRows=nil
        A.Collect(1413,false)
        assert(conversions==2 and A.worldCoordCache==nil)
        A.TurnInRows=origTurnIn;A.db.filters=savedFilters;A.db.sources={}
        C_Map.GetWorldPosFromMapPos=oldWorld;CreateVector2D=oldVec

        -- TrashBin skips scanning TrainerSpells_Data when no trashed spell needs rank checks.
        local trainerScans=0
        TrainerSpells_Data={SHAMAN={[1]={[101]={rank=1}}}}
        local origKnown=A.SpellKnown
        A.SpellKnown=function(id) trainerScans=trainerScans+1;return origKnown(id) end
        A.db.trash={['quest:999']=true}
        A.TrashEntries()
        assert(trainerScans==0)
        A.SpellKnown=origKnown;TrainerSpells_Data=nil

        -- German localization parity checks.
        assert(A.FormatMoney(nil)=='Preis unbekannt')
        assert(A.Translate('Observed training')=='Erfasste Ausbildung')
        assert(A.Translate('Map 1454')=='Karte 1454')
        assert(A.Translate('Grey prerequisite — unlocks spell 123 via this chain')=='Graue Vorquest – schaltet Zauber 123 über diese Questreihe frei')
        assert(A.Translate('Grey prerequisite — raid/access chain: raid access')=='Graue Vorquest – Schlachtzug/Zugang: Schlachtzugzugang')
        assert(A.Translate('Version 0.14.5; map 1454')=='Version 0.14.5; Karte 1454')
        assert(A.Translate('Compatibility issue [test]: err')=='Kompatibilitätsproblem [test]: err')
        assert(A.Translate('Automatic popups: true')=='Automatische Hinweise: ein')
        assert(A.Translate('Automatic popups: false')=='Automatische Hinweise: aus')
        assert(A.Translate('/olt - check | /olt settings | /olt supply ITEM_ID TARGET | /olt restore | /olt auto | /olt status'):find('prüfen',1,true))
        assert(A.Translate('Learned status is not reported. Open the flight map once to confirm.')=='Flugpunktstatus nicht gemeldet. Öffne zur Bestätigung einmal die Flugkarte.')
        local origLocName=A.LocationName;A.LocationName=function() return nil end
        A.Draw({},'Updated')
        assert(A.frame.sub:GetText():find('Unbekannter Ort',1,true))
        A.LocationName=origLocName
        local origScope=A.scope;A.scope={map=1454,x=.5,y=.5,key='1454:Orgrimmar'}
        local p={skillLineID=171,name='Alchemie',rank=60,maxRank=75,steps={{kind='train',detail='Orgrimmar'}}}
        SkillUpForever={API={version=1,Professions=function() return {p} end}}
        TrainerSpellsProfessionTrainers={Alchemy={{rank=2,faction='H',names={deDE='Yelmak'},locations={{uiMapID=1454,x=50,y=50}}}}}
        C_Map.GetMapInfo=function() return {name='Orgrimmar'} end
        local profRows={};A.ProfessionRows(profRows,1454)
        assert(#profRows==1 and profRows[1].title=='Alchemie: Nächste Berufsstufe lernen' and profRows[1].detail:find('Preis unbekannt',1,true))
        TrainerSpellsProfessionTrainers=nil;A.scope=origScope
        A.settings.signature=nil;A.BuildSettings()
        local bagIdx,flightIdx,repairIdx
        for i,c in ipairs(A.settings.controls) do
            if c.kind=='CheckButton' and c.label then
                local txt=c.label:GetText()
                if txt=='Taschenplatz' then bagIdx=i elseif txt=='Flugpunkte' then flightIdx=i elseif txt=='Reparaturen' then repairIdx=i end
            end
        end
        assert(flightIdx and repairIdx and bagIdx and flightIdx<repairIdx and repairIdx<bagIdx)
    ''')
    print('PASS: subzone flicker prevention, item-load coalescing, navigation/wheel guards, shared coords, trash scan skip and German localization parity')

    vm = fresh_client('HUNTER', locale='deDE')
    vm.execute('''
        local A=OneLastThing
        -- Borders default OFF to preserve free-floating text; opt-in toggle enables them and hides when collapsed.
        assert(A.db.showBorders==false and A.db.locked==false)
        local borderAlphas={}
        local function watchBorder(frame)
            local orig=frame.SetBackdropBorderColor
            frame.SetBackdropBorderColor=function(self,r,g,b,a) borderAlphas[self]=a;if orig then orig(self,r,g,b,a) end end
        end
        local rows={{key='q:pin',title='Pin target',detail='Detail',map=1458,x=50,y=50}}
        A.Draw(rows,'Manual check',true)
        local rowWidget=A.frame.widgets[1]
        watchBorder(A.frame);watchBorder(rowWidget)
        A.ApplyBorders()
        assert(borderAlphas[A.frame]==0 and borderAlphas[rowWidget]==0)
        A.db.showBorders=true;A.ApplyBorders()
        assert(borderAlphas[A.frame]>0 and borderAlphas[rowWidget]>0)
        A.SetCollapsed(true,'manual')
        assert(borderAlphas[A.frame]==0)
        A.SetCollapsed(false,'manual')
        assert(borderAlphas[A.frame]>0)
        A.db.showBorders=false;A.ApplyBorders()
        assert(borderAlphas[A.frame]==0 and borderAlphas[rowWidget]==0)

        -- Active pin highlights immediately on Navigate and clears on CleanupPin; hover resets on Draw/Hide.
        local wp
        UiMapPoint={CreateFromCoordinates=function(m,x,y) return {uiMapID=m,position={GetXY=function() return x,y end}} end}
        C_Map.SetUserWaypoint=function(p) wp=p;return true end
        C_Map.GetUserWaypoint=function() return wp end
        C_Map.ClearUserWaypoint=function() wp=nil end
        C_Map.CanSetUserWaypointOnMap=function() return true end
        OpenWorldMap=function() end
        assert(rowWidget.go:GetText()=='Karte' and not rowWidget.oltPinned)
        A.Navigate(rows[1])
        assert(rowWidget.oltPinned and rowWidget.go:GetText()=='Karte •' and rowWidget.accent.width==3)
        wp=nil;A.CleanupPin()
        assert(not rowWidget.oltPinned and rowWidget.go:GetText()=='Karte' and rowWidget.accent.width==2)
        rowWidget:GetScript('OnEnter')(rowWidget);assert(rowWidget.hovered==true)
        A.frame:Hide();assert(rowWidget.hovered==false)
        A.Draw(rows,'Manual check',true)

        -- Right-click opens reminder menu; Minimal left-click navigates; Lock window prevents drag/resize.
        rowWidget:GetScript('OnMouseUp')(rowWidget,'RightButton')
        assert(A.reminderMenu and A.reminderMenu:IsShown() and A.reminderMenu.row==rows[1])
        A.reminderMenu:Hide()
        A.db.rowMode='minimal';A.Draw(rows,'Manual check',true)
        local navigated=0;local origNav=A.Navigate
        A.Navigate=function(r) navigated=navigated+1 end
        rowWidget:GetScript('OnMouseUp')(rowWidget,'LeftButton')
        assert(navigated==1)
        A.Navigate=origNav;A.db.rowMode='default';A.Draw(rows,'Manual check',true)
        local moved,sized=0,0
        A.frame.StartMoving=function() moved=moved+1 end
        A.frame.StartSizing=function() sized=sized+1 end
        A.db.locked=true
        A.frame:GetScript('OnDragStart')(A.frame)
        A.frame.header:GetScript('OnDragStart')(A.frame.header)
        rowWidget:GetScript('OnDragStart')(rowWidget)
        A.frame.grip:GetScript('OnMouseDown')(A.frame.grip,'LeftButton')
        assert(moved==0 and sized==0)
        A.frame.header:GetScript('OnClick')(A.frame.header)
        assert(A.db.collapsed==true) -- header click still toggles collapse when locked
        A.SetCollapsed(false,'manual');A.db.locked=false

        -- Native WoW Key Bindings labels (deDE) and combat-safe toggle handlers.
        assert(BINDING_HEADER_ONELASTTHING=='One Last Thing')
        assert(BINDING_NAME_ONELASTTHING_TOGGLE=='Liste umschalten / prüfen')
        assert(BINDING_NAME_ONELASTTHING_SETTINGS=='Einstellungen öffnen')
        assert(A.frame:IsShown())
        A.TogglePopup();assert(not A.frame:IsShown())
        combat=true;A.TogglePopup();assert(not A.frame:IsShown())
        A.ToggleSettings();assert(not (A.settings and A.settings:IsShown()))
        combat=false;A.ToggleSettings();assert(A.settings and A.settings:IsShown())
        A.ToggleSettings();assert(not A.settings:IsShown())

        -- Four pure-API reminders: bag quest-starters, unspent talents, Hearthstone (bank vs missing), unhappy Hunter pet.
        C_Container={
            GetContainerNumSlots=function(bag) return bag==0 and 16 or 0 end,
            GetContainerItemQuestInfo=function(bag,slot)
                if bag==0 and slot==1 then return {isQuestItem=true,questID=7777,isActive=false} end
                return {isQuestItem=false}
            end,
            GetContainerItemInfo=function(bag,slot)
                if bag==0 and slot==1 then return {itemID=5555,itemName='Zerknitterte Notiz'} end
            end,
        }
        UnitCharacterPoints=function() return 2 end
        GetBindLocation=function() return 'Orgrimmar' end
        local hsBags,hsBank=0,1
        C_Item.GetItemCount=function(id,includeBank)
            if id==6948 then return includeBank and (hsBags+hsBank) or hsBags end
            return 0
        end
        UnitExists=function(u) return u=='pet' end
        local petMood=1
        GetPetHappiness=function() return petMood end
        A.db.sources={}
        for _,n in ipairs({'AttuneRows','TurnInRows','ImportantVendorRows','ProfessionRows','SupplyRows','HunterAmmoRows','RepairRows','ClassSpellRows','WeaponRows','FlightRows','TrainerRows','BagRows'}) do
            A.db.sources[n]=false
        end
        local collected=A.Collect(1458,false)
        assert(#collected==4)
        local byKey={};for _,r in ipairs(collected) do byKey[r.key]=r end
        assert(byKey['petmood'] and A.Translate(byKey['petmood'].title)=='Begleiter ist unglücklich')
        assert(byKey['bagquest:7777'] and A.Translate(byKey['bagquest:7777'].title)=='Quest im Inventar starten: Zerknitterte Notiz')
        assert(byKey['hearthstone'] and A.Translate(byKey['hearthstone'].title)=='Ruhestein liegt in der Bank')
        assert(A.Translate(byKey['hearthstone'].detail):find('Aktueller Heimatort: Orgrimmar',1,true))
        assert(byKey['talents'] and A.Translate(byKey['talents'].title)=='Freie Talentpunkte (2)')
        -- Missing Hearthstone (not in bank either), happy pet, spent talents, accepted bag quest all clear cleanly.
        hsBank=0;collected=A.Collect(1458,false)
        byKey={};for _,r in ipairs(collected) do byKey[r.key]=r end
        assert(A.Translate(byKey['hearthstone'].title)=='Ruhestein fehlt in den Taschen')
        hsBags=1;petMood=3;UnitCharacterPoints=function() return 0 end;active={[7777]=true}
        assert(#A.Collect(1458,false)==0)

        -- Settings 9-section cleanup + smart auto-collapse of Addon requirements when all 5 core addons are loaded.
        local allCore={Attune=true,Questie=true,QuestieDB=true,SkillUpForever=true,TrainerSpells=true}
        C_AddOns.IsAddOnLoaded=function(id) return allCore[id] or false end
        A.db.settingsSections={};A.ShowSettings();A.settings.signature=nil;A.BuildSettings()
        assert(#A.settings.sections==9 and not A.settings.sectionByID.addons.open)
        allCore.QuestieDB=false;A.settings.signature=nil;A.BuildSettings()
        assert(A.settings.sectionByID.addons.open)
        -- Explicit user choice overrides auto-collapse/expand.
        A.db.settingsSections.addons=false;A.LayoutSettingsSections()
        assert(not A.settings.sectionByID.addons.open)
    ''')
    print('PASS: borderless default & opt-in borders, active pin sync, row hover/right-click/minimal-click/lock, '
          'WoW keybinds, 4 pure-API reminders (bag quests, talents, Hearthstone, Hunter pet mood), Settings auto-collapse and deDE parity')


if __name__ == '__main__':
    run()
