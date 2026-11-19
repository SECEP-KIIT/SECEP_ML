#!/usr/bin/env python3
"""
embed.py — Phase C2. Frozen all-mpnet-base-v2 embeddings for every CSV in a folder.

Runs anywhere: Kaggle GPU (recommended) or local CPU (slow, ~30-60 min for the 10k pool).

    python embed.py --in-dir <folder with uid,input_text CSVs> --out <emb folder>

For each <name>.csv writes:
    <name>_emb.npy    float32 (rows in CSV order, L2-normalised, 768 dims)
    <name>_uids.txt   one uid per line, same order
    <name>_emb.json   input SHA-256, model, max tokens, device, versions, truncation count, timing

Skips a file when <name>_emb.json already records the same input SHA-256 and the .npy exists.
The encoder is never trained or modified; input_text is used exactly as given (no re-cleaning).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

MODEL = "sentence-transformers/all-mpnet-base-v2"
MAX_TOKENS = 384
SEED = 42


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_model(device: str):
    import torch
    from sentence_transformers import SentenceTransformer
    torch.manual_seed(SEED)
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(MODEL, device=device)
    model.max_seq_length = MAX_TOKENS
    model.eval()
    return model, device


def encode(model, texts: list[str], batch: int, progress: bool = True) -> np.ndarray:
    # Longest first: batches of similar length waste less padding; order is restored after.
    order = np.argsort([-len(t) for t in texts], kind="stable")
    E = model.encode([texts[i] for i in order], batch_size=batch, normalize_embeddings=True,
                     convert_to_numpy=True, show_progress_bar=progress)
    out = np.empty_like(E)
    out[order] = E
    return out.astype(np.float32)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--only", nargs="*", help="names to embed (default: every *.csv)")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--device", default="auto", help="auto | cuda | cpu")
    a = ap.parse_args()

    a.out.mkdir(parents=True, exist_ok=True)
    csvs = sorted(a.in_dir.glob("*.csv"))
    if a.only:
        csvs = [c for c in csvs if c.stem in a.only]
    if not csvs:
        raise SystemExit(f"no CSVs found in {a.in_dir}")

    model, device = None, a.device
    for csv in csvs:
        name, h = csv.stem, sha256(csv)
        npy, meta_p = a.out / f"{name}_emb.npy", a.out / f"{name}_emb.json"
        if npy.exists() and meta_p.exists() and json.loads(meta_p.read_text())["input_sha256"] == h:
            print(f"{name}: up to date, skipped")
            continue
        df = pd.read_csv(csv, dtype=str, keep_default_na=False)
        if list(df.columns[:2]) != ["uid", "input_text"]:
            raise SystemExit(f"{csv}: expected columns uid,input_text; got {list(df.columns)}")
        if model is None:
            model, device = load_model(a.device)
            print(f"model {MODEL} on {device}, max_seq_length {MAX_TOKENS}")
        texts = df["input_text"].tolist()

        n_tok = [len(ids) for ids in model.tokenizer(texts, add_special_tokens=True, truncation=False)["input_ids"]]
        n_trunc = int(sum(n > MAX_TOKENS for n in n_tok))

        t0 = time.time()
        E = encode(model, texts, a.batch)
        secs = time.time() - t0

        norms = np.linalg.norm(E, axis=1)
        assert E.shape == (len(df), 768) and np.all(np.abs(norms - 1) < 1e-3), "bad embedding shape/norm"
        np.save(npy, E)
        (a.out / f"{name}_uids.txt").write_text("\n".join(df["uid"]) + "\n", encoding="utf-8")

        import sentence_transformers
        import torch
        import transformers
        meta = {"input_file": csv.name, "input_sha256": h, "rows": len(df), "dim": int(E.shape[1]),
                "model": MODEL, "max_seq_length": MAX_TOKENS, "normalised": True, "dtype": "float32",
                "device": device, "gpu": torch.cuda.get_device_name(0) if device == "cuda" else None,
                "truncated_rows": n_trunc, "token_len_median": float(np.median(n_tok)),
                "token_len_p95": float(np.percentile(n_tok, 95)), "seconds": round(secs, 1),
                "versions": {"sentence_transformers": sentence_transformers.__version__,
                             "transformers": transformers.__version__, "torch": torch.__version__},
                "created": datetime.now().isoformat(timespec="seconds")}
        meta_p.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"{name}: {len(df)} rows, {n_trunc} truncated at {MAX_TOKENS} tokens "
              f"({n_trunc / len(df):.0%}), {secs:.0f}s -> {npy.name}")


if __name__ == "__main__":
    main()
