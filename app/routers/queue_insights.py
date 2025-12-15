# app/routers/queue_insights.py
"""
Queue Insights Router Module

This module provides routes for the AI Queue Insights feature.

Routes:
- GET /queue-insights: Dashboard listing observations and latest insight
- GET /queue-insights/new: Form to create a new observation
- POST /queue-insights/new: Create a new observation
- POST /queue-insights/analyze: Generate AI insights from observations

All routes require authentication and are scoped to the current user.
"""

from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database import get_db
from app.models.queue_observation import QueueObservation, QueueInsight
from app.schemas.user import UserResponse
from app.schemas.queue_observation import (
    QueueObservationCreate,
    QueueObservationResponse,
    QueueInsightResponse,
    QueueInsightRequest
)
from app.services.queue_insights import get_insights_service, QueueInsightsService


# Initialize router and templates
router = APIRouter(
    prefix="/queue-insights",
    tags=["queue-insights"]
)

templates = Jinja2Templates(directory="templates")


# ------------------------------------------------------------------------------
# Dashboard Route: List observations and show latest insight
# ------------------------------------------------------------------------------
@router.get("", response_class=HTMLResponse, name="queue_insights_dashboard")
async def queue_insights_dashboard(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Display the Queue Insights dashboard.
    
    Shows:
    - Recent queue observations (user-scoped)
    - Latest generated insight
    - Buttons to add observations and generate insights
    """
    # Fetch user's recent observations (last 30 days, most recent first)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    observations = db.query(QueueObservation).filter(
        QueueObservation.user_id == current_user.id,
        QueueObservation.observed_at >= thirty_days_ago
    ).order_by(desc(QueueObservation.observed_at)).limit(50).all()
    
    # Fetch latest insight for this user
    latest_insight = db.query(QueueInsight).filter(
        QueueInsight.user_id == current_user.id
    ).order_by(desc(QueueInsight.created_at)).first()
    
    return templates.TemplateResponse(
        "queue_list.html",
        {
            "request": request,
            "user": current_user,
            "observations": observations,
            "latest_insight": latest_insight,
            "observation_count": len(observations)
        }
    )


# ------------------------------------------------------------------------------
# New Observation Form Route
# ------------------------------------------------------------------------------
@router.get("/new", response_class=HTMLResponse, name="queue_insights_new_form")
async def queue_insights_new_form(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Display the form to create a new queue observation.
    """
    return templates.TemplateResponse(
        "queue_form.html",
        {
            "request": request,
            "user": current_user
        }
    )


# ------------------------------------------------------------------------------
# Create Observation Route
# ------------------------------------------------------------------------------
@router.post("/new", name="queue_insights_create")
async def queue_insights_create(
    request: Request,
    department: str = Form(...),
    observed_at: str = Form(...),
    number_of_patients: int = Form(...),
    average_wait_minutes: int = Form(...),
    notes: str = Form(None),
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new queue observation.
    
    This route accepts form data and creates a database record
    scoped to the current user.
    """
    try:
        # Parse the datetime string
        # Expected format: "2025-12-15T14:30" from datetime-local input
        observed_datetime = datetime.fromisoformat(observed_at)
        
        # Ensure it's timezone-aware (assume UTC if not specified)
        if observed_datetime.tzinfo is None:
            observed_datetime = observed_datetime.replace(tzinfo=timezone.utc)
        
        # Validate inputs
        if number_of_patients < 0:
            raise ValueError("Number of patients cannot be negative")
        if average_wait_minutes < 0:
            raise ValueError("Average wait time cannot be negative")
        
        # Create the observation
        observation = QueueObservation(
            user_id=current_user.id,
            department=department.strip(),
            observed_at=observed_datetime,
            number_of_patients=number_of_patients,
            average_wait_minutes=average_wait_minutes,
            notes=notes.strip() if notes else None
        )
        
        db.add(observation)
        db.commit()
        db.refresh(observation)
        
        # Redirect back to dashboard with success message
        return RedirectResponse(
            url="/queue-insights?success=observation_created",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except ValueError as e:
        # Validation error
        return templates.TemplateResponse(
            "queue_form.html",
            {
                "request": request,
                "user": current_user,
                "error": str(e),
                "form_data": {
                    "department": department,
                    "observed_at": observed_at,
                    "number_of_patients": number_of_patients,
                    "average_wait_minutes": average_wait_minutes,
                    "notes": notes
                }
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        # Database or other error
        db.rollback()
        return templates.TemplateResponse(
            "queue_form.html",
            {
                "request": request,
                "user": current_user,
                "error": f"Failed to create observation: {str(e)}",
                "form_data": {
                    "department": department,
                    "observed_at": observed_at,
                    "number_of_patients": number_of_patients,
                    "average_wait_minutes": average_wait_minutes,
                    "notes": notes
                }
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ------------------------------------------------------------------------------
# Generate Insights Route
# ------------------------------------------------------------------------------
@router.post("/analyze", name="queue_insights_analyze")
async def queue_insights_analyze(
    request: Request,
    days_back: int = Form(default=7),
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    insights_service: QueueInsightsService = Depends(get_insights_service)
):
    """
    Generate AI insights from queue observations.
    
    This route:
    1. Fetches the user's recent observations (default: last 7 days)
    2. Calls the insights service to generate analysis
    3. Stores the insight in the database
    4. Redirects to the dashboard to display the insight
    
    The insights service will use AI if available, or fall back to rules.
    """
    try:
        # Validate days_back
        if days_back < 1 or days_back > 365:
            days_back = 7
        
        # Fetch user's observations within the time range
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        observations = db.query(QueueObservation).filter(
            QueueObservation.user_id == current_user.id,
            QueueObservation.observed_at >= cutoff_date
        ).order_by(desc(QueueObservation.observed_at)).all()
        
        # Check if we have observations to analyze
        if not observations:
            return RedirectResponse(
                url="/queue-insights?error=no_observations",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Generate insights using the service
        insight_text, is_ai_generated, model_used = await insights_service.generate_insights(
            observations
        )
        
        # Determine date range
        date_range_start = observations[-1].observed_at if observations else None
        date_range_end = observations[0].observed_at if observations else None
        
        # Store the insight
        insight = QueueInsight(
            user_id=current_user.id,
            insight_text=insight_text,
            is_ai_generated=is_ai_generated,
            observation_count=len(observations),
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            model_used=model_used
        )
        
        db.add(insight)
        db.commit()
        db.refresh(insight)
        
        # Redirect to dashboard with success message
        return RedirectResponse(
            url="/queue-insights?success=insight_generated",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except Exception as e:
        # Log error and redirect with error message
        db.rollback()
        print(f"Error generating insights: {e}")
        return RedirectResponse(
            url=f"/queue-insights?error=insight_generation_failed",
            status_code=status.HTTP_303_SEE_OTHER
        )


# ------------------------------------------------------------------------------
# API Routes (Optional - for future extensibility)
# ------------------------------------------------------------------------------
@router.get("/api/observations", response_model=List[QueueObservationResponse])
async def get_observations_api(
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    API endpoint to retrieve observations (JSON).
    
    Optional route for future API integrations or AJAX calls.
    """
    observations = db.query(QueueObservation).filter(
        QueueObservation.user_id == current_user.id
    ).order_by(desc(QueueObservation.observed_at)).offset(skip).limit(limit).all()
    
    return observations


@router.get("/api/insights", response_model=List[QueueInsightResponse])
async def get_insights_api(
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    """
    API endpoint to retrieve insights (JSON).
    
    Optional route for future API integrations or AJAX calls.
    """
    insights = db.query(QueueInsight).filter(
        QueueInsight.user_id == current_user.id
    ).order_by(desc(QueueInsight.created_at)).offset(skip).limit(limit).all()
    
    return insights
