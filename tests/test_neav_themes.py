"""Neav palette matching is cosmetic, optional and limited to three colors."""
from test_startup import fresh_client


def run():
    for locale in ('enUS', 'deDE'):
        vm = fresh_client(locale=locale)
        vm.execute('''
            local A=OneLastThing
            local function near(a,b) assert(math.abs(a-b)<.0000001) end
            assert(A.db.theme=='blizzard') -- update never switches existing choices
            A.Draw({{key='theme:neav',title='Test'}},'Test')
            local f=A.frame;local fs=f.settingsButton:GetFontString()
            fs.SetTextColor=function(self,r,g,b) self.rgb={r,g,b} end
            local native={cast={.8,.5,.1},friendly={.1,.6,.3}}
            FlareUI={UnitFrames={Color=function(key) return native[key] end}}
            for _,theme in ipairs({'neavCurrent','neavMoss'}) do
                A.SetTheme(theme);assert(A.db.theme==theme)
                local colors={}
                local probe={SetFont=function() end,SetShadowColor=function() end,SetShadowOffset=function() end,
                    SetTextColor=function(_,r,g,b) colors[string.format('%.6f/%.6f/%.6f',r,g,b)]=true end}
                for role in pairs(A.toneSlots) do A.Font(probe,12,false,role);A.Font(probe,12,true,role) end
                local count=0;for _ in pairs(colors) do count=count+1 end;assert(count==3)
                for i=1,3 do near(fs.rgb[i],A.palette[1][i]) end
                local before=A.palette[1][1];A.AdjustFontSize(5);near(fs.rgb[1],before)
                A.ShowSettings();A.BuildSettings();assert(not next(A.errors))
                A.Init();assert(A.db.theme==theme) -- saved character choice survives initialization
            end
            local p=A.ThemePalette('neavMoss')
            near(p[1][1],225/255)
            near(p[2][2],190/255)
            near(p[3][3],209/255)
            A.SetTheme('neavMoss')
            local roles={}
            local probe={SetFont=function() end,SetShadowColor=function() end,SetShadowOffset=function() end,
                SetTextColor=function(_,r,g,b) roles.current={r,g,b} end}
            for _,role in ipairs({'brand','quests','action','settings'}) do A.Font(probe,12,false,role);roles[role]=roles.current end
            near(roles.brand[2],190/255);near(roles.quests[1],226/255)
            near(roles.action[1],225/255);near(roles.settings[2],184/255)
            p=A.ThemePalette('neavCurrent')
            near(p[1][1],.85);near(p[1][2],.625);near(p[2][3],.475)
            assert(native.cast[1]==.8 and native.friendly[3]==.3,'provider data must stay untouched')
            -- Missing provider, bad palette values and protected values use safe colors.
            FlareUI=nil;p=A.ThemePalette('neavCurrent');near(p[1][1],1);near(p[2][2],.85)
            FlareUI={UnitFrames={Color=function() return {r=.2,g=.4,b=.6} end}}
            p=A.ThemePalette('neavCurrent');near(p[1][1],.4)
            FlareUI.UnitFrames.Color=function() return {1,2,3} end
            p=A.ThemePalette('neavCurrent');near(p[1][1],1)
            FlareUI.UnitFrames.Color=function() return {.2,.4,.6} end
            issecretvalue=function(v) return v==.4 end
            p=A.ThemePalette('neavCurrent');near(p[1][1],1);issecretvalue=nil
            -- Delayed login refresh catches native palette readiness without polling it.
            A.SetTheme('neavCurrent')
            FlareUI.UnitFrames.Color=function() return {.4,.4,.4} end
            event(nil,'PLAYER_LOGIN');timerStep();near(A.palette[1][1],.55)
            A.SetTheme('blizzard');assert(A.palette[1][1]==1 and A.palette[1][2]==.82)
        ''')
    print('PASS: EN/DE Neav Current and Muted Moss themes, source-inspired hues with distinct moss/gold/ivory roles, three-color limit, live settings accent, font/reload persistence, optional provider fallback and readiness refresh')


if __name__ == '__main__':
    run()
