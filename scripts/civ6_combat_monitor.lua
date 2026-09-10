-- DRAFT: not live validated and not connected to the playing broker.
-- Operator-only monitor. Snapshot must include the fixed three city roles.
assert(CivTaskMonitor==nil,'Monitor already installed')
CivTaskMonitor={events={},sequence=0,identities={}}
local m=CivTaskMonitor
local function push(kind,extra)
  m.sequence=m.sequence+1; extra=extra or {}
  extra.kind=kind; extra.engine_sequence=m.sequence
  table.insert(m.events,extra)
end
for _,r in ipairs(CivTaskSnapshot().role_states) do
  assert(r.exists,'Starting role city missing')
  m.identities[r.owner..':'..r.id]={key=r.key,role=r.role}
end
function CivTaskCheckpoint(kind) push(kind,{state=CivTaskSnapshot()}) end
Events.CityAddedToMap.Add(function(owner,id)
  local p=Players[owner]; if not p then return end
  local c=p:GetCities():FindID(id); if not c then return end
  local key=c:GetX()..':'..c:GetY()
  for _,role in ipairs(CivTaskRoles) do if key==role.x..':'..role.y then
    m.identities[owner..':'..id]={key=key,role=role.role}
    push('role_added',{key=key,role=role.role,owner=owner,id=id,
      original_owner=c:GetOriginalOwner(),transfer_type=c:GetLastTransferType()})
  end end
end)
Events.CityRemovedFromMap.Add(function(owner,id)
  local r=m.identities[owner..':'..id]
  if r then
    push('role_removed',{key=r.key,role=r.role,owner=owner,id=id})
    m.identities[owner..':'..id]=nil
  end
end)
Events.PlayerTurnActivated.Add(function(owner,first)
  if owner==Game.GetLocalPlayer() and first then CivTaskCheckpoint('boundary') end
end)
function CivTaskDrain()
  print('CIVMON|'..CivTaskJSON(m.events)); m.events={}
end
print('COMBAT_MONITOR_INSTALLED')
