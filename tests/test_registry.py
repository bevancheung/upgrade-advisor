# -*- coding: utf-8 -*-
import os

import yaml

REG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "registry", "release_graph.yaml")
VALID_TYPES = {"fresh_pretraining", "continuation", "anneal", "soup", "unknown"}
VALID_CONF = {"verified", "inferred", "user_supplied"}


def _load():
    with open(REG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_registry_parses_and_has_edges():
    g = _load()
    assert g["checkpoints"] and g["edges"]


def test_edges_are_well_formed():
    g = _load()
    for e in g["edges"]:
        assert e["type"] in VALID_TYPES, e
        assert e.get("confidence") in VALID_CONF, e
        if e["type"] == "continuation":
            assert e.get("continuation_tokens"), \
                f"continuation edge needs a distance: {e}"
            assert isinstance(e["continuation_tokens"], (int, float)), \
                ("continuation_tokens parsed as string -- write YAML "
                 f"scientific notation with an explicit sign (2.0e+10): {e}")


def test_paper_verified_edges_present():
    g = _load()
    pairs = {(e["source"], e["target"]) for e in g["edges"]}
    assert ("allenai/OLMo-2-1124-7B@stage1-step237000",
            "allenai/OLMo-2-1124-7B@stage1-step248000") in pairs
