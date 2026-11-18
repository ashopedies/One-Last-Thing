local _,A=...
local function text(parent,value,size)
    local fs=parent:CreateFontString(nil,'OVERLAY','GameFontHighlight')
    A.SetText(fs,value);A.Font(fs,size or 11);return fs
end
function A.FiltersActive()
    for _,enabled in pairs(A.db.filters) do if enabled==false then return true end end
    return false
end
function A.UpdateFilterButton()
    if A.frame and A.frame.filterButton then A.SetText(A.frame.filterButton,A.FiltersActive() and 'Filter •' or 'Filter') end
end
function A.CloseFilters()
    local m=A.filterMenu;if not m or not m:IsShown() then return end
    m:Hide()
    local f=A.frame
    if f and f:IsShown() and not A.db.collapsed and (f.rowCount or 0)==0 then A.SetCollapsed(true,'auto') end
end
function A.UpdateFilters()
    local m=A.filterMenu;if not m or not m:IsShown() then return end
    A.SetText(m.title,'Show categories')
    for _,row in ipairs(m.rows) do row:Hide() end
    local index,y=0,0
    local relevant={}
    for _,row in ipairs(A.rows or {}) do if row.category then relevant[row.category]=true end end
    -- A.Draw also supplies categories when called manually rather than through Refresh.
    for _,widget in ipairs((A.frame and A.frame.widgets) or {}) do if widget.row then relevant[widget.row.category]=true end end
    local function entry(cat,sub,title,expanded)
        index=index+1
        local w=m.rows[index]
        if not w then
            w=CreateFrame('Frame',nil,m.content);w:SetSize(266,29)
            w.check=CreateFrame('CheckButton',nil,w,'UICheckButtonTemplate');w.check:SetSize(22,22)
            w.label=text(w,'',11);w.label:SetJustifyH('LEFT');w.label:SetHeight(18)
            w.expand=CreateFrame('Button',nil,w);w.expand:SetSize(25,25)
            local fs=text(w.expand,'+',13);fs:SetPoint('CENTER');w.expand:SetFontString(fs)
            w.check:SetScript('OnClick',function()
                local key=w.cat..(w.sub and '/'..w.sub or '')
                A.SetCategory(w.cat,w.sub,A.db.filters[key]==false)
                A.UpdateFilterButton();A.UpdateFilters()
            end)
            w.expand:SetScript('OnClick',function()
                A.db.filterExpanded[w.cat]=not w.expanded;A.UpdateFilters()
            end)
            m.rows[index]=w
        end
        w.cat,w.sub,w.expanded=cat,sub,expanded
        w:ClearAllPoints();w:SetPoint('TOPLEFT',0,-y);w:Show()
        w.check:ClearAllPoints();w.check:SetPoint('LEFT',sub and 20 or 0,0)
        w.check:SetChecked(A.db.filters[cat..(sub and '/'..sub or '')]~=false)
        w.check:SetEnabled(not sub or A.CategoryEnabled(cat))
        w.label:ClearAllPoints();w.label:SetPoint('LEFT',w.check,'RIGHT',3,0);w.label:SetWidth(sub and 211 or 207)
        A.SetText(w.label,title);A.Font(w.label,11,sub~=nil,cat)
        w.expand:SetShown(not sub)
        w.expand:ClearAllPoints();w.expand:SetPoint('RIGHT',0,0);A.SetText(w.expand,expanded and '-' or '+')
        y=y+29
    end
    A.db.filterExpanded=A.db.filterExpanded or {};m.expanded=m.expanded or {}
    for _,cat in ipairs(A.categories) do
        local expanded=A.db.filterExpanded[cat.id]
        if expanded==nil then
            if m.expanded[cat.id]==nil then m.expanded[cat.id]=relevant[cat.id]==true end
            expanded=m.expanded[cat.id]
        end
        entry(cat.id,nil,cat.name,expanded)
        if expanded then
            local subs={};for sub in pairs(cat.subs) do subs[#subs+1]=sub end
            table.sort(subs,function(a,b) return A.Translate(cat.subs[a])<A.Translate(cat.subs[b]) end)
            for _,sub in ipairs(subs) do entry(cat.id,sub,cat.subs[sub]) end
        end
    end
    m.content:SetHeight(math.max(1,y));m:SetHeight(math.min(340,y+48))
    m.scroll:SetHeight(math.min(292,y));A.UpdateScroll(m.scroll)
end
function A.ShowFilters(anchor)
    local m=A.filterMenu
    if m and m:IsShown() then A.CloseFilters();return end
    if A.reminderMenu then A.reminderMenu:Hide() end
    if not m then
        m=CreateFrame('Frame','OneLastThingFilterMenu',UIParent,'BackdropTemplate');A.filterMenu=m
        m:SetSize(290,240);m:SetFrameStrata('DIALOG');m:SetClampedToScreen(true);m:EnableMouse(true)
        m.pitSettingsBackground=true;A.Panel(m)
        m.title=text(m,'Show categories',13);m.title:SetPoint('TOPLEFT',12,-10);A.Tint(m.title,'brand')
        m.close=CreateFrame('Button',nil,m);m.close:SetSize(24,24);m.close:SetPoint('TOPRIGHT',-6,-5)
        local label=text(m.close,'x',12);label:SetPoint('CENTER');m.close:SetFontString(label)
        m.close:SetScript('OnClick',A.CloseFilters)
        m.scroll=CreateFrame('ScrollFrame',nil,m);m.scroll:SetPoint('TOPLEFT',10,-36);m.scroll:SetSize(270,190)
        m.content=CreateFrame('Frame',nil,m.scroll);m.content:SetSize(266,1);A.AttachScrolling(m.scroll,m.content)
        m:EnableMouseWheel(true);m:SetScript('OnMouseWheel',function(_,delta) local wheel=m.scroll:GetScript('OnMouseWheel');if wheel then wheel(m.scroll,delta) end end)
        m.rows={}
        table.insert(UISpecialFrames,'OneLastThingFilterMenu')
        m:SetScript('OnHide',function()
            local f=A.frame
            if f and f:IsShown() and not A.db.collapsed and (f.rowCount or 0)==0 then A.SetCollapsed(true,'auto') end
        end)
    end
    m:ClearAllPoints()
    if A.db.headerPosition=='bottom' then m:SetPoint('BOTTOMRIGHT',anchor,'TOPRIGHT',0,4)
    else m:SetPoint('TOPRIGHT',anchor,'BOTTOMRIGHT',0,-4) end
    m:Show();A.UpdateFilters()
end
