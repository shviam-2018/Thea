"""Single source of truth for Solace version information."""

from __future__ import annotations

import re


# Canonical PEP 440 package version. Build metadata reads this exact attribute.
__version__ = "0.2.0a1"

_PRE_RELEASE = re.compile(r"^(?P<release>\d+\.\d+\.\d+)(?P<phase>a|b|rc)(?P<number>\d+)$")
_PHASE_NAMES = {"a": "alpha", "b": "beta", "rc": "rc"}


def display_version(version: str = __version__) -> str:
    """Return the human-readable SemVer spelling of a PEP 440 version."""
    match = _PRE_RELEASE.fullmatch(version)
    if match is None:
        return version
    phase = _PHASE_NAMES[match.group("phase")]
    return f"{match.group('release')}-{phase}.{match.group('number')}"
