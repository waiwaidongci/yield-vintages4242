from collections import defaultdict
from src.services.validation import normalize_source,validate_policy
SCALE=100_000_000
def rate8(num,den):
 q,r=divmod(num*SCALE,den)
 if r*2>=den:q+=1
 return str(q//SCALE)+'.'+str(q%SCALE).zfill(8)
def calculate(sources,policy):
 validate_policy(policy);pivot=defaultdict(lambda:[0,0,0]);rows=[]
 for s in sources:
  d=normalize_source(s);fp=int(d['first_pass']);rw=int(d['reworked_good']);inp=int(d['input']);scrap=int(d['scrap'])
  num=fp if policy['numerator']=='first_pass' else fp+rw;den=inp if policy['denominator']=='input' else inp-scrap
  if den<=0:raise ValueError('口径分母为0：'+d['department']+' '+d['period'])
  k=(d['period'],d['department'],d['shift']);p=pivot[k];p[0]+=num;p[1]+=den;p[2]+=1
 for (period,dept,shift),(num,den,count) in sorted(pivot.items()):rows.append({'日期':period,'试制线':dept,'班次':shift,'批数':count,'分子合计':str(num),'分母合计':str(den),'良率':rate8(num,den)})
 n=sum(p[0] for p in pivot.values());d=sum(p[1] for p in pivot.values())
 return {'summary':{'批次数':len(sources),'分子合计':str(n),'分母合计':str(d),'加权良率':rate8(n,d) if d else '0.00000000','口径版本':policy['version']},'rows':rows,'method':'逐批按冻结版本选取分子/分母，再按日期×试制线×班次累加。汇总率=分子总数/分母总数，不对批次率做简单平均。可选口径仅为一次通过/总合格与全部投入/扣报废投入。件数按十进制整数精确处理（最长30位），良率按分子÷分母精确四舍五入到八位小数。','warnings':['扣报废分母会提升显示良率；比较不同版本时必须同时阅读分子与分母定义。']}
