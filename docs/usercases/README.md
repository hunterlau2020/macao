# MACAO 用例目录

- **位置**：`docs/usercases/`（由 `docs/usecases/` 合并而来；新稿只落本目录）
- **权威基准**：`docs/MACAO_PRD_v2.md`；评审方法：`docs/MACAO_REVIEW_GUIDELINES.md` + `docs/reference/*.md`
- **横切约定**：FAQ [Q5](../FAQ.md#q5-编排器-macao-本身接入了哪个大模型)–[Q16](../FAQ.md#q16-评审方法留痕和人工接管分别在哪)（编排器无模型、任务 FSM 单一事实源、yml=摘要、全文=`docs/reviews/`、agmsg=通知、加权计票、init 歧义问管理员）

状态：`设计稿` = 正文已写、待 Schema/测试对账；`目录` = 仅本索引中的范围定义，正文未写。

---

## 主旅程（对 PRD §14.1）

```text
UC-1 init ──► UC-2 task create ──► UC-3 开发/检查点
                                      │
                                      ▼
                               UC-4 评审派发/审查
                                      │
                                      ▼
                               UC-5 共识计票
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                     UC-6 返工筛选   UC-7 人工接管   UC-8 合并签字
                          │                         │
                          └──────────► UC-3 ◄───────┘
                                      │
                                      ▼
                                   归档 / 下一单
```

守护与接入不在主链上，但与主旅程并行：`UC-9` 超时守护、`UC-10` doctor/既有项目。

---

## 用例一览

| ID | 名称 | 主参与者 | 对应任务态 / 命令 | 文档 | 状态 |
|---|---|---|---|---|---|
| **UC-1** | 初始化项目配置 | 管理员 | `macao init --agteam`；探测 FSM 投影；歧义问管理员 | [UC1-init-glm.md](UC1-init-glm.md)（主稿）；[UC1-init-gemini.md](UC1-init-gemini.md)（对照稿） | 设计稿 |
| **UC-2** | 任务受理 | 管理员或执行者 | `IDLE` → `CODING`（E1）；`macao task create` | [UC2-task-create.md](UC2-task-create.md) | 设计稿 |
| **UC-3** | 开发与检查点 | 执行者 | `CODING` / `REWORK` → `READY_FOR_REVIEW`；写 `docs/reviews/*-review-request-*.md` + `.dev.yml` 摘要 | [UC3-dev-checkpoint.md](UC3-dev-checkpoint.md) | 设计稿 |
| **UC-4** | 评审派发与审查 | 编排器（邮差）+ 各评审专家 | `READY_FOR_REVIEW` → `WAITING_REVIEW`（E2）；专家写全文 + `.review.yml` | [UC4-review-dispatch.md](UC4-review-dispatch.md) | 设计稿 |
| **UC-5** | 共识计票 | 编排器（规则机） | `WAITING_REVIEW` → `CONSENSUS_CHECK`（E3）；写 `vote_result.decision` + `issues_index` | [UC5-consensus-tally.md](UC5-consensus-tally.md) | 设计稿 |
| **UC-6** | 意见筛选与返工 | 执行者 | `REWORK`；按 issue `id` 写采纳清单并改码 | [UC6-issue-triage-rework.md](UC6-issue-triage-rework.md) | 设计稿 |
| **UC-7** | 人工接管 | 管理员 | Deadlock / init 歧义 / E7；`macao override resolve` | [UC7-human-override.md](UC7-human-override.md) | 设计稿 |
| **UC-8** | 合并与签字 | 编排器 + 管理员 | `MERGING` → `DONE`（E4a）；`macao merge approve` | [UC8-merge-signoff.md](UC8-merge-signoff.md) | 设计稿 |
| **UC-9** | 超时与守护 | OrchestratorDaemon | per_reviewer 超时 → ABSTAIN 计票；不读全文 | [UC9-timeout-daemon.md](UC9-timeout-daemon.md) | 设计稿 |
| **UC-10** | 既有项目接入与诊断 | 管理员 | `macao doctor` / `preflight` / gitignore 隔离 | [UC10-existing-project-doctor.md](UC10-existing-project-doctor.md) | 设计稿 |

---

## 各用例要点（目录级，正文以分册为准）

### UC-1 初始化

吸收 `init` 与 `setup`。静态 `macao.yaml` 与动态 `agent_registry` 分离。g/h 识别任务 FSM 并投影到各席位；推不出唯一 10 态则问管理员。agmsg 只 ping。详见分册。

### UC-2 任务受理

编排器不规划、不拆 WBS。人（或执行者 CLI）提交标题、可测验收、分支；缺字段拒绝。编排器建 `tasks` 行并投递 `DEVELOPMENT_STARTED` 信封。

### UC-3 开发与检查点

执行者独占业务 commit 与评审申请**全文**。`.dev.yml` 仅摘要 + 指针 + sha256 + `signal: EXPLICIT`。Layer 1 产物触发 `READY_FOR_REVIEW`。返工轮必须新 commit。

### UC-4 评审派发与审查

编排器不写申请摘要。E2 把执行者已有 manifest 原样放入 `REVIEW_REQUEST` 并 agmsg ping。专家在独立 worktree 取 diff，全文进 `docs/reviews/*-review-result-<mid>-<reviewer>.md`，`.review.yml` 含总票 + 问题索引。方法见 GUIDELINES。

### UC-5 共识计票

编排器无模型：加权 2/3 + 席位法定人数 + 独裁帽。`issues_index` 原样拼接，不合并同类项、不标采纳。僵局 HOLD，问管理员（UC-7），不问执行者。

### UC-6 意见筛选与返工

执行者读全文与 `issues_index`，写采纳清单（按 `id` 引用），再改码并提交新检查点（回到 UC-3）。编排器只检测清单 Schema。

### UC-7 人工接管

适用：计票 Deadlock、init 无法唯一识别、覆盖上限仍返工。选项闭合：`APPROVED` / `REWORK` / `RETRY_REVIEW` / `CANCEL`。每笔裁定进审计 + `docs/reviews/`，agmsg 只回执 ping。

### UC-8 合并与签字

`MERGING` 合的是 git（ff / CI / 签字 / push），不是「合并评审意见」。评审对象 = 合并对象（checkpoint 硬绑定）。默认 `require_human_signoff`。

### UC-9 超时与守护

`daemon --once` / 后台扫描 deadline。超时记 `ABSTAIN` 并进入计票路径。不根据日志「猜」业务态；Layer 3 报告只给管理员。

### UC-10 既有项目接入与诊断

零侵入：`init`/`setup`、gitignore 隔离、`doctor`/`preflight`。不自动改已有任务 FSM；对账提示 `daemon --once`。

---

## 共享产物与通道（所有 UC 遵守）

| 载体 | 用途 |
|---|---|
| `macao.yaml` | 静态规范（含 `vote_weight`） |
| `.macao/state.db` | 动态 FSM / 席位快照 |
| agmsg | 短 ping |
| `.dev.yml` / `.review.yml` | 摘要信封 |
| `docs/reviews/*.md` | 申请与结论全文、评审留痕 |
| `vote_result.json` | 计票 + 问题目录 |
| 执行者采纳清单 | 哪些 issue 改、哪些不改 |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-01 | 首版目录：UC-1 已有设计稿；UC-2–UC-10 仅范围定义，对齐 FAQ Q12–Q16 与 UC-1 h0 |
| 2026-09-01 | 补齐 UC-2–UC-10 全部分册设计稿（glm）：统一前置/主流程/备选 A/异常 E/后置/验收/落点/自审八段式；全部对齐 PRD v2.4 §2/§3/§6/§14、FAQ Q5–Q16 与 UC-1 h0 三层载体/加权计票/编排器零内容生成约定 |
