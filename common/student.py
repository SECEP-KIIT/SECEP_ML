"""Student model pieces shared by train_heads.py (C3), predict.py (C4), infer.py and retrain.py (D).

Numpy only (no scikit-learn), so the live service can import it.

Feature vector per email (order is fixed and recorded in manifest.json):
    [ 768 mpnet dims (L2-normalised) | one-hot recipient_role | one-hot recipient_position ]
Unseen role/position -> mapped to the fallback category (Other / List/Unknown), counted, warned.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np

ENCODER = "sentence-transformers/all-mpnet-base-v2"
MAX_TOKENS = 384
EMB_DIM = 768

ROLES_I1 = ["Executive", "Manager", "Engineer", "Analyst", "Consultant", "ClientFacing", "Other"]
POSITIONS_I1 = ["To", "Cc", "Bcc", "List/Unknown"]
ROLE_FALLBACK = "Other"
POSITION_FALLBACK = "List/Unknown"


# ------------------------------------------------------------------ embeddings
def load_embeddings(prefix: Path) -> tuple[np.ndarray, list[str]]:
    """prefix = Data/emb/<name>  ->  (<name>_emb.npy, <name>_uids.txt)."""
    E = np.load(f"{prefix}_emb.npy")
    uids = Path(f"{prefix}_uids.txt").read_text(encoding="utf-8").splitlines()
    if E.shape != (len(uids), EMB_DIM):
        raise ValueError(f"{prefix}: embedding shape {E.shape} vs {len(uids)} uids")
    return E, uids


def align(E: np.ndarray, emb_uids: Sequence[str], want: Sequence[str], what: str = "") -> np.ndarray:
    """Rows of E reordered to `want` (join by uid, never by position). Fails if any uid is missing."""
    pos = {u: i for i, u in enumerate(emb_uids)}
    missing = [u for u in want if u not in pos]
    if missing:
        raise ValueError(f"{what}: {len(missing)} uids have no embedding, e.g. {missing[:3]}")
    return E[[pos[u] for u in want]]


# ------------------------------------------------------------------ features
def one_hot(values: Sequence[str], cats: Sequence[str], fallback: str) -> tuple[np.ndarray, dict]:
    idx = {c: i for i, c in enumerate(cats)}
    if fallback not in idx:
        raise ValueError(f"fallback {fallback!r} not in categories {list(cats)}")
    M = np.zeros((len(values), len(cats)))
    unseen: dict[str, int] = {}
    for r, v in enumerate(values):
        if v not in idx:
            unseen[v] = unseen.get(v, 0) + 1
            v = fallback
        M[r, idx[v]] = 1.0
    return M, unseen


def build_features(E: np.ndarray, roles: Sequence[str], positions: Sequence[str],
                   role_cats: Sequence[str], pos_cats: Sequence[str]) -> tuple[np.ndarray, dict]:
    R, ur = one_hot(roles, role_cats, ROLE_FALLBACK)
    P, up = one_hot(positions, pos_cats, POSITION_FALLBACK)
    return np.hstack([E.astype(np.float64), R, P]), {"role": ur, "position": up}


# ------------------------------------------------------------------ heads
def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def logits(X: np.ndarray, W: np.ndarray, b: np.ndarray) -> np.ndarray:
    return X @ W.T + b


def head_proba(X: np.ndarray, W: np.ndarray, b: np.ndarray, T: float = 1.0) -> np.ndarray:
    return softmax(logits(X, W, b) / T)


# ------------------------------------------------------------------ model folder (I5)
def save_model(folder: Path, heads: dict[str, tuple[np.ndarray, np.ndarray]], manifest: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    arrays = {}
    for h, (W, b) in heads.items():
        arrays[f"W_{h}"], arrays[f"b_{h}"] = W, b
    np.savez(folder / "heads.npz", **arrays)
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def load_model(folder: Path) -> tuple[dict, dict[str, tuple[np.ndarray, np.ndarray]]]:
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    z = np.load(folder / "heads.npz", allow_pickle=False)
    heads = {h: (z[f"W_{h}"], z[f"b_{h}"]) for h in manifest["classes"]}
    return manifest, heads


MODES = ("balanced", "prior", "mixed")


def head_modes(manifest: dict, mode: str) -> dict[str, str]:
    """Which probability mode each head uses. 'mixed' = per-head choice stored in manifest['head_mode']."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    if mode == "mixed":
        hm = manifest.get("head_mode")
        if not hm:
            raise ValueError("model has no head_mode; run scripts/set_head_modes.py")
        return dict(hm)
    return {h: mode for h in manifest["classes"]}


def predict_proba(manifest: dict, heads: dict, X: np.ndarray, mode: str) -> dict[str, np.ndarray]:
    """Calibrated probabilities per head.
    balanced: softmax(logits / T)                       (as trained, class-balanced)
    prior:    softmax((logits + log prior) / T_prior)   (real-world class frequencies)
    mixed:    each head uses the mode recorded in manifest['head_mode']"""
    modes = head_modes(manifest, mode)
    out = {}
    for h, (W, b) in heads.items():
        z = logits(X, W, b)
        if modes[h] == "prior":
            if "class_prior" not in manifest:
                raise ValueError("this model has no class_prior; re-run train_heads.py")
            out[h] = softmax((z + np.log(np.asarray(manifest["class_prior"][h]))) / manifest["temperatures_prior"][h])
        elif modes[h] == "balanced":
            out[h] = softmax(z / manifest["temperatures"][h])
        else:
            raise ValueError(f"head {h}: unknown mode {modes[h]!r}")
    return out


class Student:
    """Single-email inference: text + role + position -> labels, confidences, needs_review.

    Embeds with the frozen encoder on CPU (same settings as C2), then runs the numpy heads.
    """

    def __init__(self, model_dir: Path, mode: str | None = None, device: str = "cpu"):
        self.manifest, self.heads = load_model(Path(model_dir))
        self.mode = mode or self.manifest.get("default_mode", "balanced")
        self.threshold = self.manifest.get("review_threshold", 0.60)
        from sentence_transformers import SentenceTransformer  # heavy import, only when needed
        self.encoder = SentenceTransformer(self.manifest["encoder"], device=device)
        self.encoder.max_seq_length = self.manifest["max_seq_length"]

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        return self.encoder.encode(list(texts), batch_size=8, normalize_embeddings=True, convert_to_numpy=True,
                                   show_progress_bar=False).astype(np.float32)

    def predict_one(self, input_text: str, role: str, position: str) -> dict:
        E = self.embed([input_text])
        X, unseen = build_features(E, [role], [position], self.manifest["roles"], self.manifest["positions"])
        P = predict_proba(self.manifest, self.heads, X, self.mode)
        out = {"mode": self.mode, "head_modes": head_modes(self.manifest, self.mode),
               "unseen": {k: list(v) for k, v in unseen.items() if v}}
        for h, p in P.items():
            j = int(p[0].argmax())
            out[h] = {"label": self.manifest["classes"][h][j], "confidence": float(p[0, j]),
                      "probs": dict(zip(self.manifest["classes"][h], map(float, p[0])))}
        out["needs_review"] = any(out[h]["confidence"] < self.threshold for h in P)
        return out
