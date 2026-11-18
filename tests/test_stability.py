"""Location and interaction regressions in independent, native-like Lua hosts."""
from test_startup import fresh_client


def run():
    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing
        A.scope={map=1413,x=.5,y=.5,key='1413:Ratchet'}
        A.db.nearbyOnly=false
        assert(A.Nearby(1413,1,99) and not A.Nearby(1454,50,50))
        assert(A.ScopeAllows({map=1413,x=1,y=99}))
        assert(not A.ScopeAllows({map=1454,x=50,y=50}))
        A.scope.noFilter=true -- map boundary survives unavailable position API
        assert(not A.ScopeAllows({map=1454,x=50,y=50}))
        assert(A.ScopeAllows({map=1413}) and A.ScopeAllows({inventoryWarning=true}))
        A.scope.noFilter=nil;A.db.nearbyOnly=true
        assert(not A.Nearby(1413,1,99))
        A.scope={map=1458,x=.5,y=.5}
        assert(A.Nearby(1458,1,99) and not A.Nearby(1454,50,50))
        -- A resting player must not receive a remote seller through SupplyRows.
        A.db.nearbyOnly=false;A.db.supplies={[17030]={target=3,minLevel=1}}
        A.FindVendor=function() return {map=1454,x=50,y=50,name='Remote seller',source='Fixture'} end
        local rows={};A.SupplyRows(rows,1458,true);assert(#rows==0)
    ''')
    print('PASS: current-map boundary with radius disabled, missing position API, capitals and remote supply sellers')

    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing
        timers={};A.db.filters={};A.db.collapsed=false
        alpha={key='test:alpha',title='Alpha',map=1458,x=50,y=50}
        beta={key='test:beta',title='Beta',map=1458,x=50,y=50}
        testRows={alpha,beta}
        A.Collect=function()
            local rows={}
            for _,r in ipairs(testRows) do A.Add(rows,r) end
            return rows
        end
        A.Refresh('Manual check',true,true)
        local w=A.frame.rowPool[1]
        w.mouseOver=true;testRows={beta,alpha}
        A.Refresh('Updated',false)
        assert(w.row==alpha and A.pendingDraw and #timers==1)
        A.Refresh('Updated',false);assert(#timers==1) -- coalesced wait
        timerStep();assert(w.row==alpha and A.pendingDraw and #timers==1)
        w.dismiss.scripts.OnClick()
        assert(A.db.dismissed[alpha.key] and not A.db.dismissed[beta.key])
        assert(w.row==beta and not A.pendingDraw) -- explicit action applies immediately
        w.mouseOver=false;timerStep()

        A.db.dismissed={};testRows={alpha,beta};A.Refresh('Manual check',true,true)
        w.more.scripts.OnClick()
        local menu=A.reminderMenu
        testRows={beta,alpha};event(nil,'BAG_UPDATE_DELAYED');timerStep()
        assert(menu:IsShown() and menu.row==alpha and w.row==alpha)
        menu.ignore.scripts.OnClick()
        assert(A.db.trash[alpha.key] and not A.db.trash[beta.key])
        assert(w.row==beta and not A.pendingDraw and not menu:IsShown())
        timerStep()

        A.db.trash={};testRows={alpha,beta};A.Refresh('Manual check',true,true)
        w.mouseOver=true;testRows={beta,alpha};A.Refresh('Updated',false)
        w.snooze.scripts.OnClick()
        assert(A.db.snoozed[alpha.key] and not A.db.snoozed[beta.key] and w.row==beta)
        w.mouseOver=false;timerStep()

        A.db.snoozed={};testRows={alpha,beta};A.Refresh('Manual check',true,true)
        w.more.scripts.OnClick();testRows={beta,alpha};A.Refresh('Updated',false)
        menu.cancel.scripts.OnClick();timerStep()
        assert(w.row==beta and not A.pendingDraw)

        w.mouseOver=true;testRows={alpha,beta};A.Refresh('Updated',false)
        A.frame:Hide();w.mouseOver=false;timerStep()
        assert(not A.frame:IsShown() and not A.pendingDraw)

        A.Refresh('Manual check',true,true);w.more.scripts.OnClick()
        testRows={beta,alpha};A.Refresh('Updated',false)
        C_Map.GetBestMapForUnit=function() return 1454 end
        beta.map=1454;testRows={beta}
        A.Refresh('Entering Orgrimmar',true)
        assert(w.row==beta and not menu:IsShown() and not A.pendingDraw)
        timerStep();assert(w.row==beta)

        w.mouseOver=true;testRows={};A.Refresh('Updated',false)
        assert(not A.db.collapsed and A.pendingDraw)
        w.mouseOver=false;combat=true;timerStep()
        assert(A.pending and not A.db.collapsed) -- wait cannot bypass combat deferral
        combat=false;event(nil,'PLAYER_REGEN_ENABLED');timerStep()
        assert(A.db.collapsed and A.frame.rowCount==0 and not A.pendingDraw)
    ''')
    print('PASS: hover/menu stability, one wait timer, event refresh, exact action targets, '
          'immediate Skip/Hide/Ignore, cancel, close, zone change, completion and combat recovery')

    vm = fresh_client(saved='{collapsed=true,collapseMode="manual"}')
    vm.execute('''
        local A=OneLastThing
        assert(A.frame.rowCount>0 and not A.db.collapsed) -- first city arrival
        A.Collect=function() return {{key='test:arrival',title='Available task'}} end
        local function settle() for i=1,6 do timerStep() end end
        function portal(map,name)
            event(nil,'PLAYER_LEAVING_WORLD')
            C_Map.GetBestMapForUnit=function() return map end
            GetMinimapZoneText=function() return name end
            event(nil,'PLAYER_ENTERING_WORLD');settle()
        end
        A.SetCollapsed(true,'manual')
        GetMinimapZoneText=function() return 'Apothecarium' end
        event(nil,'ZONE_CHANGED');settle()
        assert(A.db.collapsed) -- walking inside a capital respects manual collapse
        portal(1454,'Orgrimmar')
        assert(A.frame:IsShown() and not A.db.collapsed)
        A.SetCollapsed(true,'manual');portal(1413,'Ratchet')
        assert(A.db.collapsed) -- outdoor arrivals preserve the previous preference
        combat=true;portal(1458,'Undercity')
        assert(A.pending and A.db.collapsed)
        combat=false;event(nil,'PLAYER_REGEN_ENABLED');settle()
        assert(A.frame:IsShown() and not A.db.collapsed)
        A.SetCollapsed(true,'manual');A.db.arrival=false
        portal(1454,'Orgrimmar');assert(A.db.collapsed and not A.frame:IsShown())
        A.db.arrival=true;A.db.auto=false
        portal(1458,'Undercity');assert(A.db.collapsed and not A.frame:IsShown())
        A.db.auto=true;A.Collect=function() return {} end
        portal(1456,'Thunder Bluff');assert(A.db.collapsed and A.frame.rowCount==0)
    ''')
    print('PASS: capital arrival expands pending work, portal/combat recovery, '
          'same-city/manual collapse, outdoor visits, empty lists and disabled automatic arrivals')


if __name__ == '__main__':
    run()
