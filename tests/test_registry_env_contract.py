"""Every documented AET setting is checked by Doctor for each template."""
import pytest

from aet_scaffolder.generator import generate
from aet_scaffolder.registry import SUPPORTED_TEMPLATES, get_template
from aet_scaffolder.validator import validate_project


@pytest.mark.parametrize("template", SUPPORTED_TEMPLATES)
def test_registry_matches_complete_generated_environment_contract(tmp_path, template):
    project = generate("env-contract", output_dir=tmp_path, template=template)
    documented = {
        line.split("=", 1)[0] + "="
        for line in (project / ".env.example").read_text(encoding="utf-8").splitlines()
        if line.startswith("AET_")
    }
    profile = set(get_template(template).required_env_fields)
    assert len(profile) == len(get_template(template).required_env_fields)
    assert profile == documented, (
        f"Doctor config drift for {template}: "
        f"undocumented={profile - documented}, unchecked={documented - profile}"
    )
    assert validate_project(project).ok


@pytest.mark.parametrize("template", SUPPORTED_TEMPLATES)
def test_doctor_rejects_any_missing_provider_field(tmp_path, template):
    project = generate("missing-field", output_dir=tmp_path, template=template)
    example = project / ".env.example"
    original = example.read_text(encoding="utf-8")
    for key in get_template(template).required_env_fields:
        example.write_text("\n".join(
            line for line in original.splitlines() if not line.startswith(key)
        ) + "\n", encoding="utf-8")
        report = validate_project(project)
        assert not report.ok, f"{template} failed to reject missing {key}"
        assert any(
            check.name == "sample_configuration" and not check.passed
            for check in report.checks
        ), (template, key)
    example.write_text(original, encoding="utf-8")
    assert validate_project(project).ok
