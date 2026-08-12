from mammal_dili.statistics.estimate import _interpret


def test_locked_interpretation_regions_cover_gain_and_inconclusive_cases() -> None:
    assert _interpret(0.031, 0.08, 0.03)[0] == "meaningful_gain"
    assert _interpret(-0.01, 0.05, 0.03)[0] == "inconclusive"
    assert _interpret(-0.08, -0.01, 0.03)[0] == "worse"
    assert _interpret(0.001, 0.02, 0.03)[0] == "important_gain_excluded"
