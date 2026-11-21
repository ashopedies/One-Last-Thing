local _,A=...
-- Three progression rules, not a recipe catalogue. Facts match SkillUp's
-- Forever RankBooks table. All vendor locations come from installed data.
local books={
    [129]={item=16084,cap=225,skill=125,level=0,price=10000},
    [185]={item=16072,cap=225,skill=125,level=0,price=10000},
    [356]={item=16083,cap=225,skill=125,level=20,price=10000},
}
-- Read-only values shared with cap warnings; buying early remains allowed.
function A.ProfessionRankBookRequirement(id)
    local b=books[id]
    if b then return b.skill,b.level,b.cap end
end
function A.IsCriticalBook(item)
    for _,b in pairs(books) do if b.item==item then return true end end
    return false
end
local function held(item)
    return (A.Safe('owned rank book',C_Item and C_Item.GetItemCount or GetItemCount,item,true,false) or 0)>0
end
A.CriticalBookOwned=held
-- Curated progression vendors; keep useful reminders when a DB lacks vendors.
local firstAidVendors={
    {map=1417,x=27.0,y=58.8,name='Deneb Walker',side='Alliance'},
    {map=1445,x=36.4,y=30.4,name="Balai Lok'Wein",side='Horde'},
}
local bookVendors={
    [16084]=firstAidVendors,[16112]=firstAidVendors,[16113]=firstAidVendors,
    [16072]={{map=1440,x=49.6,y=67.0,name='Shandrina',side='Alliance'},
             {map=1443,x=26.2,y=69.8,name='Wulan',side='Horde'}},
    [16083]={{map=1434,x=27.4,y=77.0,name='Old Man Heming'}},
}
local manuals={{item=16112,spell=7929,skill=180,price=2500},{item=16113,spell=10840,skill=210,price=5000}}
local function manualKnown(book)
    if held(book.item) or A.SpellKnown(book.spell) then return true end
    local info=C_TradeSkillUI and A.Safe('known First Aid manual',C_TradeSkillUI.GetRecipeInfo,book.spell)
    return type(info)=='table' and info.learned==true
end
function A.FirstAidManualsMissing()
    local missing={}
    for _,book in ipairs(manuals) do if not manualKnown(book) then missing[#missing+1]=book end end
    return missing
end
local function vendorFor(item,map,manual)
    local offer=A.importantOffers and A.importantOffers[item]
    if offer and offer.map==map then return offer,offer end
    local vendor=not manual and A.FindVendor(item,map)
    if vendor and vendor.map==map then return vendor end
    local side=UnitFactionGroup('player')
    for _,v in ipairs(bookVendors[item] or {}) do
        if v.map==map and (not v.side or v.side==side) then return v end
    end
end
local function manualRow(p,map,money)
    if p.skillLineID~=129 or (p.rank or 0)<125 then return end
    local missing=A.FirstAidManualsMissing()
    local vendor,cost,exact,lines,count=nil,0,true,{},0
    for _,book in ipairs(missing) do
        local v,offer=vendorFor(book.item,map,true)
        local price=offer and offer.price or book.price
        if v and v.x and v.y and A.Nearby(map,v.x,v.y) and type(price)=='number'
            and not (offer and (offer.stock==0 or offer.purchasable==false or offer.extended)) then
            -- One grouped vendor stop; never mix destinations or unaffordable totals.
            if not vendor or (vendor.x==v.x and vendor.y==v.y) then
                vendor=v;cost=cost+price;exact=exact and offer~=nil;count=count+1
                lines[#lines+1]=A.ItemName(book.item)..' | '..A.Translate('Requires')..' '..p.name..' '..book.skill..' | '..(offer and '' or '~')..A.FormatMoney(price)
            end
        end
    end
    if not vendor or count==0 or cost>money then return end
    return {key='buybooks:129:manuals',title=p.name..': '..A.Translate('Bandage manuals'),
        detail=vendor.name..' | '..(exact and '' or '~')..A.FormatMoney(cost)..'\n'..table.concat(lines,'\n'),
        why=A.Translate('Optional for the bandage route. Buy here to avoid another trip.'),
        professionID=129,profession=p.name,firstAidManuals=true,map=map,x=vendor.x,y=vendor.y,
        cost=cost,currentSkill=p.rank,buyAhead=p.rank<180,priority=13,verify=not exact}
end
function A.ObserveImportantMerchant()
    A.importantOffers={}
    if not (GetMerchantNumItems and GetMerchantItemLink) then return end
    local map=A.Map();if not map then return end
    local pos=C_Map.GetPlayerMapPosition and C_Map.GetPlayerMapPosition(map,'player')
    local x,y;if pos then x,y=pos:GetXY();x,y=x*100,y*100 end
    local allowed={[16112]=true,[16113]=true};for _,b in pairs(books) do allowed[b.item]=true end
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
    local ps=A.ProfessionPlans();if not ps then if A.CheckUnavailable then A.CheckUnavailable('SkillUp profession data unavailable') end;return end
    local money=A.Safe('purchase budget',GetMoney);if type(money)~='number' then return end
    local candidates={}
    for _,p in ipairs(ps) do
        local b=books[p.skillLineID]
        if b and p.maxRank and p.maxRank>0 and p.maxRank<b.cap and (p.rank or 0)>0 and not held(b.item) then
            local vendor,offer=vendorFor(b.item,map)
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
        local row=manualRow(p,map,money)
        if row then candidates[#candidates+1]=row end
    end
    table.sort(candidates,function(a,b)
        if not not a.firstAidManuals~=not not b.firstAidManuals then return not a.firstAidManuals end
        if a.buyAhead~=b.buyAhead then return not a.buyAhead end
        if a.currentSkill~=b.currentSkill then return a.currentSkill>b.currentSkill end
        return a.key<b.key
    end)
    local added=0
    for _,row in ipairs(candidates) do
        if row.criticalBook and A.ReminderHidden(row) and A.CategoryEnabled('professions',tostring(row.professionID))
            and A.ScopeAllows(row) then A.coveredBooks[row.professionID]=true end
        local before=#out;A.Add(out,row)
        if #out>before then added=added+1;if added==2 then break end end
    end
    A.status.ImportantBuys='Profession progression books: '..added..' nearby offers (maximum 2)'
end
