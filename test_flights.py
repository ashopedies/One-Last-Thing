"""Forever flight maps can use parent-map coordinates and unreliable learned flags."""
from test_startup import fresh_client


def run():
    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing
        local zone=9999 -- fixture for a new Forever zone; not a production map ID
        local function pos(x,y) return {GetXY=function() return x,y end} end
        C_Map.GetBestMapForUnit=function() return zone end
        C_Map.GetMapInfo=function(id)
            return {name=id==zone and 'Fixture Riverglades' or 'Eastern Kingdoms',parentMapID=id==zone and 1415 or 0,mapType=id==zone and 3 or 2}
        end
        C_Map.GetPlayerMapPosition=function() return pos(.596,.451) end
        C_Map.GetMapRectOnMap=function(map,parent)
            assert(map==zone and parent==1415);return .4,.6,.2,.4
        end
        local queried,observed={}
        C_TaxiMap={
            ShouldMapShowTaxiNodes=function(id) return id==1415 end,
            GetTaxiNodesForMap=function(id)
                queried[#queried+1]=id
                if id==zone then return {} end
                assert(id==1415)
                return {
                    {nodeID=100,name='Fixture Rogmar',faction=1,isUndiscovered=false,position=pos(.5192,.2902)},
                    {nodeID=101,name='Distant same-zone',faction=1,isUndiscovered=true,position=pos(.58,.38)},
                    {nodeID=102,name='Enemy',faction=2,isUndiscovered=true,position=pos(.5192,.2902)},
                    {nodeID=103,name='Another zone',faction=1,isUndiscovered=true,position=pos(.1,.1)}}
            end,
            GetAllTaxiNodes=function(id)
                observed=id;return {{nodeID=100,state=0},{nodeID=104,state=1},{nodeID=105,state=2}}
            end}
        A.UpdateScope();A.db.collapsed=false;A.db.nearbyOnly=true
        local rows={};A.FlightRows(rows,zone)
        assert(#rows==1 and rows[1].flightID==100 and rows[1].verify)
        assert(math.abs(rows[1].x-59.6)<.001 and math.abs(rows[1].y-45.1)<.001)
        assert(not A.db.flightKnown[100]) -- false map flag is not proof of learning
        A.db.nearbyOnly=false;rows={};A.FlightRows(rows,zone)
        assert(#rows==2) -- still excludes the enemy and points outside this zone
        A.db.nearbyOnly=true
        GetTaxiMapID=function() return 1415 end
        event(nil,'TAXIMAP_OPENED')
        assert(observed==1415 and A.db.flightKnown[100] and A.db.flightKnown[104])
        assert(not A.db.flightKnown[105]) -- Unreachable says nothing about discovery
        rows={};A.FlightRows(rows,zone);assert(#rows==0)
        -- Reaching the master does not clear a pin; confirmed learning does.
        A.db.flightKnown[100]=nil
        local point={uiMapID=zone,position=pos(.596,.451)}
        C_Map.GetUserWaypoint=function() return point end
        local clears=0;C_Map.ClearUserWaypoint=function() clears=clears+1;point=nil end
        A.TrackWaypoint({key='flight:100',flightID=100},zone,.596,.451)
        A.CleanupPin();assert(clears==0 and A.db.pin)
        A.ObserveFlights();A.CleanupPin();assert(clears==1 and not A.db.pin)
        -- Use the proven parent map if GetTaxiMapID is absent.
        GetTaxiMapID=nil;A.ObserveFlights();assert(observed==1415)
        -- The alternative world-coordinate projection also preserves the zone.
        C_Map.GetMapRectOnMap=nil
        CreateVector2D=function(x,y) return {x=x,y=y,GetXY=function() return x,y end} end
        C_Map.GetWorldPosFromMapPos=function(map,p)
            local x,y=p.x,p.y
            if map==zone then x=.4+x*.2;y=.2+y*.2 end
            x=x*10000;y=y*10000
            return 1,{x=x,y=y,GetXY=function() return x,y end}
        end
        C_Map.GetMapPosFromWorldPos=function(continent,p,map)
            return map,pos((p.x/10000-.4)/.2,(p.y/10000-.2)/.2)
        end
        A.db.flightKnown={};rows={};A.FlightRows(rows,zone)
        assert(#rows==1 and math.abs(rows[1].x-59.6)<.001)
        C_Map.GetMapPosFromWorldPos=nil;A.providerUnavailable=nil
        A.CheckUnavailable=function(reason) A.providerUnavailable=reason end
        rows={};A.FlightRows(rows,zone)
        assert(#rows==0 and A.providerUnavailable) -- never treat continent points as zone points
    ''')
    print('PASS: parent flight map selection, local projection/range, faction and zone filtering, '
          'unreliable discovery flag, observed knowledge, completion-only pin cleanup and missing geometry')

    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing
        -- User's actual diagnostic: OLT 2548 1415 false 36. Geometry below is
        -- synthetic so the test does not claim to capture real node positions.
        local function pos(x,y) return {GetXY=function() return x,y end} end
        C_Map.GetBestMapForUnit=function() return 2548 end
        C_Map.GetMapInfo=function(id)
            return {name=id==2548 and 'Riverglades' or 'Eastern Kingdoms',
                parentMapID=id==2548 and 1415 or 0,mapType=id==2548 and 3 or 2}
        end
        C_Map.GetPlayerMapPosition=function() return pos(.596,.451) end
        C_Map.GetMapRectOnMap=function(map,parent)
            assert(map==2548 and parent==1415);return .4,.6,.2,.4
        end
        local nodes={{nodeID=100,name='Fixture Rogmar',faction=1,isUndiscovered=true,position=pos(.5192,.2902)}}
        for i=2,36 do nodes[i]={nodeID=100+i,name='Other zone',faction=1,isUndiscovered=true,position=pos(.1,.1)} end
        local parentEmpty=false
        C_TaxiMap={ShouldMapShowTaxiNodes=function() return false end,
            GetTaxiNodesForMap=function(map)
                if map==1415 and parentEmpty then return {} end
                return nodes
            end}
        A.UpdateScope();A.providerHealth={}
        local rows={};A.RunProvider('FlightRows',rows,2548,false,true)
        assert(#rows==1 and rows[1].flightID==100 and rows[1].map==2548)
        assert(math.abs(rows[1].x-59.6)<.001 and not A.providerHealth.FlightRows)
        assert(not next(A.db.flightKnown)) -- no flight-master interaction required
        A.InvalidateProviders({'FlightRows'});parentEmpty=true;rows={}
        A.RunProvider('FlightRows',rows,2548,false,true)
        assert(#rows==1 and not A.providerHealth.FlightRows)
        -- An actual empty-data case remains visible and diagnostic.
        nodes={};A.InvalidateProviders({'FlightRows'});rows={}
        A.RunProvider('FlightRows',rows,2548,false,true)
        assert(#rows==0 and A.providerHealth.FlightRows)
        assert(A.status.Flights:find('2548:0/false',1,true))
    ''')
    print('PASS: Rogmar 2548/1415 false-display 36-node diagnostic, parent/child data fallback, '
          'pre-discovery reminder, provider health and empty-data diagnostics')

    vm = fresh_client(saved='''{flightKnown={[100]=true},fontScale=1.1,
        supplies={[17030]={target=5,minLevel=30}},trash={['flight:99']=true}}''')
    vm.execute('''
        local A=OneLastThing
        assert(not next(A.db.flightKnown) and A.db.flightKnowledgeVersion==2)
        assert(A.db.fontScale==1.1 and A.db.supplies[17030].target==5 and A.db.trash['flight:99'])
        A.db.flightKnown[100]=true;A.Init()
        assert(A.db.flightKnown[100]) -- verified cache survives subsequent initialization
    ''')
    print('PASS: legacy unreliable flight cache reconfirmation preserves character preferences, supplies and ignored reminders')


if __name__ == '__main__':
    run()
