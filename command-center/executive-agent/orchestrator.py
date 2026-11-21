#!/usr/bin/env python3
"""Planning-only AI-EMPIRE orchestrator."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"integrations"/"model-gateway"))
from client import GatewayError,chat_completion,message_text
sys.path.insert(0,str(ROOT/"command-center"/"task-manager"))
from task_store import save_plan
SYSTEM="""You are AI-EMPIRE's planning assistant. Return ONLY a JSON object with keys task_title, goal, assumptions (array), steps (3-7 items), risks (array), requires_human_approval (boolean). Each step has step_id, title, description, suggested_agent, depends_on (array), approval_required (boolean). Mark approval for sending/contacting/outreach/interviews/distributing surveys, posting/publishing/uploading, purchases/payments, deleting, exposing private data, or production changes. Research and drafting alone need no approval. If any step needs approval set the task flag true. Plans are proposals, never completed work."""
TERMS=("publish","publishing","post ","posting","upload","send ","sending","email","contact ","contacting","outreach","distribut","survey participant","interview participant","invite ","purchase","buy ","spend","payment","delete","remove ","share private","production deploy","deploy to production")
def extract_json(content:Any)->dict:
 text=message_text({"choices":[{"message":{"content":content}}]}).strip()
 if text.startswith("```"):
  lines=text.splitlines()
  if lines and lines[0].strip().startswith("```"): lines=lines[1:]
  if lines and lines[-1].strip()=="```": lines=lines[:-1]
  text="\n".join(lines).strip()
 start,end=text.find("{"),text.rfind("}")
 if start<0 or end<start: raise ValueError("Model response did not contain JSON.")
 try: result=json.loads(text[start:end+1])
 except json.JSONDecodeError as e: raise ValueError(f"Invalid JSON at character {e.pos}: {e.msg}") from None
 if not isinstance(result,dict): raise ValueError("Plan JSON must be an object.")
 return result
def validate_plan(p:dict)->None:
 for field in ("task_title","goal","steps","requires_human_approval"):
  if field not in p: raise ValueError(f"Missing plan field: {field}")
 steps=p["steps"]
 if not isinstance(steps,list) or not 3<=len(steps)<=7: raise ValueError("Plan must have 3-7 steps.")
 ids=set(); needs=False
 for idx,s in enumerate(steps,1):
  if not isinstance(s,dict): raise ValueError(f"Step {idx} must be an object.")
  for f in ("step_id","title","description","suggested_agent","depends_on","approval_required"):
   if f not in s: raise ValueError(f"Step {idx} missing {f}")
  if not isinstance(s["step_id"],str) or s["step_id"] in ids: raise ValueError(f"Duplicate/invalid step ID in step {idx}")
  ids.add(s["step_id"])
  if not isinstance(s["depends_on"],list) or not isinstance(s["approval_required"],bool): raise ValueError(f"Invalid step fields in {s['step_id']}")
  if any(x not in ids and x not in [later["step_id"] for later in steps] for x in s["depends_on"]): raise ValueError(f"Unknown dependency in {s['step_id']}")
  action=(s["title"]+" "+s["description"]).lower()
  if any(t in action for t in TERMS): s["approval_required"]=True
  needs |= s["approval_required"]
 if not isinstance(p["requires_human_approval"],bool): raise ValueError("Task approval flag must be boolean.")
 p["requires_human_approval"]=p["requires_human_approval"] or needs
def create_plan(request:str,model:str|None=None)->dict:
 response=chat_completion([{"role":"system","content":SYSTEM},{"role":"user","content":request}],model=model,temperature=0.1,max_tokens=1600)
 plan=extract_json(response["choices"][0]["message"].get("content"));validate_plan(plan)
 plan["status"]="PLANNED";plan["execution_enabled"]=False
 return plan
def main():
 ap=argparse.ArgumentParser(description="Create a task plan proposal.")
 ap.add_argument("request");ap.add_argument("--save",action="store_true");ap.add_argument("--model")
 a=ap.parse_args()
 if not a.request.strip(): ap.error("Request cannot be empty.")
 try:
  p=create_plan(a.request.strip(),a.model)
  if a.save: p["saved_to"]=str(save_plan(p,a.request.strip()).relative_to(ROOT))
 except (GatewayError,ValueError,OSError) as e:
  print("Plan failed: "+str(e),file=sys.stderr);raise SystemExit(1)
 print(json.dumps(p,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
