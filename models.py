from typing import Literal

from pydantic import BaseModel, Field

class CivicIssue(BaseModel):
    title: str = Field(description="A short, clear 5-6 word title of the civic issue.")
    area: str = Field(description="The specific locality in Hyderabad (e.g., Kukatpally, Mehdipatnam).")
    zone: Literal["Central", "North", "South", "West", "East", "Secunderabad"] = Field(
        description="The GHMC zone the area belongs to."
    )
    cat: Literal["Roads", "Water", "Power", "Sanitation", "Drainage"] = Field(
        description="The category of the issue."
    )
    catKey: Literal["roads", "water", "power", "sanit", "drain"] = Field(
        description="Short key mapping to the category."
    )
    S: float = Field(description="Severity (0-10): Immediate public danger or urgency.", ge=0, le=10)
    F: float = Field(description="Frequency (0-10): How often this seems to be reported or how widespread it is.", ge=0, le=10)
    R: float = Field(description="Compounding Risk (0-10): Environmental/temporal amplifiers (e.g., pre-monsoon).", ge=0, le=10)
    D: float = Field(description="Duration (0-10): How long the issue has persisted.", ge=0, le=10)
    P: float = Field(description="Population Density (0-10): Estimated density impact of the area.", ge=0, le=10)
    post_date: str = Field(description="Date the issue was first reported in YYYY-MM-DD format.")
    traction_date: str = Field(description="Date of peak traction in YYYY-MM-DD format.")

class ExtractedIssues(BaseModel):
    issues: list[CivicIssue]
