-- Operator-only: run in GameCore_Tuner AFTER founding the supplied Settler.
-- Refuse an advanced, populated, or already prepared world. Then save/reload:
-- administrative technology changes are not immediately visible in InGame.
local id=Game.GetLocalPlayer(); assert(id==0)
local p=Players[id]; assert(Game.GetCurrentGameTurn()==1)
local count=0; local capital=nil
for _,c in p:GetCities():Members() do count=count+1; capital=c end
assert(count==1 and capital:GetPopulation()==1,'Expected one fresh capital')
local units=0
for _,u in p:GetUnits():Members() do if not u:IsDelayedDeath() then units=units+1; assert(GameInfo.Units[u:GetType()].UnitType=='UNIT_WARRIOR') end end
assert(units==1,'Expected only the initial Warrior')
capital:ChangePopulation(3)
p:GetTreasury():ChangeGoldBalance(50-p:GetTreasury():GetGoldBalance())
for _,name in ipairs({'TECH_MINING','TECH_POTTERY','TECH_ANIMAL_HUSBANDRY'}) do
  local tech=GameInfo.Technologies[name].Index
  p:GetTechs():SetResearchProgress(tech,p:GetTechs():GetResearchCost(tech))
end
UnitManager.InitUnit(id,'UNIT_SCOUT',capital:GetX(),capital:GetY())
UnitManager.InitUnit(id,'UNIT_BUILDER',capital:GetX(),capital:GetY())
print('KIT_PREPARED_SAVE_AND_RELOAD_REQUIRED')
