local _, A = ...
-- Lua source uses two backslashes per separator, yielding one in the game path.
local media='Interface\\AddOns\\NeavMedia\\Media\\'
local function neav()
    return C_AddOns and C_AddOns.IsAddOnLoaded and C_AddOns.IsAddOnLoaded('NeavMedia')
end
A.fonts=setmetatable({},{__mode='k'})
A.panels=setmetatable({},{__mode='k'})
-- Each theme has exactly three foreground colors. Muted text changes only
-- opacity, never introduces an extra RGB shade outside this palette.
A.themeNames={blizzard='Blizzard',class='Class Colors',pop='Pop',original='Original'}
A.toneSlots={brand=1,quests=1,training=1,warning=1,urgent=1,
    professions=2,supplies=2,action=2,success=2,
    errands=3,text=3,muted=3,dismiss=3,snooze=3}
A.originalColors={
    text={.76,.82,.87},muted={.53,.64,.70},brand={.94,.74,.42},
    quests={.96,.77,.38},professions={.40,.83,.65},training={.75,.63,.94},
    supplies={.35,.78,.92},errands={.48,.67,.85},action={.34,.76,.98},
    dismiss={.76,.55,.55},snooze={.66,.61,.82},success={.43,.87,.56},
    warning={1,.67,.31},urgent={1,.46,.37},
}
function A.ThemePalette(theme)
    if theme=='class' then
        local _,class=UnitClass('player')
        local c=RAID_CLASS_COLORS and RAID_CLASS_COLORS[class]
        if not c and C_ClassColor and C_ClassColor.GetClassColor then c=C_ClassColor.GetClassColor(class) end
        local r,g,b
        if c then
            if c.GetRGB then r,g,b=c:GetRGB() else r,g,b=c.r,c.g,c.b end
        end
        return {{r or .2,g or .65,b or 1},{1,.78,.35},{.83,.86,.90}}
    elseif theme=='pop' then
        return {{1,.40,.48},{.25,.92,.80},{.77,.69,1}}
    end
    return {{1,.82,0},{.42,.72,1},{.94,.90,.79}}
end
function A.ApplyTheme()
    local theme=A.db and A.db.theme or 'blizzard'
    if not A.themeNames[theme] then theme='blizzard';if A.db then A.db.theme=theme end end
    A.palette=A.ThemePalette(theme)
    A.ApplyFonts()
    for scroll in pairs(A.scrolls or {}) do
        local color=A.palette[2];scroll.pitThumb:SetColorTexture(color[1],color[2],color[3],.48)
    end
end
function A.SetTheme(theme)
    if not A.themeNames[theme] then return end
    A.db.theme=theme;A.ApplyTheme()
end
function A.SharedMedia()
    if not LibStub then return end
    local lib=A.Safe('shared media',function() return LibStub('LibSharedMedia-3.0',true) end)
    if lib and lib.RegisterCallback and A.sharedMediaWatched~=lib then
        A.sharedMediaWatched=lib
        lib.RegisterCallback(A,'LibSharedMedia_Registered',function(_,kind)
            if kind=='font' then
                if A.settings then A.settings.signature=nil end
                A.ApplyFonts()
            end
        end)
    end
    return lib
end
function A.FontChoices()
    local choices={{'arial','Arial Narrow (built in)'},{'expressway','Neav Expressway'},{'accidental','Neav Accidental Presidency'},{'game','Game default'}}
    local lib=A.SharedMedia()
    local names=lib and A.Safe('shared media fonts',lib.List,lib,'font')
    for _,name in ipairs(names or {}) do choices[#choices+1]={'lsm:'..name,name} end
    return choices
end
function A.Font(fs,size,dim,tone)
    A.fonts[fs]={size=size or 12,dim=dim,tone=tone}
    local d=A.db or {}
    local lsmName=(d.fontFace or ''):match('^lsm:(.+)$')
    local lib=A.SharedMedia()
    local shared=lsmName and lib and A.Safe('shared font file',lib.Fetch,lib,'font',lsmName,true)
    local face=(d.fontFace=='arial' and [[Fonts\ARIALN.TTF]]) or (lsmName and (shared or STANDARD_TEXT_FONT)) or (d.fontFace=='accidental' and neav() and media..'AccidentalPresidency.ttf')
        or (d.fontFace~='game' and neav() and media..'Expressway.ttf') or STANDARD_TEXT_FONT
    local outline=({none='',thin='OUTLINE',thick='THICKOUTLINE'})[d.fontOutline or 'none'] or ''
    local ok=fs:SetFont(face,(size or 12)*(d.fontScale or 1),outline)
    if ok==false and face~=STANDARD_TEXT_FONT then fs:SetFont(STANDARD_TEXT_FONT,(size or 12)*(d.fontScale or 1),outline) end
    A.palette=A.palette or A.ThemePalette(d.theme)
    local color=d.theme=='original' and (A.originalColors[tone or (dim and 'muted' or 'text')] or A.originalColors.text) or A.palette[A.toneSlots[tone or 'text'] or 3]
    fs:SetTextColor(color[1],color[2],color[3],dim and .76 or 1)
    local shadow=d.fontShadow or 'soft'
    fs:SetShadowColor(0,0,0,shadow=='none' and 0 or (shadow=='strong' and 1 or .8))
    local offset=shadow=='none' and 0 or (shadow=='strong' and 2 or 1)
    fs:SetShadowOffset(offset,-offset)
end
function A.ApplyFonts()
    for fs,v in pairs(A.fonts) do A.Font(fs,v.size,v.dim,v.tone) end
    if A.ApplyCollapsed and A.db and A.db.collapsed then A.ApplyCollapsed()
    elseif A.Layout then A.Layout() end
end
function A.Tint(fs,tone)
    local v=A.fonts[fs] or {size=12}
    A.Font(fs,v.size,v.dim,tone)
end
function A.RowTone(row)
    if row.importantReason then return 'warning' end
    if row.key=='bags' or row.repair then return 'warning' end
    if row.key:find('^supply:') then
        local id=tonumber(row.key:sub(8))
        return id and A.ItemCount(id)==0 and 'urgent' or 'warning'
    end
    if row.key:find(':end$') then return 'success' end
    return row.category or 'text'
end
function A.Background(frame,r,g,b,factor)
    A.panels[frame]={r=r,g=g,b=b,factor=factor or 1}
    local compact=frame==A.frame and A.db and A.db.collapsed
    frame:SetBackdropColor(r,g,b,compact and 0 or (frame.pitSettingsBackground and .7 or (((A.db and A.db.opacity) or 0)*(factor or 1))))
end
function A.ApplyOpacity()
    for f,v in pairs(A.panels) do f:SetBackdropColor(v.r,v.g,v.b,(f==A.frame and A.db.collapsed) and 0 or (f.pitSettingsBackground and .7 or A.db.opacity*v.factor)) end
end
function A.Panel(frame)
    frame:SetBackdrop({bgFile='Interface/Buttons/WHITE8X8'})
    A.Background(frame,0,0,0,1)
end
function A.StyleButton(b)
    A.Background(b,.09,.09,.10,1);A.Font(b:GetFontString(),11)
    if b.oltStyled then return end
    b.oltStyled=true;A.Panel(b);A.Background(b,.09,.09,.10,1)
    b:SetScript('OnEnter',function(self) A.Background(self,.18,.18,.20,1) end)
    b:SetScript('OnLeave',function(self) A.Background(self,.09,.09,.10,1) end)
    b:SetScript('OnMouseDown',function(self) A.Background(self,.04,.04,.05,1) end)
    b:SetScript('OnMouseUp',function(self) A.Background(self,.18,.18,.20,1) end)
end

function A.AdjustFontSize(delta)
    if not A.db or type(delta)~='number' then return end
    local percent=math.max(80,math.min(130,math.floor((A.db.fontScale or 1)*100+.5)+delta))
    if math.abs(percent/100-(A.db.fontScale or 1))<.0001 then return end
    A.db.fontScale=percent/100
    A.ApplyFonts()
    if A.settings and A.settings:IsShown() and A.settings.fontSize then A.settings.fontSize:SetValue(percent) end
end
