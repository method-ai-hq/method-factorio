-- DRAFT: not live validated and not connected to the playing broker.
-- Operator-only setup for a fresh two-player world. No trial may call this.
-- CivTaskCombatSetup provides four city tiles and nine unit tiles.
local setup=CivTaskCombatSetup
assert(setup and #setup.cities==4 and #setup.units==9,'Incomplete combat setup')
assert(Game.GetCurrentGameTurn()==1 and Game.GetLocalPlayer()==0,'Fresh turn-one game required')
for owner=0,1 do assert(Players[owner] and Players[owner]:GetCities():GetCount()==0,'Player already has cities') end
for i,r in ipairs(setup.cities) do
  assert(r.owner==0 or r.owner==1,'Unknown owner')
  local plot=Map.GetPlot(r.x,r.y)
  assert(plot and not plot:IsWater() and not plot:IsMountain(),'Invalid city terrain')
  for j=1,i-1 do local previous=setup.cities[j]
    assert(Map.GetPlotDistance(r.x,r.y,previous.x,previous.y)>=4,'Cities too close')
  end
end
-- Create cities before removing supplied Settlers, so neither player is
-- eliminated while the fixed kit is being installed.
for _,r in ipairs(setup.cities) do
  local c=Players[r.owner]:GetCities():Create(r.x,r.y)
  assert(c,'City creation failed'); c:ChangePopulation(4-c:GetPopulation())
  print('CITY|'..r.owner..'|'..c:GetID()..'|'..r.x..'|'..r.y)
end
for owner=0,1 do
  local p=Players[owner]; local remove={}
  for _,u in p:GetUnits():Members() do table.insert(remove,u) end
  for _,u in ipairs(remove) do p:GetUnits():Destroy(u) end
  p:GetTreasury():ChangeGoldBalance(50-p:GetTreasury():GetGoldBalance())
  for _,name in ipairs({'TECH_MINING','TECH_POTTERY','TECH_ANIMAL_HUSBANDRY'}) do
    local tech=GameInfo.Technologies[name].Index
    p:GetTechs():SetResearchProgress(tech,p:GetTechs():GetResearchCost(tech))
  end
end
local archery=GameInfo.Technologies.TECH_ARCHERY.Index
Players[1]:GetTechs():SetResearchProgress(archery,Players[1]:GetTechs():GetResearchCost(archery))
for _,r in ipairs(setup.units) do
  assert(r.owner==0 or r.owner==1,'Unknown unit owner')
  local u=UnitManager.InitUnit(r.owner,r.type,r.x,r.y)
  assert(u,'Unit creation failed')
end
Players[0]:GetDiplomacy():SetHasMet(1)
Players[1]:GetDiplomacy():SetHasMet(0)
Players[0]:GetDiplomacy():DeclareWarOn(1,WarTypes.FORMAL_WAR,true)
print('COMBAT_KIT_PREPARED_SAVE_AND_RELOAD_REQUIRED')
