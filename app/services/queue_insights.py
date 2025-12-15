# app/services/queue_insights.py
"""
Queue Insights Service Module

This module provides AI-assisted analysis for queue observations.

Design Philosophy:
- Explainable AI: Users understand when and how AI is used
- Ethical Fallback: Graceful degradation to rule-based analysis
- Decision Support: Provides actionable insights, not predictions
- Transparency: Clear indication of AI vs. rule-based generation

AI Integration Strategy:
1. Primary: Use OpenAI GPT models when API key is available
2. Fallback: Use rule-based heuristic analysis when API key is missing or API fails
3. Metadata: Always track which method was used for transparency

This demonstrates production-ready AI integration with proper error handling,
cost control (limited tokens), and user transparency.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Optional
from collections import defaultdict

from app.core.config import get_settings
from app.models.queue_observation import QueueObservation

settings = get_settings()
logger = logging.getLogger(__name__)


class QueueInsightsService:
    """
    Service for generating insights from queue observations.
    
    This service implements a dual-mode approach:
    - AI Mode: Uses OpenAI API to generate natural language insights
    - Fallback Mode: Uses rule-based heuristics for analysis
    
    The fallback ensures the feature always works, even without API access.
    """
    
    def __init__(self):
        """Initialize the insights service."""
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
    
    async def generate_insights(
        self,
        observations: List[QueueObservation]
    ) -> Tuple[str, bool, str]:
        """
        Generate insights from queue observations.
        
        This method attempts AI generation first, then falls back to rules.
        
        Args:
            observations: List of QueueObservation objects to analyze
            
        Returns:
            Tuple containing:
            - insight_text: Natural language insight summary
            - is_ai_generated: True if LLM was used, False if rule-based
            - model_used: Name of the model or "rule-based"
        """
        if not observations:
            return (
                "No observations available for analysis. Please add queue observations first.",
                False,
                "rule-based"
            )
        
        # Try AI generation if API key is available
        if self.api_key:
            try:
                insight_text = await self._generate_ai_insights(observations)
                logger.info(f"Generated AI insights using {self.model}")
                return (insight_text, True, self.model)
            except Exception as e:
                logger.warning(f"AI generation failed, falling back to rules: {e}")
                # Fall through to rule-based approach
        
        # Fallback to rule-based analysis
        logger.info("Using rule-based insight generation")
        insight_text = self._generate_rule_based_insights(observations)
        return (insight_text, False, "rule-based")
    
    async def _generate_ai_insights(
        self,
        observations: List[QueueObservation]
    ) -> str:
        """
        Generate insights using OpenAI API.
        
        This method constructs a prompt with observation data and asks
        the LLM to identify patterns, bottlenecks, and recommendations.
        
        Args:
            observations: List of QueueObservation objects
            
        Returns:
            str: AI-generated insight text
            
        Raises:
            Exception: If API call fails or returns invalid response
        """
        try:
            # Lazy import to avoid requiring openai when not needed
            from openai import OpenAI
        except ImportError:
            raise Exception(
                "OpenAI package not installed. Install with: pip install openai"
            )
        
        # Initialize OpenAI client
        client = OpenAI(api_key=self.api_key)
        
        # Prepare observation data for the prompt
        obs_summary = self._prepare_observation_summary(observations)
        
        # Construct the prompt
        prompt = f"""You are an AI assistant helping hospital administrators analyze queue data.

Based on the following queue observations, provide a concise operational insight:

{obs_summary}

Your analysis should:
1. Identify the department(s) with the highest wait times or patient volumes
2. Highlight any concerning patterns or bottlenecks
3. Provide ONE actionable recommendation (e.g., staffing adjustment, scheduling change)

Keep your response professional, clear, and under 300 words.
Focus on decision support, not prediction.
"""
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes hospital queue data to provide operational insights."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=self.max_tokens,
            temperature=0.7,
        )
        
        # Extract and return the insight text
        insight_text = response.choices[0].message.content.strip()
        return insight_text
    
    def _generate_rule_based_insights(
        self,
        observations: List[QueueObservation]
    ) -> str:
        """
        Generate insights using rule-based heuristic analysis.
        
        This is the fallback method when AI is not available.
        It provides deterministic, explainable insights based on simple rules.
        
        Args:
            observations: List of QueueObservation objects
            
        Returns:
            str: Rule-based insight text
        """
        # Aggregate statistics by department
        dept_stats = defaultdict(lambda: {
            'total_patients': 0,
            'total_wait': 0,
            'count': 0,
            'max_wait': 0,
            'observations': []
        })
        
        for obs in observations:
            dept = obs.department
            dept_stats[dept]['total_patients'] += obs.number_of_patients
            dept_stats[dept]['total_wait'] += obs.average_wait_minutes
            dept_stats[dept]['count'] += 1
            dept_stats[dept]['max_wait'] = max(
                dept_stats[dept]['max_wait'],
                obs.average_wait_minutes
            )
            dept_stats[dept]['observations'].append(obs)
        
        # Calculate averages
        dept_averages = {}
        for dept, stats in dept_stats.items():
            dept_averages[dept] = {
                'avg_patients': stats['total_patients'] / stats['count'],
                'avg_wait': stats['total_wait'] / stats['count'],
                'max_wait': stats['max_wait'],
                'count': stats['count']
            }
        
        # Identify highest wait time department
        highest_wait_dept = max(
            dept_averages.items(),
            key=lambda x: x[1]['avg_wait']
        )
        
        # Identify highest volume department
        highest_volume_dept = max(
            dept_averages.items(),
            key=lambda x: x[1]['avg_patients']
        )
        
        # Build insight text
        total_obs = len(observations)
        dept_count = len(dept_stats)
        
        insight_parts = [
            f"**Queue Insights Analysis** (Rule-Based)",
            f"\n**Data Summary:**",
            f"- Analyzed {total_obs} observations across {dept_count} department(s)",
            f"- Time period: {observations[-1].observed_at.strftime('%Y-%m-%d')} to {observations[0].observed_at.strftime('%Y-%m-%d')}",
            f"\n**Key Findings:**",
        ]
        
        # Finding 1: Highest wait times
        hw_dept, hw_stats = highest_wait_dept
        insight_parts.append(
            f"1. **Longest Wait Times:** {hw_dept} has an average wait time of "
            f"{hw_stats['avg_wait']:.1f} minutes (max: {hw_stats['max_wait']} minutes)"
        )
        
        # Finding 2: Highest volume
        hv_dept, hv_stats = highest_volume_dept
        if hv_dept != hw_dept:
            insight_parts.append(
                f"2. **Highest Patient Volume:** {hv_dept} averages "
                f"{hv_stats['avg_patients']:.1f} patients per observation"
            )
        
        # Finding 3: Bottleneck identification
        bottleneck_threshold = 60  # minutes
        bottleneck_depts = [
            dept for dept, stats in dept_averages.items()
            if stats['avg_wait'] > bottleneck_threshold
        ]
        
        if bottleneck_depts:
            insight_parts.append(
                f"3. **Potential Bottlenecks:** The following departments exceed "
                f"{bottleneck_threshold} minutes average wait: {', '.join(bottleneck_depts)}"
            )
        
        # Recommendation
        insight_parts.append(f"\n**Recommendation:**")
        if hw_stats['avg_wait'] > bottleneck_threshold:
            insight_parts.append(
                f"Consider increasing staffing or adjusting scheduling for {hw_dept} "
                f"to reduce wait times. Peak periods may benefit from additional resources."
            )
        elif hw_stats['avg_wait'] > 30:
            insight_parts.append(
                f"Monitor {hw_dept} closely as wait times are elevated. "
                f"Proactive scheduling adjustments may prevent future bottlenecks."
            )
        else:
            insight_parts.append(
                f"Current wait times are within acceptable ranges. "
                f"Continue monitoring for trends and consider preventive measures during peak hours."
            )
        
        # Note about rule-based analysis
        insight_parts.append(
            f"\n*Note: This analysis uses rule-based heuristics. "
            f"For AI-powered insights, configure an OpenAI API key.*"
        )
        
        return "\n".join(insight_parts)
    
    def _prepare_observation_summary(
        self,
        observations: List[QueueObservation]
    ) -> str:
        """
        Prepare a text summary of observations for the AI prompt.
        
        Args:
            observations: List of QueueObservation objects
            
        Returns:
            str: Formatted text summary
        """
        lines = ["Queue Observations:"]
        lines.append("-" * 80)
        
        for i, obs in enumerate(observations, 1):
            lines.append(
                f"{i}. Department: {obs.department} | "
                f"Date: {obs.observed_at.strftime('%Y-%m-%d %H:%M')} | "
                f"Patients: {obs.number_of_patients} | "
                f"Avg Wait: {obs.average_wait_minutes} min"
            )
            if obs.notes:
                lines.append(f"   Notes: {obs.notes}")
        
        lines.append("-" * 80)
        lines.append(f"Total observations: {len(observations)}")
        
        return "\n".join(lines)


# Singleton instance for dependency injection
_insights_service = None

def get_insights_service() -> QueueInsightsService:
    """
    Dependency injection function for the insights service.
    
    Returns:
        QueueInsightsService: Singleton instance
    """
    global _insights_service
    if _insights_service is None:
        _insights_service = QueueInsightsService()
    return _insights_service
