local _,A=...
function A.MakeTrashRecord(row)
    local r={hiddenAt=time()}
    for _,field in ipairs({'key','title','detail','quest','spell','professionID','profession','map','x','y','category','subcategory','subcategoryName','importantReason','cost','rank','spellName','weapon','flight','capMax','criticalBook','buyItem','why','buyAhead'}) do
        local v=row[field]
        if type(v)=='string' or type(v)=='number' or type(v)=='boolean' then r[field]=v end
    end
    if row.quest then r.questLevel=A.QuestRecommendedLevel(row.quest) or row.questLevel end
    return r
end
local function record(key,value)
    if type(value)=='table' then return value end
    local r={key=key,title=key,quest=tonumber(key:match('^quest:(%d+)')),spell=tonumber(key:match('^train:spell:(%d+)'))}
    if r.quest then
        r.title=(LibQuestieDB and LibQuestieDB.Quest and A.Safe('trash quest title',LibQuestieDB.Quest.Get,r.quest,'name'))
            or (C_QuestLog and A.Safe('trash quest title',C_QuestLog.GetTitleForQuestID,r.quest)) or ('Quest '..r.quest)
    elseif r.spell then
        local info=C_Spell and A.Safe('trash spell title',C_Spell.GetSpellInfo,r.spell)
        r.title=info and info.name or ('Spell '..r.spell)
    end
    r.professionID=tonumber(key:match('^cap:(%d+)'))
    return r
end
local function professions()
    local ids={};local certain=false
    local api=SkillUpForever and SkillUpForever.API
    local list=api and A.Safe('trash professions',api.Professions)
    if list then for _,p in ipairs(list) do ids[p.skillLineID]=p end end
    if GetProfessions and GetProfessionInfo then
        local ok,a,b,c,d,e,f=pcall(GetProfessions)
        if ok then
            certain=true
            for _,index in pairs({a,b,c,d,e,f}) do
                local good,name,_,rank,maxRank,_,_,skill=pcall(GetProfessionInfo,index)
                if good and skill then ids[skill]={name=name,rank=rank,maxRank=maxRank} end
            end
        end
    end
    return ids,certain
end
local function knownClassRanks()
    local _,class=UnitClass('player')
    local source=(TrainerSpells_Data and TrainerSpells_Data[class]) or (TrainerSpellsBuiltin and TrainerSpellsBuiltin[class]) or {}
    local ranks={}
    for _,spells in pairs(source) do
        for key,value in pairs(type(spells)=='table' and spells or {}) do
            local d=type(value)=='table' and value or {}
            local id=d.spellID or (type(key)=='number' and key)
            local rank=tonumber(d.rank) or tonumber(tostring(d.rank or ''):match('%d+'))
            if id and rank and A.SpellKnown(id) then
                local info=C_Spell and A.Safe('trash known spell family',C_Spell.GetSpellInfo,id)
                local name=info and info.name or A.Safe('trash spell family',GetSpellInfo,id)
                if name then ranks[name]=math.max(ranks[name] or 0,rank) end
            end
        end
    end
    return ranks
end
local function isLearned(r,ranks)
    if not r.spell then return false end
    if A.SpellKnown(r.spell) then return true end
    if r.spellName and r.rank and (ranks[r.spellName] or 0)>=r.rank then return true end
    local info=C_TradeSkillUI and A.Safe('trashed recipe learned',C_TradeSkillUI.GetRecipeInfo,r.spell)
    return info and info.learned==true
end
function A.TrashEntries()
    local entries={};local records={};local needRanks=false
    for key,value in pairs(A.db.trash) do
        if value then
            local r=record(key,value)
            records[#records+1]={key=key,record=r}
            if r.spell and r.spellName and r.rank then needRanks=true end
        end
    end
    local skills,certain=professions();local ranks=needRanks and knownClassRanks() or {}
    for _,item in ipairs(records) do
        local key,r=item.key,item.record
        if r then
            local score,reason=500,'Other hidden reminder'
            local gray=r.quest and A.IsGrayQuest(r.quest)
            if gray==nil and r.questLevel and r.questLevel>0 and C_QuestLog and C_QuestLog.GetTrivialRange then
                local range=A.Safe('trash gray range',C_QuestLog.GetTrivialRange)
                if type(range)=='number' then gray=r.questLevel<UnitLevel('player')-range end
            end
            if gray then score,reason=10000,'Grey quest — lowest priority'
            elseif r.quest and A.QuestDone(r.quest) then score,reason=8000,'Quest already completed'
            elseif isLearned(r,ranks) then score,reason=7000,'Already learned'
            elseif r.professionID then
                local p=skills[r.professionID]
                if p and r.capMax and p.maxRank and (p.maxRank>r.capMax or (r.criticalBook and p.maxRank>=r.capMax)) then score,reason=7000,'Profession rank already surpassed'
                elseif p then score,reason=40,(p.name or r.profession or 'Current profession')..' — still relevant'
                elseif certain then score,reason=7500,'Profession no longer learned'
                else score,reason=450,'Profession relevance not confirmed' end
            elseif r.quest and A.QuestActive(r.quest) then score,reason=80,'Quest currently in your log'
            elseif r.spell then
                local money=A.Safe('trash affordability',GetMoney)
                if r.cost and money and money>=r.cost then score,reason=150,'Unlearned — affordable now'
                else score,reason=220,'Unlearned — train whenever you choose' end
            elseif r.quest then score,reason=250,'Unfinished quest' end
            entries[#entries+1]={key=key,record=r,score=score,reason=reason}
        end
    end
    table.sort(entries,function(a,b)
        if a.score==b.score then return (a.record.title or a.key)<(b.record.title or b.key) end
        return a.score<b.score
    end)
    return entries
end
function A.RestoreTrash(key)
    local r=record(key,A.db.trash[key]);A.db.trash[key]=nil
    for _,k in ipairs({key,r.key or key,r.quest and ('quest:'..r.quest..':start') or key,r.quest and ('quest:'..r.quest..':end') or key}) do
        A.db.dismissed[k]=nil;A.db.snoozed[k]=nil
    end
    A.Refresh('Restored',false)
end
function A.DrawTrashBin()
    local f=A.trashFrame;if not f then return end
    local entries=A.TrashEntries();A.SetText(f.title,'Ignored reminders ('..#entries..')')
    for _,w in ipairs(f.rows) do w:Hide() end
    for i,entry in ipairs(entries) do
        local w=f.rows[i]
        if not w then
            w=CreateFrame('Frame',nil,f.content);w:SetSize(414,66)
            w.title=w:CreateFontString(nil,'OVERLAY','GameFontHighlight');w.title:SetPoint('TOPLEFT',5,-6);w.title:SetWidth(245);w.title:SetHeight(18);w.title:SetJustifyH('LEFT');A.Font(w.title,12)
            w.detail=w:CreateFontString(nil,'OVERLAY','GameFontHighlightSmall');w.detail:SetPoint('TOPLEFT',5,-28);w.detail:SetWidth(395);w.detail:SetHeight(28);w.detail:SetJustifyH('LEFT');A.Font(w.detail,10,true)
            w.restore=CreateFrame('Button',nil,w,'BackdropTemplate');w.restore:SetSize(150,23);w.restore:SetPoint('TOPRIGHT',-3,-3)
            local fs=w.restore:CreateFontString(nil,'OVERLAY','GameFontHighlightSmall');fs:SetPoint('CENTER');w.restore:SetFontString(fs);A.SetText(w.restore,'Remind me again');A.StyleButton(w.restore);A.Tint(fs,'action')
            w.restore:SetScript('OnClick',function() A.RestoreTrash(w.key) end);f.rows[i]=w
        end
        w.key=entry.key;w:ClearAllPoints();w:SetPoint('TOPLEFT',0,-(i-1)*66)
        A.SetText(w.title,A.ReminderTitle({title=entry.record.title or entry.key,quest=entry.record.quest,questLevel=entry.record.questLevel}));A.SetText(w.detail,entry.reason)
        A.Tint(w.title,entry.score>=7000 and 'muted' or (entry.record.professionID and 'professions' or 'brand'))
        w:Show()
    end
    f.empty:SetShown(#entries==0);f.content:SetHeight(math.max(100,#entries*66));A.UpdateScroll(f.scroll)
end
function A.ShowTrashBin()
    if InCombatLockdown() then return end
    if A.trashFrame then A.DrawTrashBin();A.trashFrame:Show();return end
    local f=CreateFrame('Frame','OneLastThingTrashBin',UIParent,'BackdropTemplate');A.trashFrame=f
    f:SetSize(460,460);f:SetPoint('CENTER',UIParent,'CENTER',75,-20);f:SetFrameStrata('MEDIUM');f:SetFrameLevel((A.settings and A.settings:GetFrameLevel() or 1)+10)
    f.pitSettingsBackground=true;A.Panel(f);f:SetClampedToScreen(true);f:SetMovable(true);f:EnableMouse(true);f:RegisterForDrag('LeftButton')
    f:SetScript('OnDragStart',f.StartMoving);f:SetScript('OnDragStop',f.StopMovingOrSizing)
    f.title=f:CreateFontString(nil,'OVERLAY','GameFontHighlight');f.title:SetPoint('TOPLEFT',16,-14);A.Font(f.title,16,false,'brand')
    local close=CreateFrame('Button',nil,f,'BackdropTemplate');close:SetSize(23,23);close:SetPoint('TOPRIGHT',-9,-9)
    local fs=close:CreateFontString(nil,'OVERLAY','GameFontHighlightSmall');fs:SetPoint('CENTER');close:SetFontString(fs);A.SetText(close,'x');A.StyleButton(close);close:SetScript('OnClick',function() f:Hide() end)
    f.scroll=CreateFrame('ScrollFrame',nil,f);f.scroll:SetPoint('TOPLEFT',14,-49);f.scroll:SetPoint('BOTTOMRIGHT',-14,34)
    f.content=CreateFrame('Frame',nil,f.scroll);f.content:SetSize(414,100);A.AttachScrolling(f.scroll,f.content);f.rows={}
    f.empty=f.content:CreateFontString(nil,'OVERLAY','GameFontHighlight');f.empty:SetPoint('TOPLEFT',5,-9);A.SetText(f.empty,'No ignored reminders.');A.Font(f.empty,12,true)
    local hint=f:CreateFontString(nil,'OVERLAY','GameFontHighlightSmall');hint:SetPoint('BOTTOMLEFT',16,13);A.SetText(hint,'Learned or completed items stay out of the checklist.');A.Font(hint,10,true)
    table.insert(UISpecialFrames,'OneLastThingTrashBin');A.DrawTrashBin();f:Show()
end
