# PRD v2.5 Design Sync 与 UseCases v2.5 Alignment 独立复审结论

- **评审日期**：2026-09-02
- **评审对象**：`a0123e8`（两份申请：PRD v2.5 Design Sync、UseCases v2.5 Alignment）
- **对照基准**：`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/MACAO_PRD_v2.md`、`docs/PRD_CHANGE_PROPOSAL_v2.5.md`、`docs/usercases/`
- **结论**：**REJECT — 不授予 L1 DOC-ALIGNED / PG-0。** 本轮确实修复了上一轮若干示例与协议版本问题，但三个核心“机器契约已 fail-closed/已物理锁死”的声明仍可由合法输入绕过；规格、Schema 与用例不能唯一推出同一行为。
- **证据状态**：DOC/SPEC **CONTRADICTED**；CODE 对本轮运行时声明为 **PARTIALLY_VERIFIED**；TEST **VERIFIED**（但反例覆盖不足）。

## 已对齐 / 已确认项

1. `tests/test_prd_snippets_schema.py` 已覆盖 PRD §2.1–§2.5、§5.2、§13 的正例；`PYTHONPATH=src python3 -m unittest discover tests -q` 实测 **92 tests / OK**。`python3 -m compileall -q src tests` 亦通过。
2. PRD §2.4 的八个 AEP 正例已使用 `AEP/1.1`，`AEPType` 已有 `DISPOSITION_REQUIRED`；`docs/schemas/` 与 `src/macao/schemas/` 在本轮相同。
3. `remote_name: null` 已在 `macao_config` 与 `review_context` Schema 中可解析，且存在正例 fixture；远端 post-push 校验失败不再执行本地 reset（`src/macao/merge/controller.py:141-143`）。
4. PRD 的 disposition 正例补上了 `vote_result_ref`，并明确要求 disposition 反向引用冻结 vote result（`docs/MACAO_PRD_v2.md:676-681, 708-715`；`docs/PRD_CHANGE_PROPOSAL_v2.5.md:186-193`）。这正是下列未闭环项应当由契约保证的语义。

## P0：必须先解决

无。

## P1：不应授予本轮 L1 的阻断项

### P1-1 加权反支配与法定人数仍非机器硬约束

申请称 `dictator_cap_enabled: const true`、`minimum_winning_seats >= 2` 已“物理杜绝”支配漏洞，但这只是布尔开关及一个局部下限，并没有验证 PRD 的五重公式。PRD 要求对每位 reviewer 执行 `3*w_i < 2*W`，并要求两个 quorum 分别不低于 `ceil(2N/3)` / `ceil(2W/3)`（`docs/MACAO_PRD_v2.md:329-336`）。然而 Schema 仅将两个 quorum 允许为任意 `>= 1`（`docs/schemas/macao_config.schema.json:71-76`），`ConfigManager.load()` 也只上调 seat quorum，不校验权重 quorum 或独裁帽（`src/macao/core/config.py:39-48`）。

可复现反例：从有效 `macao_config.yaml` 复制，设置三席权重为 `100, 1, 1`，并设 `seat_quorum_required=1`、`weight_quorum_required=1`；此时 `3*100=300 >= 2*(100+1+1)=204`，但 `validate_config()` 返回 `(True, None)`。所以“D-6 反支配门禁 Schema 物理锁死”及 UC-5/UC-10 的硬约束表述不成立。

应在加载配置时以 reviewer 权重进行语义校验（或把 quorum 全部派生、禁止配置覆写），并添加上述反例、低权重 quorum 与边界等式的拒绝测试；运行时计票也必须实际读取相同权重/门槛，才能关闭此项。

### P1-2 disposition 的不可变 vote-result 绑定仍可被 Schema 和用例示例绕过

PRD/提案要求每个 disposition 反向引用冻结的 `vote_result`（`docs/MACAO_PRD_v2.md:676-681`、`docs/PRD_CHANGE_PROPOSAL_v2.5.md:186-193`），但 `vote_result_ref` 没有被列入 disposition Schema 的 `required`（`docs/schemas/review_disposition.schema.json:6-16`）。因此，移除该字段后的 manifest 仍通过 `validate_review_disposition()`。

该遗漏已经造成跨文档矛盾：`docs/usercases/UC6-issue-triage-rework.md:26-55` 和 `docs/PRD_CHANGE_PROPOSAL_v2.5.md:149-176` 的 disposition 示例都没有 `vote_result_ref`，却把自己描述成规范/结构化信封。它们恰好被当前 fail-open Schema 接受，无法满足不可变审计链。

应将 `vote_result_ref` 纳入 required，并关闭该 ref 对象的额外属性、要求 `path/evidence_commit/sha256`；同时修正 UC-6 与提案示例，并增加“移除 ref / 伪造 ref / ref 与 issues_index_hash 不匹配”负例。Schema 只能保证字段存在，跨产物 hash/ref 一致性仍须由 Orchestrator 失败关闭校验。

### P1-3 AEP 的“8 类封闭 Payload + 2048 字节双向严格校验”不是实际契约

PRD 禁止内联长正文，并规定发送端和接收端对每个内联自然语言字段执行 2048 字节限制（`docs/MACAO_PRD_v2.md:359-362`）。申请亦把“8 类封闭 Payload”列为核心修复，但各 Type payload 没有 `additionalProperties: false`，Type E 甚至只要求 `checkpoint_ref` 与 `review_round`，未要求其定义性绑定 `task_id`、`vote_result_ref`、`issues_index_sha256`、deadline（`docs/schemas/aep_envelope.schema.json:174-196`）。

运行时检查同样只遍历 payload 第一层和第一层字符串数组（`src/macao/msg/envelope.py:39-52`）。构造一个总计 4,025 字节的合法 `REVIEW_REQUEST`，仅将 `payload.review_context.task_info.description` 设为 3,000 个 ASCII 字符，`AEPEnvelope.parse()` 实测返回 `(True, None)`；该嵌套长正文未被检查。此输入直接违反 PRD 的单字段上限，而 PRD 正例测试只验证正例，未覆盖它。

应为每种 Type 的 payload 和嵌套引用对象关闭额外字段；将 Type E 最小必填字段写入 Schema；并以递归、UTF-8 字节级方式检查全部受限文本字段（包括嵌套 context/list/object）。至少增加上述 3,000-byte 嵌套反例、未知 payload 字段、缺 Type-E vote-result 绑定及多字节字符边界的发送/接收双向测试。

## P2/P3：可随后关闭，但不得误报为已实现

1. **本地模式的 review context 尚未端到端传递（P2，CODE）**：尽管 Schema 接受 `null`，`ReviewContextBuilder` 固定默认 `origin`，并在 build 时以 `self.remote_name or "origin"` 再次替换空值（`src/macao/utils/context_builder.py:24-27, 116-120`）；`dispatch_review_requests()` 也未传入项目配置的 remote。UC-8 的纯本地合并分支可以跳过 push，但 UC-4 派给 reviewer 的上下文仍会声称有 `origin`。应在实现阶段传递明确的 `null` 和对应 fetch policy，并做无 remote 的派发测试。
2. **不能把本次 L1 文档核查表述为已完成 L2（P2，CODE）**：当前 `ConsensusEngine` 仍按人数、浮点比例计票，未读取 `vote_weight` 或 D-6 五重门禁（`src/macao/consensus/engine.py:17-66`）；`collect_and_evaluate_consensus()` 在 `APPROVED` 时直接 E4 进入 `MERGING`，没有按 UC-5/UC-6 发送 `DISPOSITION_REQUIRED` 并等待 FINAL disposition（`src/macao/workflow/orchestrator.py:695-712`）。这些不改变本报告的 L1 判定依据，但使“已全面实装/全链路闭环”的措辞不能作为 L2 或场景验证证据。
3. `test_prd_snippets_schema.py` 的文件句柄未关闭，运行时出现 `ResourceWarning`（P3）。可改为 context manager，以保持回归输出干净。

## 交叉文档需做的文字修订

- 用“配置字段存在”替换“物理锁死/杜绝”之类的既成事实，直到语义校验和测试落地；或在 PRD、提案、UC-5、UC-10 中同步给出可执行的配置期公式校验。
- `docs/PRD_CHANGE_PROPOSAL_v2.5.md` 与 UC-6 的处置示例必须与 PRD §2.5 相同，显式包含 `vote_result_ref`。
- AEP 部分需把“封闭”精确定义为 payload 与必要嵌套对象 `additionalProperties: false`，并规定各 Type 的必填控制字段；不要以“正例能通过”替代 fail-closed 的反例证据。
- UC-4/UC-8 对 `remote_name: null` 的实际传递契约应说明或实现，避免 reviewer 根据伪造的 `origin` 采取远端 fetch。

## 建议的闭环顺序与验收标准

1. 先修复 P1-1 的权重/独裁帽/quorum 语义校验，并以 `100/1/1`、边界等式、低 quorum 配置证明 fail-closed。
2. 再统一 Type E、`review_disposition`、PRD/提案/UC-6 的 vote-result 引用字段，并为缺字段和伪造绑定加负例。
3. 最后关闭 AEP payload 与字节预算递归检查；验证发送和接收均拒绝嵌套 2,049-byte UTF-8 文本与未知字段。
4. 完成后重新执行所有 Schema fixture、PRD/UC 代码块（含负例）及全套 unittest。仅在上述 DOC/SPEC 反例全部失败关闭后，重新申请 L1；之后再单列申请 L2，验证加权计票、disposition HOLD 和纯本地派发的代码路径。

## Reviewer 自审记录

本轮按 GUIDELINES §9 强制检查了字段声明与运行时读取路径、强断言的反例、以及 YAML/JSON 示例。前两轮已反复出现“正例通过被误作闭环”的模式；本轮专门补做缺字段、嵌套字节限制与权重边界的反例，未将 92 项 happy-path/已有回归测试外推为 fail-closed 证明。
