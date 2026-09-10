-- DRAFT: not live validated and not connected to the playing broker.
-- Operator-only extension. Load after the base reader, with a fixed role list.
-- Do not expose role_states or opponent_state through the player API.
assert(CivTaskRoles and #CivTaskRoles==3,'Expected two starting cities and one target')
local baseReader=CivTaskSnapshot
function CivTaskSnapshot()
  local s=baseReader(); s.task_type='combat'; s.role_states={}
  for _,role in ipairs(CivTaskRoles) do
    local entry={role=role.role,key=role.x..':'..role.y,exists=false}
    for owner=0,63 do if Players[owner] and Players[owner]:IsAlive() then
      for _,c in Players[owner]:GetCities():Members() do
        if c:GetX()==role.x and c:GetY()==role.y then
          entry.exists=true; entry.owner=owner; entry.id=c:GetID()
          entry.original_owner=c:GetOriginalOwner(); entry.transfer_type=c:GetLastTransferType()
          entry.population=c:GetPopulation(); entry.name=Locale.Lookup(c:GetName()); entry.walls={}
          for _,name in ipairs({'BUILDING_WALLS','BUILDING_CASTLE','BUILDING_STAR_FORT'}) do
            local r=GameInfo.Buildings[name]
            if r and c:GetBuildings():HasBuilding(r.Index) then table.insert(entry.walls,name) end
          end
        end
      end
    end end
    table.insert(s.role_states,entry)
  end
  s.combat_transfer_code=CityTransferTypes.BY_COMBAT
  return s
end
