-- Operator-only InGame monitor. Requires civ6_snapshot.lua first.
-- Keep these globals and FireTuner outside the playing interface.
assert(CivTaskMonitor==nil,'Monitor already installed: do not reset a trial')
CivTaskMonitor={events={},sequence=0,identities={}}
local m=CivTaskMonitor
local function push(kind,extra)
  m.sequence=m.sequence+1
  extra=extra or {}; extra.kind=kind; extra.engine_sequence=m.sequence
  table.insert(m.events,extra)
end
for _,c in ipairs(CivTaskSnapshot().cities) do m.identities[c.owner..':'..c.id]=c.key end
function CivTaskCheckpoint(kind)
  push(kind,{state=CivTaskSnapshot()})
end
Events.CityInitialized.Add(function(owner,id)
  if owner~=Game.GetLocalPlayer() then return end
  local c=Players[owner]:GetCities():FindID(id)
  assert(c,'Initialized city is missing')
  local key=c:GetX()..':'..c:GetY(); m.identities[owner..':'..id]=key
  push('founded',{owner=owner,id=id,key=key})
end)
Events.CityRemovedFromMap.Add(function(owner,id)
  if owner~=Game.GetLocalPlayer() then return end
  local identity=owner..':'..id; local key=m.identities[identity]
  assert(key,'Removed city has no known identity')
  push('removed',{owner=owner,id=id,key=key}); m.identities[identity]=nil
end)
Events.PlayerTurnActivated.Add(function(owner,first)
  if owner==Game.GetLocalPlayer() and first then CivTaskCheckpoint('boundary') end
end)
function CivTaskDrain()
  print('CIVMON|'..CivTaskJSON(m.events)); m.events={}
end
print('MONITOR_INSTALLED')
