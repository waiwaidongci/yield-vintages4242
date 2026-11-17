from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker,DeclarativeBase
from src.config.settings import DATABASE_URL
class Base(DeclarativeBase): pass
engine=create_engine(DATABASE_URL,pool_pre_ping=True)
Session=sessionmaker(bind=engine,expire_on_commit=False)
def database():
 with Session() as db: yield db
def ensure_schema():
 if engine.dialect.name!='mysql': return
 with engine.begin() as c:
  cols={r[0] for r in c.execute(text("SHOW COLUMNS FROM yield_lots"))}
  if 'format_version' not in cols:
   try: c.execute(text("ALTER TABLE yield_lots ADD COLUMN format_version INT NOT NULL DEFAULT 1"))
   except Exception as exc:
    if 'Duplicate column' not in str(exc): raise
