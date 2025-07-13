import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


autonomous_path = ROOT / ".overseer" / "autonomous_system.py"
overseer_engine_path = ROOT / ".overseer" / "overseer_engine.py"

autonomous = _load_module("autonomous_system", autonomous_path)
engine_mod = _load_module("overseer_engine", overseer_engine_path)

VersionControl = autonomous.VersionControl
ChangeSet = autonomous.ChangeSet
Domain = autonomous.Domain
Proposal = autonomous.Proposal
OverseerEngine = engine_mod.OverseerEngine


@pytest.fixture()
def patched_version_control(monkeypatch):
    """Patch VersionControl to disable real git interactions."""

    def _noop(*args, **kwargs):
        return True

    monkeypatch.setattr(VersionControl, "stage", _noop)
    monkeypatch.setattr(VersionControl, "commit", _noop)
    monkeypatch.setattr(VersionControl, "revert", lambda *a, **kw: None)


def _create_dummy_proposal(tmp_dir: Path, domain: Domain, content: str = "data") -> Proposal:
    file_path = tmp_dir / f"{domain.value.replace(' ', '_').lower()}.txt"
    return Proposal(
        agent_name=f"Agent-{domain.value}",
        description=f"Dummy change for {domain.value}",
        domain=domain,
        changes=[ChangeSet(file_path=file_path, new_content=content)],
    )


def test_notification_and_conflict_flow(patched_version_control):  # type: ignore[arg-type]
    with TemporaryDirectory() as tmp:
        base_dir = Path(tmp) / "overseer"
        base_dir.mkdir(parents=True, exist_ok=True)

        engine = OverseerEngine(base_dir=base_dir)

        # Submit two proposals touching different domains
        prop1 = _create_dummy_proposal(Path(tmp), Domain.DEPENDENCIES, "dep_v1")
        engine.submit_proposal(prop1)
        engine.handle_command(f"__approve_{prop1.id}")

        notifications = engine.get_notifications()
        assert any("Dependencies" in msg for msg in notifications)

        # Create conflicting proposals (same file)
        file_conflict = Path(tmp) / "conflict.txt"
        prop_a = Proposal(
            agent_name="A",
            description="First change",
            domain=Domain.REFACTOR,
            changes=[ChangeSet(file_path=file_conflict, new_content="A")],
        )
        prop_b = Proposal(
            agent_name="B",
            description="Second change",
            domain=Domain.REFACTOR,
            changes=[ChangeSet(file_path=file_conflict, new_content="B")],
        )

        engine.submit_proposal(prop_a)
        engine.submit_proposal(prop_b)

        # Approve first, should succeed
        ok_a = engine.handle_command(f"__approve_{prop_a.id}")
        assert "approved" in ok_a.lower()

        # Second approval should be blocked due to conflict
        ok_b = engine.handle_command(f"__approve_{prop_b.id}")
        assert "cannot be approved" in ok_b.lower()