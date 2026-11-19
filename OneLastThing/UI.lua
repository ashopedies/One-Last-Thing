local _, A = ...
local function button(parent,text,w,click)
    local b=CreateFrame('Button',nil,parent,'BackdropTemplate')
    local label=b:CreateFontString(nil,'OVERLAY','GameFontHighlightSmall');label:SetPoint('CENTER');b:SetFontString(label)
    b:SetSize(w,23);A.SetText(b,text);b:SetScript('OnClick',click);A.StyleButton(b)
    return b
end
local function hint(b,text)
    local enter,leave=b:GetScript('OnEnter'),b:GetScript('OnLeave')
    b:SetScript('OnEnter',function(self)
        if enter then enter(self) end
        if GameTooltip then GameTooltip:SetOwner(self,'ANCHOR_TOP');A.SetText(GameTooltip,text,nil,nil,nil,nil,true);GameTooltip:Show() end
    end)
    b:SetScript('OnLeave',function(self) if leave then leave(self) end;if GameTooltip then GameTooltip:Hide() end end)
end
function A.ShowReminderMenu(anchor,row)
    if A.CloseFilters then A.CloseFilters() end
    local m=A.reminderMenu
    if m and m:IsShown() and m.row==row then m:Hide();return end
    if not m then
        m=CreateFrame('Frame','OneLastThingReminderMenu',UIParent,'BackdropTemplate');A.reminderMenu=m
        m:SetFrameStrata('DIALOG');m:SetClampedToScreen(true);m.pitSettingsBackground=true;A.Panel(m)
        local function action(label,fn)
            return button(m,label,230,function() local selected=m.row;m:Hide();if selected then fn(selected) end end)
        end
        m.map=action('Map',A.Navigate);m.skip=action('Skip this visit',A.Dismiss)
        m.timed=action('Hide for 30m',function(r) A.Snooze(r) end)
        m.ignore=action('Don’t remind again',A.Trash);A.Tint(m.ignore:GetFontString(),'urgent')
        m.help=m:CreateFontString(nil,'OVERLAY','GameFontHighlightSmall');m.help:SetWidth(230);m.help:SetHeight(22)
        A.SetText(m.help,'Manage in Settings > Ignored reminders');A.Font(m.help,10,true)
        m.cancel=button(m,'Cancel',230,function() m:Hide() end)
        table.insert(UISpecialFrames,'OneLastThingReminderMenu')
    end
    local minimal=A.db.rowMode=='minimal'
    m.map:SetShown(minimal and ((row.map and row.x and row.y) or row.skill~=nil or row.attuneStep~=nil) and true or false)
    m.skip:SetShown(minimal);m.timed:SetShown(minimal)
    m.ignore:Show()
    local y=7
    for _,control in ipairs({m.map,m.skip,m.timed,m.ignore}) do
        if control:IsShown() then control:ClearAllPoints();control:SetPoint('TOPLEFT',9,-y);y=y+27 end
    end
    m.help:ClearAllPoints();m.help:SetPoint('TOPLEFT',9,-y);y=y+26
    m.cancel:ClearAllPoints();m.cancel:SetPoint('TOPLEFT',9,-y)
    m:SetSize(248,y+30)
    m.row=row;m:ClearAllPoints();m:SetPoint('TOPRIGHT',anchor,'BOTTOMRIGHT',0,-3);m:Show()
end
local function savePosition(f)
    local point,_,relativePoint,x,y=f:GetPoint(1)
    A.db.position={point=point,relativePoint=relativePoint,x=x,y=y}
end
function A.RowNavigable(row)
    return row~=nil and ((row.map~=nil and row.x~=nil and row.y~=nil) or row.skill~=nil or row.attuneStep~=nil)
end
function A.StyleRow(w)
    if not (w and w.row) then return end
    local pinned=A.IsPinnedRow and A.IsPinnedRow(w.row) or false
    w.oltPinned=pinned
    if w.accent then
        local r,g,b=A.ToneColor(pinned and 'action' or A.RowTone(w.row))
        w.accent:SetWidth(pinned and 3 or 2)
        w.accent:SetColorTexture(r,g,b,pinned and .95 or .68)
    end
    if w.hoverBg then
        if w.hovered then
            local r,g,b=A.ToneColor(pinned and 'action' or 'text')
            w.hoverBg:SetColorTexture(r,g,b,.11)
        elseif pinned then
            local r,g,b=A.ToneColor('action')
            w.hoverBg:SetColorTexture(r,g,b,.07)
        else
            w.hoverBg:SetColorTexture(0,0,0,0)
        end
    end
    if A.ApplyBorder then A.ApplyBorder(w) end
end
function A.UpdateRowPinStates()
    local f=A.frame;if not f or not f.widgets then return end
    local content=f:GetWidth()-32
    for _,w in ipairs(f.widgets) do
        if w.row then
            A.StyleRow(w)
            if not A.db.collapsed then A.LayoutActions(w,content) end
        end
    end
end
function A.LayoutActions(w,width)
    if not w.go then return end
    local minimal=A.db.rowMode=='minimal'
    local pinned=A.IsPinnedRow and A.IsPinnedRow(w.row)
    local mapLabel=pinned and 'Map •' or 'Map'
    local mapShort=pinned and 'M•' or 'M'
    local controls={{w.go,mapLabel,mapShort,44},{w.dismiss,'Skip this visit','S',108},{w.snooze,'Hide for 30m','30m',98},{w.more,'...','...',26}}
    local needed=16
    for _,c in ipairs(controls) do if c[1]:IsShown() then
        A.SetText(c[1],c[2]);local fs=c[1]:GetFontString()
        local measured=fs and fs.GetStringWidth and fs:GetStringWidth() or 0
        c.width=math.max(c[4],math.ceil(measured+16));needed=needed+c.width+4
    end end
    local small=needed>width
    local left=8
    for _,c in ipairs(controls) do local b=c[1];if b:IsShown() then
        A.SetText(b,small and c[3] or c[2]);local fs=b:GetFontString()
        local measured=fs and fs.GetStringWidth and fs:GetStringWidth() or 0
        b:SetWidth(small and math.max(26,math.ceil(measured+12)) or c.width)
        b:ClearAllPoints();b:SetPoint('BOTTOMLEFT',w,'BOTTOMLEFT',left,A.db.rowMode=='default' and 7 or 4)
        left=left+b:GetWidth()+4
    end end
    if minimal then w.more:ClearAllPoints();w.more:SetPoint('RIGHT',w,'RIGHT',-8,0) end
end
A.shortCategoryNames={quests='Quests',professions='Professions',training='Training',supplies='Supplies',errands='Errands'}
local function rowLabel(w,width)
    if not w.tag then return end
    local minimal=A.db.rowMode=='minimal'
    local distance=A.DistanceText(w.row)
    local category=A.Translate(w.categoryLabel or '')
    local value=distance~='' and distance or category
    if not minimal and width>=400 and distance~='' then value=category..' · '..distance end
    local show=value~='' and (distance~='' or (width>=360 and not minimal))
    A.SetText(w.tag,value);w.tag:SetWidth(0)
    local tagWidth=0
    if show then tagWidth=math.min(160,width*.40,(w.tag.GetStringWidth and w.tag:GetStringWidth() or 80)+3);w.tag:SetWidth(tagWidth) end
    w.tag:SetShown(show)
    w.tag:ClearAllPoints();w.tag:SetPoint('TOPRIGHT',minimal and -44 or -9,A.db.rowMode=='default' and -8 or -5)
    w.title:SetWidth(width-(minimal and 50 or 18)-(show and (tagWidth+10) or 0))
end
function A.Layout()
    local f=A.frame;if not f then return end
    if A.db.collapsed then return end
    local width=f:GetWidth()
    local content=width-32
    f.content:SetWidth(content)
    f.sub:SetWidth(width-32)
    f.title:SetWidth(width-135)
    if f.empty then f.empty:SetWidth(content-16) end
    for _,w in ipairs(f.widgets) do
        w:SetWidth(content)
        A.LayoutActions(w,content)
        if w.title then rowLabel(w,content);w.detail:SetWidth(content-18) end
        if w.label then w.label:SetWidth(content-48) end
    end
    if f.scroll then A.UpdateScroll(f.scroll) end
end
local function make()
    local f=CreateFrame('Frame','OneLastThingPopup',UIParent,'BackdropTemplate');A.frame=f
    f.resumeCompactPosition=A.db.collapsed
    local size=A.db.size
    f:SetSize(size.width,size.height);f:SetPoint('CENTER');f:SetFrameStrata('LOW');A.Panel(f)
    f:SetMovable(true);f:SetClampedToScreen(true);f:EnableMouse(true);f:RegisterForDrag('LeftButton')
    f:SetResizable(true);f:SetResizeBounds(360,230,950,850);f:SetScale(A.db.scale)
    if A.db.position then local p=A.db.position;f:ClearAllPoints();f:SetPoint(p.point,UIParent,p.relativePoint,p.x,p.y) end
    f:SetScript('OnDragStart',function(self) if not A.db.locked and not InCombatLockdown() then self:StartMoving() end end)
    f:SetScript('OnDragStop',function(self) if A.db.locked then return end;self:StopMovingOrSizing();savePosition(self) end)
    f.title=f:CreateFontString(nil,'OVERLAY','GameFontNormalLarge');f.title:SetPoint('TOPLEFT',14,-11);f.title:SetJustifyH('LEFT');A.Font(f.title,15,false,'brand')
    f.header=CreateFrame('Button',nil,f);f.header:RegisterForClicks('LeftButtonUp');f.header:RegisterForDrag('LeftButton')
    f.header:SetScript('OnClick',function(self)
        if self.wasDragged then self.wasDragged=false;return end
        A.SetCollapsed(not A.db.collapsed,'manual')
    end)
    f.header:SetScript('OnDragStart',function(self)
        if A.db.locked or InCombatLockdown() then return end
        self.wasDragged=true;f:StartMoving()
    end)
    f.header:SetScript('OnDragStop',function(self)
        if A.db.locked then self.wasDragged=false;return end
        f:StopMovingOrSizing();savePosition(f)
        C_Timer.After(0,function() self.wasDragged=false end)
    end)
    f.header:SetScript('OnEnter',function()
        f.headerHovered=true;f.idleBadge=false;f.fadeElapsed=nil;f.header:SetScript('OnUpdate',nil);f.idleWaiting=false;f.idleSerial=(f.idleSerial or 0)+1
        A.ApplyCollapsed()
    end)
    f.header:SetScript('OnLeave',function() f.headerHovered=false;A.StartCompletionIdle() end)
    f.fadeUpdate=function(_,elapsed)
        if f.fadeElapsed then
            f.fadeElapsed=f.fadeElapsed+elapsed
            f.title:SetAlpha(math.max(0,1-f.fadeElapsed/.35))
            if f.fadeElapsed>=.35 then f.fadeElapsed=nil;f.header:SetScript('OnUpdate',nil);f.idleBadge=true;A.ApplyCollapsed() end
        end
    end
    f.sub=f:CreateFontString(nil,'OVERLAY','GameFontHighlightSmall');f.sub:SetPoint('TOPLEFT',14,-35);A.Font(f.sub,10,true);f.sub:SetJustifyH('LEFT')
    f.filterButton=button(f,'Filter',66,function() A.ShowFilters(f.filterButton) end)
    f.filterButton:SetPoint('TOPRIGHT',-37,-9);f.filterButton:SetFrameLevel(f.header:GetFrameLevel()+1)
    A.Tint(f.filterButton:GetFontString(),'action');hint(f.filterButton,'Show or hide reminder categories and subcategories.')
    f.close=button(f,'x',23,function() A.scopeRecovery=nil;f:Hide() end);f.close:SetPoint('TOPRIGHT',-9,-9);f.filterButton:SetPoint('TOPRIGHT',-37,-9)
    f.scroll=CreateFrame('ScrollFrame',nil,f);f.scroll:SetPoint('TOPLEFT',12,-53);f.scroll:SetPoint('BOTTOMRIGHT',-12,45)
    f.content=CreateFrame('Frame',nil,f.scroll);f.content:SetSize(408,1);A.AttachScrolling(f.scroll,f.content);f.widgets={}
    f:EnableMouseWheel(true);f:SetScript('OnMouseWheel',function(_,delta) local wheel=not A.db.collapsed and f.scroll:GetScript('OnMouseWheel');if wheel then wheel(f.scroll,delta) end end)
    local restore=button(f,'Show hidden reminders',145,function() A.db.dismissed={};A.db.snoozed={};A.Refresh('Restored',true) end);restore:SetPoint('BOTTOMLEFT',12,12)
    local check=button(f,'Check',44,function() A.Refresh('Manual check',true,true) end);check:SetPoint('LEFT',restore,'RIGHT',5,0)
    local settings=button(f,'Settings',57,function() A.ShowSettings() end);settings:SetPoint('LEFT',check,'RIGHT',5,0)
    f.smaller=button(f,'-',23,function() A.AdjustFontSize(-5) end);f.smaller:SetPoint('LEFT',settings,'RIGHT',5,0)
    f.larger=button(f,'+',23,function() A.AdjustFontSize(5) end);f.larger:SetPoint('LEFT',f.smaller,'RIGHT',3,0)
    hint(f.smaller,'Decrease font size');hint(f.larger,'Increase font size')
    f.grip=button(f,'/',22,function() end);f.grip:SetPoint('BOTTOMRIGHT',-6,6)
    f.grip:SetScript('OnMouseDown',function(_,which) if which=='LeftButton' and not A.db.locked and not InCombatLockdown() then f:StartSizing('BOTTOMRIGHT') end end)
    f.grip:SetScript('OnMouseUp',function() if A.db.locked then return end;f:StopMovingOrSizing();A.db.size={width=f:GetWidth(),height=f:GetHeight()};savePosition(f) end)
    hint(f.grip,'Drag to resize the window.')
    hint(check,'Refresh the checklist for your current location. Does not restore hidden reminders, purchase items or learn spells.')
    hint(restore,'Show reminders skipped this visit or hidden for 30 minutes. Ignored reminders and disabled categories stay hidden.')
    f:SetScript('OnHide',function()
        A.pendingDraw=nil;f.fadeElapsed=nil;f.header:SetScript('OnUpdate',nil)
        f.idleWaiting=false;f.idleSerial=(f.idleSerial or 0)+1
        for _,w in ipairs(f.widgets or {}) do if w.hovered then w.hovered=false;A.StyleRow(w) end end
        if A.reminderMenu then A.reminderMenu:Hide() end;if A.filterMenu then A.filterMenu:Hide() end
    end)
    f.restoreButton=restore
    f.chrome={f.sub,f.close,f.filterButton,f.scroll,restore,check,settings,f.smaller,f.larger,f.grip}
    f:SetScript('OnSizeChanged',function(self,w,h)
        if not self.applyingCollapse and not A.db.collapsed then A.db.size={width=w,height=h} end
        A.Layout()
    end)
    -- Escape closes menus/settings, not the persistent checklist or idle marker.
    return f
end
function A.ResizePopup(dw,dh)
    local f=A.frame;if not f or A.db.collapsed or InCombatLockdown() then return end
    f:SetSize(math.max(360,math.min(950,f:GetWidth()+dw)),math.max(230,math.min(850,f:GetHeight()+dh)))
    A.db.size={width=f:GetWidth(),height=f:GetHeight()};A.Layout()
end
local anchorX={LEFT=0,TOPLEFT=0,BOTTOMLEFT=0,CENTER=.5,TOP=.5,BOTTOM=.5,RIGHT=1,TOPRIGHT=1,BOTTOMRIGHT=1}
local anchorY={TOP=0,TOPLEFT=0,TOPRIGHT=0,CENTER=.5,LEFT=.5,RIGHT=.5,BOTTOM=1,BOTTOMLEFT=1,BOTTOMRIGHT=1}
local function resizeAtTopLeft(f,width,height)
    local oldWidth,oldHeight=f:GetWidth(),f:GetHeight()
    if f.resumeCompactPosition then
        local saved=A.db.compactSize
        oldWidth,oldHeight=saved and saved.width or width,saved and saved.height or height
        f.resumeCompactPosition=nil
    end
    local point,relative,relativePoint,x,y=f:GetPoint(1)
    f:SetSize(width,height)
    if point then
        f:ClearAllPoints()
        f:SetPoint(point,relative or UIParent,relativePoint or point,
            (x or 0)+(width-oldWidth)*(anchorX[point] or .5),
            (y or 0)+(height-oldHeight)*(A.db.headerPosition=='bottom' and (1-(anchorY[point] or .5)) or -(anchorY[point] or .5)))
        savePosition(f)
    end
end
function A.StartCompletionIdle()
    local f=A.frame
    if not f or not A.db.collapsed or (f.rowCount or 0)>0 or f.headerHovered or f.idleBadge or f.idleWaiting or f.fadeElapsed~=nil or (A.ChecksIncomplete and A.ChecksIncomplete()) then return end
    f.idleSerial=(f.idleSerial or 0)+1;local serial=f.idleSerial
    f.idleWaiting=true
    C_Timer.After(A.db.completionDelay or 10,function()
        if serial~=f.idleSerial then return end
        f.idleWaiting=false
        if serial==f.idleSerial and f:IsShown() and A.db.collapsed and (f.rowCount or 0)==0 and not f.headerHovered then
            f.fadeElapsed=0;f.header:SetScript('OnUpdate',f.fadeUpdate)
        end
    end)
end
function A.ApplyCollapsed()
    local f=A.frame;if not f or not f.chrome or f.applyingCollapse then return end
    f.applyingCollapse=true
    local collapsed=A.db.collapsed
    if collapsed and A.reminderMenu then A.reminderMenu:Hide() end
    if collapsed and A.filterMenu then A.filterMenu:Hide() end
    local empty=(f.rowCount or 0)==0
    local incomplete=A.ChecksIncomplete and A.ChecksIncomplete()
    if incomplete then f.idleBadge=false;f.fadeElapsed=nil;f.idleWaiting=false;f.idleSerial=(f.idleSerial or 0)+1 end
    if not collapsed or not empty then
        f.idleBadge=false;f.fadeElapsed=nil;f.idleWaiting=false;f.idleSerial=(f.idleSerial or 0)+1
    end
    if f.fadeElapsed==nil then f.header:SetScript('OnUpdate',nil) end
    f.title:ClearAllPoints();f.title:SetPoint('TOPLEFT',14,-11)
    f.title:SetAlpha(f.idleBadge and .6 or 1)
    if collapsed then
        f.title:SetWidth(0)
        A.SetText(f.title,f.idleBadge and 'OLT' or (empty and (incomplete and 'One Last Thing · Some checks unavailable' or 'One Last Thing · All done, yay!') or ('One Last Thing ('..tostring(f.rowCount or 0)..')')))
        A.Tint(f.title,incomplete and 'warning' or (empty and 'success' or 'brand'))
        for _,widget in ipairs(f.chrome) do widget:Hide() end
        local viewportWidth,viewportHeight=f.scroll:GetWidth(),f.scroll:GetHeight()
        f.scroll:ClearAllPoints();f.scroll:SetPoint('TOPLEFT',12,-53);f.scroll:SetSize(viewportWidth,viewportHeight)
        f:SetResizeBounds(24,24,950,850);f:SetResizable(false)
        local textWidth=f.title.GetStringWidth and f.title:GetStringWidth() or (f.idleBadge and 28 or (empty and 180 or 95))
        local width=f.idleBadge and math.max(30,math.ceil(textWidth+16)) or math.max(90,math.ceil(textWidth+28))
        resizeAtTopLeft(f,width,f.idleBadge and 32 or 36)
        A.db.compactSize={width=f:GetWidth(),height=f:GetHeight()}
        f.title:SetWidth(textWidth+2)
        if f.idleBadge then f.title:ClearAllPoints();f.title:SetPoint('CENTER') end
        f.header:ClearAllPoints();f.header:SetPoint('TOPLEFT',2,-2);f.header:SetPoint('BOTTOMRIGHT',-2,2)
    else
        A.SetText(f.title,'One Last Thing');A.Tint(f.title,'brand')
        f:SetResizeBounds(360,230,950,850);f:SetResizable(true)
        resizeAtTopLeft(f,A.db.size.width,A.db.size.height)
        f.scroll:ClearAllPoints();f.sub:ClearAllPoints();f.close:ClearAllPoints();f.restoreButton:ClearAllPoints();f.grip:ClearAllPoints();f.header:ClearAllPoints();f.filterButton:ClearAllPoints()
        if A.db.headerPosition=='bottom' then
            f.title:ClearAllPoints();f.title:SetPoint('BOTTOMLEFT',14,11)
            f.sub:SetPoint('TOPLEFT',14,-12)
            f.close:SetPoint('BOTTOMRIGHT',-9,9);f.filterButton:SetPoint('BOTTOMRIGHT',-37,9)
            f.restoreButton:SetPoint('BOTTOMLEFT',12,48);f.grip:SetPoint('BOTTOMRIGHT',-6,42)
            f.scroll:SetPoint('TOPLEFT',12,-31);f.scroll:SetPoint('BOTTOMRIGHT',-12,81)
            f.header:SetPoint('BOTTOMLEFT',4,4);f.header:SetPoint('TOPRIGHT',f,'BOTTOMRIGHT',-108,32)
        else
            f.sub:SetPoint('TOPLEFT',14,-35);f.close:SetPoint('TOPRIGHT',-9,-9);f.filterButton:SetPoint('TOPRIGHT',-37,-9)
            f.restoreButton:SetPoint('BOTTOMLEFT',12,12);f.grip:SetPoint('BOTTOMRIGHT',-6,6)
            f.scroll:SetPoint('TOPLEFT',12,-53);f.scroll:SetPoint('BOTTOMRIGHT',-12,45)
            f.header:SetPoint('TOPLEFT',4,-4);f.header:SetPoint('BOTTOMRIGHT',f,'TOPRIGHT',-108,-32)
        end
        for _,widget in ipairs(f.chrome) do widget:Show() end
    end
    A.Panel(f);f.applyingCollapse=false;A.Layout()
    A.StartCompletionIdle()
end
function A.SetCollapsed(value,mode)
    A.db.collapsed=value==true
    A.db.collapseMode=mode or 'manual'
    A.ApplyCollapsed()
end
local function scopeKey()
    local s=A.scope
    return s and (s.key or tostring(s.map)) or nil
end
function A.ReminderInteractionActive()
    local f=A.frame
    if not f or not f:IsShown() or A.db.collapsed then return false end
    if A.reminderMenu and A.reminderMenu:IsShown() then return true end
    for _,w in ipairs(f.widgets) do
        if w.row and w:IsShown() and w:IsMouseOver() then return true end
    end
    return false
end
local function waitForInteraction()
    if A.drawWaitQueued then return end
    A.drawWaitQueued=true
    C_Timer.After(.15,function()
        A.drawWaitQueued=nil
        local pending=A.pendingDraw
        if not pending then return end
        if not A.frame or not A.frame:IsShown() or pending.scope~=scopeKey() then A.pendingDraw=nil;return end
        if A.ReminderInteractionActive() then waitForInteraction();return end
        A.pendingDraw=nil
        -- Recollect rather than render an old snapshot after a long interaction.
        A.Refresh(pending.reason,false)
    end)
end
function A.Draw(rows,reason,force)
    local f=A.frame
    -- Refresh passes false for background updates; direct renders are deliberate.
    if force==false and f and f.displayScopeKey==scopeKey() and A.ReminderInteractionActive() then
        A.pendingDraw={reason=reason,scope=scopeKey()}
        waitForInteraction()
        return
    end
    A.pendingDraw=nil
    if A.reminderMenu then A.reminderMenu:Hide();A.reminderMenu.row=nil end
    f=f or make()
    f.displayScopeKey=scopeKey()
    local oldScroll=f.scroll:GetVerticalScroll()
    f.rowCount=#rows
    A.SetText(f.sub,(A.ChecksIncomplete and A.ChecksIncomplete() and (A.Translate('Some checks unavailable')..' · ') or '')..(A.LocationName() or A.Translate('Unknown location'))..' · '..A.Translate(#rows..' reminders'))
    -- Reminder rows are pooled; category controls live only in the Filter menu.
    f.rowPool=f.rowPool or {}
    for _,w in ipairs(f.widgets) do w:Hide() end
    f.widgets={}
    local y=0;local rowIndex=0
    if A.SortReminders and rows~=A.rows then A.SortReminders(rows) end
    for _,row in ipairs(rows) do
                    A.Category(row)
                    rowIndex=rowIndex+1
                    local w=f.rowPool[rowIndex]
                    if not w then
                        w=CreateFrame('Frame',nil,f.content,'BackdropTemplate');w:SetHeight(91);A.Panel(w)
                        w.hoverBg=w:CreateTexture(nil,'BACKGROUND');w.hoverBg:SetAllPoints();w.hoverBg:SetColorTexture(0,0,0,0)
                        w.accent=w:CreateTexture(nil,'OVERLAY');w.accent:SetPoint('TOPLEFT',0,-2);w.accent:SetPoint('BOTTOMLEFT',0,2);w.accent:SetWidth(2)
                        w.title=w:CreateFontString(nil,'OVERLAY','GameFontNormal');w.title:SetPoint('TOPLEFT',10,-8);w.title:SetHeight(16);w.title:SetJustifyH('LEFT');A.Font(w.title,12)
                        w.tag=w:CreateFontString(nil,'OVERLAY','GameFontHighlightSmall');w.tag:SetJustifyH('RIGHT');w.tag:SetHeight(16);A.Font(w.tag,10,true)
                        w.detail=w:CreateFontString(nil,'OVERLAY','GameFontHighlightSmall');w.detail:SetPoint('TOPLEFT',10,-27);w.detail:SetHeight(28);w.detail:SetJustifyH('LEFT');A.Font(w.detail,10,true)
                        w:EnableMouse(true);w:RegisterForDrag('LeftButton')
                        w:SetScript('OnDragStart',function(self)
                            local target=self or w
                            if A.db.locked or InCombatLockdown() then return end
                            target.wasDragged=true;f:StartMoving()
                        end)
                        w:SetScript('OnDragStop',function(self)
                            local target=self or w
                            if A.db.locked then target.wasDragged=false;return end
                            f:StopMovingOrSizing();savePosition(f)
                            C_Timer.After(0,function() target.wasDragged=false end)
                        end)
                        w:SetScript('OnMouseUp',function(self,which)
                            local target=self or w
                            if not target.row then return end
                            if which=='RightButton' then
                                if GameTooltip then GameTooltip:Hide() end
                                A.ShowReminderMenu(target.more or target,target.row)
                            elseif which=='LeftButton' and not target.wasDragged and A.db.rowMode=='minimal' and A.RowNavigable(target.row) then
                                A.Navigate(target.row)
                            end
                        end)
                        w:SetScript('OnEnter',function(self)
                            local target=self or w
                            target.hovered=true;A.StyleRow(target)
                            if target.row and GameTooltip then
                                GameTooltip:SetOwner(target,'ANCHOR_RIGHT')
                                A.SetText(GameTooltip,A.DisplayTitle(target.row))
                                GameTooltip:AddLine(A.Translate(target.row.categoryName or '')..' · '..A.Translate(target.row.subcategoryName or ''),1,1,1,true)
                                GameTooltip:AddLine(A.DistanceText(target.row),1,1,1,true)
                                GameTooltip:AddLine(A.Translate(A.DisplayDetail(target.row,true)),1,1,1,true)
                                GameTooltip:Show()
                            end
                        end)
                        w:SetScript('OnLeave',function(self)
                            local target=self or w
                            target.hovered=false;A.StyleRow(target)
                            if GameTooltip then GameTooltip:Hide() end
                        end)
                        w.go=button(w,'Map',44,function() A.Navigate(w.row) end);w.go:SetPoint('BOTTOMLEFT',8,7)
                        w.dismiss=button(w,'Skip this visit',108,function() A.Dismiss(w.row) end);w.dismiss:SetPoint('LEFT',w.go,'RIGHT',4,0)
                        w.snooze=button(w,'Hide for 30m',98,function() A.Snooze(w.row) end);w.snooze:SetPoint('LEFT',w.dismiss,'RIGHT',4,0)
                        w.more=button(w,'...',26,function() A.ShowReminderMenu(w.more,w.row) end)
                        hint(w.go,'Map');hint(w.dismiss,'Returns on your next visit to this locality, or after reloading. Show hidden reminders brings it back sooner.')
                        hint(w.snooze,'Hidden for 30 minutes, even if you change zones. Show hidden reminders brings it back sooner.')
                        hint(w.more,'More options, including Don’t remind again.')
                        f.rowPool[rowIndex]=w
                    end
                    A.SetText(w.dismiss,'Skip this visit');A.SetText(w.snooze,'Hide for 30m')
                    w.row=row;w.hovered=false;w.wasDragged=false;w:ClearAllPoints();w:SetPoint('TOPLEFT',0,-y)
                    local compact=A.db.rowMode~='default'
                    local minimal=A.db.rowMode=='minimal'
                    w:SetHeight(minimal and 27 or (compact and 51 or 91));y=y+(minimal and 31 or (compact and 55 or 97))
                    w.title:ClearAllPoints();w.title:SetPoint('TOPLEFT',compact and 9 or 10,compact and -5 or -8)
                    w.title:SetHeight(16)
                    w.tag:ClearAllPoints();w.tag:SetPoint('TOPRIGHT',-9,compact and -5 or -8)
                    w.categoryLabel=A.shortCategoryNames[row.category] or row.categoryName or '';A.Tint(w.tag,row.category)
                    w.detail:SetShown(not compact)
                    A.SetText(w.title,A.DisplayTitle(row));A.SetText(w.detail,A.DisplayDetail(row))
                    A.Tint(w.title,A.RowTone(row));A.Tint(w.go:GetFontString(),'action')
                    A.Tint(w.dismiss:GetFontString(),'dismiss');A.Tint(w.snooze:GetFontString(),'snooze');A.Tint(w.more:GetFontString(),'muted')
                    A.StyleRow(w)
                    w.go:SetShown(not minimal and A.RowNavigable(row))
                    w.dismiss:SetShown(not minimal);w.snooze:SetShown(not minimal);w.more:Show()
                    local left=8
                    for _,control in ipairs({w.go,w.dismiss,w.snooze,w.more}) do
                        if control:IsShown() then control:ClearAllPoints();control:SetPoint('BOTTOMLEFT',w,'BOTTOMLEFT',left,compact and 4 or 7);left=left+control:GetWidth()+4 end
                    end
                    A.LayoutActions(w,f:GetWidth()-32)
                    w:Show();f.widgets[#f.widgets+1]=w
    end
    if not f.empty then f.empty=f.content:CreateFontString(nil,'OVERLAY','GameFontHighlight');f.empty:SetPoint('TOPLEFT',8,-12);f.empty:SetJustifyH('LEFT');A.Font(f.empty,12,true) end
    local incomplete=A.ChecksIncomplete and A.ChecksIncomplete()
    A.SetText(f.empty,incomplete and (A.Translate('Some checks unavailable')..'\n\n'..A.CheckHealthText()) or 'No enabled reminders for this zone.\n\nUse Filter to re-enable a group.')
    f.empty:SetShown(#rows==0);f.content:SetHeight(math.max(#rows==0 and 120 or 1,y));A.Layout()
    f.scroll:SetVerticalScroll(reason=='Updated' and (oldScroll or 0) or 0);A.UpdateScroll(f.scroll)
    local map=A.Map()
    local filterOpen=A.filterMenu and A.filterMenu:IsShown()
    local newlyEmpty=#rows==0 and (f.previousCount==nil or f.previousCount>0 or f.previousMap~=map)
    if newlyEmpty and not filterOpen then
        if not (A.db.collapsed and A.db.collapseMode=='manual') then
            A.db.collapsed=true;A.db.collapseMode='auto'
        end
    elseif #rows>0 and A.db.collapseMode=='auto' then
        A.db.collapsed=false;A.db.collapseMode=nil
    end
    f.previousCount,f.previousMap=#rows,map
    A.UpdateFilterButton();A.ApplyCollapsed();f:Show();if filterOpen then A.UpdateFilters() end
end
