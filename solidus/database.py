import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_URL = "sqlite:///./database.db"

# Database setup with SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True, index=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    prompt = Column(String, index=True)
    file_identifier = Column(String, unique=True, index=True)
    headers = Column(JSON)
    output = Column(String, index=True)
    error = Column(String, index=True)
    files = Column(ARRAY(String))


class Statistics(Base):
    __tablename__ = 'statistics'
    id = Column(Integer, primary_key=True)
    numRequestSuccess = Column(Integer, nullable=False, default=0)
    numRequestFailed = Column(Integer, nullable=False, default=0)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
