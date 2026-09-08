import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vigilant.db")

# For SQLite, ensure connect_args allows multi-threaded access if needed
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency to yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables."""
    import database.models  # Ensure models are registered with Base
    Base.metadata.create_all(bind=engine)
    # The prototype has no migration dependency.  Keep existing local SQLite
    # databases usable when additive research columns are introduced.
    if engine.dialect.name == "sqlite":
        columns = {column["name"] for column in inspect(engine).get_columns("consistency_findings")}
        if columns and "confidence" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE consistency_findings "
                        "ADD COLUMN confidence FLOAT NOT NULL DEFAULT 0.0"
                    )
                )
