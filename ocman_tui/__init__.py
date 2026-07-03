"""
ocman_tui — Modern, unified TUI for ocman database administration and session recovery.
"""

# Single-source the version from the ocman CLI module so the CLI and TUI never
# drift. Fall back to a literal only if ocman cannot be imported.
try:
    from ocman import __version__ as __version__
except Exception:  # pragma: no cover - defensive fallback
    __version__ = "1.0.3"

__all__ = ["OrsessionApp"]

from .app import OrsessionApp
