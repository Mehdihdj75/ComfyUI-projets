#!/usr/bin/env python3
"""
runcomfy_submit.py — Soumet un job à un déploiement RunComfy SERVERLESS,
poll le statut, et affiche/télécharge les sorties (images/vidéos).

Flux RunComfy serverless (API v2) :
  POST   https://api.runcomfy.net/prod/v2/deployments/{id}/inference
  GET    .../requests/{request_id}/status
  GET    .../requests/{request_id}/result        (URLs valides 7 jours)
Auth : header  Authorization: Bearer <RUNCOMFY_API_TOKEN>

⚠️ Différent de l'API ComfyUI native (/prompt) : ici on envoie des `overrides`
(ou un `workflow_api_json`) sur un workflow DÉJÀ déployé sur RunComfy.

Usage :
  export RUNCOMFY_API_TOKEN=...        # depuis .env
  python runcomfy_submit.py <deployment_id> \
      --set 6.inputs.text="cinematic product shot" \
      --set 3.inputs.seed=42 \
      --out ./outputs

Dépendances : aucune (stdlib).
"""
import argparse
import json
import os
import sys
import time
import urllib.request

BASE = "https://api.runcomfy.net/prod/v2"
TOKEN = os.environ.get("RUNCOMFY_API_TOKEN") or os.environ.get("COMFYUI_API_KEY", "")


def _req(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def build_overrides(pairs):
    """pairs: 'nodeId.inputs.key=value' -> dict imbriqué {nodeId:{inputs:{key:val}}}."""
    overrides = {}
    for p in pairs:
        path, _, raw = p.partition("=")
        keys = path.split(".")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
        ref = overrides
        for k in keys[:-1]:
            ref = ref.setdefault(k, {})
        ref[keys[-1]] = value
    return overrides


def main():
    if not TOKEN:
        sys.exit("RUNCOMFY_API_TOKEN manquant (source ton .env).")
    ap = argparse.ArgumentParser()
    ap.add_argument("deployment_id")
    ap.add_argument("--set", action="append", default=[], dest="overrides",
                    help="Override : nodeId.inputs.key=value (répétable)")
    ap.add_argument("--workflow", help="Optionnel : workflow_api.json complet à exécuter")
    ap.add_argument("--out", default="./outputs")
    ap.add_argument("--poll", type=float, default=5.0, help="Intervalle de polling (s)")
    args = ap.parse_args()

    dep = f"{BASE}/deployments/{args.deployment_id}"
    body = {}
    if args.workflow:
        with open(args.workflow) as f:
            body["workflow_api_json"] = json.load(f)
    if args.overrides:
        body["overrides"] = build_overrides(args.overrides)

    print(f"→ Soumission au déploiement {args.deployment_id}")
    sub = _req("POST", f"{dep}/inference", body)
    request_id = sub.get("request_id") or sub.get("id")
    print(f"  request_id = {request_id}")

    while True:
        st = _req("GET", f"{dep}/requests/{request_id}/status")
        status = st.get("status", "")
        print(f"  statut : {status}")
        if status in ("completed", "success", "succeeded"):
            break
        if status in ("failed", "error", "cancelled"):
            sys.exit(f"Échec : {json.dumps(st)}")
        time.sleep(args.poll)

    result = _req("GET", f"{dep}/requests/{request_id}/result")
    print("--- Résultat ---")
    print(json.dumps(result, indent=2)[:2000])

    # Télécharge les URLs de sortie si présentes
    os.makedirs(args.out, exist_ok=True)
    urls = []

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str) and o.startswith("http"):
            urls.append(o)

    walk(result)
    for u in urls:
        name = u.split("?")[0].split("/")[-1] or "output"
        dest = os.path.join(args.out, name)
        urllib.request.urlretrieve(u, dest)
        print(f"  ✓ {dest}")
    print(f"Terminé : {len(urls)} fichier(s).")


if __name__ == "__main__":
    main()
