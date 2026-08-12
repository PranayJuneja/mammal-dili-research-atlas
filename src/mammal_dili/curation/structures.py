from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem.MolStandardize import rdMolStandardize

from mammal_dili.config import validate_config
from mammal_dili.io import write_json


def curate_smiles(smiles: str | None, config: dict) -> dict:
    if not isinstance(smiles, str) or not smiles.strip():
        return {"eligibility": False, "exclusion_code": "STRUCTURE_UNAVAILABLE"}
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        return {"eligibility": False, "exclusion_code": "STRUCTURE_PARSE_FAILURE"}
    fragments = Chem.GetMolFrags(molecule, asMols=True, sanitizeFrags=True)
    organic_fragments = [fragment for fragment in fragments if any(atom.GetAtomicNum() == 6 for atom in fragment.GetAtoms())]
    metal_atomic_numbers = {3, 4, 11, 12, 13, 19, 20, 26, 29, 30}
    has_metal = any(atom.GetAtomicNum() in metal_atomic_numbers for atom in molecule.GetAtoms())
    if has_metal and len(organic_fragments) > 1:
        return {
            "eligibility": False,
            "exclusion_code": "POLYMER_OR_UNRESOLVED_INORGANIC",
            "curation_flags": "METAL_WITH_MULTIPLE_ORGANIC_FRAGMENTS",
        }
    try:
        parent = rdMolStandardize.FragmentParent(molecule)
        parent = rdMolStandardize.Uncharger().uncharge(parent)
        Chem.SanitizeMol(parent)
    except (RuntimeError, ValueError):
        return {"eligibility": False, "exclusion_code": "STRUCTURE_PARSE_FAILURE"}
    if parent.GetNumHeavyAtoms() == 0:
        return {"eligibility": False, "exclusion_code": "POLYMER_OR_UNRESOLVED_INORGANIC"}
    if not any(atom.GetAtomicNum() == 6 for atom in parent.GetAtoms()):
        return {"eligibility": False, "exclusion_code": "POLYMER_OR_UNRESOLVED_INORGANIC"}
    molecular_weight = float(Descriptors.MolWt(parent))
    if molecular_weight > float(config["max_molecular_weight"]) or parent.GetNumHeavyAtoms() > int(
        config["max_heavy_atoms"]
    ):
        return {
            "eligibility": False,
            "exclusion_code": "BIOLOGIC_OR_MACROMOLECULE",
            "curated_molecular_weight": molecular_weight,
            "curated_heavy_atoms": parent.GetNumHeavyAtoms(),
        }
    amide_bonds = int(Chem.rdMolDescriptors.CalcNumAmideBonds(parent))
    if amide_bonds >= int(config["peptide_min_amide_bonds"]) and molecular_weight >= float(
        config["peptide_min_molecular_weight"]
    ):
        return {
            "eligibility": False,
            "exclusion_code": "BIOLOGIC_OR_MACROMOLECULE",
            "curation_flags": "PEPTIDE_OR_PEPTIDOMIMETIC_RULE",
            "curated_molecular_weight": molecular_weight,
            "curated_heavy_atoms": parent.GetNumHeavyAtoms(),
            "curated_amide_bonds": amide_bonds,
        }
    isomeric = Chem.MolToSmiles(parent, canonical=True, isomericSmiles=True)
    return {
        "eligibility": True,
        "exclusion_code": None,
        "standardised_isomeric_smiles": isomeric,
        "parent_inchikey": Chem.MolToInchiKey(parent),
        "curated_formula": Chem.rdMolDescriptors.CalcMolFormula(parent),
        "curated_molecular_weight": molecular_weight,
        "curated_heavy_atoms": parent.GetNumHeavyAtoms(),
        "curated_amide_bonds": amide_bonds,
        "curation_flags": "SALT_OR_MULTICOMPONENT_SOURCE" if "." in smiles else "",
    }


def _resolve_duplicates(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    eligible = frame[frame["eligibility"]].copy()
    for _, group in eligible.groupby("parent_inchikey", dropna=True):
        if len(group) < 2:
            continue
        indices = list(group.index)
        if group["outcome"].nunique() > 1:
            frame.loc[indices, "eligibility"] = False
            frame.loc[indices, "exclusion_code"] = "DUPLICATE_LABEL_CONFLICT"
            continue
        keeper = group.sort_values("dilirank_id").index[0]
        duplicates = [index for index in indices if index != keeper]
        frame.loc[duplicates, "eligibility"] = False
        frame.loc[duplicates, "exclusion_code"] = "DUPLICATE_PARENT"
    return frame


def curate_cohort(input_path: str | Path, config_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    config = validate_config(config_path)
    frame = pd.read_csv(input_path)
    decisions = []
    for row in frame.to_dict(orient="records"):
        manual_reason = config["manual_exclusions"].get(row["dilirank_id"])
        manual_parent = config["manual_parent_overrides"].get(row["dilirank_id"])
        if manual_reason:
            decisions.append(
                {
                    "eligibility": False,
                    "exclusion_code": manual_reason.split(":", 1)[0],
                    "curation_flags": f"MANUAL_REVIEW:{manual_reason}",
                }
            )
        elif manual_parent:
            decision = curate_smiles(manual_parent["isomeric_smiles"], config)
            decision.update(
                {
                    "curation_flags": "MANUAL_ACTIVE_MOIETY_OVERRIDE",
                    "active_moiety_cid": manual_parent["pubchem_cid"],
                    "active_moiety_formula": manual_parent["formula"],
                    "active_moiety_adjudication": manual_parent["justification"],
                }
            )
            decisions.append(decision)
        elif row.get("identity_status") != "resolved":
            name = str(row.get("compound_name_source", "")).casefold()
            if any(token in name for token in ("ivermectin", "simethicone-cellulose")):
                code = "MIXTURE_OR_COMBINATION"
            elif any(
                token in name
                for token in (
                    "alfa", "interferon", "toxin", "ase", "mab", "filgrastim", "somatropin",
                    "pancrelipase", "urokinase", "pegcetacoplan", "defibrotide", "protein",
                    "secretin", "dermatan", "protamine", "enoxaparin", "dalteparin", "porfimer",
                    "glatiramer", "sargramostim", "oprelvekin", "etanercept", "anakinra",
                    "palifermin", "abatacept", "rilonacept", "romiplostim", "casimersen",
                    "eteplirsen", "givosiran", "golodirsen", "inclisiran", "lumasiran",
                    "nusinersen", "patisiran", "viltolarsen",
                )
            ):
                code = "BIOLOGIC_OR_MACROMOLECULE"
            elif any(
                token in name
                for token in (
                    "poly", "ferumox", "sevelamer", "hetastarch", "technetium", "radium",
                    "patiromer", "sucralfate",
                )
            ):
                code = "POLYMER_OR_UNRESOLVED_INORGANIC"
            else:
                code = "IDENTITY_UNRESOLVED"
            decisions.append({"eligibility": False, "exclusion_code": code})
        else:
            active_smiles = row.get("active_moiety_smiles")
            has_active_smiles = isinstance(active_smiles, str) and bool(active_smiles.strip())
            chosen_smiles = active_smiles if has_active_smiles else row.get("original_smiles")
            decision = curate_smiles(chosen_smiles, config)
            if has_active_smiles:
                decision["curation_flags"] = "PUBCHEM_ACTIVE_MOIETY_SUFFIX_ADJUDICATION"
            decisions.append(decision)
    curated = pd.concat([frame.reset_index(drop=True), pd.DataFrame(decisions)], axis=1)
    curated = _resolve_duplicates(curated)
    curated["drug_id"] = curated["dilirank_id"]
    curated["review_status"] = "rules-applied-pending-independent-review"
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    curated.to_csv(target, index=False)
    write_json(
        target.with_suffix(".summary.json"),
        {
            "considered": len(curated),
            "eligible": int(curated["eligibility"].sum()),
            "excluded": int((~curated["eligibility"]).sum()),
            "exclusions": curated.loc[~curated["eligibility"], "exclusion_code"].value_counts().to_dict(),
            "eligible_outcomes": curated.loc[curated["eligibility"], "dili_category"].value_counts().to_dict(),
            "human_review_required": True,
        },
    )
    return curated


def create_review_packets(
    cohort_path: str | Path,
    curation_config_path: str | Path,
    seeds_config_path: str | Path,
    output_directory: str | Path,
) -> dict:
    config = validate_config(curation_config_path)
    seeds = validate_config(seeds_config_path)
    frame = pd.read_csv(cohort_path)
    evidence_columns = [
        "drug_id",
        "compound_name_source",
        "dili_category",
        "identity_status",
        "resolution_method",
        "pubchem_query",
        "pubchem_cid",
        "pubchem_title",
        "source_formula",
        "source_molecular_weight",
        "pubchem_candidate_count",
        "identity_adjudication",
        "original_smiles",
        "standardised_isomeric_smiles",
        "parent_inchikey",
        "curated_formula",
        "curated_molecular_weight",
        "curated_heavy_atoms",
        "curated_amide_bonds",
        "curation_flags",
        "eligibility",
        "exclusion_code",
        "review_status",
    ]
    columns = [column for column in evidence_columns if column in frame.columns]
    exclusions = frame.loc[~frame["eligibility"].astype(bool), columns].copy()
    eligible = frame.loc[frame["eligibility"].astype(bool), columns].copy()
    sample_size = max(1, int(np.ceil(len(eligible) * float(config["review_fraction"]))))
    routine = eligible.sample(n=sample_size, random_state=int(seeds["cohort_review_sample"])).sort_values(
        "drug_id"
    )
    target = Path(output_directory)
    target.mkdir(parents=True, exist_ok=True)
    exclusions.to_csv(target / "all_exclusions.csv", index=False)
    routine.to_csv(target / "routine_inclusions_10pct.csv", index=False)
    summary = {
        "status": "AWAITING_INDEPENDENT_VALIDATOR_REVIEW",
        "all_exclusions_rows": len(exclusions),
        "routine_inclusion_population": len(eligible),
        "routine_inclusion_sample_rows": len(routine),
        "routine_inclusion_fraction": float(config["review_fraction"]),
        "sampling_seed": int(seeds["cohort_review_sample"]),
        "review_instructions": (
            "Confirm identity, active-moiety choice, eligibility and exclusion code for every exclusion; "
            "apply the same checks to every routine inclusion sample row. Record disagreements explicitly."
        ),
    }
    write_json(target / "review_packet_manifest.json", summary)
    return summary
