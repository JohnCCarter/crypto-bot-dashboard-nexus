"""overseer_engine.py – Core command handling & state machine for AI Overseer 🌐.

This module is INTERNAL. It must never expose sensitive data to the user. It operates
entirely within the `.overseer` workspace folder, persisting minimal metadata such as
log snapshots and archive files.
"""
from __future__ import annotations

import datetime as _dt
import re as _re
import shutil as _shutil
from enum import Enum, auto
from pathlib import Path

_LOG_FILE = Path(__file__).with_name("Overseer_Log.md")
_SPEC_FILE = Path(__file__).with_name("Command_Handling_Spec.md")
_ARCHIVE_DIR = Path(__file__).parent.joinpath("archive")


class _State(Enum):
    IDLE = auto()
    ALIGNMENT = auto()
    ANALYSIS = auto()
    BRAINSTORM = auto()
    AWAIT_FEEDBACK = auto()
    FINALIZATION = auto()
    ARCHIVED = auto()


class OverseerEngine:
    """Stateful engine responsible for processing slash commands."""

    VERSION_PATTERN = _re.compile(r"Version (\d+)\.(\d+)")

    def __init__(self) -> None:
        self.state: _State = _State.IDLE
        self.major: int = 0
        self.minor: int = 0
        self._load_version()
        # ensure archive dir exists
        _ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def handle_command(self, raw: str) -> str:
        """Process a raw user command string and return a user-facing response."""
        cmd, *payload_parts = raw.strip().split(" ", 1)
        payload: str = payload_parts[0] if payload_parts else ""

        cmd_lower = cmd.lower()
        if cmd_lower == "/initiate":
            return self._cmd_initiate()
        if cmd_lower == "/brainstorm":
            return self._cmd_brainstorm()
        if cmd_lower == "/feedback":
            return self._cmd_feedback(payload)
        if cmd_lower == "/finalize":
            return self._cmd_finalize()
        if cmd_lower == "/reset":
            return self._cmd_reset()
        return self._help_text()

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------
    def _cmd_initiate(self) -> str:
        if self.state != _State.IDLE:
            return "Initiation already completed. Use /reset if you need a fresh session."
        self.state = _State.ALIGNMENT
        self._bump_minor()
        self._append_to_log("## Version {}.{} – Alignment\n\n**Date:** {}\n\n---\n\nInitiation confirmed. Preparing for analysis phase.".format(self.major, self.minor, _today()))
        self.state = _State.ANALYSIS
        return "Initialization acknowledged. Analysis phase has begun."

    def _cmd_brainstorm(self) -> str:
        if self.state not in (_State.ANALYSIS, _State.AWAIT_FEEDBACK):
            return "Cannot brainstorm in current state."
        self.state = _State.BRAINSTORM
        self._bump_minor()
        self._append_to_log("### Brainstorm Notes (v{}.{}).\n\n_Agent brainstorming session initiated._".format(self.major, self.minor))
        # After brainstorming, transition back to analysis
        self.state = _State.ANALYSIS
        return "Brainstorming in progress."

    def _cmd_feedback(self, feedback: str) -> str:
        if not feedback:
            return "Please provide feedback text after the /feedback command."
        self._bump_minor()
        section = ("### Feedback Integration (v{}.{}).\n\n**User Feedback:**\n\n> {}\n\n_Agents will adjust scopes accordingly._".format(self.major, self.minor, feedback.replace("\n", "\n> ")))
        self._append_to_log(section)
        self.state = _State.ANALYSIS
        return "Feedback processed and integrated."

    def _cmd_finalize(self) -> str:
        if self.state == _State.ARCHIVED:
            return "Session already finalized. Start /reset for new session."
        # Collate sanitized findings (for now just copy but could process)
        snapshot_path = _ARCHIVE_DIR / f"Overseer_Log_v{self.major}.{self.minor}.md"
        _shutil.copy(_LOG_FILE, snapshot_path)
        self.state = _State.ARCHIVED
        return "Final report prepared. Presenting consolidated summary...\n\n" + self._generate_user_summary()

    def _cmd_reset(self) -> str:
        # Archive current log with timestamp then clear
        timestamp = _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        if _LOG_FILE.exists():
            _shutil.move(_LOG_FILE, _ARCHIVE_DIR / f"Overseer_Log_reset_{timestamp}.md")
        self.major += 1
        self.minor = 0
        self.state = _State.IDLE
        # Recreate blank log
        _LOG_FILE.write_text("# Overseer Log\n\n## Version {}.0 – Reset\n\n**Date:** {}\n\n---\n".format(self.major, _today()), encoding="utf-8")
        return "Overseer state has been reset."

    # ------------------------------------------------------------------
    def _bump_minor(self) -> None:
        self.minor += 1

    def _append_to_log(self, text: str) -> None:
        with _LOG_FILE.open("a", encoding="utf-8") as fp:
            fp.write("\n\n" + text + "\n")

    def _load_version(self) -> None:
        if not _LOG_FILE.exists():
            self.major = 0
            self.minor = 0
            return
        with _LOG_FILE.open("r", encoding="utf-8") as fp:
            for line in fp:
                m = self.VERSION_PATTERN.search(line)
                if m:
                    self.major, self.minor = int(m.group(1)), int(m.group(2))
                    break

    def _generate_user_summary(self) -> str:
        """Produce sanitized report from Overseer_Log.md."""
        # Extremely simple sanitizer: strip any lines starting with '>' (internal notes)
        lines = _LOG_FILE.read_text("utf-8").splitlines()
        public_lines: list[str] = []
        for ln in lines:
            if ln.lstrip().startswith("#"):
                public_lines.append(ln)
            elif ln.startswith("- ") or ln.startswith("1.") or ln.startswith("*"):
                public_lines.append(ln)
            elif ln.startswith("### "):
                public_lines.append(ln)
        return "\n".join(public_lines)

    @staticmethod
    def _help_text() -> str:
        return (
            "Unrecognized command. Available commands: /initiate, /brainstorm, /feedback <text>, /finalize, /reset."
        )


def _today() -> str:  # helper
    return _dt.datetime.utcnow().date().isoformat()