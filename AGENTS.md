# AGENTS.md — ComfyUI-projets

## Ce que c'est
Brique d'infra transverse de **génération d'images et de vidéos par API**, réutilisée par
`video-ads-pulse360`, `avatar-ia`, Momentum et QuizFlash. Ce n'est pas un produit.

## Structure
- `workflows/` — workflows de génération
- `n8n/` — intégrations n8n
- `scripts/`, `docs/`, `SETUP.md`

## Secrets
Clés API au coffre (`osenv get NOM`). Jamais en dur, jamais commitées.

## Pièges à éviter
- **Le nom du repo ment sur l'orientation actuelle.** Décision du 15/06/2026 : la génération passe
  par **fal.ai au clip, piloté par Claude en API** — pas d'installation ComfyUI, pas de GPU mensuel.
- **Le local sur le Mac a été écarté et documenté** : WAN 2.2 14B est trop lourd en MPS sur un
  M2 Pro 32 Go, qualité dégradée. Ne pas relancer cette piste sans raison neuve.
- L'objectif réel est 1 à 2 vidéos par jour à qualité WAN 2.2 **sans faire exploser le budget** :
  toute proposition doit se juger au coût par clip.

## Conventions
- Code only : médias, `.env` et secrets restent locaux (gitignorés), jamais commités.
- Identité git : `Mehdihdj75 <mehdihdj2014@gmail.com>` — **jamais** `david@keepgrowing.fr`.
- Français, concis, orienté action.
