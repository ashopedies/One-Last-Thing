"""Responsive controls and non-destructive map interactions, in fresh Lua VMs."""
from test_startup import fresh_client


def run():
    for locale in ('enUS', 'deDE'):
        vm = fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            A.Draw({{key='ui:test',title='Test',map=1458,x=50,y=50}},'Test')
            local f=A.frame
            A.db.collapsed=false
            for _,glyph in ipairs({6.5,12,16}) do
                for _,scale in ipairs({.8,1,1.3}) do
                    A.db.fontScale=scale
                    for _,b in ipairs({f.restoreButton,f.checkButton,f.settingsButton,f.smaller,f.larger}) do
                        local fs=b:GetFontString()
                        fs.GetStringWidth=function(self) return #self:GetText()*glyph*scale end
                        fs.GetStringHeight=function() return 12*scale end
                        b.SetPoint=function(self,_,_,_,x,y) self.testX=x;self.testY=y end
                    end
                    for _,width in ipairs({360,440,950}) do
                        f:SetWidth(width);A.LayoutBottomBar()
                        local previous={}
                        for _,b in ipairs({f.restoreButton,f.checkButton,f.settingsButton,f.smaller,f.larger}) do
                            assert(b:GetWidth()>=b:GetFontString():GetStringWidth()+14)
                            assert(b.testX+b:GetWidth()<=width-20)
                            local right=previous[b.testY]
                            assert(not right or b.testX>=right+5)
                            previous[b.testY]=b.testX+b:GetWidth()
                        end
                        assert(f.smaller.testY==f.larger.testY)
                    end
                end
            end
            for _,mode in ipairs({'default','compact','minimal'}) do
                A.db.rowMode=mode;A.db.fontScale=1;A.Layout()
                local base=f.widgets[1]:GetHeight()
                A.db.fontScale=1.3;A.Layout()
                assert(mode=='minimal' and f.widgets[1]:GetHeight()==27 or f.widgets[1]:GetHeight()>base)
            end
            A.ShowFilters(f.filterButton);local m=A.filterMenu
            m.IsMouseOver=function() return true end;f.filterButton.IsMouseOver=function() return false end
            m:GetScript('OnEvent')(m,'GLOBAL_MOUSE_DOWN');assert(m:IsShown())
            m.IsMouseOver=function() return false end
            m:GetScript('OnEvent')(m,'GLOBAL_MOUSE_DOWN');assert(not m:IsShown())
            A.ShowFilters(f.filterButton);f:GetScript('OnDragStart')(f);assert(not m:IsShown())
            A.ShowFilters(f.filterButton);combat=true;f:GetScript('OnDragStart')(f);assert(m:IsShown());combat=false;A.CloseFilters()
        ''')
    print('PASS: EN/DE bottom controls fit measured wide fonts, wrap without overlap, keep +/- together; scaled rows, outside-click filters and combat-safe dragging')
    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing
        local current
        C_Map.GetUserWaypoint=function() return current end
        C_Map.GetUserWaypointHyperlink=nil
        C_Map.ClearUserWaypoint=function() current=nil end
        local function point(x) return {uiMapID=1458,position={GetXY=function() return x,.5 end}} end
        local row={key='pin:test',map=1458,x=50,y=50}
        current=point(.5);A.TrackWaypoint(row,1458,.5,.5)
        assert(A.IsPinnedRow(row))
        assert(not A.ClearOwnedPin({key='other'}) and current)
        C_Map.ClearUserWaypoint=function() end
        assert(not A.ClearOwnedPin(row) and A.db.pin)
        C_Map.ClearUserWaypoint=function() error('blocked') end
        assert(not A.ClearOwnedPin(row) and A.db.pin)
        local cleared=0
        C_Map.ClearUserWaypoint=function() cleared=cleared+1;current=nil end
        current=point(.7)
        assert(A.ClearOwnedPin(row) and current and cleared==0 and not A.db.pin)
        current=point(.5);A.TrackWaypoint(row,1458,.5,.5)
        assert(A.ClearOwnedPin(row) and current==nil and cleared==1 and not A.db.pin)
        local count=0
        C_Map.GetWorldPosFromMapPos=function(_,pos) count=count+1;return 1,pos end
        CreateVector2D=function(x,y) return {GetXY=function() return x*10000,y*10000 end} end
        A.scope={map=1413,x=.5,y=.5};A.db.nearbyOnly=true
        A.worldCoordCache={}
        A.Nearby(1413,50,50);A.Nearby(1413,50,50);assert(count==1)
        A.worldCoordCache=nil
        A.Nearby(1413,50,50);assert(count==3)
        local builds=0
        A.ShowSettings();A.BuildSettings=function() builds=builds+1 end
        A.Refresh=function() end
        local id=next(A.db.supplies)
        for i=1,20 do event(nil,'GET_ITEM_INFO_RECEIVED',id) end
        assert(builds==0);timerStep();assert(builds==1)
    ''')
    print('PASS: owned pin clears, failure/no-op retries, manual replacements survive; per-collection coordinate reuse and batched item-data settings refresh')
    vm = fresh_client()
    vm.execute('''
        local A=OneLastThing
        A.Draw({{key='theme:test',title='Test'}},'Test')
        local fs=A.frame.settingsButton:GetFontString()
        local other=A.frame.checkButton:GetFontString()
        fs.SetTextColor=function(self,r,g,b,a) self.rgb={r,g,b};self.alpha=a end
        other.SetTextColor=fs.SetTextColor
        for _,theme in ipairs({'blizzard','class','pop','original'}) do
            A.SetTheme(theme)
            local expected=theme=='original' and A.originalColors.training or A.palette[1]
            for i=1,3 do assert(fs.rgb[i]==expected[i]) end
            assert(fs.alpha==1)
            assert(fs.rgb[1]~=other.rgb[1] or fs.rgb[2]~=other.rgb[2] or fs.rgb[3]~=other.rgb[3])
            A.AdjustFontSize(5);A.LayoutBottomBar()
            for i=1,3 do assert(fs.rgb[i]==expected[i]) end
        end
    ''')
    print('PASS: Settings uses an existing distinct accent in all four themes, and retains it across live theme/font/layout changes')


if __name__ == '__main__':
    run()
