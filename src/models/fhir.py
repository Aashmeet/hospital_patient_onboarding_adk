"""HL7 FHIR R4 interoperability data models for EHR synchronization."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class FHIRResource(BaseModel):
    """Base FHIR R4 resource."""
    resourceType: str
    id: str


class FHIRPatient(FHIRResource):
    """FHIR R4 Patient Resource."""
    resourceType: str = "Patient"
    identifier: List[Dict[str, Any]]
    active: bool = True
    name: List[Dict[str, Any]]
    telecom: List[Dict[str, Any]]
    gender: str
    birthDate: str
    address: List[Dict[str, Any]]


class FHIRCoverage(FHIRResource):
    """FHIR R4 Coverage Resource (Insurance benefits)."""
    resourceType: str = "Coverage"
    status: str = "active"
    beneficiary: Dict[str, str]
    payor: List[Dict[str, str]]
    subscriberId: str


class FHIREncounter(FHIRResource):
    """FHIR R4 Encounter Resource (Hospital visit / intake)."""
    resourceType: str = "Encounter"
    status: str = "planned"
    class_: Dict[str, str] = Field(..., alias="class")
    subject: Dict[str, str]
    serviceProvider: Dict[str, str]
    period: Dict[str, str]


class FHIRBundle(BaseModel):
    """FHIR R4 Transaction Bundle for atomic EHR ingestion."""
    resourceType: str = "Bundle"
    type: str = "transaction"
    entry: List[Dict[str, Any]]
