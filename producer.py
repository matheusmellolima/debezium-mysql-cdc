"""Producer for Debezium MySQL connector."""
import logging
import uuid
from sqlalchemy import create_engine, String, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, mapped_column
from faker import Faker


def get_logger():
    """Get logger."""
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger("debezium-mysql-cdc.producer")
    logger.setLevel(logging.INFO)

    if not logger.hasHandlers():
        ch = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


log = get_logger()

engine = create_engine(
    "mysql+pymysql://debezium:dbz@localhost:3306/testdb",
    logging_name="debezium-mysql-cdc.producer")

_SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    """User model."""
    __tablename__ = 'user'

    id = mapped_column(String(255), primary_key=True)
    name = mapped_column(String(255), nullable=False)
    email = mapped_column(String(255), nullable=False)

    def __init__(self, name, email):
        self.id = uuid.uuid4().hex
        self.name = name
        self.email = email

    def __repr__(self):
        return f"User(name={self.name}, email={self.email})"


def session_factory():
    """Create session factory."""
    User.metadata.create_all(engine)
    return _SessionFactory()


def check_database_health(database_session: Session):
    """Check database health."""
    is_database_working = True
    output = 'OK'

    try:
        # to check database we will execute raw query
        database_session.execute(text('SELECT 1'))
    except Exception as e:
        output = str(e)
        is_database_working = False

    return is_database_working, output


if __name__ == "__main__":
    log.info("Creating session...")
    session = session_factory()
    log.info("Checking database health...")
    is_ok, error = check_database_health(session)
    log.info("Database health check: %s", error)

    log.info("Inserting users...")
    fake = Faker(locale="en_US")
    for i in range(1, 100):
        user = User(name=fake.name(), email=fake.email())
        log.info("Inserting user (id=%d) (user=%s)", i, user)
        session.add(user)
        session.commit()

    session.close()
