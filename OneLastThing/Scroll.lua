local _,A=...
A.scrolls=setmetatable({},{__mode='k'})
function A.UpdateScroll(scroll)
    local content=scroll.pitContent
    if not content then return end
    local view=math.max(1,scroll:GetHeight())
    local total=math.max(1,content:GetHeight())
    local maximum=math.max(0,total-view)
    local offset=math.max(0,math.min(maximum,scroll:GetVerticalScroll()))
    if offset~=scroll:GetVerticalScroll() then scroll:SetVerticalScroll(offset) end
    local thumb=scroll.pitThumb
    thumb:SetShown(maximum>0)
    if maximum>0 then
        local height=math.max(18,math.min(view,view*view/total))
        thumb:ClearAllPoints();thumb:SetSize(2,height)
        thumb:SetPoint('TOPRIGHT',scroll,'TOPRIGHT',0,-(view-height)*offset/maximum)
    end
end
function A.AttachScrolling(scroll,content)
    scroll.pitContent=content
    scroll:SetScrollChild(content);scroll:EnableMouseWheel(true)
    scroll.pitThumb=scroll:CreateTexture(nil,'OVERLAY')
    local color=(A.palette or A.ThemePalette(A.db.theme))[2]
    scroll.pitThumb:SetColorTexture(color[1],color[2],color[3],.48);A.scrolls[scroll]=true
    scroll:SetScript('OnMouseWheel',function(self,delta)
        local maximum=math.max(0,content:GetHeight()-self:GetHeight())
        self:SetVerticalScroll(math.max(0,math.min(maximum,self:GetVerticalScroll()-delta*48)))
        A.UpdateScroll(self)
    end)
    scroll:SetScript('OnVerticalScroll',function() A.UpdateScroll(scroll) end)
    scroll:SetScript('OnSizeChanged',function() A.UpdateScroll(scroll) end)
end
