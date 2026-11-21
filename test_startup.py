"""Run every startup scenario in a new Lua 5.1 VM, without shared addon globals."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'research/python-deps'))
from lupa.lua51 import LuaRuntime


def fresh_client(class_name='SHAMAN', locale='enUS', saved='nil', combat=False):
    vm = LuaRuntime(unpack_returned_tuples=True)
    vm.execute((ROOT / 'tests/wow_host.lua').read_text())
    vm.globals().testClass = class_name
    vm.globals().testLocale = locale
    vm.globals().combat = combat
    vm.execute('''
        function UnitClass() return testClass,testClass end
        function GetLocale() return testLocale end
        function UnitRace() return 'Orc','Orc' end
        function UnitGUID() return nil end
        C_AddOns.IsAddOnLoaded=function(name) return name=='OneLastThing' end
        C_Map.GetPlayerMapPosition=function() return {GetXY=function() return .5,.5 end} end
        function GetMinimapZoneText() return 'Undercity' end
        function GetSubZoneText() return '' end
        function IsInInstance() return false,'none' end
        function UnitOnTaxi() return false end
        -- Execute one timer generation, so an interaction wait cannot hang a test.
        function timerStep()
            local work=timers;timers={}
            for _,fn in ipairs(work) do fn() end
        end
    ''')
    vm.execute('OneLastThingDB=' + saved)
    toc = (ROOT / 'OneLastThing/OneLastThing.toc').read_text()
    for name in toc.splitlines():
        if name.endswith('.lua'):
            vm.globals().loadAddon((ROOT / 'OneLastThing' / name).read_text())
    vm.execute('''
        event=OneLastThing.eventFrame.scripts.OnEvent
        event(nil,'BAG_UPDATE_DELAYED') -- ignored before SavedVariables initialization
        assert(OneLastThing.db==nil)
        event(nil,'ADDON_LOADED','OneLastThing')
        event(nil,'PLAYER_LOGIN')
        for i=1,5 do timerStep() end
    ''')
    return vm


def run():
    classes = ('WARRIOR', 'PALADIN', 'HUNTER', 'ROGUE', 'PRIEST',
               'SHAMAN', 'MAGE', 'WARLOCK', 'DRUID')
    saves = (
        'nil',
        '"damaged root"',
        '{supplies=false,filters=42,trainers="bad",snoozed={bad="later"},'
        'size=false,fontScale="bad",vendors={[17030]=true}}',
        '{fontScale=1.15,nearbyRadius=1200,headerPosition="bottom",'
        'filters={["quests/turnins"]=true},supplies={[17030]={target=5,minLevel=30}}}',
    )
    cases = 0
    for class_name in classes:
        for locale in ('enUS', 'deDE'):
            for saved in saves:
                vm = fresh_client(class_name, locale, saved)
                vm.execute('''
                    local A=OneLastThing
                    assert(A.db==OneLastThingDB and A.scope.map==1458)
                    assert(type(A.db.supplies)=='table' and type(A.db.filters)=='table')
                    assert(A.ChecksIncomplete()) -- missing data is never "all done"
                    for _,row in ipairs(A.AddonRequirements()) do assert(not row.loaded) end
                    A.ShowSettings();A.BuildSettings();A.BuildSettings()
                    assert(A.settings:IsShown() and not next(A.errors))
                    A.Refresh('Manual check',true,true)
                    assert(A.frame:IsShown() and not next(A.errors))
                    if A.db.nearbyRadius==1200 then
                        assert(A.db.fontScale==1.15 and A.db.headerPosition=='bottom')
                        assert(A.db.filters['quests/turnins']==true)
                    end
                ''')
                cases += 1
    # /reload during combat: initialize data safely; defer the checklist until combat ends.
    vm = fresh_client(combat=True)
    vm.execute('''
        assert(OneLastThing.pending and not OneLastThing.frame)
        combat=false;event(nil,'PLAYER_REGEN_ENABLED')
        for i=1,4 do timerStep() end
        assert(OneLastThing.frame:IsShown() and not next(OneLastThing.errors))
    ''')
    print(f'PASS: {cases} isolated startup cases across nine classes, English/German, '
          'missing dependencies, malformed/preserved saves; combat startup recovery')


if __name__ == '__main__':
    run()
