# MACAO 用例目录

- **位置**：`docs/usercases/`（同时支持 `docs/usecases/` 软链接；新稿以本目录为准）
- **权威基准**：`docs/MACAO_PRD_v2.md`（PRD v2.5）；变更提案：`docs/PRD_CHANGE_PROPOSAL_v2.5.md`
- **评审方法**：`docs/MACAO_REVIEW_GUIDELINES.md` + `docs/reference/*.md`
- **横切约定**：FAQ [Q5](../FAQ.md#q5-编排器-macao-本身接入了哪个大模型)–[Q16](../FAQ.md#q16-评审方法留痕和人工接管分别在哪)（编排器无模型、任务 FSM 单一事实源、yml=摘要信封、全文=`docs/reviews/`、agmsg=通知、纯整数加权计票、init 歧义问管理员）
- **原文账本**：已裁定结论见 [PRODUCT-FACTS.md](PRODUCT-FACTS.md)（F-1 ～ F-22，陈述句 fact + 原话陈述片段作锚点）

状态：`设计稿` = 正文已与 PRD v2.5 全面实装对账，并通过自动化测试验证。

---

## 主旅程（对 PRD §14.1）

```text
UC-1 init ──► UC-2 task create ──► UC-3 开发/检查点 (E1/E6)
                                      │
                                      ▼
                               UC-4 评审派发/审查 (E2)
                                      │
                                      ▼
                               UC-5 共识计票 (E3)
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                   UC-6 意见处置   UC-7 人工接管   UC-8 合并签字
                     (E5/E5a)        (E7/E9)         (E4/E4a)
                          │                         │
                          └──────────► UC-3 ◄───────┘
                                      │
                                      ▼
                                   归档 / 下一单
```

守护与接入不在主链上，但与主旅程并行：`UC-9` 超时守护、`UC-10` doctor/既有项目诊断。

---

## 用例一览

| ID | 名称 | 主参与者 | 对应任务态 / 命令 | 文档 | 状态 |
|---|---|---|---|---|---|
| **UC-1** | 初始化项目配置 | 管理员 | `macao init --agteam`；探测 FSM 投影；歧义问管理员 | [UC1-init-glm.md](UC1-init-glm.md)（主稿）；[UC1-init-gemini.md](UC1-init-gemini.md)（对照稿） | 设计稿 (v2.5) |
| **UC-2** | 任务受理 | 管理员或执行者 | `IDLE` → `CODING`（E1）；`macao task create`；下发 Type A 信封 | [UC2-task-create.md](UC2-task-create.md) | 设计稿 (v2.5) |
| **UC-3** | 开发与检查点 | 执行者 | `CODING` / `REWORK` → `READY_FOR_REVIEW`（E1/E6）；写 `docs/reviews/*-review-request-*.md` + `.dev.yml` 摘要 | [UC3-dev-checkpoint.md](UC3-dev-checkpoint.md) | 设计稿 (v2.5) |
| **UC-4** | 评审派发与审查 | 编排器（邮差）+ 各评审专家 | `READY_FOR_REVIEW` → `WAITING_REVIEW`（E2）；下发 Type B；专家写全文 + `.review.yml` | [UC4-review-dispatch.md](UC4-review-dispatch.md) | 设计稿 (v2.5) |
| **UC-5** | 共识计票 | 编排器（规则机） | `WAITING_REVIEW` → `CONSENSUS_CHECK`（E3）；纯整数加权五重门禁；写不可变 `vote_result.json` | [UC5-consensus-tally.md](UC5-consensus-tally.md) | 设计稿 (v2.5) |
| **UC-6** | 意见处置与返工 | 执行者 | `CONSENSUS_CHECK` / `REWORK`；写独立 `.macao/.dispositions/r<round>/executor.disposition.yml` 意见处置；按 `requires_new_checkpoint` 分流 E4 / E5a | [UC6-issue-triage-rework.md](UC6-issue-triage-rework.md) | 设计稿 (v2.5) |
| **UC-7** | 人工接管 | 管理员 | Deadlock / init 歧义 / E7 / 超时；`macao override resolve`；写独立 `admin_override.json` | [UC7-human-override.md](UC7-human-override.md) | 设计稿 (v2.5) |
| **UC-8** | 合并与签字 | 编排器 + 管理员 | `MERGING` → `DONE`（E4a）；六道关卡（含 Pre-merge Evidence 校验）；`macao merge approve`；Git 引用与归档 | [UC8-merge-signoff.md](UC8-merge-signoff.md) | 设计稿 (v2.5) |
| **UC-9** | 超时与守护 | OrchestratorDaemon | per_reviewer 超时 → `ABSTAIN` 计入 `accounted` 触发 E3；隔离迟到票；Layer 3 报告给管理员 | [UC9-timeout-daemon.md](UC9-timeout-daemon.md) | 设计稿 (v2.5) |
| **UC-10** | 既有项目接入与诊断 | 管理员 | `macao doctor` / `preflight` / gitignore 隔离 / 纯整数共识体检 | [UC10-existing-project-doctor.md](UC10-existing-project-doctor.md) | 设计稿 (v2.5) |

---

## 各用例要点（目录级，正文以分册为准）

### UC-1 初始化
吸收 `init` 与 `setup`。静态 `macao.yaml` 与动态 `agent_registry` 分离。基于工作区特征识别任务 FSM 并投影到各席位；推不出唯一 10 态则问管理员。agmsg 只作通知 ping。

### UC-2 任务受理
编排器不规划、不拆 WBS。人（或执行者 CLI）提交标题、可测验收判据、分支；缺字段原子拒绝。编排器建 `tasks` 行并投递 `DEVELOPMENT_STARTED`（Type A）信封。

### UC-3 开发与检查点
执行者独占业务 commit 与评审申请**全文**。`.macao/.dev.yml` 仅摘要 + 指针 + sha256 + `signal: EXPLICIT`。返工轮严格要求拓扑前进的新 commit（且未被消费）。Layer 1 产物型转移触发 `READY_FOR_REVIEW`（E1/E6）。

### UC-4 评审派发与审查
编排器是邮差：E2 把执行者已有 manifest 原样放入 `REVIEW_REQUEST`（Type B，零 base64，10 个必需与语义块）并 agmsg ping。专家在独立 worktree（`.macao/worktrees/<agent_id>/<task_id>/r<round>`）取 diff，全文进 `docs/reviews/*-review-result-<mid>-<reviewer>.md`，`.review.yml` 含总票 + 问题索引。

### UC-5 共识计票
编排器无模型：纯整数五重加权门禁（独裁帽 $3w_i < 2W$、双法定人数 $E_N \ge \lceil 2N/3 \rceil$ 与 $E_W \ge \lceil 2W/3 \rceil$、胜方权重 $3W_{win} \ge 2E_W$、胜方席位 $\ge 2$）。`vote_result.json` 由编排器单写且不可变，收敛为 3 态机器决策（`APPROVED`, `REWORK_REQUIRED`, `DEADLOCK`）。`issues_index` 原样拼接各专家索引。DEADLOCK 时即时落盘并 HOLD 问管理员（UC-7）。

### UC-6 意见处置与返工
执行者读全文与 `issues_index`，输出独立 `.macao/.dispositions/r<round>/executor.disposition.yml`（三态：`DRAFT` / `PENDING_ADMIN` / `FINAL`），逐项声明处置类型与必填布尔 `requires_new_checkpoint`。全 false 且 APPROVED 触发 E4 进 `MERGING`；任一 true 触发 E5a 进 `REWORK`；机器否决触发 E5 进 `REWORK`。

### UC-7 人工接管
适用：计票 Deadlock、init 无法唯一识别、覆盖上限仍返工、处置超时。选项闭合：`APPROVED` / `REWORK` / `RETRY_REVIEW` / `CANCEL` / `EXTEND`（支持 `--exempt-issue-ids` 局部豁免）。**DEADLOCK 时已即时落盘不可变 `vote_result.json`，管理员裁定写入独立 `admin_override.json`，严禁二次回写 `vote_result.json`**。

### UC-8 合并与签字
`MERGING` 合的是 git（Pre-merge Evidence 校验 / 检出 / ff_only / CI gate / 签字 / push 与 Post-merge 封存），不是「合并评审意见」。评审对象 = 合并对象（checkpoint 硬绑定）。默认 `require_human_signoff`。合并前校验 evidence ref 已推送，合并成功后全部产物提升至 `refs/macao/evidence/<task_id>/r<round>` 并在 `.macao/archive/` 归档。

### UC-9 超时与守护
`daemon --once` / 后台扫描 deadline。超时席位记 `ABSTAIN` 计入 `accounted` 席位以触发 E3 判定，但严格排除在有效选票集（$E_N, E_W$）之外。迟到票在计票前可替换 pending 标记，在 `vote_result.json` 落盘后严格隔离为 `LATE_REVIEW_ISOLATED` 审计日志，不修改投票结果。

### UC-10 既有项目接入与诊断
零侵入：`init`/`setup`、gitignore 9 规则隔离、`doctor`/`preflight`。只读检查配置、环境、隔离、席位、适配器与产物，发现冲突提示 `daemon --once` 对账，doctor 不自动转移状态。

---

## 共享产物与单写者垄断规范（所有 UC 遵守，PRD v2.5 D-1～D-9）

| 载体 | 写者（单一垄断） | 契约与用途 |
|---|---|---|
| `macao.yaml` | 管理员 | 静态配置单一事实源（含 `vote_weight`、`consensus_rule: weighted_2/3_v1`） |
| `.macao/.dev.yml` | 执行者 (Executor) | 开发检查点摘要信封（含 `checkpoint_ref`、`signal: EXPLICIT`、`full_document`） |
| `.macao/.reviews/<reviewer_id>.review.yml` | 各评审专家 (Reviewer) | 专家票面与问题索引信封（三值 `vote`、`opinion`、`items[]`） |
| `.macao/vote_result.json` | 编排器 (Orchestrator) | 不可变机器计票与问题目录（三值 `decision`、`policy_snapshot`、`issues_index`、`requires_disposition`） |
| `.macao/.dispositions/r<round>/executor.disposition.yml` | 执行者 (Executor) | 独立意见处置信封（`disposition_status: FINAL`、`requires_new_checkpoint: boolean`） |
| `.macao/admin_override.json` | 管理员 (Admin) | 独立接管裁定件（`override_id`、`choice`、`exempt_issue_ids`） |
| `docs/reviews/*.md` | 各角色对应作者 | 人类可读申请、结论、处置、裁定全文与 Git 留痕（GUIDELINES §1.3 命名） |
| `.macao/state.db` | 编排器 (Orchestrator) | 动态 FSM 状态、席位只读投影与不可篡改审计日志库 |
| agmsg / AEP/1.1 | 协议发送方 | 控制信封与短通知 ping（零 base64，≤16 KiB 字节预算） |

---

## 修订记录

| 日期 | 版本 | 说明 |
|---|---|---|
| 2026-09-01 | v2.5 | 全面实装 PRD v2.5（D-1～D-9 架构裁定）：不可变 `vote_result.json`、独立 `executor.disposition.yml`、独立 `admin_override.json`、纯整数加权五重门禁、AEP/1.1 协议、超时 ABSTAIN 严格边界与单写者垄断规范。 |
| 2026-09-01 | v2.4 | 补齐 UC-2–UC-10 全部分册设计稿；对齐 PRD v2.4 与三层载体约定。 |
| 2026-08-31 | v1.0 | 首版目录；UC-1 初始化用例起草。 |
