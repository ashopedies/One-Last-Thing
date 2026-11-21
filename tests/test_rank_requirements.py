"""Known profession gates remain visible without inventing trainable actions."""
from test_startup import fresh_client


def run():
    for locale in ('enUS', 'deDE'):
        vm = fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            local current,level
            UnitLevel=function() return level end
            SkillUpForever={API={version=1,Professions=function() return {current} end}}
            TrainerSpellsProfessionTrainers={}
            A.scope={map=1458,x=.5,y=.5}
            -- Trainer, book and quest gates: skill requirement, character level.
            local facts={
                [164]={{50,10},{125,20},{200,35}},[165]={{50,10},{125,20},{200,35}},
                [171]={{50,10},{125,20},{200,35}},[197]={{50,10},{125,20},{200,35}},
                [202]={{50,10},{125,20},{200,35}},[333]={{50,10},{125,20},{200,35}},
                [182]={{50,0},{125,0},{200,0}},[186]={{50,0},{125,0},{200,0}},
                [393]={{50,0},{125,0},{200,35}},
                [129]={{50,0},{125,0},{225,35}},[185]={{50,10},{125,0},{225,35}},
                [356]={{50,10},{125,20},{225,35}},
            }
            local count=0
            for id,ranks in pairs(facts) do
                for index,req in ipairs(ranks) do
                    local cap=index*75
                    level=math.max(1,req[2]-1)
                    current={name=id==197 and (testLocale=='deDE' and 'Schneiderei' or 'Tailoring') or 'Test profession',
                        skillLineID=id,rank=cap-10,maxRank=cap,steps={}}
                    local out={};A.ProfessionRows(out,1458)
                    assert(#out==1 and out[1].key=='cap:'..id and not out[1].map and not out[1].professionRank)
                    local row=out[1]
                    assert(row.requiredSkill==req[1] and row.requiredLevel==req[2])
                    assert(row.detail:find(tostring(req[1]),1,true) and row.detail:find(tostring(cap),1,true))
                    if req[2]>0 then
                        assert(row.detail:find((testLocale=='deDE' and 'Benötigt Stufe ' or 'Requires level ')..req[2],1,true))
                    else
                        assert(not row.detail:find('Requires level',1,true) and not row.detail:find('Benötigt Stufe',1,true))
                    end
                    assert(row.detail:find(A.Translate('Local trainer not confirmed.'),1,true))
                    if id==197 and cap==150 then
                        assert(row.detail:find(testLocale=='deDE' and 'Schneiderei 125' or 'Tailoring 125',1,true))
                    end
                    A.db.dismissed[row.key]=true;out={};A.ProfessionRows(out,1458);assert(#out==0);A.db.dismissed={}
                    count=count+1
                end
            end
            assert(count==36)
            current={name='Tailoring',skillLineID=197,rank=140,maxRank=150,steps={}}
            TrainerSpellsProfessionTrainers={Tailoring={{npcID=4576,rank=3,faction='H',names={enUS='Josef Gregorian'},
                locations={{uiMapID=1458,x=50,y=50}}}}}
            level=19;local out={};A.ProfessionRows(out,1458)
            assert(#out==1 and out[1].key=='cap:197' and out[1].requiredLevel==20)
            level=20;out={};A.ProfessionRows(out,1458)
            assert(#out==1 and out[1].professionRank and out[1].map==1458)
            assert(out[1].detail:find(A.Translate('Requires level 20'),1,true))
            current.maxRank=225;current.rank=150;out={};A.ProfessionRows(out,1458);assert(#out==0)
            current.maxRank=300;current.rank=295;out={};A.ProfessionRows(out,1458);assert(#out==0)
            -- Unknown professions retain an honest generic warning, no guessed gate.
            current={name='Unknown profession',skillLineID=99999,rank=140,maxRank=150,steps={}}
            out={};A.ProfessionRows(out,1458)
            assert(#out==1 and out[1].requiredLevel==nil)
            assert(not A.ProfessionRankRequirementText(current))
        ''')
    print('PASS: 72 EN/DE profession cap gates across all twelve professions, trainer/book/quest requirements, no invented level gates or destinations, skip and level-up eligibility transitions')


if __name__ == '__main__':
    run()
