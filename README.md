# ComfyUI-projets

Capacité transverse de **génération images/vidéos par API/MCP** avec ComfyUI,
réutilisable sur plusieurs projets : `video-ads-pulse360`, `avatar-ia`,
`claude-video-hyperframe`, Momentum, QuizFlash.

> Relié à l'OS : `system/capabilities/connectors.md` (connecteur `comfyui`) +
> `system/capabilities/comfyui-video.md` (note de référence).

## Décisions actées (15/06/2026)
- **Infra** : Cloud GPU — **RunComfy** d'abord, RunPod en option coût/volume.
- **Pilotage** : MCP **`artokun/comfyui-mcp`** (mode remote) + node **n8n** pour la prod.
- **Usages** : social court · produit/marketing · avatars/talking-heads · pilotage Claude Code.

## Contenu du repo
| Chemin | Rôle |
|---|---|
| `SETUP.md` | Guide d'installation pas à pas (RunComfy + MCP + n8n) |
| `.mcp.json` | Config MCP `comfyui-mcp` (mode remote) — à compléter |
| `.env.example` | Variables (URL ComfyUI, clés RunComfy) |
| `scripts/comfy_submit.py` | Helper : soumet un workflow + overrides, télécharge images/vidéos |
| `workflows/` | Workflows exportés en **API format** (1 par usage) |
| `docs/cost-comparison.md` | RunComfy vs RunPod vs Replicate vs fal.ai (budget GPU) |
| `docs/n8n-integration.md` | Intégration n8n (pipelines de prod par projet) |

## Démarrage rapide
1. Créer un compte **RunComfy**, lancer une machine ComfyUI → récupérer l'URL + clé.
2. `cp .env.example .env` puis remplir ; renseigner aussi `.mcp.json`.
3. `pip install websocket-client` puis tester :
   ```bash
   set -a && source .env && set +a
   python scripts/comfy_submit.py workflows/produit-wan22-i2v.json \
       --set 6.inputs.text="cinematic product shot" --out ./outputs
   ```
4. Redémarrer Claude Code → l'outil `comfyui` (88 tools) est dispo.

Détails complets → [`SETUP.md`](./SETUP.md).
