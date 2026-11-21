"""All three row actions fit directly in each layout; no overflow/snooze UI."""
from test_startup import fresh_client


def run():
    for locale in ('enUS', 'deDE'):
        vm = fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            local row={key='test:actions',title='A long reminder title to exercise truncation',map=1458,x=50,y=50,distanceYards=180}
            A.providerHealth={}
            for _,mode in ipairs({'default','compact','minimal'}) do
                for _,scale in ipairs({.8,1,1.3}) do
                    A.db.rowMode=mode;A.db.fontScale=scale
                    for _,width in ipairs({360,440,950}) do
                        A.SetCollapsed(false,'manual');A.frame:SetSize(width,320)
                        A.Draw({row},'Manual check',true)
                        local w=A.frame.rowPool[1]
                        for _,b in ipairs({w.go,w.dismiss,w.ignore}) do
                            local fs=b:GetFontString()
                            fs.GetStringWidth=function() return #b:GetText()*6.5*A.db.fontScale end
                            b.SetPoint=function(self,point,parent,relative,x,y) self.actionX=x;self.actionY=y end
                        end
                        A.ApplyFonts();A.Layout()
                        assert(w.go:IsShown() and w.dismiss:IsShown() and w.ignore:IsShown())
                        assert(not w.more and not w.snooze and not A.reminderMenu and not A.ShowReminderMenu)
                        assert(w.go.actionX>=0)
                        assert(w.go.actionX+w.go:GetWidth()<=w.dismiss.actionX)
                        assert(w.dismiss.actionX+w.dismiss:GetWidth()<=w.ignore.actionX)
                        assert(w.ignore.actionX+w.ignore:GetWidth()<=w:GetWidth())
                        if mode=='minimal' then
                            local titleEnd=8+w.title:GetWidth()
                            assert(titleEnd<w.go.actionX)
                            assert(w:GetHeight()==27)
                        end
                        for _,b in ipairs({w.go,w.dismiss,w.ignore}) do assert(b:GetText()~='...' and b:GetScript('OnEnter')) end
                        assert(w.ignore:GetText()==(testLocale=='deDE' and 'Ignorieren' or 'Ignore'))
                    end
                end
            end
            -- Non-navigable reminders keep Skip/Ignore and hide Map.
            A.Draw({{key='test:plain',title='No destination'}},'Updated',true)
            local w=A.frame.rowPool[1]
            assert(not w.go:IsShown() and w.dismiss:IsShown() and w.ignore:IsShown())
            local help={}
            GameTooltip={SetOwner=function() end,SetText=function(_,text) help[#help+1]=text end,Show=function() end,Hide=function() end}
            w.dismiss:GetScript('OnEnter')(w.dismiss)
            w.ignore:GetScript('OnEnter')(w.ignore)
            assert(#help==2 and help[1]~=help[2])
            if testLocale=='deDE' then assert(help[2]:find('Ignorierte Hinweise',1,true))
            else assert(help[2]:find('Settings > Ignored reminders',1,true)) end
        ''')
    print('PASS: direct Map/Skip/Ignore in every density, EN/DE, 80-130% fonts and narrow/wide windows; '
          'non-overlap, title space, no overflow/timer UI, no-destination rows and distinct recovery tooltips')


if __name__ == '__main__':
    run()
