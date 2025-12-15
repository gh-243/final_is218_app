# app/models/queue_observation.py
"""
Queue Observation Models Module

This module defines the database models for the AI Queue Insights feature.
It includes:
- QueueObservation: User-submitted queue data points
- QueueInsight: AI-generated or rule-based insights

Design Philosophy:
- Supports decision support, not real-time monitoring
- User-scoped data (users only see their own observations)
- Stores both AI-generated and fallback insights
- Includes metadata to track AI vs. rule-based analysis
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    """
    Helper function to get current UTC datetime with timezone information.
    
    Returns:
        datetime: Current UTC time with timezone info
    """
    return datetime.now(timezone.utc)


class QueueObservation(Base):
    """
    Model representing a single queue observation logged by a user.
    
    Users log queue observations to build a dataset for analysis.
    Each observation captures the state of a queue at a specific point in time.
    
    Attributes:
        id: Unique identifier
        user_id: Foreign key to the User who created this observation
        department: Hospital department (e.g., "ER", "Radiology", "Check-in")
        observed_at: Timestamp when the queue was observed
        number_of_patients: Count of patients in the queue
        average_wait_minutes: Estimated average wait time in minutes
        notes: Optional text notes about the observation
        created_at: When this record was created in the database
        updated_at: When this record was last updated
    """
    __tablename__ = "queue_observations"
    
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True
    )
    
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    department = Column(
        String(100),
        nullable=False,
        index=True  # Index for filtering by department
    )
    
    observed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        index=True  # Index for time-based queries
    )
    
    number_of_patients = Column(
        Integer,
        nullable=False
    )
    
    average_wait_minutes = Column(
        Integer,
        nullable=False
    )
    
    notes = Column(
        Text,
        nullable=True
    )
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow
    )
    
    # Relationship to User model
    user = relationship("User", back_populates="queue_observations")
    
    # Composite index for efficient queries by user and time
    __table_args__ = (
        Index('ix_user_observed_at', 'user_id', 'observed_at'),
    )
    
    def __repr__(self):
        return f"<QueueObservation(id={self.id}, department={self.department}, patients={self.number_of_patients})>"


class QueueInsight(Base):
    """
    Model representing an AI-generated or rule-based insight.
    
    This stores the results of analysis performed on a user's queue observations.
    Insights are generated on-demand when the user clicks "Generate Insights".
    
    Attributes:
        id: Unique identifier
        user_id: Foreign key to the User who requested this insight
        insight_text: The generated natural language insight
        is_ai_generated: True if LLM was used, False if rule-based fallback
        observation_count: Number of observations analyzed
        date_range_start: Start of the analysis time window
        date_range_end: End of the analysis time window
        model_used: Name of the AI model or "rule-based"
        created_at: When this insight was generated
    """
    __tablename__ = "queue_insights"
    
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True
    )
    
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    insight_text = Column(
        Text,
        nullable=False
    )
    
    is_ai_generated = Column(
        Boolean,
        nullable=False,
        default=False
    )
    
    observation_count = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    date_range_start = Column(
        DateTime(timezone=True),
        nullable=True
    )
    
    date_range_end = Column(
        DateTime(timezone=True),
        nullable=True
    )
    
    model_used = Column(
        String(100),
        nullable=False,
        default="rule-based"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        index=True
    )
    
    # Relationship to User model
    user = relationship("User", back_populates="queue_insights")
    
    def __repr__(self):
        return f"<QueueInsight(id={self.id}, ai={self.is_ai_generated}, observations={self.observation_count})>"
