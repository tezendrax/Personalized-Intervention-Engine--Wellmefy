from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class RecommendationRequest(BaseModel):
    student_id: str
    twin_state: Optional[Dict[str, float]] = Field(
        default=None,
        description="Current state dimensions: stress, anxiety, fatigue, social, academic, sleep, mood, resilience, focus"
    )
    user_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Cues like time_of_day, is_weekend, screen_time_index, calendar_availability, steps_ratio, past_completion_rate"
    )
    active_mission_ids: Optional[List[str]] = Field(
        default_factory=list,
        description="Missions that the student is currently working on, to avoid repeats."
    )
    feared_subjects: Optional[List[str]] = Field(default_factory=list)
    upcoming_exams: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    programming_issues: Optional[List[str]] = Field(default_factory=list)
    daily_screen_time_hours: Optional[float] = None
    sleep_bedtime_target: Optional[str] = None

class MissionRecommendation(BaseModel):
    mission_id: str
    title: str
    description: str
    category: str
    difficulty: float
    points_value: int
    score: float
    rationale: str

class RecommendationResponse(BaseModel):
    student_id: str
    recommendations: List[MissionRecommendation]
    advice: Optional[str] = None

class FeedbackRequest(BaseModel):
    student_id: str
    mission_id: str
    reward: float = Field(..., ge=0.0, le=1.0, description="1.0 for completed, 0.0 for ignored/skipped")
    twin_state: Dict[str, float]
    user_context: Optional[Dict[str, Any]] = None

class SimulationRequest(BaseModel):
    profile_name: str = Field("Stressed Academic", description="Cohort profile to simulate: 'Stressed Academic', 'Late-Night Gamer', 'Balanced Student'")
    iterations: int = Field(100, ge=1, le=1000)
