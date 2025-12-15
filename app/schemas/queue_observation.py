# app/schemas/queue_observation.py
"""
Queue Observation Schemas Module

This module defines the Pydantic schemas for validation and serialization
of queue observation and insight data.

Schemas include:
- Base schemas for observation data
- Create schemas for new observations
- Response schemas for API responses
- Insight schemas for AI-generated analysis results

All schemas follow Pydantic best practices for validation and documentation.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class QueueObservationBase(BaseModel):
    """
    Base schema for queue observation data.
    
    This schema defines the common fields for queue observations.
    Used as a foundation for create and update operations.
    """
    department: str = Field(
        ...,
        description="Hospital department name (e.g., ER, Radiology, Check-in)",
        example="Emergency Room",
        min_length=1,
        max_length=100
    )
    
    observed_at: datetime = Field(
        ...,
        description="Timestamp when the queue was observed",
        example="2025-12-15T14:30:00Z"
    )
    
    number_of_patients: int = Field(
        ...,
        description="Number of patients observed in the queue",
        example=12,
        ge=0  # Greater than or equal to 0
    )
    
    average_wait_minutes: int = Field(
        ...,
        description="Estimated average wait time in minutes",
        example=45,
        ge=0  # Greater than or equal to 0
    )
    
    notes: Optional[str] = Field(
        None,
        description="Optional notes about the observation",
        example="Unusually busy for a Tuesday afternoon",
        max_length=1000
    )
    
    @field_validator("department")
    @classmethod
    def validate_department(cls, v):
        """
        Validates and normalizes department name.
        
        Args:
            v: The department name to validate
            
        Returns:
            str: The validated and trimmed department name
            
        Raises:
            ValueError: If the department name is empty after stripping
        """
        if not v or not v.strip():
            raise ValueError("Department name cannot be empty")
        return v.strip()
    
    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v):
        """
        Validates and normalizes notes field.
        
        Args:
            v: The notes to validate
            
        Returns:
            Optional[str]: The validated notes or None
        """
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None


class QueueObservationCreate(QueueObservationBase):
    """
    Schema for creating a new queue observation.
    
    Inherits all fields from QueueObservationBase.
    The user_id is automatically set from the authenticated user.
    """
    pass


class QueueObservationResponse(QueueObservationBase):
    """
    Schema for queue observation API responses.
    
    Includes all base fields plus database-generated fields like id and timestamps.
    """
    id: UUID = Field(
        ...,
        description="Unique identifier for the observation"
    )
    
    user_id: UUID = Field(
        ...,
        description="ID of the user who created this observation"
    )
    
    created_at: datetime = Field(
        ...,
        description="Timestamp when the record was created"
    )
    
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the record was last updated"
    )
    
    model_config = ConfigDict(from_attributes=True)


class QueueInsightBase(BaseModel):
    """
    Base schema for queue insight data.
    """
    insight_text: str = Field(
        ...,
        description="The generated natural language insight",
        min_length=1
    )
    
    is_ai_generated: bool = Field(
        ...,
        description="True if LLM was used, False if rule-based fallback"
    )
    
    observation_count: int = Field(
        ...,
        description="Number of observations analyzed",
        ge=0
    )
    
    model_used: str = Field(
        ...,
        description="Name of the AI model or 'rule-based'",
        example="gpt-4"
    )
    
    date_range_start: Optional[datetime] = Field(
        None,
        description="Start of the analysis time window"
    )
    
    date_range_end: Optional[datetime] = Field(
        None,
        description="End of the analysis time window"
    )


class QueueInsightResponse(QueueInsightBase):
    """
    Schema for queue insight API responses.
    
    Includes all base fields plus database-generated fields.
    """
    id: UUID = Field(
        ...,
        description="Unique identifier for the insight"
    )
    
    user_id: UUID = Field(
        ...,
        description="ID of the user who requested this insight"
    )
    
    created_at: datetime = Field(
        ...,
        description="Timestamp when the insight was generated"
    )
    
    model_config = ConfigDict(from_attributes=True)


class QueueInsightRequest(BaseModel):
    """
    Schema for requesting insight generation.
    
    Optional parameters to customize the analysis.
    """
    days_back: int = Field(
        default=7,
        description="Number of days of data to analyze",
        ge=1,
        le=365
    )
