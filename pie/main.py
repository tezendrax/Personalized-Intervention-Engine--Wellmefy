import logging
import os
import numpy as np
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from pie.config import settings
from pie.db import get_db, init_db, BanditParameter, RecommendationLog
from pie.taxonomy import MISSION_POOL, get_mission_by_id
from pie.rules import apply_clinical_rules
from pie.bandit import get_context_vector, load_or_init_parameters, compute_linucb_score, update_bandit_matrices
from pie.simulator import run_simulation
from pie.schemas import RecommendationRequest, RecommendationResponse, FeedbackRequest, SimulationRequest, MissionRecommendation

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wellmate_pie_api")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Contextual Multi-Armed Bandit (LinUCB) Personalization & Safety pre-filtering Engine",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# External SDT Database Mapping
# ==========================================
SdtBase = declarative_base()

class SdtDigitalTwinState(SdtBase):
    __tablename__ = "digital_twin_states"
    student_id = Column(String(64), primary_key=True)
    s_stress = Column(Float, nullable=False)
    s_anxiety = Column(Float, nullable=False)
    s_fatigue = Column(Float, nullable=False)
    s_social = Column(Float, nullable=False)
    s_academic = Column(Float, nullable=False)
    s_burnout = Column(Float, nullable=False)
    s_sleep = Column(Float, nullable=False)
    s_mood = Column(Float, nullable=False)
    s_resilience = Column(Float, nullable=False)
    s_focus = Column(Float, nullable=False)

sdt_engine = None
def init_sdt_connection():
    global sdt_engine
    try:
        url = settings.SDT_DATABASE_URL
        # Ensure path directory exists if it's a sqlite path
        if url.startswith("sqlite:///"):
            db_file = url.replace("sqlite:///", "")
            os.makedirs(os.path.dirname(os.path.abspath(db_file)), exist_ok=True)
        sdt_engine = create_engine(url, connect_args={"check_same_thread": False} if "sqlite" in url else {})
        logger.info(f"Connected to Student Digital Twin database at: {url}")
    except Exception as e:
        logger.warning(f"Could not connect to external SDT database: {e}. Fallback to mock state values.")

@app.on_event("startup")
def startup_event():
    init_db()
    init_sdt_connection()
    logger.info("PIE Server Startup: Database tables initialized.")

def load_sdt_state_from_db(student_id: str) -> dict:
    if sdt_engine is None:
        return None
    try:
        SessionLocalSdt = sessionmaker(bind=sdt_engine)
        session = SessionLocalSdt()
        try:
            twin = session.query(SdtDigitalTwinState).filter(SdtDigitalTwinState.student_id == student_id).first()
            if twin:
                return {
                    "stress": twin.s_stress,
                    "anxiety": twin.s_anxiety,
                    "fatigue": twin.s_fatigue,
                    "social": twin.s_social,
                    "academic": twin.s_academic,
                    "sleep": twin.s_sleep,
                    "mood": twin.s_mood,
                    "resilience": twin.s_resilience,
                    "focus": twin.s_focus
                }
        finally:
            session.close()
    except Exception as e:
        logger.warning(f"Error querying external SDT database: {e}")
    return None

def get_default_twin_state() -> dict:
    return {
        "stress": 0.3,
        "anxiety": 0.3,
        "fatigue": 0.3,
        "social": 0.7,
        "academic": 0.4,
        "sleep": 0.7,
        "mood": 0.6,
        "resilience": 0.7,
        "focus": 0.7
    }

def build_default_context() -> dict:
    now = datetime.now()
    return {
        "time_of_day": now.hour / 24.0,
        "is_weekend": 1.0 if now.weekday() >= 5 else 0.0,
        "screen_time_index": 0.5,
        "calendar_availability": 0.6,
        "steps_ratio": 1.0,
        "past_completion_rate": 0.7
    }

# ==========================================
# API Endpoints
# ==========================================

@app.get("/api/v1/interventions/taxonomy")
def get_taxonomy():
    """Returns the full catalog of recovery missions."""
    return MISSION_POOL

@app.post("/api/v1/interventions/recommend", response_model=RecommendationResponse)
def recommend_interventions(payload: RecommendationRequest, db: Session = Depends(get_db)):
    """
    Evaluates current student state, pre-filters via safety rules, 
    scores using LinUCB contextual bandit, and returns top 3 interventions.
    """
    # 1. Resolve Twin State
    twin_state = payload.twin_state
    if not twin_state:
        twin_state = load_sdt_state_from_db(payload.student_id)
        if not twin_state:
            twin_state = get_default_twin_state()
            logger.info(f"Student {payload.student_id} not found in SDT database. Using default state vector.")
            
    # 2. Resolve User Context
    user_context = payload.user_context if payload.user_context else {}
    default_ctx = build_default_context()
    for k, v in default_ctx.items():
        if k not in user_context:
            user_context[k] = v
            
    # 3. Assemble 15D Context Vector
    x_t = get_context_vector(twin_state, user_context)
    
    # 4. Apply safety filters
    filtered_pool = apply_clinical_rules(MISSION_POOL, twin_state, payload.active_mission_ids)
    if not filtered_pool:
        # Fallback to pool if all get filtered (avoid empty recommendations)
        filtered_pool = [m for m in MISSION_POOL if m["mission_id"] not in payload.active_mission_ids]
        if not filtered_pool:
            filtered_pool = MISSION_POOL[:3] # last resort fallback
            
    # 5. Compute scores using LinUCB
    scored_missions = []
    for item in filtered_pool:
        m_id = item["mission_id"]
        A, b, _ = load_or_init_parameters(db, m_id)
        score = compute_linucb_score(A, b, x_t)
        
        # Build contextual rationale
        rationale = item.get("rationale_template", f"Recommended based on your current state profile.")
        if item["category"] == "sleep" and twin_state.get("sleep", 1.0) < 0.6:
            rationale = "Recommended because your sleep quality has dropped and fatigue index is high."
        elif item["category"] == "academic" and twin_state.get("academic", 0.0) > 0.7:
            rationale = "Recommended to prevent academic burnout and structure your upcoming deadines."
        elif item["category"] == "mental" and twin_state.get("stress", 0.0) > 0.7:
            rationale = "Recommended because your stress and anxiety indices show negative elevations."
        elif item["category"] == "digital" and user_context.get("screen_time_index", 0.0) > 0.75:
            rationale = "Recommended to disrupt excessive smartphone usage cycles and restore focus."
            
        scored_missions.append(MissionRecommendation(
            mission_id=item["mission_id"],
            title=item["title"],
            description=item["description"],
            category=item["category"],
            difficulty=item["difficulty"],
            points_value=item["points_value"],
            score=score,
            rationale=rationale
        ))
        
    # Sort and take top 5
    scored_missions.sort(key=lambda x: x.score, reverse=True)
    top_5 = scored_missions[:5]
    
    # 5.5 Try to fetch dynamic rationales and advice from LLM wellness models
    from pie.llm import generate_llm_rationales_and_advice
    
    top_5_pool = []
    for m in top_5:
        pool_item = next((item for item in MISSION_POOL if item["mission_id"] == m.mission_id), None)
        if pool_item:
            top_5_pool.append(pool_item)
            
    llm_data = generate_llm_rationales_and_advice(
        twin_state=twin_state,
        user_context=user_context,
        missions=top_5_pool,
        feared_subjects=payload.feared_subjects,
        upcoming_exams=payload.upcoming_exams,
        programming_issues=payload.programming_issues,
        daily_screen_time_hours=payload.daily_screen_time_hours,
        sleep_bedtime_target=payload.sleep_bedtime_target
    )
    
    advice = "Wellness Focus: Establish structured sleep rituals, manage academic task blocks, and connect with peers."
    
    # Apply local heuristics to customize top_5 missions if LLM falls back
    feared = payload.feared_subjects[0] if payload.feared_subjects else None
    exam = payload.upcoming_exams[0].get("subject") if payload.upcoming_exams else None
    exam_date = payload.upcoming_exams[0].get("date") if payload.upcoming_exams else None
    prog = payload.programming_issues[0] if payload.programming_issues else None
    screen = payload.daily_screen_time_hours
    bedtime = payload.sleep_bedtime_target
    
    for m in top_5:
        if "academic-pomodoro" in m.mission_id:
            if feared:
                m.title = f"25-Min Focus: {feared}"
                m.description = f"Engage in focused study on your feared subject '{feared}' using the Pomodoro technique."
            elif prog:
                m.title = f"Debug Focus: {prog}"
                m.description = f"Focus for 25 minutes on resolving your programming block: '{prog}'."
        elif "academic-backlog" in m.mission_id:
            if feared:
                m.title = f"Audit {feared} Backlog"
                m.description = f"Make a detailed checklist of your struggles in '{feared}' over the last 7 days."
        elif "sleep-digital-detox" in m.mission_id:
            if screen is not None:
                m.title = f"Digital Curfew ({screen}h Screen)"
                m.description = f"You had {screen}h screen time today. Avoid screens 45 minutes before sleep."
        elif "sleep-bedtime-anchor" in m.mission_id:
            if bedtime:
                m.title = f"Anchor Bedtime: {bedtime}"
                m.description = f"Go to bed tonight by your target bedtime of {bedtime} to recover sleep debt."
        elif "social-chat-friend" in m.mission_id:
            if twin_state.get("social", 1.0) < 0.4:
                m.title = "Call a Friend (Low Social Status)"
                m.description = "Since your social index is low, call or chat with a close friend for 15 minutes."
                
    if llm_data:
        advice = llm_data.get("advice", advice)
        rationales_map = llm_data.get("rationales", {})
        custom_map = llm_data.get("customized_missions", {})
        for m in top_5:
            if m.mission_id in rationales_map:
                m.rationale = rationales_map[m.mission_id]
            if m.mission_id in custom_map:
                custom_item = custom_map[m.mission_id]
                m.title = custom_item.get("title", m.title)
                m.description = custom_item.get("description", m.description)
    else:
        # Build local heuristic advice list
        reports = []
        if feared:
            reports.append(f"You need to study your feared subject '{feared}' for at least 2 hours today.")
        if twin_state.get("social", 1.0) < 0.4:
            reports.append("Since you are less social right now, make a call to a friend.")
        if bedtime:
            reports.append(f"Sleep early by {bedtime} to recover sleep debt.")
        if screen is not None and screen > 4.0:
            reports.append(f"Establish a digital curfew to limit your {screen}h screen time and boost productivity.")
        if exam:
            reports.append(f"Prepare for your upcoming exam in '{exam}' on {exam_date or ''}.")
            
        if reports:
            advice = " | ".join(reports)
                
    # 6. Log Recommendation
    try:
        rec_log = RecommendationLog(
            student_id=payload.student_id,
            context_vector=x_t.tolist(),
            recommendations=[{
                "mission_id": m.mission_id,
                "title": m.title,
                "score": m.score
            } for m in top_5]
        )
        db.add(rec_log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log recommendation to database: {e}")
        db.rollback()
        
    return RecommendationResponse(
        student_id=payload.student_id,
        recommendations=top_5,
        advice=advice
    )

@app.post("/api/v1/interventions/feedback")
def submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)):
    """
    Submits reward feedback for a recommended mission (1.0 = completed, 0.0 = skipped/ignored).
    Triggers online training updates of LinUCB matrices.
    """
    # 1. Resolve User Context
    user_context = payload.user_context if payload.user_context else {}
    default_ctx = build_default_context()
    for k, v in default_ctx.items():
        if k not in user_context:
            user_context[k] = v
            
    # 2. Assemble 15D Context Vector
    x_t = get_context_vector(payload.twin_state, user_context)
    
    # 3. Update bandit parameters
    try:
        update_bandit_matrices(db, payload.mission_id, x_t, payload.reward)
        
        # 4. Update Recommendation Log if found
        recent_log = db.query(RecommendationLog).filter(
            RecommendationLog.student_id == payload.student_id,
            RecommendationLog.chosen_mission_id == None
        ).order_by(RecommendationLog.created_at.desc()).first()
        
        if recent_log:
            recent_log.chosen_mission_id = payload.mission_id
            recent_log.reward = payload.reward
            db.add(recent_log)
            db.commit()
            
        return {"status": "success", "message": f"Bandit policy updated for mission {payload.mission_id}."}
    except Exception as e:
        logger.error(f"Error updating bandit policy: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/interventions/simulate")
def simulate_learning(payload: SimulationRequest, db: Session = Depends(get_db)):
    """
    Runs a batch simulation of student responses to train the LinUCB policy and check convergence rates.
    """
    try:
        res = run_simulation(db, payload.profile_name, payload.iterations)
        return res
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/interventions/parameters")
def get_bandit_parameter_stats(db: Session = Depends(get_db)):
    """
    Returns statistical summaries of the bandit parameters (e.g. exploration coverage, norm of weights).
    """
    params = db.query(BanditParameter).all()
    stats = []
    for p in params:
        A = np.array(p.matrix_A)
        b = np.array(p.vector_b)
        
        # Calculate theta
        A_inv = np.linalg.inv(A)
        theta = A_inv.dot(b)
        
        stats.append({
            "mission_id": p.mission_id,
            "b_norm": float(np.linalg.norm(b)),
            "theta_norm": float(np.linalg.norm(theta)),
            "diagonal_sum_A": float(np.trace(A)),
            "updated_at": p.updated_at.isoformat()
        })
    return stats

@app.get("/api/v1/interventions/history")
def get_recommendation_history(limit: int = 50, db: Session = Depends(get_db)):
    """
    Returns recent recommendation and feedback logs.
    """
    logs = db.query(RecommendationLog).order_by(RecommendationLog.created_at.desc()).limit(limit).all()
    result = []
    for l in logs:
        result.append({
            "id": l.id,
            "student_id": l.student_id,
            "recommendations": l.recommendations,
            "chosen_mission_id": l.chosen_mission_id,
            "reward": l.reward,
            "created_at": l.created_at.isoformat()
        })
    return result

# Mount static files for the dashboard frontend
from fastapi.staticfiles import StaticFiles
frontend_path = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"))
os.makedirs(frontend_path, exist_ok=True)
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
