import math
import numpy as np
import logging
from sqlalchemy.orm import Session
from pie.db import BanditParameter
from pie.config import settings

logger = logging.getLogger("wellmate_pie_bandit")

CONTEXT_DIM = 15

def get_context_vector(twin_state: dict, user_context: dict) -> np.ndarray:
    """
    Constructs a 15-dimensional context vector from the student twin state and contextual cues.
    All dimensions are normalized to be roughly between 0.0 and 1.5.
    """
    # Student Twin States
    stress = twin_state.get("stress", 0.5)
    anxiety = twin_state.get("anxiety", 0.5)
    fatigue = twin_state.get("fatigue", 0.5)
    sleep_debt = 1.0 - twin_state.get("sleep", 0.7)
    resilience_deficit = 1.0 - twin_state.get("resilience", 0.7)
    mood = twin_state.get("mood", 0.6)
    focus = twin_state.get("focus", 0.6)
    academic_stress = twin_state.get("academic", 0.5)
    social_isolation = 1.0 - twin_state.get("social", 0.7)
    
    # Contextual parameters
    time_of_day = user_context.get("time_of_day", 0.5)  # Normalized hour [0.0 - 1.0]
    is_weekend = float(user_context.get("is_weekend", 0))  # 0.0 or 1.0
    screen_time_index = user_context.get("screen_time_index", 0.5)  # [0.0 - 1.0]
    calendar_availability = user_context.get("calendar_availability", 0.6)  # [0.0 - 1.0]
    steps_ratio = user_context.get("steps_ratio", 1.0)  # relative steps to target, capped at 1.5
    past_completion_rate = user_context.get("past_completion_rate", 0.7)  # [0.0 - 1.0]
    
    x = np.array([
        stress,
        anxiety,
        fatigue,
        sleep_debt,
        resilience_deficit,
        mood,
        focus,
        academic_stress,
        social_isolation,
        time_of_day,
        is_weekend,
        screen_time_index,
        calendar_availability,
        steps_ratio,
        past_completion_rate
    ], dtype=float)
    
    # Normalize context vector to unit length
    norm = np.linalg.norm(x)
    if norm > 0:
        x = x / norm
        
    return x

def load_or_init_parameters(db: Session, mission_id: str) -> tuple:
    """
    Loads A and b matrices for the given mission from the database, or initializes them if not present.
    """
    param = db.query(BanditParameter).filter(BanditParameter.mission_id == mission_id).first()
    if param:
        A = np.array(param.matrix_A)
        b = np.array(param.vector_b)
    else:
        A = np.identity(CONTEXT_DIM)
        b = np.zeros(CONTEXT_DIM)
        # Save baseline to DB
        param = BanditParameter(mission_id=mission_id)
        param.matrix_A = A.tolist()
        param.vector_b = b.tolist()
        db.add(param)
        db.commit()
    return A, b, param

def compute_linucb_score(A: np.ndarray, b: np.ndarray, x: np.ndarray, alpha: float = None) -> float:
    """
    Computes the LinUCB score for a given context vector x.
    score = theta^T * x + alpha * sqrt(x^T * A^-1 * x)
    """
    if alpha is None:
        alpha = settings.ALPHA_EXPLORE
        
    A_inv = np.linalg.inv(A)
    theta = A_inv.dot(b)
    
    pred_reward = theta.dot(x)
    variance = x.dot(A_inv).dot(x)
    
    # Prevent negative values due to floating point precision
    std_dev = math.sqrt(max(0.0, variance))
    
    score = pred_reward + alpha * std_dev
    return float(score)

def update_bandit_matrices(db: Session, mission_id: str, x: np.ndarray, reward: float):
    """
    Performs online update of LinUCB matrices for a given mission.
    A_a <- A_a + x * x^T
    b_a <- b_a + r * x
    """
    A, b, param = load_or_init_parameters(db, mission_id)
    
    # Outer product update
    A += np.outer(x, x)
    b += reward * x
    
    param.matrix_A = A.tolist()
    param.vector_b = b.tolist()
    
    db.add(param)
    db.commit()
    db.refresh(param)
    logger.info(f"Bandit Policy Updated: mission_id={mission_id}, reward={reward}")
