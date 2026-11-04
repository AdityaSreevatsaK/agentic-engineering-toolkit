"""Guard enumeration of the provider support contract used by the matrix."""
from aet_scaffolder.generator import SUPPORTED_PROVIDERS
from aet_scaffolder.registry import SUPPORTED_TEMPLATES, get_template
from scripts.comprehensive_matrix import supported_pairs


def test_matrix_covers_all_declared_template_provider_pairs():
    pairs = supported_pairs()
    assert len(pairs) == 23
    assert len(set(pairs)) == len(pairs)
    assert {template for template, _ in pairs} == set(SUPPORTED_TEMPLATES)
    for template in SUPPORTED_TEMPLATES:
        assert {provider for t, provider in pairs if t == template} == set(
            get_template(template).providers
        )


def test_matrix_includes_only_supported_provider_modes():
    assert set(provider for _, provider in supported_pairs()) <= set(
        SUPPORTED_PROVIDERS
    )
    assert ("strands-agent", "ollama") not in supported_pairs()
