"""Retired taxi nodes and delayed flight-map discovery observations."""
from test_startup import fresh_client


def run():
    vm=fresh_client()
    vm.execute('''
        local A=OneLastThing
        local function pos(x,y) return {GetXY=function() return x,y end} end
        local nodes={
            {nodeID=1,name='zzOLDPowderfuse Port',position=pos(.5,.5)},
            {nodeID=2,name='  ZZold test',position=pos(.5,.5)},
            {nodeID=3,name='Powderfuse Port',position=pos(.5,.5),isUndiscovered=true},
            {nodeID=4,name='Old Town',position=pos(.5,.5),isUndiscovered=false}}
        local states={};local observed,calls
        calls=0
        C_TaxiMap={GetTaxiNodesForMap=function() return nodes end,
            ShouldMapShowTaxiNodes=function() return true end,
            GetAllTaxiNodes=function(map) calls=calls+1;observed=map;return states end}
        GetTaxiMapID=function() return 0 end
        local rows={};A.FlightRows(rows,1458)
        assert(#rows==2 and rows[1].flightID==3 and rows[2].flightID==4)
        assert(not A.db.flightKnown[3] and not A.db.flightKnown[4])
        states={{nodeID=1,state=1},{nodeID=2,state=0}}
        A.ObserveFlights();assert(observed==1458)
        assert(not A.db.flightKnown[1] and not A.db.flightKnown[2])
        -- Opening can fire before the client has populated reachable states.
        states={};event(nil,'TAXIMAP_OPENED');assert(not A.db.flightKnown[3])
        states={{nodeID=3,state=0},{nodeID=4,state=1}}
        timerStep();assert(A.db.flightKnown[3] and A.db.flightKnown[4])
        rows={};A.FlightRows(rows,1458);assert(#rows==0)
        -- A quick close performs the pending read once, not again on its timer.
        states={};event(nil,'TAXIMAP_OPENED')
        states={{nodeID=5,state=1}};event(nil,'TAXIMAP_CLOSED')
        assert(A.db.flightKnown[5]);local before=calls;timerStep();assert(calls==before)
        states={};event(nil,'TAXIMAP_OPENED');before=calls
        event(nil,'PLAYER_LEAVING_WORLD');timerStep();assert(calls==before)
        -- A genuinely renamed/reinstated node is eligible again.
        assert(A.FlightNodeRelevant({nodeID=1,name='Restored Port'}))
        assert(A.FlightNodeRelevant({nodeID=1}))
        -- Ignoring a known path is still only a restorable hide, not discovery.
        A.Refresh=function() end
        A.Trash({key='flight:8',flightID=8,title='Known personally'})
        assert(A.db.trash['flight:8'] and not A.db.flightKnown[8])
        A.db.trash['flight:8']=nil;assert(not A.ReminderHidden({key='flight:8'}))
        -- Retirement clears only an OLT-owned map pin.
        A.FlightNodeRelevant({nodeID=9,name='zzOLD unused'})
        local point={uiMapID=1458,position=pos(.5,.5)};local clears=0
        C_Map.GetUserWaypoint=function() return point end
        C_Map.ClearUserWaypoint=function() clears=clears+1;point=nil end
        A.TrackWaypoint({key='flight:9',flightID=9},1458,.5,.5)
        A.CleanupPin();assert(clears==1 and not A.db.pin)
        point={uiMapID=1458,position=pos(.5,.5)}
        A.TrackWaypoint({key='flight:9',flightID=9},1458,.5,.5)
        point={uiMapID=1458,position=pos(.7,.7)}
        A.CleanupPin();assert(clears==1 and point)
    ''')
    print('PASS: obsolete zzOLD flights excluded, valid Old/Powderfuse names preserved, delayed/quick-close learning, travel cancellation, zero-map fallback and owned-pin cleanup')


if __name__=='__main__':
    run()
