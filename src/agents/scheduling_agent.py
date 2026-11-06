"""Department scheduling, physician assignment, and pre-visit preparation agent."""

from google.adk import Agent
from ..models.appointment import AppointmentBooking
from ..tools.scheduling_tools import (
    book_appointment_slot,
    get_available_department_slots,
)
from ...config.settings import settings

SCHEDULING_AGENT_INSTRUCTIONS = """\
You are the Hospital Scheduling & Logistics Coordinator Agent for St. Jude Memorial Health System.
Your job is to match the patient with the appropriate clinic and confirm their arrival slot:
1. Review the recommended clinical department determined during triage.
2. Query available consultation slots using `get_available_department_slots`.
3. Present available times to the patient and confirm their preferred slot.
4. Call `book_appointment_slot` to secure the physician and consultation room.
5. Provide clear, empathetic pre-visit preparation guidelines (e.g. fasting rules, what records to bring).
"""

def create_scheduling_agent() -> Agent:
    """Factory creating configured ADK Scheduling Agent."""
    return Agent(
        name="scheduling_logistics_agent",
        model=settings.onboarding_model_name,
        instruction=SCHEDULING_AGENT_INSTRUCTIONS,
        tools=[get_available_department_slots, book_appointment_slot],
        output_schema=AppointmentBooking,
    )
