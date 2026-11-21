local _,A=...
function A.FormatMoney(copper)
    local n=tonumber(copper)
    if not n then return A.Translate('price unknown') end
    n=math.max(0,math.floor(n+.5))
    local g=math.floor(n/10000);local s=math.floor(n/100)%100;local c=n%100
    return (g>0 and (g..'g') or '')..(s>0 and (s..'s') or '')..((c>0 or n==0) and (c..'c') or '')
end
function A.MerchantInfo(index)
    local info=C_MerchantFrame and A.Safe('merchant price',C_MerchantFrame.GetItemInfo,index)
    if type(info)=='table' then return info end
    if GetMerchantItemInfo then
        local ok,_,_,price,quantity,stock,usable,extended=pcall(GetMerchantItemInfo,index)
        if ok then return {price=price,stackCount=quantity,numAvailable=stock,isPurchasable=usable,hasExtendedCost=extended} end
    end
end

function A.SupplyEstimate(id,target)
    local missing=math.max(0,(target or 0)-A.ItemCount(id))
    if missing==0 then return {missing=0,buy=0,cost=0,exact=true} end
    local price=(A.liveSupplyPrices and A.liveSupplyPrices[id]) or A.db.supplyPrices[id]
    local exact=A.liveSupplyPrices and A.liveSupplyPrices[id]~=nil
    if not price and id==17030 then price={price=2000,bundle=1} end
    if not price or type(price.price)~='number' or type(price.bundle)~='number' or price.bundle<=0 then return {missing=missing} end
    local bundles=math.ceil(missing/price.bundle)
    return {missing=missing,buy=bundles*price.bundle,cost=bundles*price.price,price=price.price,bundle=price.bundle,exact=exact==true}
end
function A.SupplyEstimateText(id,target)
    local e=A.SupplyEstimate(id,target)
    if e.missing==0 then return A.Translate('Stocked') end
    if not e.cost then return A.Translate('Need '..e.missing)..' · '..A.Translate('Price unknown until a merchant visit') end
    return A.Translate('Buy '..e.buy)..' · '..(e.exact and '' or '~')..A.FormatMoney(e.cost)..' '..A.Translate('total')
end

function A.SupplySettingsText(id,target,preview)
    local status=A.SupplyStatus(id)
    local estimate=A.SupplyEstimate(id,target)
    if estimate.missing==0 then return A.Translate(status) end
    if preview or status:find(' · Need ',1,true) then
        return A.Translate(A.ItemCount(id)..' in bags')..' · '..A.SupplyEstimateText(id,target)
    end
    return A.Translate(status)..(estimate.cost and (' · '..(estimate.exact and '' or '~')..A.FormatMoney(estimate.cost)) or '')
end
