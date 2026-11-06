# 🏥 Hospital Patient Onboarding AI System (Powered by Google ADK)

An enterprise-grade, clinical and administrative AI agent system designed to streamline, automate, and safeguard the **Patient Onboarding and Intake Process** in hospital networks. Built entirely on the **Google Agent Development Kit (ADK 2.0)** and Google Gemini models, this system bridges the gap between patient self-service, clinical safety triage, real-time insurance verification, and EHR (Electronic Health Record) synchronization.

---

## 🌟 Executive Summary & Capabilities Architecture

```mermaid
flowchart TD
    User([Patient / Kiosk / Web Portal]) -->|Demographics & Consent| IntakeAgent[Patient Identity Agent]
    IntakeAgent -->|MPI Lookup & MRN Assignment| MasterPatientIndex[(Hospital MPI / EHR)]
    
    IntakeAgent -->|Verified Profile| InsuranceAgent[Insurance & Financial Agent]
    InsuranceAgent -->|EDI 270/271 Verification| PayerGateway[Payer Clearinghouse API]
    InsuranceAgent -->|Good Faith Estimate| PatientBilling[Patient Cost Transparency]
    
    InsuranceAgent -->|Verified Benefits| TriageAgent[Clinical Triage Nurse Agent]
    TriageAgent -->|Symptom & Drug Screening| AcuityEngine{ESI Triage Algorithm}
    
    AcuityEngine -->|Red Flag / Emergent ESI 1-2| EmergencyDispatch[Emergency Department Bypass]
    EmergencyDispatch --> UrgentCare[Urgent Care / Trauma Bay 1]
    
    AcuityEngine -->|Routine / Urgent ESI 3-5| SchedulingAgent[Scheduling & Logistics Agent]
    SchedulingAgent --> ClinicSlots[Specialist Clinic Reservation]
    
    UrgentCare --> FHIRNode[FHIR Sync & EHR Ingestion Node]
    ClinicSlots --> FHIRNode
    FHIRNode -->|HL7 FHIR R4 Transaction Bundle| HospitalEHR[(Epic / Cerner / HAPI FHIR)]
```


## 📁 Repository Structure

```
patient_onboarding_adk/
├── README.md                                  # This documentation
├── pyproject.toml                             # Project metadata, dependencies, tool configs
├── requirements.txt                           # Production & dev requirements
├── .env.example                               # Environment variable templates
│
├── config/                                    # Hospital configurations & settings
│   ├── __init__.py
│   ├── settings.py                            # Pydantic BaseSettings
│   └── hospital_departments.json              # Clinic directories, slots, prep instructions
│
├── src/
│   ├── models/                                # Pydantic domain models
│   │   ├── patient.py                         # Demographics, Consent, Emergency Contact
│   │   ├── insurance.py                       # Insurance Policy, Eligibility, Coverage
│   │   ├── clinical.py                        # Triage, AcuityLevel (ESI 1-5), Allergies
│   │   ├── appointment.py                     # Clinic Departments, Booking confirmations
│   │   └── fhir.py                            # HL7 FHIR R4 Bundle schemas
│   │
│   ├── tools/                                 # 1. Tool & Interface Design
│   │   ├── identity_tools.py                  # MPI lookup & registration
│   │   ├── insurance_tools.py                 # Real-time EDI 270/271 eligibility
│   │   ├── clinical_tools.py                  # ESI triage & drug-allergy contraindication checks
│   │   ├── scheduling_tools.py                # Department slot lookup & booking
│   │   ├── fhir_tools.py                      # HL7 FHIR R4 bundle generator
│   │   └── confirmation_guard.py              # Human-in-the-Loop guardrails
│   │
│   ├── memory/                                # 2. Context & Memory
│   │   ├── state_manager.py                   # Multi-scope state (session, user, app, temp)
│   │   ├── session_service.py                 # Persistent session management (SQLite/Firestore)
│   │   └── clinical_memory.py                 # Longitudinal episodic patient memory
│   │
│   ├── agents/                                # 3. Multi-Agent Hierarchy
│   │   ├── coordinator.py                     # Root Onboarding Coordinator Agent
│   │   ├── intake_agent.py                    # Demographics & HIPAA agent
│   │   ├── insurance_agent.py                 # Payer verification agent
│   │   ├── triage_agent.py                    # Clinical acuity & nurse agent
│   │   └── scheduling_agent.py                # Logistics & slot booking agent
│   │
│   ├── workflow/                              # Graph Orchestration
│   │   ├── onboarding_workflow.py             # ADK Workflow graph & routing
│   │   └── routes.py                          # Conditional route definitions
│   │
│   ├── observability/                         # 4. Observability & Tracing
│   │   ├── tracer.py                          # OpenTelemetry & ADK AutoTracingPlugin
│   │   ├── hipaa_sanitizer.py                 # PII/PHI redaction filter
│   │   ├── audit_logger.py                    # HIPAA Security Rule audit logging
│   │   └── metrics.py                         # Intake funnel KPI metrics tracker
│   │
│   └── interfaces/                            # Interfaces
│       ├── cli_runner.py                      # Interactive CLI terminal runner
│       └── api_server.py                      # Production FastAPI REST service
│
├── tests/                                     # Automated Test Suite
│   ├── conftest.py                            # Test fixtures & mock patients
│   ├── test_tools.py                          # Unit tests for tools
│   ├── test_memory.py                         # Unit tests for state & memory
│   ├── test_workflow.py                       # Integration tests for ADK graph
│   ├── test_observability.py                  # Tests for PHI redaction & audit logger
│   └── test_evaluation.py                     # Automated evaluation against evalset.json
│
├── evals/                                     # ADK Evaluation Benchmarks
│   ├── evalset.json                           # Golden clinical test scenarios
│   └── eval_criteria.json                     # Clinical safety & HIPAA evaluation rubric
│
└── infra/                                     # 5. Infrastructure & CI/CD
    ├── Dockerfile                             # Multi-stage production container
    ├── docker-compose.yml                     # Local stack (Agent + HAPI FHIR + Jaeger)
    ├── cloudrun-service.yaml                  # Google Cloud Run deployment manifest
    ├── cloudbuild.yaml                        # Google Cloud Build pipeline
    └── terraform/                             # Cloud Infrastructure as Code (GCP)
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

---

## ⚡ Local Deployment & Quickstart Guide

This project is pre-configured for **Local Deployment** using:
- **SQLite Session Persistence** (`/tmp/patient_onboarding_sessions.db`)
- **Local Mock HAPI FHIR R4 Integration** (`http://localhost:8081/fhir`)
- **Standard Conversational Consent** (Verbal intake verification)

### Option A: One-Click Local Runner (`scripts/run_local.sh`)
Execute the pre-configured local runner script:
```bash
cd patient_onboarding_adk
./scripts/run_local.sh 1   # Standard Outpatient Intake (CLI)
./scripts/run_local.sh 2   # Emergency Chest Pain Diversion (CLI)
./scripts/run_local.sh 3   # Start FastAPI Server (Port 8080)
./scripts/run_local.sh 4   # Run Pytest Test Suite
```

### Option B: Local Mock HAPI FHIR Server
To test real HTTP FHIR R4 ingestion without external dependencies or Docker:
```bash
python3 scripts/mock_fhir_server.py 8081
```
Or with Docker Compose:
```bash
docker compose -f infra/docker-compose.yml up hapi-fhir
```

### 1. Installation
Ensure Python 3.11+ is installed. Clone or navigate to the repository:

```bash
cd patient_onboarding_adk
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` (pre-configured for local mode):

```bash
cp .env.example .env
```

### 3. Run Interactive CLI Demonstration
Execute the ADK CLI runner to simulate patient onboarding:

**Scenario A: Routine Outpatient Intake (Orthopedics with Conversational Consent)**
```bash
python -m src.interfaces.cli_runner --scenario standard
```

**Scenario B: Emergent Red-Flag Diversion (Acute Chest Pain -> Emergency Care)**
```bash
python -m src.interfaces.cli_runner --scenario emergency
```

### 4. Start the FastAPI REST API Server
```bash
uvicorn src.interfaces.api_server:app --host 0.0.0.0 --port 8080 --reload
```
- Interactive Swagger UI: `http://localhost:8080/docs`
- Health check probe: `http://localhost:8080/health`
- Intake metrics summary: `http://localhost:8080/api/v1/metrics`

### 5. Run the Automated Test Suite & Evaluations
```bash
pytest -v tests/
```

---

## 🗣️ Standard Conversational Consent Mechanics

Under modern hospital intake workflows, patients frequently provide consent via conversational verbal dialogue rather than rigid e-signatures:
1. **Dialogue Prompt**: The agent presents the hospital's Notice of Privacy Practices and asks:
   > *"Do you acknowledge our Notice of Privacy Practices and give verbal consent for examination and hospital care?"*
2. **Natural Language Affirmation**: The [`evaluate_conversational_consent`](src/tools/confirmation_guard.py) engine evaluates patient statements:
   - **Affirmative**: *"Yes"*, *"I agree"*, *"I consent"*, *"Sure"*, *"Proceed"*, *"Sounds good"*.
   - **Declined**: *"No"*, *"I decline"*, *"I don't consent"*, *"Stop"*.
3. **Audit Immutability**: The accepted verbal affirmation text, ISO-8601 UTC timestamp, and `consent_mode="CONVERSATIONAL_VERBAL"` are recorded into the patient's EHR profile and logged via the HIPAA Audit Logger under HIPAA Security Rule 164.312(b).

---

## 🔒 Security, HIPAA Compliance & Clinical Safety

1. **Strict PHI Redaction**: All outbound trace spans, logging statements, and metric tags pass through `redact_phi_text` and `sanitize_phi_dict`, preventing Social Security Numbers, phone numbers, and full names from entering third-party logging sinks.
2. **Deterministic Triage Safety Net**: Life-threatening clinical conditions (e.g., myocardial infarction symptoms, acute respiratory distress, acute anaphylaxis) bypass LLM generation and are deterministically routed to Emergency Care via graph edges.
3. **No Surprises Act Compliance**: Out-of-pocket cost calculations provide transparent Good Faith Estimates for insured and self-pay patients prior to treatment.
4. **HL7 FHIR Interoperability**: Generates atomic FHIR R4 Transaction Bundles ready for direct ingestion by major hospital EHR systems (Epic Systems, Oracle Cerner, Meditech).
