import re
from src.config.settings import CONFIG
COUNT_FIELDS=('input','first_pass','reworked_good','scrap')
MAX_DIGITS=30
DIGITS=re.compile(r'^[0-9]{1,30}$')
def parse_count(value,name):
 if isinstance(value,bool):raise ValueError(name+'数值不合法')
 if isinstance(value,int):n=value
 elif isinstance(value,float):
  if not value.is_integer() or abs(value)>=2**53:raise ValueError(name+'数值不合法')
  n=int(value)
 elif isinstance(value,str):
  if not DIGITS.fullmatch(value.strip()):raise ValueError(name+'须为1至'+str(MAX_DIGITS)+'位的非负整数')
  n=int(value.strip())
 else:raise ValueError(name+'数值不合法')
 if n<0 or len(str(n))>MAX_DIGITS:raise ValueError(name+'超过'+str(MAX_DIGITS)+'位整数上限')
 return n
def normalize_source(d):
 if not isinstance(d,dict) or set(d)!=set(CONFIG['fields']):raise ValueError('底稿字段必须与业务字段一致')
 out={}
 for key in ('period','department'):
  if not isinstance(d[key],str) or not 1<=len(d[key])<=100:raise ValueError(key+'不能为空或过长')
  out[key]=d[key]
 if not isinstance(d['shift'],str) or not d['shift']:raise ValueError('班次不能为空')
 out['shift']=d['shift']
 for k in COUNT_FIELDS:out[k]=str(parse_count(d[k],k))
 if int(out['input'])<=0 or int(out['first_pass'])+int(out['reworked_good'])+int(out['scrap'])!=int(out['input']):raise ValueError('投入必须大于0且一次通过+返工合格+报废应等于投入')
 return out
def validate_source(d):normalize_source(d)
def validate_policy(d):
 if not isinstance(d,dict) or not isinstance(d.get('version'),str) or not 2<=len(d['version'])<=120: raise ValueError('口径版本名不合法')
 if d.get('numerator') not in ('first_pass','total_good') or d.get('denominator') not in ('input','non_scrap'):raise ValueError('分子分母口径无效')
 if not isinstance(d.get('description'),str):raise ValueError('必须填写口径说明')
