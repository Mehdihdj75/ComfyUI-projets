# ComfyUI — Setup pilotage par API/MCP + génération vidéo

Capacité transverse pour générer images/vidéos par programmation sur plusieurs
projets (Momentum, QuizFlash, video-ads-pulse360, avatar-ia, claude-video-hyperframe).

**Décisions actées** (15/06/2026) :
- Infra : **Cloud GPU** (RunComfy en premier, RunPod en option coût/volume).
- Usages : social court · produit/marketing · avatars/talking-heads · pilotage Claude Code.
- Pilotage : MCP **`artokun/comfyui-mcp`** en mode remote + node n8n pour la prod.

---

## Architecture

```
Claude Code ──(MCP artokun, remote)──┐
                                     ▼
n8n (pipelines récurrents) ───► ComfyUI sur RunComfy (cloud GPU)
                                     │   + custom nodes (LivePortrait…)
scripts/comfy_submit.py ◄────────────┘   + modèles WAN 2.2 / LTX
```

Aucun MCP ne "génère" lui-même : ils orchestrent une instance ComfyUI + des
modèles à héberger. La vraie décision = **où tourne ComfyUI** (ici : cloud).

---

## Phase 1 — Socle (RunComfy + 1 workflow + MCP)

1. **RunComfy** : créer un compte, lancer une machine ComfyUI interactive.
2. Charger un template **WAN 2.2 I2V** (`Workflow → Browse Templates → Video`),
   tester sur 1 visuel produit.
3. Activer le **mode dev** (Settings) → **Save (API Format)** →
   `workflows/produit-wan22-i2v.json`.
4. Brancher le MCP dans Claude Code :
   - Pré-requis : **Node ≥ 22**.
   - Renseigner `.mcp.json` (copié depuis ce repo) avec l'URL RunComfy + clé.
   - Relancer Claude Code → l'outil `comfyui` (88 tools) est dispo.
5. Tester en local (sans cloud) si besoin : `COMFYUI_URL=http://127.0.0.1:8188`.

## Phase 2 — Industrialisation (API + n8n)

6. **Déployer en serverless** sur RunComfy → endpoint async
   (`POST /prod/v2/deployments/{id}/inference` → `request_id` → poll/result, ou webhook).
   Renseigner `RUNCOMFY_DEPLOYMENT_ID` / `RUNCOMFY_API_TOKEN` dans `.env`.
7. **n8n** : installer le node communautaire `n8n-nodes-comfyui` (ou
   `n8n-nodes-comfyui-image-to-video`), credential = `COMFYUI_URL` + Bearer.
   → 1 pipeline par projet, overrides par node ID.

## Phase 3 — Élargissement (LTX + avatars)

8. Ajouter le workflow **LTX** (social court, volume rapide) → `workflows/social-ltx-t2v.json`.
9. Installer les **custom nodes avatars** (LivePortrait / lip-sync) sur la machine
   RunComfy, construire le workflow talking-head → `workflows/avatar-liveportrait.json`.

---

## Usage rapide (script)

```bash
pip install websocket-client
cp .env.example .env   # remplir COMFYUI_URL (+ clé)
set -a && source .env && set +a

python scripts/comfy_submit.py workflows/produit-wan22-i2v.json \
    --set 6.inputs.text="cinematic product shot" \
    --set 3.inputs.seed=42 \
    --out ./outputs
```

L'API native (utilisée par le script ET tous les MCP) : `POST /prompt` →
WebSocket `ws://.../ws` (fin quand `node == null`) → `GET /history/{id}` →
`GET /view`. Sorties images **et** vidéos sous `outputs`.

---

## Alternatives cloud (si besoin de scaler / comparer)

| Solution | Principe | Quand |
|---|---|---|
| **RunComfy Serverless** | workflow → endpoint autoscalé, scale-to-zero | défaut (custom nodes faciles) |
| **Replicate** (`comfyui/any-comfyui-workflow`) | envoie `workflow_json`, clients Python/Node/Go | le plus simple à brancher |
| **RunPod worker-comfyui** | `/runsync` ou `/run`+`/status`, nodes via Docker | coût/volume |

---

## Caveats (recherche vérifiée 14/06/2026)

- **Cold start RunComfy 30-60s** → OK en async/webhook, pénible en synchrone.
- **Avatars** = maillon le moins éprouvé (dépend de custom nodes tiers) → valider tôt.
- MCP vidéo **jeunes** (artokun créé fév. 2026, ~153★) → API native = plan B stable.
- **Modèles non inclus** : prévoir le download des checkpoints WAN/LTX (gros fichiers).
- `joenorton/comfyui-mcp-server` (355★, le plus populaire) = **image only**, écarté.

## Sources clés
- API native : github.com/comfyanonymous/ComfyUI (`script_examples/websockets_api_example.py`), docs.comfy.org
- MCP : github.com/artokun/comfyui-mcp
- Cloud : docs.runcomfy.com/serverless, replicate.com/docs/guides/extend/comfyui, github.com/runpod-workers/worker-comfyui
