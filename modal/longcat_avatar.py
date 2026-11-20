"""LongCat-Video-Avatar 1.6 sur Modal (un H100, DiT INT8, 8 étapes distillées).

Étape 1 : télécharger les poids une fois dans un volume Modal (CPU, presque gratuit).
    modal run modal/longcat_avatar.py::telecharger
Étape 2 : générer une vidéo photo + voix et chronométrer chaque phase.
    modal run modal/longcat_avatar.py --image photo.png --audio voix.wav --sortie out.mp4

Auth : MODAL_TOKEN_ID / MODAL_TOKEN_SECRET (Doppler shared/prd).
Les dépôts de poids sont publics (MIT) : aucun jeton Hugging Face n'est envoyé.
"""

import json
import os
import subprocess
import threading
import time
from pathlib import Path

import modal

REPO_COMMIT = "58eb336edc5c8c63389838727e40b8c18434e54e"  # meituan-longcat/LongCat-Video, 15/11/2026
FLASH_ATTN_WHEEL = (
    "https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/"
    "flash_attn-2.7.4.post1+cu12torch2.6cxx11abiFALSE-cp311-cp311-linux_x86_64.whl"
)
WEIGHTS = Path("/weights")
CODE = Path("/opt/LongCat-Video")

volume = modal.Volume.from_name("longcat-weights", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg", "libsndfile1")
    .pip_install("torch==2.6.0", "torchvision==0.21.0", "torchaudio==2.6.0",
                 index_url="https://download.pytorch.org/whl/cu124")
    .pip_install(
        "numpy==1.26.4", "transformers==4.41.0", "diffusers==0.35.1", "loguru==0.7.2",
        "einops==0.8.0", "ftfy==6.2.0", "psutil==6.0.0", "av==12.0.0",
        "opencv-python-headless==4.9.0.80", "imageio==2.37.0", "imageio-ffmpeg==0.6.0",
        "scikit-learn==1.6.1", "scikit-image==0.25.2", "scipy==1.15.3", "soundfile==0.13.1",
        "soxr==0.5.0.post1", "librosa==0.11.0", "audio-separator==0.30.2", "pyloudnorm==0.1.1",
        "onnx==1.18.0", "onnxruntime-gpu==1.20.2", "safetensors", "accelerate",
        "huggingface_hub[hf_transfer]>=0.27", FLASH_ATTN_WHEEL,
    )
    .run_commands(
        f"git clone https://github.com/meituan-longcat/LongCat-Video.git {CODE}",
        f"cd {CODE} && git checkout {REPO_COMMIT}",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
)

app = modal.App("longcat-avatar", image=image)


@app.function(volumes={str(WEIGHTS): volume}, timeout=3600, cpu=4, memory=8192)
def telecharger():
    from huggingface_hub import snapshot_download

    t = time.time()
    snapshot_download(
        "meituan-longcat/LongCat-Video", local_dir=str(WEIGHTS / "LongCat-Video"),
        allow_patterns=["tokenizer/*", "text_encoder/*.safetensors", "text_encoder/*.json",
                        "vae/*.safetensors", "vae/*.json"],
        ignore_patterns=["*fp32*", "*.bin", "*flax*", "*tf_model*"],
    )
    snapshot_download(
        "meituan-longcat/LongCat-Video-Avatar-1.6", local_dir=str(WEIGHTS / "LongCat-Video-Avatar-1.6"),
        allow_patterns=["base_model_int8/*", "loraA/*", "loraB/*", "scheduler/*", "vocal_separator/*",
                        "whisper-large-v3/model.safetensors", "whisper-large-v3/*.json", "whisper-large-v3/*.txt"],
        ignore_patterns=["*fp32*", "*flax*", "*tf_model*", "whisper-large-v3/pytorch_model*"],
    )
    volume.commit()
    taille = subprocess.run(["du", "-sh", str(WEIGHTS)], capture_output=True, text=True).stdout.strip()
    print(f"[telecharger] {taille} en {time.time() - t:.0f} s")
    return taille


def _sonde_memoire(stop, pic):
    while not stop.is_set():
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True).stdout.strip()
        if out:
            pic[0] = max(pic[0], int(out.splitlines()[0]))
        time.sleep(2)


@app.function(gpu="H100", volumes={str(WEIGHTS): volume}, timeout=2400, memory=65536)
def generer(image_png: bytes, audio_wav: bytes, prompt: str, resolution: str = "720p", num_segments: int = 1):
    t_debut = time.time()
    travail = Path("/tmp/job")
    travail.mkdir(parents=True, exist_ok=True)
    (travail / "ref.png").write_bytes(image_png)
    (travail / "voix-brute.wav").write_bytes(audio_wav)
    # L'enregistrement plante (BrokenPipe) si la vidéo générée dépasse la voix :
    # on complète la voix par du silence jusqu'à la durée générée + 1 s, puis on recoupe à la fin.
    duree_voix = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(travail / "voix-brute.wav")],
        capture_output=True, text=True).stdout.strip())
    duree_generee = (93 + (num_segments - 1) * 80) / 25
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(travail / "voix-brute.wav"), "-af",
                    f"apad=whole_dur={max(duree_voix, duree_generee) + 1.0:.3f}", str(travail / "voix.wav")], check=True)
    (travail / "entree.json").write_text(json.dumps(
        {"prompt": prompt, "cond_image": str(travail / "ref.png"), "cond_audio": {"person1": str(travail / "voix.wav")}}))

    cmd = [
        "torchrun", "--nproc_per_node=1", "run_demo_avatar_single_audio_to_video.py",
        "--context_parallel_size=1", f"--checkpoint_dir={WEIGHTS / 'LongCat-Video-Avatar-1.6'}",
        "--stage_1=ai2v", f"--input_json={travail / 'entree.json'}", f"--output_dir={travail / 'sortie'}",
        f"--resolution={resolution}", f"--num_segments={num_segments}", "--ref_img_index=10",
        "--mask_frame_range=0", "--use_distill", "--lora_path", "loraB/lora.safetensors",
        "--model_type", "avatar-v1.6", "--mix_steps=4", "--mix_alpha=1.0", "--use_int8",
    ]
    stop, pic = threading.Event(), [0]
    threading.Thread(target=_sonde_memoire, args=(stop, pic), daemon=True).start()
    journal, t_cmd, reperes = [], time.time(), {}
    proc = subprocess.Popen(cmd, cwd=CODE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for ligne in proc.stdout:
        print(ligne, end="")
        journal.append(ligne)
        for cle in ("Generating segment", "Loading INT8", "Loading mixed LoRAs"):
            if cle in ligne:
                reperes[ligne.strip()[:60]] = round(time.time() - t_cmd, 1)
    proc.wait()
    stop.set()
    duree_cmd = time.time() - t_cmd
    if proc.returncode != 0:
        raise RuntimeError("échec LongCat :\n" + "".join(journal[-40:]))

    videos = sorted((travail / "sortie").glob("*.mp4"))
    if not videos:
        raise RuntimeError("aucune vidéo produite :\n" + "".join(journal[-40:]))
    video = travail / "sortie-recoupee.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(videos[-1]), "-i", str(travail / "voix-brute.wav"),
                    "-map", "0:v:0", "-map", "1:a:0", "-t", f"{duree_voix:.3f}", "-c:v", "libx264", "-crf", "16",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(video)], check=True)
    duree_video = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True).stdout.strip())
    return {
        "video": video.read_bytes(),
        "fichier": video.name,
        "duree_video_s": duree_video,
        "duree_commande_s": round(duree_cmd, 1),
        "duree_fonction_s": round(time.time() - t_debut, 1),
        "reperes_s": reperes,
        "pic_memoire_gpu_mo": pic[0],
    }


@app.local_entrypoint()
def main(image: str, audio: str, sortie: str, prompt: str = "A person is speaking expressively, looking at the camera.",
         resolution: str = "720p", num_segments: int = 1):
    r = generer.remote(Path(image).read_bytes(), Path(audio).read_bytes(), prompt, resolution, num_segments)
    Path(sortie).write_bytes(r.pop("video"))
    r["sortie"] = sortie
    print(json.dumps(r, ensure_ascii=False, indent=2))
    Path(sortie).with_suffix(".json").write_text(json.dumps(r, ensure_ascii=False, indent=2))
