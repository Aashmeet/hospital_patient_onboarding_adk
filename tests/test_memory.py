"""Unit tests for ADK State Scopes, Memory, and Session persistence."""

import pytest
from src.memory.state_manager import HealthcareStateManager
from src.memory.clinical_memory import LongitudinalPatientMemory
from src.memory.session_service import get_session_service


def test_initial_state_generation():
    state = HealthcareStateManager.create_initial_state(
        hospital_name="St. Jude Memorial",
        hospital_id="HOSP-01"
    )
    assert state["app:hospital_name"] == "St. Jude Memorial"
    assert state["current_step"] == "IDENTITY_VERIFICATION"
    assert state["is_emergency"] is False


def test_state_actions_promotion():
    action = HealthcareStateManager.set_user_demographics(
        mrn="MRN-887766",
        name="Eleanor Vance",
        dob="1982-08-14",
        allergies=["Penicillin"]
    )
    delta = action.state_delta
    assert delta["user:mrn"] == "MRN-887766"
    assert delta["user:allergies"] == ["Penicillin"]
    assert delta["patient_mrn"] == "MRN-887766"


def test_temp_state_sanitization():
    dirty_state = {
        "app:hospital_id": "HOSP-01",
        "user:mrn": "MRN-1234",
        "temp:ocr_cache": "base64_blob_here",
        "temp:scratchpad": "scratch_calc"
    }
    cleaned = HealthcareStateManager.sanitize_for_storage(dirty_state)
    assert "temp:ocr_cache" not in cleaned
    assert "temp:scratchpad" not in cleaned
    assert "user:mrn" in cleaned


def test_longitudinal_clinical_memory():
    mem = LongitudinalPatientMemory()
    mem.record_episode(
        mrn="MRN-TEST-99",
        category="Allergy",
        summary="Documented Penicillin allergy with hives",
        details={"allergen": "Penicillin", "reaction": "Hives"}
    )
    mem.record_episode(
        mrn="MRN-TEST-99",
        category="Encounter",
        summary="Emergency intake for acute chest pain",
        details={"department": "dept_urgent_care"}
    )

    history = mem.retrieve_patient_history("MRN-TEST-99")
    assert len(history) == 2

    allergies = mem.query_recent_allergies("MRN-TEST-99")
    assert "Penicillin" in allergies


@pytest.mark.asyncio
async def test_session_lifecycle():
    service = get_session_service(backend_type="memory")
    session = await service.create_session(
        app_name="hospital_test",
        user_id="user_test_1",
        state={"app:test_key": "val_1"}
    )
    assert session.session_id is not None
    assert session.state["app:test_key"] == "val_1"

    retrieved = await service.get_session(
        app_name="hospital_test",
        user_id="user_test_1",
        session_id=session.session_id
    )
    assert retrieved.state["app:test_key"] == "val_1"
