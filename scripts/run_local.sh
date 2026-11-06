#!/usr/bin/env bash
# ==============================================================================
# Local Deployment Runner for Hospital Patient Onboarding Agent
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "========================================================================"
echo "🏥 Hospital Patient Onboarding AI System - Local Deployment Mode"
echo "========================================================================"

# Default local environment variables
export SESSION_BACKEND="sqlite"
export SQLITE_DB_PATH="/tmp/patient_onboarding_sessions.db"
export FHIR_BASE_URL="http://localhost:8081/fhir"
export ENABLE_MOCK_EHR="true"
export ENABLE_CONSOLE_TRACING="true"
export GEMINI_API_KEY="${GEMINI_API_KEY:-mock-local-key}"

# Check for mock FHIR server in background if not already running
if ! curl -s --max-time 1 http://localhost:8081/fhir/metadata > /dev/null 2>&1; then
    echo "➜ Starting lightweight local mock HAPI FHIR server on http://localhost:8081/fhir ..."
    python3 scripts/mock_fhir_server.py 8081 > /tmp/mock_hapi_fhir.log 2>&1 &
    FHIR_PID=$!
    echo "  [Started Mock HAPI FHIR server PID: ${FHIR_PID}]"
    sleep 1
else
    echo "➜ Local HAPI FHIR server detected on http://localhost:8081/fhir"
fi

echo ""
echo "Select execution mode:"
echo "  1) Run Standard Outpatient Onboarding Scenario (Interactive CLI)"
echo "  2) Run Emergency Chest Pain Diversion Scenario (Interactive CLI)"
echo "  3) Start Production FastAPI REST Service (Port 8080)"
echo "  4) Run Automated Unit Tests & Evaluation Suite"
echo ""

MODE="${1:-1}"

case "${MODE}" in
    1)
        echo "Executing Standard Outpatient Intake with Conversational Consent..."
        python3 -m src.interfaces.cli_runner --scenario standard
        ;;
    2)
        echo "Executing Emergency Cardiac Diversion Scenario..."
        python3 -m src.interfaces.cli_runner --scenario emergency
        ;;
    3)
        echo "Starting FastAPI Server on http://localhost:8080 ..."
        python3 -m uvicorn src.interfaces.api_server:app --host 0.0.0.0 --port 8080 --reload
        ;;
    4)
        echo "Running pytest test suite..."
        pytest -v tests/
        ;;
    *)
        echo "Unknown mode: ${MODE}. Usage: ./scripts/run_local.sh [1|2|3|4]"
        exit 1
        ;;
esac
