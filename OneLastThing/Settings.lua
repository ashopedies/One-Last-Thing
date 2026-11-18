local _, A = ...
local building
-- SetScript(nil) still validates the script against the native widget type.
local resetScripts={
    Button={'OnClick'},CheckButton={'OnClick'},Slider={'OnValueChanged'},
    EditBox={'OnTextChanged','OnEnterPressed','OnEditFocusLost','OnEscapePressed'},
}
local function acquire(kind,name,parent,template)
    if not building then return CreateFrame(kind,name,parent,template) end
    local key=kind..':'..(template or '')
    local pool=building.pool[key] or {};building.pool[key]=pool
    local index=(building.poolUsed[key] or 0)+1;building.poolUsed[key]=index
    local frame=pool[index]
    if not frame then frame=CreateFrame(kind,name,parent,template);pool[index]=frame
    else
        frame:Hide();frame:ClearAllPoints();frame:SetParent(parent)
        for _,script in ipairs(resetScripts[kind] or {}) do frame:SetScript(script,nil) end
    end
    frame:Show();return frame
end
local function font(parent,template)
    if not building then return parent:CreateFontString(nil,'OVERLAY',template) end
    local index=(building.fontUsed or 0)+1;building.fontUsed=index
    local fs=building.fontPool[index]
    if not fs then fs=parent:CreateFontString(nil,'OVERLAY',template);building.fontPool[index]=fs
    else fs:ClearAllPoints();fs:SetParent(parent);fs:SetWidth(0);fs:SetHeight(0) end
    fs:Show();return fs
end
local function label(parent,value,x,y,size)
    local fs=font(parent,'GameFontHighlight');fs:SetPoint('TOPLEFT',x,y)
    A.SetText(fs,value);A.Font(fs,size or 12,false,(size or 12)>=13 and 'brand' or nil);return fs
end
local function button(parent,title,x,y,w,fn)
    local b=acquire('Button',nil,parent,'BackdropTemplate');b:SetSize(w,24);b:SetPoint('TOPLEFT',x,y)
    local fs=b:GetFontString() or b:CreateFontString(nil,'OVERLAY','GameFontHighlightSmall');fs:SetPoint('CENTER');b:SetFontString(fs)
    A.SetText(b,title);A.StyleButton(b);b:SetScript('OnClick',fn);return b
end
function A.AddonRequirements()
    local definitions={
        {'Attune','Attune','Needed for quest-chain and class-quest reminders.'},
        {'Questie','Questie','Needed for full quest eligibility and zone conversion.'},
        {'QuestieDB','QuestieDB','Needed for full NPC, vendor and quest location data.'},
        {'SkillUpForever','SkillUp Forever','Used for profession ranks/books; optional for One Last Thing.'},
        {'TrainerSpells','TrainerSpells','Class spells, weapon skills and profession trainer locations.'},
        {'NeavMedia','NeavMedia','Optional: Neav fonts. Game fonts work without it.'},
    }
    local rows={}
    local loadedFn=(C_AddOns and C_AddOns.IsAddOnLoaded) or IsAddOnLoaded
    for _,d in ipairs(definitions) do
        local loaded=A.Safe('addon loaded '..d[1],loadedFn,d[1])==true
        rows[#rows+1]={id=d[1],name=d[2],loaded=loaded,status=loaded and 'Loaded' or 'Not loaded',detail=d[3]}
    end
    local shared=A.SharedMedia and A.SharedMedia()~=nil
    rows[#rows+1]={id='LibSharedMedia-3.0',name='LibSharedMedia',loaded=shared,status=shared and 'Available' or 'Unavailable',
        detail='Optional font library, often bundled by another addon.'}
    return rows
end
function A.LayoutSettingsSections()
    local f=A.settings;if not f or not f.sections then return end
    local offset=0
    for _,section in ipairs(f.sections) do
        local open=A.db.settingsSections[section.id]
        if open==nil then open=section.defaultOpen end
        section.open=open
        A.SetText(section.header,(open and '- ' or '+ ')..section.title)
        section.body:SetShown(open)
        local height=34+(open and section.height or 0)
        section.container:ClearAllPoints();section.container:SetPoint('TOPLEFT',0,-offset);section.container:SetSize(410,height)
        offset=offset+height+8
    end
    f.content:SetHeight(offset+4);A.UpdateScroll(f.scroll)
end
function A.ShowSettings()
    if InCombatLockdown() then A.Print('Open settings after combat.');return end
    if A.settings then A.settings:Show();A.BuildSettings();return end
    local f=acquire('Frame','OneLastThingSettings',UIParent,'BackdropTemplate');A.settings=f
    f:SetSize(460,520);f:SetPoint('CENTER',UIParent,'CENTER',50,0);f:SetFrameStrata('MEDIUM');f.pitSettingsBackground=true;A.Panel(f)
    f:SetMovable(true);f:SetClampedToScreen(true);f:EnableMouse(true);f:RegisterForDrag('LeftButton')
    f:SetScript('OnDragStart',function(self) if self.menu then self.menu:Hide() end;self:StartMoving() end);f:SetScript('OnDragStop',f.StopMovingOrSizing)
    f:SetScript('OnHide',function(self) if self.menu then self.menu:Hide() end end)
    label(f,'One Last Thing settings',16,-15,16)
    button(f,'x',425,-9,23,function() f:Hide();if f.menu then f.menu:Hide() end end)
    f.scroll=acquire('ScrollFrame',nil,f);f.scroll:SetPoint('TOPLEFT',10,-48);f.scroll:SetPoint('BOTTOMRIGHT',-10,18)
    f.content=acquire('Frame',nil,f.scroll);f.content:SetSize(410,1);A.AttachScrolling(f.scroll,f.content)
    local scrollWheel=f.scroll:GetScript('OnMouseWheel')
    f.scroll:SetScript('OnMouseWheel',function(self,delta) if f.menu then f.menu:Hide() end;scrollWheel(self,delta) end)
    f:EnableMouseWheel(true);f:SetScript('OnMouseWheel',function(_,delta) if f.menu then f.menu:Hide() end;f.scroll:GetScript('OnMouseWheel')(f.scroll,delta) end)
    f.controls={};f.pool={};f.boxes={}
    table.insert(UISpecialFrames,'OneLastThingSettings');A.BuildSettings();f:Show()
end
local function buildSettings()
    local f=A.settings;if not f or f.rebuilding then return end
    local keys={}
    for _,cat in ipairs(A.categories) do
        keys[#keys+1]=cat.id
        for sub in pairs(cat.subs) do keys[#keys+1]=cat.id..'/'..sub end
    end
    for id,rule in pairs(A.db.supplies) do keys[#keys+1]='supply:'..id..':'..rule.target end
    local requirements=A.AddonRequirements()
    for _,r in ipairs(requirements) do keys[#keys+1]='addon:'..r.id..':'..tostring(r.loaded) end
    if A.IsHunter() then
        local ammo=A.HunterAmmoSelection()
        keys[#keys+1]='ammo:'..tostring(ammo)..':'..A.HunterAmmoTarget()
    end
    keys[#keys+1]='economy:'..tostring(A.db.reagentEconomy)
    table.sort(keys);local signature=table.concat(keys,'|')
    if f.signature==signature then
        for _,b in ipairs(f.boxes) do b:SetChecked(b.read()) end
        for id,status in pairs(f.supplyStatuses or {}) do A.SetText(status,A.SupplySettingsText(id,A.db.supplies[id] and A.db.supplies[id].target or 0)) end
        if f.hunterAmmoStatus then local id=A.HunterAmmoSelection();A.SetText(f.hunterAmmoStatus,A.HunterAmmoStatus()..(id and (' · '..A.SupplyEstimateText(id,A.HunterAmmoTarget())) or '')) end
        f.opacity:SetValue(A.db.opacity*100);f.fontSize:SetValue(A.db.fontScale*100);f.scale:SetValue(A.db.scale*100);f.bags:SetValue(A.db.bagSlots)
        A.LayoutSettingsSections();return
    end
    f.signature=signature;f.rebuilding=true
    if f.menu then f.menu:Hide() end
    f.pool=f.pool or {};f.poolUsed={};f.fontPool=f.fontPool or {};f.fontUsed=0
    for _,pool in pairs(f.pool) do for _,c in ipairs(pool) do c:Hide() end end
    for _,fs in ipairs(f.fontPool) do fs:Hide() end
    building=f
    for _,c in ipairs(f.controls) do c:Hide() end
    f.controls={};f.boxes={};f.sections={};f.sectionButtons={};f.sectionByID={}
    local parent=f.content
    local y=0
    local function own(w) f.controls[#f.controls+1]=w;return w end
    local currentSection
    local function finishSection()
        if currentSection then currentSection.height=y;currentSection.body:SetHeight(math.max(1,y)) end
    end
    local function section(id,title,defaultOpen)
        finishSection()
        local container=own(acquire('Frame',nil,f.content));container:SetWidth(410)
        local body=acquire('Frame',nil,container);body:SetPoint('TOPLEFT',0,-34);body:SetSize(410,1)
        local header=button(container,title,0,0,400,function()
            local entry=f.sectionByID[id]
            A.db.settingsSections[id]=not entry.open
            if f.menu then f.menu:Hide() end
            A.LayoutSettingsSections()
        end)
        A.Font(header:GetFontString(),13,false,'brand')
        currentSection={id=id,title=title,defaultOpen=defaultOpen==true,container=container,body=body,header=header,height=0}
        f.sections[#f.sections+1]=currentSection;f.sectionByID[id]=currentSection;f.sectionButtons[id]=header
        parent=body;y=0
    end
    local function text(value,size)
        local fs=own(label(parent,value,8,-y,size));fs:SetWidth(390);fs:SetJustifyH('LEFT')
        y=y+math.max(26,(fs.GetStringHeight and fs:GetStringHeight() or 18)+8)
    end
    local function control(title,read,write,indent)
        local b=own(acquire('CheckButton',nil,parent,'UICheckButtonTemplate'));b:SetSize(24,24);b:SetPoint('TOPLEFT',indent and 24 or 4,-y)
        b.label=b.label or b:CreateFontString(nil,'OVERLAY','GameFontHighlight');b.label:ClearAllPoints();b.label:SetHeight(0);if b.label.SetMaxLines then b.label:SetMaxLines(0) end;b.label:SetPoint('LEFT',b,'RIGHT',3,0);A.SetText(b.label,title);A.Font(b.label,11)
        b.label:SetWidth(indent and 340 or 360);b.label:SetJustifyH('LEFT')
        b:SetChecked(read());b:SetScript('OnClick',function() write(not read());b:SetChecked(read()) end)
        b.read=read;f.boxes[#f.boxes+1]=b;y=y+math.max(26,(b.label.GetStringHeight and b.label:GetStringHeight() or 18)+8);return b
    end
    local function toggle(title,key)
        return control(title,function() return A.db[key]~=false end,function(v) A.db[key]=v;if A.InvalidateProviders then A.InvalidateProviders() end;A.Refresh('Updated',false) end)
    end
    local function slider(title,min,max,step,value,change,format)
        local titleFS=own(label(parent,title,8,-y,12));y=y+25
        local s=own(acquire('Slider',nil,parent));s:SetOrientation('HORIZONTAL');s:SetSize(365,18);s:SetPoint('TOPLEFT',15,-y)
        local track=s.track or s:CreateTexture(nil,'BACKGROUND');s.track=track;track:SetAllPoints();track:SetColorTexture(.25,.25,.28,.8)
        s:SetThumbTexture('Interface/Buttons/UI-SliderBar-Button-Horizontal');s:SetMinMaxValues(min,max);s:SetValueStep(step);s:SetObeyStepOnDrag(true)
        local function update(v) A.SetText(titleFS,title..': '..format(v)) end
        s:SetValue(value);update(value)
        s:SetScript('OnValueChanged',function(_,v) change(v);update(v) end);y=y+34
        return s
    end
    local function dropdown(title,key,choices)
        own(label(parent,title,8,-y-6,12))
        local selected
        local function options() return type(choices)=='function' and choices() or choices end
        for _,c in ipairs(options()) do if c[1]==A.db[key] then selected=c[2] end end
        if not selected and key=='fontFace' then selected=(A.db.fontFace or ''):gsub('^lsm:','')..' (unavailable)' end
        local b
        b=own(button(parent,(selected or '')..'  v',180,-y,210,function()
            if f.menu and f.menu:IsShown() and f.menu.anchor==b then f.menu:Hide();return end
            if f.menu then f.menu:Hide() end
            local current=options()
            local menu=f.menu or CreateFrame('Frame','OneLastThingSettingsDropdown',f,'BackdropTemplate');f.menu=menu;menu.items=menu.items or {};menu.anchor=b
            menu:ClearAllPoints()
            menu:SetSize(212,math.min(#current,8)*26+10);menu:SetPoint('TOPLEFT',b,'BOTTOMLEFT',0,-2);menu:SetFrameStrata('TOOLTIP');menu:SetClampedToScreen(true);menu.pitSettingsBackground=true;A.Panel(menu)
            if not menu.scroll then
                menu:Hide() -- newly created native Frames may already be shown
                menu:EnableMouse(true)
                menu:SetScript('OnEvent',function(self,event)
                    if event~='GLOBAL_MOUSE_DOWN' or not self:IsShown() then return end
                    if not self:IsMouseOver() and not (self.anchor and self.anchor:IsMouseOver()) then self:Hide() end
                end)
                menu:SetScript('OnShow',function(self) self:RegisterEvent('GLOBAL_MOUSE_DOWN') end)
                menu:SetScript('OnHide',function(self) self:UnregisterEvent('GLOBAL_MOUSE_DOWN');self.anchor=nil end)
                table.insert(UISpecialFrames,'OneLastThingSettingsDropdown')
                menu.scroll=acquire('ScrollFrame',nil,menu);menu.scroll:SetPoint('TOPLEFT',5,-5);menu.scroll:SetPoint('BOTTOMRIGHT',-5,5)
                menu.content=acquire('Frame',nil,menu.scroll);menu.content:SetSize(202,1);A.AttachScrolling(menu.scroll,menu.content)
                menu:EnableMouseWheel(true);menu:SetScript('OnMouseWheel',function(_,delta) menu.scroll:GetScript('OnMouseWheel')(menu.scroll,delta) end)
            end
            menu.content:SetHeight(#current*26)
            for _,item in ipairs(menu.items) do item:Hide() end
            for i,c in ipairs(current) do
                local choice=c
                local item=menu.items[i] or button(menu.content,choice[2],0,-(i-1)*26,202,function() end);menu.items[i]=item
                item:Show();A.SetText(item,choice[2]);item:SetScript('OnClick',function() A.db[key]=choice[1];A.SetText(b,choice[2]..'  v');if key=='theme' then A.ApplyTheme() elseif key=='headerPosition' then A.ApplyCollapsed() elseif key=='rowMode' then A.Refresh('Updated',false) elseif key=='petFoodID' then A.SelectVendorPetFood(choice[1]);f.signature=nil;A.BuildSettings() else A.ApplyFonts() end;menu:Hide() end)
            end
            menu.anchor=b;menu:Show();menu.scroll:SetVerticalScroll(0);A.UpdateScroll(menu.scroll)
        end))
        y=y+34;return b
    end
    local function supplies()
        f.supplyInputs={};f.supplyChecks={};f.supplyDeletes={};f.supplyStatuses={}
        control('I have Reagent Economy (hide class reagent checks)',function() return A.db.reagentEconomy==true end,
            function(v) A.db.reagentEconomy=v;f.signature=nil;A.BuildSettings();A.Refresh('Updated',false) end,true)
        local seen={}
        local function supplyRow(id,default,custom)
            local itemID=id
            local checked=function() return A.db.supplies[id]~=nil and A.CategoryEnabled('supplies',tostring(id)) end
            local rowY=y
            local c=control(A.SupplyName(id),checked,function(v)
                A.EnableSupply(id,v)
                A.SetText(f.supplyStatuses[id],A.SupplySettingsText(id,A.db.supplies[id] and A.db.supplies[id].target or 0))
            end,true)
            c.label:SetWidth(160);c.label:SetHeight(16)
            if c.label.SetMaxLines then c.label:SetMaxLines(1) end
            local target=own(acquire('EditBox',nil,parent,'InputBoxTemplate'))
            target:SetSize(48,24);target:SetPoint('TOPLEFT',258,-rowY);target:SetAutoFocus(false);target:SetNumeric(true)
            A.SetText(target,tostring(A.db.supplies[id] and A.db.supplies[id].target or default))
            own(label(parent,'Target',215,-rowY-6,10))
            local function save()
                if f.rebuilding then return end
                local n=tonumber(target:GetText())
                if not n or n<1 or n>10000 then A.SetText(target,tostring(A.db.supplies[id] and A.db.supplies[id].target or default));return end
                n=math.floor(n)
                if not A.db.supplies[id] or A.db.supplies[id].target~=n then
                    A.SetSupplyTarget(id,n);c:SetChecked(checked())
                end
                A.SetText(target,tostring(n));A.SetText(f.supplyStatuses[id],A.SupplySettingsText(id,A.db.supplies[id] and A.db.supplies[id].target or 0))
            end
            target:SetScript('OnEnterPressed',function() save();target:ClearFocus() end)
            target:SetScript('OnEditFocusLost',save)
            target:SetScript('OnTextChanged',function()
                if f.rebuilding then return end
                local n=tonumber(target:GetText())
                if n and n>=1 and n<=10000 and f.supplyStatuses[id] then A.SetText(f.supplyStatuses[id],A.SupplySettingsText(id,math.floor(n),true)) end
            end)
            target:SetScript('OnEscapePressed',function() A.SetText(target,tostring(A.db.supplies[id] and A.db.supplies[id].target or default));target:ClearFocus() end)
            if custom then
                f.supplyDeletes[id]=own(button(parent,'Delete',318,-rowY,65,function()
                    A.DeleteSupply(itemID);f.signature=nil;A.BuildSettings()
                end))
            end
            local status=own(label(parent,A.SupplySettingsText(id,A.db.supplies[id] and A.db.supplies[id].target or 0),50,-y,10));status:SetWidth(340);y=y+23
            f.supplyInputs[id]=target;f.supplyChecks[id]=c;f.supplyStatuses[id]=status
        end
        f.hunterAmmoStatus=nil;f.hunterAmmoTarget=nil;f.hunterAmmoCheck=nil
        if A.IsHunter() then
            text('Hunter ammunition',12)
            local rowY=y
            local c=control('Follow my equipped ammo',function() return A.HunterAmmoEnabled() end,function(v)
                A.EnableHunterAmmo(v);A.BuildSettings()
            end,true)
            c.label:SetWidth(175);f.hunterAmmoCheck=c
            local target=own(acquire('EditBox',nil,parent,'InputBoxTemplate'))
            target:SetSize(64,24);target:SetPoint('TOPLEFT',304,-rowY);target:SetAutoFocus(false);target:SetNumeric(true)
            A.SetText(target,tostring(A.HunterAmmoTarget()));own(label(parent,'Target',220,-rowY-6,10))
            local function save()
                if f.rebuilding then return end
                local n=tonumber(target:GetText())
                if n and n>=1 and n<=100000 then
                    if math.floor(n)~=A.HunterAmmoTarget() then A.SetHunterAmmoTarget(n);c:SetChecked(A.HunterAmmoEnabled()) end
                end
                A.SetText(target,tostring(A.HunterAmmoTarget()))
                if f.hunterAmmoStatus then local id=A.HunterAmmoSelection();A.SetText(f.hunterAmmoStatus,A.HunterAmmoStatus()..(id and (' · '..A.SupplyEstimateText(id,A.HunterAmmoTarget())) or '')) end
            end
            target:SetScript('OnEnterPressed',function() save();target:ClearFocus() end);target:SetScript('OnEditFocusLost',save)
            target:SetScript('OnEscapePressed',function() A.SetText(target,tostring(A.HunterAmmoTarget()));target:ClearFocus() end)
            target:SetScript('OnTextChanged',function()
                if f.rebuilding then return end
                local n=tonumber(target:GetText());local id=A.HunterAmmoSelection()
                if n and n>=1 and n<=100000 and id and f.hunterAmmoStatus then
                    A.SetText(f.hunterAmmoStatus,A.HunterAmmoStatus()..' · '..A.SupplyEstimateText(id,math.floor(n)))
                end
            end)
            f.hunterAmmoTarget=target
            f.hunterAmmoStatus=own(label(parent,A.HunterAmmoStatus()..(A.HunterAmmoSelection() and (' · '..A.SupplyEstimateText(A.HunterAmmoSelection(),A.HunterAmmoTarget())) or ''),32,-y,10));f.hunterAmmoStatus:SetWidth(360);y=y+26
            text('Equip the ammo you want to restock.',10)
            text('No ammo upgrade suggestions; you choose the tier.',10)
        end
        text('Class supplies',12)
        for _,p in ipairs(A.ClassSupplyList()) do seen[p[1]]=true;supplyRow(p[1],p[3],false) end
        text('Custom supplies',12)
        local ids={};for id in pairs(A.db.supplies) do if not seen[id] then ids[#ids+1]=id end end
        table.sort(ids,function(a,b) return A.SupplyName(a)<A.SupplyName(b) end)
        for _,id in ipairs(ids) do supplyRow(id,A.db.supplies[id].target,true) end
        text('Targets save on Enter or when leaving the field.',10)
        text('Add item ID                           Target',11)
        local item=own(acquire('EditBox',nil,parent,'InputBoxTemplate'));item:SetSize(170,24);item:SetPoint('TOPLEFT',24,-y);item:SetAutoFocus(false);item:SetNumeric(true)
        local count=own(acquire('EditBox',nil,parent,'InputBoxTemplate'));count:SetSize(70,24);count:SetPoint('TOPLEFT',220,-y);count:SetAutoFocus(false);count:SetNumeric(true);A.SetText(count,'3')
        own(button(parent,'Add',310,-y,73,function()
            local id,n=tonumber(item:GetText()),tonumber(count:GetText())
            if not id or id<1 or not n or n<1 or n>10000 then A.Print('Enter an item ID and target from 1 to 10000.');return end
            A.SetSupplyTarget(id,n);item:ClearFocus();count:ClearFocus();f.signature=nil;A.BuildSettings()
        end));y=y+36
        f.supplyItem=item;f.supplyCount=count
    end
    section('general','General & location',true)
    text('Automatic popups',14)
    toggle('Enable automatic popups','auto');toggle('Open when entering a new zone','arrival')
    toggle('Show an empty popup when nothing is pending','showEmpty');toggle('Travel, merchant and bank checks','travel')
    y=y+10;text('Local reminders',14)
    toggle('Use distance filtering outside capital cities','nearbyOnly')
    text('The six capital cities use city-wide reminders.',11)
    f.range=slider('Outside-city range (yards)',250,2000,50,A.db.nearbyRadius,function(v) A.db.nearbyRadius=v;A.Refresh('Updated',false) end,function(v) return tostring(math.floor(v+.5)) end)
    section('appearance','Appearance',false)
    f.layoutPicker=dropdown('Reminder layout','rowMode',{{'default','Default'},{'compact','Compact'},{'minimal','Minimal'}})
    dropdown('Header position','headerPosition',{{'top','Top'},{'bottom','Bottom'}})
    f.fadeDelay=slider('Completion fade delay',5,60,1,A.db.completionDelay,function(v) A.db.completionDelay=math.floor(v+.5) end,function(v) return math.floor(v+.5)..'s' end)
    dropdown('Color theme','theme',{{'blizzard','Blizzard'},{'class','Class Colors'},{'pop','Pop'},{'original','Original'}})
    f.opacity=slider('Background opacity',0,100,1,A.db.opacity*100,function(v) A.db.opacity=v/100;A.ApplyOpacity() end,function(v) return math.floor(v+.5)..'%' end)
    f.fontPicker=dropdown('Font','fontFace',A.FontChoices)
    f.fontSize=slider('Font size',80,130,5,A.db.fontScale*100,function(v) A.db.fontScale=v/100;A.ApplyFonts() end,function(v) return math.floor(v+.5)..'%' end)
    dropdown('Text shadow','fontShadow',{{'none','None'},{'soft','Soft'},{'strong','Strong'}})
    dropdown('Text outline','fontOutline',{{'none','None'},{'thin','Thin'},{'thick','Thick'}})
    f.scale=slider('Popup scale',65,150,5,A.db.scale*100,function(v) A.db.scale=v/100;if A.frame then A.frame:SetScale(A.db.scale) end end,function(v) return math.floor(v+.5)..'%' end)
    own(button(parent,'Reset popup size & position',8,-y,365,function()
        A.db.position=nil;A.db.size={width=440,height=320};A.db.scale=1;A.db.collapsed=false;A.db.collapseMode='manual'
        if A.frame then A.frame:ClearAllPoints();A.frame:SetPoint('CENTER');A.frame:SetScale(1);A.frame:SetSize(440,320);A.ApplyCollapsed() end
        A.BuildSettings()
    end));y=y+40
    for _,cat in ipairs(A.categories) do
        section('category:'..cat.id,cat.name,false)
        if cat.id=='quests' then
            toggle('Scan all unfinished Attune quest chains','attuneAllChains')
            text('Class, dungeon, raid/access and miscellaneous chains',11)
        end
        local categoryBox=control(cat.name,function() return A.CategoryEnabled(cat.id) end,function(v) A.SetCategory(cat.id,nil,v) end)
        A.Tint(categoryBox.label,cat.id)
        local keys={};for sub in pairs(cat.subs) do keys[#keys+1]=sub end
        table.sort(keys,function(a,b) return cat.subs[a]<cat.subs[b] end)
        for _,sub in ipairs(cat.id~='supplies' and keys or {}) do
            -- Child checkbox stores its own choice, independent of the parent.
            local childBox=control(cat.subs[sub],function() return A.db.filters[cat.id..'/'..sub]~=false end,
                function(v) A.SetCategory(cat.id,sub,v) end,true)
            A.Font(childBox.label,11,true,cat.id)
        end
        if cat.id=='supplies' then
            if A.IsHunter() then
                A.db.petFoodID=A.VendorPetFoodSelection() or 0
                dropdown('Vendor pet food','petFoodID',A.VendorPetFoodChoices)
                text('Choose food your current pet can eat; vendor items only.',10)
            end
            supplies()
        end
        if cat.id=='professions' then
            y=y+8;toggle('Important profession rank books (maximum 2)','importantVendorBuys')
        end
        if cat.id=='errands' then
            y=y+8
            f.repairs=slider('Repair below durability',10,90,5,A.db.repairThreshold,function(v) A.db.repairThreshold=math.floor(v+.5);A.Refresh('Updated',false) end,function(v) return math.floor(v+.5)..'%' end)
            f.bags=slider('Warn below free bag slots',0,20,1,A.db.bagSlots,function(v) A.db.bagSlots=math.floor(v+.5);A.Refresh('Updated',false) end,function(v) return tostring(math.floor(v+.5)) end)
        end
        y=y+8
    end
    section('recovery','Hidden reminders & help',false)
    text('Show hidden: skipped this visit or hidden for 30m.',11)
    text('Ignored reminders are managed separately below.',11)
    own(button(parent,'Show hidden reminders',8,-y,365,function()
        A.db.dismissed={};A.db.snoozed={};A.Refresh('Restored',false);A.Print('Skipped and timed-hidden reminders are visible again. Ignored reminders and category choices stay unchanged.')
    end));y=y+34
    own(button(parent,'Ignored reminders',8,-y,365,function() A.ShowTrashBin() end));y=y+38
    text('/olt status — connection diagnostics',11)
    section('addons','Addon requirements',true)
    text('One Last Thing works without mandatory addon dependencies.',11)
    text('These integrations enable the features listed below.',11)
    text('Missing data providers are reported in the checklist.',11)
    f.dependencyRows={}
    for _,r in ipairs(requirements) do
        local name=own(label(parent,r.name,8,-y,12));name:SetWidth(235)
        local state=own(label(parent,r.status,264,-y,11));state:SetWidth(130);state:SetJustifyH('RIGHT')
        A.Tint(state,r.loaded and 'success' or 'warning')
        local detail=own(label(parent,r.detail,8,-y-19,10));detail:SetWidth(390);detail:SetHeight(28);detail:SetJustifyH('LEFT')
        f.dependencyRows[r.id]={name=name,state=state,detail=detail,loaded=r.loaded}
        y=y+53
    end
    text('/olt status — data and compatibility diagnostics',11)
    finishSection();building=nil;A.LayoutSettingsSections();f.rebuilding=false
end
function A.BuildSettings()
    if A.settings and A.settings.rebuilding then return end
    local ok,err=pcall(buildSettings)
    building=nil
    if A.settings then
        A.settings.rebuilding=false
        if not ok then A.settings.signature=nil end
    end
    if not ok then error(err,0) end
end
function A.UpdateSettings() if A.settings then A.BuildSettings() end end
