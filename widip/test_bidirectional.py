
import pytest
from nx_yaml import nx_compose_all, nx_serialize_all
from widip.loader import hif_to_markov, markov_to_hif
from discopy.markov import Hypergraph, Diagram
from nx_hif.hif import hif_nodes

# Helper to load YAML string to nx_hif
def load_hif(yaml_str):
    return nx_compose_all(yaml_str)

def test_roundtrip_simple():
    # Simple scalar test case
    yaml_str = "x"

    hif_original = load_hif(yaml_str)

    # 1. hif -> markov
    markov_hg = hif_to_markov(hif_original)
    assert isinstance(markov_hg, Hypergraph)

    # 2. markov -> hif
    hif_new = markov_to_hif(markov_hg)

    # Verify we can serialize back to YAML
    try:
        yaml_out = nx_serialize_all(hif_new)
        print(f"Serialized YAML: {yaml_out}")
        # Note: formatting might differ, but content should be roughly "x"
        assert "x" in yaml_out
    except Exception as e:
        pytest.fail(f"Serialization failed: {e}")

def test_hello_world_file():
    with open("examples/hello-world.yaml", "r") as f:
        hif_original = nx_compose_all(f)

    markov_hg = hif_to_markov(hif_original)
    hif_new = markov_to_hif(markov_hg)

    # Verify serialization
    try:
        yaml_out = nx_serialize_all(hif_new)
        assert len(yaml_out) > 0
    except Exception as e:
        pytest.fail(f"Serialization failed: {e}")
