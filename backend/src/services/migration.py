import time
from sqlalchemy import update,func
from src.models.source import Source
from src.models.migration import MigrationState
from src.services.validation import normalize_source
from src.services.audit import log
NAME='counts-30d-v2'
BATCH=50
MAX_FAILURES=100
def state(db):
 st=db.query(MigrationState).filter_by(name=NAME).first()
 if not st:
  st=MigrationState(name=NAME,status='pending',total=0,converted=0,pending=0,failures=[],error='',updated=time.time())
  db.add(st)
  try:db.commit()
  except Exception:
   db.rollback();st=db.query(MigrationState).filter_by(name=NAME).first()
 return st
def counts(db):
 total=db.query(func.count(Source.id)).scalar() or 0
 converted=db.query(func.count(Source.id)).filter(Source.format_version>=2).scalar() or 0
 return total,converted,total-converted
def tick(db):
 st=state(db)
 if st.status not in ('pending','running'):return
 try: run_pass(db,st)
 except Exception as exc:
  db.rollback()
  try:
   st=state(db);st.status='failed';st.error='转换中断：'+str(exc);st.updated=time.time();db.commit()
  except Exception: db.rollback()
def run_pass(db,st):
 st.status='running'
 failures=list(st.failures or [])
 failed_ids=[f['id'] for f in failures]
 q=db.query(Source).filter(Source.format_version<2)
 if failed_ids:q=q.filter(~Source.id.in_(failed_ids))
 rows=q.order_by(Source.id).limit(BATCH).all()
 overflow=False
 for row in rows:
  try:new_data=normalize_source(row.data)
  except ValueError as exc:
   if len(failures)<MAX_FAILURES:failures.append({'id':row.id,'reason':str(exc)})
   else:overflow=True
   continue
  # 比较并交换：仅当记录仍是旧版时写回；并发修改已置新版、删除已移除记录，此处自然跳过，不覆盖新修改、不复活已删记录
  db.execute(update(Source).where(Source.id==row.id,Source.format_version<2).values(data=new_data,format_version=2))
 st.failures=failures
 if overflow:
  st.status='failed';st.error='转换失败超过'+str(MAX_FAILURES)+'条，请修正底稿后重试';log(db,'worker','migration.failed',st.error)
  st.total,st.converted,st.pending=counts(db);st.updated=time.time();db.commit();return
 if rows:
  st.total,st.converted,st.pending=counts(db)
 else:
  bad=[]
  last=0
  while True:
   batch=db.query(Source).filter(Source.id>last).order_by(Source.id).limit(200).all()
   if not batch:break
   for r in batch:
    try:
     if r.format_version!=2 or normalize_source(r.data)!=r.data:raise ValueError('底稿未转换为规范新表示')
    except ValueError as exc:
     if len(bad)<MAX_FAILURES:bad.append({'id':r.id,'reason':str(exc)})
   last=batch[-1].id
  st.total,st.converted,st.pending=counts(db)
  if bad:
   st.status='failed';st.failures=bad;st.error='核对发现'+str(len(bad))+'条底稿未通过新表示校验';log(db,'worker','migration.failed',st.error)
  else:
   st.status='completed';st.error='';st.failures=[];st.pending=0;log(db,'worker','migration.completed','共'+str(st.total)+'条底稿全部核对通过')
 st.updated=time.time()
 db.commit()
def retry(db,user):
 st=state(db)
 if st.status=='failed':
  st.status='pending';st.failures=[];st.error='';st.updated=time.time();log(db,user.email,'migration.retry',NAME);db.commit()
 return st
