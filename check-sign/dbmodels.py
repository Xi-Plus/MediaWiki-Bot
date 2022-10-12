from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    last_warn = Column(DateTime, server_default='1970-01-01')
    warn_count = Column(Integer, server_default='0')

    def __repr__(self):
        return f'User(id={self.id!r}, name={self.name!r})'


if __name__ == '__main__':
    import configparser

    from config import USERDB_CONFIG_PATH

    reader = configparser.ConfigParser()
    reader.read(USERDB_CONFIG_PATH)
    USERDB_HOST = reader.get('client', 'host')
    USERDB_PORT = reader.get('client', 'port')

    engine = create_engine(
        f'mysql+pymysql://{USERDB_HOST}:{USERDB_PORT}',
        connect_args={'read_default_file': USERDB_CONFIG_PATH},
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user1 = User(name='Example')
        session.add(user1)
        session.commit()
