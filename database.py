import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Session, sessionmaker

load_dotenv()

Base = declarative_base()


def init_db(test: bool = False):
    url = 'sqlite:///:memory:' if test else os.getenv('DATABASE_URL')
    db_engine = create_engine(
        url,
        echo=os.getenv('ECHO', 'False').lower() == 'true',
        connect_args={'check_same_thread': False} if 'sqlite' in url else {},
    )

    session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    Base.metadata.create_all(db_engine)
    return db_engine, session


engine, session_factory = init_db()


def get_session() -> Generator[Session, None, None]:
    db_session = session_factory()

    try:
        yield db_session
    finally:
        db_session.close()


def close_db():
    engine.dispose()
