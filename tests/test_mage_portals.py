"""City-specific Mage training uses the installed portal trainer table, not generic teachers."""
from test_startup import fresh_client


SETUP = '''
    A=OneLastThing
    cities={
        {map=1453,npc=2485,side='Alliance',teleport=3561,portal=10059,tLevel=20,pLevel=40},
        {map=1455,npc=2489,side='Alliance',teleport=3562,portal=11416,tLevel=20,pLevel=40},
        {map=1458,npc=2492,side='Horde',teleport=3563,portal=11418,tLevel=20,pLevel=40},
        {map=1457,npc=4165,side='Alliance',teleport=3565,portal=11419,tLevel=30,pLevel=50},
        {map=1456,npc=5957,side='Horde',teleport=3566,portal=11420,tLevel=30,pLevel=50},
        {map=1454,npc=5958,side='Horde',teleport=3567,portal=11417,tLevel=20,pLevel=40}}
    TrainerSpells_Data={MAGE={}}
    TrainerSpellsPortalTrainers={MAGE={}}
    TrainerSpellsClassTrainers={MAGE={}}
    for _,city in ipairs(cities) do
        for _,level in ipairs({city.tLevel,city.pLevel}) do TrainerSpells_Data.MAGE[level]=TrainerSpells_Data.MAGE[level] or {} end
        TrainerSpells_Data.MAGE[city.tLevel][city.teleport]={faction=city.side,cost=2000}
        TrainerSpells_Data.MAGE[city.pLevel][city.portal]={faction=city.side,cost=15000}
        -- Synthetic coordinates make accidental fallback to the generic trainer obvious.
        TrainerSpellsPortalTrainers.MAGE[#TrainerSpellsPortalTrainers.MAGE+1]={
            npcID=city.npc,faction=city.side=='Horde' and 'H' or 'A',
            names={enUS='Portal teacher '..city.npc,deDE='Portallehrer '..city.npc},
            locations={{uiMapID=city.map,x=20,y=30}}}
        TrainerSpellsClassTrainers.MAGE[#TrainerSpellsClassTrainers.MAGE+1]={
            faction=city.side,names={enUS='Generic teacher'},locations={{uiMapID=city.map,x=80,y=70}}}
    end
    C_Spell={GetSpellInfo=function(id) return {name='Spell '..id} end}
    learned={};A.SpellKnown=function(id) return learned[id]==true end
    function enter(city,level)
        C_Map.GetBestMapForUnit=function() return city.map end
        UnitLevel=function() return level end
        UnitFactionGroup=function() return city.side end
        A.UpdateScope();A.db.filters={};A.db.dismissed={};A.db.trash={};A.db.snoozed={}
    end
'''


def run():
    cases = 0
    for locale in ('enUS', 'deDE'):
        vm = fresh_client('MAGE', locale=locale)
        vm.execute(SETUP)
        for city in range(1, 7):
            for level in (19, 20, 29, 30, 39, 40, 49, 50):
                vm.globals().cityIndex = city
                vm.globals().testLevel = level
                vm.execute('''
                    local city=cities[cityIndex];enter(city,testLevel)
                    local rows={};A.ClassSpellRows(rows,city.map)
                    local expected=(testLevel>=city.tLevel and 1 or 0)+(testLevel>=city.pLevel and 1 or 0)
                    assert(#rows==expected)
                    for _,r in ipairs(rows) do
                        assert(r.spell==city.teleport or r.spell==city.portal)
                        assert(r.map==city.map and r.x==20 and r.y==30)
                        local prefix=testLocale=='deDE' and 'Portallehrer ' or 'Portal teacher '
                        assert(r.detail:find(prefix..city.npc,1,true))
                    end
                ''')
                cases += 1
    print(f'PASS: {cases} Mage portal/teleport cases across six cities, level boundaries and EN/DE; exact portal NPC destinations')

    vm = fresh_client('MAGE')
    vm.execute(SETUP)
    vm.execute('''
        local city=cities[6];enter(city,50)
        local function collect()
            local out={};A.RunProvider('ClassSpellRows',out,city.map,false,true);return out
        end
        A.InvalidateProviders();local rows=collect();assert(#rows==2)
        TrainerSpells_Data.MAGE[1]={[90001]={cost=100}}
        A.InvalidateProviders();rows=collect();assert(#rows==3)
        for _,r in ipairs(rows) do if r.spell==90001 then assert(r.x==80 and r.y==70) end end
        TrainerSpells_Data.MAGE[1]=nil;A.InvalidateProviders()
        learned[city.teleport]=true;A.InvalidateForEvent('SPELLS_CHANGED')
        rows=collect();assert(#rows==1 and rows[1].spell==city.portal)
        A.db.dismissed[rows[1].key]=true;assert(#collect()==0)
        A.db.dismissed={};A.db.trash[rows[1].key]=true;assert(#collect()==0)
        A.db.trash={};TrainerSpells_IsIgnored=function(id) return id==city.portal end
        A.InvalidateProviders();assert(#collect()==0)
        TrainerSpells_IsIgnored=nil;learned={};A.InvalidateProviders()
        LibQuestieDB={Npc={Get=function(id,key) if key=='name' then return 'Native NPC '..id end end}}
        rows=collect();assert(rows[1].detail:find('Native NPC '..city.npc,1,true))
        -- Replacing the portal table invalidates cached destinations immediately.
        TrainerSpellsPortalTrainers={MAGE={{npcID=city.npc,faction='H',names={enUS='Moved portal teacher'},
            locations={{uiMapID=city.map,x=25,y=35}}}}}
        rows=collect();assert(#rows==2 and rows[1].x==25)
        -- A portal teacher can be available without a generic class teacher.
        TrainerSpellsClassTrainers={MAGE={}};A.InvalidateProviders()
        assert(#collect()==2)
        -- Missing portal data never falls back to an unrelated teacher.
        TrainerSpellsPortalTrainers=nil;A.providerHealth={};A.InvalidateProviders()
        rows=collect();assert(#rows==0 and A.providerHealth.ClassSpellRows)
        -- Explicit spell sources remain supported, within the spell's own city.
        A.providerHealth={}
        TrainerSpells_Data.MAGE[20][city.teleport].sourceLocations={{uiMapID=city.map,x=15,y=45,name='Explicit portal teacher'}}
        learned[city.portal]=true;A.InvalidateProviders()
        rows=collect();assert(#rows==1 and rows[1].x==15)
        -- Wrong-faction Mage gets no enemy-city offers.
        learned={};UnitFactionGroup=function() return 'Alliance' end;A.InvalidateProviders()
        assert(#collect()==0)
    ''')
    print('PASS: Mage learned/ignored/skip filtering, native NPC names, cache data replacement, portal-only trainers, '
          'missing-data health, explicit sources and faction isolation')


if __name__ == '__main__':
    run()
