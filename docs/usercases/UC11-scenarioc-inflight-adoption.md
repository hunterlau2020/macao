# UC-11 场景 C 在途项目接管与在途评审（半途项目物理事实对账与生命周期纳管）

- **设计日期**：2026-09-07
- **设计人**：glm
- **状态**：设计稿 (v2.5)
- **关联**：PRD v2.5 §3.3、§14.1–§14.3；`docs/PROBE_TECHNICAL_DESIGN.md` §3；UC-1（init 接入）、UC-2（任务受理与边界）、UC-3（开发检查点）、UC-4（评审派发）、UC-5（共识计票）、UC-10（既有项目诊断）；PRODUCT-FACTS F-6、F-23、F-24；Reviewer 裁定意见（Codex P1-03、Grok P2-2）。
- **边界声明**：**物理事实驱动，严禁虚构与倒退**。在已处于推进中的项目（场景 C，如 `english_learning_system` 或 MACAO 自身）中，MACAO 作为外层编排器介入时，项目客观世界的物理指针可能停留在生命周期的任意截面。编排器必须依据 Git 拓扑和 `docs/reviews/` 下的物理产物如实对账，**严禁将已处于待评审（`WAITING_REVIEW`）或审查中（`IN_REVIEW`）的项目强制重置为 `IDLE -> CODING` 并错误派发给 Executor**。

---

## 1. 业务背景与问题定义

### 1.1 绿地（Greenfield）与棕地（Brownfield / 场景 C）的本质差异

- **绿地新开工**：项目从零起步，无历史提交与在途产物。生命周期严格按 `IDLE -> CODING -> WAITING_REVIEW -> CONSENSUS -> MERGE` 顺序单向展开，首个任务必然由 `macao task create` 派发给 **Executor** 进行代码编写。
- **棕地在途接管（场景 C）**：项目此前已在使用 AI CLI 进行开发，物理目录中已存在 Git 历史、未合入分支、评审申请单（`docs/reviews/*-review-request-*.md`）甚至部分评审结论。
  - 若此时编排器机械地假设“所有任务起点都必须是 Executor 编码”，强行执行 `task create`，将造成**灾难性状态倒退**：丢弃已完成的编码工作、破坏正在等待审查的客观物理状态、向错误的席位（给 Executor 而不是 Reviewer）发送矛盾指令。

---

## 2. 场景 C 现实截面的五大物理态与派发矩阵

当 MACAO 接入场景 C 时，必须通过 `TeamProber` 与 `GitManager` 精准识别以下 5 种互斥的物理截面，并执行对应的接管与派发：

| 物理现实截面 | 底层物理证据（Git + 目录） | 对应生命周期态 | 编排器接管动作 | 任务派发对象（唯一责任方） |
| :--- | :--- | :--- | :--- | :--- |
| **态 1：在途编码未提审** | 工作区存在 dirty 修改（`modified_files > 0`），或分支有未提交变更，无未闭环评审申请 | `CODING` / `ACTIVE_DEV` | 识别为未纳管开发；待工作区 clean 并产生 commit 后引导提交检查点 | **Executor**（继续编码、本地测试、准备自评提交） |
| **态 2：在途已提审待落票** | 存在最新 commit，且 `docs/reviews/` 下有对应的 `*-review-request-<ref>.md`，但尚无匹配评审结果（$|Results| = 0$） | `WAITING_REVIEW` / `REVIEW_PENDING` | **直接接管为待审态**；禁止倒退回 CODING；分发 Diff 与上下文至沙箱 | **Reviewers 团队**（全员派发独立审查任务，Executor 处于 STANDBY） |
| **态 3：在途部分落票审查中** | 存在有效评审申请，已有部分审查员提交了 `*-review-result-<ref>-*.md`，但未达法定 Quorum（$0 < |Results| < N$） | `WAITING_REVIEW` / `IN_REVIEW` | 计算缺票差集 $R_{missing} = R_{configured} \setminus R_{submitted}$；保留已有结果 | **未交卷的 Reviewer(s)**（定向派发/督促未完成评审，不重复打扰已交卷专家） |
| **态 4：在途评审驳回待返工** | 存在完整评审结论且决议为 `REWORK`（或存在阻断性 P0/P1），且尚未产生新 commit 与新申请 | `REWORK` | 提取评审问题索引（`issues_index`）；注入返工上下文至 Executor 会话 | **Executor**（针对评审意见进行修复打补丁，产出子孙 commit） |
| **态 5：在途评审通过待合入** | 全员或法定权重通过（`APPROVED`），且当前分支未合入 `target_branch` | `MERGING` / `READY_TO_MERGE` | 校验 Pre-merge Evidence 与分支干净度；就绪等待合入批准 | **Administrator / 编排器**（管理员执行 `macao merge approve`） |

---

## 3. 前置条件

| # | 条件 | 不满足时的行为 |
|---|---|---|
| P1 | 处于已存在的 Git 代码库，`macao.yaml` 存在且配置合法 | 提示 `macao init` 完成基础席位绑定 |
| P2 | Git 仓库有可解析的 commit 历史（`HEAD` 有效） | E1（空仓库退回绿地流程） |
| P3 | 未发生物理证据矛盾（如同一 baseline 既有通过结论又有未消费的新 request） | 触发 UC-7 管理员接管问询 |
| P4 | 目标派发席位已通过预检（`PreflightCheckResult.installed == True`） | 席位级告警，按降级或超时弃权策略处理 |

---

## 4. 主成功场景（在途接管流程）

### a. 运行态探活对账（`macao probe`）
1. 编排器扫描 Git 历史（HEAD commit、分支、dirty 状态）；
2. 扫描 `docs/reviews/` 下的所有物理产物，提取最新申请单及其基线（`latest_request_baseline`）；
3. 精确匹配已提交的评审结果集，构建 `submitted_reviewers` 集合；
4. 综合推导出真实的运行态（态 1 ～ 态 5），在输出中如实报告物理现状，杜绝假空报 `IDLE`。

### b. 在途评审接管指令（`macao task adopt`）
针对**态 2**与**态 3**（最典型的待审/在审场景）：
```bash
# 自动探测最新物理提审并纳管进 WAITING_REVIEW
macao task adopt

# 或显式指定基线 commit / 申请单文件
macao task adopt --from-request docs/reviews/2026-09-07-review-request-d042395.md
```

### c. 编排器构建状态机快照与任务账本
1. 在 `StateStore` 中建立或对账任务记录：
   - `task_id = task-adopt-<baseline_sha[:8]>`；
   - `state = WAITING_REVIEW`；
   - `checkpoint_ref = <baseline_sha>`；
   - `review_round = <round_number>`（由申请单或历史文件确定）；
2. FSM 明确记录触发源为 `E2_ADOPT`，审计日志记录 `TASK_ADOPTED_INTO_REVIEW`。

### d. 评审任务分发（仅派发给 Reviewers，零干扰 Executor）
1. 计算缺失选票席位：
   $$R_{missing} = \{ r \in R_{configured} \mid r \notin R_{submitted} \}$$
2. 若 $R_{missing}$ 非空：
   - 为每个缺票的 Reviewer 初始化工作区（或复用 Shared In-repo 工作区）；
   - 构造 `REVIEW_REQUEST` 上下文（提取 `<target>..<checkpoint_ref>` 之 Diff、申请单全文路径、验收准则）；
   - 通过 `PTYSession` 注入审查指令至对应 Reviewer 的 CLI；
3. **此时 Executor 席位保持 `STANDBY`，编排器绝对不对 Executor 发送任何编码指示**。

### e. 计票收敛与后续推进
1. 当其余 Reviewer 提交 `.review.yml` 或结论落盘，编排器增量收票；
2. 全体就绪后触发 UC-5（`CONSENSUS_CHECK`）进入法定共识判定；
3. 随后自然衔接至 UC-6（返工）或 UC-8（合并）。

---

## 5. 备选流与异常流

### 备选流
- **A1（态 1 编码接管）**：工作区脏且有未提交开发成果。`macao task adopt` 将其纳管为 `CODING`，派发对象为 Executor，提示完成本地测试后提交 `.dev.yml`。
- **A2（态 3 全员已落票但未结案）**：接管时发现所有配置的 Reviewer 均已产出结果，但 `state.db` 未记录。编排器直接跳转至 UC-5 执行共识对账，无需二次唤醒 Reviewer。
- **A3（态 4 返工接管）**：前次评审为 REJECT。接管后直接置为 `REWORK`，将历史问题清单注入 Executor，等待产生新的拓扑前进 commit。

### 异常流
- **E1（申请单指向不存在的 commit）**：申请单声明的 baseline 在 git 历史中无法定位。原子拒绝接管，要求提交者修正申请单。
- **E2（脏工作区与待审冲突）**：当前既存在未完成的 review-request，工作区又被修改了多个文件（脏树遮蔽）。编排器优先提示待审基线，并在报告中显式告警“工作区存在未提审改动，评审对象以申请单声明为准”，禁止将待审任务吞没为编码任务。
- **E3（法定审查员 CLI 缺失）**：缺票审查员的本地 CLI 未安装。按白名单降级或启动超时弃权，禁止无限期挂起。

---

## 6. 验收标准（可测试）

1. **待审态禁止伪造任务**：在已存在 `*-review-request-*.md` 且未结案的项目中，`probe` 必须输出 `REVIEW_PENDING`，禁止建议 `task create` 从头编码。
2. **派发对象严格对称**：
   - 接管进入 `CODING` / `REWORK` 时，活动对象**必须是 Executor**；
   - 接管进入 `WAITING_REVIEW` 时，活动对象**必须是 Reviewers**，Executor 必须为 `STANDBY`。
3. **缺票差集幂等**：若 Reviewer A 已落票、Reviewer B 未落票，`task adopt` 仅唤醒 Reviewer B，严禁向 Reviewer A 重复派活或覆盖其既有有效票。
4. **状态机与审计闭环**：接管后的 FSM 转移、审计表、SQLite 状态均具备完整的合法前序，满足单任务串行锁与不可篡改审计账本。

---

## 7. 架构自审与结论

- 场景 C 证明了：**MACAO 不仅是正向流程执行器，更是具备现场接管能力的裁判。**
- 任务不是单一属性的“编码命令”，而是根据阶段分别具象为**“工程实现任务（给 Executor）”**与**“独立审查任务（给 Reviewers）”**。在途接管补齐了这一核心闭环。
