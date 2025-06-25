from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# Create the SQLAlchemy engine
# connect_args={'check_same_thread': False} is needed for SQLite to allow multiple threads
# to interact with the database, which is common in web applications.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class
# This class will be an actual database session for a single request.
# The `autocommit=False` and `autoflush=False` settings ensure that
# changes are not committed until explicitly told to, and objects are not
# flushed to the database automatically.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models
# This is the base class that our SQLAlchemy models will inherit from.
Base = declarative_base()

# Dependency to get a database session
# This function will be used with FastAPI's Depends to inject a database session
# into our path operations. It ensures that the session is properly closed
# after the request is finished.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()