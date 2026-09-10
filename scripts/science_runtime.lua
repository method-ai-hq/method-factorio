-- Trusted game code. Never expose this file or RCON as a playing action.
function science_snapshot()
  local s=game.surfaces[1]; local f=game.forces.player
  local out={tick=game.tick,speed=game.speed,paused=game.tick_paused,
    always_day=s.always_day,inventory={},entities={},
    produced={},stock={},ore={},ground_items=0}
  for name,count in pairs(storage.science.inventory) do out.inventory[name]=count end
  local function contents(inv)
    local result={}
    if inv then for _,item in pairs(inv.get_contents()) do
      result[item.name]=(result[item.name] or 0)+item.count
    end end
    return result
  end
  local function add(inv)
    for name,count in pairs(contents(inv)) do
      if out.stock[name]~=nil then out.stock[name]=out.stock[name]+count end
    end
  end
  for _,name in ipairs(storage.science.items) do
    out.stock[name]=0
    out.produced[name]=f.get_item_production_statistics(s).get_input_count(name)
  end
  for _,name in ipairs({'iron-ore','copper-ore'}) do
    local total=0
    for _,e in pairs(s.find_entities_filtered{name=name}) do total=total+e.amount end
    out.ore[name]=total
  end
  for _,e in pairs(s.find_entities_filtered{type='item-entity'}) do
    out.ground_items=out.ground_items+e.stack.count
    if out.stock[e.stack.name] then out.stock[e.stack.name]=out.stock[e.stack.name]+e.stack.count end
  end
  for _,e in pairs(s.find_entities_filtered{force=f}) do
    if e.type~='character' then
      local q={id=e.unit_number,name=e.name,type=e.type,position=e.position,direction=e.direction,
        status=e.status,energy=e.energy,box=e.bounding_box,inventories={}}
      for i=1,e.get_max_inventory_index() do
        local inv=e.get_inventory(i)
        if inv then q.inventories[tostring(i)]=contents(inv); add(inv) end
      end
      if e.type=='assembling-machine' or e.type=='furnace' then
        local recipe=e.get_recipe()
        q.recipe=recipe and recipe.name or nil
        if not q.recipe and e.type=='furnace' and e.previous_recipe then
          q.recipe=e.previous_recipe.name
        end
        q.products=e.products_finished; q.progress=e.crafting_progress
      end
      if e.type=='inserter' then
        q.pickup=e.pickup_position; q.drop=e.drop_position
        if e.held_stack.valid_for_read then
          q.held={name=e.held_stack.name,count=e.held_stack.count}
          if out.stock[q.held.name] then out.stock[q.held.name]=out.stock[q.held.name]+q.held.count end
        end
      end
      if e.type=='mining-drill' then q.drop=e.drop_position end
      if e.type=='transport-belt' or e.type=='underground-belt' or e.type=='splitter' then
        q.lines={}
        for i=1,e.get_max_transport_line_index() do
          local line=e.get_transport_line(i); q.lines[i]=contents(line); add(line)
        end
      end
      table.insert(out.entities,q)
    end
  end
  table.sort(out.entities,function(a,b) return a.id<b.id end)
  return out
end

function science_clear_materials()
  local s=game.surfaces[1]
  for _,e in pairs(s.find_entities_filtered{force='player'}) do
    for i=1,e.get_max_inventory_index() do local inv=e.get_inventory(i); if inv then inv.clear() end end
    if e.type=='inserter' then e.held_stack.clear() end
    if e.type=='assembling-machine' or e.type=='furnace' then
      e.crafting_progress=0; e.bonus_progress=0
    end
    if e.type=='transport-belt' or e.type=='underground-belt' or e.type=='splitter' then
      for i=1,e.get_max_transport_line_index() do e.get_transport_line(i).clear() end
    end
  end
  for _,e in pairs(s.find_entities_filtered{type='item-entity'}) do e.destroy() end
end

function science_finish()
  assert(not storage.science.finished,'playing access revoked')
  storage.science.finished=true
  science_clear_materials()
  storage.science.clean=science_snapshot()
  storage.science.measurement={start=game.tick,samples={},done=false}
  script.on_event(defines.events.on_tick,function(event)
    local m=storage.science.measurement; local d=event.tick-m.start
    if d==7200 or d==10800 or d==14400 or d==18000 then
      table.insert(m.samples,science_snapshot())
    end
    if d==18000 then game.tick_paused=true; m.done=true end
  end)
end

function science_action(req)
  local b=storage.science; local s=game.surfaces[1]
  b.audit.actions=b.audit.actions+1
  local function reject(message) b.audit.violations=b.audit.violations+1; error(message) end
  if b.finished then reject('playing access revoked') end
  if b.audit.actions>b.rules.actions then reject('action limit reached') end
  if type(req)~='table' then reject('request must be an object') end
  local op=req.action
  if op=='observe' then
    local names={}
    if req.names~=nil then
      if type(req.names)~='table' then reject('names must be an array of equipment names') end
      for _,name in pairs(req.names) do
        if not b.rules.kit[name] then reject('unknown equipment name') end
        names[name]=true
      end
    else
      for name,_ in pairs(b.rules.kit) do
        if name~='transport-belt' and name~='underground-belt' and name~='splitter'
           and name~='medium-electric-pole' and name~='solar-panel' then names[name]=true end
      end
    end
    local state=science_snapshot(); local selected={}
    for _,e in ipairs(state.entities) do if names[e.name] then table.insert(selected,e) end end
    state.entities=selected; return state
  end
  if op=='finish' then science_finish(); return {finished=true} end
  if op=='recipes' then
    local result={}
    for _,name in ipairs(b.recipes) do
      local r=game.forces.player.recipes[name]
      result[name]={ingredients=r.ingredients,products=r.products,energy=r.energy,category=r.category}
    end
    return result
  end
  if op=='resources' then return b.patches end
  if op~='place' and op~='pickup' and op~='rotate' and op~='recipe' then reject('action not allowed') end
  local pos=req.position
  if type(pos)~='table' or type(pos.x)~='number' or type(pos.y)~='number' or
     pos.x~=pos.x or pos.y~=pos.y or math.abs(pos.x)>120 or math.abs(pos.y)>120 then
    reject('position must be within -120..120')
  end
  local directions={UP=defines.direction.north,RIGHT=defines.direction.east,
                    DOWN=defines.direction.south,LEFT=defines.direction.west}
  if req.direction and not directions[req.direction] then reject('invalid direction') end
  local direction=directions[req.direction or 'UP']
  if op=='place' then
    if not b.rules.kit[req.item] then reject('item not in supplied kit') end
    if (b.inventory[req.item] or 0)<1 then error('no item left') end
    if req.type and req.type~='input' and req.type~='output' then reject('invalid underground type') end
    local spec={name=req.item,position=pos,direction=direction,force='player',type=req.type or 'input'}
    assert(s.can_place_entity(spec),'position blocked')
    local e=s.create_entity(spec); assert(e,'placement failed')
    b.inventory[req.item]=b.inventory[req.item]-1
    return {id=e.unit_number,position=e.position}
  end
  if not b.rules.kit[req.name] then reject('target not in supplied kit') end
  local e=s.find_entity(req.name,pos)
  assert(e and e.force==game.forces.player,'target not found')
  if op=='pickup' then
    -- Recover equipment only. Materials are discarded, never transferred by the player.
    b.inventory[e.name]=(b.inventory[e.name] or 0)+1; e.destroy(); return {picked_up=true}
  end
  if op=='rotate' then e.direction=direction; return {rotated=true} end
  if op=='recipe' then
    if e.type~='assembling-machine' then reject('recipes require an assembler') end
    local allowed=false
    for _,n in ipairs(b.recipes) do if n==req.recipe then allowed=true end end
    if not allowed then reject('recipe not allowed') end
    -- set_recipe returns removed ingredients; discard them rather than granting items.
    e.set_recipe(req.recipe); return {recipe=req.recipe}
  end
end
