import numpy as np
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pie.db import Base, get_db
from pie.main import app
from pie.bandit import get_context_vector, compute_linucb_score, load_or_init_parameters, update_bandit_matrices
from pie.rules import apply_clinical_rules
from pie.taxonomy import MISSION_POOL

# Setup temporary SQLite database for testing
TEST_DATABASE_URL = "sqlite:///./test_pie.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_pie.db"):
        try:
            os.remove("./test_pie.db")
        except Exception:
            pass

def test_linucb_math():
    # 1. Setup mock matrices (15 dimensions)
    A = np.identity(15)
    b = np.zeros(15)
    x = np.ones(15) / np.linalg.norm(np.ones(15))
    
    # 2. Compute score (should be prediction (0.0) + alpha (1.0) * sqrt(x^T * I * x) (1.0) = 1.0)
    score = compute_linucb_score(A, b, x, alpha=1.0)
    assert pytest.approx(score) == 1.0
    
    # 3. Update A and b with reward 1.0
    A_updated = A + np.outer(x, x)
    b_updated = b + 1.0 * x
    
    # 4. Compute new score
    score_new = compute_linucb_score(A_updated, b_updated, x, alpha=1.0)
    # The variance x^T * A_updated^-1 * x should shrink, while the prediction term becomes positive
    assert score_new != score

def test_clinical_rules():
    # 1. Define high fatigue twin state
    twin_state_fatigue = {"fatigue": 0.90, "sleep": 0.7}
    filtered_fatigue = apply_clinical_rules(MISSION_POOL, twin_state_fatigue)
    
    # Verify no academic or physical missions (except desk stretching or priority matrix)
    for m in filtered_fatigue:
        if m["category"] in ["physical", "academic"]:
            assert m["mission_id"] in ["body-stretching-flow", "academic-matrix-priority"]
            
    # 2. Define excellent sleep twin state
    twin_state_sleep = {"fatigue": 0.2, "sleep": 0.90}
    filtered_sleep = apply_clinical_rules(MISSION_POOL, twin_state_sleep)
    for m in filtered_sleep:
        assert m["category"] != "sleep"

    # 3. Define active mission exclusion
    filtered_active = apply_clinical_rules(MISSION_POOL, {}, active_mission_ids=["academic-pomodoro-focus"])
    for m in filtered_active:
        assert m["mission_id"] != "academic-pomodoro-focus"

def test_context_vector_assembly():
    twin_state = {
        "stress": 0.8,
        "anxiety": 0.6,
        "fatigue": 0.5,
        "sleep": 0.4,
        "resilience": 0.5,
        "mood": 0.5,
        "focus": 0.5,
        "academic": 0.8,
        "social": 0.4
    }
    user_context = {
        "time_of_day": 0.6,
        "is_weekend": 1.0,
        "screen_time_index": 0.8,
        "calendar_availability": 0.4,
        "steps_ratio": 0.5,
        "past_completion_rate": 0.6
    }
    
    x = get_context_vector(twin_state, user_context)
    assert len(x) == 15
    assert pytest.approx(np.linalg.norm(x)) == 1.0

def test_api_endpoints():
    client = TestClient(app)
    
    # 1. Test taxonomy
    response = client.get("/api/v1/interventions/taxonomy")
    assert response.status_code == 200
    assert len(response.json()) == 24
    
    # 2. Test recommend
    rec_payload = {
        "student_id": "test-std-1",
        "twin_state": {
            "stress": 0.6, "anxiety": 0.5, "fatigue": 0.8, "social": 0.4, 
            "academic": 0.7, "sleep": 0.4, "mood": 0.5, "resilience": 0.6, "focus": 0.5
        },
        "user_context": {
            "time_of_day": 0.6, "is_weekend": 0.0, "screen_time_index": 0.8
        },
        "active_mission_ids": []
    }
    response = client.post("/api/v1/interventions/recommend", json=rec_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "test-std-1"
    assert len(data["recommendations"]) == 10
    
    # 3. Test feedback
    feedback_payload = {
        "student_id": "test-std-1",
        "mission_id": "mental-breathing-box",
        "reward": 1.0,
        "twin_state": rec_payload["twin_state"],
        "user_context": rec_payload["user_context"]
    }
    response = client.post("/api/v1/interventions/feedback", json=feedback_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # 4. Test parameter summary
    response = client.get("/api/v1/interventions/parameters")
    assert response.status_code == 200
    assert len(response.json()) > 0
    
    # 5. Test history logs
    response = client.get("/api/v1/interventions/history")
    assert response.status_code == 200
    assert len(response.json()) > 0
    
    # 6. Test simulation
    sim_payload = {
        "profile_name": "Stressed Academic",
        "iterations": 10
    }
    response = client.post("/api/v1/interventions/simulate", json=sim_payload)
    assert response.status_code == 200
    sim_data = response.json()
    assert sim_data["profile_name"] == "Stressed Academic"
    assert len(sim_data["history"]) > 0
