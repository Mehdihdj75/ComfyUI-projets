# Comparatif coût — héberger/exécuter ComfyUI (juin 2026)

> ⚠️ Chiffres **indicatifs** (juin 2026), à revérifier sur les pages pricing : le GPU
> cloud bouge vite. Objectif : cadrer le budget, pas un devis exact.

## Les 4 options

| Option | Modèle de prix | Repère 2026 | Force | Faiblesse |
|---|---|---|---|---|
| **RunComfy** (machine + serverless) | Crédits/seconde (≈ tarif horaire par tier GPU) ; Pro = -20 à -30% | "0,39 crédit/s" sur tier moyen | Custom nodes faciles, UI, déploiement API 1-clic | **Cher si >10 h/sem** ; cold start 30-60s |
| **RunPod** (Pods ou Serverless) | Pod = /seconde ; Serverless = /milliseconde | A100 80 Go ≈ **2,17 $/h** ; T4 ≈ 0,40 $/h ; spot dès 0,22 $/h | Le moins cher à volume ; contrôle total | Custom nodes = build Docker ; plus technique |
| **Replicate** (`comfyui/any-comfyui-workflow`) | Au temps GPU/seconde | A100 ≈ **0,0014 $/s** (~5 $/h) ; H100 ≈ 0,001525 $/s | Zéro infra, clients Python/Node/Go | Moins flexible ; modèles/nodes pas tous préinstallés |
| **fal.ai** (modèles vidéo hébergés) | Au /seconde de vidéo générée | WAN ≈ **0,05 $/s** de vidéo → Veo 3 ≈ 0,40 $/s | Le plus simple pour de la vidéo "API pure" | Pas "any workflow" ComfyUI ; moins de contrôle |

## Règle de décision (utilisation = clé)
- **Break-even serverless vs dédié ≈ 30% d'utilisation GPU** :
  - **< 30%** (usage par à-coups, multi-projets irréguliers) → **serverless** (RunPod/Replicate/fal) gagne.
  - **> 30%** (génération quasi continue) → **machine dédiée à l'heure** (RunPod Pod) moins chère.
- RunComfy = **excellent bac à sable de prototypage**, vite cher en prod continue.

## Reco pour ton cas (cloud, 4 usages, démarrage)
1. **Prototypage + avatars (custom nodes)** → **RunComfy** (installer LivePortrait facilement).
2. **Social court à volume (LTX)** → **Replicate** ou **fal.ai** (au /seconde, simple, scalable).
3. **Produit/marketing WAN 2.2 régulier** → si volume monte, **RunPod** (Pod dédié, Docker avec les nodes).

→ Architecture cible : **RunComfy pour construire/itérer les workflows**, puis **basculer
les workflows matures en endpoint Replicate/RunPod** pour la prod automatisée (n8n).

## Ordre de grandeur d'un clip vidéo
Une vidéo WAN/LTX courte (3-5s) = quelques dizaines de secondes à quelques minutes de GPU.
À ~0,0014 $/s (A100 Replicate), un clip ≈ **0,05 à 0,30 $** selon durée/résolution/steps.
Volume social (100 clips/jour) ≈ **5 à 30 $/jour** — à valider sur tes workflows réels.

## Sources
- runcomfy.com/pricing · docs.runcomfy.com/serverless/about-billing
- runpod.io/articles/guides/serverless-gpu-pricing · deploybase.ai/articles/runpod-gpu-pricing
- replicate.com (pricing GPU/seconde) · fal.ai/pricing
- claudiaperez.co.uk/article/runcomfy-review-2026 (analyse break-even)
