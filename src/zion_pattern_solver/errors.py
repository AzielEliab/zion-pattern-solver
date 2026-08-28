"""Engine errors. Local-first; no network."""

from __future__ import annotations


class ZSolverError(Exception):
    """Base error for ZionPattern Solver."""


class CapViolation(ZSolverError):
    """Raised if a caller tries to store uncapped conclusion confidence."""


class TerminationRefused(ZSolverError):
    """Termination is refused (missing ledger, not near cap, or rule miss)."""


class ReceiptError(ZSolverError):
    """Receipt is malformed, uncapped, or hash-invalid."""


class SessionError(ZSolverError):
    """Session is in a bad state for the requested step."""
