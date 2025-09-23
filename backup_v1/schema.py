from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, List
import re


class Contact(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


class ParsedEvent(BaseModel):
    title: str = Field(..., description="Event name")
    organizer: Optional[str] = None
    contacts: List[Contact] = []
    date_start: str = Field(..., description="YYYY-MM-DD")
    time_start: Optional[str] = Field(None, description="HH:MM 24h")
    time_end: Optional[str] = None
    timezone: str = "America/New_York"
    location: Optional[str] = None
    description: Optional[str] = None
    urls: List[HttpUrl] = []
    # food details:
    food_type: Optional[str] = None         # e.g., "Bonchon", "pizza", "sushi"
    food_quantity_hint: Optional[str] = None # e.g., "dinner provided", "limited snacks"
    # source ids:
    source_message_id: Optional[str] = None
    source_subject: Optional[str] = None
    mailing_list: Optional[str] = None  # Extracted from [XXXXX] in subject line
    original_email_body: Optional[str] = None  # Original email content for display

    @field_validator("date_start")
    @classmethod
    def _date_fmt(cls, v: str) -> str:
        # enforce YYYY-MM-DD
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v or ""):
            raise ValueError("date_start must be YYYY-MM-DD")
        return v

    @field_validator("time_start", "time_end")
    @classmethod
    def _time_fmt(cls, v: Optional[str]) -> Optional[str]:
        if v is None: 
            return v
        if not re.fullmatch(r"\d{2}:\d{2}", v):
            raise ValueError("time must be HH:MM 24h")
        return v
