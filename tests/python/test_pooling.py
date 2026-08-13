import pytest

torch = pytest.importorskip("torch")

from mammal_dili.embeddings.mammal import masked_mean_l2


def test_masked_pooling_ignores_padding_and_normalises() -> None:
    hidden = torch.tensor([[[3.0, 0.0], [0.0, 4.0], [100.0, 100.0]]])
    mask = torch.tensor([[1, 1, 0]])
    result = masked_mean_l2(hidden, mask, torch)
    expected = torch.tensor([[0.6, 0.8]])
    assert torch.allclose(result, expected)
