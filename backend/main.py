from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

import backend.services as services

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sbar_dados.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SubmissionDB(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String)
    student_email = Column(String)
    situation = Column(Text)
    background = Column(Text)
    assessment = Column(Text)
    recommendation = Column(Text)

Base.metadata.create_all(bind=engine)

class SubmissionCreate(BaseModel):
    student_name: str
    student_email: EmailStr
    situation: str
    background: str
    assessment: str
    recommendation: str

def task_process(sub: SubmissionCreate):
    data_ia = services.analyze_sbar(sub.situation, sub.background, sub.assessment, sub.recommendation)
    services.send_email(sub.student_email, data_ia, sub.situation, sub.background, sub.assessment, sub.recommendation)

@app.post("/api/submit")
async def submit_sbar(sub: SubmissionCreate, background_tasks: BackgroundTasks):
    try:
        db = SessionLocal()
        db_sub = SubmissionDB(**sub.dict())
        db.add(db_sub)
        db.commit()
        db.close()

        background_tasks.add_task(task_process, sub)
        return {"message": "SBAR enviado com sucesso! O feedback chegará no seu e-mail em instantes."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Monta a pasta frontend na raiz do site
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")