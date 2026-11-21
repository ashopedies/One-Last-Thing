"""Routine trainer recipes never become individual errands; progression stays visible."""
from test_startup import fresh_client


def run():
    for locale in ('enUS', 'deDE'):
        vm = fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            local reads=0
            UnitGUID=function() return 'Creature-0-0-0-0-9999-00000001' end
            UnitName=function(unit) return unit=='npc' and 'Profession teacher' or 'Test' end
            IsTradeskillTrainer=function() return true end
            GetNumTrainerServices=function() return 1000 end
            GetTrainerServiceInfo=function() reads=reads+1;return 'Recipe '..reads,'available' end
            GetTrainerServiceCost=function() return 1000 end
            GetTrainerServiceSkillReq=function() return nil end
            -- Even metadata-free recipe lists are excluded before reading every row.
            A.ObserveTrainer()
            assert(reads==0)
            local entry=A.db.trainers['1458:9999']
            assert(entry.professionTrainer and not next(entry.services))
            local out={};A.TrainerRows(out,1458);assert(#out==0)
            -- An old saved recipe list is retired without touching preferences.
            for i=1,1000 do entry.services['name:'..i]={name='Recipe '..i,rank='',cost=100} end
            A.db.dismissed.keep=true;A.db.trash.keep=true;A.db.supplies[17030].target=5
            out={};A.TrainerRows(out,1458)
            assert(#out==0 and not next(entry.services))
            assert(A.db.dismissed.keep and A.db.trash.keep and A.db.supplies[17030].target==5)

            -- Native class observations still work and retain individual gold decisions.
            IsTradeskillTrainer=function() return false end
            UnitGUID=function() return 'Creature-0-0-0-0-8888-00000001' end
            UnitName=function(unit) return unit=='npc' and 'Class teacher' or 'Test' end
            GetNumTrainerServices=function() return 1 end
            GetTrainerServiceInfo=function() return 'Class spell','available' end
            C_TooltipInfo={GetTrainerService=function() return {id=12345} end}
            A.ObserveTrainer();out={};A.TrainerRows(out,1458)
            assert(#out==1 and out[1].spell==12345)
            A.Dismiss(out[1]);out={};A.TrainerRows(out,1458);assert(#out==0)

            -- Service metadata catches recipes even if trainer type is unavailable.
            IsTradeskillTrainer=nil
            GetTrainerServiceSkillReq=function() return testLocale=='deDE' and 'Alchemie' or 'Alchemy' end
            C_TooltipInfo.GetTrainerService=function() return {id=23456} end
            A.ObserveTrainer()
            assert(not A.db.trainers['1458:8888'].services['spell:23456'])
        ''')
    print('PASS: EN/DE tradeskill observation skips 1000 recipes without scanning them, retires old offers, '
          'preserves preferences and individual class-spell decisions, and handles profession metadata')

    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing
        TrainerSpellsProfessionTrainers={Alchemy={{npcID=777,names={enUS='Alchemist',deDE='Alchimist'}}}}
        TrainerSpellsBuiltin_Profession={Alchemy={[1]={[101]={cost=100}}}}
        TrainerSpells_ProfessionData={Cooking={[1]={Soup={spellID=102,cost=100}}}}
        local function offer(name,id,professionID)
            return {name=name,rank='',spell=id,professionID=professionID,cost=100}
        end
        A.db.trainers={
            npc={map=1458,x=50,y=50,name='Unknown',npcID=777,services={a=offer('Old no-ID recipe')}},
            name={map=1458,x=50,y=50,name='Alchimist',services={b=offer('Old no-ID recipe')}},
            collision={map=1458,x=50,y=50,npcID=888,name='Alchimist',services={g=offer('Unrelated class spell',105)}},
            mixed={map=1458,x=50,y=50,name='Unknown legacy teacher',services={
                c=offer('Alchemy recipe',101),d=offer('Cooking recipe',102),
                e=offer('Metadata recipe',103,171),f=offer('Class spell',104)}}}
        local rows={};A.TrainerRows(rows,1458)
        local kept={};for _,row in ipairs(rows) do kept[row.spell]=true end
        assert(#rows==2 and kept[104] and kept[105])
        assert(not next(A.db.trainers.npc.services) and not next(A.db.trainers.name.services))
        assert(not A.db.trainers.mixed.services.c and not A.db.trainers.mixed.services.d)
        -- A previously selected recipe's owned waypoint is removed as obsolete.
        local point={uiMapID=1458,position={GetXY=function() return .5,.5 end}}
        C_Map.GetUserWaypoint=function() return point end
        C_Map.ClearUserWaypoint=function() point=nil end
        A.TrackWaypoint({key='train:spell:101',spell=101},1458,.5,.5)
        A.CleanupPin();assert(not point and not A.db.pin)
    ''')
    print('PASS: legacy profession NPC IDs/localized names, bundled/observed recipe IDs and metadata are filtered; '
          'class offers survive and obsolete owned recipe pins clear')

    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing
        GetMoney=function() return 20000 end
        local professions={
            {name='First Aid',skillLineID=129,rank=145,maxRank=150,steps={}},
            {name='Alchemy',skillLineID=171,rank=145,maxRank=150,steps={
                {kind='train',text='Train rank',cost=1000},
                {kind='train',questID=123,text='Rank quest'},
                {kind='train',spellID=999,itemID=888,text='Routine recipe'},
                {kind='buy',itemID=777,text='Buy recipe materials'}}}}
        SkillUpForever={API={version=1,Professions=function() return professions end}}
        TrainerSpellsProfessionTrainers={Alchemy={{npcID=777,rank=3,faction='H',names={enUS='Rank teacher'},
            locations={{uiMapID=1458,x=50,y=50}}}}}
        A.FindVendor=function() return {map=1458,x=50,y=50,name='Book vendor'} end
        A.QuestLocation=function() return 1458,50,50,'Rank questgiver',true end
        local rows={};A.ImportantVendorRows(rows,1458);A.ProfessionRows(rows,1458)
        local book,rank,quest
        for _,row in ipairs(rows) do
            book=book or row.criticalBook;rank=rank or row.professionRank;quest=quest or row.quest==123
            assert(not row.spell and not (row.buyItem==888))
        end
        assert(book and rank and quest)
    ''')
    print('PASS: essential profession books, rank upgrades and progression quests remain; route recipes/materials stay excluded')


if __name__ == '__main__':
    run()
