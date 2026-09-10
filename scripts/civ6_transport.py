"""One-owner FireTuner transport. Never retry an uncertain game command."""
import asyncio
import secrets
from civ6_admin import Connection


class StrictConnection(Connection):
    async def __aenter__(self):
        # FireTuner can briefly stop listening after the prior client closes.
        # Retrying connection establishment cannot replay a game command.
        for attempt in range(20):
            try:
                return await super().__aenter__()
            except ConnectionError:
                if attempt==19: raise
                await asyncio.sleep(.25)

    async def execute(self, code, context='gamecore'):
        from civ_mcp import tuner_client
        from civ_mcp.connection import _parse_output
        g = self.game
        if type(context) is int:
            index=context
        elif context == 'main':
            index = next(i for i, name in g.lua_states.items() if name == 'MainMenu')
        else:
            index = g.ingame_index if context == 'ingame' else g.gamecore_index
        if index is None or not g.is_connected:
            raise ConnectionError('Required game context is unavailable')
        token = 'CIVEND_' + secrets.token_hex(16)
        # pcall gives an explicit outcome for script errors; no stale sentinel can
        # satisfy this request. No automatic reconnect or command replay.
        wrapped = ('local ok,err=pcall(function()\n' + code + '\nend); '
                   'if not ok then print("CIVERR|"..tostring(err)) end; print("' + token + '")')
        async with g._lock:
            await tuner_client.drain_messages(g._reader, timeout=.05)
            await tuner_client.send_message(g._writer, tuner_client.TAG_COMMAND, f'CMD:{index}:{wrapped}')
            lines = []
            async with asyncio.timeout(15):
                while True:
                    msg = await tuner_client.recv_message_timeout(g._reader, timeout=2)
                    if msg is None:
                        continue
                    if msg.payload.startswith('ERR:'):
                        raise RuntimeError(msg.payload)
                    line = _parse_output(msg.payload)
                    if line == token:
                        return lines
                    if line is not None:
                        lines.append(line)
