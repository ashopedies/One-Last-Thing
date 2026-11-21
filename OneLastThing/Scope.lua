local _,A=...
-- Capital map IDs, not localized names or the surrounding outdoor zones.
local capitals={[1453]=true,[1454]=true,[1455]=true,[1456]=true,[1457]=true,[1458]=true}
function A.IsCapitalMap(map) return capitals[map]==true end
function A.InTransit()
    return A.Safe('flight state',UnitOnTaxi,'player')==true
end
local function localName(map)
    local minimap=A.Safe('minimap zone name',GetMinimapZoneText)
    if type(minimap)=='string' and minimap~='' then return minimap end
    local sub=A.Safe('subzone name',GetSubZoneText)
    if type(sub)=='string' and sub~='' then return sub end
    return A.MapName(map)
end
function A.UpdateScope()
    A.scope=nil
    if A.InTransit() then return nil end
    local map=A.Map();if not map then return end
    if not A.IsCapitalMap(map) then A.cityVisitMap=nil end
    local name=localName(map)
    local getPos=C_Map and C_Map.GetPlayerMapPosition
    local pos=getPos and A.Safe('local player position',getPos,map,'player')
    -- A present API with no position is usually loading/travel. Wait rather
    -- than display a stale, whole-zone list during a flight or map transition.
    if getPos and not pos then A.status.Location='Waiting for local position';return nil end
    local x,y
    if pos then
        x,y=pos:GetXY()
        if x<0 or x>1 or y<0 or y>1 or (x==0 and y==0) then return nil end
    end
    local key=A.IsCapitalMap(map) and tostring(map) or (tostring(map)..':'..tostring(name))
    A.scope={map=map,name=name,x=x,y=y,key=key,noFilter=not getPos}
    if not A.IsCapitalMap(map) and A.db.nearbyOnly~=false and not A.scope.noFilter then
        local _,approximate=A.DestinationDistance(map,(x or 0)*100,(y or 0)*100)
        A.scope.rangeApproximate=approximate or nil
    end
    A.status.Range=A.scope.rangeApproximate and A.Translate('Range estimated from map coordinates; yard conversion unavailable.') or nil
    A.status.Location=name..(A.IsCapitalMap(map) and ' | city-wide reminders' or (A.db.nearbyOnly==false and ' | whole map' or (' | nearby reminders: '..(A.db.nearbyRadius or 850)..' yards')))
    if A.scope.rangeApproximate then A.status.Location=A.status.Location..' | '..A.Translate('Approximate range') end
    return A.scope
end
function A.LocationName()
    return (A.scope and A.scope.name) or localName(A.Map())
end
local function world(map,x,y)
    if not (C_Map and C_Map.GetWorldPosFromMapPos and CreateVector2D) then return end
    local cache=A.worldCoordCache
    local key=cache and (tostring(map)..':'..tostring(x)..':'..tostring(y))
    if key and cache[key] then return unpack(cache[key]) end
    local continent,p=A.Safe('local world position',C_Map.GetWorldPosFromMapPos,map,CreateVector2D(x,y))
    if p then
        local wx,wy=p:GetXY()
        if key then cache[key]={continent,wx,wy} end
        return continent,wx,wy
    end
end
local function coordinate(value) return type(value)=='number' and value==value and value>=0 and value<=100 end
function A.ValidDestination(p)
    return type(p)=='table' and type(p.map)=='number' and p.map>0 and p.map<math.huge and coordinate(p.x) and coordinate(p.y)
end
-- The distance estimate retains the existing map fallback, but callers can
-- distinguish its units from an actual world-coordinate measurement.
function A.DestinationDistance(map,x,y)
    local scope=A.scope
    if not scope or scope.map~=map or type(scope.x)~='number' or type(scope.y)~='number' then return end
    local ca,ax,ay=world(map,scope.x,scope.y)
    local cb,bx,by=world(map,x/100,y/100)
    if ca and ca==cb and ax and bx then return math.sqrt((ax-bx)^2+(ay-by)^2),false end
    return math.sqrt((scope.x-x/100)^2+(scope.y-y/100)^2)*850/.045,true
end
function A.SelectDestination(points,map)
    local best,bestDistance,bestInside
    local px,py=.5,.5
    if A.scope and A.scope.map==map then px,py=A.scope.x or .5,A.scope.y or .5 end
    for _,p in ipairs(points or {}) do
        if A.ValidDestination(p) and p.map==map then
            local distance=A.DestinationDistance(map,p.x,p.y) or math.sqrt((px-p.x/100)^2+(py-p.y/100)^2)*850/.045
            local inside=A.Nearby(map,p.x,p.y)
            if not best or (inside and not bestInside) or (inside==bestInside and distance<bestDistance) then
                best,bestDistance,bestInside=p,distance,inside
            end
        end
    end
    return best
end
function A.PlaceDestination(row,map)
    if not row.destinations then return row end
    local target=A.SelectDestination(row.destinations,map)
    if not target then return end
    local placed={};for key,value in pairs(row) do placed[key]=value end
    placed.map,placed.x,placed.y=target.map,target.x,target.y
    placed.locationSource=target.locationSource or row.locationSource
    if row.destinationSuffix then placed.detail=(row.destinationPrefix or '')..(target.name or row.destinationName or '')..row.destinationSuffix end
    return placed
end
function A.Nearby(map,x,y)
    local scope=A.scope
    local current=scope and scope.map
    if current and map~=current then return false end
    if not scope or scope.noFilter or A.db.nearbyOnly==false then return true end
    if not coordinate(x) or not coordinate(y) then return false end
    if A.IsCapitalMap(map) then return true end
    local distance,approximate=A.DestinationDistance(map,x,y)
    if approximate then
        scope.rangeApproximate=true
        A.status.Range=A.Translate('Range estimated from map coordinates; yard conversion unavailable.')
    end
    return distance~=nil and distance<=(A.db.nearbyRadius or 850)
end
function A.ScopeAllows(row)
    local s=A.scope
    if row.map then return A.Nearby(row.map,row.x,row.y) end
    if not s or s.noFilter or A.db.nearbyOnly==false then return true end
    -- General inventory/cap warnings have no claimed physical destination.
    return not row.quest and not row.skill
end

function A.ClearLocation(recover,previous)
    local scope=previous or A.scope
    if recover and A.frame and A.frame:IsShown() and not A.loadingWorld and not A.InTransit() and not A.AutomaticSuppressed() then
        A.scopeRecovery={key=scope and scope.key,manual=A.db.auto==false}
        -- Every district shares this city's destinations. Keep the existing
        -- display while fresh coordinates settle; RequireScope still returns
        -- nil on missing data so Refresh cannot collect with stale positions.
        if scope and A.IsCapitalMap(scope.map) and A.Map()==scope.map then
            A.scope=scope
            return
        end
    elseif not recover then A.scopeRecovery=nil end
    A.scope=nil
    if A.frame then A.frame:Hide() end
end
function A.RequireScope()
    if A.loadingWorld then A.ClearLocation();return end
    local previous=A.scope
    local scope=A.UpdateScope()
    if not scope then A.ClearLocation(true,previous) end
    return scope
end
function A.AutomaticSuppressed()
    local inside,kind=A.Safe('instance context',IsInInstance)
    return inside==true or kind=='party' or kind=='raid' or kind=='pvp' or kind=='arena' or kind=='scenario'
end

function A.UpdateDistances(rows)
    local scope=A.scope
    local origin,ox,oy
    if scope and scope.map and type(scope.x)=='number' and type(scope.y)=='number' then origin,ox,oy=world(scope.map,scope.x,scope.y) end
    local points={}
    for _,row in ipairs(rows) do
        row.distanceYards=nil;row.rangeApproximate=(scope and scope.map==row.map and scope.rangeApproximate and A.db.nearbyOnly~=false and not A.IsCapitalMap(row.map) and row.x and row.y) and true or nil
        if origin and ox and oy and row.map==scope.map and type(row.x)=='number' and type(row.y)=='number' then
            local key=tostring(row.x)..':'..tostring(row.y)
            local distance=points[key]
            if distance==nil then
                local continent,x,y=world(row.map,row.x/100,row.y/100)
                distance=(continent==origin and x and y) and math.sqrt((x-ox)^2+(y-oy)^2) or false
                points[key]=distance
            end
            row.distanceYards=distance or nil
            if distance then row.rangeApproximate=nil end
            if not distance and not A.IsCapitalMap(row.map) and A.db.nearbyOnly~=false and not scope.noFilter then row.rangeApproximate=true end
        end
    end
end
