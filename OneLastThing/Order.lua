local _,A=...
local function group(chain,key)
    local translated=AttuneLang and AttuneLang[key]
    return chain.GROUP==key or (translated and chain.GROUP==translated)
end
function A.IsDungeonChain(chain)
    return chain and (chain.TYPE=='Dungeon' or tonumber(chain.GROUPSIZE)==5 or group(chain,'DUNGEONS')) or false
end
function A.IsAccessChain(chain)
    return chain and (chain.TYPE=='Raid' or (tonumber(chain.GROUPSIZE) or 0)>=10 or group(chain,'KEYS') or group(chain,'RAIDS')) or false
end
function A.ChainWhy(chain,finish)
    if not chain then return end
    local name=chain.NAME or tostring(chain.ID or '')
    if A.IsDungeonChain(chain) then
        return (finish and 'Dungeon quest chain: ' or 'Pick up before entering the dungeon: ')..name
    end
    if chain.CLASS and chain.CLASS~='' then return 'Part of your class progression: '..name end
    if A.IsAccessChain(chain) then return 'Raid/access progression: '..name end
end
local function tier(row)
    if row.quest and not row.finish and row.dungeonPickup then return 10 end
    if row.emptyEssential or row.brokenGear then return 15 end
    if row.bagQuest then return 20 end
    if row.quest and not row.finish and (row.classQuest or row.accessQuest or row.importantReason) then return 20 end
    if row.hearthstone then return 24 end
    if row.criticalBook or row.professionRank or row.flight then return 25 end
    if row.quest and not row.finish then return 30 end
    if row.talents then return 32 end
    if row.quest and row.finish then return 35 end
    if row.weapon then return 55 end
    if row.spell or (row.key or ''):match('^train:') then return 80 end
    if row.inventoryWarning or row.ammoItem or (row.key or ''):match('^supply:') then return 85 end
    if row.repair then return 90 end
    if not row.map then return 95 end
    return 60
end
function A.SortReminders(rows)
    if A.UpdateDistances then A.UpdateDistances(rows) end
    for _,row in ipairs(rows) do row.sortTier=tier(row) end
    table.sort(rows,function(a,b)
        if a.sortTier~=b.sortTier then return a.sortTier<b.sortTier end
        if (a.gray==true)~=(b.gray==true) then return a.gray~=true end
        if (a.verify==true)~=(b.verify==true) then return a.verify~=true end
        local da=a.distanceYards and math.floor(a.distanceYards/25) or math.huge
        local db=b.distanceYards and math.floor(b.distanceYards/25) or math.huge
        if da~=db then return da<db end
        local pa,pb=a.priority or 50,b.priority or 50
        if pa~=pb then return pa<pb end
        return a.key<b.key
    end)
end
function A.DistanceText(row)
    if row.distanceYards then return '~'..(math.floor(row.distanceYards/10+.5)*10)..' '..A.Translate('yd') end
    if row.map and row.x and row.y then return A.Translate('Distance unknown') end
    return ''
end
function A.DisplayTitle(row)
    local title=A.Translate(A.ReminderTitle(row))
    if row.verify and not (row.title or ''):match('^Check ') then title=A.Translate('[Check]')..' '..title end
    return title
end
function A.DisplayDetail(row,tooltip)
    local detail=A.Translate(row.detail or '')
    local reason=row.importantReason or row.why
    -- Buy-ahead rows reserve their two visible lines for requirements and price.
    -- The title explains the action; hover retains the full reason as well.
    if reason and (not row.buyAhead or tooltip) then detail=A.Translate(reason)..'\n'..detail end
    if row.verify then detail=A.Translate('Check availability')..' · '..detail end
    return detail
end
