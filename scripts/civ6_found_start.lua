-- Operator-only first action in the new calibration world, InGame context.
local p=Players[Game.GetLocalPlayer()]
assert(p:GetCities():GetCount()==0,'Refuse to found another setup capital')
local settler=nil
for _,u in p:GetUnits():Members() do if GameInfo.Units[u:GetType()].UnitType=='UNIT_SETTLER' then assert(settler==nil); settler=u end end
assert(settler and UnitManager.CanStartOperation(settler,UnitOperationTypes.FOUND_CITY,nil,true),'No legal starting Settler')
local params={};params[UnitOperationTypes.PARAM_X]=settler:GetX();params[UnitOperationTypes.PARAM_Y]=settler:GetY()
UnitManager.RequestOperation(settler,UnitOperationTypes.FOUND_CITY,params)
print('CAPITAL_FOUNDING_REQUESTED')
