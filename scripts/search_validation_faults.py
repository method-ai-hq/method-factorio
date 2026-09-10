"""Operator-only negative fixtures. Never enabled for scored policies."""
def install_fault(client,case):
    if case=='two_windows':
        client.send_command('/sc script.on_nth_tick(1,function(event) local m=storage.benchmark_measure; if m and event.tick==m.start+3000 then for _,e in pairs(game.surfaces[1].find_entities_filtered{type="mining-drill"}) do e.active=false end end end)')
    elif case=='stored_only':
        client.send_command('/sc local c=storage.agent_characters[1]; for _,e in pairs(c.surface.find_entities_filtered{type="mining-drill"}) do e.active=false end; for _,e in pairs(c.surface.find_entities_filtered{type="furnace"}) do e.get_inventory(defines.inventory.furnace_source).insert{name="iron-ore",count=50} end')
    else:raise ValueError(case)
