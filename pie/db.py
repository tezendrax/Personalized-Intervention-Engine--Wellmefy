import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from pie.config import settings

Base = declarative_base()
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class BanditParameter(Base):
    __tablename__ = "bandit_parameters"

    mission_id = Column(String(64), primary_key=True, index=True)
    matrix_a_json = Column(Text, nullable=False)  # Serialized 2D list of float (d x d)
    vector_b_json = Column(Text, nullable=False)  # Serialized 1D list of float (d)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def matrix_A(self):
        return json.loads(self.matrix_a_json)

    @matrix_A.setter
    def matrix_A(self, val):
        self.matrix_a_json = json.dumps(val)

    @property
    def vector_b(self):
        return json.loads(self.vector_b_json)

    @vector_b.setter
    def vector_b(self, val):
        self.vector_b_json = json.dumps(val)

class RecommendationLog(Base):
    __tablename__ = "recommended_interventions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(64), index=True, nullable=False)
    context_vector_json = Column(Text, nullable=False)  # Serialized float list (x_t)
    recommendations_json = Column(Text, nullable=False)  # Serialized top 3 recommended items
    chosen_mission_id = Column(String(64), nullable=True)  # Set when a user starts/accepts a mission
    reward = Column(Float, nullable=True)  # 1.0 if completed, 0.0 if skipped/ignored
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def context_vector(self):
        return json.loads(self.context_vector_json)

    @context_vector.setter
    def context_vector(self, val):
        self.context_vector_json = json.dumps(val)

    @property
    def recommendations(self):
        return json.loads(self.recommendations_json)

    @recommendations.setter
    def recommendations(self, val):
        self.recommendations_json = json.dumps(val)

def init_db():
    Base.metadata.create_all(bind=engine)
