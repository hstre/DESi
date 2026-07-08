"""The classifier is measured, not asserted - and the measurement is a pinned regression floor."""
from desi_router import classifier_eval


def test_the_eval_set_is_a_pinned_regression_floor():
    # 100% on the shipped set. Honest scope: the patterns were tuned against this very set, so
    # this pins "no regression", it does NOT claim generalization - the module says so.
    result = classifier_eval.evaluate()
    assert result["n"] >= 30
    assert result["accuracy"] == 1.0
    assert all(v["accuracy"] == 1.0 for v in result["per_class"].values())


def test_hard_negatives_stay_general():
    from desi_router.policy import classify
    assert classify("My meeting is on 2025-03-04 in room 12") == "general"
    assert classify("The recipe needs 2 pounds of flour and 3 eggs") == "general"
    assert classify("The study of 12 patients was published in 2024") == "general"


def test_render_names_misroutes():
    out = classifier_eval.render(classifier_eval.evaluate(
        [("what is 2+2", "math_arithmetic"), ("hello", "math_arithmetic")]))
    assert "accuracy=50%" in out and "general:1" in out
