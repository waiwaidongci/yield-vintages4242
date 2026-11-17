from sqlalchemy import Column,Integer,String,JSON,Text,Float
from src.config.database import Base
class MigrationState(Base):
 __tablename__='migration_state'
 id=Column(Integer,primary_key=True); name=Column(String(80),unique=True); status=Column(String(20))
 total=Column(Integer,default=0); converted=Column(Integer,default=0); pending=Column(Integer,default=0)
 failures=Column(JSON,default=list); error=Column(Text,default=''); updated=Column(Float)
