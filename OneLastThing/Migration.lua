local _,A=...
-- The previous addon name exists only in this one-time import boundary.
local function copy(value,seen)
    if type(value)~='table' then return value end
    seen=seen or {};if seen[value] then return seen[value] end
    local result={};seen[value]=result
    for key,item in pairs(value) do
        if type(key)=='string' or type(key)=='number' then result[key]=copy(item,seen) end
    end
    return result
end
function A.ImportLegacySettings()
    if type(OneLastThingDB)=='table' then return end
    local previous=rawget(_G,'PitStopDB')
    if type(previous)~='table' then
        local metadata=(C_AddOns and C_AddOns.GetAddOnMetadata) or GetAddOnMetadata
        local load=(C_AddOns and C_AddOns.LoadAddOn) or LoadAddOn
        -- Never load an arbitrary older full addon. Only our inert migration stub.
        if A.Safe('legacy migration marker',metadata,'PitStop','X-OneLastThing-Migration')=='1' then
            A.Safe('legacy settings import',load,'PitStop')
            previous=rawget(_G,'PitStopDB')
        end
    end
    if type(previous)=='table' then
        OneLastThingDB=copy(previous)
        OneLastThingDB.legacySettingsImported=true
    end
end
