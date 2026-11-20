"""secep_ml — SECEP inference package (Phase D).

    from secep_ml import triage
    t = triage.load("model_v1")
    result = t.classify(raw_bytes, "Manager", "To")

The package sits next to `common/` in ML_Training and imports the training-time text
recipe and numpy heads from there, so train and serve share one implementation.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
try:
    import common.text  # noqa: F401
except ImportError:  # running from outside ML_Training: make the sibling `common` importable
    sys.path.insert(0, str(_ROOT))

__version__ = "0.1.0"
