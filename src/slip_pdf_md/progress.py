"""Human-facing progress so a lawyer can see percent complete."""

from __future__ import annotations

from collections.abc import Callable

ProgressFn = Callable[[float, str], None]


def emit(fraction: float, message: str) -> None:
    pct = max(0.0, min(100.0, fraction * 100.0))
    print(f"  [{pct:5.1f}%] {message}", flush=True)


def make_file_progress(index: int, total: int) -> ProgressFn:
    """Map 0..1 inside one file onto the batch (index is 1-based)."""
    if total <= 0:
        total = 1
    span = 1.0 / total
    base = (index - 1) * span

    def _inner(fraction: float, message: str) -> None:
        overall = base + max(0.0, min(1.0, fraction)) * span
        emit(overall, f"file {index}/{total} · {message}")

    return _inner
