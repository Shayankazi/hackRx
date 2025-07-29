from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from config.settings import settings
from models.database import Base


class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.is_initialized = False
    
    def initialize(self):
        """Initialize database connection"""
        if self.is_initialized:
            return
        
        # Create database engine
        self.engine = create_engine(
            settings.DATABASE_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        self.is_initialized = True
        print("Database initialized successfully")
    
    def get_session(self) -> Session:
        """Get a database session"""
        if not self.is_initialized:
            self.initialize()
        return self.SessionLocal()
    
    @contextmanager
    def get_session_context(self):
        """Get a database session with context management"""
        if not self.is_initialized:
            self.initialize()
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


# Global instance
db_manager = DatabaseManager()


def get_db():
    """Dependency for FastAPI to get database session"""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()
