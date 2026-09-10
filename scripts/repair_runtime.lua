-- Additional public observations for repair. No fault labels or oracle plans.
local repair_original_action=science_action
local repair_status_names={}
for name,value in pairs(defines.entity_status) do repair_status_names[value]=name end

function repair_action(req)
  local result=repair_original_action(req)
  if type(req)=='table' and req.action=='observe' and type(result)=='table' then
    local selected={}
    for _,e in ipairs(result.entities) do
      e.status_name=repair_status_names[e.status] or tostring(e.status)
      local include=true
      if req.area then
        local a=req.area
        if type(a)~='table' or type(a.left_top)~='table' or type(a.right_bottom)~='table' or
          type(a.left_top.x)~='number' or type(a.left_top.y)~='number' or
          type(a.right_bottom.x)~='number' or type(a.right_bottom.y)~='number' then
          storage.science.audit.violations=storage.science.audit.violations+1
          error('area needs left_top and right_bottom points')
        end
        include=e.position.x>=a.left_top.x and e.position.x<=a.right_bottom.x
          and e.position.y>=a.left_top.y and e.position.y<=a.right_bottom.y
      end
      if include then table.insert(selected,e) end
    end
    result.entities=selected
  end
  return result
end
