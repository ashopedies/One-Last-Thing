local _,A=...
A.categories={
    {id='quests',name='Quests & chains',subs={turnins='Other completed quests',bagquests='Quest items in bags'}},
    {id='professions',name='Professions',subs={
        ['129']='First Aid',['185']='Cooking',['356']='Fishing',['171']='Alchemy',
        ['164']='Blacksmithing',['333']='Enchanting',['202']='Engineering',
        ['182']='Herbalism',['165']='Leatherworking',['186']='Mining',
        ['393']='Skinning',['197']='Tailoring'}},
    {id='training',name='Class & other training',subs={class='Class spells',weapons='Weapon skills',talents='Unspent talent points'}},
    {id='supplies',name='Supplies',subs={['17030']='Ankhs'}},
    {id='errands',name='Travel & errands',subs={bags='Bag space',flights='Flight paths',repairs='Repairs',hearthstone='Hearthstone',petmood='Hunter pet mood'}},
}
function A.Category(row)
    local key=row.key or ''
    local cat,sub,label
    if row.professionID or row.skill then
        cat='professions';sub=tostring(row.professionID or row.skill);label=row.profession or row.title:match('^([^:]+):') or sub
    elseif row.attuneStep then
        cat='quests';sub='chain:'..row.attuneStep.ID_ATTUNE;label=row.chainName or 'Quest chain'
    elseif row.bagQuest then cat='quests';sub='bagquests';label='Quest items in bags'
    elseif row.quest then cat='quests';sub='turnins';label='Other completed quests'
    elseif row.talents then cat='training';sub='talents';label='Unspent talent points'
    elseif row.ammoItem then cat='supplies';sub='ammo';label='Hunter ammunition'
    elseif key:find('^supply:') then cat='supplies';sub=key:sub(8);label=A.ItemName(tonumber(sub))
    elseif row.weapon then cat='training';sub='weapons';label='Weapon skills'
    elseif row.repair then cat='errands';sub='repairs';label='Repairs'
    elseif row.flight then cat='errands';sub='flights';label='Flight paths'
    elseif row.hearthstone then cat='errands';sub='hearthstone';label='Hearthstone'
    elseif row.petMood then cat='errands';sub='petmood';label='Hunter pet mood'
    elseif key:find('^train:') then cat='training';sub='class';label='Observed trainer spells'
    else cat='errands';sub='bags';label='Bag space' end
    for _,c in ipairs(A.categories) do
        if c.id==cat then
            if not c.subs[sub] then c.subs[sub]=label end
            row.category,row.subcategory=cat,sub
            row.categoryName,row.subcategoryName=c.name,c.subs[sub]
            return cat,sub
        end
    end
end
function A.CategoryEnabled(cat,sub)
    local filters=A.db.filters or {}
    return filters[cat]~=false and (not sub or filters[cat..'/'..sub]~=false)
end
function A.SetCategory(cat,sub,enabled)
    A.db.filters=A.db.filters or {}
    A.db.filters[cat..(sub and '/'..sub or '')]=enabled
    if A.InvalidateProviders then A.InvalidateProviders() end
    A.Refresh('Updated',false)
end
