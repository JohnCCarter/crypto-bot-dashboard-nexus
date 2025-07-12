"""autonomous_system.py – Internal autonomous action workflow implementation.

This module defines the data structures and helper managers used by expert
agents to submit proposals, for Overseer to validate, and to apply changes
with testing & version control hooks. All operations remain internal;
no user-facing exposure is done here.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List

# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

class ProposalStatus(Enum):
    DRAFT = auto()
    UNDER_REVIEW = auto()
    APPROVED = auto()
    REJECTED = auto()
    APPLIED = auto()
    FAILED = auto()


@dataclass
class ChangeSet:
    """Represents an atomic modification to a single file.

    The system currently supports *replace* operations where the entire file
    content is replaced with ``new_content``. Future modes (unified diff patch)
    can be added as needed.
    """

    file_path: Path
    new_content: str  # full replacement text for the file


@dataclass
class Proposal:
    """Container for an expert agent's proposed change or refactor."""

    agent_name: str
    description: str
    changes: List[ChangeSet] = field(default_factory=list)
    tests_to_run: List[str] = field(default_factory=list)
    id: int | None = None
    status: ProposalStatus = ProposalStatus.DRAFT


# ---------------------------------------------------------------------------
# Proposal Management
# ---------------------------------------------------------------------------

class ProposalManager:
    """Manages lifecycle of agent proposals."""

    def __init__(self) -> None:
        self._proposals: list[Proposal] = []
        self._next_id: int = 1

    # ------------------------ public interface ---------------------------
    def submit(self, proposal: Proposal) -> Proposal:
        """Register a new proposal from an agent."""
        proposal.id = self._next_id
        self._next_id += 1
        proposal.status = ProposalStatus.UNDER_REVIEW
        self._proposals.append(proposal)
        return proposal

    def list_pending(self) -> list[Proposal]:
        return [p for p in self._proposals if p.status == ProposalStatus.UNDER_REVIEW]

    def approve(self, pid: int) -> bool:
        prop = self._get(pid)
        if prop and prop.status == ProposalStatus.UNDER_REVIEW:
            # conflict detection
            conflicts = self.detect_conflicts(prop)
            if conflicts:
                # keep under review; decision postponed
                prop.description += (
                    "\n\n[Blocked] Conflicts with proposal(s): "
                    + ", ".join(str(c.id) for c in conflicts)
                )
                return False
            prop.status = ProposalStatus.APPROVED
            return True
        return False

    def reject(self, pid: int, reason: str | None = None) -> bool:
        prop = self._get(pid)
        if prop and prop.status == ProposalStatus.UNDER_REVIEW:
            prop.status = ProposalStatus.REJECTED
            if reason:
                prop.description += f"\n\n[Rejection Reason] {reason}"
            return True
        return False

    def get(self, pid: int) -> Proposal | None:
        return self._get(pid)

    # ------------------------ conflict detection ---------------------------
    def detect_conflicts(self, target: Proposal) -> list[Proposal]:
        """Return proposals that touch the same files as *target*."""
        target_files = {cs.file_path for cs in target.changes}
        conflicts: list[Proposal] = []
        for p in self._proposals:
            if p.id == target.id or p.status in {ProposalStatus.REJECTED}:
                continue
            other_files = {cs.file_path for cs in p.changes}
            if target_files & other_files:
                conflicts.append(p)
        return conflicts

    # ------------------------ internals ---------------------------
    def _get(self, pid: int) -> Proposal | None:  # noqa: D401
        """Internal: retrieve proposal by id."""
        return next((p for p in self._proposals if p.id == pid), None)


# ---------------------------------------------------------------------------
# Testing Helper
# ---------------------------------------------------------------------------

def run_backend_tests() -> bool:
    """Run backend optimized tests and return success boolean."""
    try:
        result = subprocess.run(
            [
                "python",
                "scripts/testing/run_tests_optimized.py",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        # Fallback to standard pytest
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "-v",
                "--maxfail=10",
            ],
            check=False,
        )
        return result.returncode == 0


def run_frontend_tests() -> bool:
    """Run frontend test suite using npm/vitest; return success bool."""
    result = subprocess.run([
        "npm",
        "test",
        "--silent",
    ], check=False)
    return result.returncode == 0


def run_all_tests() -> bool:
    """Run both backend and frontend tests, short-circuit on first failure."""
    return run_backend_tests() and run_frontend_tests()


###############################################################################
# Version Control Integration (Git wrapper)
###############################################################################


class VersionControl:
    """Lightweight Git wrapper for staging, committing, and reverting changes.

    All operations are best-effort; if the repository is not a Git repo or Git
    is unavailable, the class will act as a no-op to avoid breaking workflow.
    """

    def __init__(self) -> None:
        # Detect git root lazily
        self._root = self._detect_git_root()

    # ------------------------------------------------------------------
    def stage(self, file_paths: list[Path]) -> bool:
        if not self._root:
            return True
        try:
            subprocess.run(["git", "add", *[str(p) for p in file_paths]], check=True)
            return True
        except Exception:
            return False

    def commit(self, message: str) -> bool:
        if not self._root:
            return True
        try:
            subprocess.run(["git", "commit", "-m", message, "--no-verify"], check=True)
            return True
        except Exception:
            return False

    def revert(self, file_paths: list[Path]) -> None:
        if not self._root:
            return
        subprocess.run(["git", "checkout", "--", *[str(p) for p in file_paths]], check=False)

    # ------------------------------------------------------------------
    @staticmethod
    def _detect_git_root() -> Path | None:
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / ".git").exists():
                return parent
        return None