import os
from dotenv import load_dotenv
from sqlalchemy import Table, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
load_dotenv()

schema = 'public'
SQLALCHEMY_DATABASE_URL = os.getenv("POSTGRES_URL")
success_message = "Request processed successfully "

def setup_db():
    engine = create_engine(SQLALCHEMY_DATABASE_URL,
                           pool_pre_ping=True, pool_recycle=3600)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal, engine

Base = declarative_base()
SessionLocal, engine = setup_db()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


    
class Session(Base):
    __table__ = Table('session', Base.metadata,
                      schema=schema, autoload_with=engine)

class Users(Base):
    __table__ = Table('users', Base.metadata,
                      schema=schema, autoload_with=engine)

class Generic(Base):
    __table__ = Table('generic_text', Base.metadata,
                      schema=schema, autoload_with=engine)
    
class Image(Base):
    __table__ = Table('image_data', Base.metadata,
                      schema=schema, autoload_with=engine)
    
class BlogData(Base):
    __table__ = Table('blog_data', Base.metadata,
                      schema=schema, autoload_with=engine)
    
class PptData(Base):
    __table__ = Table('ppt_data', Base.metadata,
                      schema=schema, autoload_with=engine)
    
class PdfData(Base):
    __table__ = Table('pdf_data', Base.metadata,
                      schema=schema, autoload_with=engine)
    