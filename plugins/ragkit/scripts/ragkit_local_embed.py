# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "sentence-transformers>=3"]
# ///
"""RagKit local-embedding sidecar. Heavy deps (torch/sentence-transformers) live
ONLY here; ragkit.py calls this via `uv run` subprocess when backend=local.

Verbs:
  install [model]                 download model into HF cache (~1.2GB default)
  encode --model M --in F --out F encode texts.json -> vecs.npy (normalized)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_MODEL = "Qwen/Qwen3-Embedding-0.6B"


def main() -> int:
    p = argparse.ArgumentParser(prog="ragkit_local_embed")
    sub = p.add_subparsers(dest="cmd", required=True)
    ip = sub.add_parser("install")
    ip.add_argument("model", nargs="?", default=DEFAULT_MODEL)
    ep = sub.add_parser("encode")
    ep.add_argument("--model", default=DEFAULT_MODEL)
    ep.add_argument("--in", dest="inp", required=True)
    ep.add_argument("--out", required=True)
    args = p.parse_args()

    if args.cmd == "install":
        print(f"RagKit：开始下载本地模型 {args.model}（默认模型约 1.2GB）…", flush=True)
        if not os.environ.get("HF_ENDPOINT"):
            print("提示：直连超时的话可先 export HF_ENDPOINT=https://hf-mirror.com 再重试", flush=True)
        from sentence_transformers import SentenceTransformer

        try:
            SentenceTransformer(args.model)
        except Exception as exc:
            # 镜像若对 resolve 请求回 308 跳转，huggingface_hub(httpx) 不跟随会直接失败，
            # 症状是"couldn't connect"。此时去掉 HF_ENDPOINT 直连重试一次。
            if os.environ.pop("HF_ENDPOINT", None):
                print(f"RagKit：经 HF_ENDPOINT 镜像下载失败（{type(exc).__name__}），"
                      "自动改为直连 huggingface.co 重试…", flush=True)
                SentenceTransformer(args.model)
            else:
                raise
        print("RagKit：模型已缓存，embed/query 将自动使用本地后端。")
        return 0

    # encode 只在本地模型已缓存时被调用（backend.resolve 前置保证），
    # 强制离线加载：不 ping hub、不受镜像/网络波动影响。
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import numpy as np
    from sentence_transformers import SentenceTransformer

    texts = json.loads(Path(args.inp).read_text(encoding="utf-8"))
    model = SentenceTransformer(args.model)
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    np.save(args.out, np.asarray(vecs, dtype="float32"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
