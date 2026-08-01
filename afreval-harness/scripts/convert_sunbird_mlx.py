#!/usr/bin/env python3
"""Convert the Sunbird HF transformers Whisper fine-tune to mlx-whisper format.

Experiment status: the MLX conversion WORKS (verified transcribing ach/sna/amh)
but was NOT adopted for the QA pass — under MPS contention with the running
torch pass it measured slower, and memory was critical. Weights regenerable with
this script; revisit if a single-model MLX-only pass is wanted.

Key conversion facts (mlx-whisper 0.4.3):
  - key naming: HF `layers.N.self_attn.q_proj` -> mlx `blocks.N.attn.query`, etc.
  - conv weights: HF (out,in,K) -> mlx (out,K,in)  [channels-last in mlx]
  - lm_head tied to embed_tokens (tie_word_embeddings: true) -> drop
  - encoder positional embedding is `_positional_embedding` (learned, loaded)
  - language forcing: Sunbird reuses base-Whisper token ids, so pass the base
    language name that maps to the same id (ach=50357 -> "su", etc.)

Output dir is loadable by mlx_whisper.load_model().
"""
import json
import os
import numpy as np
from safetensors import safe_open

HF_SNAP = os.environ.get("SUNBIRD_SNAP", "")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "waxal", "models", "sunbird-mlx")

CFG = json.load(open(os.path.join(HF_SNAP, "config.json")))
DIMS = {
    "n_mels": CFG["num_mel_bins"],
    "n_audio_ctx": CFG["max_source_positions"],
    "n_audio_state": CFG["d_model"],
    "n_audio_head": CFG["encoder_attention_heads"],
    "n_audio_layer": CFG["encoder_layers"],
    "n_vocab": CFG["vocab_size"],
    "n_text_ctx": CFG["max_target_positions"],
    "n_text_state": CFG["d_model"],
    "n_text_head": CFG["decoder_attention_heads"],
    "n_text_layer": CFG["decoder_layers"],
}


def map_key(k: str):
    parts = k.split(".")
    side = parts[1]
    rest = parts[2:]
    m = {
        "embed_positions.weight": "_positional_embedding" if side == "encoder" else "positional_embedding",
        "layer_norm.bias": "ln.bias" if side == "decoder" else "ln_post.bias",
        "layer_norm.weight": "ln.weight" if side == "decoder" else "ln_post.weight",
        "conv1.bias": "conv1.bias", "conv1.weight": "conv1.weight",
        "conv2.bias": "conv2.bias", "conv2.weight": "conv2.weight",
    }
    if side == "decoder":
        m["embed_tokens.weight"] = "token_embedding.weight"
    if rest[0] == "layers":
        n = rest[1]
        inner = rest[2:]

        def attn(prefix, src):
            return f"{side}.blocks.{n}.{prefix}.{src}"

        if inner[0] == "self_attn":
            q = {"q_proj": "query", "k_proj": "key", "v_proj": "value", "out_proj": "out"}[inner[1]]
            return attn("attn", f"{q}.{inner[2]}")
        if inner[0] == "encoder_attn":
            q = {"q_proj": "query", "k_proj": "key", "v_proj": "value", "out_proj": "out"}[inner[1]]
            return attn("cross_attn", f"{q}.{inner[2]}")
        if inner[0] == "self_attn_layer_norm":
            return attn("attn_ln", inner[1])
        if inner[0] == "encoder_attn_layer_norm":
            return attn("cross_attn_ln", inner[1])
        if inner[0] == "fc1":
            return attn("mlp1", inner[1])
        if inner[0] == "fc2":
            return attn("mlp2", inner[1])
        if inner[0] == "final_layer_norm":
            return attn("mlp_ln", inner[1])
        return None
    joined = ".".join(rest)
    if joined in m:
        return f"{side}.{m[joined]}"
    return f"{side}.{joined}"


def main():
    if not HF_SNAP or not os.path.exists(HF_SNAP):
        raise SystemExit("set SUNBIRD_SNAP to the HF snapshot dir of Sunbird/asr-whisper-51-african-languages")
    with safe_open(os.path.join(HF_SNAP, "model.safetensors"), framework="numpy") as f:
        weights = {}
        for k in f.keys():
            mk = map_key(k)
            if mk is None:
                continue
            arr = f.get_tensor(k)
            if mk in ("encoder.conv1.weight", "encoder.conv2.weight"):
                arr = arr.transpose(0, 2, 1)
            weights[mk] = arr.astype(np.float16)
    os.makedirs(OUT, exist_ok=True)
    np.savez(os.path.join(OUT, "weights.npz"), **weights)
    with open(os.path.join(OUT, "config.json"), "w") as fh:
        json.dump(DIMS, fh)
    print(f"mapped {len(weights)} tensors -> {OUT}")


if __name__ == "__main__":
    main()
