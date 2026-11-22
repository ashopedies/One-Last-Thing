"""Behavior tests in a Lua runtime with explicit WoW/addon API fixtures."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).parent.parent/'research/python-deps'))
from lupa.lua51 import LuaRuntime
root=Path(__file__).parent.parent
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
load=loadstring
now=1000
function time() return now end
function UnitClass() return 'Shaman','SHAMAN' end
function UnitName(unit) if unit=='npc' then return 'Trainer' end return 'Test','Surname' end
function UnitLevel() return 30 end
function UnitFactionGroup() return 'Horde' end
function GetZoneText() return 'Undercity' end
function IsResting() return true end
function InCombatLockdown() return combat or false end
C_Map={GetBestMapForUnit=function() return 1458 end,GetMapInfo=function(id) return {name=id==1458 and 'Undercity' or 'Other'} end}
C_Item={GetItemCount=function() return itemCount or 0 end,GetItemNameByID=function() return 'Ankh' end}
C_QuestLog={IsOnQuest=function(id) return active and active[id] or false end,
 IsComplete=function(id) return completed and completed[id] or false end,
 IsQuestFlaggedCompleted=function(id) return turned and turned[id] or false end}
ns={}; function loadAddon(s) assert(load(s))('OneLastThing',ns) end
''')
for file in ['Locale.lua','Migration.lua','SavedData.lua','Core.lua','Collection.lua','Money.lua','ClassSupplies.lua','HunterAmmo.lua','VendorClassItems.lua','Scope.lua','Order.lua','Categories.lua','Providers.lua','DungeonJournal.lua','ClassTraining.lua','ImportantBuys.lua','TravelTraining.lua','Repairs.lua']:
    lua.globals().loadAddon((root/'OneLastThing'/file).read_text())
lua.execute('OneLastThing.Init()')
def check(code): lua.execute(code)
check('''
assert(OneLastThing.db.supplies[17030].target==3)
local rows=OneLastThing.Collect(1458,true);assert(#rows==1 and rows[1].key=='supply:17030')
OneLastThing.db.dismissed['supply:17030']=true
assert(#OneLastThing.Collect(1458,true)==0)
OneLastThing.db.dismissed={}
OneLastThing.Snooze({key='supply:17030'},30)
assert(#OneLastThing.Collect(1458,true)==0)
now=1031;assert(#OneLastThing.Collect(1458,true)==1)
itemCount=5;assert(#OneLastThing.Collect(1458,true)==0)
Attune_Data={attunes={{ID='1',NAME='Class chain',CLASS='SHAMAN',FACTION='Horde'}},
steps={{ID_ATTUNE='1',ID='10',TYPE='Pick Up',ID_WOWHEAD='450',LOCATION='Undercity'}},
questGivers={[450]={1458,48,69,'Apothecary'}}}
Attune_DB={toons={['Test Surname']={next={['1-10']=1},done={},skip={}}}}
LibQuestieDB={Quest={Get=function(id,key) if key=='name' then return 'Important quest' end return 0 end}}
local eligibility=true
QuestieLoader={ImportModule=function(self,name)
 if name=='QuestieDB' then return {IsDoable=function() return eligibility end} end
end}
local rows=OneLastThing.Collect(1458,false)
assert(#rows==1 and rows[1].title=='Pick up: Important quest')
assert(#OneLastThing.Collect(1437,false)==0)
eligibility=false;assert(#OneLastThing.Collect(1458,false)==0)
eligibility=true
Attune_DB.toons['Test Surname'].skip['1']=true;assert(#OneLastThing.Collect(1458,false)==0)
Attune_DB.toons['Test Surname'].skip={}
Attune_Data.attunes[1].CLASS='MAGE';assert(#OneLastThing.Collect(1458,false)==0)
Attune_Data.attunes[1].CLASS='SHAMAN'
active={[450]=true};assert(#OneLastThing.Collect(1458,false)==0)
active={};turned={[450]=true};assert(#OneLastThing.Collect(1458,false)==0)
turned={};QuestieLoader=nil
rows=OneLastThing.Collect(1458,false);assert(rows[1].title=='Check pickup: Important quest')
-- Do not use a pickup pin for a turn-in in a different zone.
Attune_Data.steps[1].TYPE='Turn In';Attune_Data.steps[1].LOCATION='Other'
active={[450]=true};completed={[450]=true}
assert(#OneLastThing.Collect(1458,false)==0)
Attune_Data=nil;Attune_DB=nil
SkillUpForever={API={version=1,Professions=function() return {{name='Alchemy',skillLineID=171,rank=145,maxRank=150,
steps={{kind='train',text='Train next rank',detail='Faranell, Undercity · fee'}}}} end}}
rows=OneLastThing.Collect(1458,false);assert(#rows==2)
rows=OneLastThing.Collect(1437,false);assert(#rows==1 and rows[1].key=='cap:171')
assert(OneLastThing.NoteRows==nil and OneLastThing.CompleteNote==nil)
-- Combat defers automatic windows.
combat=true;OneLastThing.Refresh('Entering Undercity',true);assert(OneLastThing.pending.show)
combat=false
SkillUpForever=nil
function GetNumTrainerServices() return 2 end
function GetTrainerServiceInfo(i) return i==1 and 'Spell A' or 'Spell B','available' end
function GetTrainerServiceCost(i) return i*100 end
OneLastThing.ObserveTrainer()
rows=OneLastThing.Collect(1458,false);assert(#rows==2)
OneLastThing.db.dismissed[rows[1].key]=true
assert(#OneLastThing.Collect(1458,false)==1)
OneLastThing.db.dismissed={}
function GetTrainerServiceInfo(i) return i==1 and 'Spell A' or 'Spell B','used' end
OneLastThing.ObserveTrainer();assert(#OneLastThing.Collect(1458,false)==0)
''')
# Compile all shipped Lua, including UI and events.
for file in (root/'OneLastThing').glob('*.lua'):
    lua.execute('assert(load(...))',file.read_text())
print('PASS: supply targets, dismiss/restore, snooze expiry, quest eligibility, zone/faction/class filtering, active/completed quests, turn-in pin safety, profession route and cap, combat deferral, per-spell trainer dismissal, Lua compilation')
# Exercise UI creation, row callbacks and arrival scheduling with a minimal UI host.
lua.execute('''
local methods={}
local buttonScripts={OnClick=true}
local sliderScripts={OnValueChanged=true}
local editScripts={OnTextChanged=true,OnEnterPressed=true,OnEditFocusLost=true,OnEscapePressed=true}
function methods:SetScript(name,fn)
 if buttonScripts[name] then assert(self.kind=='Button' or self.kind=='CheckButton','unsupported '..name..' on '..tostring(self.kind)) end
 if sliderScripts[name] then assert(self.kind=='Slider','unsupported '..name..' on '..tostring(self.kind)) end
 if editScripts[name] then assert(self.kind=='EditBox','unsupported '..name..' on '..tostring(self.kind)) end
 self.scripts[name]=fn
end
function methods:GetScript(name) return self.scripts[name] end
function methods:GetPoint() return 'CENTER',UIParent,'CENTER',0,0 end
function methods:SetFrameStrata(value) self.strata=value end
function methods:SetText(value) self.text=value end
function methods:GetText() return self.text or "" end
function methods:GetFontString() return self.fontString end
function methods:SetFontString(fs) self.fontString=fs end
function methods:CreateFontString() return CreateFrame('FontString') end
function methods:CreateTexture() return CreateFrame('Texture') end
function methods:SetSize(w,h) self.width=w;self.height=h end
function methods:SetWidth(w) self.width=w end
function methods:SetHeight(h) self.height=h end
function methods:GetWidth() return self.width or 440 end
function methods:GetHeight() return self.height or 320 end
function methods:GetVerticalScroll() return self.offset or 0 end
function methods:SetVerticalScroll(v) self.offset=v end
function methods:IsShown() return self.shown or false end
function methods:Show() if self.shown then return end;self.shown=true;if self.scripts.OnShow then self.scripts.OnShow(self) end end
function methods:Hide() if not self.shown then return end;self.shown=false;if self.scripts.OnHide then self.scripts.OnHide(self) end end
function methods:SetShown(value) if value then self:Show() else self:Hide() end end
function methods:GetFrameLevel() return 1 end
function methods:StartMoving() end
function methods:StopMovingOrSizing() end
for _,name in ipairs({'SetEnabled','SetParent','SetPoint','SetBackdrop','SetBackdropColor','SetBackdropBorderColor','SetFont','SetTextColor','SetShadowColor','SetShadowOffset','SetMovable','EnableMouse','RegisterForDrag','SetJustifyH','SetScrollChild','ClearAllPoints','SetClampedToScreen','SetScale','SetChecked','SetAutoFocus','SetFocus','ClearFocus','HighlightText','SetNumeric','SetAlpha','SetFrameLevel','EnableMouseWheel','RegisterForClicks','SetTexture','SetTexCoord','SetAllPoints','SetColorTexture','SetResizable','SetResizeBounds','SetOrientation','SetThumbTexture','SetMinMaxValues','SetValueStep','SetObeyStepOnDrag','SetValue','StartSizing'}) do methods[name]=function() end end
function methods:RegisterEvent(event) self.events=self.events or {};self.events[event]=true end
function methods:UnregisterEvent(event) if self.events then self.events[event]=nil end end
function methods:IsMouseOver() return self.mouseOver==true end
frames={}
function CreateFrame(kind,name,parent,template)
 local f=setmetatable({scripts={},kind=kind}, {__index=methods});table.insert(frames,f);return f
end
UIParent=CreateFrame('Frame');UISpecialFrames={};SlashCmdList={}
STANDARD_TEXT_FONT='default'
C_AddOns={IsAddOnLoaded=function() return true end}
timers={};C_Timer={After=function(delay,fn) table.insert(timers,fn) end,NewTicker=function() end}
function flushTimers()
 while #timers>0 do local work=timers;timers={};for _,fn in ipairs(work) do fn() end end
end
''')
for file in ['Skin.lua','Scroll.lua','Pins.lua','UI.lua','Filters.lua','Settings.lua','TrashBin.lua','Events.lua']:
    lua.globals().loadAddon((root/'OneLastThing'/file).read_text())
lua.execute('''
OneLastThing.db.supplies[17030].target=6
OneLastThing.Draw(OneLastThing.Collect(1458,false),'Entering Undercity')
assert(OneLastThing.frame:IsShown())
local row=OneLastThing.frame.rowPool[1]
row.dismiss.scripts.OnClick();assert(OneLastThing.db.dismissed['supply:17030'])
OneLastThing.frame:Hide()
SlashCmdList.ONELASTTHING('');assert(OneLastThing.frame:IsShown())
OneLastThing.Draw({},'Entering zone');assert(OneLastThing.frame.empty:IsShown())
''')
print('PASS: styled popup creation, dismiss click, manual reopening, empty arrival state, UI/event loading')

lua.execute("""
local driver
for _,frame in ipairs(frames) do if frame.scripts.OnEvent then driver=frame end end
assert(driver)
OneLastThing.db.dismissed={};OneLastThing.frame:Hide()
driver.scripts.OnEvent(driver,'PLAYER_LOGIN');flushTimers()
assert(OneLastThing.frame:IsShown())
OneLastThing.frame:Hide()
driver.scripts.OnEvent(driver,'ZONE_CHANGED');flushTimers()
assert(not OneLastThing.frame:IsShown()) -- same map is not a new arrival
C_Map.GetBestMapForUnit=function() return 1437 end
combat=true;driver.scripts.OnEvent(driver,'ZONE_CHANGED_NEW_AREA');flushTimers()
assert(not OneLastThing.frame:IsShown() and OneLastThing.pending.show)
combat=false;driver.scripts.OnEvent(driver,'PLAYER_REGEN_ENABLED');flushTimers()
assert(OneLastThing.frame:IsShown())
OneLastThing.db.supplies[17030].target=10
local reason
local original=OneLastThing.Refresh
OneLastThing.Refresh=function(r) reason=r end
driver.scripts.OnEvent(driver,'TAXIMAP_OPENED')
driver.scripts.OnEvent(driver,'QUEST_LOG_UPDATE');flushTimers()
assert(reason=='Before travel')
OneLastThing.Refresh=original
""")
print('PASS: automatic zone-entry popup, no same-zone reopen, arrival during combat, post-combat popup, travel reminder survives batched updates')

lua.execute("""
OneLastThing.ShowSettings();assert(OneLastThing.settings:IsShown())
local first=OneLastThing.settings.boxes[1]
first.scripts.OnClick(first);assert(OneLastThing.db.auto==false)
first.scripts.OnClick(first);assert(OneLastThing.db.auto==true)
OneLastThing.SetCategory('professions','129',false);assert(not OneLastThing.CategoryEnabled('professions','129'))
OneLastThing.SetCategory('professions','129',true);assert(OneLastThing.CategoryEnabled('professions','129'))
function OneLastThing.frame:GetPoint() return 'TOPLEFT',UIParent,'TOPLEFT',25,-35 end
OneLastThing.frame.scripts.OnDragStop(OneLastThing.frame)
assert(OneLastThing.db.position.x==25 and OneLastThing.db.position.y==-35)
""")
print('PASS: settings panel, auto/category toggles, drag position saved without Edit Mode')
# Regression checks for vendor lookup, categories, resizing, opacity and atlas layout.
lua.execute(r"""
OneLastThing.scope=nil -- direct provider fixtures below supply their own map
itemCount=0
OneLastThing.db.supplies[17030]={target=5,minLevel=30}
local seller=OneLastThing.FindVendor(17030,1458)
assert(seller and seller.name=='Thomas Mordan' and seller.map==1458)
assert(seller.x==69.5 and seller.y==39.1)
local rows={};OneLastThing.SupplyRows(rows,1458,false)
assert(rows[1].x==69.5 and rows[1].detail:find('Thomas Mordan',1,true))
-- Public item vendor and spawn data must work for arbitrary configured supplies.
LibQuestieDB={Item={Get=function(id,key) if id==123 and key=='vendors' then return {88,99} end end},
 Npc={Get=function(id,key)
  if key=='friendlyToFaction' then return id==88 and 'H' or 'A' end
  if key=='spawns' then return {[1497]={{11,22}}} end
  if key=='name' then return 'Database seller' end
 end}}
local seller=OneLastThing.FindVendor(123,1458)
assert(seller and seller.name=='Database seller' and seller.x==11)
-- The user's supplied list can resolve missing item-vendor links by NPC name.
LibQuestieDB.Item.Get=function() return nil end
LibQuestieDB.Npc.IdsByName=function(name) if name=='Hannah Akeley' then return {88} end end
seller=OneLastThing.FindVendor(17030,1458)
assert(seller and seller.name=='Database seller')
LibQuestieDB=nil
local out={}
OneLastThing.SetCategory('professions','129',false)
OneLastThing.Add(out,{key='cap:129',title='First Aid: 145 / 150',professionID=129})
OneLastThing.Add(out,{key='cap:171',title='Alchemy: 145 / 150',professionID=171})
assert(#out==1 and out[1].professionID==171)
OneLastThing.SetCategory('professions','129',true)
OneLastThing.Add(out,{key='cap:129',title='First Aid: 145 / 150',professionID=129})
assert(#out==2)
OneLastThing.Draw(out,'Manual check')
OneLastThing.SetCollapsed(false,'manual')
assert(OneLastThing.frame:GetWidth()==440 and OneLastThing.frame:GetHeight()==320)
OneLastThing.ResizePopup(-1000,-1000)
assert(OneLastThing.db.size.width==360 and OneLastThing.db.size.height==230)
OneLastThing.ResizePopup(1000,1000)
assert(OneLastThing.db.size.width==950 and OneLastThing.db.size.height==850)
OneLastThing.ResizePopup(-510,-530)
-- Borders have been removed entirely.
assert(OneLastThing.db.borders==nil and OneLastThing.frame.pitEdges==nil)
OneLastThing.db.opacity=0;OneLastThing.ApplyOpacity()
OneLastThing.db.fontFace='expressway';OneLastThing.db.fontOutline='thick';OneLastThing.db.fontShadow='none';OneLastThing.ApplyFonts()
local called={}
local fs={SetFont=function(_,path,size,outline) called.path=path;called.outline=outline end,
 SetTextColor=function() end,SetShadowColor=function(_,r,g,b,a) called.alpha=a end,SetShadowOffset=function() end}
OneLastThing.Font(fs,12)
assert(called.path==[[Interface\AddOns\NeavMedia\Media\Expressway.ttf]])
assert(called.outline=='THICKOUTLINE' and called.alpha==0)
local alpha
local bg={SetBackdropColor=function(_,r,g,b,a) alpha=a end}
OneLastThing.Background(bg,0,0,0,1);assert(alpha==0)
OneLastThing.db.opacity=1;OneLastThing.ApplyOpacity();assert(alpha==1);OneLastThing.panels[bg]=nil
-- Map action is user-triggered and uses real vendor coordinates.
local point,opened
UiMapPoint={CreateFromCoordinates=function(map,x,y) return {map=map,x=x,y=y} end}
C_Map.SetUserWaypoint=function(p) point=p end
OpenWorldMap=function(map) opened=map end
OneLastThing.Navigate({map=1458,x=69.5,y=39.1})
assert(point and point.map==1458 and point.x==.695 and opened==1458)
""")
print('PASS: Ankh fallback and database seller pins, name-based vendor links, faction filtering, First Aid opt-out, min/max resize persistence, borderless panels, valid media paths, opacity endpoints, outline/shadow settings, vendor map navigation')
lua.execute("""
-- Completion collapses to a name-sized label without destroying expanded size.
local originalCollect=OneLastThing.Collect
OneLastThing.providerHealth={}
local note={key='test:99',title='Finish this errand',detail='Test',map=1437}
local resolved=false
OneLastThing.db.dismissed[note.key]=nil
OneLastThing.Collect=function()
 if OneLastThing.db.dismissed[note.key] or resolved then return {} end
 return {note}
end
OneLastThing.SetCollapsed(false,'manual')
OneLastThing.Draw({note},'Manual check')
local width,height=OneLastThing.db.size.width,OneLastThing.db.size.height
assert(OneLastThing.frame.strata=='LOW')
OneLastThing.frame.rowPool[1].dismiss.scripts.OnClick()
assert(OneLastThing.db.collapsed and OneLastThing.db.collapseMode=='auto')
assert(OneLastThing.frame.title.text=='One Last Thing · All done, yay!')
assert(OneLastThing.frame:GetHeight()==36)
assert(OneLastThing.db.size.width==width and OneLastThing.db.size.height==height)
for _,widget in ipairs(OneLastThing.frame.chrome) do assert(not widget:IsShown()) end
-- Background/border options never turn the compact text label into a panel.
assert(OneLastThing.frame.pitEdges==nil)
-- New work reopens an automatically collapsed overlay.
OneLastThing.db.dismissed[note.key]=nil;OneLastThing.Refresh('Updated',false)
assert(not OneLastThing.db.collapsed and OneLastThing.frame:GetWidth()==width)
-- A manual collapse survives background refreshes and empty/nonempty transitions.
OneLastThing.frame.header.scripts.OnClick(OneLastThing.frame.header)
assert(OneLastThing.db.collapsed and OneLastThing.frame.title.text=='One Last Thing (1)')
OneLastThing.Draw({},'Updated');OneLastThing.Draw({note},'Updated')
assert(OneLastThing.db.collapsed and OneLastThing.db.collapseMode=='manual')
OneLastThing.frame.header.scripts.OnClick(OneLastThing.frame.header)
assert(not OneLastThing.db.collapsed)
resolved=true;OneLastThing.Refresh('Updated',false)
assert(OneLastThing.db.collapsed and OneLastThing.db.collapseMode=='auto')
-- You can expand an empty popup without the next timer immediately closing it.
OneLastThing.frame.header.scripts.OnClick(OneLastThing.frame.header)
OneLastThing.Refresh('Updated',false);assert(not OneLastThing.db.collapsed)
OneLastThing.Collect=originalCollect
-- Wheel scrolling is clamped, and the thin indicator only appears for overflow.
local scroll,content=OneLastThing.frame.scroll,OneLastThing.frame.content
scroll:SetHeight(100);content:SetHeight(400);scroll:SetVerticalScroll(0)
scroll.scripts.OnMouseWheel(scroll,-1);assert(scroll:GetVerticalScroll()==48)
scroll.scripts.OnMouseWheel(scroll,-100);assert(scroll:GetVerticalScroll()==300)
scroll.scripts.OnMouseWheel(scroll,100);assert(scroll:GetVerticalScroll()==0)
assert(scroll.pitThumb:IsShown())
content:SetHeight(50);OneLastThing.UpdateScroll(scroll)
assert(not scroll.pitThumb:IsShown() and scroll:GetVerticalScroll()==0)
""")
assert('UIPanelScrollFrameTemplate' not in (root/'OneLastThing/UI.lua').read_text())
assert('UIPanelScrollFrameTemplate' not in (root/'OneLastThing/Settings.lua').read_text())
print('PASS: low strata, manual/automatic collapse, all-done header, done/dismiss completion, expanded-size preservation, compact border suppression, wheel-only scrolling, bounds and overflow indicator')
lua.execute("""
-- Regression: a combined Attune Quest step's LOCATION is the pickup city,
-- not the hand-in. Scooty must never remain as a turn-in in Orgrimmar.
OneLastThing.scope=nil -- exercise pickup/hand-in maps without an active HUD scope
OneLastThing.db.filters={};OneLastThing.db.dismissed={};OneLastThing.db.snoozed={}
active={[2842]=true};completed={[2842]=true};turned={}
Attune_Data={attunes={{ID='240',NAME='Gnomeregan',FACTION='Horde'}},
 steps={{ID_ATTUNE='240',ID='120',TYPE='Quest',LOCATION='Orgrimmar',ID_WOWHEAD='2842'}},
 questGivers={[2842]={1454,75.6,25.2,'Sovik'}}}
Attune_DB={toons={['Test Surname']={next={['240-120']=1},done={},skip={}}}}
local oldInfo=C_Map.GetMapInfo
C_Map.GetMapInfo=function(id) return {name=id==1454 and 'Orgrimmar' or 'Stranglethorn Vale'} end
LibQuestieDB={Quest={Get=function(id,key)
 if key=='name' then return 'Chief Engineer Scooty' end
 if key=='finishedBy' then return {{7406}} end
 if key=='startedBy' then return {{3413}} end
 end},Npc={Get=function(id,key)
 if key=='spawns' then return id==7406 and {[33]={{27.6,77.5}}} or {[1637]={{75.6,25.2}}} end
 if key=='name' then return id==7406 and 'Scooty' or 'Sovik' end
 end}}
QuestieLoader={ImportModule=function(_,name)
 if name=='ZoneDB' then return {GetUiMapIdByAreaId=function(_,area) return area==33 and 1434 or 1454 end} end
 end}
local out={};OneLastThing.AttuneRows(out,1454);assert(#out==0)
OneLastThing.AttuneRows(out,1434)
assert(#out==1 and out[1].finish and out[1].x==27.6 and out[1].map==1434)
-- Hand-in map actions bypass Attune's pickup-only quest-giver map view.
local usedPickupView=false
Attune_ToggleView=function() end;Attune_Select=function() end
Attune_ShowQuestDetail=function() usedPickupView=true end
local destination
C_Map.SetUserWaypoint=function(p) destination=p end
OneLastThing.Navigate(out[1]);assert(not usedPickupView and destination.map==1434)
-- With the DB unavailable, suppress guessed hand-ins and use only the
-- explicit verified destination for this reported quest.
LibQuestieDB=nil;QuestieLoader=nil
out={};OneLastThing.AttuneRows(out,1454);assert(#out==0)
OneLastThing.AttuneRows(out,1434);assert(#out==1 and out[1].finish)
Attune_Data.steps[1].ID_WOWHEAD='99900';active[99900]=true;completed[99900]=true
out={};OneLastThing.AttuneRows(out,1454);assert(#out==0)
C_Map.GetMapInfo=oldInfo
""")
print('PASS: Scooty hand-in stays out of Orgrimmar, appears in Booty Bay, uses destination waypoint, and never falls back to an Attune pickup zone')
lua.execute("""
-- Render every text role, including muted text, through each theme. A switch
-- must recolor existing font strings and keep the complete UI to three RGBs.
RAID_CLASS_COLORS={SHAMAN={r=0,g=.44,b=.87}}
local paletteColors={}
local probe={SetFont=function() end,SetShadowColor=function() end,SetShadowOffset=function() end,
 SetTextColor=function(_,r,g,b,a) paletteColors[string.format('%.4f/%.4f/%.4f',r,g,b)]=true end}
for _,theme in ipairs({'blizzard','class','pop'}) do
 OneLastThing.SetTheme(theme);assert(OneLastThing.db.theme==theme)
 paletteColors={}
 for role in pairs(OneLastThing.toneSlots) do
  OneLastThing.Font(probe,12,false,role);OneLastThing.Font(probe,12,true,role)
 end
 local count=0;for _ in pairs(paletteColors) do count=count+1 end
 assert(count==3,'Theme must have exactly three text colors: '..theme)
end
OneLastThing.SetTheme('class')
assert(OneLastThing.palette[1][1]==0 and OneLastThing.palette[1][2]==.44 and OneLastThing.palette[1][3]==.87)
OneLastThing.SetTheme('blizzard');OneLastThing.ApplyFonts()
assert(OneLastThing.db.theme=='blizzard' and OneLastThing.palette[1][1]==1)
""")
assert('|cff' not in (root/'OneLastThing/UI.lua').read_text())
print('PASS: Blizzard/Class Colors/Pop each use exactly three text colors, muted roles stay in palette, class accent matches character, switches recolor existing text')
lua.execute("""
-- A completed alternative or a later quest must suppress obsolete starters.
OneLastThing.sessionCompleted={};Questie=nil;QuestieLoader=nil;LibQuestieDB=nil
OneLastThing.db.filters={};OneLastThing.db.dismissed={};OneLastThing.db.snoozed={}
active={};turned={};completed={}
local oldCount=C_Item.GetItemCount;C_Item.GetItemCount=function() return 0 end
Attune_Data={attunes={{ID='5234',NAME='Call of Water',CLASS='SHAMAN',FACTION='Horde'}},
 steps={
 {ID_ATTUNE='5234',ID='20',TYPE='Quest',LOCATION='Durotar',ID_WOWHEAD='1528',FOLLOWS='10',OR=true},
 {ID_ATTUNE='5234',ID='21',TYPE='Quest',LOCATION='Durotar',ID_WOWHEAD='1529',FOLLOWS='10',OR=true},
 {ID_ATTUNE='5234',ID='30',TYPE='Quest',LOCATION='Other',ID_WOWHEAD='1530',FOLLOWS='20|21'},
 {ID_ATTUNE='5234',ID='100',TYPE='Quest',LOCATION='Other',ID_WOWHEAD='96',FOLLOWS='30'}},
 questGivers={}}
Attune_DB={toons={['Test Surname']={next={['5234-20']=1,['5234-21']=1},done={},skip={},attuned={}}}}
local oldInfo=C_Map.GetMapInfo
C_Map.GetMapInfo=function() return {name='Durotar'} end
local out={};OneLastThing.AttuneRows(out,1411);assert(#out==2)
-- Native history says the final quest is complete, despite stale Attune next.
turned[96]=true;out={};OneLastThing.AttuneRows(out,1411);assert(#out==0)
turned={};Questie={db={char={complete={[96]=true}}}}
out={};OneLastThing.AttuneRows(out,1411);assert(#out==0)
Questie=nil;active[1530]=true;out={};OneLastThing.AttuneRows(out,1411);assert(#out==0)
active={};active[1529]=true;out={};OneLastThing.AttuneRows(out,1411);assert(#out==0)
active={};Attune_DB.toons['Test Surname'].attuned['5234']=100
out={};OneLastThing.AttuneRows(out,1411);assert(#out==0)
Attune_DB.toons['Test Surname'].attuned={}
local oldKnown=IsPlayerSpell
IsPlayerSpell=function(id) return id==5394 end
out={};OneLastThing.AttuneRows(out,1411);assert(#out==0)
IsPlayerSpell=function() return false end
C_Item.GetItemCount=function(id) return id==5177 and 1 or 0 end
out={};OneLastThing.AttuneRows(out,1411);assert(#out==0)
C_Item.GetItemCount=oldCount;IsPlayerSpell=oldKnown;C_Map.GetMapInfo=oldInfo
-- Read the installed class catalogue before ever visiting the local trainer.
local known={[1001]=true,[1006]=true}
IsPlayerSpell=function(id) return known[id] or false end
UnitRace=function() return 'Orc','Orc',2 end
local oldSpell=C_Spell
C_Spell={GetSpellInfo=function(id) return {name=({[1001]='Healing Wave',[1002]='Flame Shock',[1003]='Future Spell',
 [1004]='Healing Wave',[1005]='Quest Reward',[1006]='Lightning Shield',[1007]='Lightning Shield',
 [1008]='Wrong Race',[1009]='Distant Spell'})[id]} end}
TrainerSpellsBuiltin={SHAMAN={
 [1]={[1001]={cost=10,rank=1},[1004]={cost=10,rank=1},[1007]={cost=10,rank=1}},
 [20]={[1002]={cost=2300,rank=1},[1005]={cost=0,questReward=true},[1006]={cost=2000,rank=2},
 [1008]={cost=2000,race='Tauren'},[1009]={cost=2000,sourceLocations={{uiMapID=1456,x=50,y=50}}}},
 [40]={[1003]={cost=10000}},}}
TrainerSpellsClassTrainers={SHAMAN={
 {npcID=1,faction='H',names={enUS='Local Shaman Trainer'},locations={{uiMapID=1454,x=39,y=37}}},
 {npcID=2,faction='A',names={enUS='Enemy Trainer'},locations={{uiMapID=1454,x=1,y=1}}}}}
GetMoney=function() return 500 end
TrainerSpells_Data=nil;TrainerSpells_IsIgnored=nil
out={};OneLastThing.ClassSpellRows(out,1454)
assert(#out==1 and out[1].spell==1002 and out[1].key=='train:spell:1002')
assert(out[1].map==1454 and out[1].x==39 and out[1].detail:find('short on gold',1,true))
OneLastThing.db.dismissed['train:spell:1002']=true
out={};OneLastThing.ClassSpellRows(out,1454);assert(#out==0)
OneLastThing.db.dismissed={};TrainerSpells_IsIgnored=function(id) return id==1002 end
out={};OneLastThing.ClassSpellRows(out,1454);assert(#out==0)
TrainerSpells_IsIgnored=nil;known[1002]=true
out={};OneLastThing.ClassSpellRows(out,1454);assert(#out==0)
known[1002]=false
out={};OneLastThing.ClassSpellRows(out,1411);assert(#out==0)
-- The fourth Original option intentionally keeps its original multicolor set.
OneLastThing.SetTheme('original');assert(OneLastThing.db.theme=='original')
local rgb
local fs={SetFont=function() end,SetShadowColor=function() end,SetShadowOffset=function() end,
 SetTextColor=function(_,r,g,b) rgb={r,g,b} end}
OneLastThing.Font(fs,12,false,'professions');assert(rgb[1]==.40 and rgb[2]==.83)
OneLastThing.Font(fs,12,false,'quests');assert(rgb[1]==.96 and rgb[2]==.77)
C_Spell=oldSpell
""")
print('PASS: Call of Water alternative/downstream completion, Questie history, Attune chain status, learned reward, pre-visit class spells/costs, individual dismissal, ignored/known/future/race/local-source filtering, Original multicolor theme')
lua.execute("""
-- All Attune chain kinds are considered even without cached next flags.
OneLastThing.scope={noFilter=true};OneLastThing.db.attuneAllChains=true
OneLastThing.db.filters={};OneLastThing.db.dismissed={};OneLastThing.db.trash={};OneLastThing.db.snoozed={}
OneLastThing.sessionCompleted={};Questie=nil;active={};turned={};completed={}
IsPlayerSpell=function() return false end
C_Item.GetItemCount=function() return 0 end
C_QuestLog.GetTrivialRange=function() return 10 end
local levelByID={[1001]=30,[1002]=10,[1003]=30,[1004]=10,[1005]=30,[1006]=30,[1007]=10,[1008]=10,[1009]=35}
LibQuestieDB={Quest={Get=function(id,key)
 if key=='name' then return 'Quest '..id end
 if key=='questLevel' then return levelByID[id] end
 if key=='requiredLevel' then return id==1009 and 35 or 1 end
 end}}
QuestieLoader=nil
Attune_Data={attunes={
 {ID='1',NAME='Dungeon',GROUP='Dungeons'},
 {ID='2',NAME='Class unlock',CLASS='SHAMAN',GROUP='Shaman'},
 {ID='3',NAME='Misc',GROUP='Miscellaneous'},
 {ID='4',NAME='Raid access',GROUP='Raids',GROUPSIZE=40},
 {ID='5',NAME='Future'}, {ID='6',NAME='Completed'},
 {ID='7',NAME='Old dungeon'}, {ID='8',NAME='Useful prerequisite'},
 {ID='9',NAME='No quests'}},steps={},questGivers={},questRewards={[2002]={spells={9999}}}}
local steps=Attune_Data.steps
for i=1,8 do
 steps[#steps+1]={ID_ATTUNE=tostring(i),ID='20',TYPE='Quest',ID_WOWHEAD=tostring(1000+i),LOCATION='Orgrimmar',FOLLOWS=i==5 and '10' or '0'}
 Attune_Data.questGivers[1000+i]={1454,40,40,'Giver'}
end
steps[#steps+1]={ID_ATTUNE='2',ID='30',TYPE='Quest',ID_WOWHEAD='2002',FOLLOWS='20'}
steps[#steps+1]={ID_ATTUNE='4',ID='30',TYPE='End',FOLLOWS='20'}
steps[#steps+1]={ID_ATTUNE='5',ID='10',TYPE='Level',ID_WOWHEAD='60',FOLLOWS='0'}
steps[#steps+1]={ID_ATTUNE='8',ID='30',TYPE='Quest',ID_WOWHEAD='1009',FOLLOWS='20'}
steps[#steps+1]={ID_ATTUNE='9',ID='10',TYPE='Stat',FOLLOWS='0'}
Attune_DB={toons={['Test Surname']={done={},skip={},attuned={['6']=100}}}}
local out={};OneLastThing.AttuneRows(out,1454)
local found={};for _,row in ipairs(out) do found[row.quest]=row end
assert(found[1001] and found[1002] and found[1003] and found[1004] and found[1008])
assert(not found[1005] and not found[1006] and not found[1007] and not found[1009])
assert(found[1002].importantReason:find('unlocks',1,true))
assert(found[1004].importantReason:find('raid/access',1,true))
assert(found[1008].importantReason:find('level 35',1,true))
assert(OneLastThing.categories[1].subs['chain:3']:find('Miscellaneous',1,true))
OneLastThing.db.attuneAllChains=false
out={};OneLastThing.AttuneRows(out,1454);assert(#out==0)
OneLastThing.db.attuneAllChains=true
-- A known giver elsewhere must beat a stale whole-zone LOCATION fallback.
Attune_Data.questGivers[1003]={1434,27,77,'Giver'}
out={};OneLastThing.AttuneRows(out,1454)
for _,row in ipairs(out) do assert(row.quest~=1003) end
-- Dismiss lasts this visit; Snooze lasts across visits; Trash lasts until restored.
local reminder={key='test:one',title='Test'}
OneLastThing.Dismiss(reminder);out={};OneLastThing.Add(out,reminder);assert(#out==0)
OneLastThing.BeginVisit();OneLastThing.Add(out,reminder);assert(#out==1)
OneLastThing.Snooze(reminder,30);OneLastThing.BeginVisit();out={};OneLastThing.Add(out,reminder);assert(#out==0)
now=now+31;OneLastThing.Add(out,reminder);assert(#out==1)
OneLastThing.Trash({key='quest:888:start',quest=888,title='Unwanted quest'})
OneLastThing.BeginVisit();out={};OneLastThing.Add(out,{key='quest:888:end',quest=888,title='Turn in'})
assert(#out==0 and OneLastThing.db.trash['quest:888'])
OneLastThing.db.dismissed={};OneLastThing.db.snoozed={};assert(OneLastThing.db.trash['quest:888'])
-- Nearby locality rather than a map-wide Barrens list.
local map=1413;local place='Ratchet';local taxi=false
UnitOnTaxi=function() return taxi end
GetMinimapZoneText=function() return place end
C_Map.GetBestMapForUnit=function() return map end
C_Map.GetMapInfo=function(id) return {name=id==1413 and 'The Barrens' or 'Stranglethorn Vale'} end
C_Map.GetPlayerMapPosition=function() return {GetXY=function() return .60,.20 end} end
OneLastThing.db.nearbyOnly=true;OneLastThing.db.nearbyRadius=850
local scope=OneLastThing.UpdateScope();assert(scope.name=='Ratchet')
assert(OneLastThing.ScopeAllows({map=1413,x=60.5,y=20}))
assert(not OneLastThing.ScopeAllows({map=1413,x=30,y=70}))
assert(not OneLastThing.ScopeAllows({map=1434,x=60,y=20}))
assert(not OneLastThing.ScopeAllows({map=1413,quest=123}))
-- Flight travel hides the stale checklist; landing rebuilds the correct scope.
local driver;for _,frame in ipairs(frames) do if frame.scripts.OnEvent then driver=frame end end
OneLastThing.frame:Show();taxi=true
OneLastThing.Refresh('Updated',false);assert(not OneLastThing.frame:IsShown())
driver.scripts.OnEvent(driver,'PLAYER_ENTERING_WORLD');flushTimers()
map=1434;place='Booty Bay';taxi=false
OneLastThing.db.dismissed['temporary']=true
driver.scripts.OnEvent(driver,'PLAYER_CONTROL_GAINED');flushTimers()
assert(OneLastThing.scope.name=='Booty Bay' and OneLastThing.scope.map==1434 and not OneLastThing.db.dismissed.temporary)
-- Settings always keeps its own 50% black panel, regardless of popup opacity.
OneLastThing.ShowSettings()
local alpha;OneLastThing.settings.SetBackdropColor=function(_,r,g,b,a) alpha=a end
OneLastThing.db.opacity=0;OneLastThing.ApplyOpacity();assert(alpha==.7)
OneLastThing.db.opacity=1;OneLastThing.ApplyOpacity();assert(alpha==.7)
-- Flight discovery distinguishes confirmed learned from undiscovered/unknown.
OneLastThing.scope={noFilter=true};OneLastThing.db.trash={};OneLastThing.db.dismissed={};OneLastThing.db.flightKnown={}
local nodes={
 {nodeID=1,name='Local',faction=1,isUndiscovered=true,position={GetXY=function() return .5,.5 end}},
 {nodeID=2,name='Known',faction=1,isUndiscovered=false,position={GetXY=function() return .5,.5 end}},
 {nodeID=3,name='Enemy',faction=2,isUndiscovered=true,position={GetXY=function() return .5,.5 end}}}
C_TaxiMap={GetTaxiNodesForMap=function() return nodes end,GetAllTaxiNodes=function() return {{nodeID=1,state=0},{nodeID=2,state=1}} end}
out={};OneLastThing.FlightRows(out,1454);assert(#out==2 and out[1].flight and out[2].verify)
OneLastThing.ObserveFlights();nodes[1].isUndiscovered=nil
out={};OneLastThing.FlightRows(out,1454);assert(#out==0 and OneLastThing.db.flightKnown[1])
-- Weapon skill rows use only class/faction/level-eligible, unlearned skills.
local learned={}
IsPlayerSpell=function(id) return learned[id] or false end
C_Spell={GetSpellInfo=function(id) return {name='Skill '..id} end}
TrainerSpellsWeaponSkills={
 trainers={[10]={zoneID=1637,x=81.5,y=19.6,names={enUS='Weapon master'}}},
 zones={[1637]={uiMapID=1454}},
 skills={[196]={cost=1000,classes={SHAMAN=true},trainers={Horde={10}}},
 [197]={cost=1000,classes={WARRIOR=true},trainers={Horde={10}}},
 [198]={level=40,cost=1000,classes={SHAMAN=true},trainers={Horde={10}}}}}
out={};OneLastThing.WeaponRows(out,1454);assert(#out==1 and out[1].weapon and out[1].spell==196)
learned[196]=true;out={};OneLastThing.WeaponRows(out,1454);assert(#out==0)
-- Compact pending label counts the visible reminders.
OneLastThing.SetCollapsed(true,'manual')
OneLastThing.Draw({{key='a',title='One'},{key='b',title='Two'}},'Updated')
assert(OneLastThing.frame.title.text=='One Last Thing (2)')
""")
for file in ['OneLastThing.toc','OneLastThing_Forever.toc']:
    assert('## SavedVariablesPerCharacter: OneLastThingDB' in (root/'OneLastThing'/file).read_text())
print('PASS: all unfinished Attune chain kinds, gray-quest filtering and explained exceptions, Dismiss/Snooze/Trash lifetimes, Ratchet proximity and Booty Bay landing, fixed 70% settings background, discovered flight paths, eligible weapon training, pending count, per-character settings')
lua.execute("""
-- Settings-only trash bin keeps enough metadata to recover individual rows.
OneLastThing.scope={noFilter=true};OneLastThing.db.trash={};OneLastThing.db.dismissed={};OneLastThing.db.snoozed={}
SkillUpForever={API={version=1,Professions=function() return {{skillLineID=129,name='First Aid',rank=100,maxRank=150,steps={}}} end}}
active={[3301]=true};turned={[3300]=true}
LibQuestieDB={Quest={Get=function(id,key)
 if key=='questLevel' then return id==3330 and 5 or 30 end
 if key=='name' then return 'Quest '..id end
 end}}
IsPlayerSpell=function(id) return id==9002 end
GetMoney=function() return 10000 end
OneLastThing.Trash({key='cap:129',title='First Aid rank',professionID=129,profession='First Aid',capMax=150})
OneLastThing.Trash({key='quest:3301:start',title='Current quest',quest=3301})
OneLastThing.Trash({key='train:spell:9001',title='Deferred class spell',spell=9001,cost=1000})
OneLastThing.Trash({key='train:spell:9002',title='Learned class spell',spell=9002,cost=1000})
OneLastThing.Trash({key='quest:3300:start',title='Completed quest',quest=3300})
OneLastThing.Trash({key='quest:3330:start',title='Grey dungeon quest',quest=3330})
local entries=OneLastThing.TrashEntries()
assert(#entries==6)
assert(entries[1].record.professionID==129 and entries[1].reason:find('still relevant',1,true))
assert(entries[2].record.quest==3301)
assert(entries[3].record.spell==9001 and entries[3].reason:find('affordable',1,true))
assert(entries[#entries].record.quest==3330)
OneLastThing.ShowSettings();OneLastThing.ShowTrashBin()
assert(OneLastThing.trashFrame:IsShown() and OneLastThing.trashFrame.pitSettingsBackground)
assert(OneLastThing.trashFrame.rows[1].key=='cap:129')
OneLastThing.trashFrame.rows[1].restore.scripts.OnClick()
assert(not OneLastThing.db.trash['cap:129'] and OneLastThing.db.trash['train:spell:9001'])
-- Restoring a hidden class spell neither buys nor learns it; it just removes
-- OneLastThing's hide. The real trainer and TrainerSpells data remain unchanged.
OneLastThing.RestoreTrash('train:spell:9001')
assert(not OneLastThing.db.trash['train:spell:9001'] and not IsPlayerSpell(9001))
assert(OneLastThing.db.trash['train:spell:9002'])
""")
assert('Ignored reminders' in (root/'OneLastThing/Settings.lua').read_text())
assert('ShowTrashBin' not in (root/'OneLastThing/Events.lua').read_text())
print('PASS: recoverable settings-only Trash Bin, current profession/quest relevance ordering, affordable deferred spells, learned/completed status, gray quests last, individual restore without learning/purchasing')

# New supply settings, rank relevance and lifecycle checks.
lua.execute("""
local originalClass=UnitClass
C_Item.GetItemCount=function() return itemCount or 0 end
local known={}
IsPlayerSpell=function(id) return known[id] or false end
IsSpellKnown=nil;IsSpellKnownOrOverridesKnown=nil
for class,list in pairs(OneLastThing.classSupplies) do
 UnitClass=function() return class,class end
 OneLastThingDB={};OneLastThing.Init()
 for _,p in ipairs(list) do
  assert(OneLastThing.db.supplies[p[1]].target==p[3],class)
  assert(OneLastThing.db.supplies[p[1]].classDefault)
 end
end
UnitClass=function() return 'Druid','DRUID' end
OneLastThingDB={};OneLastThing.Init();known={[20484]=true}
assert(OneLastThing.SupplyRelevant(17034,OneLastThing.db.supplies[17034]))
assert(not OneLastThing.SupplyRelevant(17035,OneLastThing.db.supplies[17035]))
known[20739]=true
assert(not OneLastThing.SupplyRelevant(17034,OneLastThing.db.supplies[17034]))
assert(OneLastThing.SupplyRelevant(17035,OneLastThing.db.supplies[17035]))
OneLastThing.db.filters['supplies/17035']=false
assert(not OneLastThing.CategoryEnabled('supplies','17035'))
UnitClass=originalClass;known={};OneLastThingDB={};OneLastThing.Init()
local originalDraw,originalRefresh=OneLastThing.Draw,OneLastThing.Refresh
OneLastThing.Draw=function() end;OneLastThing.Refresh=function() end
itemCount=1
OneLastThing.db.dismissed['supply:17030']=true;OneLastThing.db.snoozed['supply:17030']=99999;OneLastThing.db.trash['supply:17030']=true
assert(OneLastThing.SetSupplyTarget(17030,3):find('Need 2',1,true))
assert(not OneLastThing.db.dismissed['supply:17030'] and not OneLastThing.db.snoozed['supply:17030'] and not OneLastThing.db.trash['supply:17030'])
OneLastThing.Init();assert(OneLastThing.db.supplies[17030].target==3)
OneLastThing.SetSupplyTarget(17030,5);OneLastThing.SyncClassSupplies();assert(OneLastThing.db.supplies[17030].target==5)
OneLastThing.settings.signature=nil;OneLastThing.BuildSettings()
assert(OneLastThing.settings.supplyInputs[17030]:GetText()=='5')
OneLastThing.settings.supplyInputs[17030]:SetText('6')
OneLastThing.settings.supplyInputs[17030].scripts.OnEnterPressed()
assert(OneLastThing.db.supplies[17030].target==6)
OneLastThing.SetSupplyTarget(17030,0);OneLastThing.SyncClassSupplies();assert(not OneLastThing.db.supplies[17030])
OneLastThing.SetSupplyTarget(17030,3);assert(OneLastThing.db.supplies[17030].classDefault)
OneLastThing.SetSupplyTarget(99999,7);OneLastThing.Init();assert(OneLastThing.db.supplies[99999].target==7)
OneLastThing.Draw, OneLastThing.Refresh=originalDraw,originalRefresh
-- Partial restock stays missing; visiting again clears only visit dismissals.
OneLastThing.db.supplies={[17030]={target=3,minLevel=30,classDefault=true}}
OneLastThing.scope={noFilter=true};OneLastThing.BeginVisit()
local out={};OneLastThing.SupplyRows(out,1454,true)
assert(#out==1 and out[1].title:find('1 / 3',1,true) and out[1].detail:find('40s total',1,true))
itemCount=3;out={};OneLastThing.SupplyRows(out,1454,true);assert(#out==0)
assert(OneLastThing.FormatMoney(12000)=='1g20s' and OneLastThing.FormatMoney(12003)=='1g20s3c' and OneLastThing.FormatMoney(0)=='0c')
-- Only the owned waypoint is cleared, only when supply target is met.
local waypoint={uiMapID=1454,position={GetXY=function() return .5,.4 end}}
C_Map.GetUserWaypoint=function() return waypoint end
local clears=0;C_Map.ClearUserWaypoint=function() clears=clears+1;waypoint=nil end
OneLastThing.TrackWaypoint({key='supply:17030'},1454,.5,.4)
itemCount=1;OneLastThing.CleanupPin();assert(clears==0 and OneLastThing.db.pin)
itemCount=3;OneLastThing.CleanupPin();assert(clears==1 and not OneLastThing.db.pin)
waypoint={uiMapID=1454,position={GetXY=function() return .5,.4 end}}
OneLastThing.TrackWaypoint({key='supply:17030'},1454,.5,.4)
waypoint={uiMapID=1454,position={GetXY=function() return .8,.4 end}}
OneLastThing.CleanupPin();assert(clears==1 and waypoint and not OneLastThing.db.pin)
-- Completion fades to P, hover reveals, and pending work never loses its count.
timers={};OneLastThing.frame.idleWaiting=false;OneLastThing.frame.headerHovered=false
OneLastThing.frame.previousCount=1
OneLastThing.db.headerPosition='bottom';OneLastThing.db.collapsed=false
OneLastThing.Draw({},'Updated');flushTimers()
OneLastThing.frame.header.scripts.OnUpdate(OneLastThing.frame.header,.4)
assert(OneLastThing.frame.title.text=='OLT',tostring(OneLastThing.frame.title.text)..' collapsed='..tostring(OneLastThing.db.collapsed)..' wait='..tostring(OneLastThing.frame.idleWaiting)..' fade='..tostring(OneLastThing.frame.fadeElapsed))
OneLastThing.frame.header.scripts.OnEnter();assert(OneLastThing.frame.title.text=='One Last Thing · All done, yay!')
OneLastThing.frame.header.scripts.OnLeave()
OneLastThing.Draw({{key='pending',title='Pending'}},'Updated');OneLastThing.SetCollapsed(true,'manual');flushTimers()
assert(OneLastThing.frame.header.scripts.OnUpdate==nil)
assert(OneLastThing.frame.title.text=='One Last Thing (1)')
OneLastThing.db.headerPosition='top';OneLastThing.SetCollapsed(false,'manual')
""")
print('PASS: all nine class preset lists, learned spell/rank relevance, individual supply filters, saved editable targets, custom items, removal persistence, partial restock, g/s/c costs, completed-pin cleanup and player-pin safety, bottom/top header, completion fade and hover')

lua.execute("""
-- Essential vendor purchases: no learned/owned/irrelevant recipe shopping list.
itemCount=0;C_Item.GetItemCount=function() return itemCount end
GetMoney=function() return 100000 end
OneLastThing.db.filters={};OneLastThing.db.trash={};OneLastThing.db.dismissed={};OneLastThing.db.snoozed={}
OneLastThing.db.importantVendorBuys=true;OneLastThing.scope={noFilter=true}
local p={skillLineID=129,name='First Aid',rank=125,maxRank=150,steps={}}
SkillUpForever={API={version=1,Professions=function() return {p} end}}
local oldFind=OneLastThing.FindVendor
OneLastThing.FindVendor=function() return {name='Seller',map=1454,x=50,y=50} end
local out={};OneLastThing.ImportantVendorRows(out,1454);assert(#out==1 and out[1].buyItem==16084)
p.maxRank=225;out={};OneLastThing.ImportantVendorRows(out,1454);assert(#out==0)
p.maxRank=150;itemCount=1;out={};OneLastThing.ImportantVendorRows(out,1454);assert(#out==0)
itemCount=0;p={skillLineID=171,name='Alchemy',rank=100,maxRank=150,steps={{kind='train',itemID=90000,spellID=90001}},recipes={{spellID=90001,learned=false,fromRank=100,toRank=115}}}
SkillUpForever.API.IsTracked=function() return true end
SkillUpForever.API.RequiredMaterials=function() return {{itemID=1,count=1}} end
C_Item.GetItemCount=function(id) return id==1 and 2 or 0 end
OneLastThing.importantOffers={[90000]={map=1454,x=50,y=50,price=1000,stock=1,purchasable=true}}
out={};OneLastThing.ImportantVendorRows(out,1454);assert(#out==0) -- dynamic route recipes are no longer reminders
p.recipes[1].learned=true;out={};OneLastThing.ImportantVendorRows(out,1454);assert(#out==0)
p.recipes[1].learned=false;OneLastThing.importantOffers[90000].stock=0
out={};OneLastThing.ImportantVendorRows(out,1454);assert(#out==0)
OneLastThing.importantOffers[90000].stock=1;SkillUpForever.API.IsTracked=function() return false end
out={};OneLastThing.ImportantVendorRows(out,1454);assert(#out==0)
OneLastThing.FindVendor=oldFind
""")
print('PASS: essential profession books, learned/owned suppression, dynamic route recipes excluded, irrelevant/untracked rejection')

lua.execute("""
-- An upgrade repairs stale Ankh hides, but only once; future choices persist.
UnitClass=function() return 'Shaman','SHAMAN' end
C_Item.GetItemCount=function() return 1 end
OneLastThingDB={supplies={[17030]={target=3,minLevel=30}},filters={supplies=false,['supplies/17030']=false},
 sources={SupplyRows=false},trash={['supply:17030']=true},snoozed={['supply:17030']=99999}}
OneLastThing.Init();OneLastThing.scope={noFilter=true}
local rows={};OneLastThing.SupplyRows(rows,1454,false)
assert(#rows==1 and rows[1].title:find('1 / 3',1,true))
assert(OneLastThing.SupplyStatus(17030)=='1 in bags · Need 2 more')
OneLastThing.EnableSupply(17030,false);rows={};OneLastThing.SupplyRows(rows,1454,false);assert(#rows==0)
OneLastThing.Init();assert(OneLastThing.db.filters['supplies/17030']==false)
OneLastThing.db.trash['supply:17030']=true;OneLastThing.db.filters.supplies=false
OneLastThing.EnableSupply(17030,true);assert(OneLastThing.CategoryEnabled('supplies','17030') and not OneLastThing.db.trash['supply:17030'])
OneLastThing.SetSupplyTarget(99999,4);OneLastThing.settings.signature=nil;OneLastThing.BuildSettings()
assert(OneLastThing.settings.supplyChecks[17030] and OneLastThing.settings.supplyInputs[17030])
assert(not OneLastThing.settings.supplyDeletes[17030] and OneLastThing.settings.supplyDeletes[99999])
OneLastThing.settings.supplyDeletes[99999].scripts.OnClick()
assert(not OneLastThing.db.supplies[99999] and not OneLastThing.settings.supplyInputs[99999])
OneLastThing.Init();assert(not OneLastThing.db.supplies[99999])
""")
print('PASS: stale Ankh state repaired once, 1/3 reminder, enable clears hide/filter blocks, inline targets, custom-only Delete and saved deletion')

lua.execute("""
C_Item.GetItemInfo=function() return 'Ankh',nil,0 end
OneLastThing.scope={map=1454,name='Orgrimmar',x=.95,y=.95}
OneLastThing.db.nearbyOnly=true
OneLastThing.db.supplies[17030].target=3;OneLastThing.BeginVisit()
local rows={};OneLastThing.SupplyRows(rows,1454,false)
assert(#rows==1 and rows[1].key=='supply:17030')
""")
print('PASS: Ankh warning across Orgrimmar even far from vendor, item quality does not falsely suppress reagent')

lua.execute("""
-- Real clients can return plain Vector2 fields rather than GetXY methods.
local wp={uiMapID=1454,position={x=.454012,y=.566012}}
C_Map.GetUserWaypoint=function() return wp end
local clears,untracks=0,0
C_Map.ClearUserWaypoint=function() clears=clears+1;wp=nil end
C_SuperTrack={SetSuperTrackedUserWaypoint=function(v) if not v then untracks=untracks+1 end end}
C_Item.GetItemCount=function() return 3 end
OneLastThing.TrackWaypoint({key='supply:17030'},1454,.454,.566)
assert(OneLastThing.db.pin.x==.454012)
OneLastThing.CleanupPin();assert(clears==1 and untracks==1 and not OneLastThing.db.pin)
-- Completion cleanup must run even if no zone/task list can be drawn.
wp={uiMapID=1454,position={x=.5,y=.4}}
OneLastThing.TrackWaypoint({key='supply:17030'},1454,.5,.4)
local oldTransit=OneLastThing.InTransit;OneLastThing.InTransit=function() return true end
OneLastThing.Refresh('Updated',false);assert(clears==2 and not OneLastThing.db.pin)
OneLastThing.InTransit=oldTransit
-- Dismissed/trashed/snoozed task pins are cleared independently of locality.
for _,action in ipairs({'Dismiss','Trash','Snooze'}) do
 wp={uiMapID=1454,position={x=.5,y=.4}}
 local row={key='quest:7777:start',quest=7777}
 OneLastThing.db.dismissed={};OneLastThing.db.trash={};OneLastThing.db.snoozed={}
 OneLastThing.TrackWaypoint(row,1454,.5,.4);OneLastThing[action](row)
 assert(not wp and not OneLastThing.db.pin,action)
end
-- Accepted quest pickup and learned profession recipe each finish their pins.
wp={uiMapID=1454,position={x=.5,y=.4}}
OneLastThing.TrackWaypoint({key='quest:7778:start',quest=7778},1454,.5,.4)
active={[7778]=true};OneLastThing.CleanupPin();assert(not wp)
wp={uiMapID=1454,position={x=.5,y=.4}}
OneLastThing.TrackWaypoint({key='skill:171:123',skill=171,spell=123},1454,.5,.4)
SkillUpForever={API={Professions=function() return {{skillLineID=171,recipes={{spellID=123,learned=true}}}} end}}
OneLastThing.CleanupPin();assert(not wp)
-- Clear failures retain ownership for the next retry.
wp={uiMapID=1454,position={x=.5,y=.4}}
OneLastThing.TrackWaypoint({key='supply:17030'},1454,.5,.4)
C_Map.ClearUserWaypoint=function() error('not ready') end
OneLastThing.CleanupPin();assert(OneLastThing.db.pin and wp)
C_Map.ClearUserWaypoint=function() wp=nil end
OneLastThing.CleanupPin();assert(not OneLastThing.db.pin and not wp)
-- A reader-less client can still prove ownership via an exact waypoint link.
C_Map.GetUserWaypoint=nil
local href='|Hworldmap:1454:5000:4000|h[Pin]|h'
C_Map.GetUserWaypointHyperlink=function() return href end
OneLastThing.TrackWaypoint({key='supply:17030'},1454,.5,.4)
C_Map.ClearUserWaypoint=function() href=nil end
OneLastThing.CleanupPin();assert(not href and not OneLastThing.db.pin)
-- Known quest destinations use only a native pin, with no extra Attune panel.
C_Map.GetUserWaypoint=function() return wp end
C_Map.GetUserWaypointHyperlink=nil
C_Map.CanSetUserWaypointOnMap=function() return true end
UiMapPoint={CreateFromCoordinates=function(map,x,y) return {uiMapID=map,position={x=x,y=y}} end}
C_Map.SetUserWaypoint=function(p) wp=p end
local attuneCalls=0
Attune_ToggleView=function() attuneCalls=attuneCalls+1 end
Attune_Select=function() end;Attune_ShowQuestDetail=function() attuneCalls=attuneCalls+1 end
OneLastThing.Navigate({key='quest:9998:start',quest=9998,attuneStep={ID_ATTUNE='test'},map=1454,x=50,y=40})
assert(wp and OneLastThing.db.pin and attuneCalls==0)
-- A skill provider reporting success without placing a native pin cannot
-- accidentally claim an existing personal waypoint.
OneLastThing.db.pin=nil
SkillUpForever={API={Navigate=function() return true end}}
OneLastThing.Navigate({key='skill:171:1',skill=171,stepIndex=1})
assert(not OneLastThing.db.pin and wp)
""")
print('PASS: plain/quantized waypoint coordinates, transit cleanup, Dismiss/Trash/Snooze cleanup, accepted quest and learned recipe, retry after clear failure, hyperlink identity fallback, single native quest pin, unrelated pin protection')

lua.execute("""
-- Direct row actions preserve visit skips and settings-only ignored recovery.
OneLastThing.db.dismissed={};OneLastThing.db.snoozed={};OneLastThing.db.trash={};OneLastThing.db.filters={}
local originalRefresh=OneLastThing.Refresh
OneLastThing.Refresh=function() end
local one={key='test:998',title='First reminder'}
local two={key='test:999',title='Second reminder'}
OneLastThing.Draw({one,two},'Updated')
local first=OneLastThing.frame.rowPool[1]
assert(first.dismiss.text=='Skip' and first.ignore.text=='Ignore')
assert(not first.more and not first.snooze and not OneLastThing.ShowReminderMenu)
first.ignore.scripts.OnClick()
assert(OneLastThing.db.trash['test:998'] and not OneLastThing.db.trash['test:999'])
OneLastThing.db.dismissed['test:123']=true;OneLastThing.db.snoozed['test:124']=99999
assert(OneLastThing.frame.restoreButton.text=='Show hidden reminders')
OneLastThing.frame.restoreButton.scripts.OnClick()
assert(not next(OneLastThing.db.dismissed) and not next(OneLastThing.db.snoozed) and OneLastThing.db.trash['test:998'])
OneLastThing.ShowTrashBin()
assert(OneLastThing.trashFrame.title.text=='Ignored reminders (1)')
assert(OneLastThing.trashFrame.rows[1].restore.text=='Remind me again')
OneLastThing.trashFrame.rows[1].restore.scripts.OnClick();assert(not next(OneLastThing.db.trash))
OneLastThing.Refresh=originalRefresh
""")
print('PASS: direct Skip/Ignore actions, no overflow or timer controls, exact target, legacy timed-hide restore, ignored entries restored only from settings')

lua.execute("""
OneLastThingDB={};OneLastThing.Init();OneLastThing.db.filters={}
local wear=35
GetInventoryItemDurability=function(slot)
 if slot==1 then return wear,100 end
 if slot==16 then return 95,100 end
end
assert(OneLastThing.EquipmentDurability()==.35)
OneLastThing.scope={map=1454,x=.5,y=.5,name='Orgrimmar'}
OneLastThing.db.nearbyOnly=true;C_Map.GetWorldPosFromMapPos=nil
C_Map.GetPlayerMapPosition=function() return {GetXY=function() return .52,.5 end} end
LibQuestieDB={Enum={npcFlags={REPAIR=8}},Npc={
 GetAllIds=function() return {1,2,3,4} end,
 Get=function(id,key)
  if key=='npcFlags' then return id==3 and 0 or 8 end
  if key=='name' then return 'Vendor '..id end
  if key=='friendlyToFaction' then return id==2 and 'A' or 'H' end
  if key=='spawns' then return {[1637]={{id==4 and 90 or 51,50}}} end
 end}}
QuestieLoader={ImportModule=function(_,name)
 if name=='ZoneDB' then return {GetUiMapIdByAreaId=function(_,id) return id==1637 and 1454 end} end
end}
bit={band=function(a,b) return math.floor(a/b)%2==1 and b or 0 end}
local originalRefresh=OneLastThing.Refresh
OneLastThing.Refresh=function() end;timers={}
local rows={};OneLastThing.RepairRows(rows,1454);assert(#rows==0)
flushTimers();rows={};OneLastThing.RepairRows(rows,1454)
assert(#rows==1 and rows[1].repair and rows[1].title:find('35%',1,true))
assert(rows[1].detail:find('Vendor 1',1,true) and rows[1].map==1454)
-- There is only one repair reminder, and neither the hostile nor far vendor is offered.
assert(OneLastThing.FindRepairVendor(1454).name=='Vendor 1')
local row=rows[1]
OneLastThing.db.dismissed[row.key]=true;rows={};OneLastThing.RepairRows(rows,1454);assert(#rows==0)
OneLastThing.db.dismissed={};OneLastThing.db.filters['errands/repairs']=false
rows={};OneLastThing.RepairRows(rows,1454);assert(#rows==0)
OneLastThing.db.filters={};wear=40;rows={};OneLastThing.RepairRows(rows,1454);assert(#rows==0)
wear=0;rows={};OneLastThing.RepairRows(rows,1454);assert(#rows==1)
-- Repair vendors are also learned directly from the live merchant; only live prices are shown.
CanMerchantRepair=function() return true end
GetRepairAllCost=function() return 2500,true end
C_Map.GetBestMapForUnit=function() return 1454 end
OneLastThing.ObserveRepairMerchant();assert(OneLastThing.liveRepairCost==2500 and next(OneLastThing.db.repairVendors))
rows={};OneLastThing.RepairRows(rows,1454);assert(rows[1].detail:find('25s to repair all',1,true))
OneLastThing.liveRepairCost=nil;rows={};OneLastThing.RepairRows(rows,1454);assert(not rows[1].detail:find('25s',1,true))
-- Repair pins disappear after repair; no RepairAllItems/purchase API is called.
local wp={uiMapID=1454,position={x=.51,y=.5}}
C_Map.GetUserWaypoint=function() return wp end
C_Map.ClearUserWaypoint=function() wp=nil end
OneLastThing.TrackWaypoint(row,1454,.51,.5);wear=100
OneLastThing.CleanupPin();assert(not wp and not OneLastThing.db.pin)
GetInventoryItemDurability=function() return nil end
rows={};OneLastThing.RepairRows(rows,1454);assert(#rows==0 and OneLastThing.EquipmentDurability()==nil)
OneLastThing.Refresh=originalRefresh
""")
assert('RepairAllItems' not in (root/'OneLastThing/Repairs.lua').read_text())
assert('UPDATE_INVENTORY_DURABILITY' in (root/'OneLastThing/Events.lua').read_text())
print('PASS: repair threshold uses lowest equipped durability, background Questie repair index, nearby/faction filtering, one reminder, category and hide choices, broken/healthy/unknown durability, merchant observations and live g/s/c cost, repaired pin cleanup, no automatic purchases')

lua.execute("""
local originalRefresh=OneLastThing.Refresh;OneLastThing.Refresh=function() end
OneLastThingDB={};OneLastThing.Init();assert(OneLastThing.db.rowMode=='default')
local row={key='test:991',title='A compact reminder',detail='Vendor and price details'}
OneLastThing.Draw({row},'Updated');OneLastThing.SetCollapsed(false,'manual')
local w=OneLastThing.frame.rowPool[1]
assert(w:GetHeight()==91 and w.detail:IsShown())
local normalHeight=OneLastThing.frame.content:GetHeight()
OneLastThing.db.rowMode='compact';OneLastThing.Draw({row},'Updated')
assert(w:GetHeight()==51 and not w.detail:IsShown())
assert(OneLastThing.frame.content:GetHeight()<normalHeight)
assert(w.dismiss:IsShown() and w.ignore:IsShown() and not w.snooze and not w.more and w.done==nil)
local tooltipTitle,tooltipDetail,visible
GameTooltip={SetOwner=function() end,SetText=function(_,t) tooltipTitle=t end,
 AddLine=function(_,t) tooltipDetail=t end,Show=function() visible=true end,Hide=function() visible=false end}
w.scripts.OnEnter(w)
assert(visible and tooltipTitle==row.title and tooltipDetail==row.detail)
w.scripts.OnLeave();assert(not visible)
OneLastThing.SetCollapsed(true,'manual');assert(OneLastThing.db.collapsed and not OneLastThing.reminderMenu)
OneLastThing.Init();assert(OneLastThing.db.rowMode=='compact')
OneLastThing.db.rowMode='default';OneLastThing.Draw({row},'Updated');OneLastThing.SetCollapsed(false,'manual')
assert(w:GetHeight()==91 and w.detail:IsShown() and OneLastThing.frame.content:GetHeight()==normalHeight)
tooltipTitle=nil;w.scripts.OnEnter(w);assert(tooltipTitle==row.title)
OneLastThing.Refresh=originalRefresh;GameTooltip=nil
""")
print('PASS: compact rows off by default, 91-to-51 height change, all controls retained, hover details, smaller content, saved choice, normal layout restored, menu closes on collapse')

lua.execute("""
local originalRefresh=OneLastThing.Refresh;OneLastThing.Refresh=function() end
OneLastThingDB={compactRows=true};OneLastThing.Init();assert(OneLastThing.db.rowMode=='compact' and OneLastThing.db.compactRows==nil)
OneLastThing.db.rowMode='minimal'
local row={key='test:901',title='Minimal reminder',detail='Details still available',map=1454,x=50,y=40}
OneLastThing.Draw({row},'Updated');OneLastThing.SetCollapsed(false,'manual')
local w=OneLastThing.frame.rowPool[1]
assert(w:GetHeight()==27 and not w.detail:IsShown())
assert(w.go:IsShown() and w.dismiss:IsShown() and w.ignore:IsShown() and not w.more and not w.snooze)
w.dismiss.scripts.OnClick();assert(OneLastThing.db.dismissed[row.key])
OneLastThing.db.dismissed={};w.ignore.scripts.OnClick();assert(OneLastThing.db.trash[row.key])
OneLastThing.db.trash={};OneLastThing.db.rowMode='default';OneLastThing.Draw({row},'Updated')
assert(w.go:IsShown() and w.dismiss:IsShown() and w.ignore:IsShown())
OneLastThing.Init();assert(OneLastThing.db.rowMode=='default')
-- SharedMedia lists are copied, selected files are fetched without LSM defaults,
-- missing providers fall back safely without losing the saved selection.
local names={'Expressive','Readable'}
local registry={Expressive='Fonts/Expressive.ttf',Readable='Fonts/Readable.ttf'}
local registered
local lsm={List=function(_,kind) assert(kind=='font');return names end,
 Fetch=function(_,kind,name,noDefault) assert(kind=='font' and noDefault);return registry[name] end,
 RegisterCallback=function(owner,event,fn) assert(event=='LibSharedMedia_Registered');registered=fn end}
LibStub=function(name,silent) assert(name=='LibSharedMedia-3.0' and silent);return lsm end
local choices=OneLastThing.FontChoices();assert(#choices==6 and #names==2 and choices[5][1]=='lsm:Expressive')
OneLastThing.db.fontFace='lsm:Readable'
local path
local fs={SetFont=function(_,p) path=p end,SetTextColor=function() end,SetShadowColor=function() end,SetShadowOffset=function() end}
OneLastThing.Font(fs,12);assert(path=='Fonts/Readable.ttf')
OneLastThing.Init();assert(OneLastThing.db.fontFace=='lsm:Readable')
registry.Readable=nil;OneLastThing.ApplyFonts();assert(path==STANDARD_TEXT_FONT and OneLastThing.db.fontFace=='lsm:Readable')
registry.Readable='Fonts/Readable.ttf';registered('LibSharedMedia_Registered','font','Readable');assert(path=='Fonts/Readable.ttf')
for i=1,20 do names[#names+1]='Extra '..i end
OneLastThing.settings.signature=nil;OneLastThing.BuildSettings();OneLastThing.settings.fontPicker.scripts.OnClick()
assert(OneLastThing.settings.menu:GetHeight()==218 and OneLastThing.settings.menu.content:GetHeight()==#OneLastThing.FontChoices()*26)
local firstFont=OneLastThing.settings.menu.items[5];firstFont.scripts.OnClick()
assert(OneLastThing.db.fontFace=='lsm:Expressive' and path=='Fonts/Expressive.ttf')
OneLastThing.settings.layoutPicker.scripts.OnClick();OneLastThing.settings.menu.items[3].scripts.OnClick();assert(OneLastThing.db.rowMode=='minimal')
LibStub=nil;OneLastThing.ApplyFonts();assert(path==STANDARD_TEXT_FONT)
OneLastThing.Refresh=originalRefresh
""")
print('PASS: three saved modes and compact migration, minimal one-line rows with direct actions, Default controls restored, SharedMedia font enumeration/selection, safe missing-font fallback, late registration, scrollable font dropdown')

lua.execute("""
local originalRefresh=OneLastThing.Refresh;OneLastThing.Refresh=function() end
OneLastThingDB={};OneLastThing.Init()
local loaded={Attune=true,Questie=true,QuestieDB=false,SkillUpForever=true,TrainerSpells=false,NeavMedia=true}
C_AddOns={IsAddOnLoaded=function(id) return loaded[id] or false end}
LibStub=nil
OneLastThing.settings.signature=nil;OneLastThing.BuildSettings()
local f=OneLastThing.settings
assert(#f.sections==9 and f.sections[#f.sections].id=='addons')
assert(f.sectionByID.general.open and f.sectionByID.addons.open)
assert(not f.sectionByID.appearance.open and not f.sectionByID['category:supplies'].open)
assert(f.dependencyRows.Attune.state.text=='Loaded')
assert(f.dependencyRows.QuestieDB.state.text=='Not loaded')
assert(f.dependencyRows.TrainerSpells.state.text=='Not loaded')
assert(f.dependencyRows.NeavMedia.detail.text:find('Optional',1,true))
assert(f.dependencyRows['LibSharedMedia-3.0'].state.text=='Unavailable')
-- Expanding/collapsing reflows existing frames without rebuilding the form.
local controls=f.controls
local closedHeight=f.content:GetHeight()
f.sectionButtons.appearance.scripts.OnClick()
assert(f.sectionByID.appearance.open and f.sectionByID.appearance.body:IsShown())
assert(f.content:GetHeight()==closedHeight+f.sectionByID.appearance.height and f.controls==controls)
f.sectionButtons.appearance.scripts.OnClick()
assert(not f.sectionByID.appearance.open and f.content:GetHeight()==closedHeight)
f.sectionButtons['category:supplies'].scripts.OnClick()
assert(OneLastThing.db.settingsSections['category:supplies']==true)
OneLastThing.Init();f.signature=nil;OneLastThing.BuildSettings()
assert(f.sectionByID['category:supplies'].open and not f.sectionByID.appearance.open)
-- Refreshing loaded states does not reset choices or imply that media is mandatory.
loaded.QuestieDB=true;OneLastThing.BuildSettings()
assert(f.dependencyRows.QuestieDB.state.text=='Loaded' and f.sectionByID['category:supplies'].open)
LibStub=function() return {List=function() return {} end} end
OneLastThing.BuildSettings();assert(f.dependencyRows['LibSharedMedia-3.0'].state.text=='Available')
-- Legacy clients without C_AddOns still show native addon load state.
C_AddOns=nil;IsAddOnLoaded=function(id) return id=='TrainerSpells' end
local rows=OneLastThing.AddonRequirements();local byID={}
for _,r in ipairs(rows) do byID[r.id]=r end
assert(byID.TrainerSpells.loaded and not byID.Attune.loaded)
-- Collapsing a long section clamps its old scroll offset to the new bounds.
f.scroll:SetVerticalScroll(999999);OneLastThing.LayoutSettingsSections()
assert(f.scroll:GetVerticalScroll()<=math.max(0,f.content:GetHeight()-f.scroll:GetHeight()))
OneLastThing.Refresh=originalRefresh;LibStub=nil;IsAddOnLoaded=nil
""")
print('PASS: nine collapsible sections, addon requirements last, per-feature/optional explanations, actual and legacy addon load status, embedded library detection, saved expansion, no frame rebuild on toggle, content reflow and scroll bounds')

lua.execute("""
-- Custom-note removal retires only that feature's saved state and UI.
OneLastThingDB={notes={{map=1454,text='Old note'}},filters={['errands/notes']=false,['errands/repairs']=false},
 sources={NoteRows=false},supplies={[17030]={target=5,minLevel=30}},
 dismissed={['note:1']=true},snoozed={['note:2']=99999,['quest:44:start']=99999},
 trash={['note:3']={title='Old ignored note'},['quest:45']=true}}
OneLastThing.Init()
assert(OneLastThing.db.notes==nil and OneLastThing.NoteRows==nil and OneLastThing.CompleteNote==nil)
assert(OneLastThing.db.filters['errands/notes']==nil and OneLastThing.db.sources.NoteRows==nil)
assert(OneLastThing.db.filters['errands/repairs']==false and OneLastThing.db.supplies[17030].target==5)
assert(not OneLastThing.db.trash['note:3'] and OneLastThing.db.trash['quest:45'])
assert(not OneLastThing.db.snoozed['note:2'] and OneLastThing.db.snoozed['quest:44:start']==99999)
for _,cat in ipairs(OneLastThing.categories) do assert(not cat.subs.notes) end
SlashCmdList.ONELASTTHING('note Should not be created');assert(OneLastThing.db.notes==nil)
local wp={uiMapID=1454,position={x=.5,y=.4}}
C_Map.GetUserWaypoint=function() return wp end
C_Map.ClearUserWaypoint=function() wp=nil end
OneLastThing.db.pin={key='note:1',map=1454,x=.5,y=.4,note=1}
OneLastThing.CleanupPin();assert(not wp and not OneLastThing.db.pin)
OneLastThing.Draw({{key='repair:equipment',title='Repair gear',repair=true}},'Updated')
assert(OneLastThing.frame.rowPool[1].done==nil)
OneLastThing.settings.signature=nil;OneLastThing.BuildSettings()
""")
for filename in ['UI.lua','Filters.lua','Settings.lua','Events.lua']:
    assert('/olt note' not in (root/'OneLastThing'/filename).read_text())
print('PASS: custom-note command/provider/category/Done UI removed, old notes and only their hide entries retired, automatic reminder settings preserved, owned legacy-note pin cleared')

lua.execute("""
-- Recommended quest level must never be replaced with minimum acceptance level.
LibQuestieDB={Quest={Get=function(id,key)
 if key=='questLevel' then return ({[1]=30,[3]=-1,[4]=0})[id] end
 if key=='requiredLevel' then return 20 end
end}}
C_QuestLog.GetLogIndexForQuestID=function(id) return id==2 and 1 or nil end
C_QuestLog.GetInfo=function(index)
 if index==1 then return {questID=2,level=42} end
 if index==2 then return {questID=3,level=50} end
end
C_QuestLog.GetNumQuestLogEntries=function() return 2 end
assert(OneLastThing.QuestRecommendedLevel(1)==30)
assert(OneLastThing.QuestRecommendedLevel(2)==42)
assert(OneLastThing.QuestRecommendedLevel(3)==50)
assert(OneLastThing.QuestRecommendedLevel(4)==nil)
assert(OneLastThing.ReminderTitle({quest=4,title='Unknown quest'})=='[Lv ?] Unknown quest')
assert(OneLastThing.ReminderTitle({title='Restock Ankh: 1 / 3'})=='Restock Ankh: 1 / 3')
local pickup={key='quest:1:start',quest=1,title='Pick up: Example quest',detail='Example chain'}
local turnin={key='quest:2:end',quest=2,finish=true,title='Turn in: Example quest'}
assert(OneLastThing.ReminderTitle(turnin)=='[Lv 42] Turn in: Example quest')
for _,mode in ipairs({'default','compact','minimal'}) do
 OneLastThing.db.rowMode=mode
 OneLastThing.Draw({pickup},'Updated')
 assert(OneLastThing.frame.rowPool[1].title.text=='[Lv 30] Pick up: Example quest')
 assert(pickup.title=='Pick up: Example quest')
end
local tooltipTitle
GameTooltip={SetOwner=function() end,SetText=function(_,text) tooltipTitle=text end,AddLine=function() end,Show=function() end,Hide=function() end}
OneLastThing.frame.rowPool[1].scripts.OnEnter(OneLastThing.frame.rowPool[1])
assert(tooltipTitle=='[Lv 30] Pick up: Example quest')
local record=OneLastThing.MakeTrashRecord(pickup);assert(record.questLevel==30)
LibQuestieDB=nil;C_QuestLog.GetLogIndexForQuestID=nil;C_QuestLog.GetNumQuestLogEntries=nil
assert(OneLastThing.ReminderTitle({quest=1,questLevel=record.questLevel,title=record.title})=='[Lv 30] Pick up: Example quest')
GameTooltip=nil
""")
print('PASS: recommended level distinct from minimum level, quest-log fallback, unknown levels marked, pickup/turn-in labels in all layouts and tooltips, cached ignored-reminder levels, unmodified nonquest titles')

lua.execute(r"""
-- Recipe optimisation must never become a shopping or recipe-training errand.
OneLastThingDB={};OneLastThing.Init();OneLastThing.scope={noFilter=true}
C_Map.GetMapInfo=function() return {name='Orgrimmar'} end
local p={name='Alchemy',skillLineID=171,rank=145,maxRank=150,steps={
 {kind='buy',itemID=2678,count=20,text='Buy spices',detail='Vendor, Orgrimmar'},
 {kind='train',spellID=90001,itemID=90002,text='Train a route recipe',detail='Trainer, Orgrimmar'},
 {kind='train',text='Learn next rank',detail='Rank trainer, Orgrimmar',cost=1000}}}
SkillUpForever={API={version=1,Professions=function() return {p} end}}
local rows={};OneLastThing.ProfessionRows(rows,1454)
assert(#rows==2)
local rank
for _,row in ipairs(rows) do
 assert(not row.buyItem and not row.spell)
 if row.professionRank then rank=row end
end
assert(rank and rank.key=='rank:171:150')
local key=rank.key
p.steps={p.steps[3]};rows={};OneLastThing.ProfessionRows(rows,1454)
for _,row in ipairs(rows) do if row.professionRank then assert(row.key==key) end end
-- A rank pin remains until the cap increases (not merely because the old cap matches).
local wp={uiMapID=1454,position={x=.5,y=.4}}
C_Map.GetUserWaypoint=function() return wp end
C_Map.ClearUserWaypoint=function() wp=nil end
OneLastThing.TrackWaypoint(rank,1454,.5,.4);OneLastThing.CleanupPin();assert(wp and OneLastThing.db.pin)
p.maxRank=225;OneLastThing.CleanupPin();assert(not wp and not OneLastThing.db.pin)
-- Fresh installs use the built-in Arial Narrow without either media provider.
local oldAddons=C_AddOns
C_AddOns={IsAddOnLoaded=function() return false end};LibStub=nil
OneLastThingDB={};OneLastThing.Init();assert(OneLastThing.db.fontFace=='arial')
local paths={}
local fs={SetFont=function(_,path) paths[#paths+1]=path;return true end,
 SetTextColor=function() end,SetShadowColor=function() end,SetShadowOffset=function() end}
OneLastThing.Font(fs,12);assert(paths[#paths]==[[Fonts\ARIALN.TTF]])
fs.SetFont=function(_,path) paths[#paths+1]=path;return path~= [[Fonts\ARIALN.TTF]] end
OneLastThing.Font(fs,12);assert(paths[#paths]==STANDARD_TEXT_FONT)
OneLastThing.db.fontFace='expressway';OneLastThing.Init();assert(OneLastThing.db.fontFace=='expressway')
C_AddOns=oldAddons
""")
print('PASS: spices/materials and route-recipe training excluded, rank/cap reminders retained, stable rank keys, pin clears only after rank increases, fresh Arial default without media addons, fallback and existing selections preserved')

lua.execute(r"""
-- German localizes presentation while all saved keys/IDs stay unchanged.
GetLocale=function() return 'deDE' end
UnitClass=function() return 'Schamane','SHAMAN' end
OneLastThingDB={};OneLastThing.Init();OneLastThing.scope={noFilter=true}
C_Item.GetItemCount=function() return 1 end
assert(OneLastThing.Translate('Target')=='Sollbestand')
assert(OneLastThing.Translate('[Lv 30] Pick up: Ruf des Wassers')=='[St. 30] Annehmen: Ruf des Wassers')
assert(OneLastThing.Translate('Restock Ankh: 1 / 3')=='Ankh auffüllen: 1 / 3')
assert(OneLastThing.Translate('1 in bags · Need 2 more')=='1 im Inventar · 2 fehlen')
assert(OneLastThing.Translate('Buy 2 | ~20s each | ~40s total')=='2 kaufen | ~20s pro Stück | ~40s insgesamt')
assert(OneLastThing.Translate('- General & location')=='- Allgemein & Standort')
assert(OneLastThing.Translate('Font size: 110%')=='Schriftgröße: 110%')
assert(OneLastThing.Translate('One Last Thing · All done, yay!')=='One Last Thing · Alles erledigt, juhu!')
assert(OneLastThing.Translate('Named NPC α')=='Named NPC α')
GetProfessions=function() return nil,4 end
GetProfessionInfo=function(i) if i==4 then return 'Alchemie',nil,145,150,nil,nil,171 end end
assert(OneLastThing.ProfessionID('Alchemie')==171 and OneLastThing.ProfessionID('Erste Hilfe')==129)
-- Native and database names are already localized; no writes to QuestieDB locale.
LibQuestieDB={l10n={currentLocale='deDE',SetLocale=function() error('must not change provider locale') end},
 Quest={Get=function(id,key) if key=='questLevel' then return 30 end;if key=='name' then return 'Ruf des Wassers' end end}}
C_QuestLog.GetTitleForQuestID=function() return 'Ruf des Wassers' end
local row={key='quest:999:start',quest=999,title='Pick up: Ruf des Wassers',detail='Attune chain'}
for _,mode in ipairs({'default','compact','minimal'}) do
 OneLastThing.db.rowMode=mode;OneLastThing.Draw({row},'Updated')
 assert(OneLastThing.frame.rowPool[1].title.text=='[St. 30] Annehmen: Ruf des Wassers')
 assert(OneLastThing.frame.rowPool[1].dismiss.text==(mode=='minimal' and 'S' or 'Diesmal nicht'))
 assert(OneLastThing.frame.rowPool[1].ignore.text=='Ignorieren' and not OneLastThing.frame.rowPool[1].snooze)
end
OneLastThing.settings.signature=nil;OneLastThing.BuildSettings()
assert(OneLastThing.settings.sectionButtons.appearance.text=='+ Darstellung')
assert(OneLastThing.settings.dependencyRows.SkillUpForever.detail.text=='Für Berufsstufen und Bücher; für One Last Thing optional.')
assert(OneLastThing.db.filters['professions/171']==nil and OneLastThing.db.fontFace=='arial')
-- German profession metadata must not reintroduce recipe shopping tasks.
GetNumTrainerServices=function() return 1 end
GetTrainerServiceInfo=function() return 'Alchemie','available' end
GetTrainerServiceSkillReq=function() return 'Alchemie' end
GetTrainerServiceCost=function() return 1000 end
C_Map.GetBestMapForUnit=function() return 1458 end
OneLastThing.ObserveTrainer()
local found=false
for _,trainer in pairs(OneLastThing.db.trainers) do
 for _,service in pairs(trainer.services) do if service.professionID==171 then found=true end end
end
assert(not found)
GetLocale=function() return 'enUS' end
assert(OneLastThing.Translate('Target')=='Target')
GetProfessions=nil;GetProfessionInfo=nil
""")
print('PASS: deDE UI, Sollbestand, German quest/purchase/status text in all layouts, exact dynamic values preserved, native German profession/trainer IDs, untouched provider locale/settings keys, English fallback')

lua.execute("""
UnitClass=function() return 'Hunter','HUNTER' end
C_Map.GetBestMapForUnit=function() return 1454 end
OneLastThingDB={};OneLastThing.Init();OneLastThing.scope={noFilter=true}
local weapon,ammo=100,2515
GetInventorySlotInfo=function(name) return name=='AmmoSlot' and 0 or 18 end
GetInventoryItemID=function(_,slot) return slot==0 and ammo or (slot==18 and weapon) end
C_Item.GetItemInfoInstant=function(id)
 if id==100 then return id,nil,nil,nil,nil,2,2 end -- bow
 if id==101 then return id,nil,nil,nil,nil,2,3 end -- gun
 if id==102 then return id,nil,nil,nil,nil,2,18 end -- crossbow
 if id==999 then return id,nil,nil,nil,nil,6,2 end -- non-vendor special arrow
end
C_Item.GetItemNameByID=function(id) return ({[2515]='Sharp Arrow',[3030]='Razor Arrow',[2519]='Heavy Shot'})[id] end
local counts={[2515]=100,[3030]=600,[2519]=50}
C_Item.GetItemCount=function(id) return counts[id] or 0 end
local oldFind=OneLastThing.FindVendor
OneLastThing.FindVendor=function() return {map=1454,x=50,y=40,name='Ammo vendor',source='QuestieDB'} end
LibQuestieDB={Item={Get=function() return nil end}}
local id,kind,vendor=OneLastThing.HunterAmmoSelection();assert(id==2515 and kind=='arrow' and vendor)
local rows={};OneLastThing.HunterAmmoRows(rows,1454,false)
assert(#rows==1 and rows[1].ammoItem==2515 and rows[1].key=='ammo:arrow')
assert(rows[1].title=='Restock Sharp Arrow: 100 / 400')
assert(OneLastThing.db.supplies[2515]==nil) -- not duplicated into custom items
-- Exhaustion preserves the selected tier, even with a better tier in bags.
ammo=nil;counts[2515]=0
C_Container={GetContainerNumSlots=function(bag) return bag==0 and 1 or 0 end,GetContainerItemID=function() return 3030 end}
id,kind=OneLastThing.HunterAmmoSelection();assert(id==2515 and kind=='arrow')
weapon=101;ammo=2519
id,kind=OneLastThing.HunterAmmoSelection();assert(id==2519 and kind=='bullet')
rows={};OneLastThing.HunterAmmoRows(rows,1454,false);assert(#rows==1 and rows[1].ammoItem==2519)
weapon=102;ammo=nil;assert(OneLastThing.HunterAmmoSelection()==2515) -- crossbow shares arrows
-- The hunter changes tier by equipping it; no affordability/DPS upgrade selection.
ammo=3030;assert(OneLastThing.HunterAmmoSelection()==3030)
OneLastThing.SetHunterAmmoTarget(800);rows={};OneLastThing.HunterAmmoRows(rows,1454,false)
assert(#rows==1 and rows[1].title:find('600 / 800',1,true))
OneLastThing.Init();assert(OneLastThing.HunterAmmoTarget()==800 and OneLastThing.HunterAmmoSelection()==3030)
-- The current item is mapped and its pin clears after the target is reached.
local wp={uiMapID=1454,position={x=.5,y=.4}}
C_Map.GetUserWaypoint=function() return wp end
C_Map.ClearUserWaypoint=function() wp=nil end
OneLastThing.TrackWaypoint(rows[1],1454,.5,.4)
OneLastThing.CleanupPin();assert(wp and OneLastThing.db.pin)
counts[3030]=800;OneLastThing.CleanupPin();assert(not wp and not OneLastThing.db.pin)
-- Disable, category and per-visit choices are respected.
OneLastThing.EnableHunterAmmo(false);rows={};counts[3030]=10;OneLastThing.HunterAmmoRows(rows,1454,false);assert(#rows==0)
OneLastThing.EnableHunterAmmo(true);OneLastThing.db.dismissed['ammo:arrow']=true
rows={};OneLastThing.HunterAmmoRows(rows,1454,false);assert(#rows==0)
OneLastThing.BeginVisit();rows={};OneLastThing.HunterAmmoRows(rows,1454,false);assert(#rows==1)
-- Non-vendor ammo is not replaced by common ammo or turned into a shopping errand.
ammo=999;rows={};OneLastThing.HunterAmmoRows(rows,1454,false);assert(#rows==0)
assert(OneLastThing.HunterAmmoSelection()==999)
-- First use with no history chooses a matching bag item, without preferring a tier.
OneLastThing.db.hunterAmmo.last={};ammo=nil;assert(OneLastThing.HunterAmmoSelection()==3030)
OneLastThing.settings.signature=nil;OneLastThing.BuildSettings()
assert(OneLastThing.settings.hunterAmmoTarget:GetText()=='800' and OneLastThing.settings.hunterAmmoCheck)
GetLocale=function() return 'deDE' end;OneLastThing.settings.signature=nil;OneLastThing.BuildSettings()
assert(OneLastThing.settings.hunterAmmoCheck.label.text=='Ausgerüstete Munition')
GetLocale=function() return 'enUS' end
weapon=nil;rows={};OneLastThing.HunterAmmoRows(rows,1454,false);assert(#rows==0)
OneLastThing.FindVendor=oldFind
""")
print('PASS: weapon-dependent vendor ammo, selected/last-used/bag fallback, no tier upgrade, separate remembered arrows/bullets, editable saved stock, no duplicate custom entry, non-vendor exclusion, category/dismiss behavior, ammo pin cleanup, German ammo settings')

lua.execute("""
-- Ammo bought in bundles must not display a rounded, misleading '0c each'.
GetLocale=function() return 'enUS' end
GetInventoryItemID=function(_,slot) return slot==0 and 3030 or (slot==18 and 100) end
C_Item.GetItemCount=function() return 50 end
C_MerchantFrame=nil
GetMerchantNumItems=function() return 1 end
GetMerchantItemLink=function() return 'item:3030' end
GetMerchantItemInfo=function() return 'Razor Arrow',nil,5,200,-1,true,false end
OneLastThing.SetHunterAmmoTarget(400);OneLastThing.ObserveMerchant()
assert(OneLastThing.db.supplies[3030]==nil and OneLastThing.db.supplyPrices[3030].bundle==200)
local rows={};OneLastThing.HunterAmmoRows(rows,1454,true)
assert(#rows==1 and rows[1].detail:find('5c per 200',1,true) and rows[1].detail:find('10c total',1,true))
assert(not rows[1].detail:find('0c each',1,true))
GetLocale=function() return 'deDE' end
assert(OneLastThing.Translate('5c per 200')=='5c je 200')
GetLocale=function() return 'enUS' end
""")
print('PASS: selected ammo merchant observations without custom supplies, bundle-aware refill cost, no rounded zero unit cost, German bundle price')

lua.execute("""
-- Retire only old automatic non-vendor class entries, not other saved choices.
UnitClass=function() return 'Shaman','SHAMAN' end
UnitLevel=function() return 60 end
IsPlayerSpell=function() return true end
LibQuestieDB={Item={Get=function() return nil end}}
OneLastThingDB={supplies={[17030]={target=5,minLevel=30,classDefault=true},
 [17057]={target=3,classDefault=true},[17058]={target=4,classDefault=true}},filters={['professions/129']=false}}
OneLastThing.Init();local list=OneLastThing.ClassSupplyList()
assert(#list==1 and list[1][1]==17030)
assert(not OneLastThing.db.supplies[17057] and not OneLastThing.db.supplies[17058])
assert(OneLastThing.db.retiredClassSupplies[17058].target==4 and OneLastThing.db.supplies[17030].target==5)
assert(OneLastThing.db.filters['professions/129']==false)
local rows={};OneLastThing.AddSupplyReminder(rows,17058,{target=5},1454,true);assert(#rows==0)
for _,p in ipairs(list) do assert(p[1]~=5175 and p[1]~=5176 and p[1]~=5177 and p[1]~=5178) end
-- 'Vendor pays' (sellPrice) is not a seller relationship.
C_Item.GetItemInfo=function() return 'Fish Oil',nil,1,1,0,nil,nil,nil,nil,nil,500 end
assert(not OneLastThing.HasVendorSource(17058))
-- If a real merchant sells a conditional item, that is positive source evidence.
C_Map.GetBestMapForUnit=function() return 1454 end
C_Map.GetPlayerMapPosition=function() return {GetXY=function() return .5,.5 end} end
GetMerchantNumItems=function() return 1 end
GetMerchantItemLink=function() return 'item:17058' end
GetMerchantItemInfo=function() return 'Fish Oil',nil,100,1,-1,true,false end
OneLastThing.ObserveMerchant();assert(OneLastThing.HasVendorSource(17058))
OneLastThing.SyncClassSupplies();assert(OneLastThing.db.supplies[17058].target==4)
-- Tools are a non-consumed utility purchase with their own item control.
UnitClass=function() return 'Rogue','ROGUE' end
OneLastThingDB={};OneLastThing.Init()
assert(OneLastThing.db.supplies[5060].target==1 and OneLastThing.db.supplies[5060].classUtility)
assert(OneLastThing.SupplyRelevant(5060,OneLastThing.db.supplies[5060]))
assert(OneLastThing.SupplyRelevant(5140,OneLastThing.db.supplies[5140]))
OneLastThing.db.filters['supplies/5140']=false
assert(not OneLastThing.CategoryEnabled('supplies','5140'))
-- Finished poisons only enter the list when actually carried and vendor-sourced.
C_Container={GetContainerNumSlots=function(b) return b==0 and 1 or 0 end,GetContainerItemID=function() return 6947 end}
OneLastThing.SyncClassSupplies();assert(not OneLastThing.db.supplies[6947])
LibQuestieDB.Item.Get=function(id,key) if id==6947 and key=='vendors' then return {99} end end
OneLastThing.SyncClassSupplies();assert(OneLastThing.db.supplies[6947] and OneLastThing.db.supplies[6947].classUtility)
""")
print('PASS: vendor-only class defaults, corrected Shaman stock, no quest totems, sell price is not sale evidence, observed conditional vendors, archived target recovery, Thieves Tools/utility perk handling, no craft/AH poison inference')

lua.execute("""
UnitClass=function() return 'Hunter','HUNTER' end
IsPlayerSpell=function(id) return id==6991 end
UnitLevel=function(unit) return 40 end
UnitExists=function(unit) return unit=='pet' end
GetPetFoodTypes=function() return 'Meat','Fish' end
GetInventorySlotInfo=function(name)
 if name=='AmmoSlot' then return 0 end;if name=='RangedSlot' then return 18 end
 local n=name:match('Bag(%d)Slot');if n then return 20+tonumber(n) end
end
local bagEquipped
GetInventoryItemID=function(_,slot) if slot==18 then return 100 end;if slot==20 then return bagEquipped end end
C_Item.GetItemInfoInstant=function(id)
 if id==100 then return id,nil,nil,nil,nil,2,2 end
 if id==10002 then return id,nil,nil,nil,nil,11,2 end -- any owned quiver, not necessarily the small one
end
C_Item.GetItemInfo=function(id)
 local level=({[117]=5,[2287]=15,[4540]=5,[4594]=35})[id]
 if level then return 'Food '..id,nil,1,level,0 end
end
C_Item.GetItemNameByID=function(id) return 'ItemName '..id end
LibQuestieDB={Item={Get=function(id,key)
 if key=='vendors' and (id==117 or id==2287 or id==4540 or id==4594 or id==5439) then return {99} end
end}}
C_Container={GetContainerNumSlots=function(b) return b==0 and 3 or 0 end,
 GetContainerItemID=function(_,i) return ({117,4540,2287})[i] end}
OneLastThingDB={};OneLastThing.Init()
assert(OneLastThing.VendorPetFoodSelection()==2287) -- excludes too-low food and wrong diet
assert(OneLastThing.db.supplies[2287].target==10 and OneLastThing.db.supplies[5439].target==1)
OneLastThing.SelectVendorPetFood(4594)
assert(OneLastThing.VendorPetFoodSelection()==4594 and OneLastThing.db.supplies[4594])
assert(not OneLastThing.db.supplies[2287])
bagEquipped=10002;OneLastThing.SyncClassSupplies();assert(not OneLastThing.db.supplies[5439])
GetLocale=function() return 'deDE' end;GetPetFoodTypes=function() return 'Fleisch','Fisch' end
assert(OneLastThing.VendorPetFoodSelection()==4594)
OneLastThing.SelectVendorPetFood(0);assert(OneLastThing.VendorPetFoodSelection()==nil)
GetLocale=function() return 'enUS' end
""")
print('PASS: vendor pet food only, pet diet/level and German diet names, saved explicit food choice, no needless quiver when a matching bag is owned')

lua.execute("""
-- The renamed addon imports once without mutating old settings or loading an old HUD.
OneLastThingDB=nil
PitStopDB={supplies={[17030]={target=7}},filters={['quests']=false},fontFace='game'}
OneLastThing.ImportLegacySettings()
assert(OneLastThingDB.legacySettingsImported and OneLastThingDB.supplies[17030].target==7)
OneLastThingDB.supplies[17030].target=8;assert(PitStopDB.supplies[17030].target==7)
OneLastThing.ImportLegacySettings();assert(OneLastThingDB.supplies[17030].target==8)
OneLastThingDB=nil;PitStopDB=nil
local attempts=0
C_AddOns={GetAddOnMetadata=function() return nil end,LoadAddOn=function() attempts=attempts+1 end}
OneLastThing.ImportLegacySettings();assert(attempts==0 and OneLastThingDB==nil)
C_AddOns.GetAddOnMetadata=function(_,key) return key=='X-OneLastThing-Migration' and '1' end
C_AddOns.LoadAddOn=function(name) assert(name=='PitStop');attempts=attempts+1;PitStopDB={scale=1.2} end
OneLastThing.ImportLegacySettings();assert(attempts==1 and OneLastThingDB.scale==1.2)
assert(SLASH_ONELASTTHING1=='/olt' and SLASH_ONELASTTHING2=='/onelastthing' and SlashCmdList.ONELASTTHING)
PitStopDB=nil
""")
for path in (root/'OneLastThing').glob('*.lua'):
    if path.name!='Migration.lua':
        assert('PitStop' not in path.read_text() and '/pitstop' not in path.read_text())
print('PASS: One Last Thing namespace/commands, isolated legacy migration, copied per-character settings, existing new settings preserved, marked inert importer only')
# Review fixes: retain valid character choices while repairing malformed saved data.
lua.execute('''
UnitClass=function() return 'Shaman','SHAMAN' end
for _,bad in ipairs({17,{sources=true},{filters=true},{supplies={bad=true,[12]=true},snoozed={bad='x'}}}) do
 OneLastThingDB=bad;OneLastThing.Init()
 assert(type(OneLastThing.db)=='table' and type(OneLastThing.db.filters)=='table')
end
OneLastThingDB={supplyControlsV2=true,trashMigration=true,categoryMigration=true,
 auto=false,filters={['supplies/17030']=false},supplies={[17030]={target=7,minLevel=30,classDefault=true},[99999]={target=8}},
 size={width='bad',height=99999},scale='bad',opacity=99,fontFace='game',
 position={point='INVALID',relativePoint='CENTER',x=0,y=0},pin={key='supply:1',map=1458,x=.5,y=.5,supply={}},
 vendors={[17030]={[1458]={name='bad',x='bad',y=2}}},trainers={bad={services=true}},
 hunterAmmo={target='bad',last={arrow={},bullet=2516}},supplyPrices={[2]={price=2,bundle=0}},
 trash={bad={title={}},good={key='train:spell:12',title='Kept',spell=12,cost=100}}}
OneLastThing.Init()
assert(OneLastThing.db.supplies[17030].target==7 and OneLastThing.db.supplies[99999].target==8)
assert(not OneLastThing.db.auto and OneLastThing.db.filters['supplies/17030']==false and OneLastThing.db.fontFace=='game')
assert(OneLastThing.db.size.width==440 and OneLastThing.db.size.height==850 and OneLastThing.db.scale==1 and OneLastThing.db.opacity==1)
assert(not OneLastThing.db.position and not OneLastThing.db.pin)
assert(not next(OneLastThing.db.vendors[17030]) and not next(OneLastThing.db.trainers))
assert(not next(OneLastThing.db.supplyPrices) and OneLastThing.db.trash.good and not OneLastThing.db.trash.bad)
assert(OneLastThing.db.hunterAmmo.target==400 and OneLastThing.db.hunterAmmo.last.bullet==2516 and not OneLastThing.db.hunterAmmo.last.arrow)
OneLastThing.db.auto=true;OneLastThing.db.filters={}
-- Rebuilding changed values must not allocate any further frames, fontstrings or textures.
OneLastThing.settings.signature=nil;OneLastThing.BuildSettings()
local total=#frames
for i=1,20 do OneLastThing.db.supplies[17030].target=3+i;OneLastThing.BuildSettings() end
assert(#frames==total,'settings rebuild allocated '..(#frames-total)..' objects')
-- Adding and deleting dynamic rows reuses the high-water pool too.
OneLastThing.db.supplies[88888]={target=2};OneLastThing.BuildSettings()
local high=#frames
OneLastThing.db.supplies[88888]=nil;OneLastThing.BuildSettings()
OneLastThing.db.supplies[88888]={target=4};OneLastThing.BuildSettings()
assert(#frames==high)
''')
print('PASS: malformed saved-data recovery preserves valid choices; 20 target rebuilds allocate zero new UI objects; dynamic settings rows reuse pools')

# Providers: failures are distinct from empty success; dirty events invalidate only relevant caches.
lua.execute('''
OneLastThingDB={};OneLastThing.Init();OneLastThing.db.filters['quests/turnins']=true
local originals={};for _,n in ipairs({'AttuneRows','TurnInRows','ClassSpellRows','WeaponRows','FlightRows','SupplyRows'}) do originals[n]=OneLastThing[n] end
local readies={Attune_Data,Attune_DB,LibQuestieDB,TrainerSpellsClassTrainers,TrainerSpellsBuiltin,TrainerSpells_Data,C_TaxiMap}
Attune_Data={steps={},attunes={}};Attune_DB={toons={['Test Surname']={}}};LibQuestieDB={Quest={}}
TrainerSpellsClassTrainers={SHAMAN={}};TrainerSpells_Data={SHAMAN={[1]={}}};C_TaxiMap={GetTaxiNodesForMap=function() return {} end}
local names={'AttuneRows','TurnInRows','ClassSpellRows','WeaponRows','FlightRows','SupplyRows'}
OneLastThing.db.sources={};for _,n in ipairs({'ImportantVendorRows','ProfessionRows','RepairRows','TrainerRows','HunterAmmoRows','BagRows'}) do OneLastThing.db.sources[n]=false end
local calls={}
for _,name in ipairs(names) do local n=name;OneLastThing[n]=function(out,map)
 calls[n]=(calls[n] or 0)+1
 if n=='AttuneRows' then OneLastThing.Add(out,{key='quest:777777:start',quest=777777,title='Cached task',map=map,x=50,y=50}) end
end end
C_QuestLog.GetNumQuestLogEntries=function() return 0 end;C_QuestLog.GetInfo=function() end
TrainerSpellsWeaponSkills={skills={},trainers={},zones={}}
OneLastThing.scope=nil;OneLastThing.db.nearbyOnly=false;OneLastThing.InvalidateProviders()
local rows=OneLastThing.Collect(1458,false,true)
assert(#rows==1 and not OneLastThing.ChecksIncomplete())
OneLastThing.Collect(1458,false,true)
assert(calls.AttuneRows==1 and calls.ClassSpellRows==1 and calls.SupplyRows==2)
OneLastThing.InvalidateForEvent('UNIT_SPELLCAST_SENT')
OneLastThing.Collect(1458,false,true);assert(calls.AttuneRows==1 and calls.ClassSpellRows==1)
OneLastThing.InvalidateForEvent('PLAYER_MONEY');OneLastThing.Collect(1458,false,true)
assert(calls.AttuneRows==1 and calls.ClassSpellRows==2)
OneLastThing.InvalidateForEvent('BAG_UPDATE_DELAYED');OneLastThing.Collect(1458,false,true)
assert(calls.AttuneRows==2 and calls.ClassSpellRows==2)
local row=rows[1];OneLastThing.db.dismissed[row.key]=true
assert(#OneLastThing.Collect(1458,false,true)==0)
OneLastThing.db.dismissed={};assert(#OneLastThing.Collect(1458,false,true)==1)
assert(calls.AttuneRows==2,'restore should refilter cached rows, not leave them missing')
OneLastThing.AttuneRows=function(out) OneLastThing.Add(out,{key='bad',title='Partial'});error('provider broke') end
OneLastThing.Collect(1458,false,true)
assert(OneLastThing.providerHealth.AttuneRows and OneLastThing.errors.AttuneRows)
OneLastThing.Draw({},'Updated')
assert(OneLastThing.frame.title.text:find('Some checks unavailable',1,true) and not OneLastThing.frame.idleBadge)
OneLastThing.AttuneRows=function() OneLastThing.Safe('nested failure',function() error('nested') end) end
OneLastThing.Collect(1458,false,true);assert(OneLastThing.providerHealth.AttuneRows)
OneLastThing.AttuneRows=function() end;OneLastThing.Collect(1458,false,true)
assert(not OneLastThing.ChecksIncomplete() and not OneLastThing.errors.AttuneRows)
Attune_Data=nil;OneLastThing.Collect(1458,false,true);assert(OneLastThing.providerHealth.AttuneRows)
OneLastThing.db.filters.quests=false;OneLastThing.Collect(1458,false,true)
assert(not OneLastThing.providerHealth.AttuneRows and not OneLastThing.providerHealth.TurnInRows)
for name,fn in pairs(originals) do OneLastThing[name]=fn end
Attune_Data,Attune_DB,LibQuestieDB,TrainerSpellsClassTrainers,TrainerSpellsBuiltin,TrainerSpells_Data,C_TaxiMap=unpack(readies)
OneLastThing.InvalidateProviders()
''')
print('PASS: provider caching and selective invalidation, cached skip/restore, partial/nested failure reporting, disabled-source health and truthful completion')

# Map/loading/instance policy, manual reopening with automatic popups disabled.
lua.execute('''
local getMap=C_Map.GetBestMapForUnit;local update=OneLastThing.UpdateScope;local collect=OneLastThing.Collect
OneLastThing.db.auto=true;OneLastThing.frame:Show();C_Map.GetBestMapForUnit=function() return nil end
OneLastThing.Refresh('Updated',false)
assert(not OneLastThing.frame:IsShown() and not OneLastThing.scope)
C_Map.GetBestMapForUnit=getMap
local pos=C_Map.GetPlayerMapPosition
C_Map.GetPlayerMapPosition=function() return nil end
OneLastThing.frame:Show();OneLastThing.Refresh('Updated',false)
assert(not OneLastThing.frame:IsShown() and not OneLastThing.scope)
C_Map.GetPlayerMapPosition=pos
local count=0
OneLastThing.Collect=function() count=count+1;OneLastThing.providerHealth={};return {} end
IsInInstance=function() return true,'pvp' end
OneLastThing.frame:Show();OneLastThing.manualInstance=nil
OneLastThing.Refresh('Entering arena',true)
assert(count==0 and not OneLastThing.frame:IsShown())
OneLastThing.db.auto=false;SlashCmdList.ONELASTTHING('')
assert(count==1 and OneLastThing.frame:IsShown() and OneLastThing.manualInstance)
OneLastThing.frame:Hide();OneLastThing.Refresh('Merchant',true)
assert(count==1 and not OneLastThing.frame:IsShown(),'automatic event reopened a closed manual instance checklist')
OneLastThing.eventFrame.scripts.OnEvent(nil,'PLAYER_LEAVING_WORLD')
assert(not OneLastThing.frame:IsShown() and OneLastThing.loadingWorld and not OneLastThing.manualInstance)
OneLastThing.Refresh('Manual check',true,true);assert(count==1 and not OneLastThing.frame:IsShown())
OneLastThing.loadingWorld=nil;IsInInstance=function() return false,'none' end
combat=true;OneLastThing.Refresh('Manual check',true,true)
assert(OneLastThing.pending.manual)
combat=false;OneLastThing.eventFrame.scripts.OnEvent(nil,'PLAYER_REGEN_ENABLED')
assert(OneLastThing.frame:IsShown() and count==2)
OneLastThing.frame:Hide();OneLastThing.Refresh('Updated',false);assert(count==2)
OneLastThing.db.auto=true;OneLastThing.Collect=collect;OneLastThing.UpdateScope=update;OneLastThing.pending=nil
-- Repeated merchant updates are observed once, and closing cancels pending observations.
local merchant=OneLastThing.ObserveMerchant;local repair=OneLastThing.ObserveRepairMerchant;local buys=OneLastThing.ObserveImportantMerchant
local observed=0
OneLastThing.ObserveMerchant=function() observed=observed+1 end
OneLastThing.ObserveRepairMerchant=function() end;OneLastThing.ObserveImportantMerchant=function() end
timers={}
for i=1,10 do OneLastThing.eventFrame.scripts.OnEvent(nil,'MERCHANT_UPDATE') end
assert(observed==0);flushTimers();assert(observed==1)
OneLastThing.eventFrame.scripts.OnEvent(nil,'MERCHANT_UPDATE')
OneLastThing.eventFrame.scripts.OnEvent(nil,'MERCHANT_CLOSED');flushTimers();assert(observed==1)
OneLastThing.ObserveMerchant=merchant;OneLastThing.ObserveRepairMerchant=repair;OneLastThing.ObserveImportantMerchant=buys
''')
print('PASS: nil map/position hides stale HUD, loading invalidation, automatic instance suppression, manual instance/combat reopening, hidden-auto-off scan suppression and coalesced merchant observation')

# Modern pet food table and responsive German actions with measured font widths.
lua.execute('''
UnitClass=function() return 'Hunter','HUNTER' end
OneLastThingDB={};OneLastThing.Init()
UnitExists=function(unit) return unit=='pet' end;UnitLevel=function() return 40 end
IsPlayerSpell=function(id) return id==6991 end;IsSpellKnown=function() return false end
C_SpellBook={IsSpellKnown=function(id) return id==6991 end}
GetPetFoodTypes=function() error('legacy diet API must not be used') end;TrainerSpellsHunterBeasts=nil
C_PetInfo={GetPetFoodTypes=function() return {'Fleisch','Fisch'} end}
GetLocale=function() return 'deDE' end
LibQuestieDB={Item={Get=function(id,key) if key=='vendors' and id==2287 then return {1} end end}}
C_Item.GetItemInfo=function(id) return 'Food',nil,1,15,0 end
C_Container={GetContainerNumSlots=function(bag) return bag==0 and 1 or 0 end,GetContainerItemID=function() return 2287 end}
assert(OneLastThing.VendorPetFoodSelection()==2287)
assert(#OneLastThing.VendorPetFoodChoices()==2)
local row={key='supply:2287',title='Food',detail='Vendor',map=1458,x=50,y=50}
OneLastThing.providerHealth={};OneLastThing.db.rowMode='compact';OneLastThing.SetCollapsed(false,'manual');OneLastThing.Draw({row},'Manual check')
local w=OneLastThing.frame.rowPool[1]
for _,b in ipairs({w.go,w.dismiss,w.ignore}) do
 local fs=b:GetFontString();fs.GetStringWidth=function() return #(b.text or '')*9 end
end
OneLastThing.LayoutActions(w,220)
assert(w.go.text=='M' and w.dismiss.text=='S' and w.ignore.text=='Ignorieren')
local width=16
for _,b in ipairs({w.go,w.dismiss,w.ignore}) do width=width+b:GetWidth()+4 end
assert(width<=220)
OneLastThing.LayoutActions(w,900)
assert(w.go.text=='Karte' and w.dismiss.text=='Diesmal nicht')
-- Missing prerequisite + no legacy talent inspection is explicitly qualified.
UnitClass=function() return 'Shaman','SHAMAN' end
GetNumTalentTabs=nil;GetNumTalents=nil;GetTalentInfo=nil
C_Spell={GetSpellInfo=function(id) return {name='Spell '..id} end}
TrainerSpells_Data={SHAMAN={[1]={[888]={cost=10,rank=2,requires={777}}}}}
TrainerSpellsClassTrainers={SHAMAN={{faction='Horde',names={enUS='Trainer'},locations={{uiMapID=1458,x=50,y=50}}}}}
TrainerSpells_IsIgnored=function() return false end
local rows={};OneLastThing.scope=nil;OneLastThing.ClassSpellRows(rows,1458)
assert(#rows==1 and rows[1].title:find('Check training:',1,true))
assert(rows[1].detail:find('Requirements not verified',1,true))
assert(OneLastThing.Translate(rows[1].title):find('Ausbildung prüfen:',1,true))
''')
print('PASS: native 16001 pet diet table, German responsive action widths, full labels at larger widths and qualified unverified training requirements')
# Six capital maps bypass only distance, never map identity; other localities keep the saved radius.
lua.execute('''
OneLastThing.db.nearbyOnly=true;OneLastThing.db.nearbyRadius=850
local capitals={1453,1454,1455,1456,1457,1458}
for _,map in ipairs(capitals) do
 OneLastThing.scope={map=map,x=.1,y=.1}
 assert(OneLastThing.IsCapitalMap(map))
 for _,kind in ipairs({'quest','spell','flight','repair','supply'}) do
  assert(OneLastThing.ScopeAllows({key=kind..':test',map=map,x=95,y=95,quest=kind=='quest' and 1 or nil}))
 end
 assert(OneLastThing.Nearby(map,95,95)) -- repair/trainer location selection uses this helper too
 assert(not OneLastThing.ScopeAllows({map=1413,x=10,y=10,inventoryWarning=true}))
 local other=map==1453 and 1454 or 1453
 assert(not OneLastThing.ScopeAllows({map=other,x=10,y=10}))
 assert(not OneLastThing.ScopeAllows({map=map,quest=1})) -- no invented task coordinates
end
for _,map in ipairs({1413,1434,1446,1452,1451,1423}) do
 OneLastThing.scope={map=map,x=.5,y=.5}
 assert(not OneLastThing.IsCapitalMap(map))
 assert(OneLastThing.ScopeAllows({map=map,x=50.1,y=50.1}))
 assert(not OneLastThing.ScopeAllows({map=map,x=95,y=95}))
end
-- Use a known world-coordinate scale to test yard distances without the map approximation.
local oldWorld,oldVector=C_Map.GetWorldPosFromMapPos,CreateVector2D
CreateVector2D=function(x,y) return {x=x,y=y} end
C_Map.GetWorldPosFromMapPos=function(map,p) return 1,{GetXY=function() return p.x*10000,p.y*10000 end} end
OneLastThing.scope={map=1413,x=.5,y=.5}
assert(OneLastThing.Nearby(1413,58.4,50) and not OneLastThing.Nearby(1413,58.6,50))
OneLastThing.db.nearbyRadius=1200
assert(OneLastThing.Nearby(1413,61,50) and not OneLastThing.Nearby(1413,63,50))
OneLastThing.scope={map=1454,x=.1,y=.1};OneLastThing.db.nearbyRadius=250
assert(OneLastThing.Nearby(1454,95,95))
C_Map.GetWorldPosFromMapPos=nil
OneLastThing.scope={map=1413,x=.5,y=.5};OneLastThing.db.nearbyRadius=850
assert(OneLastThing.Nearby(1413,54,50) and not OneLastThing.Nearby(1413,60,50))
assert(OneLastThing.ScopeAllows({key='cap:171',professionID=171}))
-- Live slider changes refilter immediately and survive normal initialization.
local refresh=OneLastThing.Refresh;local refreshed=0
OneLastThing.Refresh=function() refreshed=refreshed+1 end
OneLastThing.db.nearbyRadius=850;OneLastThing.settings.signature=nil;OneLastThing.BuildSettings()
OneLastThing.settings.range.scripts.OnValueChanged(nil,1250)
assert(OneLastThing.db.nearbyRadius==1250 and refreshed==1)
OneLastThing.Init();assert(OneLastThing.db.nearbyRadius==1250)
local source=OneLastThing.settings.range
assert(source and OneLastThing.db.nearbyOnly)
OneLastThing.Refresh=refresh;C_Map.GetWorldPosFromMapPos=oldWorld;CreateVector2D=oldVector
''')
print('PASS: all six capitals city-wide for every located reminder, no adjacent/cross-capital leakage, outdoor yard/fallback filtering, general warnings and per-character range slider persistence')
# Header Filter menu replaces all full-line category/subcategory controls.
lua.execute('''
GetLocale=function() return 'enUS' end
UnitClass=function() return 'Shaman','SHAMAN' end
OneLastThingDB={};OneLastThing.Init();OneLastThing.providerHealth={}
OneLastThing.db.size={width=440,height=320};OneLastThing.db.rowMode='default'
local originals={refresh=OneLastThing.Refresh,collect=OneLastThing.Collect}
local testRows={
 {key='supply:17030',title='Restock Ankh: 1 / 3',detail='Vendor',map=1458,x=50,y=50},
 {key='repair:equipment',title='Repair gear',detail='Repair vendor',repair=true,map=1458,x=50,y=50}}
OneLastThing.Refresh=function()
 local rows={};for _,row in ipairs(testRows) do
  local cat,sub=OneLastThing.Category(row)
  if OneLastThing.CategoryEnabled(cat,sub) then rows[#rows+1]=row end
 end
 OneLastThing.rows=rows;OneLastThing.Draw(rows,'Updated')
end
OneLastThing.Refresh();OneLastThing.SetCollapsed(false,'manual')
local f=OneLastThing.frame
assert(#f.widgets==2 and f.widgets[1].row and f.widgets[2].row)
assert(f.content:GetHeight()==194,'category headers still occupy space')
assert(f.rowPool[1].tag and f.rowPool[1].tag.text:find('Supplies',1,true))
assert(not f.widgets[1].check and not f.widgets[2].check)
assert(f.sub.text:find('2 reminders',1,true) and not f.sub.text:find('Untick',1,true))
f.filterButton.scripts.OnClick();local m=OneLastThing.filterMenu
assert(m:IsShown())
local function find(cat,sub)
 for _,w in ipairs(m.rows) do if w:IsShown() and w.cat==cat and w.sub==sub then return w end end
end
assert(find('supplies') and find('supplies','17030') and find('errands','repairs'))
-- Parent disabling retains child preference; it can always be re-enabled here.
find('supplies').check.scripts.OnClick()
assert(OneLastThing.db.filters.supplies==false and OneLastThing.db.filters['supplies/17030']==true)
assert(f.rowCount==1 and m:IsShown() and f.filterButton.text=='Filter •')
find('supplies').check.scripts.OnClick();assert(f.rowCount==2 and OneLastThing.db.filters.supplies)
find('supplies','17030').check.scripts.OnClick()
find('errands','repairs').check.scripts.OnClick()
assert(f.rowCount==0 and m:IsShown() and not OneLastThing.db.collapsed)
assert(find('supplies','17030') and find('errands','repairs'),'hidden children became unrecoverable')
find('supplies','17030').check.scripts.OnClick();assert(f.rowCount==1 and not OneLastThing.db.collapsed)
-- Expanding/collapsing menu sections and rebuilding do not allocate repeatedly.
find('professions').expand.scripts.OnClick()
local count=#frames
for i=1,10 do OneLastThing.UpdateFilters() end
assert(#frames==count,'Filter menu did not reuse UI objects')
assert(OneLastThing.db.filterExpanded.professions==true)
-- Closing after hiding categories only closes the menu, even when no rows remain.
find('supplies','17030').check.scripts.OnClick();assert(f.rowCount==0)
OneLastThing.CloseFilters();assert(not m:IsShown() and not OneLastThing.db.collapsed)
OneLastThing.SetCollapsed(false,'manual');OneLastThing.ShowFilters(f.filterButton)
find('supplies','17030').check.scripts.OnClick();OneLastThing.CloseFilters()
assert(not OneLastThing.db.collapsed and f.rowCount==1)
-- All layouts keep Filter, omit group headers, and retain row actions.
for _,mode in ipairs({'default','compact','minimal'}) do
 OneLastThing.db.rowMode=mode;OneLastThing.Refresh();assert(#f.widgets==1 and f.widgets[1].row)
 assert(f.filterButton:IsShown() and f.widgets[1].ignore:IsShown())
end
OneLastThing.db.headerPosition='bottom';OneLastThing.ApplyCollapsed();OneLastThing.ShowFilters(f.filterButton)
assert(m:IsShown());OneLastThing.SetCollapsed(true,'manual');assert(not m:IsShown() and not f.filterButton:IsShown())
OneLastThing.SetCollapsed(false,'manual');OneLastThing.ShowFilters(f.filterButton)
f.scripts.OnHide();assert(not m:IsShown())
-- Saved category choices and expansion preferences survive initialization, with German labels.
OneLastThing.Init();assert(OneLastThing.db.filters['errands/repairs']==false and OneLastThing.db.filterExpanded.professions)
GetLocale=function() return 'deDE' end
OneLastThing.db.headerPosition='top';OneLastThing.SetCollapsed(false,'manual');OneLastThing.Refresh();OneLastThing.ShowFilters(f.filterButton)
assert(m.title.text=='Anzeigen' and find('supplies').label.text=='Vorräte')
OneLastThing.CloseFilters();OneLastThing.Refresh=originals.refresh;OneLastThing.Collect=originals.collect
''')
print('PASS: header Filter menu, no list checkmark lines, parent/child filtering and recovery, empty-menu safety, pooled controls, all layouts/header positions, saved choices and German labels')
# Importance precedes distance and visual category order; geometry uses only world-coordinate data.
lua.execute('''
GetLocale=function() return 'enUS' end
OneLastThingDB={};OneLastThing.Init();OneLastThing.db.nearbyOnly=false;OneLastThing.providerHealth={}
OneLastThing.scope={map=1454,x=.5,y=.5}
local oldWorld,oldVector=C_Map.GetWorldPosFromMapPos,CreateVector2D
CreateVector2D=function(x,y) return {x=x,y=y} end
C_Map.GetWorldPosFromMapPos=function(map,p) return 1,{GetXY=function() return p.x*10000,p.y*10000 end} end
assert(OneLastThing.IsDungeonChain({GROUPSIZE=5}) and OneLastThing.IsDungeonChain({TYPE='Dungeon'}))
AttuneLang={DUNGEONS='Dungeons',KEYS='Schlüssel'}
assert(OneLastThing.IsDungeonChain({GROUP='Dungeons'}) and OneLastThing.IsAccessChain({GROUP='Schlüssel'}))
assert(not OneLastThing.IsDungeonChain({GROUPSIZE=40,TYPE='Raid'}))
local dungeon={key='quest:1:start',quest=1,dungeonPickup=true,title='Dungeon pickup',map=1454,x=90,y=50}
local repair={key='repair:equipment',repair=true,title='Repair',map=1454,x=50.1,y=50}
local spell={key='train:spell:9',spell=9,title='Class trainer',map=1454,x=50.1,y=50}
local book={key='buybook:2',criticalBook=true,professionID=129,title='Important book',map=1454,x=60,y=50}
local class={key='quest:3:start',quest=3,classQuest=true,title='Class quest',map=1454,x=70,y=50}
local urgent={key='supply:17030',emptyEssential=true,inventoryWarning=true,title='Empty Ankhs',map=1454,x=51,y=50}
local far={key='quest:4:start',quest=4,title='Ordinary far',map=1454,x=57,y=50}
local near={key='quest:5:start',quest=5,title='Ordinary near',map=1454,x=52,y=50}
local unknown={key='quest:6:start',quest=6,title='Ordinary unknown',map=1454}
local rows={repair,spell,book,class,urgent,far,unknown,near,dungeon}
OneLastThing.SortReminders(rows)
assert(rows[1]==dungeon and rows[2]==urgent and rows[3]==class and rows[4]==book)
assert(rows[5]==near and rows[6]==far and rows[7]==unknown and rows[8]==spell and rows[9]==repair)
assert(math.abs(dungeon.distanceYards-4000)<.01 and OneLastThing.DistanceText(dungeon)=='~4000 yd')
-- Repeated destinations use one conversion per coordinate, plus one for the origin.
local conversions=0;local native=C_Map.GetWorldPosFromMapPos
C_Map.GetWorldPosFromMapPos=function(...) conversions=conversions+1;return native(...) end
OneLastThing.SortReminders({near,{key='same',title='Same NPC',map=1454,x=52,y=50}})
assert(conversions==2)
C_Map.GetWorldPosFromMapPos=nil;OneLastThing.SortReminders(rows)
assert(not dungeon.distanceYards and OneLastThing.DistanceText(dungeon)=='Distance unknown')
assert(OneLastThing.DistanceText({key='cap:171'})=='')
assert(rows[1]==dungeon)
C_Map.GetWorldPosFromMapPos=native
-- Draw must preserve global priorities rather than putting professions/training groups first.
OneLastThing.rows={};OneLastThing.db.rowMode='default';OneLastThing.SetCollapsed(false,'manual')
OneLastThing.Draw({repair,book,spell,dungeon},'Updated')
assert(OneLastThing.frame.rowPool[1].row==dungeon and OneLastThing.frame.rowPool[2].row==book)
assert(OneLastThing.frame.rowPool[1].tag.text:find('4000 yd',1,true))
for _,mode in ipairs({'compact','minimal'}) do
 OneLastThing.db.rowMode=mode;OneLastThing.Draw({spell,dungeon},'Updated')
 assert(OneLastThing.frame.rowPool[1].row==dungeon and OneLastThing.frame.rowPool[1].tag:IsShown())
end
GetLocale=function() return 'deDE' end
assert(OneLastThing.DisplayTitle({title='Train: Test',verify=true})=='[Prüfen] Lernen: Test')
assert(OneLastThing.DisplayDetail({verify=true,detail='Example'}):find('Verfügbarkeit prüfen',1,true))
assert(OneLastThing.DistanceText({map=1454,x=50,y=50})=='Entfernung unbekannt')
C_Map.GetWorldPosFromMapPos=oldWorld;CreateVector2D=oldVector
''')
print('PASS: dungeon pickups first, location-bound progression before routine services, urgent stock, distance tie-breaking, unknown distances, shared-coordinate conversion reuse and global order in all layouts')

# Estimates account for merchant bundles, partial stock, live versus remembered prices, and live target previews.
lua.execute('''
GetLocale=function() return 'enUS' end
UnitClass=function() return 'Shaman','SHAMAN' end
OneLastThingDB={};OneLastThing.Init()
local count=C_Item.GetItemCount
C_Item.GetItemCount=function(id) return id==17030 and 1 or id==3030 and 100 or 0 end
local e=OneLastThing.SupplyEstimate(17030,3)
assert(e.missing==2 and e.buy==2 and e.cost==4000 and not e.exact)
OneLastThing.db.supplyPrices[3030]={price=5,bundle=200}
e=OneLastThing.SupplyEstimate(3030,400)
assert(e.missing==300 and e.buy==400 and e.cost==10)
assert(OneLastThing.SupplyEstimateText(3030,400)=='Buy 400 · ~10c total')
OneLastThing.liveSupplyPrices={[17030]={price=1800,bundle=1}}
assert(OneLastThing.SupplyEstimateText(17030,5)=='Buy 4 · 72s total')
OneLastThing.liveSupplyPrices=nil
assert(OneLastThing.SupplyEstimate(999999,3).cost==nil)
assert(OneLastThing.SupplyEstimate(17030,1).cost==0)
-- Preview does not save a target or trigger a purchase/refresh.
OneLastThing.settings.signature=nil;OneLastThing.BuildSettings()
local input=OneLastThing.settings.supplyInputs[17030]
local saved=OneLastThing.db.supplies[17030].target
input:SetText('5');input.scripts.OnTextChanged(input)
assert(OneLastThing.db.supplies[17030].target==saved)
assert(OneLastThing.settings.supplyStatuses[17030].text:find('Buy 4',1,true))
assert(OneLastThing.settings.supplyStatuses[17030].text:find('~80s',1,true))
GetLocale=function() return 'deDE' end
assert(OneLastThing.SupplyEstimateText(17030,5)=='4 kaufen · ~80s insgesamt')
C_Item.GetItemCount=count
''')
print('PASS: bundle-aware supply cost estimates, observed-price accuracy labels, partial/stocked/unknown states, unsaved live target previews and German prices')
# Dungeon and uncertainty metadata must originate in the real Attune adapter, not just hand-made rows.
lua.execute('''
GetLocale=function() return 'enUS' end;UnitLevel=function() return 30 end
OneLastThingDB={};OneLastThing.Init();OneLastThing.scope=nil
local oldToon=OneLastThing.AttuneToon
OneLastThing.AttuneToon=function() return {done={},next={},attuned={},skip={}} end
Attune_Data={attunes={{ID='test',NAME='Dungeon chain',GROUPSIZE=5,FACTION='Both'}},
 steps={{ID=1,ID_ATTUNE='test',TYPE='Pick Up',ID_WOWHEAD='900001',FOLLOWS='0'}},
 questGivers={[900001]={1454,50,50,'Giver'}}}
LibQuestieDB={Quest={Get=function(id,key) if key=='questLevel' then return 30 end;if key=='requiredLevel' then return 1 end end}}
QuestieLoader={ImportModule=function(_,name) if name=='QuestieDB' then return {IsDoable=function() return true end} end end}
local rows={};OneLastThing.AttuneRows(rows,1454)
assert(#rows==1 and rows[1].dungeonPickup and not rows[1].verify)
QuestieLoader=nil;rows={};OneLastThing.AttuneRows(rows,1454)
assert(#rows==1 and rows[1].dungeonPickup and rows[1].verify and rows[1].title:find('Check pickup:',1,true))
OneLastThing.AttuneToon=oldToon
''')
print('PASS: real Attune adapter classifies dungeon pickups and distinguishes verified eligibility from prerequisite-only suggestions')
# A same-locality event or brief missing position must recover the visible HUD without starting a new visit.
lua.execute('''
GetLocale=function() return 'enUS' end
OneLastThingDB={};OneLastThing.Init();OneLastThing.providerHealth={}
UnitOnTaxi=function() return false end;IsInInstance=function() return false,'none' end
local position=true
C_Map.GetBestMapForUnit=function() return 1454 end
C_Map.GetPlayerMapPosition=function() if position then return {GetXY=function() return .5,.5 end} end end
GetMinimapZoneText=function() return 'Orgrimmar' end
local collect,begin=OneLastThing.Collect,OneLastThing.BeginVisit
local visits=0
OneLastThing.BeginVisit=function() visits=visits+1;begin() end
OneLastThing.Collect=function() OneLastThing.providerHealth={};return {{key='test:visible',title='Task',detail='Test'}} end
local event=OneLastThing.eventFrame.scripts.OnEvent
timers={};event(nil,'PLAYER_LEAVING_WORLD');event(nil,'PLAYER_ENTERING_WORLD');flushTimers()
assert(OneLastThing.frame:IsShown() and visits==1)
OneLastThing.db.dismissed.keep=true
event(nil,'PLAYER_CONTROL_GAINED');assert(OneLastThing.frame:IsShown() and OneLastThing.scopeRecovery)
flushTimers();assert(OneLastThing.frame:IsShown() and visits==1 and OneLastThing.db.dismissed.keep)
-- Background refresh may lose coordinates, but the existing two-second zone poll can recover.
position=false;OneLastThing.Refresh('Updated',false)
assert(OneLastThing.frame:IsShown() and OneLastThing.scopeRecovery)
position=true;event(nil,'ZONE_CHANGED_INDOORS');flushTimers()
assert(OneLastThing.frame:IsShown() and not OneLastThing.scopeRecovery and visits==1)
-- An explicitly closed popup must not be resurrected by that recovery path.
event(nil,'ZONE_CHANGED');OneLastThing.frame.close.scripts.OnClick();flushTimers()
assert(not OneLastThing.frame:IsShown() and not OneLastThing.scopeRecovery)
-- A manually opened HUD with auto opening disabled also recovers after a transient event.
OneLastThing.db.auto=false;SlashCmdList.ONELASTTHING('')
assert(OneLastThing.frame:IsShown())
event(nil,'ZONE_CHANGED_INDOORS');flushTimers();assert(OneLastThing.frame:IsShown() and not OneLastThing.db.auto)
-- It remains an OLT badge after successful completion; it is not an Escape-close window.
for _,name in ipairs(UISpecialFrames) do assert(name~='OneLastThingPopup') end
OneLastThing.providerHealth={};OneLastThing.Draw({},'Updated')
OneLastThing.db.collapsed=true;OneLastThing.frame.rowCount=0
OneLastThing.frame.headerHovered=false;OneLastThing.frame.idleBadge=false;OneLastThing.frame.idleWaiting=false;OneLastThing.frame.fadeElapsed=nil
OneLastThing.StartCompletionIdle();flushTimers();OneLastThing.frame.header.scripts.OnUpdate(nil,.4)
assert(OneLastThing.frame:IsShown() and OneLastThing.frame.title.text=='OLT')
OneLastThing.Collect=collect;OneLastThing.BeginVisit=begin
-- Locate the existing Check button in unchanged bottom controls and verify both tooltip languages.
local check
for _,w in ipairs(OneLastThing.frame.chrome) do if w.text=='Check' then check=w end end
assert(check)
local tooltip
GameTooltip={SetOwner=function() end,SetText=function(_,value) tooltip=value end,Show=function() end,Hide=function() end}
check.scripts.OnEnter(check);assert(tooltip:find('Refresh the checklist',1,true))
GetLocale=function() return 'deDE' end;check.scripts.OnEnter(check)
assert(tooltip:find('Aktualisiert die Liste',1,true))
GameTooltip=nil
''')
print('PASS: same-location/control and missing-position recovery, visit skips preserved, deliberate closure respected, manual-auto-off recovery, persistent idle marker and bilingual Check tooltip')
# Ordinary quest turn-ins are opt-in without hiding important tracked-chain turn-ins.
lua.execute('''
OneLastThingDB={};OneLastThing.Init();OneLastThing.scope=nil
assert(OneLastThing.db.filters['quests/turnins']==false)
assert(not OneLastThing.ProviderEnabled('TurnInRows') and OneLastThing.ProviderEnabled('AttuneRows'))
assert(OneLastThing.categories[1].subs.turnins=='Other completed quests','disabled option must remain discoverable')
local ordinary={key='quest:527:end',quest=527,finish=true,title='Turn in: Battle of Hillsbrad'}
local important={key='quest:999999:end',quest=999999,finish=true,title='Turn in: Important chain',attuneStep={ID_ATTUNE='important'}}
local rows={};OneLastThing.Add(rows,ordinary);OneLastThing.Add(rows,important)
assert(#rows==1 and rows[1]==important)
local refresh=OneLastThing.Refresh;OneLastThing.Refresh=function() end
OneLastThing.SetCategory('quests','turnins',true)
rows={};OneLastThing.Add(rows,ordinary);assert(#rows==1)
OneLastThing.Init();assert(OneLastThing.db.filters['quests/turnins']==true,'explicit opt-in lost on reload')
OneLastThing.SetCategory('quests','turnins',false)
OneLastThing.Init();assert(OneLastThing.db.filters['quests/turnins']==false)
-- Existing characters with no child choice get the new default; explicit existing choices remain intact.
OneLastThingDB={filters={quests=true},supplies={[17030]={target=6,minLevel=30,classDefault=true}},supplyControlsV2=true}
OneLastThing.Init();assert(OneLastThing.db.filters['quests/turnins']==false and OneLastThing.db.filters.quests==true)
assert(OneLastThing.db.supplies[17030].target==6)
OneLastThingDB={filters={['quests/turnins']=true}};OneLastThing.Init()
assert(OneLastThing.db.filters['quests/turnins']==true)
OneLastThing.Refresh=refresh
''')
print('PASS: ordinary turn-ins default off, important-chain turn-ins retained, option always discoverable, opt-in/opt-out persistence and existing-character defaults preserve other settings')
# Essential books can be bought ahead without broadening quest eligibility or adding recipe shopping.
lua.execute('''
GetLocale=function() return 'enUS' end
OneLastThingDB={};OneLastThing.Init();OneLastThing.scope=nil
local level,money=10,10000
UnitLevel=function() return level end;GetMoney=function() return money end
local bags,bank={},{}
C_Item.GetItemCount=function(id,includeBank) return (bags[id] or 0)+(includeBank and (bank[id] or 0) or 0) end
C_Item.GetItemNameByID=function(id) return 'Book '..id end
local profession={skillLineID=356,name='Fishing',rank=110,maxRank=150,steps={}}
SkillUpForever={API={version=1,Professions=function() return {profession} end}}
local find=OneLastThing.FindVendor
OneLastThing.FindVendor=function() return {map=1454,x=50,y=50,name='Book seller'} end
OneLastThing.importantOffers=nil
local rows={};OneLastThing.ImportantVendorRows(rows,1454)
assert(#rows==1 and rows[1].buyItem==16083 and rows[1].buyAhead)
assert(rows[1].title=='Buy ahead: Book 16083')
assert(rows[1].detail:find('Requires Fishing 125 · current 110',1,true))
assert(rows[1].detail:find('Requires level 20 · current 10',1,true))
assert(OneLastThing.DisplayDetail(rows[1]):find('Requires Fishing',1,true))
assert(not OneLastThing.DisplayDetail(rows[1]):find('avoid a return trip',1,true))
assert(OneLastThing.DisplayDetail(rows[1],true):find('avoid a return trip',1,true))
local book=rows[1]
bank[16083]=1;rows={};OneLastThing.ImportantVendorRows(rows,1454);assert(#rows==0)
bank[16083]=nil;bags[16083]=1;rows={};OneLastThing.ImportantVendorRows(rows,1454);assert(#rows==0)
bags[16083]=nil;profession.maxRank=225;rows={};OneLastThing.ImportantVendorRows(rows,1454);assert(#rows==0)
profession.maxRank=150;money=9999;rows={};OneLastThing.ImportantVendorRows(rows,1454);assert(#rows==0)
money=10000;profession.rank=0;profession.maxRank=0;rows={};OneLastThing.ImportantVendorRows(rows,1454);assert(#rows==0)
profession.rank=110;profession.maxRank=150
OneLastThing.importantOffers={[16083]={map=1454,x=50,y=50,name='Book seller',price=8000,stock=0,purchasable=true}}
rows={};OneLastThing.ImportantVendorRows(rows,1454);assert(#rows==0)
OneLastThing.importantOffers[16083].stock=1
rows={};OneLastThing.ImportantVendorRows(rows,1454);assert(#rows==1 and rows[1].cost==8000 and not rows[1].verify)
profession.rank=125;level=20;rows={};OneLastThing.ImportantVendorRows(rows,1454)
assert(#rows==1 and not rows[1].buyAhead and rows[1].title:find('Unlock next rank:',1,true))
assert(OneLastThing.DisplayDetail(rows[1]):find('Profession rank book',1,true))
-- Filters still apply and the fixed shortlist remains capped at two reminders.
OneLastThing.db.filters['professions/356']=false;rows={};OneLastThing.ImportantVendorRows(rows,1454);assert(#rows==0)
OneLastThing.db.filters={};OneLastThing.importantOffers=nil
SkillUpForever.API.Professions=function() return {
 {skillLineID=129,name='First Aid',rank=125,maxRank=150},
 {skillLineID=185,name='Cooking',rank=50,maxRank=75},
 {skillLineID=356,name='Fishing',rank=50,maxRank=75}} end
rows={};OneLastThing.ImportantVendorRows(rows,1454)
assert(#rows==2 and rows[1].buyItem==16084 and not rows[1].buyAhead)
-- A banked early purchase also completes its owned map pin.
local live={uiMapID=1454,position={x=.5,y=.5}};local cleared=false
C_Map.GetUserWaypoint=function() return live end;C_Map.GetUserWaypointHyperlink=function() end
C_Map.ClearUserWaypoint=function() live=nil;cleared=true end
OneLastThing.TrackWaypoint(book,1454,.5,.5);bank[16083]=1;OneLastThing.CleanupPin()
assert(cleared and not OneLastThing.db.pin)
GetLocale=function() return 'deDE' end
assert(OneLastThing.DisplayTitle(book):find('Auf Vorrat kaufen:',1,true))
assert(OneLastThing.DisplayDetail(book):find('Benötigt Angeln 125 · aktuell 110',1,true))
assert(OneLastThing.DisplayDetail(book):find('Benötigt Stufe 20 · aktuell 10',1,true))
OneLastThing.FindVendor=find
''')
print('PASS: early profession books below skill/player requirements, requirement text, owned/banked/learned/affordability/stock/filter suppression, ready-first shortlist, banked-purchase pin cleanup and German wording')

lua.execute('''
GetLocale=function() return 'enUS' end
local dungeon={ID='d',NAME='Test Dungeon',GROUPSIZE=5}
local class={ID='c',NAME='Test Class',CLASS='SHAMAN'}
local access={ID='a',NAME='Test Access',TYPE='Raid'}
assert(OneLastThing.ChainWhy(dungeon,false)=='Pick up before entering the dungeon: Test Dungeon')
assert(OneLastThing.ChainWhy(dungeon,true)=='Dungeon quest chain: Test Dungeon')
assert(OneLastThing.ChainWhy(class,false)=='Part of your class progression: Test Class')
assert(OneLastThing.ChainWhy(access,false)=='Raid/access progression: Test Access')
assert(OneLastThing.ChainWhy({ID='ordinary',NAME='Ordinary'},false)==nil)
local row={key='quest:7:start',title='Pick up: Test',detail='Giver | Chain',why=OneLastThing.ChainWhy(dungeon,false),dungeonPickup=true,quest=7}
local detail=OneLastThing.DisplayDetail(row)
assert(detail:find('Pick up before entering',1,true) and detail:find('Giver | Chain',1,true))
row.gray=true;row.importantReason='Grey prerequisite — leads to level 35 Later quest'
detail=OneLastThing.DisplayDetail(row)
assert(detail:find('Grey prerequisite',1,true) and detail:find('Giver | Chain',1,true))
local saved=OneLastThing.MakeTrashRecord(row);assert(saved.why==row.why and saved.importantReason==row.importantReason)
GetLocale=function() return 'deDE' end
assert(OneLastThing.Translate(OneLastThing.ChainWhy(dungeon,false))=='Vor dem Dungeonbesuch abholen: Test Dungeon')
assert(OneLastThing.Translate(OneLastThing.ChainWhy(access,false))=='Schlachtzug-/Zugangsquestreihe: Test Access')
''')
print('PASS: data-backed dungeon/class/access reasons, no invented ordinary-chain rewards, grey-prerequisite reason preserved with NPC details, ignored-record preservation and German explanations')
# Every supported profession uses the shared rank-location and reason path, not a character-specific whitelist.
lua.execute('''
GetLocale=function() return 'enUS' end
OneLastThingDB={};OneLastThing.Init();OneLastThing.scope=nil
UnitFactionGroup=function() return 'Horde' end;UnitLevel=function() return 30 end
local professions={}
for _,category in ipairs(OneLastThing.categories) do if category.id=='professions' then
 for id,name in pairs(category.subs) do professions[#professions+1]={id=tonumber(id),name=name} end
end end
assert(#professions==12)
TrainerSpellsProfessionTrainers={}
for _,p in ipairs(professions) do TrainerSpellsProfessionTrainers[p.name]={
 {rank=1,faction='H',names={enUS='Insufficient rank'},locations={{uiMapID=1454,x=49,y=50}}},
 {rank=2,faction='A',names={enUS='Wrong faction'},locations={{uiMapID=1454,x=49,y=50}}},
 {rank=2,faction='H',names={enUS='Rank trainer',deDE='Berufslehrer'},locations={{uiMapID=1454,x=50,y=50}}}} end
C_Map.GetMapInfo=function() return {name='Other zone'} end
for _,p in ipairs(professions) do
 local entry={skillLineID=p.id,name=p.name,rank=60,maxRank=75,steps={{kind='train',text='Next rank',cost=100,detail='Some other zone'}}}
 SkillUpForever={API={version=1,Professions=function() return {entry} end}}
 local rows={};OneLastThing.ProfessionRows(rows,1454)
 assert(#rows==1 and rows[1].professionID==p.id and rows[1].x==50 and rows[1].y==50,p.name)
 assert(rows[1].detail:find('Rank trainer',1,true) and rows[1].why=='Profession rank progression: '..p.name)
 assert(rows[1].verify)
 rows={};OneLastThing.ProfessionRows(rows,1434);assert(#rows==0,'rank trainer leaked to another map')
end
-- Current client language does not change the canonical profession ID/provider key.
local p={skillLineID=171,name='Alchemie',rank=60,maxRank=75,steps={{kind='train',text='Nächste Stufe',cost=100}}}
GetLocale=function() return 'deDE' end
SkillUpForever.API.Professions=function() return {p} end
local rows={};OneLastThing.ProfessionRows(rows,1454)
assert(#rows==1 and rows[1].detail:find('Berufslehrer',1,true))
assert(OneLastThing.DisplayDetail(rows[1]):find('Nächste Berufsstufe: Alchemie',1,true))
-- Rank quests still respect known acceptance levels and use the actual hand-in when ready.
GetLocale=function() return 'enUS' end
local savedDone,savedActive,savedReady=OneLastThing.QuestDone,OneLastThing.QuestActive,OneLastThing.QuestReady
local done,active,ready=false,false,false
OneLastThing.QuestDone=function() return done end
OneLastThing.QuestActive=function() return active end
OneLastThing.QuestReady=function() return ready end
LibQuestieDB={Quest={Get=function(id,key) if key=='requiredLevel' then return 35 end end}}
p={skillLineID=129,name='First Aid',rank=225,maxRank=225,steps={{kind='train',text='Artisan',questID=900009}}}
SkillUpForever.API.Professions=function() return {p} end
local location=OneLastThing.QuestLocation
OneLastThing.QuestLocation=function(id,finish,map) return map,finish and 60 or 50,50,'Quest NPC' end
rows={};OneLastThing.ProfessionRows(rows,1454)
for _,row in ipairs(rows) do assert(not row.quest,'under-level profession quest offered') end
UnitLevel=function() return 40 end;active=true;ready=true
rows={};OneLastThing.ProfessionRows(rows,1454)
local handin
for _,row in ipairs(rows) do if row.quest then handin=row end end
assert(handin and handin.finish and handin.x==60 and handin.title:find('Turn in rank quest',1,true))
OneLastThing.QuestLocation=location
OneLastThing.QuestDone,OneLastThing.QuestActive,OneLastThing.QuestReady=savedDone,savedActive,savedReady
''')
print('PASS: shared rank reminders and reasons for all twelve professions, faction/rank/map checks, German profession IDs, quest minimum-level gate and actual rank-quest hand-in location')
# Native widget script contracts are enforced for the entire suite, including nil-handler resets.
lua.execute('''
GetLocale=function() return 'enUS' end
local oldClass=UnitClass
for _,class in ipairs({'SHAMAN','MAGE','HUNTER','WARRIOR'}) do
 UnitClass=function() return class,class end
 OneLastThingDB={};OneLastThing.Init();OneLastThing.ShowSettings()
 OneLastThing.settings.signature=nil;OneLastThing.BuildSettings()
 local high=#frames
 for i=1,5 do OneLastThing.settings.signature=nil;OneLastThing.BuildSettings() end
 assert(#frames==high,'alt settings rebuild allocated more widgets')
end
UnitClass=oldClass
OneLastThingDB={};OneLastThing.Init();OneLastThing.db.rowMode='default'
OneLastThing.providerHealth={};OneLastThing.rows={}
OneLastThing.Draw({{key='font:test',title='Font test',detail='Details'}},'Manual check')
OneLastThing.SetCollapsed(false,'manual')
local f=OneLastThing.frame
local width,height=f:GetWidth(),f:GetHeight()
local savedWidth,savedHeight=OneLastThing.db.size.width,OneLastThing.db.size.height
local fs=f.rowPool[1].title;local setFont=fs.SetFont;local points
fs.SetFont=function(_,path,size,outline) points=size;return true end
local slider=OneLastThing.settings.fontSize;local setValue=slider.SetValue;local shownValue
slider.SetValue=function(self,value)
 shownValue=value
 local onChange=self:GetScript('OnValueChanged');if onChange then onChange(self,value) end
end
OneLastThing.db.fontScale=1
f.larger.scripts.OnClick()
assert(OneLastThing.db.fontScale==1.05 and math.abs(points-12*1.05)<.001)
assert(shownValue==105)
f.smaller.scripts.OnClick();assert(OneLastThing.db.fontScale==1)
assert(f:GetWidth()==width and f:GetHeight()==height)
assert(OneLastThing.db.size.width==savedWidth and OneLastThing.db.size.height==savedHeight)
for i=1,20 do f.smaller.scripts.OnClick() end
assert(OneLastThing.db.fontScale==.8)
for i=1,30 do f.larger.scripts.OnClick() end
assert(OneLastThing.db.fontScale==1.3)
OneLastThing.Init();assert(OneLastThing.db.fontScale==1.3)
local value
GameTooltip={SetOwner=function() end,SetText=function(_,text) value=text end,Show=function() end,Hide=function() end}
f.smaller.scripts.OnEnter(f.smaller);assert(value=='Decrease font size')
GetLocale=function() return 'deDE' end
f.larger.scripts.OnEnter(f.larger);assert(value=='Schrift vergrößern')
f.grip.scripts.OnEnter(f.grip);assert(value=='Ziehen, um die Fenstergröße zu ändern.')
GameTooltip=nil;fs.SetFont=setFont;slider.SetValue=setValue
''')
print('PASS: native script-type checks across all settings rebuilds, four-class alt reuse, +/- changes fonts only, settings synchronization, saved limits and bilingual tooltips')
# Settings dropdowns dismiss normally without intercepting unrelated mouse clicks.
lua.execute('''
GetLocale=function() return 'enUS' end
OneLastThingDB={};OneLastThing.Init();OneLastThing.ShowSettings()
local f=OneLastThing.settings
local previousRegistrations=0
for _,name in ipairs(UISpecialFrames) do if name=='OneLastThingSettingsDropdown' then previousRegistrations=previousRegistrations+1 end end
if f.menu then f.menu:Hide() end;f.menu=nil
local originalCreate=CreateFrame
CreateFrame=function(kind,name,...)
 local frame=originalCreate(kind,name,...)
 if name=='OneLastThingSettingsDropdown' then frame.shown=true end
 return frame
end
f.fontPicker.scripts.OnClick();local menu=f.menu
CreateFrame=originalCreate
assert(menu:IsShown() and menu.events.GLOBAL_MOUSE_DOWN,'first-open listener missing on initially shown native frame')
assert(menu.anchor==f.fontPicker)
-- A click inside the list keeps it open for selection/scrolling.
menu.mouseOver=true;menu.scripts.OnEvent(menu,'GLOBAL_MOUSE_DOWN','LeftButton')
assert(menu:IsShown())
-- The anchor toggles it closed; clicking elsewhere closes without changing a value.
menu.mouseOver=false;f.fontPicker.mouseOver=true
menu.scripts.OnEvent(menu,'GLOBAL_MOUSE_DOWN','LeftButton');assert(menu:IsShown())
f.fontPicker.scripts.OnClick();assert(not menu:IsShown() and not menu.events.GLOBAL_MOUSE_DOWN)
f.fontPicker.mouseOver=false
f.fontPicker.scripts.OnClick();local font=OneLastThing.db.fontFace
menu.scripts.OnEvent(menu,'GLOBAL_MOUSE_DOWN','LeftButton')
assert(not menu:IsShown() and not menu.events.GLOBAL_MOUSE_DOWN and OneLastThing.db.fontFace==font)
-- Clicking another picker can open its list on the same click.
f.fontPicker.scripts.OnClick();menu.scripts.OnEvent(menu,'GLOBAL_MOUSE_DOWN','LeftButton')
f.layoutPicker.scripts.OnClick();assert(menu:IsShown() and menu.anchor==f.layoutPicker)
menu.items[2].scripts.OnClick();assert(OneLastThing.db.rowMode=='compact' and not menu:IsShown())
-- Scrolling or moving the settings window closes the list, as does any hide path.
f.fontPicker.scripts.OnClick();f.scroll.scripts.OnMouseWheel(f.scroll,-1);assert(not menu:IsShown())
f.fontPicker.scripts.OnClick();f.scripts.OnDragStart(f);assert(not menu:IsShown())
f.fontPicker.scripts.OnClick();f:Hide();assert(not menu:IsShown() and not menu.events.GLOBAL_MOUSE_DOWN)
-- Native Escape-close registration exists once; repeated openings reuse controls.
f:Show();f.fontPicker.scripts.OnClick();local count=#frames
menu:Hide()
for i=1,10 do f.fontPicker.scripts.OnClick();menu:Hide() end
assert(#frames==count)
local registrations=0
for _,name in ipairs(UISpecialFrames) do if name=='OneLastThingSettingsDropdown' then registrations=registrations+1 end end
assert(registrations==previousRegistrations+1)
''')
print('PASS: settings dropdown outside-click/anchor/selection dismissal, first native-shown creation, switching pickers, parent hide/drag/scroll cleanup, Escape registration and pooled reuse')

# Independent VMs cover clean starts instead of inheriting this suite's globals.
from test_startup import run as run_startup_tests
from test_stability import run as run_stability_tests
run_startup_tests()
run_stability_tests()
from test_refinements import run as run_refinement_tests
run_refinement_tests()
from test_flights import run as run_flight_tests
run_flight_tests()
from test_city_visits import run as run_city_visit_tests
run_city_visit_tests()
from test_mage_portals import run as run_mage_portal_tests
run_mage_portal_tests()
from test_row_actions import run as run_row_action_tests
run_row_action_tests()
from test_profession_recipes import run as run_profession_recipe_tests
run_profession_recipe_tests()

from test_profession_ranks import run as run_profession_ranks
run_profession_ranks()

from test_profession_progression import run as run_profession_progression
run_profession_progression()

from test_dungeonjournal import run as run_dungeonjournal
run_dungeonjournal()

from test_supply_controls import run as run_supply_controls
run_supply_controls()

from test_ui_polish import run as run_ui_polish
run_ui_polish()

from test_rank_requirements import run as run_rank_requirements
run_rank_requirements()

from test_neav_themes import run as run_neav_themes
run_neav_themes()

from test_review_fixes import run as run_review_fixes
run_review_fixes()

from test_explanations import run as run_explanations
run_explanations()

from test_filter_toggle import run as run_filter_toggle
run_filter_toggle()

from test_flight_cleanup import run as run_flight_cleanup
run_flight_cleanup()

from test_settings_polish import run as run_settings_polish
run_settings_polish()
