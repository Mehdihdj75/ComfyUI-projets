#!/usr/bin/env python3
"""
comfy_submit.py — Soumet un workflow ComfyUI (format API) à une instance
locale ou distante, suit l'exécution via WebSocket, et télécharge les sorties
(images ET vidéos).

Pattern officiel ComfyUI (vérifié) :
  POST /prompt  ->  ws://.../ws  ->  GET /history/{id}  ->  GET /view

Usage :
  python comfy_submit.py workflow_api.json \
      --set 6.inputs.text="a cinematic product shot" \
      --set 3.inputs.seed=42 \
      --out ./outputs

Le workflow DOIT être exporté en "API format" depuis ComfyUI
(active le mode dev dans les settings, puis "Save (API Format)").

Dépendances : pip install websocket-client
"""
import argparse
import json
import os
import sys
import uuid
import urllib.parse
import urllib.request

try:
    import websocket  # websocket-client
except ImportError:
    sys.exit("pip install websocket-client")

SERVER = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")
API_KEY = os.environ.get("COMFYUI_API_KEY", "")
CLIENT_ID = str(uuid.uuid4())


def _headers():
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


def _http_host():
    return SERVER.split("://", 1)[-1]


def _ws_scheme():
    return "wss" if SERVER.startswith("https") else "ws"


def queue_prompt(prompt):
    payload = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{SERVER}/prompt", data=data, headers=_headers())
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["prompt_id"]


def get_history(prompt_id):
    req = urllib.request.Request(f"{SERVER}/history/{prompt_id}", headers=_headers())
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_file(filename, subfolder, ftype):
    params = urllib.parse.urlencode(
        {"filename": filename, "subfolder": subfolder, "type": ftype}
    )
    req = urllib.request.Request(f"{SERVER}/view?{params}", headers=_headers())
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def wait_for_completion(prompt_id):
    ws = websocket.WebSocket()
    ws.connect(f"{_ws_scheme()}://{_http_host()}/ws?clientId={CLIENT_ID}")
    try:
        while True:
            out = ws.recv()
            if not isinstance(out, str):
                continue  # frames binaires = previews, on ignore
            msg = json.loads(out)
            if msg.get("type") == "executing":
                d = msg["data"]
                if d.get("node") is None and d.get("prompt_id") == prompt_id:
                    break  # fini
            elif msg.get("type") == "execution_error":
                raise RuntimeError(f"Execution error: {msg['data']}")
    finally:
        ws.close()


def apply_overrides(prompt, overrides):
    """overrides: liste 'nodeId.inputs.key=value' (value auto-typée JSON sinon str)."""
    for ov in overrides:
        path, _, raw = ov.partition("=")
        keys = path.split(".")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
        ref = prompt
        for k in keys[:-1]:
            ref = ref[k]
        ref[keys[-1]] = value
    return prompt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow", help="Fichier workflow exporté en API format")
    ap.add_argument("--set", action="append", default=[], dest="overrides",
                    help="Override : nodeId.inputs.key=value (répétable)")
    ap.add_argument("--out", default="./outputs", help="Dossier de sortie")
    args = ap.parse_args()

    with open(args.workflow) as f:
        prompt = json.load(f)
    prompt = apply_overrides(prompt, args.overrides)

    print(f"→ Soumission sur {SERVER}")
    prompt_id = queue_prompt(prompt)
    print(f"  prompt_id = {prompt_id}")
    wait_for_completion(prompt_id)
    print("  exécution terminée, récupération des sorties…")

    os.makedirs(args.out, exist_ok=True)
    history = get_history(prompt_id)[prompt_id]
    n = 0
    for node_id, node_out in history["outputs"].items():
        for key in ("images", "gifs", "videos", "audio"):
            for item in node_out.get(key, []):
                data = get_file(item["filename"], item.get("subfolder", ""),
                                item.get("type", "output"))
                dest = os.path.join(args.out, item["filename"])
                with open(dest, "wb") as f:
                    f.write(data)
                print(f"  ✓ {dest}")
                n += 1
    print(f"Terminé : {n} fichier(s) dans {args.out}")


if __name__ == "__main__":
    main()
