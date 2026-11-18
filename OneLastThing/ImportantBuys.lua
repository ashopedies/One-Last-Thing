local _,A=...
-- Three progression rules, not a recipe catalogue. Facts match SkillUp's
-- Forever RankBooks table. All vendor locations come from installed data.
local books={
    [129]={item=16084,cap=225,skill=125,level=0,price=10000},
    [185]={item=16072,cap=225,skill=125,level=0,price=10000},
    [356]={item=16083,cap=225,skill=125,level=20,price=10000},
}
function A.IsCriticalBook(item)
    for _,b in pairs(books) do if b.item==item then return true end end
    return false
end
local function held(item)
    return (A.Safe('owned rank book',C_Item and C_Item.GetItemCount or GetItemCount,item,true,false) or 0)>0
end
A.CriticalBookOwned=held
local function plans()
    local api=SkillUpForever and SkillUpForever.API
    if not (api and api.version==1 and api.Professions) then return end
    return A.Safe('important vendor profession plans',api.Professions),api
end
function A.ObserveImportantMerchant()
    A.importantOffers={}
    if not (GetMerchantNumItems and GetMerchantItemLink) then return end
    local map=A.Map();if not map then return end
    local pos=C_Map.GetPlayerMapPosition and C_Map.GetPlayerMapPosition(map,'player')
    local x,y;if pos then x,y=pos:GetXY();x,y=x*100,y*100 end
    local allowed={};for _,b in pairs(books) do allowed[b.item]=true end
    for i=1,GetMerchantNumItems() do
        local link=GetMerchantItemLink(i);local id=link and tonumber(link:match('item:(%d+)'))
        if id and allowed[id] then
            local info=A.MerchantInfo(i)
            if info then
                A.importantOffers[id]={map=map,x=x,y=y,name=UnitName('npc') or 'Merchant',price=info.price,
                    stock=info.numAvailable,purchasable=info.isPurchasable,extended=info.hasExtendedCost}
                A.db.vendors[id]=A.db.vendors[id] or {}
                A.db.vendors[id][map]={name=UnitName('npc') or 'Merchant',x=x,y=y}
            end
        end
    end
end
function A.ImportantVendorRows(out,map)
    A.coveredBooks={}
    if A.db.importantVendorBuys==false then return end
    local ps=plans();if not ps then if A.CheckUnavailable then A.CheckUnavailable('SkillUp profession data unavailable') end;return end
    local money=A.Safe('purchase budget',GetMoney);if type(money)~='number' then return end
    local candidates={}
    for _,p in ipairs(ps) do
        local b=books[p.skillLineID]
        if b and p.maxRank and p.maxRank>0 and p.maxRank<b.cap and (p.rank or 0)>0 and not held(b.item) then
            local vendor=A.importantOffers and A.importantOffers[b.item] or A.FindVendor(b.item,map)
            local offer=A.importantOffers and A.importantOffers[b.item]
            local price=offer and offer.price or b.price
            if vendor and vendor.map==map and vendor.x and vendor.y and price and money>=price
                and not (offer and (offer.stock==0 or offer.purchasable==false or offer.extended)) then
                local early=p.rank<b.skill or UnitLevel('player')<b.level
                local requirements='Requires '..p.name..' '..b.skill..' · current '..p.rank
                if b.level>0 then requirements=requirements..' | Requires level '..b.level..' · current '..UnitLevel('player') end
                local seller=(vendor.name or 'Book seller')..' | '..(offer and '' or '~')..A.FormatMoney(price)
                local detail=early and (requirements..'\n'..seller) or (seller..'\n'..p.name..': raises your skill cap to '..b.cap)
                candidates[#candidates+1]={key='buybook:'..b.item,title=(early and 'Buy ahead: ' or 'Unlock next rank: ')..A.ItemName(b.item),
                    detail=detail,buyAhead=early,requiredSkill=b.skill,requiredLevel=b.level,currentSkill=p.rank,
                    why=early and 'Buy here now to avoid a return trip when you meet the requirements.' or ('Profession rank book: raises your skill cap to '..b.cap),
                    professionID=p.skillLineID,profession=p.name,capMax=b.cap,criticalBook=true,
                    map=map,x=vendor.x,y=vendor.y,cost=price,buyItem=b.item,priority=11,verify=not offer}
            end
        end
    end
    table.sort(candidates,function(a,b)
        if a.buyAhead~=b.buyAhead then return not a.buyAhead end
        if a.currentSkill~=b.currentSkill then return a.currentSkill>b.currentSkill end
        return a.key<b.key
    end)
    local added=0
    for _,row in ipairs(candidates) do
        if A.ReminderHidden(row) and A.CategoryEnabled('professions',tostring(row.professionID))
            and A.ScopeAllows(row) then A.coveredBooks[row.professionID]=true end
        local before=#out;A.Add(out,row)
        if #out>before then added=added+1;if added==2 then break end end
    end
    A.status.ImportantBuys='Profession rank books only: '..added..' nearby offers (maximum 2)'
end
