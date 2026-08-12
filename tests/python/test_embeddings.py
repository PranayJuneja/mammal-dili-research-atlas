from mammal_dili.embeddings.mammal import make_prompt


def test_prompt_contract_is_byte_explicit() -> None:
    config = {
        "prompt_prefix": "<@TOKENIZER-TYPE=SMILES><MOLECULAR_ENTITY><MOLECULAR_ENTITY_OF_TYPE_SMALL_MOL>",
        "prompt_suffix": "<EOS>",
    }
    assert make_prompt("CCO", config) == (
        "<@TOKENIZER-TYPE=SMILES><MOLECULAR_ENTITY>"
        "<MOLECULAR_ENTITY_OF_TYPE_SMALL_MOL>CCO<EOS>"
    )

