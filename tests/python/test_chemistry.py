import numpy as np

from mammal_dili.chemistry.features import molecule_features
from mammal_dili.curation.structures import curate_smiles
from mammal_dili.grouping.scaffolds import assign_scaffold_groups

CONFIG = {
    "max_molecular_weight": 2000,
    "max_heavy_atoms": 160,
    "peptide_min_amide_bonds": 6,
    "peptide_min_molecular_weight": 700,
}


def test_parent_selection_collapses_sodium_counterion() -> None:
    acid = curate_smiles("CC(=O)O", CONFIG)
    salt = curate_smiles("CC(=O)[O-].[Na+]", CONFIG)
    assert acid["eligibility"] is True
    assert salt["eligibility"] is True
    assert acid["parent_inchikey"] == salt["parent_inchikey"]


def test_invalid_structure_is_excluded_with_code() -> None:
    result = curate_smiles("not-a-smiles", CONFIG)
    assert result == {"eligibility": False, "exclusion_code": "STRUCTURE_PARSE_FAILURE"}


def test_carbon_free_inorganic_entity_is_excluded() -> None:
    result = curate_smiles("[Cu+2]", CONFIG)
    assert result == {
        "eligibility": False,
        "exclusion_code": "POLYMER_OR_UNRESOLVED_INORGANIC",
    }


def test_calcium_acetate_is_not_collapsed_to_acetic_acid() -> None:
    result = curate_smiles("CC(=O)[O-].CC(=O)[O-].[Ca+2]", CONFIG)
    assert result["eligibility"] is False
    assert result["curation_flags"] == "METAL_WITH_MULTIPLE_ORGANIC_FRAGMENTS"


def test_large_peptide_is_excluded_even_under_size_ceiling() -> None:
    peptide = "NCC(=O)NCC(=O)NCC(=O)NCC(=O)NCC(=O)NCC(=O)N" + "C" * 45
    result = curate_smiles(peptide, CONFIG)
    assert result["eligibility"] is False
    assert result["exclusion_code"] == "BIOLOGIC_OR_MACROMOLECULE"


def test_features_are_fixed_and_deterministic() -> None:
    names = ["MolWt", "MolLogP", "TPSA"]
    first_descriptors, first_bits = molecule_features("CCO", names, 2, 2048)
    second_descriptors, second_bits = molecule_features("CCO", names, 2, 2048)
    assert first_descriptors == second_descriptors
    assert first_bits.shape == (2048,)
    assert np.array_equal(first_bits, second_bits)


def test_same_ring_scaffold_stays_in_one_group() -> None:
    groups = assign_scaffold_groups(["Cc1ccccc1", "Oc1ccccc1", "CCO", "CCCO"], 0.5)
    assert groups[0] == groups[1]
    assert groups[2].startswith("acyclic:")
    assert groups[3].startswith("acyclic:")
