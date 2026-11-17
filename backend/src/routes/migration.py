from fastapi import APIRouter,Depends
from src.config.database import database
from src.controllers.auth import current,admin
from src.services.migration import state,counts,retry
router=APIRouter()
def view(db,st):
 total,converted,pending=counts(db)
 return {'name':st.name,'status':st.status,'total':total,'converted':converted,'pending':pending,'failures':st.failures or [],'error':st.error or '','updated':st.updated}
@router.get('/migration')
def migration(db=Depends(database),u=Depends(current)): return view(db,state(db))
@router.post('/migration/retry')
def migration_retry(db=Depends(database),u=Depends(admin)): return view(db,retry(db,u))
