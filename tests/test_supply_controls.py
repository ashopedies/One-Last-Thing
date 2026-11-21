"""One parent/item checkbox hierarchy, with no invisible reagent override."""
from test_startup import fresh_client


def run():
    for locale in ('enUS','deDE'):
        vm=fresh_client(locale=locale,saved='''{
            reagentEconomy=true,categoryMigration=true,trashMigration=true,supplyControlsV2=true,
            filters={['supplies/17030']=false,['quests/dungeonjournal']=true},
            supplies={[17030]={target=5,minLevel=30,classDefault=true},[900001]={target=2}},
            trash={['quest:900002']=true}
        }''')
        vm.execute('''
            local A=OneLastThing
            assert(A.db.reagentEconomy==nil)
            assert(A.db.supplies[17030].target==5 and A.db.supplies[900001].target==2)
            assert(not A.CategoryEnabled('supplies','17030') and A.db.trash['quest:900002'])
            assert(A.SupplyRelevant(17030,A.db.supplies[17030]),'no retired override may suppress Ankhs')
            assert(A.SupplyStatus(17030):find('Disabled',1,true))
            A.ShowSettings()
            local f=A.settings
            local parent,questParent,attune,dungeon
            local indexes={}
            for i,box in ipairs(f.boxes) do
                local text=box.label and box.label.text or ''
                assert(not text:find('Reagent Economy',1,true))
                if text==A.Translate('Supplies') then parent=box;indexes.supplies=i end
                if text==A.Translate('Quests & chains') then questParent=box;indexes.quests=i end
                if text==A.Translate('Scan all unfinished Attune quest chains') then attune=box;indexes.attune=i end
                if text==A.Translate('DungeonJournal dungeon quests (optional)') then dungeon=box;indexes.dungeon=i end
                if box==f.supplyChecks[17030] then indexes.ankh=i end
            end
            assert(parent and questParent and attune and dungeon)
            assert(indexes.supplies<indexes.ankh and indexes.quests<indexes.attune and indexes.quests<indexes.dungeon)
            local item=f.supplyChecks[17030]
            assert(parent.read() and not item.read())
            parent.scripts.OnClick(parent)
            assert(not parent.read() and not item.read())
            parent.scripts.OnClick(parent)
            assert(parent.read() and not item.read(),'parent must retain individual disabled choice')
            item.scripts.OnClick(item)
            assert(item.read() and A.db.supplies[17030].target==5)
            assert(not A.SupplyStatus(17030):find('Disabled',1,true))
            item.scripts.OnClick(item)
            assert(not item.read() and A.db.supplies[17030].target==5)
            A.Init();A.BuildSettings()
            assert(not A.CategoryEnabled('supplies','17030') and A.db.supplies[17030].target==5)
            assert(A.db.supplies[900001].target==2 and A.db.trash['quest:900002'])
            -- Parent categories retain their children's settings across toggles too.
            local enabled=A.db.filters['quests/dungeonjournal']
            questParent.scripts.OnClick(questParent);questParent.scripts.OnClick(questParent)
            assert(A.db.filters['quests/dungeonjournal']==enabled)
        ''')
        alt=fresh_client(locale=locale)
        alt.execute("assert(OneLastThing.db.supplies[17030].target==3 and OneLastThing.CategoryEnabled('supplies','17030'))")
    print('PASS: EN/DE retired reagent override cleanup, preserved per-character targets/item filters/ignored entries, '
          'parent-first quest/supply controls, individual toggles and independent alt defaults')
