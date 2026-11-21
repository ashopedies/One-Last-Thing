"""Curated progression independent of recipe routes, with actual trainer records."""
from pathlib import Path
from test_startup import fresh_client

ROOT=Path(__file__).resolve().parent.parent


def run():
    for locale in ('enUS','deDE'):
        vm=fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            local id,rank,cap,level=356,125,150,40
            local names={[356]='Fishing',[129]='First Aid',[185]='Cooking'}
            UnitLevel=function() return level end
            GetProfessions=function() return 1 end
            GetProfessionInfo=function() return names[id],nil,rank,cap,nil,nil,id end
            SkillUpForever={API={version=1,Professions=function() return {} end}}
            local owned,known={},{}
            C_Item.GetItemCount=function(item,bank) return owned[item] or 0 end
            C_Item.GetItemNameByID=function(item) return 'Book '..item end
            C_TradeSkillUI={GetRecipeInfo=function(spell) return {learned=known[spell]==true} end}
            IsPlayerSpell=function(spell) return known[spell]==true end
            GetMoney=function() return 100000 end
            A.FindVendor=function() return nil end
            A.scope={map=1434,x=.274,y=.770}
            local function buys(map) local out={};A.ImportantVendorRows(out,map);return out end
            local out=buys(1434)
            assert(#out==1 and out[1].buyItem==16083 and not out[1].buyAhead)
            owned[16083]=1;assert(#buys(1434)==0);owned[16083]=nil
            cap=225;assert(#buys(1434)==0);cap=150
            -- Native profession checks also work if SkillUp is not ready/installed.
            SkillUpForever=nil;assert(#buys(1434)==1)
            A.scope.x=.1;A.scope.y=.1;assert(#buys(1434)==0)
            id=185;A.scope={map=1443,x=.262,y=.698}
            out=buys(1443);assert(#out==1 and out[1].buyItem==16072)
            UnitFactionGroup=function() return 'Alliance' end
            assert(#buys(1443)==0)
            UnitFactionGroup=function() return 'Horde' end
            id=129;A.scope={map=1445,x=.364,y=.304}
            out=buys(1445);assert(#out==2 and out[1].criticalBook and out[2].firstAidManuals)
            local group=out[2]
            assert(group.detail:find('Book 16112',1,true) and group.detail:find('Book 16113',1,true))
            if testLocale=='deDE' then assert(group.title:find('Verbandhandbücher',1,true)) end
            A.db.dismissed[group.key]=true;out=buys(1445);assert(#out==1 and out[1].criticalBook)
            A.db.dismissed={};A.db.trash[group.key]=true;assert(#buys(1445)==1);A.db.trash={}
            local saved=A.MakeTrashRecord(group);assert(saved.firstAidManuals)
            A.db.trash[group.key]=saved;A.ValidateSavedData();assert(A.db.trash[group.key].firstAidManuals);A.db.trash={}
            -- A manual owned in bank or already learned must not be suggested.
            owned[16112]=1;out=buys(1445)
            assert(#out==2 and not out[2].detail:find('Book 16112',1,true) and out[2].cost==5000)
            owned[16112]=nil;known[7929]=true;out=buys(1445)
            assert(#out==2 and not out[2].detail:find('Book 16112',1,true))
            -- One grouped pin stays until every missing manual is owned/learned.
            local point={uiMapID=1445,position={GetXY=function() return .364,.304 end}}
            C_Map.GetUserWaypoint=function() return point end
            C_Map.ClearUserWaypoint=function() point=nil end
            A.TrackWaypoint(group,1445,.364,.304);A.CleanupPin();assert(point)
            owned[16113]=1;A.CleanupPin();assert(not point and not A.db.pin)
            assert(#buys(1445)==1)
            known={};owned={};rank=124;out=buys(1445);assert(#out==1 and out[1].criticalBook)
            rank=125;A.importantOffers={[16112]={map=1445,x=36.4,y=30.4,name='Vendor',price=2000,stock=0}}
            out=buys(1445);assert(#out==2 and not out[2].detail:find('Book 16112',1,true))
            A.importantOffers=nil;GetMoney=function() return 7000 end
            out=buys(1445);assert(#out==0,'unaffordable grouped trip offered')
            A.db.importantVendorBuys=false;GetMoney=function() return 100000 end;assert(#buys(1445)==0)
            A.db.importantVendorBuys=true;A.db.filters['professions/129']=false;assert(#buys(1445)==0)
        ''')
    print('PASS: EN/DE native Fishing/Cooking/First Aid book progression, vendor fallbacks, grouped manuals, '
          'learned/banked/stock/budget/filter/skip/ignore checks, persistence and grouped pin completion')

    for side in ('Horde','Alliance'):
        for pid,qid,mapid,x,y in ((129,6622 if side=='Horde' else 6624,1417 if side=='Horde' else 1445,
                                  73.4 if side=='Horde' else 67.6,36.8 if side=='Horde' else 48.8),
                                 (185,6610,1446,52.6,28),(356,6607,1445,58.6,60)):
            vm=fresh_client()
            vm.globals().pid=pid;vm.globals().qid=qid;vm.globals().mapid=mapid
            vm.globals().qx=x;vm.globals().qy=y;vm.globals().side=side
            vm.execute('''
                local A=OneLastThing
                UnitFactionGroup=function() return side end
                local rank,cap,level=225,225,35
                UnitLevel=function() return level end
                GetProfessions=function() return 1 end
                GetProfessionInfo=function() return 'Profession',nil,rank,cap,nil,nil,pid end
                SkillUpForever={API={version=1,Professions=function() return {} end}}
                A.scope={map=mapid,x=qx/100,y=qy/100}
                local function rows() local out={};A.ProfessionRows(out,mapid);return out end
                local out=rows();assert(#out==1 and out[1].quest==qid and not out[1].finish)
                local quest=out[1]
                assert(A.Category(quest)=='professions' and quest.professionID==pid)
                A.db.dismissed[quest.key]=true;assert(#rows()==0);A.db.dismissed={}
                A.db.trash[quest.key]=true;assert(#rows()==0);A.db.trash={}
                active={[qid]=true};out=rows();for _,r in ipairs(out) do assert(not r.quest) end
                completed={[qid]=true};out=rows();assert(#out==1 and out[1].quest==qid and out[1].finish)
                turned={[qid]=true};out=rows();for _,r in ipairs(out) do assert(not r.quest) end
                active=nil;completed=nil;turned=nil
                level=34;out=rows();for _,r in ipairs(out) do assert(not r.quest) end
                level=35;rank=224;out=rows();for _,r in ipairs(out) do assert(not r.quest) end
                rank=225;cap=300;assert(#rows()==0);cap=225
                A.scope.x=.01;A.scope.y=.01;out=rows();for _,r in ipairs(out) do assert(not r.quest) end
                A.scope.x=qx/100;A.scope.y=qy/100
                -- Installed location data wins over fallback; distant givers cannot be invented.
                A.QuestLocation=function() return nil,nil,nil,nil,true end
                out=rows();for _,r in ipairs(out) do assert(not r.quest) end
            ''')
    print('PASS: independent Triage/Clamlette/Nat Pagle in both factions, acceptance level/skill, '
          'active/ready/completed states, range, installed locations and hidden-reminder coverage')

    for locale in ('enUS','deDE'):
        vm=fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            local rank,cap,level=200,225,35
            UnitLevel=function() return level end
            GetProfessions=function() return 1 end
            GetProfessionInfo=function() return testLocale=='deDE' and 'Verzauberkunst' or 'Enchanting',nil,rank,cap,nil,nil,333 end
            SkillUpForever=nil
            local function rows() local out={};A.ProfessionRows(out,1418);return out end
            for _,pos in ipairs({{.442,.122},{.651,.434}}) do
                A.scope={map=1418,x=pos[1],y=pos[2]}
                local out=rows();assert(#out==1 and out[1].key=='rank:333:225')
                assert(out[1].detail:find('Annora',1,true) and math.abs(out[1].x-pos[1]*100)<.000001)
                if testLocale=='deDE' then assert(out[1].detail:find('Eingang',1,true)) end
                A.db.dismissed[out[1].key]=true;assert(#rows()==0);A.db.dismissed={}
            end
            level=34;assert(#rows()==0);level=35
            rank=199;assert(#rows()==0);rank=200
            A.scope={map=1418,x=.9,y=.9};assert(#rows()==0)
            A.scope={map=1418,x=.442,y=.122};cap=300;assert(#rows()==0);cap=225
            IsInInstance=function() return true,'party' end
            A.manualInstance=false;A.Refresh('Updated',true)
            assert(not A.frame:IsShown(),'Annora support must not auto-open a dungeon checklist')
        ''')
    print('PASS: EN/DE Annora entrance reminder at tested skill 200/level 35, both entrances, '
          'distance, skip, completion and automatic instance suppression')

    vm=fresh_client()
    vm.execute((ROOT/'tests/fixtures/profession_trainers.lua').read_text())
    vm.execute('''
        local A=OneLastThing
        UnitLevel=function() return 40 end
        local ids={Alchemy=171,Tailoring=197,Blacksmithing=164,Engineering=202,Enchanting=333,
            Leatherworking=165,Mining=186,Herbalism=182,Skinning=393}
        local p
        SkillUpForever={API={version=1,Professions=function() return {p} end}}
        local count=0
        for name,trainers in pairs(TrainerSpellsProfessionTrainers) do
            for _,t in ipairs(trainers) do
                UnitFactionGroup=function() return t.faction=='A' and 'Alliance' or 'Horde' end
                local loc=t.locations[1]
                A.scope={map=loc.uiMapID,x=loc.x/100,y=loc.y/100}
                local cap=(t.rank-1)*75
                p={skillLineID=ids[name],name=name,rank=cap-20,maxRank=cap,steps={}}
                local out={};A.ProfessionRows(out,loc.uiMapID)
                assert(#out==1 and out[1].professionRank and out[1].detail:find(t.names.enUS,1,true),t.names.enUS)
                assert(out[1].x==loc.x and out[1].y==loc.y,t.names.enUS..' destination')
                count=count+1
            end
        end
        assert(count>=18)
        -- Confirmed Tailoring requirement changes; disputed Skinning is retained.
        UnitLevel=function() return 34 end
        p={skillLineID=197,name='Tailoring',rank=200,maxRank=225,steps={{kind='train',text='Old rank route'}}}
        A.scope={map=1424,x=.6375,y=.2079}
        local out={};A.ProfessionRows(out,1424);assert(#out==0)
    ''')
    print('PASS: actual trainer snapshot across nine professions, exact destinations, empty-route upgrades '
          'and corrected Tailoring requirement applies to route-supplied steps too')
