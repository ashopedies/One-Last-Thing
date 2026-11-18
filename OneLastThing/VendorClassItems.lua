local _,A=...
-- No AH, crafting or quest-reward source is used to qualify a shopping item.
local conditional={
 SHAMAN={{17057,'Shiny Fish Scales',3,{131}},{17058,'Fish Oil',3,{546}}},
 MAGE={{17056,'Light Feather',5,{130}}},
 PRIEST={{17056,'Light Feather',5,{1706}}},
 ROGUE={{5530,'Blinding Powder',5,{2094}}},
}
local poisonGroups={
 instant={{6947,20},{6949,28},{6950,36},{8926,44},{8927,52},{8928,60}},
 crippling={{3775,20},{3776,50}},mindnumbing={{5237,24},{6951,38},{9186,52}},
 deadly={{2892,30},{2893,38},{8984,46},{8985,54},{20844,60}},
 wound={{10918,32},{10920,40},{10921,48},{10922,56}},
}
local poisonIndex={}
for family,entries in pairs(poisonGroups) do for _,p in ipairs(entries) do poisonIndex[p[1]]={family=family,level=p[2]} end end
-- Ordinary food families; actual vendor relation and native item level are required.
local foods={
 [117]=1,[2287]=1,[3770]=1,[3771]=1,[4599]=1,[8952]=1,
 [787]=2,[4592]=2,[4593]=2,[4594]=2,[8957]=2,[8959]=2,
 [2070]=4,[414]=4,[422]=4,[1707]=4,[3927]=4,[8932]=4,
 [4540]=8,[4541]=8,[4542]=8,[4544]=8,[4601]=8,[8950]=8,
 [4604]=16,[4605]=16,[4606]=16,[4607]=16,[4608]=16,[8948]=16,
 [4536]=32,[4537]=32,[4538]=32,[4539]=32,[4602]=32,[8953]=32,
}
local dietNames={Meat=1,Fleisch=1,Fish=2,Fisch=2,Cheese=4,["Käse"]=4,Bread=8,Brot=8,Fungus=16,Pilze=16,Fruit=32,Obst=32}
local function hasBit(mask,flag) return math.floor(mask/flag)%2==1 end
local function bags(visit)
 if not (C_Container and C_Container.GetContainerNumSlots and C_Container.GetContainerItemID) then return end
 for bag=0,(NUM_TOTAL_EQUIPPED_BAG_SLOTS or NUM_BAG_SLOTS or 4) do
  for index=1,(A.Safe('class supply bag size',C_Container.GetContainerNumSlots,bag) or 0) do
   local id=A.Safe('class supply bag item',C_Container.GetContainerItemID,bag,index)
   if id then visit(id) end
  end
 end
end
local function petDiet()
 if not A.IsHunter() or A.Safe('active pet',UnitExists,'pet')~=true or not A.SpellKnown(6991) then return end
 local mask=0
 local native=C_PetInfo and A.Safe('native pet food types',C_PetInfo.GetPetFoodTypes)
 if type(native)=='table' then
  for _,name in ipairs(native) do
   local flag=dietNames[name]
   if flag and not hasBit(mask,flag) then mask=mask+flag end
  end
 end
 if mask==0 and GetPetFoodTypes then
  local answer={pcall(GetPetFoodTypes)}
  if answer[1] then
   for i=2,#answer do
    if type(answer[i])=='string' then
     for name in answer[i]:gmatch('[^,]+') do
      local flag=dietNames[name:match('^%s*(.-)%s*$')]
      if flag and not hasBit(mask,flag) then mask=mask+flag end
     end
    end
   end
  end
 end
 if mask==0 then
  local family=A.Safe('pet family',UnitCreatureFamily,'pet')
  local locale=GetLocale and GetLocale() or 'enUS'
  for _,entry in pairs((TrainerSpellsHunterBeasts and TrainerSpellsHunterBeasts.families) or {}) do
   if family and ((entry.names or {})[locale]==family or (entry.names or {}).enUS==family) then mask=entry.food or 0;break end
  end
 end
 if mask==0 then return end
 return mask,'diet:'..mask
end
local function foodEligible(id,mask)
 local flag=foods[id]
 if not flag or not hasBit(mask,flag) or not A.HasVendorSource(id) then return false end
 local fn=(C_Item and C_Item.GetItemInfo) or GetItemInfo
 if not fn then return false end
 local ok,_,_,_,level,required=pcall(fn,id)
 if not ok or type(level)~='number' then A.ItemName(id);return false end
 local petLevel=A.Safe('pet level',UnitLevel,'pet')
 if not petLevel or petLevel<1 or level<petLevel-30 then return false end
 return not required or required<=UnitLevel('player')
end
function A.VendorPetFoodSelection()
 local mask,key=petDiet();if not mask then return end
 A.db.petFoodByDiet=A.db.petFoodByDiet or {}
 local chosen=A.db.petFoodByDiet[key]
 if chosen==false then return end
 if chosen and foodEligible(chosen,mask) then return chosen end
 local found
 bags(function(id) if not found and foodEligible(id,mask) then found=id end end)
 if found then A.db.petFoodByDiet[key]=found end
 return found
end
function A.VendorPetFoodChoices()
 local choices={{0,'Choose vendor pet food'}}
 local mask=petDiet();if not mask then return choices end
 local ids={}
 for id in pairs(foods) do if foodEligible(id,mask) then ids[#ids+1]=id end end
 table.sort(ids,function(a,b) return A.ItemName(a)<A.ItemName(b) end)
 for _,id in ipairs(ids) do choices[#choices+1]={id,A.ItemName(id)} end
 return choices
end
function A.SelectVendorPetFood(id)
 local mask,key=petDiet();if not key then return end
 if id~=0 and not foodEligible(id,mask) then return end
 A.db.petFoodByDiet=A.db.petFoodByDiet or {};A.db.petFoodByDiet[key]=id~=0 and id or false
 A.SyncClassSupplies();A.Refresh('Updated',false)
end
function A.HasAmmoBag(kind)
 local found=false
 local fn=(C_Item and C_Item.GetItemInfoInstant) or GetItemInfoInstant
 local function inspect(id)
  if not id or not fn then return end
  local ok,_,_,_,_,_,class,sub=pcall(fn,id)
  if ok and class==((Enum and Enum.ItemClass and Enum.ItemClass.Quiver) or 11) then
   if (kind=='arrow' and sub==2) or (kind=='bullet' and sub==3) then found=true end
  end
 end
 for i=0,3 do
  local slot=GetInventorySlotInfo and A.Safe('ammo bag slot',GetInventorySlotInfo,'Bag'..i..'Slot') or 20+i
  if slot then inspect(A.Safe('equipped ammo bag',GetInventoryItemID,'player',slot)) end
 end
 bags(inspect)
 return found
end
function A.IsClassVendorCandidate(id)
 local _,class=UnitClass('player')
 for _,p in ipairs(conditional[class] or {}) do if p[1]==id then return true end end
 if class=='ROGUE' and poisonIndex[id] then return true end
 return class=='HUNTER' and (foods[id]~=nil or id==5439 or id==5441)
end
function A.VendorClassExtras(list,class)
 -- Drop/crafted reagents do not become defaults merely because a spell needs them.
 for _,p in ipairs(conditional[class] or {}) do if A.HasVendorSource(p[1]) then list[#list+1]=p end end
 if class=='ROGUE' then
  A.db.vendorPoisons=A.db.vendorPoisons or {}
  local current={}
  bags(function(id)
   local entry=poisonIndex[id]
   if entry and entry.level<=UnitLevel('player') and A.HasVendorSource(id) then
    local old=current[entry.family]
    if not old or entry.level>poisonIndex[old].level then current[entry.family]=id end
   end
  end)
  for family,id in pairs(current) do A.db.vendorPoisons[family]=id end
  local families={};for family in pairs(A.db.vendorPoisons) do families[#families+1]=family end;table.sort(families)
  for _,family in ipairs(families) do
   local id=A.db.vendorPoisons[family];local entry=poisonIndex[id]
   if entry and A.HasVendorSource(id) then list[#list+1]={id,A.ItemName(id),5,{},entry.level,classUtility=true} end
  end
 elseif class=='HUNTER' then
  local food=A.VendorPetFoodSelection()
  if food then list[#list+1]={food,A.ItemName(food),10,{6991},1,classUtility=true} end
  local kind=A.HunterWeaponKind()
  if kind and not A.HasAmmoBag(kind) then
   local id=kind=='arrow' and 5439 or 5441
   if A.HasVendorSource(id) then list[#list+1]={id,A.ItemName(id),1,{},1,classUtility=true} end
  end
 end
end
