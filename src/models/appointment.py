"""Hospital scheduling and department appointment domain models."""

from typing import Optional
from pydantic import BaseModel, Field


class HospitalDepartment(BaseModel):
    """Clinical department details."""
    id: str = Field(..., description="Unique department code, e.g. dept_cardiology")
    name: str = Field(..., description="Human-readable department title")
    lead_physician: str = Field(..., description="Lead attending physician name")
    location: str = Field(..., description="Physical hospital pavilion/room location")
    prep_instructions: str = Field(..., description="Pre-visit preparation requirements")


class AppointmentBooking(BaseModel):
    """Booked appointment details for patient intake."""
    booking_id: str = Field(..., description="Unique scheduling confirmation code")
    mrn: str = Field(..., description="Patient Medical Record Number")
    department_id: str = Field(..., description="Target department identifier")
    department_name: str = Field(..., description="Human-readable department name")
    assigned_physician: str = Field(..., description="Attending physician")
    appointment_time: str = Field(..., description="Scheduled arrival timestamp")
    location: str = Field(..., description="Hospital location instructions")
    prep_instructions: str = Field(..., description="Patient preparation guide")
    status: str = Field(default="CONFIRMED", description="CONFIRMED, ARRIVED, CANCELLED, ESCALATED_ER")
