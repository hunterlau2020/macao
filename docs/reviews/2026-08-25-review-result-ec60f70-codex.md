# MACAO 文档对齐评审结论

- 评审日期：2026-08-25
- 评审范围：`EXECUTIVE_SUMMARY.md`、`IMPROVEMENT_SUMMARY.md`、`MACAO_PRD_v2.md`、`SRSv1.md`
- 对齐基准：`MACAO_PRD_v2.md`。该文件已在开头明确为 v2.0 权威基准；`SRSv1.md` 是历史基线，其正文不应作为当前实现依据。
- 结论：**部分对齐，建议在进入实现前完成 P0 闭环。** 四份文档对产品定位、MVP 收敛方向、三类核心产物、CLI 角色及 v1→v2 演进关系已经一致；但状态转换、投票降级和机器可执行契约尚不能导出唯一行为。

## 已对齐项

| 主题 | 对齐结果 | 证据与结论 |
|---|---|---|
| 文档层级 | 一致 | PRD 定义自身为权威基准；执行摘要和改进总结均明确“以 PRD 为准”；SRS 开头完整标注为 v1.0 历史基线。 |
| 产品与 MVP 方向 | 一致 | 当前范围为本地单机、Claude Code 执行、Codex/Kimi 评审，远程 SSH 与调度等放入后续版本。PRD 的跨物理机定位已注明非 MVP，不构成冲突。 |
| 主流程 | 基本一致 | 四份文档均表达“开发检查点 → 评审请求 → Reviewer 意见 → 共识 → 合并/返工”的主干；v2 也统一采用 AEP + agmsg。 |
| 演进说明 | 一致 | SRS 开头的 v1/v2 对照、改进总结的痛点说明，和 PRD 的显式产物、Context、人工接管设计相互支持。 |
| 两 Reviewer 的 2/3 解释 | 已纠正 | 执行摘要第 348 行补充了 MVP 为 Codex + Kimi 时须两票同意、1:1 进入人工裁定，和 PRD §2.3 相符。 |

## P0：实现前必须统一

### P0-1 状态识别的文字、伪代码和 FSM 相互矛盾

**证据**：PRD §3.1 规定 Layer 2 “仅作辅助，不改变实际状态”（第 548–554 行），但 §3.2 的伪代码在无显式信号且未触发低置信度诊断时返回 `inferred_state`（第 621 行）。同一伪代码只读取 `.dev.yml`，未实现 §3.1 所述 `.review.yml` 和 `vote_result.json` 的显式状态；而 §2.1 的校验示例还错误地从根路径读取 `quality_metrics`、`git`（第 204–206 行），这两个字段实际位于 `development` 下。

**影响**：不同实现会分别选择“等待人工接管”“以推断推进”“直接相信任意 `EXPLICIT` 文件”，破坏“显式信号优先、可审计”的核心承诺。

**建议**：在 PRD 增加唯一的规范状态机（输入、验证、转移、拒绝路径），并以它替换两段伪代码。明确：

1. Layer 2 是否只能产生日志/告警，还是可进入一个明确的 `SUSPECTED_*` 非业务状态；不得直接返回业务状态。
2. `.dev.yml` 的最小有效性：Schema 版本、`status`、`signal`、`development.quality_metrics`、commit 存在且与 checkpoint 一致，以及“没有测试”时的可验证豁免字段。
3. `.review.yml`、`vote_result.json` 的验证与转移规则（包括 checkpoint/round 匹配），并让实现入口覆盖三种显式产物。
4. 人工接管超时后不得静默“按高置信度状态继续”；若保留默认动作，必须写明可配置默认值、审计记录和用户授权模型。

### P0-2 投票、超时和降级没有定义可执行的法定人数

**证据**：PRD §2.3 将弃权从有效票分母中移除（第 360–364 行），流程图/状态表却要求“所有 Reviewer 返回”（第 90、631 行）；§6.2 又说一个 Reviewer 不可用后“2/3 Reviewers”继续（第 861–863 行）。执行摘要第 404–410 行同样允许用户将超时 Reviewer 标为弃权，但未说明剩下一票能否独自批准或返工。

**影响**：两 Reviewer MVP 中，一个弃权后，按现有公式一张 YES/NO 票即达到 2/3；这与“多 Reviewer 共识”目标及超时安全性可能不符，也无法实现一致的重试/人工接管行为。

**建议**：在 PRD §2.3 定义并给出决策表：`configured_reviewers`、`responded`、`abstain`、`effective_votes`、`minimum_quorum`、`deadline`、`manual_override`。至少覆盖 2 人和 3 人配置下的全同意、1:1、1 人超时/弃权、全弃权、拒绝票达到阈值等场景。同步把“所有 Reviewer 返回”改为“达到法定人数或超时处理完成”。

### P0-3 Review Context 的交付物无法被 Reviewer 按规范复现

**证据**：PRD AEP 示例把 `code_changes.diff` 写成 `git diff ...`（§2.4），详细 Context 又将 `detailed_diff` 写成同一条命令字符串（第 723 行），但 Reviewer 步骤要求读取未定义的 `/tmp/code_changes.patch` 并 `git apply`（第 783–787 行）。摘要和改进总结则描述为“完整 diff”。

**影响**：实施者无法确定消息承载的是 patch 内容、命令、文件路径还是 Git ref；不同工作树也会导致评审的对象不一致。

**建议**：选择一种规范并声明：推荐携带 `repository_uri`（或本地工作区标识）、不可变 `base_commit`/`head_commit`、`patch` 的编码与摘要；或明确只传 refs、Reviewer 必须 clone/fetch/checkout 的步骤。补充最大消息大小、缺失仓库/不可达 commit 的失败路径，以及敏感 diff 的脱敏/访问控制约束。

### P0-4 术语与产物责任存在会误导实现的漂移

**证据**：执行摘要第 21–24 行称“所有 CLI 必须生成三类 `.yml` 文件”，但 `vote_result.json` 是 JSON 且由 MACAO 生成；PRD 流程图使用 `REJECTED`（第 97 行），共识记录与状态表使用 `REWORK_REQUIRED`/`REWORK`；摘要示例把权威字段 `checkpoint_ref` 写为 `checkpoint`（第 175 行）。

**影响**：Schema、路由和 UI 的状态枚举会出现不兼容字段与决策名称。

**建议**：建立一张“产物—生成者—路径—Schema—版本—保留策略”表，并建立唯一的状态/决策枚举表。摘要示例应逐字段可被 PRD Schema 验证；明确 Executor 仅写 `.dev.yml`、Reviewer 写各自 `.review.yml`、MACAO 写 `vote_result.json`。

## P1：发布前应修正

| 编号 | 发现 | 建议 |
|---|---|---|
| P1-1 | PRD §2.4 声称 AEP 有 7 类消息，但只给出 1–4 的格式；改进总结第 231 行却称“完整格式”。且示例中 `to`、`to_agent`、`to_agents` 三种路由字段并存。 | 发布 JSON Schema/字段约束和 5–7 的最小 payload；声明路由字段是信封统一字段还是按 type 分支。改进总结改为“定义 7 类，详细示例覆盖前 4 类”。 |
| P1-2 | `.macao/.reviews/<reviewer_id>.review.yml` 会在不同 checkpoint/round 覆写；“可 git log 审计”的前提（何时提交、原子写入、重试去重）未定义。 | 用 checkpoint/round 目录或不可变文件名，写入原子化；在 `vote_result.json` 记录输入文件 hash、AEP `message_id` 与决策时间。 |
| P1-3 | PRD §4.1 的 P0 使用 `[x]`，但 §4.2 及下一步仍是未来实施计划。 | 若只是“范围内必做”，一律改用 `[ ]` 或“P0 scope”；若确已交付，补版本、证据和验收结果。 |
| P1-4 | PRD KPI 中“State Recognition Accuracy”的测量方式写为“自动化测试覆盖”，覆盖率不能代表准确率；99%/100% 的表述又与正式目标 `>95%`、`>99%`混用。 | 分别定义准确率样本集、分母、观察期、数据来源与置信目标；将摘要/改进说明的确定性数字改为目标或待 PoC 验证的假设。 |
| P1-5 | `opinion.status` 与 `vote` 均能表达批准/返工，但没有冲突时的校验规则；AEP 示例代码块带 `#` 注释，不是合法 JSON。 | 规定二者的一一映射或只保留一个权威字段；将注释移出 JSON 示例，并提供可运行的 Schema fixture。 |
| P1-6 | SRS 已有充分的历史标识，但其正文仍保留 v1 的 OpenCode、远程 Agent、旧 AEP 名称，读者跳过开头时仍可能误用。 | 在每个旧 MVP/AEP/状态章节加醒目的“历史内容，不得用于实现”提示，并链接到对应 PRD 章节；无需改写历史事实。 |

## 交叉文档需做的文字修订

1. `IMPROVEMENT_SUMMARY.md` 第 22 行的“单机+单 Reviewer 先行”应标注为 **Week 1–2 PoC**，不是 MVP 配置；同文第 218 行与 PRD 一致地写的是 Codex/Kimi 两个 Reviewer，当前容易造成范围歧义。
2. `EXECUTIVE_SUMMARY.md` 的产物表述改为“三类标准产物（两类 YAML manifest + 一份 JSON 共识记录）”；`vote_result.json` 示例字段改为 `checkpoint_ref`。
3. 三份 v2 文档都应把“100% 可信”“99%+ 由显式信号驱动”等结果性用语改为“设计目标/待 PoC 验证”，除非补充测量定义与实证来源。
4. SRS 保持为历史基线即可；其开头的版本映射与 v2 文档体系说明是此次对齐中做得最清楚的部分。

## 建议的闭环顺序与验收

1. 先修订 PRD 的状态机、Schema、投票法定人数和 Context 交付协议（P0-1 至 P0-4）。
2. 用同一组可机器校验的正/反例验证 `.dev.yml`、`.review.yml`、`vote_result.json` 和七类 AEP 消息。
3. 再由 PRD 回填执行摘要与改进总结；SRS 只补历史提示与跳转链接。
4. 验收标准：任一“开发完成、双评审同意、1:1 僵局、一人超时、全弃权、返工第二轮、进程重启”场景，都能从文档唯一推出状态、责任人、产物、超时和审计记录。

在以上 P0 项关闭前，建议不要将四份文档作为可直接开发的完整规格；关闭后可视为 **v2 文档体系对齐完成**。
