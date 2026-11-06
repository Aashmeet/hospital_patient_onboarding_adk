"""FastAPI REST Service exposing ADK Patient Onboarding endpoints."""

from typing import Any, Dict
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from google.adk import Runner
from ..workflow.onboarding_workflow import create_patient_onboarding_workflow
from ..memory.session_service import get_session_service
from ..observability.audit_logger import HIPAAClinicalAuditLogger
from ..observability.metrics import metrics_tracker
from ...config.settings import settings

app = FastAPI(
    title="Hospital Patient Onboarding API (ADK)",
    description="Enterprise AI-powered Patient Intake and Triage Service built on Google Agent Development Kit",
    version="1.0.0",
)

# Cross-Origin Resource Sharing for patient mobile app and web portal
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Monitoring"])
async def health_check() -> Dict[str, str]:
    """Liveness and readiness probe for Cloud Run and Kubernetes."""
    return {"status": "HEALTHY", "hospital": settings.hospital_name, "version": "1.0.0"}


@app.get("/api/v1/metrics", tags=["Observability"])
async def get_funnel_metrics() -> Dict[str, Any]:
    """Retrieve operational KPIs and intake funnel telemetry."""
    return metrics_tracker.get_summary()


@app.post("/api/v1/onboard/submit", status_code=status.HTTP_200_OK, tags=["Onboarding"])
async def submit_patient_onboarding(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process patient registration, insurance verification, clinical triage, and scheduling.

    Args:
        payload: JSON object containing demographics, consent, insurance, and clinical details.

    Returns:
        Final onboarding summary with MRN, assigned appointment, and HL7 FHIR bundle ID.
    """
    if "demographics" not in payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing required 'demographics' object in payload."
        )

    metrics_tracker.record_start()
    session_service = get_session_service()
    workflow = create_patient_onboarding_workflow()
    runner = Runner(agent=workflow, session_service=session_service)

    user_id = f"api_user_{payload.get('demographics', {}).get('first_name', 'anon').lower()}"
    session = await session_service.create_session(
        app_name="hospital_onboarding_api",
        user_id=user_id,
        state={"api_payload": payload},
    )

    HIPAAClinicalAuditLogger.log_event(
        event_type="API_ONBOARDING_REQUEST",
        actor_id=user_id,
        patient_mrn=None,
        action="POST /api/v1/onboard/submit",
    )

    final_result = None
    async for event in runner.run_async(session=session, node_input=payload):
        if event.output:
            final_result = event.output

    if not final_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Workflow completed without generating final onboarding output."
        )

    booking = final_result.get("booking", {})
    metrics_tracker.record_completion(
        department_id=booking.get("department_id", "unknown"),
        acuity=str(final_result.get("triage_acuity", "Unknown")),
    )

    return final_result


def run() -> None:
    """Run uvicorn server for local development."""
    import uvicorn
    uvicorn.run("src.interfaces.api_server:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    run()
