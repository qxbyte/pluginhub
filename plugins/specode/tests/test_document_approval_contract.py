"""Behavior-contract tests for specode's per-document approval gates."""
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SPEC_SKILL = PLUGIN_ROOT / "skills" / "spec" / "SKILL.md"
APPROVAL_REF = PLUGIN_ROOT / "skills" / "spec" / "references" / "document-approval.md"
INTAKE_SKILL = PLUGIN_ROOT / "skills" / "intake" / "SKILL.md"
CONTINUE_SKILL = PLUGIN_ROOT / "skills" / "continue" / "SKILL.md"
EXECUTE_SKILL = PLUGIN_ROOT / "skills" / "execute" / "SKILL.md"
CHANGELOG = PLUGIN_ROOT / "CHANGELOG.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_document_approval_reference_is_canonical_and_blocking():
    text = _read(APPROVAL_REF)
    for value in (
        "requirements.md",
        "design.md",
        "tasks.md",
        "确认并继续",
        "需要修改",
        "immediately end the turn",
        "do not generate the next document in the same turn",
    ):
        assert value in text


def test_spec_pipeline_orders_each_approval_before_the_next_phase():
    text = _read(SPEC_SKILL)
    req_gate = text.index("requirements approval gate")
    design_phase = text.index("3. **design (traditional design doc)**")
    design_gate = text.index("design approval gate")
    tasks_phase = text.index("4. **tasks (executable plan)**")
    tasks_gate = text.index("tasks approval gate")
    execute_phase = text.index("5. **Execution tail")

    assert req_gate < design_phase
    assert design_phase < design_gate < tasks_phase
    assert tasks_phase < tasks_gate < execute_phase


def test_spec_pipeline_forbids_advance_without_explicit_approval():
    text = _read(SPEC_SKILL)
    assert "never infer approval from silence" in text
    assert "must not generate the next document in the same turn" in text
    assert "before tasks.md is explicitly approved" in text
