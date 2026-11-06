"""Integration tests for the ADK Graph-Based Patient Onboarding Workflow."""

import pytest
from google.adk import Runner
from src.workflow.onboarding_workflow import create_patient_onboarding_workflow
from src.memory.session_service import get_session_service


@pytest.mark.asyncio
async def test_standard_onboarding_workflow(mock_standard_patient):
    """Test full execution of standard non-emergent patient onboarding."""
    workflow = create_patient_onboarding_workflow()
    session_service = get_session_service(backend_type="memory")
    runner = Runner(agent=workflow, session_service=session_service)

    session = await session_service.create_session(
        app_name="hospital_test_app",
        user_id="user_eleanor",
        state={"initial": True}
    )

    events = []
    final_output = None
    async for event in runner.run_async(session=session, node_input=mock_standard_patient):
        events.append(event)
        if event.output:
            final_output = event.output

    assert final_output is not None
    assert final_output["status"] == "COMPLETED"
    assert final_output["mrn"].startswith("MRN-")
    assert "ESI-3" in final_output["triage_acuity"] or "ESI-4" in final_output["triage_acuity"]
    assert final_output["booking"]["booking_status"] == "CONFIRMED"
    assert final_output["fhir_bundle_id"].startswith("bundle-onboard-")


@pytest.mark.asyncio
async def test_emergency_diversion_workflow(mock_emergency_patient):
    """Test workflow diversion when clinical emergency red flags are detected."""
    workflow = create_patient_onboarding_workflow()
    session_service = get_session_service(backend_type="memory")
    runner = Runner(agent=workflow, session_service=session_service)

    session = await session_service.create_session(
        app_name="hospital_test_app",
        user_id="user_marcus",
        state={"initial": True}
    )

    final_output = None
    async for event in runner.run_async(session=session, node_input=mock_emergency_patient):
        if event.output:
            final_output = event.output

    assert final_output is not None
    assert final_output["status"] == "COMPLETED"
    assert "ESI-1" in final_output["triage_acuity"] or "ESI-2" in final_output["triage_acuity"]
    assert final_output["booking"]["booking_status"] == "ESCALATED_EMERGENCY"
    assert final_output["booking"]["department_id"] == "dept_urgent_care"
