# Workflows ComfyUI (format API)

Range ici tes workflows **exportés en API format** (un fichier `.json` par usage).

## Comment exporter en API format
1. Dans ComfyUI : Settings → active le **mode dev** (`Enable Dev mode Options`).
2. Construis/charge ton workflow, vérifie qu'il tourne.
3. Menu → **Save (API Format)** → enregistre le `.json` ici.
   ⚠️ Différent du "Save" normal (qui exporte le graphe visuel, non utilisable par l'API).

## Convention de nommage
- `social-ltx-t2v.json` — social court (LTX, text-to-video) → Momentum / QuizFlash
- `produit-wan22-i2v.json` — produit/marketing (WAN 2.2, image-to-video) → video-ads-pulse360
- `avatar-liveportrait.json` — talking head / avatar → avatar-ia
- `hyperframe-*.json` — claude-video-hyperframe

## Override des paramètres (réutilisation multi-projets)
Chaque node a un ID (clé du JSON). On modifie les inputs sans toucher au fichier :

```bash
# Génère une vidéo produit à partir d'un prompt + seed différents
python ../scripts/comfy_submit.py produit-wan22-i2v.json \
    --set 6.inputs.text="luxury watch on marble, cinematic" \
    --set 3.inputs.seed=123 \
    --out ../outputs
```

Pour trouver les bons node IDs : ouvre le `.json` et repère `class_type`
(`CLIPTextEncode` = prompt, `KSampler` = seed/steps, `LoadImage` = image source…).

## Rappel modèles par usage
| Fichier | Modèle | Type |
|---|---|---|
| social-ltx-t2v | LTX Video | rapide, volume |
| produit-wan22-i2v | WAN 2.2 | qualité ciné, i2v |
| avatar-liveportrait | LivePortrait + i2v | custom nodes requis |
