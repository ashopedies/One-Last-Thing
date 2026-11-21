-- Strict, fresh-runtime WoW UI fixtures for isolated startup tests.

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
