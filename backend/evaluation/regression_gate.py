"""Regression gate — fails if retrieval quality drops below baseline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GateResult:
    passed: bool
    regressions: tuple[str, ...] = ()


class RegressionGate:

    def __init__(
        self,
        precision_tolerance: float = 0.05,
        recall_tolerance: float = 0.05,
        latency_tolerance: float = 0.50,
    ):
        self._prec_tol = precision_tolerance
        self._rec_tol = recall_tolerance
        self._lat_tol = latency_tolerance

    def check(
        self,
        baseline: dict[str, float],
        current: dict[str, float],
    ) -> GateResult:
        regressions: list[str] = []

        bp = baseline.get("precision", 0)
        cp = current.get("precision", 0)
        if bp > 0 and (bp - cp) / bp > self._prec_tol:
            regressions.append(f"Precision dropped: {bp:.3f} → {cp:.3f}")

        br = baseline.get("recall", 0)
        cr = current.get("recall", 0)
        if br > 0 and (br - cr) / br > self._rec_tol:
            regressions.append(f"Recall dropped: {br:.3f} → {cr:.3f}")

        bl = baseline.get("latency_p99", 0)
        cl = current.get("latency_p99", 0)
        if bl > 0 and (cl - bl) / bl > self._lat_tol:
            regressions.append(f"Latency p99 increased: {bl:.1f}ms → {cl:.1f}ms")

        return GateResult(
            passed=len(regressions) == 0,
            regressions=tuple(regressions),
        )
