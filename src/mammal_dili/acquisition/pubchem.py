from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests

from mammal_dili.config import validate_config
from mammal_dili.io import write_json

SALT_SUFFIXES = re.compile(
    r"\s+(hydrochloride|hydrobromide|sodium|potassium|calcium|magnesium|mesylate|maleate|"
    r"fumarate|tartrate|citrate|phosphate|sulfate|succinate|acetate|lactate|nitrate|besylate|"
    r"tosylate|ditosylate|isethionate|gluconate|palmitate|valerate|estolate|pamoate|"
    r"tromethamine|meglumine|dimeglumine|olamine|hemifumarate|polistirex|monohydrate|"
    r"dimethyl sulfoxide|sodium glycinate|complex)$",
    re.IGNORECASE,
)


def candidate_names(name: str) -> list[tuple[str, str]]:
    candidates = [(name.strip(), "exact-name")]
    stripped = SALT_SUFFIXES.sub("", name.strip())
    if stripped.casefold() != name.strip().casefold():
        candidates.append((stripped, "salt-suffix-fallback"))
    return candidates


def _request_property(
    session: requests.Session,
    endpoint: str,
    name: str,
    timeout: int,
    retries: int,
) -> dict | None:
    url = endpoint.format(name=quote(name, safe=""))
    for attempt in range(retries):
        response = session.get(url, timeout=timeout, headers={"User-Agent": "mammal-dili-research/0.1"})
        if response.status_code == 200:
            properties = response.json()["PropertyTable"]["Properties"]
            if properties:
                exact_titles = [
                    item
                    for item in properties
                    if str(item.get("Title", "")).strip().casefold() == name.strip().casefold()
                ]
                if len(exact_titles) == 1:
                    selected = exact_titles[0]
                    adjudication = "exact-title-among-candidates"
                elif len(properties) == 1:
                    selected = properties[0]
                    adjudication = "unique-pubchem-name-result"
                else:
                    return None
                return {
                    **selected,
                    "_candidate_count": len(properties),
                    "_candidate_cids": [item.get("CID") for item in properties],
                    "_adjudication": adjudication,
                }
        if response.status_code in {400, 404}:
            return None
        if response.status_code not in {429, 500, 502, 503, 504}:
            response.raise_for_status()
        time.sleep(2**attempt)
    return None


def resolve_pubchem(
    input_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
    cache_path: str | Path,
) -> pd.DataFrame:
    source_config = validate_config(config_path)["pubchem"]
    frame = pd.read_csv(input_path)
    frame = frame[frame["outcome"].notna()].copy()
    cache_target = Path(cache_path)
    cache_target.parent.mkdir(parents=True, exist_ok=True)
    cache: dict[str, dict | None] = {}
    if cache_target.exists():
        cache = json.loads(cache_target.read_text(encoding="utf-8"))

    def resolve_one(source: dict) -> tuple[dict, dict[str, dict | None]]:
        resolved = None
        active_moiety = None
        query_used = source["compound_name_source"]
        method = "unresolved"
        additions: dict[str, dict | None] = {}
        with requests.Session() as session:
            candidate_results = []
            for query, candidate_method in candidate_names(source["compound_name_source"]):
                cache_key = query.casefold()
                value = cache.get(cache_key)
                if value is None:
                    value = _request_property(
                    session,
                    source_config["property_endpoint"],
                    query,
                    int(source_config["timeout_seconds"]),
                    int(source_config["retries"]),
                )
                    additions[cache_key] = value
                candidate_results.append((query, candidate_method, value))
            exact = candidate_results[0][2]
            fallback = candidate_results[1][2] if len(candidate_results) > 1 else None
            if exact:
                resolved = exact
                query_used = candidate_results[0][0]
                method = "exact-name"
                active_moiety = fallback
            elif fallback:
                resolved = fallback
                active_moiety = fallback
                query_used = candidate_results[1][0]
                method = "salt-suffix-fallback"
            result = dict(source)
            result.update(
                {
                    "identity_status": "resolved" if resolved else "unresolved",
                    "resolution_method": method,
                    "pubchem_query": query_used,
                    "pubchem_cid": resolved.get("CID") if resolved else None,
                    "pubchem_title": resolved.get("Title") if resolved else None,
                    "original_smiles": (
                        resolved.get("SMILES")
                        or resolved.get("IsomericSMILES")
                        or resolved.get("ConnectivitySMILES")
                    )
                    if resolved
                    else None,
                    "canonical_smiles_source": (
                        resolved.get("ConnectivitySMILES") or resolved.get("CanonicalSMILES")
                    )
                    if resolved
                    else None,
                    "source_inchi": resolved.get("InChI") if resolved else None,
                    "source_inchikey": resolved.get("InChIKey") if resolved else None,
                    "source_formula": resolved.get("MolecularFormula") if resolved else None,
                    "source_molecular_weight": resolved.get("MolecularWeight") if resolved else None,
                    "pubchem_candidate_count": resolved.get("_candidate_count") if resolved else None,
                    "pubchem_candidate_cids": (
                        "|".join(str(value) for value in resolved.get("_candidate_cids", []))
                        if resolved
                        else None
                    ),
                    "identity_adjudication": resolved.get("_adjudication") if resolved else None,
                    "active_moiety_query": candidate_results[1][0] if active_moiety and len(candidate_results) > 1 else None,
                    "active_moiety_cid": active_moiety.get("CID") if active_moiety else None,
                    "active_moiety_title": active_moiety.get("Title") if active_moiety else None,
                    "active_moiety_smiles": (
                        active_moiety.get("SMILES")
                        or active_moiety.get("IsomericSMILES")
                        or active_moiety.get("ConnectivitySMILES")
                    )
                    if active_moiety
                    else None,
                    "active_moiety_inchikey": active_moiety.get("InChIKey") if active_moiety else None,
                    "active_moiety_formula": active_moiety.get("MolecularFormula") if active_moiety else None,
                    "active_moiety_adjudication": (
                        "compound-name-suffix-resolved-to-unique-or-exact-PubChem-active"
                        if active_moiety
                        else None
                    ),
                }
            )
        return result, additions

    rows: list[dict] = []
    records = frame.to_dict(orient="records")
    workers = int(source_config["requests_per_second"])
    for start in range(0, len(records), 50):
        chunk = records[start : start + 50]
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for result, additions in executor.map(resolve_one, chunk):
                rows.append(result)
                cache.update(additions)
        cache_target.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")

    output = pd.DataFrame(rows)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(target, index=False)
    write_json(
        target.with_suffix(".summary.json"),
        {
            "records": len(output),
            "resolved": int((output["identity_status"] == "resolved").sum()),
            "unresolved": int((output["identity_status"] == "unresolved").sum()),
            "resolution_methods": output["resolution_method"].value_counts().to_dict(),
            "licence_url": source_config["licence_url"],
        },
    )
    return output
