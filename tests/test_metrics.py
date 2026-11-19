"""Run from ML_Training:  python -m pytest tests -q"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import metrics as M  # noqa: E402

TYPE = M.HEADS["type"]


# ---------------------------------------------------------------- absent-class rule
def test_class_unused_by_both_sides_is_left_out():
    t = ["Task", "Info", "Info", "Meeting"]
    p = ["Task", "Info", "Task", "Meeting"]
    # Credentials and Approval never used -> average over Task, Info, Meeting only
    f_task, f_info, f_meet = 2 / 3, 2 / 3, 1.0
    assert M.macro_f1(t, p, TYPE) == pytest.approx((f_task + f_info + f_meet) / 3)
    assert M.per_class(t, p, TYPE)["Credentials"]["f1"] is None


def test_class_predicted_but_absent_from_truth_counts_as_zero():
    t = ["Info", "Info"]
    p = ["Info", "Credentials"]
    # Info: tp1 fn1 -> 2/3 ; Credentials: fp1 -> 0 ; macro = (2/3 + 0)/2
    assert M.macro_f1(t, p, TYPE) == pytest.approx(1 / 3)


def test_class_in_truth_never_predicted_counts_as_zero():
    t = ["Info", "Credentials"]
    p = ["Info", "Info"]
    assert M.macro_f1(t, p, TYPE) == pytest.approx((2 / 3 + 0) / 2)


def test_matches_human_baseline_rule_and_sklearn():
    from sklearn.metrics import f1_score
    rng = np.random.default_rng(0)
    for _ in range(50):
        t = list(rng.choice(TYPE, 30, p=[.3, .5, .02, .1, .08]))
        p = list(rng.choice(TYPE, 30))
        used = sorted(set(t) | set(p))
        ref = f1_score(t, p, labels=used, average="macro", zero_division=0)
        assert M.macro_f1(t, p, TYPE) == pytest.approx(ref)


def test_unknown_label_raises():
    with pytest.raises(ValueError):
        M.macro_f1(["Info"], ["Spam"], TYPE)


# ---------------------------------------------------------------- lenient rule
def test_lenient_truth_rules():
    t = ["Task", "Task", "Task", "Info"]
    a = ["Info", "Info", "", ""]
    p = ["Info", "Meeting", "Task", "Task"]
    # matches alt -> alt ; wrong -> primary ; matches primary -> primary ; blank alt never matches
    assert M.lenient_truth(t, a, p) == ["Info", "Task", "Task", "Info"]


def test_lenient_never_below_strict_accuracy():
    t = ["Task", "Approval", "Info"]
    a = ["Info", "Task", ""]
    p = ["Info", "Task", "Info"]
    assert M.accuracy(M.lenient_truth(t, a, p), p) == 1.0
    assert M.accuracy(t, p) == pytest.approx(1 / 3)


# ---------------------------------------------------------------- fixed cases
def test_perfect_is_one():
    t = ["Task"] * 5 + ["Info"] * 9 + ["Credentials"]
    assert M.macro_f1(t, t, TYPE) == 1.0


def test_all_info_hand_calc_gold_dev_counts():
    # gold-dev counts: Info 100, Task 53, Approval 16, Meeting 13, Credentials 2
    t = ["Info"] * 100 + ["Task"] * 53 + ["Approval"] * 16 + ["Meeting"] * 13 + ["Credentials"] * 2
    p = ["Info"] * len(t)
    f_info = 200 / 284
    assert M.macro_f1(t, p, TYPE) == pytest.approx(f_info / 5)            # 0.140845
    assert M.macro_f1(M.to_view(t, "type_action"), M.to_view(p, "type_action"),
                      M.VIEWS["type_action"][2]) == pytest.approx(f_info / 2)


def test_views_match_human_baseline_labels():
    assert M.to_view(["Info", "Task"], "type_action") == ["Info", "Needs something"]
    assert M.to_view(["Critical", "High", "Medium", "Low"], "urgency_2") == ["Act soon"] * 2 + ["Can wait"] * 2
    assert M.to_view(["Neutral", "Frustrated"], "sentiment_2") == ["Neutral", "Not neutral"]


def test_confusion_orientation():
    cm = M.confusion(["Task", "Task"], ["Info", "Task"], TYPE)
    assert cm[TYPE.index("Task"), TYPE.index("Info")] == 1  # row = truth, col = pred
    assert cm.sum() == 2


# ---------------------------------------------------------------- bootstrap
def test_bootstrap_deterministic_and_brackets():
    rng = np.random.default_rng(1)
    t = list(rng.choice(TYPE, 100))
    p = [x if rng.random() < .7 else "Info" for x in t]
    a = M.bootstrap_macro_f1_ci(t, p, TYPE, 500)
    assert a == M.bootstrap_macro_f1_ci(t, p, TYPE, 500)
    assert a[0] <= M.macro_f1(t, p, TYPE) <= a[1]


def test_bootstrap_empty_is_nan():
    lo, hi = M.bootstrap_macro_f1_ci([], [], TYPE, 10)
    assert math.isnan(lo) and math.isnan(hi)


# ---------------------------------------------------------------- calibration
def test_ece_zero_when_calibrated():
    conf = [0.8] * 10
    corr = [True] * 8 + [False] * 2
    assert M.ece(conf, corr, 10, "width")[0] == pytest.approx(0.0)


def test_ece_overconfident():
    e, bins = M.ece([0.95] * 4, [True, False, False, False], 10, "width")
    assert e == pytest.approx(0.70)
    assert sum(b["n"] for b in bins) == 4 and bins[9]["n"] == 4


def test_ece_count_bins_equal_size():
    _, bins = M.ece(np.linspace(0.3, 1, 200), [True] * 200, 10, "count")
    assert [b["n"] for b in bins] == [20] * 10


def test_review_rate():
    assert M.review_rate([0.59, 0.60, 0.9, 0.2]) == 0.5
