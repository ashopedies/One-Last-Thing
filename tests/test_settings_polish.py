"""Small borrowed UI refinements without importing the experimental addon."""
from test_startup import fresh_client


def run():
    for locale in ('enUS','deDE'):
        vm=fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            assert(A.SkippedCount()==0)
            A.db.dismissed={a=true,b=true,ignored=true}
            A.db.snoozed={a=time()+60,c=time()+60,expired=time()-1}
            A.db.trash.ignored=true
            assert(A.SkippedCount()==3)
            A.db.collapsed=false;A.LayoutBottomBar()
            assert(A.frame.restoreButton:GetText():find('(3)',1,true))
            A.ShowSettings()
            local f=A.settings
            assert(f.skippedStatus:GetText():find('3',1,true))
            local heading={};local itemLabel,targetLabel
            for _,fs in ipairs(f.fontPool) do
                heading[fs:GetText()]=true
                assert(not fs:GetText():find('                           ',1,true))
            end
            assert(heading[A.Translate('Window & layout')])
            assert(heading[A.Translate('Theme & style')])
            assert(heading[A.Translate('Text')])
            assert(heading[A.Translate('Add item ID')])
            assert(heading[A.Translate('Target')])
            assert(f.scale and f.opacity and f.fontSize and f.supplyItem and f.supplyCount)
            A.db.dismissed={};A.db.snoozed={};A.BuildSettings();A.LayoutBottomBar()
            assert(A.SkippedCount()==0 and not A.frame.restoreButton:GetText():find('(3)',1,true))
            assert(f.skippedStatus:GetText()==A.Translate('No reminders skipped this visit.'))
            A.db.dismissed.a=true;A.BuildSettings()
            assert(f.skippedStatus:GetText()==A.Translate('1 reminder skipped this visit.'))
            if A.IsGerman() then
                assert(A.Translate('Map 123')=='Karte 123')
                assert(A.Translate('spell 123')=='Zauber 123')
                assert(A.Translate('Automatic popups: false')=='Automatische Hinweise: aus')
                A.deDE['Fixture chain']='Testkette'
                assert(A.Translate('Grey prerequisite — raid/access chain: Fixture chain'):find('Testkette',1,true))
                assert(A.Translate('Observed training')=='Erfasste Ausbildung')
                assert(A.Translate('Add item ID')=='Gegenstands-ID')
            end
        ''')
    print('PASS: EN/DE aligned supply captions, Appearance groups, live deduplicated skipped counts excluding ignored/expired entries, recovery and translation fixes')


if __name__=='__main__':
    run()
