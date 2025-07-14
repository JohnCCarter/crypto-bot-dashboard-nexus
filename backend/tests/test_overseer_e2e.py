import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, path: Path):
    try:
        print(f"  Creating spec for {name} from {path}")
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {name} from {path}")
        print(f"  Creating module from spec for {name}")
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]

        # Registrera modulen i sys.modules för att dataclass ska fungera
        import sys

        sys.modules[name] = mod

        print(f"  Executing module {name}")
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        print(f"  Successfully loaded {name}")
        return mod
    except Exception as e:
        print(f"  Error loading {name}: {e}")
        import traceback

        traceback.print_exc()
        pytest.skip(f"Could not load {name} module: {e}", allow_module_level=True)


autonomous_path = ROOT / ".overseer" / "autonomous_system.py"
overseer_engine_path = ROOT / ".overseer" / "overseer_engine.py"

# Skip tests if modules can't be loaded
if not autonomous_path.exists():
    pytest.skip("autonomous_system.py not found", allow_module_level=True)
if not overseer_engine_path.exists():
    pytest.skip("overseer_engine.py not found", allow_module_level=True)

try:
    print(f"Loading autonomous_system from {autonomous_path}")
    autonomous = _load_module("autonomous_system", autonomous_path)

    # Registrera .overseer paketet innan vi laddar overseer_engine
    import sys

    overseer_package = type(sys)(name=".overseer")
    sys.modules[".overseer"] = overseer_package
    overseer_package.autonomous_system = autonomous

    print(f"Loading overseer_engine from {overseer_engine_path}")
    engine_mod = _load_module("overseer_engine", overseer_engine_path)

    VersionControl = autonomous.VersionControl
    ChangeSet = autonomous.ChangeSet
    Domain = autonomous.Domain
    Proposal = autonomous.Proposal
    OverseerEngine = engine_mod.OverseerEngine
    print("Successfully loaded all overseer modules")
except Exception as e:
    print(f"Error loading overseer modules: {e}")
    import traceback

    traceback.print_exc()
    pytest.skip(f"Could not import overseer modules: {e}", allow_module_level=True)


@pytest.fixture()
def patched_version_control(monkeypatch):
    """Patch VersionControl to disable real git interactions."""

    def _noop(*args, **kwargs):
        return True

    monkeypatch.setattr(VersionControl, "stage", _noop)
    monkeypatch.setattr(VersionControl, "commit", _noop)
    monkeypatch.setattr(VersionControl, "revert", lambda *a, **kw: None)

    # Mock run_all_tests to always return True for testing
    monkeypatch.setattr(autonomous, "run_all_tests", lambda: True)
    # Also mock it in the engine module since it imports it directly
    monkeypatch.setattr(engine_mod, "run_all_tests", lambda: True)


def _create_dummy_proposal(
    tmp_dir: Path, domain: Domain, content: str = "data"
) -> Proposal:
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
