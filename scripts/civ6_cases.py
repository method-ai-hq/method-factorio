"""Operator tools for creating, inspecting, and freezing Civ calibration saves."""
import argparse
import asyncio
import json
from pathlib import Path
from civ6_admin import DEFAULT_SAVES,sha256
from civ6_transport import StrictConnection
from civ6_broker import ROOT,lua,response
from civ6_verify import check_start,canonical,digest


async def execute(conn,code,context):
    lines=await conn.execute(code,context)
    if any(line.startswith('CIVERR|') for line in lines):
        raise RuntimeError(str(lines))
    return lines


async def run(args):
    if args.action=='new':
        async with StrictConnection() as conn:
            if conn.game.ingame_index is not None:
                await execute(conn,'Events.ExitToMainMenu()','ingame')
        await asyncio.sleep(.5)
        async with StrictConnection() as conn:
            if 'MainMenu' not in conn.game.lua_states.values():
                raise RuntimeError('Main menu is not ready; no new-game command was sent')
            config={'map_seed':args.seed,'game_seed':args.seed+1}
            code='CivTaskSetup='+lua(config)+'\n'
            if args.combat:code+='CivTaskSetup.combat=true\n'
            code+=(ROOT/'civ6_new_game.lua').read_text()
            print(await execute(conn,code,'main'))
        print('Close the leader load screen before the next operation.');return
    async with StrictConnection() as conn:
        if args.action=='prepare':
            if not args.save:raise ValueError('Save name required')
            print(await execute(conn,(ROOT/'civ6_found_start.lua').read_text(),'ingame'))
            await asyncio.sleep(.4)
            print(await execute(conn,(ROOT/'civ6_prepare.lua').read_text(),'gamecore'))
            await asyncio.sleep(.4)
            save=await conn.save(args.save)
            print(json.dumps(save,indent=2))
            await conn.load(args.save)
            print('Close the leader load screen, then freeze the starting profile.');return
        state=await conn.snapshot()
        if args.action=='freeze':
            if not args.save or not args.output or not args.family:raise ValueError('Save, output, and family required')
            check_start(state)
            if state['ruleset']!='RULESET_STANDARD' or state['gathering_storm_loaded']:
                raise ValueError('Wrong rule set')
            original=json.loads((ROOT.parent/'docs/civ6/profiles/economy-nearby-food-1.json').read_text())
            if state['active_mods']!=json.loads((ROOT.parent/'evidence/civ6-economy-setup-2026-09-10/start-state.json').read_text())['active_mods']:
                raise ValueError('Unexpected active mods')
            original.update(id=args.output.stem,map_family=args.family,start_save_name=args.save,
                            start_save_sha256=sha256(DEFAULT_SAVES/(args.save+'.Civ6Save')),start_state_sha256=digest(state))
            args.output.parent.mkdir(parents=True,exist_ok=True)
            with args.output.open('xb') as f:f.write(canonical(original))
            with args.output.with_suffix('.state.json').open('xb') as f:f.write(canonical(state))
            print(json.dumps({'profile':str(args.output),'start_state_sha256':digest(state)},indent=2));return
        if args.action=='map':
            if not args.output:raise ValueError('Output required')
            if state['turn']!=1:raise ValueError('Map design inspection requires turn one')
            code='''local tiles={}
for i=0,Map.GetPlotCount()-1 do
 local t=Map.GetPlotByIndex(i); local terrain=GameInfo.Terrains[t:GetTerrainType()]
 local feature=GameInfo.Features[t:GetFeatureType()];local resource=GameInfo.Resources[t:GetResourceType()]
 table.insert(tiles,{x=t:GetX(),y=t:GetY(),terrain=terrain.TerrainType,
  feature=feature and feature.FeatureType or '',resource=resource and resource.ResourceType or '',
  water=t:IsWater(),mountain=t:IsMountain(),hills=t:IsHills(),river=t:IsRiver(),fresh_water=t:IsFreshWater(),
  food=t:GetYield(0),production=t:GetYield(1)})
end
print('MAP|'..CivTaskJSON(tiles))'''
            tiles=response(await conn.execute(code,'ingame'),'MAP|')
            with args.output.open('xb') as f:f.write(canonical({'state':state,'tiles':tiles}))
            print(json.dumps({'path':str(args.output),'tiles':len(tiles)}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['new','prepare','freeze','map'])
    p.add_argument('--seed',type=int,default=6100920);p.add_argument('--combat',action='store_true')
    p.add_argument('--save');p.add_argument('--output',type=Path);p.add_argument('--family')
    asyncio.run(run(p.parse_args()))
