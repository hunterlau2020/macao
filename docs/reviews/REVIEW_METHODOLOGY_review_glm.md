# 三份参考评审指南对比分析与本项目指南汲取建议

- **评审日期**：2026-08-31
- **评审人**：glm（独立分析）
- **分析对象**：`docs/reference/` 下三份评审指南（均随 `3c5ed32` 入库）：
  1. `REVIEW_METHODOLOGY.md`（738 行）——Washdb 财务数据管线评审方法论 v2.2（**源**）
  2. `MACAO_REVIEW_GUIDELINES.md`（244 行）——MACAO 评审方法论 v1.0（Washdb 的域适配版，与顶级 `docs/MACAO_REVIEW_GUIDELINES.md` 逐字节相同）
  3. `REVIEW_GUIDE.md`（190 行）——某儿童英语学习后端的单轮代码评审范围书（外来项目文档）
- **分析目的**：判明三份文档的谱系与体裁差异，并回答"本项目现行评审指南可从中汲取什么"。

---

## 一、一句话定位

| 文件 | 体裁 | 谱系 |
|---|---|---|
| `REVIEW_METHODOLOGY.md` | **稳定方法论**（源） | Washdb v2.2（2026-08-09）：财务 Loader/Pipeline/SEC 数据评审，另两份的源头 |
| `MACAO_REVIEW_GUIDELINES.md` | **稳定方法论**（域适配版） | 从 Washdb v2.2 改编（2026-08-25）：裁去金融语义/SEC/DuckDB 章节，替换为 MACAO 状态机/投票/AEP Schema 域；即历轮门禁的现行标准 |
| `REVIEW_GUIDE.md` | **单轮范围清单**（方法论的应用层产物） | 另一项目（FastAPI/SQLAlchemy/MySQL、笔友 AI、PK 结算）一轮后端代码评审的范围书，与前两份无方法论继承关系 |

## 二、共同骨架（MACAO 版自 Washdb 直接继承）

- L1–L4 四级结论 + PG-0~PG-3 门禁；`UNKNOWN ≠ PASS`；局部对齐不得外推为整体
- 六值验证状态（VERIFIED / PARTIALLY_VERIFIED / CLAIM_ONLY / UNKNOWN / CONTRADICTED / NOT_APPLICABLE）
- P0/P1 不可豁免；P2/P3 可延期但须登记；UNKNOWN 涉及核心语义时按 P0/P1 处理
- **"真理不等于投票"**（Washdb §14.2："不以人数直接投票""P0/P1 事实成立即阻断，不受多数覆盖"）+ "沉默 ≠ 同意"
- 稳定规范与实时状态分离（STATUS / 单次报告 / meta 复盘另存）
- Reviewer 自审机制（Washdb §18 ↔ MACAO §9 的 A–D 盲点表）与双签生效（Washdb §17 ↔ MACAO §11）

## 三、关键差异对照

| 维度 | Washdb（源） | MACAO（适配） | Backend Guide |
|---|---|---|---|
| 评审对象 | 财务 Loader/Pipeline/SEC 数据 | 设计文档、Schema、状态机、多 Agent 代码 | 单个后端代码库一轮评审 |
| 证据类型 | DOC/CODE/**DATA/TEST/SEC**/OPS | DOC/**SPEC**/CODE/**SIM**/TEST/OPS（以 SPEC/SIM 替 DATA/SEC，域适配合理） | 无证据类型模型，只要求 `file:line` + 反例 |
| **PG-1 条件** | 当前 Phase **L3** + P0/P1 零 | **L2** + P0/P1 零（**弱化一级**） | — |
| L4 条件 | SEC 核验、Legacy diff、回滚演练、运维门禁 | **人工接管实机演练**、回归无 P0/P1、用户手册 | — |
| P0 语义 | 沿等级纪律，未给域定义 | 同左 | **P0=越权/儿童隐私泄露**（域定义具体）；但其 §2 的 P0~P6 又是"重点领域优先级"——**P 记号双义**，易混 |
| 领域专属章节 | §5 财务语义硬门、§7 Loader Contract、§12 SEC 抽样 | §4 声明矩阵（投票/审计/context）、§6 反例库（超时/弃权/僵局 11 场景）、§7 沙箱隔离 | §3 IDOR 逐端点清单、§1.2 已接受简化边界表、§4 复现命令 |
| 独有强项 | 证据 YAML 记录（evidence_id/build_id/sha256）；风险接受登记字段最全（risk_acceptor/scope/expiry，到期自动重新阻断）；双 reviewer 独立验证与签名门槛；Reviewer 修正声明模板 | 声明验证矩阵与反例库对本仓库针对性最强（历轮 P1-Q 系列发现即源于此类推演） | "验证修复而非重报旧缺陷"（§0.4）；"缺陷与决策分离"（§0.3）；"分级看影响不看观感"（§0.2） |

## 四、本项目指南的汲取建议（按优先级）

### 高价值——把本项目"重新发明过却未写成条文"的纪律固化

| # | 汲取自 | 条款 | 入 `docs/MACAO_REVIEW_GUIDELINES.md` 后 | 能避免的历史代价 |
|---|---|---|---|---|
| 1 | Backend §0.4 | **"验证修复 = 构造反例击穿修复，而非重报旧缺陷；修复必须附回归测试"** | 新增"修复验证纪律"，并补该指南没有的一条：**测试不得以显式传参绕开生产路径** | 本项目面板花约 7 轮才自发形成此打法（qwen"修复完备性反例"、claude"不把新增单测当穷尽"、其 3e1a991 发现 `timed_out_reviewers=[...]` 传参绕过生产检测分支）——成文后新 reviewer 首轮即可继承 |
| 2 | Washdb §14.1 | 风险接受登记补全：`risk_acceptor / scope / expiry / resolution_commit`，**到期或扩大范围后自动重新阻断** | Known Issues 登记格式升级（STATUS.md 配合） | 治"无限期 P2 携带"：codex 7 项（qwen 定 P2）连续 4 轮被重复提起、每轮重写理由——登记一次 + 到期机制即免重复诉讼 |
| 3 | Backend §0.2+§0.3 | **分级看影响不看观感**（域定义具体到可判定）+ **"决策项"类别**（已接受的简化边界不记缺陷；不可接受时单列并写业务代价） | 写出 MACAO 影响导向定义表，建议：P0=未评审代码被合并/审计链断裂；P1=状态机违约/票面完整性破坏；P2=过程卫生与健壮性；另设"决策项" | claude P1-NEW-11 vs qwen P2 的定级之争消耗 7973853/3ea5256 两轮大量篇幅；kimi P2-1（ping 与实现不一致）本质是决策项却每轮重辩 |
| 4 | Washdb §14.2 | **L3/PG-2 至少两人独立验证关键证据；reviewer 不得仅复用他人查询输出；争议由第三人重放；签名列 evidence IDs 与未验证项** | 把 panel 自发惯例制度化（qwen 每轮"先复放后读同行报告"、claude"不采信他方结论"——目前全靠自觉） | 防"报告洗稿"（引用他人证据当独立验证）；zcode/grok 缺席不再需要每轮澄清 |
| 5 | Washdb §14.3 | **Reviewer 修正声明模板**（原结论/修正结论/遗漏原因/证据等级变化/对既有结论的影响/防复发检查） | 新增 Reviewer 自审附表 | claude 在 f41b9da 轮已自发做过一次（"GOV-1 下修 + 补 P1-NEW-7"），证明有真实需求；目前修正格式无约束，事后难审计"改了什么、为何漏" |
| 6 | Washdb §3.2/§11 | **证据结构化**：`evidence_id / type / status / commit / 脚本与输出哈希`；结论钉死不可变输入 | 与既有"钉死 commit"惯例（P3-NEW-10 教训）配套：复放脚本归档至 `docs/reviews/evidence/` 或报告附录 + 哈希 | 历轮反例脚本全在 `/tmp`（q79/q3ea 等），复审者无法重放发现——证据可复现性停在"报告里贴输出" |

### 中价值（可选）

- **Washdb §1.2**"不得以一次性脚本为名绕过门禁写入生产表" → MACAO 化："**演练/研究路径不得写入主仓库状态**"——与 claude P2-NEW-6（state.db 入库）及 3c5ed32 轮 live-run 伪演练（P1-Q4）构成制度级呼应
- **PG-1 语义**：Washdb 为 L3、MACAO 弱化为 L2——实践已收敛（PG-2 授予伴随 L3），建议在指南注明弱化理由或对齐
- Backend 的"复现与运行"命令节——MACAO 申请模板已有，无需引入

### 不应引入

- Washdb 的 SEC/DATA/财务语义章节（当初裁剪正确）
- Backend 的 P0~P6 记号（"重点领域优先级"与"严重度"双义，前车之鉴）

## 五、伴随治理发现（P3 级）

1. **出处声明自相矛盾**：MACAO 版注记称改编自"Washdb……第三方项目文档，**未随本仓库提供**"，而本轮 Washdb v2.2 原文已随仓提供——注记应更新，并补第三方文档来源/许可标注（若仓库公开，整份搬运第三方文档有归属风险）
2. **`REVIEW_GUIDE.md` 为外来项目文档**：含另一项目真实路径（`C:\mysoft\mysql-8.0.33-winx64`）、模块与裁决记录，与 MACAO 无关——入 `reference/` 无 README 谱系说明，易误导后来者
3. **双副本漂移风险**：`reference/MACAO_REVIEW_GUIDELINES.md` 与顶级文件逐字节相同，与 `src/macao/schemas` vs `docs/schemas` 同模式——建议 `reference/` 改为指针/README，单一事实源
4. `REVIEW_METHODOLOGY.md:4-6` 尾随空白系 Markdown 硬换行写法（行尾双空格），语义无害但会被 `git diff --check` 击穿——3c5ed32 轮"100% Clean"声明失实即源于此，入库前应统一处理

## 六、修订路径建议

按 MACAO 指南 §11 修订规则（触发问题 + 正反例 + 双 reviewer 审阅）：高价值 #1–#3 可作为一次修订提交，触发案例直接引用本项目史实——"P1-NEW-11 定级之争"（#3）与"codex 七项四轮重辩"（#2）；#4–#6 可作为第二次修订。两份参考文档（Washdb §14、Backend §0）即正例来源，反例取本报告 §四"历史代价"列。

---

## Reviewer 自审记录

- 本报告为方法论对比分析，非门禁定级轮；不涉及 L/PG 判定
- 全部结论基于三份文档全文通读 + 与顶级指南 `diff` 比对（逐字节相同）+ 本项目历轮评审记录（2026-08-25 至 2026-08-31，docs/reviews/ 76 份结果）
- "历史代价"列引用的轮次/编号（P1-NEW-11、P1-Q4、P3-NEW-10 等）均可在对应日期的 review-result 文件中溯源
- 利益相关声明：建议 #4 涉及将本人（及同行）的自发惯例制度化，判断依据为历轮报告原文，非事后重构
