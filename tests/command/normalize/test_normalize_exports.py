from kmap import model
from kmap.command import normalize


def test_normalize_reexports_model_normalize_architecture():
    assert normalize.__all__ == ["normalize_architecture"]
    assert normalize.normalize_architecture is model.normalize_architecture
