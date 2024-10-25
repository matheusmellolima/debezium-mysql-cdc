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
    "mysql+pymysql://debezium:dbz@localhost:3306/debezium",
    logging_name="debezium-mysql-cdc.producer")

_SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    """User model."""
    __tablename__ = 'user'

    user_id = mapped_column(String(255), primary_key=True)
    first_name = mapped_column(String(50), nullable=False)
    last_name = mapped_column(String(50), nullable=False)
    city = mapped_column(String(50), nullable=False)
    state = mapped_column(String(50), nullable=False)
    zipcode = mapped_column(String(10), nullable=False)

    def __init__(self, first_name, last_name, city, state, zipcode):
        self.user_id = uuid.uuid4().hex
        self.first_name = first_name
        self.last_name = last_name
        self.city = city
        self.state = state
        self.zipcode = zipcode

    @property
    def name(self):
        """Get user name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"User(name={self.name}, uuid={self.user_id})"


def session_factory():
    """Create session factory."""
    User.metadata.drop_all(engine)
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
    for i in range(1, 101):
        user = User(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            city=fake.city(),
            state=fake.state(),
            zipcode=fake.zipcode(),
        )
        log.info("Inserting user (no=%d) (user=%s)", i, user)
        session.add(user)
        session.commit()

    session.close()
