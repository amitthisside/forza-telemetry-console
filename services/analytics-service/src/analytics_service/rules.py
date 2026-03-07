from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CoachingMessage(BaseModel):
    rule_id: str
    message: str
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)


class SessionSignalSnapshot(BaseModel):
    brake_release_variance: float = 0.0
    rear_slip_events: int = 0
    early_throttle_pct: float = 0.0
    exit_speed_delta_kmh: float = 0.0


class DiagnosticSignal(BaseModel):
    diagnostic_type: str
    summary: str
    score: float



def evaluate_coaching(snapshot: SessionSignalSnapshot) -> list[CoachingMessage]:
    messages: list[CoachingMessage] = []

    if snapshot.brake_release_variance > 0.35:
        messages.append(
            CoachingMessage(
                rule_id="brake-release-consistency",
                message="Inconsistent brake release across similar zones",
                severity=Severity.MEDIUM,
                confidence=0.78,
            )
        )

    if snapshot.rear_slip_events >= 3 and snapshot.early_throttle_pct > 0.45:
        messages.append(
            CoachingMessage(
                rule_id="early-throttle-rear-slip",
                message="Early throttle application is causing rear slip",
                severity=Severity.HIGH,
                confidence=0.86,
            )
        )

    if snapshot.exit_speed_delta_kmh < -6.0:
        messages.append(
            CoachingMessage(
                rule_id="low-exit-speed",
                message="Reduced exit speed compared to best lap trace",
                severity=Severity.MEDIUM,
                confidence=0.74,
            )
        )

    return messages



def evaluate_diagnostics(snapshot: SessionSignalSnapshot) -> list[DiagnosticSignal]:
    diagnostics: list[DiagnosticSignal] = []

    if snapshot.rear_slip_events >= 3:
        diagnostics.append(
            DiagnosticSignal(
                diagnostic_type="suspected_oversteer_trend",
                summary="Rear traction instability appears repeatedly",
                score=min(1.0, 0.2 * snapshot.rear_slip_events),
            )
        )

    if snapshot.exit_speed_delta_kmh < -4.0:
        diagnostics.append(
            DiagnosticSignal(
                diagnostic_type="traction_instability",
                summary="Exit speed deficit suggests traction loss on corner exits",
                score=min(1.0, abs(snapshot.exit_speed_delta_kmh) / 20.0),
            )
        )

    return diagnostics
