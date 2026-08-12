from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdFingerprintGenerator, rdMolDescriptors

from mammal_dili.config import validate_config
from mammal_dili.io import sha256_file, write_json

DESCRIPTOR_FUNCTIONS = {
    "MolWt": Descriptors.MolWt,
    "MolLogP": Crippen.MolLogP,
    "TPSA": rdMolDescriptors.CalcTPSA,
    "NumHDonors": Lipinski.NumHDonors,
    "NumHAcceptors": Lipinski.NumHAcceptors,
    "NumRotatableBonds": Lipinski.NumRotatableBonds,
    "RingCount": Lipinski.RingCount,
    "FormalCharge": Chem.GetFormalCharge,
    "FractionCSP3": rdMolDescriptors.CalcFractionCSP3,
}


def molecule_features(smiles: str, descriptor_names: list[str], radius: int, bits: int) -> tuple[list[float], np.ndarray]:
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"Invalid curated SMILES: {smiles}")
    descriptors = [float(DESCRIPTOR_FUNCTIONS[name](molecule)) for name in descriptor_names]
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=radius,
        fpSize=bits,
        includeChirality=True,
    )
    fingerprint = np.asarray(generator.GetFingerprintAsNumPy(molecule), dtype=np.uint8)
    return descriptors, fingerprint


def build_conventional_features(
    cohort_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
) -> Path:
    config = validate_config(config_path)
    frame = pd.read_csv(cohort_path)
    frame = frame[frame["eligibility"]].reset_index(drop=True)
    names = config["descriptors"]
    fp_config = config["fingerprint"]
    descriptor_rows = []
    fingerprint_rows = []
    for smiles in frame["standardised_isomeric_smiles"]:
        descriptors, fingerprint = molecule_features(
            smiles, names, int(fp_config["radius"]), int(fp_config["bits"])
        )
        descriptor_rows.append(descriptors)
        fingerprint_rows.append(fingerprint)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        target,
        drug_ids=frame["drug_id"].to_numpy(dtype=str),
        descriptors=np.asarray(descriptor_rows, dtype=np.float64),
        morgan=np.asarray(fingerprint_rows, dtype=np.uint8),
        descriptor_names=np.asarray(names, dtype=str),
    )
    write_json(
        target.with_suffix(".manifest.json"),
        {
            "rows": len(frame),
            "descriptor_dimension": len(names),
            "fingerprint_dimension": int(fp_config["bits"]),
            "source_cohort_sha256": sha256_file(cohort_path),
            "output_sha256": sha256_file(target),
        },
    )
    return target
