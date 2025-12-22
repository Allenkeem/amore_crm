# rag_chatbot.py

from __future__ import annotations

import json, sys, argparse
from pathlib import Path
from typing import List, Tuple
import numpy as np
import faiss  # type: ignore
from sentence_transformers import SentenceTransformer  # type: ignore
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline,
)
import torch

###############################################################################
# Utils
###############################################################################
PROJ_ROOT = Path(__file__).resolve().parents[1]

def _resolve(p: str | Path) -> Path:
    p = Path(p)
    if p.is_file():
        return p
    if (PROJ_ROOT / p).is_file():
        return PROJ_ROOT / p
    raise FileNotFoundError(p)

###############################################################################
# 데이터 로더
###############################################################################

def load_chunks(chunks_path: str | Path, vectors_path: str | Path) -> Tuple[List[str], List[dict], np.ndarray]:
    chunks_path, vectors_path = _resolve(chunks_path), _resolve(vectors_path)

    with open(chunks_path, encoding="utf-8") as f_txt:
        chunks_raw = json.load(f_txt)

    # extract texts & metadata
    texts, metas = [], []
    for entry in chunks_raw:
        if isinstance(entry, str):  # plain text list
            texts.append(entry)
            metas.append({})
        elif isinstance(entry, dict):  # {text|content, metadata}
            texts.append(entry.get("text") or entry.get("content"))
            metas.append(entry.get("metadata", {}))
        else:
            raise ValueError(f"Unsupported chunk format: {type(entry)}")

    # load vectors
    with open(vectors_path, encoding="utf-8") as f_vec:
        vec_raw = json.load(f_vec)

    # vectors may be [{embedding:[...]}] or [[...]]
    if isinstance(vec_raw[0], dict):
        vecs = np.asarray([row["embedding"] for row in vec_raw], dtype="float32")
    else:
        vecs = np.asarray(vec_raw, dtype="float32")

    if len(vecs) != len(texts):
        raise ValueError("#vectors != #texts — check files match")

    # L2‑normalize for cosine under IndexFlatIP
    faiss.normalize_L2(vecs)
    return texts, metas, vecs


def build_index(vecs: np.ndarray) -> faiss.Index:
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    return index

###############################################################################
# Embedding & LLM loaders
###############################################################################

def load_embedder(model_name: str = "jhgan/ko-sbert-nli", device: str = "cpu"):
    return SentenceTransformer(model_name, device=device)


def load_llm(device: str = "cpu", model_id: str = "google/gemma-3-1b-it"):
    """Returns a HuggingFace pipeline ready for generation.
    `device` is only used to pick dtype; actual placement is handled by accelerate via device_map="auto".
    """
    dtype = torch.float16 if device in {"cuda", "mps"} else torch.float32
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=dtype,
        device_map="auto" if device != "cpu" else None,
    )
    return pipeline(
        task="text-generation",
        model=model,
        tokenizer=tok,
        max_new_tokens=512,
        do_sample=True,
        top_p=0.9,
        temperature=0.7,
    )

###############################################################################
# Main chat loop
###############################################################################

def chat_loop(args: argparse.Namespace):
    print("[INFO] Loading data …")
    texts, metas, vecs = load_chunks(args.chunks, args.vectors)
    index = build_index(vecs)
    embedder = load_embedder(device=args.device)
    llm = load_llm(device=args.device)

    print("[READY] Type your question — Ctrl+C to exit\n")
    try:
        while True:
            q = input("🗨️  Q: ").strip()
            if not q:
                continue

            q_vec = embedder.encode(q, normalize_embeddings=True)
            D, I = index.search(np.asarray([q_vec], dtype="float32"), args.topk)
            ctx = []
            for rank, (idx, score) in enumerate(zip(I[0], D[0]), 1):
                ctx.append(f"[{rank}] (S={score:.3f})\n{texts[idx]}\n")
            prompt = (
                "질문: " + q + "\n" +\
                "문맥:\n" + "\n".join(ctx) +\
                "\n\n대답 (한국어):"
            )
            print("⏳  Generating…")
            ans = llm(prompt)[0]["generated_text"][len(prompt):].strip()
            print("🤖 A:", ans, "\n")
    except KeyboardInterrupt:
        print("\n[EXIT]")

###############################################################################
# CLI
###############################################################################

def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--chunks", default="data/chunks/pages_text_chunks.json")
    p.add_argument("--vectors", default="data/index/pages_text_chunks_vectors.json")
    p.add_argument("--device", choices=["cpu", "cuda", "mps"], default="cpu")
    p.add_argument("--topk", type=int, default=4)
    return p.parse_args(argv)

###############################################################################
# Entrypoint
###############################################################################
if __name__ == "__main__":
    chat_loop(parse_args())