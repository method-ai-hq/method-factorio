-- Read-only full-precision state. No repair, selection, or game mutation.
function CivTaskJSON(value)
  local t=type(value)
  if t=='number' then assert(value==value and math.abs(value)<math.huge,'non-finite number'); return string.format('%.17g',value) end
  if t=='boolean' then return value and 'true' or 'false' end
  if t=='string' then return '"'..value:gsub('[%z\1-\31\\"]',function(c) if c=='"' then return '\\"' elseif c=='\\' then return '\\\\' else return string.format('\\u%04x',string.byte(c)) end end)..'"' end
  assert(t=='table','Unsupported or missing value: '..t)
  local keys={}; for k in pairs(value) do table.insert(keys,k) end
  table.sort(keys,function(a,b) return tostring(a)<tostring(b) end)
  local array=(#keys==#value)
  local out={}
  if array then for i=1,#value do out[i]=CivTaskJSON(value[i]) end; return '['..table.concat(out,',')..']' end
  for _,k in ipairs(keys) do table.insert(out,CivTaskJSON(tostring(k))..':'..CivTaskJSON(value[k])) end
  return '{'..table.concat(out,',')..'}'
end
function CivTaskSnapshot()
  local id=Game.GetLocalPlayer(); assert(id>=0,'No human player')
  local p=Players[id]; local tr=p:GetTreasury()
  local result={schema='civ6-state/1',player=id,turn=Game.GetCurrentGameTurn(),
    ruleset=GameConfiguration.GetRuleSet(),speed=GameConfiguration.GetGameSpeedType(),
    cost_multiplier=GameInfo.GameSpeeds[GameConfiguration.GetGameSpeedType()].CostMultiplier,
    civilization=PlayerConfigurations[id]:GetCivilizationTypeName(),
    leader=PlayerConfigurations[id]:GetLeaderTypeName(),
    gold=tr:GetGoldBalance(),net_gold=tr:GetGoldYield()-tr:GetTotalMaintenance(),
    science=p:GetTechs():GetScienceYield(),culture=p:GetCulture():GetCultureYield(),
    cities={},units={},technologies={},civics={},players={},research_progress={},civic_progress={},policies={},
    era=p:GetEra(),government=p:GetCulture():GetCurrentGovernment(),
    active_mods={},gathering_storm_loaded=(GameInfo.Buildings['BUILDING_COAL_POWER_PLANT']~=nil),
    disaster_intensity=GameConfiguration.GetValue('DISASTER_INTENSITY'),
    multiplayer=GameConfiguration.IsAnyMultiplayer(),
    quick_movement=UserConfiguration.GetValue('QuickMovement'),
    quick_combat=UserConfiguration.GetValue('QuickCombat'),
    auto_end_turn=UserConfiguration.GetValue('AutoEndTurn'),
    tutorial_level=UserConfiguration.TutorialLevel(),
    map_seed=MapConfiguration.GetValue('RANDOM_SEED'),
    game_seed=GameConfiguration.GetValue('GAME_SYNC_RANDOM_SEED'),
    map_script=MapConfiguration.GetScript(),
    no_barbarians=GameConfiguration.GetValue('GAME_NO_BARBARIANS'),
    no_huts=GameConfiguration.GetValue('GAME_NO_GOODY_HUTS'),
    width=select(1,Map.GetGridSize()),height=select(2,Map.GetGridSize())}
  for _,c in p:GetCities():Members() do
    local g=c:GetGrowth(); local buildings={}; local districts={}
    for b in GameInfo.Buildings() do if c:GetBuildings():HasBuilding(b.Index) then table.insert(buildings,{type=b.BuildingType,pillaged=c:GetBuildings():IsPillaged(b.Index)}) end end
    for _,d in c:GetDistricts():Members() do table.insert(districts,{type=GameInfo.Districts[d:GetType()].DistrictType,pillaged=d:IsPillaged(),x=d:GetX(),y=d:GetY()}) end
    local row={id=c:GetID(),key=c:GetX()..':'..c:GetY(),owner=c:GetOwner(),x=c:GetX(),y=c:GetY(),
      population=c:GetPopulation(),food_surplus=g:GetFoodSurplus(),food=g:GetFood(),housing=g:GetHousing(),
      science=c:GetYield(YieldTypes.SCIENCE),production=c:GetYield(YieldTypes.PRODUCTION),
      buildings=buildings,districts=districts,queue_size=c:GetBuildQueue():GetSize(),stored_production={}}
    local q=c:GetBuildQueue()
    for _,entry in ipairs({{GameInfo.Units,q.GetUnitProgress},{GameInfo.Buildings,q.GetBuildingProgress},{GameInfo.Districts,q.GetDistrictProgress},{GameInfo.Projects,q.GetProjectProgress}}) do
      for item in entry[1]() do local progress=entry[2](q,item.Index)
        assert(type(progress)=='number','Missing production value')
        if progress~=0 then table.insert(row.stored_production,{hash=item.Hash,progress=progress}) end
      end
    end
    table.insert(result.cities,row)
  end
  table.sort(result.cities,function(a,b) return a.key<b.key end)
  for _,u in p:GetUnits():Members() do
    table.insert(result.units,{id=u:GetID(),type=GameInfo.Units[u:GetType()].UnitType,x=u:GetX(),y=u:GetY(),moves=u:GetMovesRemaining(),damage=u:GetDamage(),charges=u:GetBuildCharges()})
  end
  table.sort(result.units,function(a,b) return a.id<b.id end)
  for t in GameInfo.Technologies() do
    if p:GetTechs():HasTech(t.Index) then table.insert(result.technologies,t.TechnologyType) end
    local progress=p:GetTechs():GetResearchProgress(t.Index)
    if progress>0 then table.insert(result.research_progress,{type=t.TechnologyType,progress=progress}) end
  end
  for c in GameInfo.Civics() do
    if p:GetCulture():HasCivic(c.Index) then table.insert(result.civics,c.CivicType) end
    local progress=p:GetCulture():GetCulturalProgress(c.Index)
    if progress>0 then table.insert(result.civic_progress,{type=c.CivicType,progress=progress}) end
  end
  for s=0,p:GetCulture():GetNumPolicySlots()-1 do table.insert(result.policies,{slot=s,policy=p:GetCulture():GetSlotPolicy(s)}) end
  table.sort(result.technologies); table.sort(result.civics)
  for _,m in ipairs(Modding.GetActiveMods()) do table.insert(result.active_mods,{id=m.Id,name=m.Name}) end
  table.sort(result.active_mods,function(a,b) return a.id<b.id end)
  for i=0,63 do if Players[i] and Players[i]:IsAlive() then table.insert(result.players,{id=i,major=Players[i]:IsMajor(),human=Players[i]:IsHuman()}) end end
  return result
end
print('CIVTASK|'..CivTaskJSON(CivTaskSnapshot()))
