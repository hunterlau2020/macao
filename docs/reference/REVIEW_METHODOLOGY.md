# Washdb 评审方法论

> **版本**：v2.2（2026-08-09）
> **状态**：候选强制规范，完成双签后生效  
> **适用对象**：财务数据 Loader、Raw/Normalized/Candidates/Cleaned/Audit Pipeline、策略与实现文档  
> **上位准则**：`docs/CLEAN_FINANCIAL_STATEMENT_PRINCIPLE.md`  
> **相关设计**：`docs/US_FINANCIAL_CLEANING_STRATEGY_V3.md`、`docs/US_FINANCIAL_PIPELINE_IMPLEMENTATION.md`

本方法论的核心是：

```text
声明 → 文档/代码 → 实表 → 反例与失败路径 → 上位准则
```

任何“通过”都必须指明评审对象、构建版本、证据、适用门禁和未决风险。作者自述、成功日志、单只股票样本及 reviewer 投票均不能代替证据。

---

## 1. 目的、边界与文档分工

### 1.1 目的

1. 防止把“方向正确”“代码存在”“实表正确”“可生产发布”混为一谈；
2. 防止只看提交说明、AAPL/MSFT 样本或输出行数；
3. 验证正常路径、异常路径、历史版本、身份、期间、币种单位及会计语义；
4. 使结论可复现、可反驳、可追溯到不可变输入和构建；
5. 允许不同 Phase 并行编码，同时隔离未验收数据依赖；
6. 让 reviewer 的遗漏、分歧和修正同样进入审计记录。

### 1.2 适用范围按风险裁剪

| 对象 | 最低适用章节 |
|---|---|
| 新 Loader / 重大 Loader 变更 | 全文 |
| Raw/Normalized/Candidates/Cleaned/Audit Pipeline | 全文，并增加跨层、跨源和发布验证 |
| 策略或实现文档 | §1–§6、§9、§12、§15；实表部分改为“文档—代码—现状一致性” |
| 一次性研究脚本 | §2、§3、§7、§13；若进入正式数据流则立即按 Loader 全文执行 |
| 纯文字/格式修改 | DOC-VERIFIED、引用与一致性检查；无需虚构 DATA/TEST 证据 |

不得以“一次性脚本”为名绕过门禁后写入生产表。

### 1.3 稳定规范与实时状态分离

本文件只保存稳定规范。以下内容必须另存：

```text
docs/reviews/STATUS.md                         当前 Phase/门禁状态
docs/reviews/<phase>_<commit>_<reviewer>.md   单次评审
docs/reviews/consensus_<phase>_<commit>.md    分歧裁决
docs/reviews/meta_<yyyy-mm>.md                reviewer 偏差复盘
```

不得把某个临时 commit、当前队列或项目进度写进本规范正文。

---

## 2. 四级结论与四类 Phase Gate

### 2.1 四级结论

| 级别 | 结论 | 最低条件 | 允许动作 |
|---|---|---|---|
| **L1** | 设计方向可接受 | DOC-VERIFIED；与 PRINCIPLE 逐条相容；关键假设显式 | 允许编码或原型 |
| **L2** | 代码实现与设计一致 | L1 + CODE-VERIFIED；静态检查和单元测试通过 | 允许继续开发，不代表数据可消费 |
| **L3** | 指定 build 的数据结果通过 | L2 + DATA-VERIFIED；所有适用 P0/P1 失败路径 TEST-VERIFIED；对账闭合 | 具备申请下游消费资格 |
| **L4** | 可生产发布 | L3 + SEC 核验、Legacy diff、质量报告、回滚演练、运维门禁 | 允许正式发布 |

`UNKNOWN` 不等于 PASS；局部 PASS 不得外推为整个阶段 PASS。

### 2.2 Phase Gate

| 门禁 | 含义 | 条件 |
|---|---|---|
| **PG-0** | 允许开始编码 | L1 |
| **PG-1** | 当前 Phase 内部验收 | 当前 Phase L3；P0/P1 为零 |
| **PG-2** | 允许下游读取/依赖 | PG-1 + 接口稳定 + consumer contract 测试 |
| **PG-3** | 生产发布 | L4 |

后续 Phase 可以在 PG-0 后并行编码，但不得读取尚未达到 PG-2 的上游正式表。测试只能使用 fixture、mock 或明确标记的实验 build。

---

## 3. 证据模型

### 3.1 证据类型与验证状态分离

证据类型：

| 类型 | 含义 |
|---|---|
| **DOC** | 文档、上位准则、字段定义和设计合同 |
| **CODE** | reviewer 静态检查指定 commit 的代码 |
| **DATA** | reviewer 对指定 build 独立执行实表查询 |
| **TEST** | 正常、边界、失败和恢复路径测试 |
| **SEC** | SEC accession、accepted_at、XBRL concept/context/unit 原始证据 |
| **OPS** | 调度、并发、资源、锁、恢复、发布和回滚演练 |

验证状态：

```text
VERIFIED
PARTIALLY_VERIFIED
CLAIM_ONLY
UNKNOWN
CONTRADICTED
NOT_APPLICABLE
```

不能把 DATA 简单视为比 CODE“更高级”；它们回答不同问题。一个结论可能同时需要 CODE、DATA 和 TEST。

### 3.2 证据记录

每条证据至少保存：

```yaml
evidence_id: P0.2-<full_commit_sha>-001
type: DATA
status: VERIFIED
build_id: <immutable_build_id>
input_manifest_sha256: <sha256>
query_or_test: <可复现命令、SQL 或测试名>
result_artifact: <相对路径>
reviewer: <name>
executed_at: <timestamp_with_timezone>
limitations: <已知限制>
```

短 commit SHA 只用于展示，证据必须关联完整 SHA。查询输出应持久化，不能只存在终端滚屏或 agmsg 简报。

### 3.3 证据最低要求

- L1：DOC/PRINCIPLE trace 为 VERIFIED；
- L2：CODE 为 VERIFIED，关键静态规则与单元测试通过；
- L3：DATA 为 VERIFIED，所有适用 P0/P1 控制有 TEST 证据；
- L4：SEC + OPS 为 VERIFIED，并完成 §12 发布门禁。

“至少跑一个测试”不能使整个 L3 通过。

---

## 4. 声明验证矩阵

作者提交中的每个强声明必须转成检查项。

| 声明 | 必须验证 |
|---|---|
| lossless / 全字段保留 | 输入 manifest、schema diff、行漏斗、source row identity、解析异常 |
| atomic publish | 明确事务边界；切换中断后旧 approved build 是否仍可查询 |
| append-only | 是否覆盖旧 build/filing；旧版本是否仍可查询 |
| source_file | 是否对应 manifest 中真实文件；单文件来源允许一个值 |
| reconciliation | 是否持久化；是否满足 input = loaded + quarantined + rejected |
| idempotent | 相同输入/代码/配置重跑，稳定业务记录及构建 checksum 是否相同 |
| 合法多版本 | 是否有 accession/accepted_at 或可批准的版本证据 |
| latest-restated | 是否使用合法 filing 版本链，而不是供应商更新时间猜测 |
| PIT | 是否不存在未来 filing、未来拆股、未来行业或供应商快照前视 |
| CIK 覆盖率 | 行、ticker、permaticker、active/delisted 分母及缺失原因 |
| 去重/消除扇出 | 被淘汰记录是否一致；是否存在身份或时变属性差异 |
| schema 演化安全 | 新增、缺失、类型变化和未知列是否阻断或隔离 |
| 可回滚 | 上一 approved build、配置和下游引用能否恢复 |

Loader 的 `--describe` 只用于生成待验证声明清单，属于 CLAIM_ONLY，不能替代 commit diff、实表和测试。

---

## 5. 财务语义与实例硬门

工程结果正确不代表财务含义正确。任何进入 Candidates/Cleaned 的记录必须审计：

```text
永久公司身份
证券/share class（EPS 和股数）
statement_type
report_period_start/end
duration_days
fiscal_year / fiscal_period
FY / single-quarter / YTD / TTM
form_type / accession / accepted_at / version
reported_currency / 原始单位 / 标准化单位
accounting_standard
consolidation_scope
instant / duration
crosswalk_version / semantic_definition
split / ADR ratio adjustment policy
```

### 5.1 高风险语义

至少单独检查：

- consolidated / parent / common net income；
- parent equity / NCI / total equity / mezzanine equity；
- revenue / total revenue；
- CFO / cash net change / ending cash；
- basic/diluted EPS 与加权平均股数；
- 资产负债表 instant 与利润/现金流 duration；
- 52/53 周财年和非自然财年；
- 银行、保险、REIT、SPAC、矿业、生物科技的 N/A 字段。

### 5.2 PIT 强约束

`lastupdated`、抓取时间和当前 TICKERS 属性不自动等于 filing vintage。正式 PIT 至少需要：

```text
filing_accession
SEC accepted_at
source_snapshot_at
knowledge_at
version chain
effective-dated identity/industry/split evidence
```

近似 PIT 必须命名为 approximate，默认禁止回测消费。

---

## 6. 重复、冲突与版本分类

Raw 层不得因“重复”删除来源记录。Raw 保存 source row；Normalized/Audit 使用 `source_record_id` 和完整行指纹建立等价组。

| 类别 | 证据 | 处理 |
|---|---|---|
| **R1 exact_duplicate** | 同 source key、完整规范化行指纹相同 | Raw 全保留；Normalized 可标记 canonical representative，保留成员关系 |
| **R2 vendor_snapshot_duplicate** | 相同事实、不同供应商快照/抓取时间 | 保留快照链；不得冒充 filing version |
| **R3 filing_version** | accession/accepted_at/form/context 证明不同 filing | 建立 filing 版本链 |
| **R4 amended_filing** | accession/form 明确为 amendment | 保留修订范围；不得假设所有字段都被替代 |
| **R5 value_conflict** | 同 verified instance/version 但数值冲突 | 隔离并查单位、币种、语义、供应商处理 |
| **R6 identity_conflict** | ticker 对应不同 CIK/permaticker 或有效期冲突 | 拆分实体或隔离，不得任取 latest |
| **R7 unresolved** | 证据不足 | 保留全部候选，禁止自动选源 |

禁止：

- 把所有重复称为重述；
- 以最新 `lastupdated` 选择 latest-restated；
- 对并列排序键任意 `ROW_NUMBER()=1`；
- 在 Raw 阶段删除 R1；
- 依靠评分掩盖版本、身份或语义冲突。

latest-restated 应基于合法 filing 版本链，通常以 SEC `accepted_at + accession + form_type` 为主要证据。10-K/A、10-Q/A 需审计具体修订范围。

---

## 7. Loader Contract 与对账

### 7.1 不可变输入 manifest

每个 build 至少保存：

```text
source_file
relative_path
full_file_sha256
file_size
mtime（仅辅助，非身份）
source_snapshot_at
schema_fingerprint
loader_version
full_commit_sha
config_version
build_id
```

不得只 hash 文件前缀。输入身份使用完整文件 SHA-256。

### 7.2 Source record identity

每条 Raw 记录至少可追溯：

```text
source_file_id
source_row_number 或稳定来源 record id
raw_record_fingerprint
ingested_at
build_id
```

CSV/JSON 原始文本、解析值和转换状态按来源风险保存。未知字段不得静默消失。

### 7.3 Reconciliation

必须在 approved build 切换前持久化：

```text
discovered_files
read_ok_files
failed_files
empty_files
input_records
raw_loaded
normalized
filtered_by_policy
quarantined
rejected
duplicate_classification
schema_added/removed/type_changed
date_parse_status
identity_mapping_status
unknown_fields
```

最低恒等式：

```text
input_records
= raw_loaded
 + explicitly_rejected_before_raw
```

若 Raw 忠实接收全部记录，则 `input_records = raw_loaded`。Normalized 漏斗另行满足：

```text
raw_loaded
= normalized
 + filtered_by_approved_policy
 + quarantined
 + rejected_with_reason
```

stdout 摘要不能代替持久化 reconciliation。

### 7.4 Build、事务和 append-only

DuckDB 支持 ACID 事务，`ALTER TABLE` 遵循事务语义。应区分：

- 官方事务文档：<https://duckdb.org/docs/current/sql/statements/transactions>
- 官方 `ALTER TABLE` 事务语义：<https://duckdb.org/docs/stable/sql/statements/alter_table>

- **atomic switch**：同一数据库事务中切换对象，失败可回滚；
- **build versioning**：旧 build 仍可查询；
- **append-only filing history**：不同 filing/vendor snapshot 不被覆盖。

推荐：

```text
immutable input manifest
→ staging_<build_id>
→ pre-publish validation
→ immutable physical build/table or rows tagged build_id
→ transactionally switch approved view/config pointer
```

事务内 `DROP current + RENAME staging` 可以是 atomic switch，但仍不满足 build history。禁止以 `INSERT OR REPLACE` 覆盖不同 filing。

生产 gate 必须显式抛错并回滚；不得只依赖可被 `python -O` 关闭的 `assert`。

---

## 8. 实表最小检查

SQL 为模板，reviewer 必须按真实 schema 调整并保存执行结果；不得复制不可执行伪 SQL 后声称已验证。

### 8.1 Loader 必查

1. `DESCRIBE` 与输入 schema diff；
2. manifest 文件数、SHA-256 与实际输入一致；
3. NULL、空字符串、NaN/Infinity、解析失败分布；
4. input→Raw→Normalized 完整漏斗；
5. source_file/source_record_id/record fingerprint 抽样；
6. exact duplicate、value conflict、vendor snapshot、unresolved 分类；
7. CIK/permaticker/ticker/share-class 映射冲突；
8. 期间、版本、币种、单位、合并范围缺失；
9. build_id、commit/config/schema version；
10. 上一 build 与本 build 的差异分桶。

`source_file` 只有一个 distinct 值不一定是反模式；应与 manifest 中输入文件数比较。例如单一 SF1 CSV 合法，数千 FMP JSON 只有一个固定 prefix 则不合法。

### 8.2 Pipeline 必查

1. 下游只引用 PG-2 approved build；
2. verified instance key 完整；
3. rejected/quarantined 候选仍可追溯；
4. 核心语义字段组是否同 filing/version/source；
5. gap-fill 是否满足全部硬门并保留字段级来源；
6. latest-restated 与 PIT 是否物理或逻辑隔离；
7. 会计恒等式按来源、行业、字段组独立运行；
8. source selection reason、gate result 和 conflict flags 是否可查询；
9. Legacy diff 是否按身份/期间/版本/语义原因分类；
10. Cleaned 重建是否不修改 Raw。

---

## 9. 反例与边界样本

每个 market 建立版本化反例库，至少覆盖：

```text
退市与 ticker 复用
改名、并购、反向并购
多 share class
ADR / IFRS foreign private issuer
非自然财年、52/53 周财年
10-K/A、10-Q/A 和供应商重新加工
银行、保险、券商、REIT、公用事业
SPAC、临床期生物科技、零收入公司
负值、合法零值、极小分母
拆股、ADR ratio 变化
币种非 USD 和金额/股数数量级异常
同日多 filing、版本并列和无 accession
```

每个样本保存来源 commit、预期、复现 SQL/测试、影响和最后验证 build。成功样本只证明 happy path，不证明全量质量。

---

## 10. 安全的失败路径与恢复测试

### 10.1 测试隔离

所有破坏性 failure-path 测试必须：

1. 使用 `mktemp -d` 或测试框架临时目录；
2. 复制最小 fixture；
3. 使用独立临时 DuckDB；
4. 不修改 `data/` 中真实源文件；
5. 不连接生产数据库；
6. 优先使用 fault-injection hook，避免真实 `kill -9`；
7. 测试结束验证临时文件、锁和 WAL 恢复。

### 10.2 风险驱动测试矩阵

| 测试 | 预期 |
|---|---|
| 坏 JSON/CSV/编码 | Raw 或 quarantine 按合同处理；原因可计数，不静默丢失 |
| annual/quarter 子集缺失 | per-pattern 对账显示缺失，不伪造数据 |
| schema 新增/删除/变型 | schema gate 报告并按策略阻断或隔离 |
| staging 后校验失败 | approved build 不变 |
| 切换事务失败 | rollback 后旧 approved build 可查询 |
| 相同输入重跑 | 稳定业务记录、分类统计和 build checksum 一致 |
| 身份一对多 | 不任取 latest，进入 conflict/quarantine |
| 版本排序并列 | 不任取 `_rn=1`，保留 unresolved |
| loader 并发 | 明确单写者、锁超时与重试策略 |
| 磁盘/内存不足 | 失败可恢复，不留下半发布版本 |
| 临时目录残留 | 清理或可安全重用，不误删其他进程文件 |

P0/P1 相关测试全部通过后才可达到 L3；NOT_APPLICABLE 必须有理由。

---

## 11. 可复现性、哈希与隔离

### 11.1 不使用大表 `string_agg` 或不稳定 rowid

禁止把以下方式当作百万行表的正式证明：

```text
md5(string_agg(... ORDER BY rowid))
```

原因包括内存放大、rowid 不稳定、NULL/浮点/时区序列化歧义。

### 11.2 推荐校验

1. 输入文件使用完整 SHA-256；
2. 明确 canonical serialization（字段顺序、NULL、浮点、日期、时区）；
3. 每行计算 `record_hash`；
4. 按稳定 `source_record_id` 分区并计算分区 checksum；
5. 保存总行数、schema hash、NULL profile、分区 hash；
6. 对相同 input/code/config 的两个 build 比较上述产物；
7. 对非确定性字段（如 ingested_at）明确排除。

### 11.3 Loader isolation

重跑一个 loader 前后，对所有非目标表比较：

```text
schema hash
row count
partition checksum
approved build pointer
```

不得用不存在的 `make clean_all`、占位 SQL 或真实数据删除来证明重建。

---

## 12. SEC 抽样、统计门槛与生产发布

### 12.1 SEC 最小核验集

不少于 PRINCIPLE 规定的 30 家，并覆盖规定风险类型。每家公司至少验证：

```text
CIK/身份
report period / duration
form/accession/accepted_at
reported currency/unit
收入或利润核心字段
资产负债字段
现金流字段
EPS或加权平均股数
XBRL concept/context/unit
```

抽样计划还必须记录：

- 分层类别与每类样本数；
- 抽样种子或确定性选择规则；
- 字段级容差；
- 错误后的扩样规则；
- 缺陷率和适用置信区间；
- 样本不能外推为未覆盖来源/年份的准确率。

### 12.2 PG-3 必备条件

1. P0/P1 为零；
2. SEC 样本通过；
3. PRINCIPLE §28 质量报告齐备；
4. Legacy diff 完成并解释重大变化；
5. 字段级 lineage 可查询；
6. rollback 演练通过；
7. input/build/config/code 均可复现；
8. 资源、锁、调度和告警通过 OPS 验证；
9. 覆盖范围和已知限制已发布；
10. 下游变更通知与兼容性方案完成。

多数 reviewer 投票不能覆盖任何未解决 P0/P1。

---

## 13. 安全、供应链与运行质量

Loader/Pipeline 评审还应检查：

```text
来源授权与许可证
输入来源真实性、完整 SHA-256
依赖锁定与漏洞
API token/数据库凭证不进入代码和日志
路径/SQL 注入
压缩包路径穿越与压缩炸弹
超大文件/恶意 schema
访问权限和供应商数据保密
峰值内存、磁盘和 spill 预算
并发写、锁超时、恢复和重试
日志、指标、reconciliation 留存期
临时文件不误删其他进程数据
```

运行成功一次不等于 OPS-VERIFIED。

---

## 14. Known issues、豁免与 reviewer 分歧

### 14.1 缺陷等级

- P0/P1：PG-1、PG-2、PG-3 不可豁免；
- P2/P3：可在明确风险接受后延期；
- UNKNOWN 若可能影响身份、期间、币种单位、版本或语义，按 P0/P1 处理直到澄清。

延期项至少记录：

```text
issue_id
phase/build/commit
severity
evidence_ids
owner
due_date
risk_acceptor
scope
expiry
resolution_commit
status
```

“采纳 + 备注”不构成风险接受。到期或扩大范围后自动重新阻断。

### 14.2 独立复核与分歧

- L3/PG-2：至少两名 reviewer 独立验证关键 DATA/TEST 证据；
- L4/PG-3：至少两名 reviewer 签发，且 SEC、OPS 责任明确；
- reviewer 不得仅复用作者或另一 reviewer 的查询输出；
- 结论冲突时先复现实验和比较证据，不以人数直接投票；
- 第三 reviewer 负责独立重放争议证据；
- 任何 P0/P1 事实成立即阻断，不受 2/3 多数覆盖。

签名应列 evidence IDs、未验证项和责任范围，不按模型名称永久绑定角色。

### 14.3 Reviewer 修正声明

发现原评审存在重大遗漏时，必须追加：

```text
原结论
修正结论
遗漏问题
遗漏原因
证据等级变化
对既有发布的影响
后续防复发检查
```

修正不是惩罚，而是证据体系的一部分。

---

## 15. PRINCIPLE 可执行矩阵

每份评审报告必须把适用条款映射为：

| 原则 | 设计/代码 | DATA 查询 | TEST/SEC/OPS | 证据产物 | 状态 |
|---|---|---|---|---|---|
| Raw 不可变 | append-only/build contract | source row/manifest | 重跑/失败恢复 | manifest + recon | PASS/FAIL/UNKNOWN |
| 永久身份 | CIK/permaticker policy | 一对多冲突 | ticker reuse 反例 | identity audit |  |
| 期间口径 | duration/period_type | FY/Q/YTD/TTM 分布 | 非自然年/52周 | period audit |  |
| 版本/PIT | accession/version chain | vintage 冲突 | 未来信息测试 | version audit |  |
| 币种单位 | unit policy | NULL/数量级 | ADR/非USD | currency-unit report |  |
| 字段语义 | approved crosswalk | 高风险字段分布 | SEC concept/context | semantic audit |  |
| Loader 对账 | manifest/recon | 漏斗恒等式 | 坏文件/schema drift | reconciliation |  |
| 发布治理 | build/view/rollback | diff | rollback/OPS | release package |  |

不同条款需要不同证据：文档条款不强制 DATA，SEC 条款不能用一般 TEST 代替。

---

## 16. 单次评审交付物

`docs/reviews/<phase>_<commit>_<reviewer>.md` 至少包含：

```markdown
# Review: <phase> <full_commit_sha>

## Scope and pinned build
## L1–L4 conclusion
## PG-0–PG-3 determination
## Claims under review
## Evidence inventory
## Input manifest and reconciliation
## Code findings
## Data findings
## Reverse cases
## Failure/recovery tests
## Financial semantics and PIT
## Previous open issues
## New issues and severity
## PRINCIPLE matrix
## Unverified/unknown items
## Final verdict and conditions
## Reviewer signature and evidence IDs
```

agmsg 简报只发送结论、1–2 个 blocker 和详细报告路径；完整证据不得塞进短消息后丢失。

---

## 17. 生效与修订

本方法论的修改必须：

1. 指明触发问题和上位原则；
2. 提供至少一个正例和一个反例；
3. 避免把当前项目状态写入稳定规范；
4. 检查代码块可执行性和 Markdown 完整性；
5. 由至少两名 reviewer 审阅；
6. 不得以方法论更新追认已经失败的 P0/P1 build。

### 修订记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.x | 2026-07-30 | 初始五段闭环、证据、Phase Gate、反例和失败路径框架 |
| v2.0 | 2026-07-31 | 修正证据模型、DuckDB 事务、重复/版本语义和危险测试；增加财务语义、PIT、build versioning、安全、统计与运维门禁；拆分实时状态 |
| v2.1 | 2026-08-07 | 新增 §18 Reviewer 自审：连续漏审防范；5 项强制 checklist + 已记录漏审模式 A-D |
| v2.2 | 2026-08-09 | §18 边界修正（qwen R52 复审）：具体 reviewer/model 历史迁至 `docs/reviews/meta_2026-08.md`（§1.3 稳定规范与实时状态分离）；§18.1 改匿名通用反例；§18.4 移除 reviewer 权重提升——分歧一律要求可复现实证，任何 reviewer 身份/历史不替代证据 |

## 18. Reviewer 自审：连续漏审防范

同一 reviewer 在相邻轮次对**同一类盲点**连续漏审时，必须显式登记 + 沉淀到 checklist，否则会跨 commit 重复犯错。

> 具体 reviewer/model 与 commit 级历史案例（含实例与原始评审记录）见
> `docs/reviews/meta_2026-08.md`，按 §1.3 与稳定规范分离，不在此沉淀人名与轮次。

### 18.1 通用连续漏审模式（匿名反例）

以下模式曾以不同形式反复出现（实例与后果见 reviews meta），评审人应以此自检：

| # | 漏审模式 | 典型后果 |
|---|---|---|
| **A** | 字段名语义 vs 填充范围契约（实例级/公司级/跨实例边界与填充 WHERE 不一致） | 误填大规模错位数据；文档按字段名措辞掩盖 |
| **B** | 代码正确 ≠ 文档正确（V3/README/CHANGELOG/注释语义三方漂移） | 评审按文档结论合入，真实行为被抹平 |
| **C** | 告警/状态变更仅 stdout/return，未持久化 build_log | 不可追溯审计缺口 |
| **D** | 三态 sentinel 退化为 NULL 单态（首 build vs checked-no-anomaly 歧义） | 状态语义歧义，后续评审误判 |

### 18.2 强制 checklist（L2 评审每轮必查）

任何字段/告警/状态变更评审，按以下顺序自检 5 项：

```text
□ 1. 字段名 vs 填充范围一致性
     - 字段名语义边界是实例级 / 公司级 / 跨实例？
     - 填充 WHERE clause 与语义边界一致？
     - 反例：per-ticker distinct sanity（一查即知）

□ 2. 代码正确 ≠ 文档正确
     - V3/README/CHANGELOG/注释 三方语义一致？
     - 反例：文档「company-level stable」措辞 vs per-instance 真实行为

□ 3. build_log = immutable audit trail
     - 告警/状态变更是否持久化进 build_log？
     - stdout print / return dict 是 transient，build_log 是 durable
     - 反例：row_drop_warning 仅 stdout/return

□ 4. 三态 sentinel vs NULL 单态
     - NULL 是否歧义（首 build vs checked-no-anomaly）？
     - 必须用 sentinel 字符串区分「未检查」vs「检查无异常」
     - 反例：row_drop_warning=NULL 歧义

□ 5. 真理 ≠ 投票
     - 每项 REJECT/P1 必须附可复现实证（fixture/命令/输出路径）
     - 多数 ACCEPT 不构成合入依据；沉默 ≠ 同意
     - 反例：多数 ACCEPT 但异议方以实证 REJECT
```

### 18.3 评审员漏审登记机制

发现自己连续漏审同一盲点，必须：

1. **立即登记** 到本次评审 review 文件 §0「self-criticism」段；
2. **更新** `docs/reviews/meta_2026-08.md`（review meta）追加新案例（漏审 #E 等）；
3. **激活对应 checklist 项**（§18.2），后续评审必查；
4. **不得** 用「新视角」「前次评审没问题」等理由回避漏审事实；
5. 若出现新的**通用**模式，按 §18.1 匿名化沉淀进稳定规范（人名/轮次/commit 一律进 review meta）。

### 18.4 Reviewer 分歧与表决

参考 §14.2 独立复核与分歧。本节作为延伸：

- **证据而非投票**：每项 REJECT/P1 必须附可复现实证（最小 fixture、命令、输出路径/行号）；
  任何 reviewer 的身份、历史命中记录或权重**不替代**当前证据——REJECT 的正确性由实证
  本身成立，不由提出者是谁成立；
- **沉默 ≠ 同意**：reviewer 未表态视为「未审」，不可计入多数；
- **审计系统变更**（build_log 列增删、状态语义改写）必须 100% reviewer 共识（不可多数表决）。

### 18.5 自审与项目状态分离

- §18.1 / §18.2 是**评审标准**（项目无关），可永久写入稳定规范；
- 具体 commit / build_id / reviewer / model 历史属**实时状态**，只进 `docs/reviews/meta_2026-08.md`
  与当次 review 文件，按 §1.3 与稳定规范分离。
