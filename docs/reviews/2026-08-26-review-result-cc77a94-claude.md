# MACAO PRD v2.3 独立复审结论（响应 review-request-PRD-v2.3）

- 评审日期：2026-08-26
- 被评审 commit：`cc77a94`（PRD v2.3；申请方为 `docs/reviews/2026-08-26-review-request-PRD-v2.3.md`）
- 评审范围：`docs/MACAO_PRD_v2.md`、`docs/EXECUTIVE_SUMMARY.md`、`docs/IMPROVEMENT_SUMMARY.md`、`docs/schemas/*`（含 fixtures）、`docs/reviews/STATUS.md`
- 定级申请：L1 DOC-ALIGNED / PG-0
- **结论：不予定级，仍为 PARTIALLY_VERIFIED / 未达 L1。** 机器校验、review_context 单一结构、EXEC/IMPROVEMENT_SUMMARY 示例合规性全部通过复核；但请求方标注为"应复核项"的 Deadlock 终局处理，在最关键的一环——"票已收齐、判定为 Deadlock 后，如何在 §6.1 承诺的时限内确定性地触发人工接管"——仍未在转移表/伪代码/场景推演中落地，且 STATUS.md 所称已完成的"六场景 SIM 复核"实际未写入 PRD 权威文本 §3.4。另有 1 处 10 态 FSM 表述不一致（§11.4 DDL 注释仍写"9 态"）。

## 一、机器校验复现结果（独立执行，未直接采信申请方数字）

按请求第四节指引，本地重跑：

```
python3 + jsonschema 4.10.3
```

| 检查项 | 结果 |
|---|---|
| 6 个 `docs/schemas/*.schema.json` 自身 `Draft7Validator.check_schema` | 全部通过 |
| `fixtures/valid/*` 6 例 × 对应 Schema | 全部 VALID（含新增 `review_context_full.json`、`review_context_minimal.json`、`aep_review_request.json`） |
| `fixtures/invalid/*` 3 例 × 对应 Schema | 全部被正确拒绝（`aep_unknown_type` 因 `type` 枚举、`context_missing_refs` 因 `refs` 必填、`review_status_vote_conflict` 因 status↔vote if/then） |
| PRD §2.4 Type B `payload.review_context` vs `review_context.schema.json` | VALID |
| PRD §5.2 完整模型 YAML vs `review_context.schema.json` | VALID |
| §2.4 与 §5.2 两个 `review_context` 示例顶层键集合 | 完全一致：`code_changes / dev_checkpoint / executor_self_assessment / history / quality_snapshot / references / repository / task_info` |
| `EXECUTIVE_SUMMARY.md` 内 `.dev.yml` 示例 vs `dev_manifest.schema.json` | VALID |
| `EXECUTIVE_SUMMARY.md` 内 `.review.yml` 示例 vs `review_manifest.schema.json` | VALID |
| `EXECUTIVE_SUMMARY.md` 内 `vote_result.json` 示例 vs `vote_result.schema.json` | VALID |
| `IMPROVEMENT_SUMMARY.md` 内 `review_context` 示例 vs `review_context.schema.json` | VALID |

**结论**：请求第四节列出的机器校验项与第三节高风险区第 1、4 点（review_context 单一结构、摘要文档示例合规性）**予以确认，独立复核通过**。

## 二、高风险区第 2、3 点：不予确认

### 2.1 Consensus Deadlock 的人工接管触发仍未在转移表/伪代码中落地（沿用自本人 `8ab9be7` 轮报告，本轮未实质关闭）

**已修复的部分**（予以认可）：
- `vote_result.schema.json:52` 新增 `"resolution": {"enum": ["automatic", "human_override"]}`，解决了"decision 只有两个合法值，人工裁定结果无处安放"的表达问题；
- `MACAO_PRD_v2.md:778-782` Layer 1c 伪代码把此前的隐式 `else` 改成显式两分支并加注释，可读性改善。

**仍未关闭的部分**：

1. `MACAO_PRD_v2.md:393-413`（§2.3 决策表）与 `MACAO_PRD_v2.md:1101-1105`（§6.1 "Consensus deadlock" 触发条件）都把 Deadlock 定义为**独立于**"State ambiguity"（E8，60 分钟+置信度<0.7）的另一类触发，并承诺 **10 分钟**内确定性地询问用户——这是一个纯粹由票数决定的确定性判断（票已收齐即可算出），不依赖任何 LLM 诊断。
2. 但 §3.3 统一转移表（`MACAO_PRD_v2.md:814-834`）中，唯一涉及 Deadlock 的 `E7` 行触发类型是"**命令**"——即人工已经做出裁定之后如何落盘转移，而不是"票已收齐、算出 Deadlock 时如何进入人工接管"这一入口本身。
3. Layer 1c 伪代码（`MACAO_PRD_v2.md:771-782`）里，进入 `CONSENSUS_CHECK` 后唯一的动作是 `load_and_validate('.macao/vote_result.json', ...)`；若为 Deadlock，注释明确写"Deadlock 轮先人工裁定、后写终局 decision"（`MACAO_PRD_v2.md:779`），也就是说 Deadlock 发生时 `vote_result.json` **尚不存在合法内容**，`result.valid` 为假，代码会直接跳过 if 块、落到 Layer 2（仅日志）与 Layer 3。而 Layer 3 的人工接管只在 `is_agent_suspected_deadlock()` 判定"疑似卡死"且**60 分钟**无进展时才触发（`MACAO_PRD_v2.md:790-802`，对应 E8）——这与 §6.1 承诺的独立 10 分钟路径不是同一条代码路径，且以"疑似卡死+LLM 置信度"这种模糊信号去覆盖一个本可以精确计算的票数判断。
4. 换言之：**"票已收齐 → 算出 Deadlock → 触发人工接管"这一步，在自称穷尽的统一转移表里找不到对应的产物/命令/信号来源**，只能退化到与它设计初衷不符的 60 分钟通用诊断路径。

**关于"已验证"的证据缺口**：`docs/reviews/STATUS.md` "下一步" 第 2 条列出了六场景 SIM 复核（S1–S6），其中 S3（"1:1 僵局 → 裁定 APPROVED"）和 S6（RETRY_REVIEW/CANCEL）声称已于本轮修订随附完成，并被本次复审申请第二节列为"已修复"的证据。但经核对 `MACAO_PRD_v2.md:843-884`（§3.4"产物生命周期与场景推演"，PRD 自己在 §3.3 里指定的"验收标准…推演见 §3.4"的权威落点），**该节目前仍然只有"场景推演一"（首次批准）与"场景推演二"（返工第二轮）两个场景**，并未包含 Deadlock、弃权降级或 RETRY_REVIEW/CANCEL 的推演。STATUS.md 表格中的 S3–S6 只存在于评审跟踪文件本身，从未被写入 PRD 正文。这意味着"每一步最多命中一个合法转移"这一验收标准，对 Deadlock/RETRY_REVIEW/CANCEL 路径**从未被实际验证过**，只是被记录为"已完成"。

**建议**（二选一，并把结果写回 §3.4 补第三个场景）：
- 方案 A：在 §3.3 新增一条产物触发边，例如 `E3a`：`CONSENSUS_CHECK` + 产物（`.review.yml` 全部到齐后内部计算）+ 结果为 Deadlock → `UNKNOWN`，伴随动作里明确调用 `trigger_human_override`（复用 §6.1 的 10 分钟超时），使其与 E3（进入 CONSENSUS_CHECK）衔接，而不是隐藏在 `vote_result.json` 是否存在这件事背后；
- 方案 B：明确"票数判定"本身就是一个可即时求值的确定性函数，直接在 E3 的"伴随动作"里写明"若判定为 Deadlock，同步发送 `HUMAN_OVERRIDE_REQUEST` 并不写 `vote_result.json`，等待 E7 裁定"，把这一步显式纳入 E3 的产物触发定义而不是留给 Layer 3；
- 无论哪种方案，都必须在 §3.4 补一条"1:1 平票 → Deadlock → 人工裁定 → E7"的完整推演，作为 §3.3 验收标准的实际证据，而不是仅登记在 `STATUS.md`。

### 2.2 §11.4 State Store DDL 注释仍写"9 态"，与全文"10 态"矛盾

**证据**：`MACAO_PRD_v2.md:1299`：`state TEXT NOT NULL, -- 当前 FSM 状态（9 态之一）`；而 `MACAO_PRD_v2.md:837`（§3.3 说明）、`EXECUTIVE_SUMMARY.md:267`、`IMPROVEMENT_SUMMARY.md:514` 均已同步为"10 个业务状态"（含新增 `CANCELLED` 终态）。这正是本次复审申请第三节第 3 点明确要求核对的"§1.1/§1.2/§3.3/§11.4 State Store/执行摘要之间状态清单无矛盾"——核查结果为**不一致**。

**建议**：`MACAO_PRD_v2.md:1299` 注释改为"10 态之一"。

## 三、高风险区其余部分：确认无误

- §1.1 简化流程图（`MACAO_PRD_v2.md:39-118`）明确自称"简化视图"，并在图后（`MACAO_PRD_v2.md:117`）声明完整权威关系以 §3.3 为准，不构成矛盾；图中 `MERGING`/`DONE`/`REWORK` 与 §3.3 一致。图中 Phase 3 使用了非枚举术语 "REVIEWING"（`MACAO_PRD_v2.md:85`）描述 Reviewer 工作中的非正式阶段，不在 10 态正式列表内——鉴于该图已自我声明为简化视图且未被其他章节引用为权威来源，本轮不作为缺陷登记，仅记录供下轮清理措辞（P3）。
- §1.2 阶段定义表（`MACAO_PRD_v2.md:129-130`）与 §3.3 转移表引用（E4/E4a/E4b/E5/E6/E7/E9/E10）逐项核对一致。

## 四、汇总

| 编号 | 级别 | 发现 | 状态 |
|---|---|---|---|
| P1（原 P0 的延续，范围收窄） | P1 | Deadlock 检测→人工接管的入口转移边缺失；§3.4 缺 Deadlock/RETRY_REVIEW/CANCEL 场景推演证据 | 待处理 |
| P2 | P2 | `MACAO_PRD_v2.md:1299` DDL 注释仍写"9 态" | 待处理 |
| P3 | P3 | §1.1 简化图使用非正式术语 "REVIEWING"，与 10 态正式列表不完全对应（图已自称简化，非强缺陷） | 登记，非阻塞 |

上一轮（`8ab9be7`）我报告的"decision 枚举无法表达 Deadlock"定级为 P0，本轮下调为 P1：因为 `resolution` 字段的引入已经解决了"落盘后的终局结果可被合法序列化"这一半问题，真正残留的是"检测到 Deadlock 那一刻如何确定性地转移"这一入口问题，性质从"数据无法表达"收窄为"转移表遗漏一条边+验收证据未落地"，风险有所降低但仍需在定级前处理——因为 §6.1 对该场景做出了具体、可测试的时限承诺（10 分钟），而目前的实现路径无法兑现。

## 五、建议的闭环顺序

1. 关闭 P1：任选 §2.2 中的方案 A 或方案 B，把 Deadlock 检测到接管的转移边写入 §3.3，并在 §3.4 补第三个场景推演（1:1 平票路径），使其成为可核查的文本而非仅存在于 STATUS.md；
2. 顺带修正 P2（`MACAO_PRD_v2.md:1299` 注释勘误）；
3. P3 可延后，不阻塞定级；
4. 以上完成后，本轮复核的其余部分（review_context 单一结构、EXEC/IMPROVEMENT_SUMMARY 示例、9 个 fixtures 机验）已达标，无需重新验证；下一轮复审可直接聚焦 P1 的修订是否正确即可定级 **L1 DOC-ALIGNED / PG-0**。

## Reviewer 自审记录

本轮方法：不直接采信申请方在请求文档与 STATUS.md 中给出的"已修订"结论，逐项用可执行的机器校验（jsonschema 实测，而非重复读文字描述）与逐行原文核对两种方式复核；对申请方明确列出的四个高风险区，按其原文位置逐一验证而非泛读全文。发现"评审跟踪文件记录的验证结果未同步写入被评审的权威文档正文"这一模式（STATUS.md 的六场景表 vs PRD §3.4 实际只有两场景），提示今后复审应把"证据是否在权威文档内可查"本身作为一项独立核查点，而不仅核查证据内容是否正确。未验证真实代码、CLI 行为或 SQLite 恢复过程；结论仅覆盖文档、Schema 与 fixture 级证据。
