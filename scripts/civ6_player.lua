-- Fixed InGame player API. Only the broker can load this file or call Lua.
-- Player fields enter as validated data, never executable text.
local function row(tableName,index,field)
  local r=GameInfo[tableName][index]; return r and r[field] or ''
end
local function city(id)
  local c=Players[Game.GetLocalPlayer()]:GetCities():FindID(id)
  assert(c,'No owned city with that ID'); return c
end
local function unit(id)
  local u=Players[Game.GetLocalPlayer()]:GetUnits():FindID(id)
  assert(u,'No owned unit with that ID'); return u
end
local function visible(x,y)
  local plot=Map.GetPlot(x,y); assert(plot,'Invalid tile')
  assert(PlayersVisibility[Game.GetLocalPlayer()]:IsVisible(plot:GetIndex()),'Target is not visible')
  return plot
end
local function pack(r)
  local t={}
  for _,k in ipairs({'Index','Hash','Name','Description','UnitType','BuildingType','DistrictType','ProjectType','TechnologyType','CivicType','PolicyType','ImprovementType','UnitPromotionType','Cost','Combat','RangedCombat','Range','BaseMoves','Maintenance','StrategicResource','PrereqTech','PrereqCivic','PrereqDistrict','PrereqBuilding','AdvisorType','GovernmentSlotType','Housing','Entertainment','YieldType','YieldChange','TilesRequired','AdjacentTerrain','AdjacentFeature','AdjacentDistrict','AdjacentImprovement','AdjacentRiver','AdjacentSeaResource','AdjacentWonder','ID','Name','Value','PrereqTech','PrereqCivic'}) do
    local v=r[k]; if type(v)=='string' or type(v)=='number' or type(v)=='boolean' then t[k]=v end
  end
  if t.Description then t.description_text=Locale.Lookup(t.Description) end
  return t
end
local function purchaseCity(t)
  local c=Cities.GetPlotPurchaseCity(t:GetX(),t:GetY()); return c and c:GetID() or -1
end
local itemTables={UNIT='Units',BUILDING='Buildings',DISTRICT='Districts',PROJECT='Projects'}
local itemFields={UNIT='UnitType',BUILDING='BuildingType',DISTRICT='DistrictType',PROJECT='ProjectType'}
function CivPlayerTurnStatus()
  local blocking=NotificationManager.GetFirstEndTurnBlocking(Game.GetLocalPlayer()); local name='UNKNOWN'
  for k,v in pairs(EndTurnBlockingTypes) do if v==blocking then name=k end end
  return {turn=Game.GetCurrentGameTurn(),blocking=name,processing=UI.IsProcessingMessages(),sent=UI.HasSentTurnComplete(),can_end=UI.CanEndTurn()}
end
function CivPlayerObserve()
  local me=Game.GetLocalPlayer(); local p=Players[me]; local s=CivTaskSnapshot()
  local result={turn=s.turn,player=me,gold=s.gold,net_gold=s.net_gold,science=s.science,culture=s.culture,
    cities=s.cities,units=s.units,technologies=s.technologies,civics=s.civics,
    research_progress=s.research_progress,civic_progress=s.civic_progress,
    government=s.government,policies={},researching=p:GetTechs():GetResearchingTech(),
    progressing_civic=p:GetCulture():GetProgressingCivic(),width=s.width,height=s.height,turn_status=CivPlayerTurnStatus()}
  for _,r in ipairs(result.cities) do
    local c=city(r.id); local q=c:GetBuildQueue()
    r.name=Locale.Lookup(c:GetName()); r.current_production=q:GetCurrentProductionTypeHash()
    r.turns_left=(r.current_production~=0 and q:GetTurnsLeft(r.current_production) or -1)
  end
  for _,r in ipairs(s.policies) do
    table.insert(result.policies,{slot=r.slot,slot_type=p:GetCulture():GetSlotType(r.slot),
      policy=row('Policies',r.policy,'PolicyType')})
  end
  return result
end
function CivPlayerMap()
  local me=Game.GetLocalPlayer(); local vis=PlayersVisibility[me]; local result={tiles={},units={},cities={}}
  local resources=Players[me]:GetResources()
  for i=0,Map.GetPlotCount()-1 do
    local t=Map.GetPlotByIndex(i)
    if vis:IsRevealed(i) then
      local r={x=t:GetX(),y=t:GetY(),visible=vis:IsVisible(i),terrain=row('Terrains',t:GetTerrainType(),'TerrainType'),
        feature=row('Features',t:GetFeatureType(),'FeatureType'),water=t:IsWater(),mountain=t:IsMountain(),
        hills=t:IsHills(),river=t:IsRiver(),fresh_water=t:IsFreshWater()}
      -- Mutable information is returned only under current sight. This avoids
      -- leaking improvements, ownership, or enemy work in explored fog.
      if r.visible then
        r.owner=t:GetOwner(); r.purchase_city=purchaseCity(t)
        r.improvement=row('Improvements',t:GetImprovementType(),'ImprovementType')
        r.district=row('Districts',t:GetDistrictType(),'DistrictType'); r.yields={}
        for n=0,5 do r.yields[n+1]=t:GetYield(n) end
        local ri=t:GetResourceType(); local rr=GameInfo.Resources[ri]
        if rr and (not rr.PrereqTech or Players[me]:GetTechs():HasTech(GameInfo.Technologies[rr.PrereqTech].Index)) then r.resource=rr.ResourceType end
      else r.feature=nil end
      table.insert(result.tiles,r)
    end
  end
  for owner=0,63 do if Players[owner] and Players[owner]:IsAlive() then
    for _,u in Players[owner]:GetUnits():Members() do
      local t=Map.GetPlot(u:GetX(),u:GetY())
      if t and vis:IsVisible(t:GetIndex()) then table.insert(result.units,{owner=owner,id=u:GetID(),type=row('Units',u:GetType(),'UnitType'),x=u:GetX(),y=u:GetY(),damage=u:GetDamage()}) end
    end
    for _,c in Players[owner]:GetCities():Members() do
      local t=Map.GetPlot(c:GetX(),c:GetY())
      if vis:IsVisible(t:GetIndex()) then table.insert(result.cities,{owner=owner,id=c:GetID(),x=c:GetX(),y=c:GetY(),population=c:GetPopulation(),name=Locale.Lookup(c:GetName())}) end
    end
  end end
  return result
end
function CivPlayerChoices(a)
  local p=Players[Game.GetLocalPlayer()]; local result={technologies={},civics={},policies={}}
  for r in GameInfo.Technologies() do
    if p:GetTechs():CanResearch(r.Index) then table.insert(result.technologies,{type=r.TechnologyType,cost=p:GetTechs():GetResearchCost(r.Index),progress=p:GetTechs():GetResearchProgress(r.Index),description=Locale.Lookup(r.Description or '')}) end
  end
  for r in GameInfo.Civics() do
    if p:GetCulture():CanProgress(r.Index) then table.insert(result.civics,{type=r.CivicType,cost=p:GetCulture():GetCultureCost(r.Index),progress=p:GetCulture():GetCulturalProgress(r.Index),description=Locale.Lookup(r.Description or '')}) end
  end
  for r in GameInfo.Policies() do
    local slots={}; for i=0,p:GetCulture():GetNumPolicySlots()-1 do if p:GetCulture():CanSlotPolicy(r.Index,i) then table.insert(slots,i) end end
    if #slots>0 then table.insert(result.policies,{type=r.PolicyType,slots=slots,description=Locale.Lookup(r.Description)}) end
  end
  if a.city_id then
    local c=city(a.city_id); local q=c:GetBuildQueue(); result.production={}
    for kind,tableName in pairs(itemTables) do for r in GameInfo[tableName]() do
      if q:CanProduce(r.Hash,true) then
        local entry={type=r[itemFields[kind]],kind=kind,hash=r.Hash,base_cost=r.Cost,turns=q:GetTurnsLeft(r.Hash),description=Locale.Lookup(r.Description or ''),placements={}}
        if kind=='DISTRICT' or r.IsWonder then
          for i=0,Map.GetPlotCount()-1 do local t=Map.GetPlotByIndex(i)
            if t:GetOwner()==Game.GetLocalPlayer() and purchaseCity(t)==c:GetID() then
              local params={[CityOperationTypes['PARAM_'..kind..'_TYPE']]=r.Hash,[CityOperationTypes.PARAM_X]=t:GetX(),[CityOperationTypes.PARAM_Y]=t:GetY()}
              if CityManager.CanStartOperation(c,CityOperationTypes.BUILD,params,true) then table.insert(entry.placements,{x=t:GetX(),y=t:GetY()}) end
            end
          end
        end
        table.insert(result.production,entry)
      end
    end end
  end
  if a.unit_id then
    local u=unit(a.unit_id); result.improvements={}
    for r in GameInfo.Improvements() do
      local params={[UnitOperationTypes.PARAM_X]=u:GetX(),[UnitOperationTypes.PARAM_Y]=u:GetY(),[UnitOperationTypes.PARAM_IMPROVEMENT_TYPE]=r.Hash}
      if UnitManager.CanStartOperation(u,UnitOperationTypes.BUILD_IMPROVEMENT,nil,params) then table.insert(result.improvements,r.ImprovementType) end
    end
  end
  return result
end
function CivPlayerAction(a)
  local me=Game.GetLocalPlayer(); local p=Players[me]
  if a.action=='observe' then return CivPlayerObserve() end
  if a.action=='map' then return CivPlayerMap() end
  if a.action=='choices' then return CivPlayerChoices(a) end
  if a.action=='rules' then
    local out={}; for r in GameInfo[a.table]() do
      if not a.type or r[a.table=='Technologies' and 'TechnologyType' or a.table=='Civics' and 'CivicType' or a.table=='Policies' and 'PolicyType' or a.table=='Improvements' and 'ImprovementType' or a.table=='Units' and 'UnitType' or a.table=='Buildings' and 'BuildingType' or a.table=='Districts' and 'DistrictType' or 'ProjectType']==a.type then table.insert(out,pack(r)) end
    end; return out
  end
  if a.action=='research' or a.action=='civic' then
    local tech=a.action=='research'; local r=GameInfo[tech and 'Technologies' or 'Civics'][a.type]; assert(r,'Unknown research')
    assert(tech and p:GetTechs():CanResearch(r.Index) or not tech and p:GetCulture():CanProgress(r.Index),'Research is not available')
    UI.RequestPlayerOperation(me,tech and PlayerOperations.RESEARCH or PlayerOperations.PROGRESS_CIVIC,{[tech and PlayerOperations.PARAM_TECH_TYPE or PlayerOperations.PARAM_CIVIC_TYPE]=r.Index})
  elseif a.action=='production' or a.action=='purchase' then
    local c=city(a.city_id); local r=GameInfo[itemTables[a.kind]][a.type]; assert(r,'Unknown item')
    local purchase=a.action=='purchase'; local types=purchase and CityCommandTypes or CityOperationTypes
    local params={[types['PARAM_'..a.kind..'_TYPE']]=r.Hash}
    if a.x then visible(a.x,a.y); params[types.PARAM_X]=a.x; params[types.PARAM_Y]=a.y end
    if purchase then
      params[types.PARAM_YIELD_TYPE]=GameInfo.Yields.YIELD_GOLD.Index
      if a.kind=='UNIT' then params[types.PARAM_MILITARY_FORMATION_TYPE]=MilitaryFormationTypes.STANDARD_MILITARY_FORMATION end
      assert(CityManager.CanStartCommand(c,types.PURCHASE,false,params,true),'Cannot purchase item')
      CityManager.RequestCommand(c,types.PURCHASE,params)
    else
      assert(CityManager.CanStartOperation(c,types.BUILD,params,true),'Cannot produce item here')
      params[types.PARAM_INSERT_MODE]=types.VALUE_EXCLUSIVE
      CityManager.RequestOperation(c,types.BUILD,params)
    end
  elseif a.action=='policies' then
    local clear={}; local add={}; local cu=p:GetCulture()
    for _,assignment in ipairs(a.assignments) do
      local r=GameInfo.Policies[assignment.type]; assert(r,'Unknown policy')
      assert(cu:CanSlotPolicy(r.Index,assignment.slot) or cu:GetSlotPolicy(assignment.slot)==r.Index,'Cannot slot policy')
      table.insert(clear,assignment.slot); add[assignment.slot]=r.Hash
    end
    UI.RequestPlayerOperation(me,PlayerOperations.UNLOCK_POLICIES,{})
    cu:RequestPolicyChanges(clear,add)
  elseif a.action=='focus' then
    local c=city(a.city_id); local r=GameInfo.Yields[a.type]; assert(r,'Unknown yield')
    CityManager.RequestCommand(c,CityCommandTypes.SET_FOCUS,{[CityCommandTypes.PARAM_YIELD_TYPE]=r.Index,[CityCommandTypes.PARAM_FLAGS]=1})
  elseif a.action=='buy_tile' then
    local c=city(a.city_id); visible(a.x,a.y)
    local params={[CityCommandTypes.PARAM_X]=a.x,[CityCommandTypes.PARAM_Y]=a.y}
    assert(CityManager.CanStartCommand(c,CityCommandTypes.PURCHASE_PLOT,false,params,true),'Cannot buy tile')
    CityManager.RequestCommand(c,CityCommandTypes.PURCHASE_PLOT,params)
  elseif a.action=='unit_command' then
    local u=unit(a.unit_id); local params={}; local command=UnitCommandTypes[a.command]
    assert(command,'Unknown unit command')
    if a.type then local r=GameInfo.UnitPromotions[a.type]; assert(r,'Unknown promotion'); params[UnitCommandTypes.PARAM_PROMOTION_TYPE]=r.Hash end
    assert(UnitManager.CanStartCommand(u,command,nil,params),'Command not available')
    UnitManager.RequestCommand(u,command,params)
  else
    local u=unit(a.unit_id); local params={}; local op
    if a.action=='move' or a.action=='attack' then
      local t=Map.GetPlot(a.x,a.y); assert(t,'Invalid tile')
      -- Moving into unexplored tiles is allowed. Attacks require current sight.
      if a.action=='attack' then visible(a.x,a.y) end
      params[UnitOperationTypes.PARAM_X]=a.x; params[UnitOperationTypes.PARAM_Y]=a.y
      if a.action=='attack' and GameInfo.Units[u:GetType()].Range>0 then op=UnitOperationTypes.RANGE_ATTACK
      else op=UnitOperationTypes.MOVE_TO; if a.action=='attack' then params[UnitOperationTypes.PARAM_MODIFIERS]=UnitOperationMoveModifiers.ATTACK end end
    elseif a.action=='found' then op=UnitOperationTypes.FOUND_CITY; params[UnitOperationTypes.PARAM_X]=u:GetX();params[UnitOperationTypes.PARAM_Y]=u:GetY()
    elseif a.action=='improve' then
      local r=GameInfo.Improvements[a.type]; assert(r,'Unknown improvement'); op=UnitOperationTypes.BUILD_IMPROVEMENT
      params[UnitOperationTypes.PARAM_X]=u:GetX();params[UnitOperationTypes.PARAM_Y]=u:GetY();params[UnitOperationTypes.PARAM_IMPROVEMENT_TYPE]=r.Hash
    else
      local ops={skip='SKIP_TURN',fortify='FORTIFY',heal='HEAL',remove_feature='REMOVE_FEATURE',harvest='HARVEST_RESOURCE',repair='REPAIR'}
      local r=GameInfo.UnitOperations['UNITOPERATION_'..ops[a.action]]; assert(r,'Unknown unit operation');op=r.Hash
      params[UnitOperationTypes.PARAM_X]=u:GetX();params[UnitOperationTypes.PARAM_Y]=u:GetY()
    end
    assert(UnitManager.CanStartOperation(u,op,nil,params),'Unit operation not available')
    UnitManager.RequestOperation(u,op,params)
  end
  return {submitted=true}
end
print('PLAYER_API_READY')
