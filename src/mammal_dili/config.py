from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from mammal_dili.io import load_yaml, sha256_json


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DilirankSource(StrictModel):
    canonical_url: str
    snapshot_path: str
    snapshot_transport: str
    expected_records: int
    expected_labels: dict[str, int]
    licence: str


class PubChemSource(StrictModel):
    property_endpoint: str
    requests_per_second: int
    timeout_seconds: int
    retries: int
    licence_url: str


class SourcesConfig(StrictModel):
    schema_version: Literal[1]
    dilirank: DilirankSource
    pubchem: PubChemSource


class ParentOverride(StrictModel):
    name: str
    pubchem_cid: int
    formula: str
    isomeric_smiles: str
    justification: str


class CurationConfig(StrictModel):
    schema_version: Literal[1]
    outcome_include: list[str]
    positive_labels: list[str]
    negative_labels: list[str]
    parent_selection: str
    preserve_stereochemistry: bool
    tautomer_canonicalization: bool
    max_molecular_weight: float
    max_heavy_atoms: int
    peptide_min_amide_bonds: int
    peptide_min_molecular_weight: float
    duplicate_policy: str
    review_fraction: float
    exclusion_codes: list[str]
    manual_exclusions: dict[str, str]
    manual_parent_overrides: dict[str, ParentOverride]


class MammalConfig(StrictModel):
    schema_version: Literal[1]
    checkpoint: str
    checkpoint_revision: str
    code_repository: str
    code_revision: str
    prompt_prefix: str
    prompt_suffix: str
    hidden_state: str
    pooling: str
    special_tokens: str
    max_sequence_length: int
    overlength_rule: str
    dtype: str
    device: str
    batch_size: int
    repeatability_atol: float
    repeatability_rtol: float
    pilot_required_successes: int
    pilot_total: int
    full_cohort_minimum_coverage: float
    failure_codes: list[str]


class FingerprintConfig(StrictModel):
    type: Literal["Morgan"]
    radius: int
    bits: int
    chirality: bool


class FeaturesConfig(StrictModel):
    schema_version: Literal[1]
    descriptors: list[str]
    fingerprint: FingerprintConfig


class FoldsConfig(StrictModel):
    schema_version: Literal[1]
    outer_folds: int
    inner_folds: int
    repeats: int
    scaffold: str
    acyclic_grouping: str
    acyclic_similarity_threshold: float
    seeds: list[int]


class AnalysisConfig(StrictModel):
    schema_version: Literal[1]
    models: dict[str, list[str]]
    classifier: str
    solver: str
    max_iterations: int
    regularization_grid: list[float]
    class_weight: str | None
    primary_metric: str
    primary_contrast: str
    practical_gain: float
    threshold: str
    sensitivity_target: float
    bootstrap_resamples: int
    bootstrap_seed: int


class SeedsConfig(StrictModel):
    schema_version: Literal[1]
    cohort_review_sample: int
    outer_fold_repeats: list[int]
    inner_cv_base: int
    classifier: int
    group_bootstrap: int
    negative_control: int
    label_permutation: int


CONFIG_MODELS = {
    "sources.yaml": SourcesConfig,
    "curation.yaml": CurationConfig,
    "mammal_embedding.yaml": MammalConfig,
    "features.yaml": FeaturesConfig,
    "folds.yaml": FoldsConfig,
    "analysis.yaml": AnalysisConfig,
    "seeds.yaml": SeedsConfig,
}


def validate_config(path: str | Path) -> dict:
    target = Path(path)
    model = CONFIG_MODELS.get(target.name)
    if model is None:
        raise ValueError(f"No registered schema for {target.name}")
    return model.model_validate(load_yaml(target)).model_dump(mode="json")


def validate_config_bundle(directory: str | Path = "configs") -> tuple[dict[str, dict], str]:
    bundle = {
        name: validate_config(Path(directory) / name)
        for name in sorted(CONFIG_MODELS)
    }
    return bundle, sha256_json(bundle)
