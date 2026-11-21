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


if __name__ == '__main__':
    run()
