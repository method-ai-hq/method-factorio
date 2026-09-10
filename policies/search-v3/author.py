"""Author frozen Method v3 policy documents; no gameplay or model calls."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent

RULES = '''Build automatic iron production from the supplied kit. You have one burner-mining-drill, one stone-furnace, one burner-inserter, ten transport-belt and 150 coal. Discover the world with the tools. Build a connected drill → at least one transport belt → inserter → furnace path. Fuel machines with coal. The fixed checker requires at least 5 newly mined iron ore and 5 new iron plates in EACH of three consecutive 1200-tick windows after a 600-tick warmup. No actions are permitted after finish. Game speed is 20 and game time passes while you think. The total trial limit is 300 wall-clock seconds, including launch and checking. There are at most 200 actions, with each batch member and rejected action counted. Do not use harvest, craft, extract, wait, raw code, game administration or any other endpoint.

observe takes {endpoint}. act takes {endpoint, action}, where action is a JSON string. Allowed action objects: {action:"observe"}; {action:"nearest",resource:"iron-ore"}; {action:"move",position:{x,y}}; {action:"place",item,position:{x,y},exact:true,direction:"UP"|"RIGHT"|"DOWN"|"LEFT"}; {action:"insert",item:"coal",quantity:1..100,target:{name,position:{x,y}}}; {action:"entities"}; {action:"pickup",target:{name,position:{x,y}}}; {action:"rotate",target:{name,position:{x,y}},direction:"UP"|"RIGHT"|"DOWN"|"LEFT"}; {action:"finish"}. Use only observed actual positions for placed machines. Placement may not be where you requested; inspect its result. Snapshot data includes machine direction, drop_position, pickup_position, belt connections/contents, mining target and ore remaining, furnace status/products/fuel. Coal insertion is only for fuel. pickup preserves contents. Treat action errors as potentially partial operations: observe before retry. You may batch 1 to 50 allowed operations if the endpoint documents its batch shape. Never fabricate state or claim that your report proves success. Return a concise report with observations, actions and remaining defects. Call finish when ready or unable to improve within the budget.'''

def agent(prompt, model='planner', timeout=220000, requests=50):
    return {'purpose':'Build and inspect automatic production using restricted game tools.',
            'in':{'endpoint':'environment.game'},
            'do':{'kind':'agent','model':model,'prompt':RULES+'\n\n'+prompt,'tools':['observe','act']},
            'out':{'report':{'type':'text','description':'Observed factory state and actions.'}},
            'changes':['environment.game'],'check':{'present':'report'},
            'limits':{'timeout_ms':timeout,'max_agent_turns':requests,'max_model_requests':requests}}

def save(pid, name, hypothesis, steps, result='report', parent=None, files=None):
    document={'format':'method/3','name':name,'goal':'Build a self-running iron production chain within the fixed supplied-kit benchmark.',
              'environment':{'game':{'type':'service','description':'Restricted game action endpoint.'}},'steps':steps,'result':result}
    if files:
        document['files']=files
    path=ROOT/(pid+'.method')
    if path.exists():
        raise RuntimeError('Frozen policy exists: '+str(path))
    path.write_text(json.dumps(document,indent=2)+'\n')
    meta={'id':pid,'parent':parent,'hypothesis':hypothesis,'author':'gpt-6-astra through Codex subscription',
          'authored_at':datetime.now(timezone.utc).isoformat(),'format':'method/3',
          'policy_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'gameplay_feedback_seen':False,
          'files':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files or []}}
    (ROOT/(pid+'.json')).write_text(json.dumps(meta,indent=2)+'\n')

if __name__=='__main__':
    save('p01-initial','Initial Astra Method v3',
         'A single agent can use an explicit observe-build-inspect control loop to create automatic iron production.',
         {'build':agent('Start with one observation and find iron. Decide a compact arrangement from what you see. Work through three checkpoints: a viable mining site, a connected and fueled factory, then live evidence of flow. At each checkpoint inspect only the facts needed for the next decision. Use drop and pickup positions to detect routing errors. Repair a failed connection before extending the factory. When ore and plates both increase without manual transfers, finish. Do not overfill buffers or spend time proving the external verdict.')})
    save('b00-direct-agent','Direct agent baseline',
         'An agent given the objective and tools, without a multi-stage Method policy, provides the matched baseline.',
         {'play':agent('Use the allowed tools to complete the objective. Choose your own approach. Finish when ready.')})
