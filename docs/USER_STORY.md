# MACAO 用户故事（User Stories）

- **创建日期**：2026-09-04
- **来源**：由 `docs/usercases/`（UC-1 ～ UC-10，PRD v2.5 对账版）转写
- **划分维度**：用例按 FSM 流程阶段纵向切分；用户故事按**角色价值**横向切分为 4 个 Epic
- **角色总览**：管理员（Admin）、执行者（Executor）、评审专家（Reviewer）、编排器/守护进程（Orchestrator / OrchestratorDaemon，规则机）

---

## Epic A：管理员 — 项目治理与异常裁定

| # | 用户故事 | 来源用例 |
|---|---|---|
| A-1 | 作为管理员，我想运行 `macao init --agteam` 生成席位/角色/模型建议并逐项确认，以便快速搭建评审环境 | UC-1 |
| A-2 | 作为管理员，我想在系统无法唯一判定 FSM 状态时被停下来询问（而非启发式猜态），以便状态零误判 | UC-1 h5、UC-10 |
| A-3 | 作为管理员，我想在 DEADLOCK/返工超限时通过 `override resolve` 五选项（`APPROVED / REWORK / RETRY_REVIEW / CANCEL / EXTEND`）裁定并独立留痕于 `admin_override.json`，以便异常可收敛且审计完整 | UC-7 |
| A-4 | 作为管理员，我想在合并前人工签字（`macao merge approve`），以便控制发布放行 | UC-8 |
| A-5 | 作为管理员，我想配置静态 `vote_weight`（含独裁帽校验 $\forall i, 3w_i < 2W$），以便表达对评审者的信任差异 | UC-1 / UC-5 |
| A-6 | 作为管理员，我想用 `doctor` 只读诊断 + `reconcile` 确定性恢复，以便零侵入接入既有项目 | UC-10 |

## Epic B：执行者 — 开发、检查点与意见处置

| # | 用户故事 | 来源用例 |
|---|---|---|
| B-1 | 作为执行者，我想提交带可测验收判据的任务表单，以便工作有明确完成标准（缺字段原子拒绝） | UC-2 |
| B-2 | 作为执行者，我想独占撰写业务 commit、评审申请全文与 `.dev.yml` 摘要信封，以便内容不被编排器改写 | UC-3 |
| B-3 | 作为执行者，我想逐项声明意见处置（`ADOPTED / DEFERRED / REJECTED / NEEDS_ADMIN / EXEMPTED_BY_ADMIN`），以便自主决定采纳而非被机器代裁 | UC-6 |
| B-4 | 作为执行者，返工时我想提交拓扑前进的新 checkpoint，以便复审对象可追溯 | UC-3 g、UC-6 |

## Epic C：评审专家 — 独立审查与投票

| # | 用户故事 | 来源用例 |
|---|---|---|
| C-1 | 作为评审专家，我想在隔离 worktree 中收到零改写的 `REVIEW_REQUEST` 信封与 diff，以便基于完整上下文审查 | UC-4 |
| C-2 | 作为评审专家，我想写全文结论 + `.review.yml` 票面（含问题索引），以便意见被完整留痕并进入计票 | UC-4 |
| C-3 | 作为评审专家，我超时未交票时希望被记 `ABSTAIN` 而非被替代投票，以便流程不卡死且我的立场不被伪造 | UC-9 |

## Epic D：编排器/守护进程 — 系统故事（规则保障）

| # | 用户故事 | 来源用例 |
|---|---|---|
| D-1 | 作为编排器（无模型规则机），我要用纯整数五重门禁计票并单写不可变 `vote_result.json`，以便决策可审计、无人可篡改 | UC-5 |
| D-2 | 作为编排器，我只做信封校验（Schema/sha256/拓扑）与邮差投递，以便内容与流程物理分离 | UC-2 / UC-3 / UC-4 |
| D-3 | 作为 OrchestratorDaemon，我要在超时后注入弃权票、隔离迟到票（`LATE_REVIEW_ISOLATED`），以便计票必然收敛 | UC-9 |
| D-4 | 作为 Merge Controller，我要执行六道关卡（证据校验/检出/技术合并/CI/签字/push 与归档），以便评审对象 = 合并对象 | UC-8 |

---

## 与用例划分的关键差异

1. **切分轴不同**：用例按 FSM 事件（E1–E10）纵向切；用户故事按角色横向切，一个用例常拆 2–3 条故事（如 UC-1 拆出「初始化」A-1 与「歧义问管理员」A-2 两条）。
2. **异常流去向不同**：用例的备选流/异常流（A1–A7、E1–E7）不再独立成故事，而是收敛为故事的**验收标准**（Given/When/Then），例如：
   - B-1 的 AC：Given 已有活动任务，When 再次 `task create`，Then 拒绝且 tasks 表零副作用（UC-2 E3）
   - B-2 的 AC：Given `full_document.sha256` 与文件字节不一致，When 提交 `.dev.yml`，Then 信封无效（fail-closed，UC-3 d5）
   - D-1 的 AC：Given 全弃权，When 计票，Then `decision=DEADLOCK` 且即时落盘不可变并 HOLD 问管理员（UC-5）
3. **系统角色合法化**：本项目特色是「编排器无模型」的规则机（FAQ Q5/Q10），用户故事允许把它作为一类 persona（系统故事，Epic D），对应用例中大量的「编排器禁止做 X」边界声明。

---

## 修订记录

| 日期 | 版本 | 说明 |
|---|---|---|
| 2026-09-04 | v1.0 | 首版：由 UC-1 ～ UC-10 转写为 4 个 Epic、17 条用户故事。 |
