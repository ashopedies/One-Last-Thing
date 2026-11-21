"""Hover explanations describe evidence; cap-advice visibility is independent."""
from test_startup import fresh_client


def run():
    for locale in ('enUS', 'deDE'):
        vm = fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            assert(A.db.showCapWarnings==true)
            local cases={
                {key='train:spell:111',classSpell=true,provider='ClassSpellRows',spell=111,cost=0,priceConfidence='catalogue',map=1458,x=50,y=50,locationSource='TrainerSpells',verify=true},
                {key='supply:17030',provider='SupplyRows',cost=100,priceConfidence='observed',map=1458,x=50,y=50,locationSource='Observed by you'},
                {key='buybook:16083',criticalBook=true,buyAhead=true,priceConfidence='estimate',requiredLevel=20,map=1434,x=27,y=77,locationSource='OLT curated locations'},
                {key='cap:197',informational=true,requiredLevel=20},
                {key='flight:1',flight=true,map=1458,x=50,y=50,locationSource='WoW taxi map'},
                {key='train:spell:222',classSpell=true,spell=222,priceConfidence='unknown'},
            }
            for _,row in ipairs(cases) do
                local lines=A.ReminderExplanation(row)
                assert(#lines>=3 and lines[1]:find(A.Translate('Source')..': ',1,true))
                if testLocale=='deDE' then assert(lines[1]:find('Quelle:',1,true)) end
            end
            local lines=table.concat(A.ReminderExplanation(cases[1]),'\\n')
            assert(lines:find('TrainerSpells',1,true) and lines:find(A.Translate('Catalogue price; discounts may differ.'),1,true))
            assert(lines:find(A.Translate('Recorded coordinates; not a live NPC check.'),1,true))
            lines=table.concat(A.ReminderExplanation(cases[2]),'\\n')
            assert(lines:find(A.Translate('Recorded during an earlier visit; not a live NPC check.'),1,true))
            assert(lines:find(A.Translate('Observed price; check the current offer.'),1,true))
            lines=table.concat(A.ReminderExplanation(cases[3]),'\\n')
            assert(lines:find(A.Translate('Requires level 20'),1,true) and lines:find(A.Translate('Estimated price; verify at the merchant.'),1,true))
            lines=table.concat(A.ReminderExplanation(cases[6]),'\\n');assert(lines:find(A.Translate('price unknown'),1,true))
            -- Row hover exposes the section in every density without extra controls.
            local text={}
            GameTooltip={SetOwner=function() end,SetText=function(_,s) text[#text+1]=s end,
                AddLine=function(_,s) text[#text+1]=s end,Show=function() end,Hide=function() end}
            cases[1].title='Test spell'
            for _,mode in ipairs({'default','compact','minimal'}) do
                A.db.rowMode=mode;A.Draw({cases[1]},'Test')
                text={};local w=A.frame.widgets[1];w:GetScript('OnEnter')(w)
                local all=table.concat(text,'\\n')
                assert(all:find(A.Translate('Why this reminder?'),1,true) and all:find(A.Translate('Source')..': TrainerSpells',1,true))
            end
            -- Provenance follows selected cached coordinates, not the previous NPC.
            A.scope={map=1413,x=.5,y=.5}
            local row={key='quest:111:start',destinations={
                {map=1413,x=50,y=50,name='A',locationSource='Attune'},
                {map=1413,x=90,y=90,name='B',locationSource='QuestieDB'}},destinationSuffix=' detail'}
            local placed=A.PlaceDestination(row,1413);assert(placed.locationSource=='Attune')
            A.scope.x=.9;A.scope.y=.9;placed=A.PlaceDestination(row,1413);assert(placed.locationSource=='QuestieDB' and row.locationSource==nil)
        ''')
    print('PASS: EN/DE Why this reminder hover in all densities, recorded versus observed locations, catalogue/observed/estimated/unknown prices, required levels and immutable moving provenance')

    for locale in ('enUS', 'deDE'):
        vm = fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            local p={name='Tailoring',skillLineID=197,rank=140,maxRank=150,steps={}}
            A.ProfessionPlans=function() return {p} end
            local level=19;UnitLevel=function() return level end
            A.scope={map=1458,x=.5,y=.5}
            TrainerSpellsProfessionTrainers={Tailoring={{rank=3,faction='H',names={enUS='Tailor'},locations={{uiMapID=1458,x=50,y=50}}}}}
            local out={};A.ProfessionRows(out,1458)
            assert(#out==1 and out[1].informational and out[1].key=='cap:197')
            A.ShowSettings();local toggle
            for _,b in ipairs(A.settings.boxes) do if b.label:GetText()==A.Translate('Show informational profession-cap warnings') then toggle=b end end
            assert(toggle and toggle.read());local books=A.db.importantVendorBuys
            toggle:GetScript('OnClick')();assert(A.db.showCapWarnings==false and A.db.importantVendorBuys==books)
            out={};A.ProfessionRows(out,1458);assert(#out==0)
            -- Actual local training still appears once eligible.
            level=20;out={};A.ProfessionRows(out,1458)
            assert(#out==1 and out[1].professionRank and out[1].locationSource=='TrainerSpells')
            A.Init();assert(A.db.showCapWarnings==false)
            -- Buy-ahead books keep their own setting and requirements.
            p={name='Cooking',skillLineID=185,rank=100,maxRank=150,steps={}}
            GetMoney=function() return 100000 end;A.ItemCount=function() return 0 end;A.CriticalBookOwned=function() return false end
            A.FindVendor=function() return {map=1458,x=50,y=50,name='Seller',source='QuestieDB'} end
            out={};A.ImportantVendorRows(out,1458)
            assert(#out==1 and out[1].criticalBook and out[1].buyAhead and out[1].locationSource=='QuestieDB' and out[1].priceConfidence=='estimate')
            -- Artisan rank quests are not informational cap warnings.
            p={name='First Aid',skillLineID=129,rank=225,maxRank=225,steps={}};level=35
            A.scope={map=1417,x=.734,y=.368}
            A.QuestDone=function() return false end;A.QuestActive=function() return false end;A.QuestEligible=function() return true end
            out={};A.ProfessionRows(out,1417)
            assert(#out==1 and out[1].quest==6622 and out[1].professionRank)
        ''')
    # Existing, malformed and independent character settings.
    for saved, expected in (('{showCapWarnings=false}', False), ('{showCapWarnings="bad"}', True), ('nil', True)):
        vm=fresh_client(saved=saved)
        assert vm.globals().OneLastThing.db.showCapWarnings == expected
    print('PASS: per-character informational-cap toggle, actual settings control and reload persistence, independent defaults, local rank training, Artisan quests and buy-ahead books preserved')


if __name__ == '__main__':
    run()
