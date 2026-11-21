"""Optional installed-data adapter: no bundled DungeonJournal database required."""
from test_startup import fresh_client


def setup(vm):
    vm.execute('''
        A=OneLastThing
        UnitLevel=function() return 30 end
        C_QuestLog.GetTrivialRange=function() return 10 end
        GetMoney=function() return 0 end
        local required={}
        LibQuestieDB={Quest={Get=function(id,key)
            if key=='requiredLevel' then return required[id] or 10 end
        end}}
        local doable={}
        QuestieLoader={ImportModule=function(_,name)
            if name=='QuestieDB' then return {IsDoable=function(id)
                if doable[id]==nil then return true end
                return doable[id]
            end} end
        end}
        canDo=doable;requirements=required
        local point={mapID=1458,x=.5,y=.5,label='Local giver'}
        local far={mapID=1458,x=.9,y=.9,label='Far giver'}
        local function q(id,extra)
            local t={id=id,name='Dungeon quest '..id,requires=10,level=30,faction='Horde',startMap=point}
            for k,v in pairs(extra or {}) do t[k]=v end
            return t
        end
        makeQuest=q
        ForeverDungeonJournal_NS={DB={Dungeon={quests={q(100),q(101,{faction='Alliance'}),
            q(102,{classOnly='MAGE'}),q(103,{profession='ENGINEERING'}),
            q(104,{requires=31}),q(105,{level=10}),q(106,{startItem={42}}),
            q(107,{hubPlaceholder=true}),q(108,{repeatable=true}),
            q(109,{startMap=far}),q(110,{startMap={mapID=1454,x=.5,y=.5}})}}},
            QUEST_PREREQ_CHAINS={},QUEST_PREREQ_DETAILS={},QUEST_START_MAPS={}}
        A.scope={map=1458,x=.5,y=.5}
        for name in pairs({AttuneRows=true,TurnInRows=true,ImportantVendorRows=true,ProfessionRows=true,
            SupplyRows=true,HunterAmmoRows=true,RepairRows=true,ClassSpellRows=true,WeaponRows=true,
            FlightRows=true,TrainerRows=true,BagRows=true}) do A.db.sources[name]=false end
        function collect(cache)
            A.providerHealth={};local out={};A.RunProvider('DungeonJournalRows',out,1458,false,cache)
            return out
        end
        function enable()
            A.db.filters['quests/dungeonjournal']=true;A.InvalidateProviders()
        end
    ''')


def run():
    for locale in ('enUS','deDE'):
        vm=fresh_client(locale=locale);setup(vm)
        vm.execute('''
            assert(not A.ProviderEnabled('DungeonJournalRows') and #collect()==0)
            local d=ForeverDungeonJournal_NS
            ForeverDungeonJournal_NS=nil;assert(#collect()==0 and not next(A.providerHealth))
            enable();assert(#collect()==0 and A.providerHealth.DungeonJournalRows)
            ForeverDungeonJournal_NS=d;A.InvalidateProviders()
            local out=collect(true)
            assert(#out==2 and out[1].quest==100 and out[2].quest==109) -- capitals are city-wide
            assert(out[1].dungeonPickup and out[1].dungeonJournal and A.Category(out[1])=='quests')
            assert(out[1].subcategory=='dungeonjournal')
            A.db.dismissed['quest:100:start']=true;out=collect(true);assert(#out==1 and out[1].quest==109)
            A.db.dismissed={};A.db.trash['quest:100']=true;out=collect(true);assert(#out==1);A.db.trash={}
            -- Acceptance invalidates cached candidates immediately; completion stays absent.
            active={[100]=true};A.InvalidateForEvent('QUEST_LOG_UPDATE');out=collect(true)
            assert(#out==1 and out[1].quest==109)
            active=nil;turned={[109]=true};A.InvalidateForEvent('QUEST_TURNED_IN');out=collect(true)
            assert(#out==1 and out[1].quest==100);turned=nil
            -- A shared quest ID from Attune produces one entry, regardless of source order.
            local first={key='quest:100:start',quest=100,title='Attune quest',attuneStep={ID_ATTUNE='test'}}
            A.InvalidateProviders();local both={first};A.RunProvider('DungeonJournalRows',both,1458,false,false)
            assert(#both==2 and both[1]==first)
            -- Settings saves the optional choice per character and exposes load status.
            A.ShowSettings()
            local found
            for _,box in ipairs(A.settings.boxes) do
                if box.label and box.label.text==A.Translate('DungeonJournal dungeon quests (optional)') then found=box end
            end
            assert(found and found.read())
            assert(A.settings.dependencyRows.ForeverDungeonJournal)
            local refresh=A.Refresh;A.Refresh=function() end
            found.scripts.OnClick(found);assert(not A.ProviderEnabled('DungeonJournalRows'))
            A.Init();assert(A.db.filters['quests/dungeonjournal']==false)
            found.scripts.OnClick(found);A.Init();assert(A.db.filters['quests/dungeonjournal']==true)
            A.Refresh=refresh
            -- An owned DJ pin is removed when the source is disabled.
            local point={uiMapID=1458,position={GetXY=function() return .5,.5 end}}
            C_Map.GetUserWaypoint=function() return point end
            C_Map.ClearUserWaypoint=function() point=nil end
            A.TrackWaypoint({key='quest:100:start',quest=100,dungeonJournal=true},1458,.5,.5)
            A.db.filters['quests/dungeonjournal']=false;A.CleanupPin();assert(not point and not A.db.pin)
        ''')
    print('PASS: EN/DE optional DungeonJournal setting defaults off, character persistence, dependency status, '
          'missing data health, faction/class/profession/level/gray/item/placeholder/repeatable filters, '
          'quest event invalidation, Skip/Ignore, Attune deduplication and disabled-source pin cleanup')

    vm=fresh_client();setup(vm)
    vm.execute('''
        enable()
        local d=ForeverDungeonJournal_NS
        d.DB={Dungeon={quests={makeQuest(200)}}}
        d.QUEST_PREREQ_CHAINS[200]={{id=201,name='Early prerequisite'},{id=202,name='Next prerequisite'}}
        d.QUEST_PREREQ_DETAILS[201]={level=5,requires=1,map={mapID=1458,x=.5,y=.5}}
        d.QUEST_PREREQ_DETAILS[202]={level=25,requires=10,map={mapID=1458,x=.5,y=.5}}
        local out=collect(false)
        assert(#out==1 and out[1].quest==201 and out[1].gray and out[1].importantReason)
        -- The next step does not appear until the current one is handed in.
        active={[201]=true};out=collect(false);assert(#out==0)
        turned={[201]=true};active=nil;out=collect(false);assert(#out==1 and out[1].quest==202)
        -- Later progress also prevents resurfacing an unrecorded earlier step.
        turned={[202]=true};out=collect(false);assert(#out==1 and out[1].quest==200)
        turned=nil;d.QUEST_PREREQ_DETAILS[201].hubPlaceholder=true
        assert(#collect(false)==0)
        d.QUEST_PREREQ_DETAILS[201].hubPlaceholder=nil
        d.QUEST_PREREQ_DETAILS[201].itemStep=true;assert(#collect(false)==0)
        d.QUEST_GUIDE_CHAINS={[200]=true};out=collect(false);assert(#out==1 and out[1].quest==200)
        -- Unknown or negative Questie eligibility must never be advertised as a pickup.
        canDo[200]=false;assert(#collect(false)==0)
        QuestieLoader=nil;out=collect(false);assert(#out==0 and A.providerHealth.DungeonJournalRows)
    ''')
    print('PASS: ordered prerequisite pickups, active/later progress, gray prerequisites explained, '
          'unfinished hub/item-step exclusion, completion-guide chains and strict Questie availability')

    vm=fresh_client();setup(vm)
    vm.execute('''
        enable()
        local d=ForeverDungeonJournal_NS
        d.DB={Dungeon={quests={makeQuest(300,{startMap={mapID=1413,x=.5,y=.5}})}}}
        A.scope={map=1413,x=.1,y=.1}
        local function run(cache)
            A.providerHealth={};local out={};A.RunProvider('DungeonJournalRows',out,1413,false,cache);return out
        end
        assert(#run(true)==0)
        local cache=A.providerCache.DungeonJournalRows
        A.scope.x=.5;A.scope.y=.5;local out=run(true)
        assert(#out==1 and A.providerCache.DungeonJournalRows==cache,'movement must filter cached coordinates')
        -- Existing Questie destinations take precedence over a conflicting journal map.
        A.QuestLocation=function() return nil,nil,nil,nil,true end
        A.InvalidateProviders();assert(#run(false)==0)
        A.QuestLocation=function() return 1413,50,50,'Verified giver',true end
        out=run(false);assert(#out==1 and out[1].detail:find('Verified giver',1,true))
        -- Source table replacement changes the cache identity; no stale quest IDs remain.
        d.DB={Dungeon={quests={makeQuest(301,{startMap={mapID=1413,x=.5,y=.5}})}}}
        out=run(true);assert(#out==1 and out[1].quest==301)
        A.InvalidateForEvent('SKILL_LINES_CHANGED');assert(not A.providerCache.DungeonJournalRows)
        local a={key='quest:301:start',quest=301,dungeonJournal=true,category='quests',subcategory='dungeonjournal',title='Quest'}
        local record=A.MakeTrashRecord(a);assert(record.dungeonJournal)
        A.db.trash['quest:301']=record;A.ValidateSavedData();assert(A.db.trash['quest:301'].dungeonJournal)
    ''')
    print('PASS: DungeonJournal outdoor range replays cached rows, native destination priority, '
          'source replacement, profession invalidation and ignored-record persistence')
