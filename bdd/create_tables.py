from db_config import engine
from models import Base

Base.metadata.create_all(bind=engine)
