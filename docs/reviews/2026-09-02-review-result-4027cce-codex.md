# PRD v2.5 架构方案、契约库与用例体系（4027cce）独立评审结论

- **评审日期**：2026-09-02
- **Reviewer**：Codex
- **受审内容 commit**：`4027cce3ae0e2359b3bd8c31f5a58f524072a326`（短 SHA：`4027cce`）
- **复核范围**：`6e35a71..4027cce` 的变更，及 `4027cce` 的 PRD、Schema、UseCases、根配置和对应实现/测试
- **评审申请**：`docs/reviews/2026-09-02-review-request-4027cce.md`
- **权威基准**：`docs/MACAO_PRD_v2.md`、`docs/PRD_CHANGE_PROPOSAL_v2.5.md` D-1～D-9、`docs/MACAO_REVIEW_GUIDELINES.md`
- **证据状态**：DOC=`CONTRADICTED`；SPEC=`CONTRADICTED`；TEST=`PARTIALLY_VERIFIED`；CODE=`CONTRADICTED`（仅作实施差距记录，不以 L2 结论替代本轮 L1 判定）

## 结论

**REJECT：未达到 L1 DOC-ALIGNED，PG-0 不授予。**

`4027cce` 确实完成了一批有价值的整改：`.dev.yml` 核心字段、加权策略字段、Disposition 的枚举—布尔互锁、UC-7 触发域和 UC-8 本地/共享远端文字均有改进。但新增 Schema 没有同步回 PRD 的正式示例和仓库根配置；AEP/1.1 的字节与消息类型契约仍不完整，E7/E9 及提案的 E7 覆盖边仍不唯一。故 DOC/SPEC 不能标为 VERIFIED。

- P0：0
- P1：5
- P2/P3：2

## 已对齐 / 已确认项

1. `dev_manifest.schema.json` 已将 `task_id`、`checkpoint_ref`、`full_document` 纳入根级 required。
2. `macao_config.schema.json` 已要求 `version`、`policy`、每个 Reviewer 的 `vote_weight`，并把 `consensus_rule` 限定为 `weighted_2/3_v1`。
3. `review_disposition.schema.json` 已要求非空 `issues_index_sha256`，并拒绝 `DEFERRED`、`REJECTED`、`EXEMPTED_BY_ADMIN` 与 `requires_new_checkpoint=true` 的组合。
4. UC-7 已从运行期 E7 触发条件中剥离 init 歧义和 Git conflict；UC-8 也把共享远端与纯本地的意图分开说明。
5. 9 份 valid fixture 均被接受、13 份 invalid fixture 均被拒绝；`docs/schemas/` 与 `src/macao/schemas/` 的 8 份 Schema 无差异。
6. `PYTHONPATH=src python3 -m unittest discover tests -q`：`Ran 86 tests in 35.637s — OK`；`python3 -m compileall -q src tests` 通过。
7. 受审主文档和 13 份 UseCase 中 27 个标注 YAML/JSON 的代码块均可解析；`git diff --check 6e35a71..4027cce` 无空白错误。

解析通过不等于契约通过；以下 P1 的关键反例正是“JSON/YAML 合法、但不符合当前 Draft-07 Schema 或无法唯一推出行为”。

## P0：必须先解决

无。

## P1：进入 PG-0 前必须修正

### P1-1：PRD 的正式产物/AEP 示例与刚收紧的 Schema 不一致

**证据与可复现结果**：以 `src/macao/core/schema.py` 的实际 `SchemaValidator` 校验 PRD 代码块：

| PRD 示例位置 | 对应 Schema | 实际结果 | 直接原因 |
|---|---|---|---|
| `docs/MACAO_PRD_v2.md:372` Type A | `aep_envelope` | REJECT | 缺 `payload.specification_summary` 与 `acceptance_criteria` |
| `:403` Type B | `aep_envelope` / `review_context` | REJECT | `review_context` 缺 Schema 强制的 `evidence` 块，且 `dev_checkpoint` 少字段 |
| `:537` Type E | `aep_envelope` | REJECT | 示例使用 `vote_result` / `deadline`，Schema 要求 `vote_result_ref` / `timeout_deadline` |
| `:642` `executor.disposition.yml` | `review_disposition` | REJECT | 缺刚改为必填的 `issues_index_sha256` |
| `:1370` `macao.yaml` | `macao_config` | REJECT | 缺必填 `version` 和 `policy.min_effective_votes` |

PRD `docs/MACAO_PRD_v2.md:364-368` 把这些信封定义为全部 8 类的统一协议，§2.5 又把 disposition 的代码块标为正式格式；评审方法论要求示例可与正式 Schema 逐字段核验。因此不能把这些当作“仅示意”。

**验收标准**：选择一套规范字段名并同步 PRD §2.4/§2.5/§13、变更提案、fixtures、Schema；在 CI 中从文档提取这些示例并用 `SchemaValidator` 校验。尤其应将 Type E 的 `vote_result_ref`、`issues_index_sha256`、deadline 的唯一命名固定下来。

### P1-2：AEP 仍未实现 PRD 所承诺的 16 KiB/2048 字节及全部 8 类 payload 契约

**证据**：

- PRD `docs/MACAO_PRD_v2.md:359-362` 要求消息总量 16384 **字节**、每个内联自然语言字段 2048 **字节**、收发端双向拒绝超限；代码清单 `docs/v2.5_CODE_CHANGE_INVENTORY.md:64` 将其称为 Schema 的硬约束。
- 实际 `docs/schemas/aep_envelope.schema.json:33-134` 仅为 Type A/B/E/H 定义部分 required 字段；Type C/D/F/G 仍可用 `payload: {}`。
- `:43`、`:46`、`:108-109` 使用的是 JSON Schema `maxLength: 2048`（Unicode 字符计数），既不是 UTF-8 字节计数，也没有总 envelope 的 16384 字节限制；各 payload object 也未关闭额外属性。

**独立反例**：以下输入被实际 `validate_aep_envelope()` 接受：

```text
Type A 的 specification_summary = 2048 个“中”（6144 UTF-8 bytes）
再附加 extra = 50000 个字符

Type C / D / F / G 的 payload = {}
```

**影响**：超限正文仍能进入消息队列，未定义的消息类型可缺控制字段，和 D-7“只承载控制字段与可验证引用”相反。

**验收标准**：为八类消息各自定义关闭额外字段的 payload Schema；在 `AEPEnvelope.create/parse` 与 MessageBus 的发送、接收路径按 JSON UTF-8 序列化字节数实施 16384/2048 限制；加入 CJK/emoji 多字节边界、总包超限、未知字段、八类空 payload 的正反测试。

### P1-3：AEP/1.1 与 `DISPOSITION_REQUIRED` 在实现层仍不可用，现有测试反而固化了旧协议

**证据**：

- PRD `docs/MACAO_PRD_v2.md:346-366`、提案 `docs/PRD_CHANGE_PROPOSAL_v2.5.md:40` 定义 AEP/1.1 的 8 类消息，并规定统一发送协议为 `AEP/1.1`（兼容读取 1.0）。
- `src/macao/msg/envelope.py:1,11-15,35-46` 的注释、类文档、`PROTOCOL` 仍为 AEP/1.0；`src/macao/msg/bus.py:75-85` 接收时也重建 AEP/1.0。
- `src/macao/core/types.py:22-30` 只有 7 个枚举，缺少 `DISPOSITION_REQUIRED`；独立执行 `AEPType.DISPOSITION_REQUIRED` 得到 `AttributeError`。
- `tests/test_msg_bus.py:13-25` 显式断言新建信封的协议是 `AEP/1.0`，使 86 项回归无法证明 v2.5 协议已切换。

**影响**：UC-5/UC-6 和 PRD E5 所要求的 Type E 调度无法通过类型安全 API 发出；生产发送端也持续产生与规范不同的协议版本。

**验收标准**：将默认发送、持久化、重建协议统一为 AEP/1.1；加入第八枚举和实际 `DISPOSITION_REQUIRED` 发送路径；保留 AEP/1.0 仅作为 parse 的向后兼容分支，并覆盖 1.0 输入/1.1 输出的双向测试。

### P1-4：纯本地模式与 `macao_config` Schema/根配置相互矛盾

**证据**：

- UC-8 `docs/usercases/UC8-merge-signoff.md:23-24,56` 把纯本地模式定义为 `repository.remote_name: null`，并要求跳过远端 push、保留本地 evidence seal。
- `docs/schemas/macao_config.schema.json:16-20` 却把 `remote_name` 设为根级必填的非空 string；将 valid fixture 的 `remote_name` 改为 `null` 后，`validate_config()` 结果为 `False`。
- 仓库根 `macao.yaml` 本身也不能通过新 Schema：它缺少 `version`、所有 reviewer 的 `vote_weight`、完整 policy 字段，且仍使用旧 `consensus_rule: "2/3_majority"`；`validate_config(macao.yaml)` 返回 `False: 'version' is a required property`。

**影响**：UC-8 声称支持的模式无法由单一事实源表示，而真实项目配置已在该 commit 下被自身 Schema 拒绝；这会使 `init`、merge、测试和部署消费方无法取得唯一配置。

**验收标准**：明确支持策略。若支持本地模式，Schema/ConfigManager 必须允许并保留显式 `null`（不得默认回填 `origin`）；若不支持，应删除 UC-8 本地分支。无论哪种方案，更新根 `macao.yaml` 与 PRD §13 示例，并为共享/纯本地各加一份有效配置 fixture 与一次 Merge Controller 场景测试。

### P1-5：E7/E9 和提案的 REWORK 覆盖边仍给出互斥状态机

**证据**：

- PRD 状态表 `docs/MACAO_PRD_v2.md:859` 允许 E7 从 `HOLD(CONSENSUS_CHECK 或 REWORK)` 选择 `RETRY_REVIEW` 并“触发 E9”。
- 同表 `:860` 却限定 E9 的源状态为 `CONSENSUS_CHECK`。因此从 `REWORK` HOLD 选择 `RETRY_REVIEW` 时，目标边不合法。
- 变更提案 `docs/PRD_CHANGE_PROPOSAL_v2.5.md:135` 仍写“REWORK_REQUIRED 覆盖为 APPROVED … 通过 E7 转移**直接**推进至 `MERGING`”；这与 PRD `:859` 和 UC-7 `docs/usercases/UC7-human-override.md:35-41` 的两步路径（override → `SHOULD_DISPOSE` → Executor FINAL → E4/E5a）冲突。

**影响**：同一管理员选择可被实现为直接 MERGING、等待 Executor FINAL，或因 E9 源状态不匹配而拒绝，不能唯一推导。

**验收标准**：固定 E7 各源状态 × choice 的完整矩阵。若 `REWORK` 可选 `RETRY_REVIEW`，E9 必须接受该源状态并定义 round/归档语义；否则 E7 必须禁止该组合。删除提案中的直接 MERGING 表述，所有 APPROVED 路径统一为等待 Executor 的合法 FINAL 后再走 E4/E5a。

## P2/P3：可延期但需登记

### P2-1：Disposition 的“反向引用 vote result”仍未成为可表示的机器字段

提案 `docs/PRD_CHANGE_PROPOSAL_v2.5.md:78-81,188-193` 要求 `review_disposition` 引用冻结 vote result 的 `path + evidence_commit + sha256` 与 `issues_index` hash；现有 Schema `docs/schemas/review_disposition.schema.json:6-42` 只要求一个任意非空 `issues_index_sha256`，没有 `vote_result_ref`。这不能单凭 Schema 完成跨产物 hash 比对，但至少应能表达引用，以便 Orchestrator 进行运行时验证并审计。

### P3-1：申请中的 Markdown 数量不可从受审 commit 重现

申请 `docs/reviews/2026-09-02-review-request-4027cce.md:43` 声称“188 份文档（git ls-files 170、docs 177）”；在被评审 `4027cce` 上，`git ls-tree -r --name-only 4027cce` 实计 `.md` 为 176，其中 `docs/` 为 175。应记录精确命令、是否展开 symlink、是否包含未跟踪评审文件，避免将工作区统计写成 commit 基线事实。

## 交叉文档需做的文字修订

1. 更新 PRD §2.4 Type A/B/E 的字段和 §2.5、§13 示例，使其逐个通过对应 Schema；将当前 PRD AEP 代码块纳入 doctest/CI。
2. 在 AEP 规范中明确“字符”与“UTF-8 字节”的区别，补上 16 KiB 的总体约束和八类消息的最小 payload。
3. 同步 `macao.yaml`、UC-8、Config Schema、ConfigManager 的 remote mode 定义。
4. 清理提案中 E7 的“直接 MERGING”，并收敛 E7/E9 源状态。
5. 为 disposition 加入 `vote_result_ref`，由运行时校验该引用、checkpoint/round 和 `issues_index_sha256` 一致。

## 建议的闭环顺序与验收标准

1. 先确定唯一 AEP v1.1 wire contract：八类消息字段、输出协议、字节预算和 Type E 调度，随后同步 PRD 示例、Schema、枚举、MessageBus 与测试。
2. 冻结 `macao.yaml` 的共享/本地远端模型，保证根配置与 PRD 示例均是 valid fixture。
3. 以 E7 源状态×choice 表消除 E7/E9/提案冲突，并用 DEADLOCK、超时、REWORK 上限、NEEDS_ADMIN 四条场景验证。
4. 添加文档示例 Schema 测试、UTF-8 budget 测试、AEP 1.0 输入兼容/AEP 1.1 输出测试、Type E 实际发送测试、纯本地/共享远端合并测试。
5. P1 为零后重新申请 L1；若继续把实现纳入申请，则需另行复核 L2，不能用当前 86 项回归外推。

## Reviewer 自审记录

- 已以当前 `SchemaValidator` 而非纯 JSON/YAML 解析验证 PRD 正式示例。
- 已检查字段声明与实际读取/发送路径（AEP 协议、枚举、MessageBus、ConfigManager）。
- 已区分 L1 的 DOC/SPEC 结论与实现的 L2 差距；本结论不因测试通过外推 L2/L3。
- 所有 P1 均附具体文件、行号和可复现输入或状态推演。
- 未修改用户已有的 `docs/MACAO_REVIEW_GUIDELINES.md` 工作区改动，也未修改 `docs/reviews/STATUS.md`。
