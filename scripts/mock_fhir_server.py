"""Pure-Python Local Mock HAPI FHIR R4 Server.

Runs without Docker or external dependencies on port 8081.
Provides FHIR R4 Bundle transaction ingestion and resource inspection.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import uuid
import datetime

FHIR_STORE = {
    "Patient": {},
    "Coverage": {},
    "Encounter": {},
    "Bundle": {}
}


class MockHapiFhirHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/fhir+json; charset=utf-8")
        self.send_header("X-Powered-By", "Mock-HAPI-FHIR-R4-Server")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")

        if path in ["/fhir/metadata", "/metadata"]:
            # CapabilityStatement
            cap = {
                "resourceType": "CapabilityStatement",
                "status": "active",
                "date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "publisher": "Mock HAPI FHIR Core",
                "kind": "instance",
                "fhirVersion": "4.0.1",
                "format": ["application/fhir+json", "application/json"],
                "rest": [{"mode": "server"}]
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(cap, indent=2).encode("utf-8"))
            return

        # Query resource: /fhir/Patient/123
        parts = [p for p in path.split("/") if p and p != "fhir"]
        if len(parts) == 2:
            res_type, res_id = parts[0], parts[1]
            if res_type in FHIR_STORE and res_id in FHIR_STORE[res_type]:
                self._set_headers(200)
                self.wfile.write(json.dumps(FHIR_STORE[res_type][res_id], indent=2).encode("utf-8"))
                return
            else:
                self._set_headers(404)
                err = {"resourceType": "OperationOutcome", "issue": [{"severity": "error", "diagnostics": f"Resource {res_type}/{res_id} not found"}]}
                self.wfile.write(json.dumps(err).encode("utf-8"))
                return

        # Resource collection listing
        if len(parts) == 1 and parts[0] in FHIR_STORE:
            res_type = parts[0]
            bundle = {
                "resourceType": "Bundle",
                "type": "searchset",
                "total": len(FHIR_STORE[res_type]),
                "entry": [{"resource": v} for v in FHIR_STORE[res_type].values()]
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(bundle, indent=2).encode("utf-8"))
            return

        self._set_headers(200)
        status_info = {
            "server": "Mock HAPI FHIR R4 Service",
            "status": "RUNNING",
            "stored_patients": len(FHIR_STORE["Patient"]),
            "stored_encounters": len(FHIR_STORE["Encounter"]),
            "stored_bundles": len(FHIR_STORE["Bundle"])
        }
        self.wfile.write(json.dumps(status_info, indent=2).encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(body)
        except Exception:
            self._set_headers(400)
            self.wfile.write(b'{"resourceType":"OperationOutcome","issue":[{"diagnostics":"Invalid JSON"}]}')
            return

        res_type = payload.get("resourceType")
        if res_type == "Bundle":
            # Process transaction bundle
            bundle_id = payload.get("id", f"bundle-{uuid.uuid4().hex[:6]}")
            FHIR_STORE["Bundle"][bundle_id] = payload

            response_entries = []
            for entry in payload.get("entry", []):
                inner_res = entry.get("resource", {})
                inner_type = inner_res.get("resourceType")
                inner_id = inner_res.get("id", f"res-{uuid.uuid4().hex[:6]}")
                if inner_type:
                    if inner_type not in FHIR_STORE:
                        FHIR_STORE[inner_type] = {}
                    FHIR_STORE[inner_type][inner_id] = inner_res
                    response_entries.append({
                        "response": {
                            "status": "201 Created",
                            "location": f"{inner_type}/{inner_id}"
                        }
                    })

            ack_bundle = {
                "resourceType": "Bundle",
                "type": "transaction-response",
                "entry": response_entries
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(ack_bundle).encode("utf-8"))
            print(f"[HAPI-FHIR-MOCK] Ingested Transaction Bundle {bundle_id} with {len(response_entries)} resources.")
            return

        # Single resource POST
        if res_type:
            res_id = payload.get("id", f"res-{uuid.uuid4().hex[:6]}")
            payload["id"] = res_id
            if res_type not in FHIR_STORE:
                FHIR_STORE[res_type] = {}
            FHIR_STORE[res_type][res_id] = payload
            self._set_headers(201)
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        self._set_headers(400)
        self.wfile.write(b'{"error": "Unknown resourceType"}')


def run(port=8081):
    server = HTTPServer(("0.0.0.0", port), MockHapiFhirHandler)
    print(f"🚀 Mock HAPI FHIR R4 Server listening on http://localhost:{port}/fhir")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("Mock HAPI FHIR server stopped.")


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    run(port)
