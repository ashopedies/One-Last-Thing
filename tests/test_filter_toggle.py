"""Filter is a menu toggle, not an empty-window collapse shortcut."""
from test_startup import fresh_client


def run():
    for locale in ('enUS','deDE'):
        vm=fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            A.ChecksIncomplete=function() return false end
            local row={key='supply:17030',title='Ankh'}
            local function draw(rows) A.rows=rows;A.Draw(rows,'Test',true) end
            for _,position in ipairs({'top','bottom'}) do
                A.db.headerPosition=position
                for _,mode in ipairs({'default','compact','minimal'}) do
                    A.db.rowMode=mode
                    draw({row});A.SetCollapsed(false,'manual')
                    local f=A.frame;local click=f.filterButton:GetScript('OnClick')
                    click();assert(A.filterMenu:IsShown() and not A.db.collapsed)
                    click();assert(not A.filterMenu:IsShown() and not A.db.collapsed)
                    -- Manually inspecting an empty checklist must remain possible.
                    draw({});A.SetCollapsed(false,'manual')
                    click();click();assert(not A.db.collapsed and not A.filterMenu:IsShown())
                    -- A real completion while the menu is open still collapses after closing.
                    draw({row});A.SetCollapsed(false,'manual');click()
                    draw({});assert(not A.db.collapsed and f.collapseAfterFilters)
                    click();assert(A.db.collapsed and not A.filterMenu:IsShown())
                    -- Filter edits are not completion: emptying the list must leave recovery available.
                    draw({row});A.SetCollapsed(false,'manual');click()
                    local refresh=A.Refresh;A.Refresh=function() end
                    A.SetCategory('supplies',nil,false);A.Refresh=refresh
                    draw({});click();assert(not A.db.collapsed and not f.collapseAfterFilters)
                    A.db.filters.supplies=true
                end
            end
            -- A pending genuine completion is cancelled if new work appears.
            draw({row});A.SetCollapsed(false,'manual');A.ShowFilters(A.frame.filterButton)
            draw({});assert(A.frame.collapseAfterFilters)
            draw({row});A.CloseFilters();assert(not A.db.collapsed)
            -- Escape/native Hide and outside-click closure share the same safe path.
            draw({});A.SetCollapsed(false,'manual');A.ShowFilters(A.frame.filterButton)
            A.filterMenu:Hide();assert(not A.db.collapsed)
            A.ShowFilters(A.frame.filterButton)
            A.filterMenu.IsMouseOver=function() return false end
            A.frame.filterButton.IsMouseOver=function() return false end
            A.filterMenu:GetScript('OnEvent')(A.filterMenu,'GLOBAL_MOUSE_DOWN')
            assert(not A.filterMenu:IsShown() and not A.db.collapsed)
        ''')
    print('PASS: EN/DE Filter toggle keeps manually opened/filtered-empty windows expanded in every density/header position; genuine completion still collapses, new work cancels it, Escape/outside-click are safe')


if __name__=='__main__':
    run()
