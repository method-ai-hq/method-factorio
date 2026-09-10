-- Operator-only setup. Run in MainMenu before a game is loaded.
assert(UI.IsInFrontEnd(), 'Refuse to replace a loaded game')
GameConfiguration.SetToDefaults()
-- Base-game calibration profile. Gathering Storm requires a separate save.
GameConfiguration.SetRuleSet('RULESET_STANDARD')
GameConfiguration.SetGameSpeedType('GAMESPEED_ONLINE')
GameConfiguration.SetHandicapType('DIFFICULTY_PRINCE')
MapConfiguration.SetScript('Pangaea.lua')
MapConfiguration.SetMapSize('MAPSIZE_DUEL')
MapConfiguration.SetValue('RANDOM_SEED', 6100910)
GameConfiguration.SetValue('GAME_SYNC_RANDOM_SEED', 6100911)
GameConfiguration.SetValue('CITY_STATE_COUNT', 0)
GameConfiguration.SetValue('GAME_NO_BARBARIANS', true)
GameConfiguration.SetValue('GAME_NO_GOODY_HUTS', true)
GameConfiguration.SetValue('DISASTER_INTENSITY', 0)
GameConfiguration.SetValue('GAME_TURN_LIMIT', 0)
for _,v in ipairs({'VICTORY_CONQUEST','VICTORY_SCIENCE','VICTORY_CULTURE','VICTORY_RELIGIOUS','VICTORY_DIPLOMATIC','VICTORY_SCORE'}) do GameConfiguration.SetValue(v, false) end
GameConfiguration.SetParticipatingPlayerCount(1)
local p=PlayerConfigurations[0]
p:SetLeaderTypeName('LEADER_TRAJAN')
p:SetCivilizationTypeName('CIVILIZATION_ROME')
p:SetSlotStatus(SlotStatus.SS_TAKEN)
for i=1,61 do local other=PlayerConfigurations[i]; if other then other:SetSlotStatus(SlotStatus.SS_CLOSED) end end
UserConfiguration.SetValue('QuickCombat', true)
UserConfiguration.SetValue('QuickMovement', true)
UserConfiguration.SetValue('AutoEndTurn', false)
UserConfiguration.SetValue('TutorialLevel', -1)
print('START_CONFIG|'..GameConfiguration.GetRuleSet()..'|'..GameConfiguration.GetGameSpeedType()..'|'..tostring(GameConfiguration.GetParticipatingPlayerCount()))
Network.HostGame(ServerType.SERVER_TYPE_NONE)
