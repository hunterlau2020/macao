# 用例分册 vs PRODUCT-FACTS 符合性审计

- **审计日期**：2026-09-01
- **审计对象**：`docs/usercases/UC1`–`UC10`（含工作区未提交的 UC-5/UC-6 补丁，基线 commit `42b5c07` + 工作区）
- **审计基准**：`docs/usercases/PRODUCT-FACTS.md`（16 条 fact + 第三节状态对照裁定）——按其自我定位为"已裁定结论，钉结论防走样"
- **评审人**：glm
- **总体结论**：**UC-2/3/4/8/9/10 及 UC-1 的 h1–h2/i 段未发现违反；发现 2 项 P1（UC-1 h0(2) 与 F-13/F-16 直接矛盾；UC-5 §2c 补丁不彻底）、3 项 P2 表述张力**

---

## 1. 逐 fact 符合性矩阵

| fact | 一句话要点 | 涉及分册 | 判定 |
|---|---|---|---|
| F-1 | 探测判定的是任务 FSM 十态，非 CLI 空闲 | UC-1 h1/h2、UC-10 | ✅ |
| F-2 | 调度罗盘=任务 FSM；CLI 自报不能代替 | UC-1 h3、UC-9 | ✅（UC-1 h3b 明令禁止覆盖） |
| F-3 | UC-1 2.h/2.i 按 FSM 口径 | UC-1 | ✅ |
| F-4 | 单一 FSM；READING_MSG 不列态；REVIEWING 非第十一态；MERGING 合 git | UC-1 h2（`REVIEWING` 仅作 role_view 注记）、UC-8（"合的是 git 不是合并意见"） | ✅ |
| F-5 | 意见以标题清单+正文索引进 vote_result，全文在 docs/reviews/ | UC-5 c2、UC-4 e3 | ✅（落地指针指定 UC-5 issues_index） |
| F-6 | init 无法唯一判定问管理员，禁止猜测 | UC-1 h5、UC-7 P3、UC-10 a2 | ✅ |
| F-7 | 方法=GUIDELINES；留痕只进 docs/reviews/ | UC-4 e2、UC-7 e、UC-10 f | ✅ |
| F-8 | agmsg=通知，非事实源 | 全部分册 ping 语义 | ✅ |
| F-9 | 编排器不规划不拆 WBS | UC-2（只做表单受理） | ✅ |
| F-10 | 编排器不写申请摘要；REVIEW_REQUEST 只投递信封 | UC-3 c（执行者写）、UC-4 b（原样引用） | ✅ |
| F-11 | 编排器不裁决采纳；计票是规则函数 | UC-5 b、UC-6 d | ✅（但见 P2-1 摘录权归属张力） |
| F-12 | 编排器不接模型、不介入内容 | 全部分册边界声明 | ✅ |
| **F-13** | **执行者汇总各结论：摘录是否通过供计票；把标题清单、正文索引、专家、严重性、是否采纳写入 vote_result；不写 decision** | UC-5 / UC-6 / UC-1 h0(2) | ⚠️ **部分违反（P1-1/P1-2/P2-1）** |
| F-14 | agmsg 体积受限只放摘要 | UC-1 h0(1)、UC-4 d | ✅ |
| F-15 | yml 只存摘要，全文在 docs/reviews/ | UC-3 c、UC-4 e3 | ✅ |
| **F-16** | **vote_weight 只作用总票；单条采纳由执行者在汇总段标明** | UC-1 h0(3)（权重部分 ✅）、UC-6 b（issues_summary ✅）、**UC-1 h0(2) 第 3 点 ✗** | ⚠️ **部分违反（P1-1）** |
| 三节裁定 | 采纳/汇总发生在 REWORK，由执行者写入 vote_result 汇总段 | UC-6（时机 ✅ 载体见 P1） | ⚠️ |

## 2. P1：违反已裁定 fact，须修正

### P1-1　UC-1 h0(2) 第 3 点与 F-13/F-16 直接矛盾（已提交主稿）

- **证据**：`UC1-init-glm.md` h0(2)："3. **采纳**不在此文件：执行者另写，按 `id` 引用目录"；同段小标题"不写「采纳」"。
- **矛盾**：F-13"把…**是否采纳**写入 `vote_result`"；F-16"单条意见是否采纳仍由执行者**在汇总段**标明"；三节裁定"总结采纳…由执行者写入 `vote_result` 汇总段"；落地指针明确"F-5、F-16 → UC-6 `issues_summary`"。
- **修正**：h0(2) 改为四段口径——计票段（规则）、`issues_index`（机器原样拼接）、**`issues_summary` 汇总段（执行者写：归并、found_by、是否采纳）**；"不写采纳"限定为**编排器**不写，而非"文件里没有采纳"。

### P1-2　UC-5 §2 c 补丁不彻底（工作区未提交）

- **证据**：`UC5-consensus-tally.md` 边界声明已改（引用 F-13），但 §2 c 第 3 点仍为旧口径："**不写采纳**：…采纳清单是 UC-6 执行者产物"——与同文件新边界声明、UC-6 b（汇总段写入 `vote_result.issues_summary`）自相矛盾；§7 落点表"三段式 vote_result"未更新为四段式（含 issues_summary 段位声明）。
- **修正**：c 段补第 4 点"汇总段位预留（executor writes issues_summary，见 UC-6 b；机器段落盘后只读）"；验收标准 2 的"编排器产物无代写字段"补"且 issues_summary 段初始为空/缺省"。

## 3. P2：表述张力，建议澄清（不构成违反）

- **P2-1　"摘录是否通过供计票"的执行者归属**：F-13 字面把"摘录各份是否通过"也归执行者；UC-5/现行 `VoteAggregator` 由编排器机械读信封计票。工作区补丁的解释是"原样机械摘录≠内容工作"。建议在 PRODUCT-FACTS 或 FAQ Q15 补一条锚点裁定（"编排器从信封原样摘录 vote 供规则计票，不属内容介入"），否则实现者会两读。
- **P2-2　E7 终局 vote_result 的汇总段缺省**：DEADLOCK HOLD 时执行者无从预写 issues_summary，UC-7 d 的终局落盘未说明该段处理。建议 Schema 允许 `issues_summary` 缺省并在 UC-7 d 注记（裁定路径补汇总或显式 absent）。
- **P2-3　PRODUCT-FACTS 自身小瑕疵**：F-5 引用"（见 F-8b）"悬空（无 F-8b）；建议修正为 F-14/F-15 或删除。

## 4. 未发现违反的分册（抽样证据）

- UC-2：F-9 ✅（"编排器只收表单"，规划归人/执行者）
- UC-3：F-10/F-13/F-15 ✅（申请全文+信封均执行者写，编排器只校验 sha256）
- UC-4：F-7/F-8/F-10/F-14 ✅（REVIEW_REQUEST 原样投递、ping 极短、全文进 docs/reviews/）
- UC-8：F-4 ✅（"MERGING 合的是 git 不是意见"为边界声明首句）
- UC-9：F-2/F-12 ✅（不读日志猜业务态；Layer 3 只给管理员）
- UC-10：F-6 ✅（可疑已开始走 UC-1 h5 问管理员）

## 5. 建议闭环顺序

1. 修 P1-1（UC-1 h0(2) 四段化）+ P1-2（UC-5 §2c/§7/验收同步）——一次提交；
2. P2-1 提请管理员一句话裁定并回填 PRODUCT-FACTS 锚点；
3. P2-2/P2-3 随 Schema 对账轮批处理；
4. 验收：`grep -n "采纳不在此文件" docs/usercases/*.md` 零命中；UC-5 与 UC-6 对 `issues_summary` 的写者/只读约定互引一致。
