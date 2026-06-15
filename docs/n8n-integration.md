# Intégration n8n — ComfyUI en pipeline de prod

Objectif : déclencher la génération vidéo ComfyUI depuis tes workflows n8n
(1 pipeline par projet : Momentum, video-ads-pulse360, avatar-ia…).

Deux approches. Commence par A (rapide), passe à B si tu veux du contrôle fin.

---

## Approche A — Node communautaire (le plus rapide)
1. n8n → Settings → Community Nodes → installer **`n8n-nodes-comfyui`**
   (générique) ou **`n8n-nodes-comfyui-image-to-video`** (spécialisé i2v).
2. Credential : `COMFYUI_URL` (ton endpoint RunComfy) + Bearer token si protégé.
3. Dans le node : coller le **workflow exporté en API format** + les overrides.
4. Brancher en aval : upload Drive / Airtable / publication réseaux.

> Le node pilote l'API native (`POST /prompt`, `/upload/image`, poll `/history`, `/view`).
> Modeste/peu éprouvé → garder l'approche B en secours.

---

## Approche B — HTTP Request natifs (robuste, sans dépendance)
Reproduit le pattern API officiel avec des nodes n8n standard.

```
[Trigger]
   │
   ▼
[HTTP Request: POST {{COMFYUI_URL}}/prompt]      ← body = { "prompt": <workflow API JSON> }
   │  (récupère prompt_id)
   ▼
[Wait 5s]
   │
   ▼
[HTTP Request: GET {{COMFYUI_URL}}/history/{{prompt_id}}]
   │
   ▼
[IF: history vide ?] ──oui──► retour à [Wait 5s]   (boucle de polling)
   │ non
   ▼
[HTTP Request: GET {{COMFYUI_URL}}/view?filename=...&type=output]  ← télécharge la vidéo
   │
   ▼
[Suite : Drive / Airtable / publication]
```

Config des nodes clés :
- **POST /prompt** : Method POST, JSON body `{ "prompt": {...}, "client_id": "n8n" }`.
  Override d'un paramètre via expression : `={{ $json.workflow }}` préparé dans un node Set.
- **Polling** : Wait (5s) + HTTP GET `/history/{{ $json.prompt_id }}` + IF sur
  `{{ Object.keys($json).length === 0 }}` pour reboucler.
- **Download** : HTTP GET `/view`, Response Format = File.

> Variante cloud serverless RunComfy : remplacer par
> `POST /prod/v2/deployments/{id}/inference` → `request_id` → poll `/requests/{id}/status`
> → `/result`, ou configurer un **webhook** (n8n Webhook node) pour éviter le polling.

---

## Override des paramètres par projet
Un node **Set** construit le JSON workflow avec les valeurs du projet
(prompt, seed, image source) avant le POST. Même workflow figé, valeurs différentes :

```
workflow["6"]["inputs"]["text"]  = {{ $json.prompt }}
workflow["3"]["inputs"]["seed"]  = {{ $json.seed }}
workflow["10"]["inputs"]["image"] = {{ $json.imageUrl }}   // i2v
```

## Workflow importable prêt
✅ `n8n/comfyui-runcomfy-video.json` — webhook → RunComfy serverless → poll → URL vidéo.
Import + payload : voir `n8n/README.md`.

## TODO (une fois le deployment_id créé)
- [x] Générer le **workflow n8n importable (.json)** prêt à l'emploi.
- [ ] Créer le credential `RunComfy Bearer` + renseigner le `deployment_id`.
- [ ] Tester end-to-end sur 1 clip WAN 2.2.
- [ ] Dupliquer le pipeline par projet (Momentum / video-ads-pulse360 / avatar-ia).
