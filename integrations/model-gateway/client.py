"""Dependency-free OpenRouter gateway client."""
from __future__ import annotations
import json, os, urllib.error, urllib.request
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
API_URL="https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL="openrouter/free"
class GatewayError(RuntimeError): """Safe gateway error."""
def load_local_env():
 p=ROOT/".env"
 if not p.exists(): return
 for raw in p.read_text(encoding="utf-8").splitlines():
  line=raw.strip()
  if not line or line.startswith("#") or "=" not in line: continue
  k,v=line.split("=",1); k=k.strip(); v=v.strip().strip('"').strip("'")
  if k and k not in os.environ: os.environ[k]=v
def chat_completion(messages:list[dict[str,Any]],*,model:str|None=None,temperature:float=0.2,max_tokens:int=500)->dict[str,Any]:
 load_local_env(); key=os.getenv("OPENROUTER_API_KEY")
 if not key: raise GatewayError("OPENROUTER_API_KEY is missing. Add it to local .env.")
 payload={"model":model or os.getenv("AI_EMPIRE_MODEL") or DEFAULT_MODEL,"messages":messages,"temperature":temperature,"max_tokens":max_tokens}
 req=urllib.request.Request(API_URL,data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","HTTP-Referer":"https://github.com/Zethii/AI-EMPIRE","X-Title":"AI-EMPIRE"},method="POST")
 try:
  with urllib.request.urlopen(req,timeout=60) as res: data=json.loads(res.read().decode("utf-8"))
 except urllib.error.HTTPError as e:
  try: detail=e.read(1000).decode("utf-8",errors="replace")
  except Exception: detail="No details"
  raise GatewayError(f"OpenRouter HTTP {e.code}: {detail}") from None
 except urllib.error.URLError as e: raise GatewayError(f"Network error: {e.reason}") from None
 except (json.JSONDecodeError,UnicodeDecodeError): raise GatewayError("Gateway returned invalid JSON.") from None
 if not isinstance(data,dict) or not isinstance(data.get("choices"),list) or not data["choices"]: raise GatewayError("Gateway response contained no choices.")
 return data
def extract_message_text(content:Any)->str:
 if isinstance(content,str): return content.strip()
 if isinstance(content,list):
  parts=[]
  for item in content:
   if isinstance(item,str): parts.append(item)
   elif isinstance(item,dict):
    if isinstance(item.get("text"),str): parts.append(item["text"])
    elif item.get("type") in ("text","output_text") and isinstance(item.get("content"),str): parts.append(item["content"])
  return "\n".join(p for p in parts if p.strip()).strip()
 return ""
def message_text(response:dict[str,Any])->str:
 try: content=response["choices"][0]["message"].get("content")
 except (KeyError,IndexError,TypeError,AttributeError): raise GatewayError("Response has no assistant message.") from None
 text=extract_message_text(content)
 if not text: raise GatewayError("Model returned no readable text content (tool-only or multimodal response).")
 return text
def ask(prompt:str,*,model:str|None=None)->str:
 return message_text(chat_completion([{"role":"user","content":prompt}],model=model))
