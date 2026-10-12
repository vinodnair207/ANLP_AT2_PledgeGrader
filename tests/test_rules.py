"""Unit tests for the rule based baseline."""
from src import rules
from src.utils import load_config

POINTS = load_config()["scoring"]


def test_net_zero_full_signals():
    text = ("We will reach net zero by 2040 including Scope 3, limit offsets to residual "
            "emissions, and set an interim target of 50% by 2030.")
    out = rules.score_and_explain(text, POINTS)
    assert out["label"] == "net_zero" and out["score"] == 100


def test_reduction_label():
    assert rules.classify_target("We reduce our emissions by 30% by 2030.") == "reduction"


def test_none_label_scores_zero():
    out = rules.score_and_explain("Our board met on Tuesday.", POINTS)
    assert out["label"] == "none" and out["score"] == 0


def test_missing_signals_are_explained():
    out = rules.score_and_explain("We aim for net zero.", POINTS)
    assert "target year" in out["explanation"] and out["score"] == 0


def test_target_year_requires_target_context():
    signals = rules.detect_signals("Our baseline year is 2020 and the report was published in 2024.")
    assert signals["target_year"] is False


def test_target_year_detects_by_year():
    signals = rules.detect_signals("We will reach net zero by 2050.")
    assert signals["target_year"] is True


def test_scope3_detects_explicit_scope3():
    signals = rules.detect_signals("The target covers Scope 1, Scope 2 and Scope 3 emissions.")
    assert signals["scope3"] is True


def test_scope3_detects_value_chain_coverage():
    signals = rules.detect_signals("We will reduce emissions across our full value chain.")
    assert signals["scope3"] is True


def test_generic_indirect_emissions_do_not_automatically_mean_scope3():
    signals = rules.detect_signals("Indirect emissions are discussed elsewhere in the report.")
    assert signals["scope3"] is False


def test_scope3_detects_scope_lists():
    """Lists of scopes that end in 3 count as Scope 3 coverage (regression for the demo pledge)."""
    for text in (
        "We will reach net zero across Scopes 1, 2 and 3 by 2040.",
        "The target covers Scope 1, 2, and 3 emissions.",
        "The target covers Scopes 1 to 3.",
        "The target covers Scope 1-3 emissions.",
        "The target covers Scope 1, 2 & 3 emissions.",
    ):
        assert rules.detect_signals(text)["scope3"] is True, text


def test_scope3_ignores_scopes_one_and_two_only():
    """A list that stops at Scope 2, or a stray number after it, does not count as Scope 3."""
    for text in (
        "Our goal is to reduce Scope 1 and 2 greenhouse gas emissions by 2030.",
        "Scope 1 and 2 emissions fall 50% and 3 sites close.",
        "We will reduce Scope 2 emissions by 30%.",
    ):
        assert rules.detect_signals(text)["scope3"] is False, text


def test_demo_pledge_scores_one_hundred():
    """The example pledge shown in the app earns all four signals."""
    text = ("We will reach net zero across Scopes 1, 2 and 3 by 2040, with a 50% cut in absolute "
            "emissions by 2030 against a 2020 baseline. Offsets will only be used for residual "
            "emissions, through verified carbon removals.")
    assert rules.score_and_explain(text, POINTS)["score"] == 100


def test_generic_offset_mention_does_not_count_as_offset_use():
    signals = rules.detect_signals("The report discusses carbon offsets and carbon markets.")
    assert signals["offsets"] is False


def test_offset_use_detects_residual_emissions_policy():
    signals = rules.detect_signals("We will use verified carbon removals for residual emissions.")
    assert signals["offsets"] is True


def test_offset_non_use_is_still_an_explained_policy():
    signals = rules.detect_signals("We will reach the target without relying on carbon offsets.")
    assert signals["offsets"] is True


def test_single_final_target_is_not_an_interim_milestone():
    signals = rules.detect_signals("We will reach net zero by 2030.")
    assert signals["target_year"] is True
    assert signals["milestones"] is False


def test_explicit_interim_target_is_a_milestone():
    signals = rules.detect_signals("We set an interim target of a 50% reduction by 2030.")
    assert signals["milestones"] is True


def test_two_dated_targets_imply_an_interim_step():
    text = "We will reduce emissions 50% by 2030 and reach net zero by 2050."
    signals = rules.detect_signals(text)
    assert signals["milestones"] is True

def test_carbon_neutrality_is_net_zero():
    text = "We have committed to achieve carbon neutrality by 2040."
    assert rules.classify_target(text) == "net_zero"


def test_climate_neutrality_is_net_zero():
    text = "Spain must achieve climate neutrality before 2050."
    assert rules.classify_target(text) == "net_zero"


def test_carbon_neutrality_overrides_reduction_label():
    text = (
        "We will reduce greenhouse gas emissions and "
        "achieve carbon neutrality by 2030."
    )
    assert rules.classify_target(text) == "net_zero"


def test_net_greenhouse_gas_neutral_is_net_zero():
    text = "The bank has committed to be net greenhouse gas neutral by 2050."
    assert rules.classify_target(text) == "net_zero"


def test_zero_greenhouse_gas_emissions_is_net_zero():
    text = (
        "We have set a long-term target of zero greenhouse "
        "gas emissions from business activities by 2050."
    )
    assert rules.classify_target(text) == "net_zero"


def test_zero_co2_emissions_is_net_zero():
    text = "We plan to reach zero CO2 emissions by 2038."
    assert rules.classify_target(text) == "net_zero"


def test_real_zero_is_net_zero():
    text = (
        "Our goal is to reduce Scope 1 and 2 greenhouse gas "
        "emissions to real zero by 2050."
    )
    assert rules.classify_target(text) == "net_zero"


def test_emission_neutral_is_net_zero():
    text = "The city will become emission neutral by 2050."
    assert rules.classify_target(text) == "net_zero"


def test_net_neutrality_is_net_zero():
    text = "We aim to achieve net neutrality by 2040."
    assert rules.classify_target(text) == "net_zero"


def test_climate_positive_is_net_zero_style_target():
    text = "Our goal is a fossil-free and climate-positive city by 2040."
    assert rules.classify_target(text) == "net_zero"


def test_parenthesised_net_zero_is_detected():
    text = "We pledge to reach (net)-zero in the 2040s."
    assert rules.classify_target(text) == "net_zero"


def test_neutrality_of_greenhouse_gas_emissions_is_net_zero():
    text = (
        "The objective is to reach and maintain neutrality "
        "of greenhouse gas emissions by the year 2050."
    )
    assert rules.classify_target(text) == "net_zero"


def test_eliminate_co2_emissions_is_net_zero():
    text = "By 2050, we aim to eliminate CO2 emissions from our energy use."
    assert rules.classify_target(text) == "net_zero"


def test_by_the_year_detected_as_target_year():
    signals = rules.detect_signals(
        "We will achieve carbon neutrality by the year 2050."
    )
    assert signals["target_year"] is True

def test_percentage_before_ghg_reduction():
    text = (
        "Guatemala proposes a 22.6% GHG reduction, "
        "conditional on international financial aid."
    )
    assert rules.classify_target(text) == "reduction"


def test_percentage_range_before_reduction():
    text = "30-40% reduction by FY2030 compared to FY2013."
    assert rules.classify_target(text) == "reduction"


def test_emissions_reduction_target():
    text = (
        "Their emissions reduction target is aligned "
        "with the science-based targets initiative."
    )
    assert rules.classify_target(text) == "reduction"


def test_percentage_co2_emissions_reduction_target():
    text = (
        "50% CO2 emissions reduction target "
        "from a FY2019 base year."
    )
    assert rules.classify_target(text) == "reduction"


def test_reduction_in_greenhouse_gases():
    text = (
        "An interim goal for a 30% reduction in "
        "greenhouse gases by 2030."
    )
    assert rules.classify_target(text) == "reduction"


def test_eliminate_percentage_of_emissions():
    text = (
        "The goal is to eliminate 60% of Scope 1 and 2 "
        "emissions and 47% of Scope 3 emissions by 2030."
    )
    assert rules.classify_target(text) == "reduction"


def test_minimise_ghg_emissions():
    text = (
        "Minimize operational GHG emissions by 55% "
        "compared with 2016 levels."
    )
    assert rules.classify_target(text) == "reduction"


def test_carbon_neutral_growth_not_full_net_zero():
    text = (
        "Achieving carbon neutral growth by 2020. "
        "Reducing CO2 emissions by 50% by 2050 "
        "relative to 2005."
    )
    assert rules.classify_target(text) == "reduction"