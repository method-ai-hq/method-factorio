#!/usr/bin/env python3
"""Operator-only Civ 6 connection. Never expose this command to a playing Method."""
from __future__ import annotations
import argparse
import asyncio
import fcntl
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
DEFAULT_MCP = Path.home() / '.local/share/civ6-mcp'
DEFAULT_SAVES = Path.home() / "Library/Application Support/Sid Meier's Civilization VI/Sid Meier's Civilization VI/Saves/Single"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Connection:
    def __init__(self, mcp_dir=DEFAULT_MCP):
        sys.path.insert(0, str(Path(mcp_dir) / 'src'))
        from civ_mcp.connection import GameConnection
        self.game = GameConnection()
        self.lock = None

    async def __aenter__(self):
        path = Path.home() / '.local/share/civ6-task-connection.lock'
        path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = path.open('a')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            await asyncio.wait_for(self.game.connect(), 10)
        except BaseException:
            self.lock.close()
            await self.game.disconnect()
            raise
        return self

    async def __aexit__(self, *args):
        await self.game.disconnect()
        self.lock.close()

    async def execute(self, code, context='gamecore'):
        code += "\nprint('---END---')"
        if context == 'main':
            index = next(i for i, name in self.game.lua_states.items() if name == ('MainMenu' if 'MainMenu' in self.game.lua_states.values() else 'Main State'))
            return await self.game.execute_in_state(index, code)
        if context == 'ingame':
            return await self.game.execute_write(code)
        return await self.game.execute_read(code)

    async def snapshot(self):
        lines = await self.execute((ROOT / 'civ6_snapshot.lua').read_text(), 'ingame')
        rows = [line[8:] for line in lines if line.startswith('CIVTASK|')]
        if len(rows) != 1:
            raise RuntimeError('Expected one complete state snapshot: ' + repr(lines))
        return json.loads(rows[0], parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

    async def save(self, name, directory=DEFAULT_SAVES):
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name):
            raise ValueError('Save name must contain only letters, digits, underscore, or hyphen')
        path = Path(directory) / (name + '.Civ6Save')
        if path.exists():
            raise FileExistsError(path)
        await self.execute('local s={Name=' + json.dumps(name) + ', Location=SaveLocations.LOCAL_STORAGE, Type=SaveTypes.SINGLE_PLAYER, IsAutosave=false, IsQuicksave=false}; Network.SaveGame(s)', 'ingame')
        previous = None
        stable = 0
        for _ in range(60):
            await asyncio.sleep(.25)
            if path.exists() and path.stat().st_size > 100:
                current = (path.stat().st_size, sha256(path))
                stable = stable + 1 if current == previous else 0
                if stable >= 3:
                    return {'path': str(path), 'sha256': current[1], 'bytes': current[0]}
                previous = current
        raise RuntimeError('No stable save file appeared: ' + str(path))

    async def load(self, name):
        path = DEFAULT_SAVES / (name + '.Civ6Save')
        if not path.is_file():
            raise FileNotFoundError(path)
        # The save query provides the engine's full descriptor. Do not guess it.
        code = '''local function results(files, qid)
          UI.CloseFileListQuery(qid); LuaEvents.FileListQueryResults.Remove(results)
          for _,s in ipairs(files) do if s.Name == NAME .. '.Civ6Save' then
            Network.LeaveGame(); Network.LoadGame(s,ServerType.SERVER_TYPE_NONE); return
          end end
        end
        LuaEvents.FileListQueryResults.Add(results)
        UI.QuerySaveGameList(SaveLocations.LOCAL_STORAGE,SaveTypes.SINGLE_PLAYER,
          SaveLocationOptions.NORMAL + SaveLocationOptions.LOAD_METADATA)
        print('LOAD_REQUESTED')'''.replace('NAME', json.dumps(name))
        await self.execute(code, 'ingame')
        return {'requested': name, 'sha256': sha256(path),
                'next': 'Close the load screen, then inspect in a new process.'}


async def run(args):
    async with Connection(args.mcp_dir) as conn:
        start = time.monotonic()
        if args.lua:
            result = await conn.execute(Path(args.lua).read_text(), args.context)
        elif args.save:
            result = await conn.save(args.save)
        elif args.load:
            result = await conn.load(args.load)
        elif args.snapshot:
            result = await conn.snapshot()
        else:
            result = conn.game.lua_states
        output = {'elapsed_seconds': time.monotonic() - start, 'result': result}
        if args.output:
            with Path(args.output).open('x') as out:
                json.dump(output, out, indent=2, allow_nan=False)
                out.write('\n')
        print(json.dumps(output, indent=2, allow_nan=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mcp-dir', type=Path, default=DEFAULT_MCP)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--lua', type=Path)
    group.add_argument('--snapshot', action='store_true')
    group.add_argument('--save')
    group.add_argument('--load')
    parser.add_argument('--context', choices=['main','gamecore','ingame'], default='gamecore')
    parser.add_argument('--output', type=Path)
    asyncio.run(run(parser.parse_args()))
