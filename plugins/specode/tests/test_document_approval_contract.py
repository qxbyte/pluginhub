"""Behavior-contract tests for specode's per-document approval gates."""
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SPEC_SKILL = PLUGIN_ROOT / "skills" / "spec" / "SKILL.md"
APPROVAL_REF = PLUGIN_ROOT / "skills" / "spec" / "references" / "document-approval.md"
SUPERPOWERS_WIRING = PLUGIN_ROOT / "skills" / "spec" / "references" / "superpowers-wiring.md"
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
    assert "once design.md is produced (by it or by you), proceed into the tasks phase (step 4)" not in text
    assert "and continue to Flow step 5 (invoke `specode:execute`)" not in text


def test_superpowers_wiring_blocks_brainstorming_handoff_until_design_approval():
    text = _read(SUPERPOWERS_WIRING)
    assert "let it flow naturally into the tasks phase" not in text
    assert "Only after the user explicitly approves `design.md` may the pipeline enter the tasks phase." in text


def test_intake_returns_to_requirements_approval_instead_of_design():
    text = _read(INTAKE_SKILL)
    assert "waiting for requirements approval" in text
    assert "which proceeds into the design phase" not in text
    assert "next action (entering design)" not in text


def test_continue_uses_go_ahead_as_latest_document_approval():
    text = _read(CONTINUE_SKILL)
    assert "explicitly approves the latest planning document" in text
    assert "Modification requests are not approval" in text
    assert "present the document approval gate again" in text


def test_execute_distinguishes_pipeline_and_manual_authorization():
    text = _read(EXECUTE_SKILL)
    assert "Pipeline entry requires an explicitly approved `tasks.md`" in text
    assert "Manual entry is explicit approval" in text


def test_changelog_records_document_approval_regression():
    unreleased = _read(CHANGELOG).split("## 6.5.1", 1)[0]
    for value in (
        "文档审批门",
        "v6.1.2",
        "specode:intake",
        "旧 brainstorming 提供的 approval gate 未被完整迁移",
        "requirements.md",
        "design.md",
        "tasks.md",
        "各自落盘后必须停轮等待明确确认",
        "/specode:continue",
        "跨会话批准语义",
        "不新增持久状态",
    ):
        assert value in unreleased
