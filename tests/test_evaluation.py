"""Automated evaluation runner validating evalset cases against criteria."""

import json
from pathlib import Path
import pytest
from google.adk import Runner
from src.workflow.onboarding_workflow import create_patient_onboarding_workflow
from src.memory.session_service import get_session_service

EVALSET_PATH = Path(__file__).resolve().parent.parent / "evals" / "evalset.json"


@pytest.mark.asyncio
async def test_evalset_cases():
    """Execute all golden test cases defined in evalset.json and assert criteria pass."""
    assert EVALSET_PATH.exists(), f"Missing evalset file at {EVALSET_PATH}"

    with open(EVALSET_PATH, "r", encoding="utf-8") as f:
        eval_cases = json.load(f)

    session_service = get_session_service(backend_type="memory")
    workflow = create_patient_onboarding_workflow()
    runner = Runner(agent=workflow, session_service=session_service)

    for case in eval_cases:
        eval_id = case["eval_id"]
        patient_input = case["input"]
        expected = case["expected_outcome"]

        session = await session_service.create_session(
            app_name="hospital_eval",
            user_id=f"eval_user_{eval_id}",
            state={"eval_id": eval_id}
        )

        final_result = None
        async for event in runner.run_async(session=session, node_input=patient_input):
            if event.output:
                final_result = event.output

        assert final_result is not None, f"Eval case {eval_id} produced no output"
        assert final_result["status"] == expected["expected_status"], f"Eval case {eval_id} failed status check"

        # Check emergency routing criteria
        if "is_emergency" in expected:
            if expected["is_emergency"]:
                assert final_result["booking"]["booking_status"] == "ESCALATED_EMERGENCY"
                assert final_result["booking"]["department_id"] == "dept_urgent_care"
            else:
                assert final_result["booking"]["booking_status"] == "CONFIRMED"
                assert final_result["booking"]["department_id"] == expected["recommended_department"]
