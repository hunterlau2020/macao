# MACAO 修订后文档复审结论

- 评审日期：2026-08-26
- 被评审 commit：`47f54f2`（按评审反馈修订文档）
- 评审范围：`EXECUTIVE_SUMMARY.md`、`IMPROVEMENT_SUMMARY.md`、`MACAO_PRD_v2.md`、`SRSv1.md`；同时检查新增的 `MACAO_REVIEW_GUIDELINES.md`
- 对齐基准：`MACAO_PRD_v2.md`，并按 `MACAO_REVIEW_GUIDELINES.md` 的 L1/PG-0 规则复核
- 结论：**PARTIALLY_VERIFIED；尚未达到 L1 DOC-ALIGNED / PG-0。** 上轮 P0/P1 多数已关闭，但仍有 2 个 P0 使 Reviewer 无法从规范唯一推导状态与取得被评审代码。

## 已对齐 / 已确认项

| 上轮发现 | 复审结果 | 证据 |
|---|---|---|
| 产物责任与名称漂移 | **已关闭** | 执行摘要第 21–24 行明确 Executor/Reviewer/MACAO 三方产物责任；`checkpoint_ref` 已替换摘要中的 `checkpoint`。 |
| Layer 2 推断会推进业务状态 | **已关闭** | PRD 第 682–685、708–730 行明确 Layer 2 仅日志/预警、无显式信号时 HOLD；人工接管超时默认也改为 HOLD（第 940–944 行）。 |
| 两 Reviewer 的弃权与 2/3 无法判定 | **已关闭** | PRD 第 382–400 行给出法定人数公式与 2/3 的决策表；执行摘要第 348、410–414 行同步为“有效票不足即人工仲裁”。 |
| `opinion.status` 与 `vote` 双重语义 | **已关闭** | PRD 第 300–310 行定义映射、以 `vote` 计票并拒绝不一致产物。 |
| AEP 不完整、路由/检查点字段不统一 | **基本关闭** | PRD 第 420–426 行统一 `to`、`checkpoint_ref`，第 577–637 行补齐 Type E–G 示例。 |
| JSON/YAML 示例可解析性 | **v2 文档已验证** | 对 PRD 提取的 8 段 `json` 代码块执行 `jq empty` 均通过；3 段 `yaml` 代码块以 Ruby Psych 解析均通过。 |
| MVP 勾选状态与范围表述 | **已关闭** | PRD 第 757–765 行将 P0 改为未完成的 `[ ]`；改进总结区分了单 Reviewer PoC 和双 Reviewer MVP。 |
| 历史 SRS 误用风险 | **明显改善** | SRS 在 CLI、状态识别、AEP、MVP 章节均加“历史内容”提示和 PRD 跳转。 |

## P0：必须先解决

### P0-1 “唯一状态入口”按固定文件顺序读取，持久的 `.dev.yml` 会遮蔽后续评审/共识产物

**证据（SPEC）**：PRD 第 690–706 行的 `recognize_agent_state()` 先验证 `.macao/.dev.yml`，只要有效便立即返回 `READY_FOR_REVIEW`；对 `.review.yml` 与 `vote_result.json` 的读取在其后。`.dev.yml` 的唯一位置是 `.macao/.dev.yml`（§2.1），文档没有规定在进入评审后删除、归档或标记为已消费；反而第 402 行规定第二轮仅会覆盖同名 review 文件。因此正常路径中 `.dev.yml` 会持续有效，导致即使已收到两份 review 或已生成 `vote_result.json`，状态识别仍返回 `READY_FOR_REVIEW`。

同时，第 733–736 行宣称“业务状态只能由三类显式产物驱动”，但状态表第 742、744 行又以 `DEVELOPMENT_STARTED` / `REVIEW_REQUEST` AEP 消息推进业务状态；两类显式来源的优先级和消费规则未定义。

**影响**：这是 happy path 即可复现的阻断问题，不能唯一推导 `WAITING_REVIEW → CONSENSUS_CHECK → DONE/REWORK`，也不满足“唯一规范入口”的承诺。

**修订建议**：

1. 将状态识别改为**当前 FSM 状态 + 当前 checkpoint/round 驱动**：`CODING` 只接受当前 `.dev.yml`，`WAITING_REVIEW` 只收当前 round 的 review，`CONSENSUS_CHECK` 只收当前 round 的 vote result；AEP 指令是命令型显式转移，须列入同一状态转移表。
2. 或定义产物生命周期（生成、消费、归档/失效）和不可变路径，且明确消息与文件的优先级、幂等键与重复消息处理规则。不得仅反转读取顺序，因为旧 `vote_result.json` 同样可能遮蔽新轮次。
3. 为“正常开发完成 → 双 Reviewer 同意 → 合并”和“返工第二轮”各补一份逐步场景推演，验收点是每一步只命中一个合法转移。

### P0-2 `review_context.code_changes` 的权威结构仍不一致，且缺少可定位工作区的契约

**证据（DOC/SPEC）**：AEP `REVIEW_REQUEST` 的实际发送示例使用扁平字段 `code_changes.base_commit` / `head_commit`（PRD 第 480–484 行）；PRD §5.2 的“以本节 Schema 为准”示例却使用 `code_changes.refs.base_commit` / `head_commit`（第 832–841 行），而 Reviewer 工作流也读取嵌套的 `.code_changes.refs.*`（第 903–908 行）。因此按 AEP 示例生成的消息会使规范工作流读到 `null`。

此外，协议只给出 commit refs 与 `project` 名称，未定义 `repository_uri`、项目配置中的工作区映射或必须使用的 remote；第 904–905 行的 `<workspace>` / `git fetch --all` 无法从消息或现有配置规范唯一确定。

**影响**：Reviewer 无法按 AEP 规范稳定取得同一份被评审代码，核心的“完整 Context”尚不可执行。

**修订建议**：选定一种唯一结构（推荐所有位置均使用 `code_changes.refs.{base_commit,head_commit}`），并将其写入 AEP 字段表/Schema；`REVIEW_REQUEST` 必须提供或可由 `project` 唯一解析出 `repository_uri`、remote/工作区标识和 checkout/fetch 规则。将 §5.3 命令与这个 Schema 做一次端到端 fixture 验证。

## P1：发布/进入下一阶段前应修正

| 编号 | 发现与证据 | 建议 |
|---|---|---|
| P1-1 | PRD 第 120–124 行仍有流程表述残留：CHECKPOINT 的入口/出口顺序倒置，CONSENSUS 仍写“所有 `.review.yml` 收集完毕”，与法定人数/超时规则不一致。 | 用 FSM 事件重写表格：触发产物或命令、校验、目标状态、超时、消费/归档动作；“所有”改为“达到法定人数或超时处置完成”。 |
| P1-2 | PRD 第 402 行要求 `vote_result.json` 记录输入 SHA-256 与 AEP `message_id`，但第 321–377 行的权威 JSON Schema/示例没有承载这些字段；第 736 行要求 round 校验，`.review.yml` 示例却没有 `review_round`，状态伪代码也只传 `checkpoint_ref`。 | 在三类产物补齐 `review_round`、`input_artifacts`（path/hash/message_id）等字段及验证规则；或删除无法实现的强制承诺。 |
| P1-3 | Layer 3 图示称“立即触发 HUMAN_OVERRIDE”（PRD 第 665–673 行），实现伪代码仅在诊断置信度 `<0.7` 时触发（第 715–727 行）。 | 统一为“始终提示、低置信度触发人工接管”或“任意诊断均触发人工接管”，并同步摘要。 |
| P1-4 | `MACAO_REVIEW_GUIDELINES.md` 第 75 行保留“当前仍有 P0、处于 PG-0 与 PG-1 之间”的实时结论，违反其第 39–49 行“实时状态必须另存”的规则；第 4 行引用的 `docs/REVIEW_METHODOLOGY.md` 当前不在 `docs/` 文件清单中。 | 将实时门禁状态移至 `docs/reviews/STATUS.md`（或删除）；将来源改为可访问路径、附带副本，或明确它只是外部不可用参考。 |
| P1-5 | SRS 虽已标为历史，但全仓 14 段 JSON 示例中有 5 段来自 SRS 且不能被 `jq` 解析。 | 把历史伪格式代码块改为 `text`，或改写成合法 JSON 并明确仅用于历史说明，以满足方法论 L1 的“所有 JSON/YAML 示例可解析”要求。 |

## P2/P3：可延期但需登记

- KPI 第 1038–1044 行已把“准确率”与“测试覆盖率”分离，这是正确修订；但样本集来源、标注者、观察期和用户 KPI baseline 的采集方法仍未定义。可在 PoC 设计阶段补充，不阻断本文档 P0 闭环。
- `.dev.yml` 示例伪代码直接索引 `manifest['development']`，与“解析失败/无效即返回 None”的意图不完全一致；实际 Schema validator 应在索引前处理缺字段，建议在实现规范阶段补正。

## 交叉文档需做的文字修订

1. PRD、执行摘要、改进总结中的“99%/100%”均已增加设计目标提示，保持现状即可；后续不得把 PoC 目标写成既成实测事实。
2. 在 P0-1 修复后，同步执行摘要的状态决策树，注明它按“当前 FSM 状态/当前 checkpoint”读取产物，而不是无条件查找任一文件。
3. 在 P0-2 修复后，把执行摘要和改进总结的 `review_context` 示例也改为同一 JSON 路径，避免摘要再次演变为第二套协议。

## 建议的闭环顺序与验收标准

1. 先解决 P0-2 并提交一份可解析的 `REVIEW_REQUEST` fixture；以 §5.3 的 `jq` 路径读取 refs，且能从消息唯一得到仓库/工作区并输出 diff。
2. 再解决 P0-1，形成一张包含 AEP 命令与三类产物的单一 FSM 转移表和产物生命周期表。
3. 对以下四个文档场景做 SIM 复核：首次双 Reviewer 批准、1:1 僵局、一人超时/弃权、返工第二轮。每个场景的状态、当前 checkpoint/round、读取产物、决策与审计记录必须唯一。
4. 关闭 P1-1 至 P1-5 后，复审可给出 **L1 DOC-ALIGNED / PG-0**；当前不建议以此规格直接实现状态机或 Review Adapter。

## 产品规划补充审查：使用流程与跨 CLI 支持

**产品结论：不完备。** 当前 PRD 足以表达一个“单机、Claude Code 固定为 Executor、Codex/Kimi 固定为 Reviewer”的 PoC 主流程；它尚不是用户、管理员或新 CLI 接入方可以自行完成部署、配置、运行、治理和扩展的产品规格。PRD 自己也将 Adapter、CLI UI、端到端测试和用户手册列为未完成 P0（第 757–765 行），并把扩展 CLI、Capability Registry、远程 SSH 放在后续版本（第 767–772 行）。

### 使用流程：主干有，完整用户旅程缺失

| 优先级 | 缺口 | 证据 | 产品影响 / 应补充的流程 |
|---|---|---|---|
| P0 | **项目初始化与任务受理没有 v2 流程** | PRD 第 119 行把 REQUIREMENT 简化为“用户给出指令 → Executor 收到任务”；第 1013 行称项目/团队配置“沿用 agmsg team 定义”，但未给出 v2 的创建、导入、校验或变更流程。相关 `create team` 仅存在于已标为历史的 SRS。 | 新用户无法知道如何注册仓库、配置工作区、定义团队与角色、选择分支、录入验收标准。补 `macao init/project add/team configure/task create`（名称可调整）的输入、输出、失败提示与权限模型；需求必须含验收标准、范围、目标仓库/分支及人工批准点。 |
| P0 | **从“批准”到“合并”的发布责任未定义** | PRD 流程图仅写 `APPROVED → Merge`（第 103–106 行），AEP 仅通告 `MERGE_COMPLETED`（第 577–595 行）。 | 无法决定谁有 merge 权限、合并到哪里、是否要求 CI/分支保护、冲突后的回退和已合并后的通知。应定义 merge policy、CI gate、dry-run、人工批准、失败/回滚和发布记录。 |
| P1 | **人工接管是提示语，不是可操作的用户交互** | PRD §6.1 列出六类触发条件；执行摘要将操作写成自然语言输入。 | 用户不知道在哪个界面查看证据、选择某个候选状态、确认弃权、重试、取消或恢复。应定义 CLI 命令、状态展示、决策选项、默认值、审计回执与会话恢复。 |
| P1 | **日常运维流程缺失** | 文档有超时、崩溃和 Git 冲突处置，但未定义暂停/取消、并发任务、资源耗尽、升级/降级、日志保留及告警归属。 | 团队无法安全地同时运行多个任务或在 CLI/机器异常时恢复。应补“启动前检查 → 运行中观察 → 暂停/取消 → 重试/恢复 → 归档”的操作手册与 SLA。 |
| P1 | **数据、权限与成本边界未定义** | RBAC/Multi-tenant 被列为后续能力，当前 Context 会把任务、diff、日志交给多个厂商 CLI。 | 企业用户无法判断代码、密钥、日志是否可发送给不同供应商，也无法控制 API/订阅成本。MVP 至少应提供项目级允许的 CLI、数据脱敏、凭据保管、网络/沙箱策略、预算/并发上限和审计保留期。 |

### 跨 CLI 支持：有“三 CLI 集成计划”，没有“可扩展兼容体系”

| 优先级 | 缺口 | 证据 | 建议 |
|---|---|---|---|
| P0 | **“Adapter 可插拔、新 CLI 不改核心”的承诺没有 v2 Adapter 契约** | PRD 第 24、32 行作出承诺，但可操作的 `start/stop/sendMessage/getState` 接口只在历史 SRS §5.3；v2 仅指定 Claude Hook + Codex/Kimi PTY 的实现计划。 | 在 v2 新增 `Adapter Contract v1`：能力声明、安装/认证探测、启动/停止、任务注入、显式产物写入、消息 ACK、日志、超时/取消、重试/幂等、错误码及版本兼容性。 |
| P0 | **CLI 能力差异没有被建模，角色实际被写死** | MVP 固定 Claude Code 为 Executor、Codex/Kimi 为 Reviewer；Capability Registry 延后到 v1.2。 | 定义最小 capability manifest 与准入矩阵，例如 `can_execute`、`can_review`、`supports_hook`、`supports_noninteractive`、`supports_worktree`、平台/CLI 版本。没有该矩阵，新增 CLI 仍需修改编排规则或依赖人工约定。 |
| P1 | **缺少接入认证和兼容性验收** | Week 1–2 只验证 Hook/PT Y “可行性”；没有厂商 CLI 版本、OS、登录态、权限、退出码、提示词格式或限流的支持矩阵。 | 给每个 Adapter 建立支持版本表、preflight、模拟 CLI fixture 和 conformance test kit；通过后才可标记为“支持”。 |
| P1 | **跨 CLI 的协议生命周期不完整** | AEP 定义任务、评审、返工、合并、状态、人工接管，但缺 ACK、取消、心跳/健康检查、能力协商、重复投递去重和统一错误语义。 | 将这些加入 AEP 或 Adapter Contract，并以“PTY 断开、重复回执、CLI 升级、限流、凭据失效”作为一致性测试场景。 |

### 推荐的产品边界与下一阶段门槛

将 v2.0 对外准确定位为 **“固定三 CLI 的本地协作 PoC 规格”**，而不是“通用跨 CLI 编排平台”。在宣称可用 MVP 前，至少完成：

1. 一条可从零开始执行的用户旅程：安装/preflight → 初始化项目与团队 → 创建带验收标准的任务 → 观察与人工处置 → CI gate/合并 → 审计归档。
2. 一份 v2 Adapter Contract、能力矩阵和三个 CLI 的兼容性验收结果。
3. 上述 P0-1/P0-2 的状态机与 Context 契约闭环；否则多 CLI 评审连同一代码版本都不能保证。

## Reviewer 自审记录

本轮按新增方法论检查了字段“声明路径—AEP 示例—Reviewer 消费路径”与持久产物的顺序遮蔽问题。上一轮已指出 Context 载体不明确，但本次修订引入了新的扁平/嵌套路径分叉；后续复审将把每个 producer fixture 直接喂给 consumer 命令作为强制检查项。
