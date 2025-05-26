import os
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv('ENVIRONMENT', "DEVELOPMENT")

DATABASE_URL = os.getenv('DATABASE_URL')
# DEVELOPMENT_DATABASE_URL = os.getenv('DEVELOPMENT_DATABASE_URL')
DEVELOPMENT_DATABASE_URL = os.getenv('DATABASE_URL')

SQLALCHEMY_DATABASE_URL = (
    DATABASE_URL if ENVIRONMENT == "PRODUCTION" else DEVELOPMENT_DATABASE_URL
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
