"""Unit tests for choosing where the ClimateBERT weights are loaded from."""
import logging

from src import model


def make_cfg(output_dir, hub_repo=None, hub_revision=None):
    """Builds the minimal configuration used by the model loader."""
    settings = {"output_dir": str(output_dir), "max_length": 128}
    if hub_repo:
        settings["hub_repo"] = hub_repo
        settings["hub_revision"] = hub_revision
    return {"climatebert": settings, "scoring": {"target_year": 25, "scope3": 25, "offsets": 25, "milestones": 25}}


def test_a_local_folder_is_preferred_over_the_hub(tmp_path):
    cfg = make_cfg(tmp_path, hub_repo="owner/repo", hub_revision="abc1234")
    assert model.resolve_model_source(cfg) == (str(tmp_path), None)


def test_the_hub_repository_and_pinned_revision_are_used_without_a_local_folder(tmp_path):
    cfg = make_cfg(tmp_path / "missing", hub_repo="owner/repo", hub_revision="abc1234")
    assert model.resolve_model_source(cfg) == ("owner/repo", "abc1234")


def test_no_source_is_reported_when_nothing_is_configured(tmp_path):
    assert model.resolve_model_source(make_cfg(tmp_path / "missing")) is None


def test_get_arms_skips_climatebert_when_there_is_no_source(tmp_path):
    arms = model.get_arms(make_cfg(tmp_path / "missing"), ("rules", "climatebert"))
    assert list(arms) == ["rules"]


def test_get_arms_logs_a_warning_and_keeps_rules_when_the_hub_load_fails(tmp_path, monkeypatch, caplog):
    def broken(self, cfg):
        raise OSError("repository not reachable")

    monkeypatch.setattr(model.ClimateBertArm, "__init__", broken)
    cfg = make_cfg(tmp_path / "missing", hub_repo="owner/repo", hub_revision="abc1234")
    with caplog.at_level(logging.WARNING):
        arms = model.get_arms(cfg, ("rules", "climatebert"))
    assert list(arms) == ["rules"]
    assert "ClimateBERT unavailable" in caplog.text
