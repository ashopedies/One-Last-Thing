local _,A=...
-- Item/spell IDs are catalogue facts. Targets are conservative, editable per character.
-- Ranks share a group so obsolete reagent tiers stop producing reminders.
A.classSupplies={
 SHAMAN={{17030,'Ankh',3,{20608},30}},
 MAGE={{17031,'Rune of Teleportation',5,{3561,3562,3563,3565,3566,3567}},
       {17032,'Rune of Portals',5,{10059,11416,11417,11418,11419,11420}},
       {17020,'Arcane Powder',5,{23028}}},
 PRIEST={{17028,'Holy Candle',5,{21562}},{17029,'Sacred Candle',5,{21564,27683,27681}}},
 PALADIN={{17033,'Symbol of Divinity',3,{19752}},{21177,'Symbol of Kings',5,{25782,25894,25898,25895,25890,25899}}},
 ROGUE={{5140,'Flash Powder',5,{1856,1857}},{5060,"Thieves' Tools",1,{1804},15,classUtility=true}},
 WARLOCK={{5565,'Infernal Stone',3,{1122}},{16583,'Demonic Figurine',3,{18540}}},
 DRUID={{17034,'Maple Seed',3,{20484},nil,'rebirth',1},{17035,'Stranglethorn Seed',3,{20739},nil,'rebirth',2},
        {17036,'Ashwood Seed',3,{20742},nil,'rebirth',3},{17038,'Hornbeam Seed',3,{20747},nil,'rebirth',4},
        {17037,'Ironwood Seed',3,{20748},nil,'rebirth',5},
        {17021,'Wild Berries',5,{21849},nil,'gift',1},{17026,'Wild Thornroot',5,{21850},nil,'gift',2}},
 WARRIOR={}, HUNTER={}
}
local function unlocked(p)
 for _,spell in ipairs(p[4]) do if A.SpellKnown(spell) then return true end end
 -- Reincarnation can be reported inconsistently by passive-spell APIs.
 return p[1]==17030 and UnitLevel('player')>=30
end
-- A vendor selling an item is different from the price a vendor pays for loot.
-- These are curated ordinary vendor items; all other candidates need a seller relation.
local ordinaryVendor={}
for _,list in pairs(A.classSupplies) do for _,p in ipairs(list) do ordinaryVendor[p[1]]=true end end
function A.HasVendorSource(id)
 if ordinaryVendor[id] then return true end
 if A.db and A.db.vendors[id] and next(A.db.vendors[id]) then return true end
 local lib=LibQuestieDB
 local vendors=lib and lib.Item and A.Safe('class item vendors',lib.Item.Get,id,'vendors')
 return type(vendors)=='table' and next(vendors)~=nil or false
end
function A.ClassSupplyList()
 if A.collecting and A.collectClassList then return A.collectClassList end
 local _,class=UnitClass('player')
 local list={};for _,p in ipairs(A.classSupplies[class] or {}) do list[#list+1]=p end
 if A.VendorClassExtras then A.VendorClassExtras(list,class) end
 if A.collecting then A.collectClassList=list end
 return list
end
function A.SyncClassSupplies()
 if not A.db then return end
 A.db.supplyOverrides=A.db.supplyOverrides or {}
 A.db.retiredClassSupplies=A.db.retiredClassSupplies or {}
 local list=A.ClassSupplyList();local allowed={}
 for _,p in ipairs(list) do allowed[p[1]]=true end
 for id,rule in pairs(A.db.supplies) do
  if rule.classDefault and not allowed[id] then
   A.db.retiredClassSupplies[id]=rule;A.db.supplies[id]=nil
  end
 end
 for _,p in ipairs(list) do
  if not A.db.supplies[p[1]] and (A.db.retiredClassSupplies[p[1]] or not A.db.supplyOverrides[p[1]]) then
   A.db.supplies[p[1]]=A.db.retiredClassSupplies[p[1]] or {target=p[3],minLevel=p[5] or 1,classDefault=true}
  end
  local rule=A.db.supplies[p[1]]
  if rule then rule.classDefault=true;rule.classUtility=p.classUtility;rule.minLevel=p[5] or 1 end
 end
end
function A.SupplyRelevant(id,rule)
 if not rule.classDefault then return true end
 if id==17028 and A.SpellKnown(21564) then return false end
 for _,p in ipairs(A.ClassSupplyList()) do
  if p[1]==id then
   if not p.classUtility and not unlocked(p) then return false end
   if p.classUtility and #p[4]>0 and not unlocked(p) then return false end
   if p[6] then
    for _,higher in ipairs(A.ClassSupplyList()) do
     if higher[6]==p[6] and higher[7]>p[7] and unlocked(higher) then return false end
    end
   end
   return true
  end
 end
 return false
end
function A.SupplyName(id)
 local name=A.ItemName(id)
 if name=='Item '..id and not A.IsGerman() then
  for _,p in ipairs(A.ClassSupplyList()) do if p[1]==id then return p[2] end end
 end
 return name
end
