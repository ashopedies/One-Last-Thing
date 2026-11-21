"""Rank upgrades must not depend on a recipe planner's next few steps."""
from test_startup import fresh_client


def run():
    for locale in ('enUS', 'deDE'):
        vm = fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            local p={name=testLocale=='deDE' and 'Alchemie' or 'Alchemy',skillLineID=171,rank=219,maxRank=225,
                steps={{kind='train',spellID=999,text='A routine recipe'}}}
            local level=35
            UnitLevel=function() return level end
            UnitFactionGroup=function() return 'Horde' end
            SkillUpForever={API={version=1,Professions=function(limits)
                assert(limits.steps==25 and limits.recipes==1);return {p}
            end}}
            TrainerSpellsProfessionTrainers={} -- missing Rogvar in the Forever table
            A.scope={map=1435,x=.4853,y=.5585}
            local function collect() local out={};A.ProfessionRows(out,1435);return out end
            local out=collect()
            assert(#out==1 and out[1].professionRank and out[1].capMax==225)
            assert(out[1].key=='rank:171:225' and out[1].map==1435 and out[1].x==48.53)
            assert(out[1].detail:find('Rogvar',1,true))
            if testLocale=='deDE' then
                assert(out[1].title=='Alchemie: Nächste Berufsstufe lernen')
                assert(out[1].detail:find('Neue maximale Fertigkeit: 300',1,true))
            end
            -- No cap warning is resurrected by skipping/ignoring the specific rank.
            A.db.dismissed[out[1].key]=true;assert(#collect()==0);A.db.dismissed={}
            A.db.trash[out[1].key]=true;assert(#collect()==0);A.db.trash={}
            p.rank=199;out=collect();assert(#out==0)
            p.rank=200;assert(#collect()==1)
            level=34;assert(#collect()==0);level=35
            p.rank=219;p.maxRank=300;assert(#collect()==0);p.maxRank=225
            UnitFactionGroup=function() return 'Alliance' end
            for _,row in ipairs(collect()) do assert(not row.professionRank) end
            UnitFactionGroup=function() return 'Horde' end
            A.scope.x=.1;A.scope.y=.1
            for _,row in ipairs(collect()) do assert(not row.professionRank) end
            A.scope.x=.4853;A.scope.y=.5585
            -- Installed data replaces the fallback; don't overwrite upstream tables.
            TrainerSpellsProfessionTrainers={Alchemy={{npcID=1386,rank=4,faction='H',names={enUS='Updated Rogvar'},
                locations={{uiMapID=1435,x=48.6,y=55.8}}}}}
            out=collect();assert(#out==1 and out[1].x==48.6 and out[1].detail:find('Updated Rogvar',1,true))
            assert(#TrainerSpellsProfessionTrainers.Alchemy==1)
            p.steps={{kind='train',text='Artisan',cost=50000,detail='Other zone'}}
            out=collect();assert(#out==1 and out[1].cost==50000,'route and independent check duplicated')
            -- Native gathering state is not lost when SkillUp omits it from crafting routes.
            SkillUpForever.API.Professions=function() return {} end
            GetProfessions=function() return 2 end
            GetProfessionInfo=function() return 'Herbalism',nil,219,225,nil,nil,182 end
            TrainerSpellsProfessionTrainers.Herbalism={{rank=4,faction='H',names={enUS='Herb teacher'},
                locations={{uiMapID=1435,x=48.5,y=55.8}}}}
            out=collect();assert(#out==1 and out[1].professionID==182)
            local point={uiMapID=1435,position={GetXY=function() return .485,.558 end}}
            C_Map.GetUserWaypoint=function() return point end
            C_Map.ClearUserWaypoint=function() point=nil end
            A.TrackWaypoint(out[1],1435,.485,.558)
            A.CleanupPin();assert(point,'arrival must not complete a rank upgrade')
            GetProfessionInfo=function() return 'Herbalism',nil,219,300,nil,nil,182 end
            A.CleanupPin();assert(not point and not A.db.pin,'native rank completion must clear its pin')

        ''')
    print('PASS: EN/DE Alchemy 219 Stonard rank reminder without route steps, eligibility, faction/radius, '
          'skip/ignore, learned cap, upstream override, deduplication and native gathering state')

    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing
        UnitLevel=function() return 40 end
        UnitFactionGroup=function() return 'Alliance' end
        A.scope={map=1425,x=.1339,y=.4349}
        SkillUpForever={API={version=1,Professions=function() return {
            {name='Leatherworking',skillLineID=165,rank=219,maxRank=225,steps={}},
            {name='Cooking',skillLineID=185,rank=219,maxRank=225,steps={}},
            {name='First Aid',skillLineID=129,rank=219,maxRank=225,steps={}},
            {name='Fishing',skillLineID=356,rank=219,maxRank=225,steps={}}
        } end}}
        local out={};A.ProfessionRows(out,1425)
        local ranks={}
        for _,row in ipairs(out) do if row.professionRank then ranks[#ranks+1]=row end end
        assert(#ranks==1 and ranks[1].detail:find('Drakk Stonehand',1,true))
        assert(ranks[1].professionID==165)
    ''')
    print('PASS: missing Artisan Leatherworking trainer fallback; no fabricated trainer rank for secondary quest professions')

    for locale in ('enUS', 'deDE'):
        vm = fresh_client(locale=locale)
        vm.execute(''' 
            local A=OneLastThing
            UnitLevel=function() return 40 end
            UnitFactionGroup=function() return 'Horde' end
            local professions={}
            for _,cat in ipairs(A.categories) do if cat.id=='professions' then
                for id,name in pairs(cat.subs) do professions[#professions+1]={id=tonumber(id),name=name} end
            end end
            assert(#professions==12)
            A.scope={map=1458,x=.5,y=.5};TrainerSpellsProfessionTrainers={}
            local current
            SkillUpForever={API={version=1,Professions=function() return {current} end}}
            local count=0
            for _,p in ipairs(professions) do
                TrainerSpellsProfessionTrainers[p.name]={{rank=4,faction='H',names={enUS='Rank NPC'},
                    locations={{uiMapID=1458,x=50,y=50}}}}
                for _,cap in ipairs({75,150,225}) do
                    local secondary=p.id==129 or p.id==185 or p.id==356
                    if not secondary or cap==75 then
                        current={name=p.name,skillLineID=p.id,rank=cap-20,maxRank=cap,steps={}}
                        local out={};A.ProfessionRows(out,1458)
                        assert(#out==1 and out[1].professionRank and out[1].capMax==cap,p.name..':'..cap)
                        count=count+1
                    end
                end
            end
            assert(count==30)
        ''')
    print('PASS: 60 EN/DE rank-up cases across all twelve professions without any route steps')
