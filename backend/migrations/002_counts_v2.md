# 002 件数30位精确表示（counts-30d-v2）

## 背景
件数超过 2^53（约九千万亿）后，浏览器 Number、MySQL JSON 数值与浮点除法都会丢尾数。件数改为十进制整数字符串（1–30 位）全程传输与存储；良率按分子÷分母精确四舍五入到八位小数。

## 结构变更
- `yield_lots` 新增 `format_version INT NOT NULL DEFAULT 1`：1=旧表示（JSON 数值），2=新表示（十进制字符串）。应用启动时 `ensure_schema()` 对存量库在线 `ALTER TABLE`；新库由 `create_all` 直接建全。
- 新增表 `migration_state`（单列族：name 唯一，status/total/converted/pending/failures/error/updated），由 `create_all` 创建。

```sql
ALTER TABLE yield_lots ADD COLUMN format_version INT NOT NULL DEFAULT 1;
CREATE TABLE migration_state (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(80) UNIQUE,
  status VARCHAR(20),
  total INT, converted INT, pending INT,
  failures JSON, error TEXT, updated DOUBLE
);
```

## 在线转换（worker 每轮一批，50 条/批）
1. 扫描 `format_version<2` 的底稿，逐条规范化后用 CAS 写回：`UPDATE ... WHERE id=? AND format_version<2`。并发增改（写入即置 2）与删除使 CAS 落空自然跳过——不覆盖新修改、不复活已删记录；转换只 UPDATE 不 INSERT/DELETE。
2. 无存量旧版记录后进入核对：全表分批重读，要求每条 `format_version=2` 且数据等于规范化新表示；全部通过才置 `completed`，否则置 `failed` 并记录失败明细。
3. 中断恢复：状态持久化于 `migration_state`，worker 重启继续扫描剩余旧版记录；转换幂等，重试不漏转、不重复。`POST /migration/retry`（admin）将 failed 重置为 pending 重跑。
4. 转换期间写入路径（保存底稿、提交核算）一律产出新表示；核算提交时把快照内全部底稿规范化为同版新表示，保证每份报告采用完整同版底稿。
5. 已冻结报告（yield_runs.snapshot/checksum/result）与交付（deliveries.payload）不做任何改写，原值与指纹保持不变；旧表示数据读取路径全程兼容。
