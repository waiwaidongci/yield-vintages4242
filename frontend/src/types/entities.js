// API实体字段约定：来源{id,natural_key,data,format_version}（data件数为1–30位十进制字符串，format_version 1=旧表示待转换、2=新表示）、口径{id,version,data}、报告{id,status,snapshot,checksum,result,approved}（结果中分子/分母合计与良率为精确字符串，良率八位小数）、计划{next_at,enabled}、转换状态{status,total,converted,pending,failures,error}。
export const ENTITY_KEYS=['sources','policies','runs','schedules','deliveries'];
