# Workflow n8n — Génération vidéo ComfyUI via RunComfy

Fichier : `comfyui-runcomfy-video.json` (importable).

## Ce qu'il fait
Webhook → soumet un job à un déploiement RunComfy serverless → poll le statut →
récupère l'URL de la vidéo → répond au projet appelant. Réutilisable par tous les
projets (Momentum, video-ads-pulse360, avatar-ia) via le même endpoint.

## Import (3 min)
1. n8n → **Workflows → Import from File** → choisir `comfyui-runcomfy-video.json`.
2. Créer le **credential** (une fois) :
   - Credentials → New → **Header Auth**
   - Name : `RunComfy Bearer`
   - Header **Name** : `Authorization`
   - Header **Value** : `Bearer <TON_TOKEN>` (le token de `.env`, ⚠️ avec le préfixe `Bearer `)
   - Réaffecter ce credential sur les 3 nodes HTTP (un warning les signale).
3. **Activer** le workflow → copier l'URL du webhook (`/webhook/comfyui-video`).

## Appeler le workflow (depuis un projet)
```bash
curl -X POST https://<ton-n8n>/webhook/comfyui-video \
  -H "Content-Type: application/json" \
  -d '{
    "deployment_id": "ton-deployment-id",
    "prompt": "luxury watch on marble, cinematic",
    "seed": 42,
    "projet": "video-ads-pulse360"
  }'
```
Réponse : `{ "status": "completed", "projet": "...", "videoUrl": "https://...", "allUrls": [...] }`

Payload accepté : `deployment_id` (sinon défaut à remplacer dans le node "Prépare"),
`prompt`, `seed`, `image_url` (i2v), `overrides` (objet brut prioritaire), `projet`.

## ⚠️ À adapter
- Les **node IDs des overrides** (`6` prompt, `3` seed, `10` image) sont des exemples :
  ajuste-les aux IDs de TON workflow déployé (regarde le workflow API JSON sur RunComfy).
- Le token vit dans le **credential n8n**, jamais dans le fichier workflow.
- Garde-fou anti-boucle : abandon après 60 tentatives (~5 min). Ajuste le node
  "Le job a échoué ou expiré ?" si tes vidéos sont plus longues à générer.
