"""A capital's districts share a visit while outdoor localities stay independent."""
from test_startup import fresh_client


def run():
    for capital in (1453, 1454, 1455, 1456, 1457, 1458):
        for locale in ('enUS', 'deDE'):
            vm = fresh_client(locale=locale)
            vm.globals().capital = capital
            vm.execute('''
                local A=OneLastThing
                local map,place,position=capital,'District A',true
                C_Map.GetBestMapForUnit=function() return map end
                C_Map.GetPlayerMapPosition=function()
                    if position then return {GetXY=function() return .5,.5 end} end
                end
                GetMinimapZoneText=function() return place end
                local rows={}
                for _,key in ipairs({'skip','pending','timed','ignored'}) do
                    rows[#rows+1]={key='test:'..key,title=key,map=capital,x=50,y=50}
                end
                A.Collect=function()
                    local result={};for _,row in ipairs(rows) do A.Add(result,row) end;return result
                end
                local function settle() for i=1,6 do timerStep() end end
                event(nil,'PLAYER_LEAVING_WORLD');event(nil,'PLAYER_ENTERING_WORLD');settle()
                local visits=0;local begin=A.BeginVisit
                A.BeginVisit=function() visits=visits+1;begin() end
                A.Dismiss(rows[1]);A.Snooze(rows[3]);A.Trash(rows[4])
                A.SetCollapsed(true,'manual')
                local hides=0;local hide=A.frame.Hide
                A.frame.Hide=function(self) hides=hides+1;return hide(self) end
                for _,name in ipairs({'Trade Quarter','Apothecarium','War Quarter'}) do
                    place=name;event(nil,'ZONE_CHANGED');event(nil,'ZONE_CHANGED_INDOORS');settle()
                    assert(A.scope.key==tostring(capital) and A.scope.name==name)
                    assert(A.LocationName()==name and A.frame.sub:GetText():find(name,1,true))
                    assert(visits==0 and A.db.dismissed['test:skip'])
                    assert(A.frame.rowCount==1 and A.db.collapsed)
                    assert(hides==0)
                end
                -- Temporary map-position loss preserves the same capital visit.
                position=false;A.Refresh('Updated',false)
                assert(A.frame:IsShown() and hides==0)
                position=true;place='District B';event(nil,'ZONE_CHANGED_INDOORS');settle()
                assert(visits==0 and A.db.dismissed['test:skip'])
                assert(hides==0)
                A.frame.Hide=hide
                -- A loading transition within the capital is still one visit.
                event(nil,'PLAYER_LEAVING_WORLD');event(nil,'PLAYER_ENTERING_WORLD');settle()
                assert(visits==0 and A.db.dismissed['test:skip'])
                -- Leaving and returning starts a new visit, preserving other hide types.
                map=1420;place='Outside';event(nil,'ZONE_CHANGED_NEW_AREA');settle()
                map=capital;place='District C';event(nil,'ZONE_CHANGED_NEW_AREA');settle()
                assert(visits==2 and not A.db.dismissed['test:skip'])
                assert(A.db.snoozed['test:timed']>now and A.db.trash['test:ignored'])
                assert(A.frame.rowCount==2)
                -- Outdoor subzones remain separate visits.
                map=1420;place='Outdoor A';event(nil,'ZONE_CHANGED_NEW_AREA');settle()
                local previous=visits;A.db.dismissed['test:outdoor']=true
                place='Outdoor B';event(nil,'ZONE_CHANGED');settle()
                assert(visits==previous+1 and not A.db.dismissed['test:outdoor'])
                assert(A.scope.key=='1420:Outdoor B')
                -- Reload semantics still reset visit skips only.
                A.db.dismissed['test:skip']=true;A.Init()
                assert(not A.db.dismissed['test:skip'] and not A.cityVisitMap)
                assert(A.db.snoozed['test:timed'] and A.db.trash['test:ignored'])
                if testLocale=='deDE' then
                    assert(A.Translate('Districts within a capital count as one visit.')==
                        'Alle Stadtviertel einer Hauptstadt zählen als ein Besuch.')
                end
            ''')
    print('PASS: all six capitals in English/German share district visits; labels, skips, collapse, '
          'position/loading recovery, exit/re-entry, outdoor localities and other hide lifetimes')

    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing
        local map,place,position,taxi,instance=1458,'Trade Quarter',true,false,false
        C_Map.GetBestMapForUnit=function() return map end
        C_Map.GetPlayerMapPosition=function()
            if position then return {GetXY=function() return .5,.5 end} end
        end
        GetMinimapZoneText=function() return place end
        UnitOnTaxi=function() return taxi end
        IsInInstance=function() return instance,instance and 'party' or 'none' end
        local scans=0
        A.Collect=function()
            scans=scans+1
            local rows={};for i=1,12 do rows[i]={key='test:steady'..i,title='Task '..i} end
            A.providerHealth={};return rows
        end
        local function settle() for i=1,6 do timerStep() end end
        A.Refresh('Manual check',true,true)
        local f=A.frame;f.scroll:SetVerticalScroll(55)
        A.ShowFilters(f.filterButton)
        local hides=0;local hide=f.Hide
        f.Hide=function(self) hides=hides+1;return hide(self) end
        place='Apothecarium';event(nil,'ZONE_CHANGED')
        assert(f:IsShown() and hides==0 and A.filterMenu:IsShown())
        position=false;local before=scans
        A.Refresh('Updated',false);settle()
        assert(f:IsShown() and hides==0 and scans==before) -- old positions never used for a scan
        position=true;event(nil,'ZONE_CHANGED_INDOORS');settle()
        assert(f:IsShown() and hides==0 and f.scroll:GetVerticalScroll()==55)
        assert(A.filterMenu:IsShown() and A.scope.name=='Apothecarium')
        A.CloseFilters()
        A.db.auto=false;place='War Quarter';event(nil,'ZONE_CHANGED');settle()
        assert(f:IsShown() and hides==0 and not A.db.auto)
        -- Deliberate closure cancels an in-flight recovery.
        position=false;A.Refresh('Updated',false)
        f.close:GetScript('OnClick')();position=true;settle()
        assert(not f:IsShown())
        -- Different maps, missing map identity, flights and instances still clear immediately.
        A.db.auto=true
        for _,kind in ipairs({'outside','unknown','taxi','instance'}) do
            map=1458;taxi=false;instance=false;A.Refresh('Manual check',true,true)
            if kind=='outside' then map=1420
            elseif kind=='unknown' then map=nil
            elseif kind=='taxi' then taxi=true
            else instance=true end
            event(nil,'ZONE_CHANGED_NEW_AREA')
            assert(not f:IsShown(),kind..' retained an outdated checklist')
        end
    ''')
    print('PASS: capital checklist stays visible without stale scans, preserves scroll/filter/manual display, '
          'and still clears on closure, map changes, missing identity, taxi or instances')


if __name__ == '__main__':
    run()
