# Créer son 1er déploiement RunComfy serverless (→ deployment_id)

But : passer de "j'ai juste la clé API" à "j'ai un endpoint appelable".
Token API = celui déjà dans `.env`. Il manque le **deployment_id**.

## Étapes (dashboard RunComfy)

1. **Se connecter** sur runcomfy.com → lancer un **ComfyUI Cloud** (workspace/machine).
2. **Charger un workflow vidéo** : `Workflow → Browse Templates → Video` →
   choisir **Wan2.2 14B T2V** (texte→vidéo) ou **I2V** (image→vidéo, produit).
3. **Lancer une génération test** dans l'UI (la 1re fois, RunComfy télécharge les
   modèles WAN — ça peut prendre quelques minutes). Vérifier qu'une vidéo sort.
4. **Cloud Save** le workflow (crée une *version* déployable).
5. Aller dans **Deployments → Create Deployment** :
   - sélectionner le workflow sauvegardé,
   - choisir un **tier GPU** avec assez de VRAM pour WAN 14B (≥ 24-48 Go conseillé),
   - autoscaling : `min = 0`, `keep-warm = 0` pour payer au plus juste (cold start accepté).
6. **Copier le `deployment_id`** affiché.
7. (Le **token API** est déjà récupéré → dans `.env`.)

## Repérer les node IDs (pour les overrides)
Dans l'éditeur, le node du **prompt positif** (`CLIPTextEncode`) et du **sampler**
(`KSampler`, seed/steps) portent un ID. On les utilisera ainsi :
```
--set <idPrompt>.inputs.text="..."   --set <idSampler>.inputs.seed=42
```
Astuce : un 1er test SANS override valide d'abord la chaîne.

## Lancer un test (une fois le deployment_id en main)
```bash
set -a && source .env && set +a
python scripts/runcomfy_submit.py <deployment_id> --out ./outputs
# puis avec override de prompt :
python scripts/runcomfy_submit.py <deployment_id> \
    --set 6.inputs.text="luxury watch on marble, cinematic" --out ./outputs
```
