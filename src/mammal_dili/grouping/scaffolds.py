from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.ML.Cluster import Butina
from sklearn.model_selection import StratifiedGroupKFold

from mammal_dili.config import validate_config
from mammal_dili.io import write_json


def assign_scaffold_groups(smiles_values: list[str], similarity_threshold: float) -> list[str]:
    groups: list[str | None] = []
    acyclic_indices: list[int] = []
    acyclic_molecules = []
    for index, smiles in enumerate(smiles_values):
        molecule = Chem.MolFromSmiles(smiles)
        scaffold = MurckoScaffold.GetScaffoldForMol(molecule)
        scaffold_smiles = Chem.MolToSmiles(scaffold, canonical=True, isomericSmiles=False)
        if scaffold_smiles:
            groups.append(f"scaffold:{scaffold_smiles}")
        else:
            groups.append(None)
            acyclic_indices.append(index)
            acyclic_molecules.append(molecule)
    if acyclic_molecules:
        generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
        fingerprints = [generator.GetFingerprint(molecule) for molecule in acyclic_molecules]
        distances = []
        for i in range(1, len(fingerprints)):
            similarities = DataStructs.BulkTanimotoSimilarity(fingerprints[i], fingerprints[:i])
            distances.extend(1 - similarity for similarity in similarities)
        clusters = Butina.ClusterData(
            distances,
            len(fingerprints),
            1 - similarity_threshold,
            isDistData=True,
        )
        for cluster_number, cluster_members in enumerate(clusters):
            for member in cluster_members:
                groups[acyclic_indices[member]] = f"acyclic:{cluster_number:04d}"
    return [str(group) for group in groups]


def build_groups_and_folds(
    cohort_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
) -> pd.DataFrame:
    config = validate_config(config_path)
    frame = pd.read_csv(cohort_path)
    frame = frame[frame["eligibility"]].copy().reset_index(drop=True)
    frame["scaffold_id"] = assign_scaffold_groups(
        frame["standardised_isomeric_smiles"].tolist(),
        float(config["acyclic_similarity_threshold"]),
    )
    for repeat, seed in enumerate(config["seeds"]):
        splitter = StratifiedGroupKFold(
            n_splits=int(config["outer_folds"]),
            shuffle=True,
            random_state=int(seed),
        )
        fold_values = np.full(len(frame), -1, dtype=int)
        for fold, (_, test_indices) in enumerate(
            splitter.split(frame, frame["outcome"].astype(int), groups=frame["scaffold_id"])
        ):
            if frame.iloc[test_indices]["outcome"].nunique() != 2:
                raise ValueError(f"Repeat {repeat} fold {fold} does not contain both outcome classes")
            fold_values[test_indices] = fold
        frame[f"outer_fold_repeat_{repeat}"] = fold_values
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(target, index=False)
    group_fold_pairs = frame.melt(
        id_vars=["scaffold_id"],
        value_vars=[column for column in frame if column.startswith("outer_fold_repeat_")],
    ).drop_duplicates()
    if group_fold_pairs.duplicated(["scaffold_id", "variable"]).any():
        raise AssertionError("A scaffold group was split within a repeat")
    write_json(
        target.with_suffix(".summary.json"),
        {
            "eligible_drugs": len(frame),
            "groups": frame["scaffold_id"].nunique(),
            "largest_group": int(frame["scaffold_id"].value_counts().max()),
            "acyclic_drugs": int(frame["scaffold_id"].str.startswith("acyclic:").sum()),
            "repeats": len(config["seeds"]),
            "folds": int(config["outer_folds"]),
        },
    )
    return frame
