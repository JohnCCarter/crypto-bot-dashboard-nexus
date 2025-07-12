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
    """Represents an atomic modification to a single file."""

    file_path: Path
    patch: str  # unified diff or replacement text


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

    # ------------------------ internals ---------------------------
    def _get(self, pid: int) -> Proposal | None:
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