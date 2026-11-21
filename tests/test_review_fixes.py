"""Review regressions: choose destinations before filtering; trust native state."""
from test_startup import fresh_client


def run():
    for locale in ('enUS', 'deDE'):
        vm = fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            local reads=0
            local by={startedBy={{10,11},{12}},finishedBy={{20},{21}}}
            local spawns={
                [10]={[999]={{90,90},{50,50},{'bad',45}}},[11]={[999]={{51,50}}},[12]={[999]={{52,50}}},
                [20]={[999]={{80,80},{50,50}}},[21]={[999]={{51,50}}}}
            LibQuestieDB={Quest={Get=function(id,key) reads=reads+1;return by[key] end},
                Npc={Get=function(id,key) if key=='spawns' then return spawns[id] elseif key=='name' then return 'NPC '..id end end},
                Object={Get=function(id,key) if key=='spawns' then return spawns[id] elseif key=='name' then return 'Object '..id end end}}
            QuestieLoader={ImportModule=function(_,name)
                if name=='ZoneDB' then return {GetUiMapIdByAreaId=function() return 1413 end} end
                if name=='QuestieDB' then return {IsDoable=function() return true end} end
            end}
            A.scope={map=1413,name='Hub',key='1413:Hub',x=.5,y=.5}
            A.db.nearbyOnly=true;A.db.nearbyRadius=850
            local m,x,y,npc,known,points=A.QuestLocation(111,false,1413)
            assert(m==1413 and x==50 and y==50 and npc=='NPC 10' and known and #points==4)
            m,x,y,npc=A.QuestLocation(111,true,1413);assert(x==50 and npc=='NPC 20')
            -- Invalid/far first NPCs do not block nearer NPCs or objects.
            spawns[10]={[999]={{90,90}}};A.scope.x=.52
            m,x,y,npc=A.QuestLocation(111,false,1413);assert(x==52 and npc=='Object 12')
            -- Cached turn-ins relocate both the map pin target and displayed NPC.
            C_QuestLog.GetNumQuestLogEntries=function() return 1 end
            C_QuestLog.GetInfo=function() return {questID=111,title='Done quest'} end
            A.QuestReady=function() return true end
            A.db.filters['quests/turnins']=true
            A.scope.x=.5;A.InvalidateProviders();A.providerHealth={}
            local out={};A.RunProvider('TurnInRows',out,1413,false,true)
            assert(#out==1 and out[1].x==50 and out[1].detail:find('NPC 20',1,true))
            assert(out[1].provider=='TurnInRows' and out[1].locationSource=='QuestieDB')
            local original=out[1];local before=reads
            A.scope.x=.51;out={};A.RunProvider('TurnInRows',out,1413,false,true)
            assert(#out==1 and out[1].x==51 and out[1].detail:find('Object 21',1,true))
            assert(reads==before and original.x==50,'movement should not rescan or mutate a displayed row')
            -- Attune uses the same immutable candidate replay as ordinary hand-ins.
            A.QuestDone=function() return false end;A.QuestActive=function() return false end
            Attune_Data={attunes={{ID=1,NAME='Dungeon chain',FACTION='Both',TYPE='Dungeon'}},
                steps={{ID=1,ID_ATTUNE=1,TYPE='Pick Up',ID_WOWHEAD='111',FOLLOWS='0',LOCATION='Other'}}}
            A.AttuneToon=function() return {done={},next={['1-1']=true},race='Orc'} end
            A.InvalidateProviders();A.scope.x=.51;out={};A.RunProvider('AttuneRows',out,1413,false,true)
            assert(#out==1 and out[1].x==51)
            before=reads;A.scope.x=.52;out={};A.RunProvider('AttuneRows',out,1413,false,true)
            assert(#out==1 and out[1].x==52 and out[1].detail:find('Object 12',1,true) and reads==before)
            -- Coordinate-less Attune hints stay hints; empty candidate arrays do not erase them.
            local oldLocation=A.QuestLocation;A.QuestLocation=function() return nil,nil,nil,nil,false end
            A.MapName=function() return 'Other' end;A.db.nearbyOnly=false
            A.InvalidateProviders();out={};A.RunProvider('AttuneRows',out,1413,false,true)
            assert(#out==1 and out[1].verify and not out[1].x)
            A.QuestLocation=oldLocation;A.db.nearbyOnly=true
            -- Known destinations elsewhere still prevent an invented local hint.
            m,x,y,npc,known=A.QuestLocation(111,true,1454);assert(not m and known)
            -- Curated hand-in fallback stays separate from pickup locations.
            by.finishedBy=nil
            Attune_Data={questGivers={[2842]={1454,50,50,'Pickup'}}}
            assert(not A.QuestLocation(2842,true,1454))
            m,x=A.QuestLocation(2842,true,1434);assert(m==1434 and x==27.6)
            -- Native coordinates, rather than map percentages, decide closest.
            CreateVector2D=function(x,y) return {GetXY=function() return x,y end} end
            C_Map.GetWorldPosFromMapPos=function(map,pos)
                local px,py=pos:GetXY();return 1,{GetXY=function() return px*10000,py*1000 end}
            end
            A.scope={map=1413,x=.5,y=.5}
            local chosen=A.SelectDestination({{map=1413,x=51,y=50,name='100 yards'},{map=1413,x=50,y=55,name='50 yards'}},1413)
            assert(chosen.name=='50 yards')
            TrainerSpellsClassTrainers={SHAMAN={
                {faction='H',names={enUS='Map-near'},locations={{uiMapID=1413,x=51,y=50}}},
                {faction='H',names={enUS='World-near'},locations={{uiMapID=1413,x=50,y=55}}}}}
            assert(A.LocalClassTrainer(1413).name=='World-near')
            TrainerSpellsProfessionTrainers={Alchemy={
                {rank=3,faction='H',names={enUS='Map-near'},locations={{uiMapID=1413,x=51,y=50}}},
                {rank=3,faction='H',names={enUS='World-near'},locations={{uiMapID=1413,x=50,y=55}}}}}
            assert(A.LocalProfessionTrainer({skillLineID=171,maxRank=150},1413).name=='World-near')
        ''')
    print('PASS: EN/DE nearest valid quest NPC/object/spawn, cached movement with correct NPC text and no rescan/template mutation, map boundaries, Scooty hand-in fallback and native distance ranking')

    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing
        A.scope={map=1413,x=.5,y=.5};A.db.nearbyOnly=true
        A.SpellKnown=function() return false end
        C_Spell={GetSpellInfo=function() return {name='Weapon skill'} end}
        TrainerSpellsWeaponSkills={skills={[123]={classes={SHAMAN=true},trainers={Horde={1,2}},cost=0}},
            trainers={[1]={zoneID=1,x=90,y=90,names={enUS='Far master'}},[2]={zoneID=1,x=50,y=50,names={enUS='Near master'}}},
            zones={[1]={uiMapID=1413}}}
        A.providerHealth={};A.InvalidateProviders()
        local out={};A.RunProvider('WeaponRows',out,1413,false,true)
        assert(#out==1 and out[1].x==50 and out[1].detail:find('Near master',1,true))
        local original=out[1];A.scope.x=.9;A.scope.y=.9
        out={};A.RunProvider('WeaponRows',out,1413,false,true)
        assert(#out==1 and out[1].x==90 and out[1].detail:find('Far master',1,true) and original.x==50)
        -- Native rank/cap replace stale planner fields, preserving route metadata.
        local source={name='Alchemy',skillLineID=171,rank=199,maxRank=225,steps={{kind='train'}},icon=123}
        SkillUpForever={API={version=1,Professions=function() return {source} end}}
        GetProfessions=function() return 1 end
        local rank,cap=200,225
        GetProfessionInfo=function() return 'Alchemy',nil,rank,cap,nil,nil,171 end
        local p=A.ProfessionPlans()[1]
        assert(p.rank==200 and p.maxRank==225 and p.steps==source.steps and p.icon==123 and source.rank==199)
        cap=300;rank=225;p=A.ProfessionPlans()[1];assert(p.rank==225 and p.maxRank==300 and source.maxRank==225)
        -- Eligible artisan training follows native rank 200 immediately.
        rank=200;cap=225;A.scope={map=1435,x=.4853,y=.5585}
        UnitLevel=function() return 35 end
        TrainerSpellsProfessionTrainers={};out={};A.ProfessionRows(out,1435)
        assert(#out==1 and out[1].professionRank and out[1].detail:find('Rogvar',1,true))
    ''')
    print('PASS: nearest weapon trainer survives initial cache capture and movement replay; native profession rank/cap win without mutating planner data or losing route metadata')

    for locale in ('enUS', 'deDE'):
        vm = fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            A.SpellKnown=function() return false end
            C_Spell={GetSpellInfo=function(id) return {name='Spell '..id} end}
            TrainerSpells_Data={SHAMAN={[1]={[111]={rank=1},[112]={rank=1,cost=0},[113]={rank=1,cost=500}}}}
            TrainerSpellsClassTrainers={SHAMAN={{faction='H',names={enUS='Trainer'},locations={{uiMapID=1458,x=50,y=50}}}}}
            local money=0;GetMoney=function() return money end
            local out={};A.ClassSpellRows(out,1458)
            local rows={};for _,r in ipairs(out) do rows[r.spell]=r end
            assert(rows[111].cost==nil and rows[111].detail:find(A.Translate('price unknown'),1,true))
            assert(rows[112].cost==0 and rows[112].detail:find('0c',1,true))
            assert(rows[113].cost==500 and rows[113].detail:find('5s',1,true))
            -- Fallback filtering is labeled without pretending to measure yards.
            C_Map.GetWorldPosFromMapPos=nil
            A.scope={map=1413,key='Hub',x=.5,y=.5}
            assert(A.Nearby(1413,50,50) and A.scope.rangeApproximate)
            local r={map=1413,x=50,y=50};A.UpdateDistances({r})
            assert(r.rangeApproximate and not r.distanceYards and A.DistanceText(r)==A.Translate('Approximate range'))
            A.scope={map=1458,x=.5,y=.5};r.map=1458;A.UpdateDistances({r});assert(not r.rangeApproximate)
            -- Exact distance and disabled radius modes do not claim fallback use.
            CreateVector2D=function(x,y) return {GetXY=function() return x,y end} end
            C_Map.GetWorldPosFromMapPos=function(map,pos) return 1,pos end
            A.scope={map=1413,x=.5,y=.5};r.map=1413;A.UpdateDistances({r})
            assert(r.distanceYards==0 and not r.rangeApproximate)
            A.db.nearbyOnly=false;C_Map.GetWorldPosFromMapPos=nil;A.UpdateDistances({r});assert(not r.rangeApproximate)
        ''')
    print('PASS: EN/DE unknown/free/priced class spells, no nil affordability errors, explicit approximate-radius labels, exact/capital/disabled-radius distinctions')


if __name__ == '__main__':
    run()
