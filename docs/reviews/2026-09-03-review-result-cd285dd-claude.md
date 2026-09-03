# PRD v2.5 Design-Sync 轨 与 UseCases v2.5 Alignment 轨 独立评审结论（`cd285dd`）

- **评审日期**：2026-09-03
- **评审人**：claude
- **评审对象**：
  - 轨 A：[`2026-09-03-review-request-cd285dd-PRD-v2.5-Design-Sync.md`](2026-09-03-review-request-cd285dd-PRD-v2.5-Design-Sync.md)
  - 轨 B：[`2026-09-03-review-request-cd285dd-UseCases-v2.5-Alignment.md`](2026-09-03-review-request-cd285dd-UseCases-v2.5-Alignment.md)
- **申请声称基线**：`cd285dd`；**工作区 HEAD**：`6746294`（差量 = 三份 `cd285dd` 申请 + `STATUS.md`；PRD / Schema / 提案 / 清单 / 用例 / `src/` 正文与 `cd285dd` 一致）
- **前序对象与我的票**：`a0123e8`（轨 A `NO_APPROVE` P1×2；轨 B `YES_APPROVE`）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§8、§9；`docs/MACAO_PRD_v2.md`；提案 §2 D-1～D-9；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **定级申请**：两轨均为 **L1 DOC-ALIGNED / PG-0**

## 结论

| 轨 | 机器票 | BLOCKING | 说明 |
|---|---|---|---|
| **A 设计同步** | **`NO_APPROVE`** | **P1 × 5** | 无 P0。E7 源态（我上轮 A-P1-1）已**完全闭环**；D-6 配置期语义校验（我上轮 A-P1-2）**主体闭环**。但本轮的 E7 统一在提案 §4.2 留下两处新的同类矛盾；仓库自身的 `macao.yaml` 通不过本轮宣称落地的校验；`vote_result.json` 运行时写出的 `policy_snapshot` 与 `issues_index_sha256` 是**与实际算法无关的伪证**；契约库对同一实体保留双名。 |
| **B 用例体系** | **`YES_APPROVE`** | **P1 × 0** | 13 份用例正文无机器可证的不一致；UC-6 `vote_result_ref` 已按 PRD §2.5 与收紧后的契约补齐并过校验。P2×4 登记，不作为条件（F-17 禁止「有条件通过」）。 |

轨 A 的 5 条 P1 全部落在交付物 #2（契约库）、#3（提案）与运行时；**没有一条落在轨 B 的 13 份用例正文内**，故两轨分票。93/93 与 `compileall` 本机为真，但**不构成 L2 证据**。

---

## 0. Reviewer 自审记录（GUIDELINES §9）

### 0.1 本轮我判错、经同行证据复验后**推翻自己**的一条

我在独立复放申请 §3 时，对仓库根 `macao.yaml` 只跑了 Draft-07 结构校验，打印 `root macao.yaml -> True` 并据此认定「根配置过契约」。**这是错的。**

本轮申请的核心修复恰恰是把 D-6 五重公式放进 `validate_config()` 这一**语义层**；只跑 Draft-07 等于绕开了本轮唯一需要检验的那一层。Grok 的 DesignSync P1-1 指出根文件通不过语义校验后，我复验：

```
N = 4  weights = [1, 1, 1, 1]
policy: seat_quorum_required=2  weight_quorum_required=2  minimum_winning_seats=2
validate_config(root macao.yaml) -> (False, 'seat_quorum_required (2) is less than required minimum ceil(2N/3) = 3')
ConfigManager().load('macao.yaml') -> ValueError: Invalid macao.yaml schema: seat_quorum_required (2) is ...
```

结论成立，已作为本轮 **A-P1-2** 记入。这是我在 `a0123e8` 轮亲手命名的「枚举封闭 ≠ 语义成立」陷阱的**镜像形态**：那次我误把布尔开关当成公式，这次我误把结构校验当成语义校验。**同一条自审规则我连续两轮踩中两个方向**，故本条按 §9 模式 A（声明的校验位置 ≠ 实际起作用的校验位置）登记为我的漏审，而非仅记为「他人补充」。

### 0.2 本轮我先怀疑、经隔离测试后**撤回**的四条

| # | 我的初判 | 隔离测试 | 处置 |
|---|---|---|---|
| 1 | 交付物 #6 `docs/FAQ.md` 不存在（链接检查报 BROKEN） | 我的脚本在 `cd docs/reviews` 后的残留 cwd 下运行。以仓库根重跑：`docs/FAQ.md` 存在，65 条相对链接仅 1 条断（见 P3-1） | **撤回** |
| 2 | STATUS.md 计数错误（盘面 133 结论类 vs 声称 130） | 盘面含 3 份**未跟踪**的本轮同行报告。`git ls-files` 口径：`review-result-*` 126 + `review-2.5-*` 2 + `REVIEW_METHODOLOGY_*` 2 = **130**，申请类 **32**，与头部第 6 行**完全一致** | **撤回**（仅保留表标题滞后，见 P3-2） |
| 3 | 清单 #4 声称「与现有仓库目录结构精确对齐」但 7 条路径不存在 | 逐行核对：7 条全部标注 **新建 / 计划测试**（`INVENTORY:93,112-117`），缺失是预期 | **撤回** |
| 4 | 提案 `:394` 配置示例缺 `version` 而 FAIL | 该块是 §7.1 的**片段**（自 `team:` 起），非完整 `macao.yaml`。误报源于我的形状探测器 | **撤回** |

另有一条**探针无异常**需登记（避免只报阳性）：`macao init` 的 `DEFAULT_CONFIG_TEMPLATE`（`src/macao/cli/main.py:26-59`，N=3 权重全 1，quorum 2/2 = ⌈2·3/3⌉）与向导 `src/macao/cli/wizard.py:176-200`（`quorum_votes = ceil(2·N/3)`，且 `r.setdefault("vote_weight", 1)` 强制 W=N）**均产出可被 `validate_config` 接受的配置**。这反过来收紧了 A-P1-2 的范围：**全仓唯一不合规的配置文件，就是本项目自己在用的那一份**。

### 0.3 强制自检 5 项

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 实际读取路径 | E7 源态四处同句 ✓；**提案 §4.2 L128/L129 的 HOLD 与 PRD:888 的 HOLD 定义不同句**（A-P1-1）；**`policy_snapshot` 字段名与其取值来源不同源**（A-P1-3） |
| 2 | 「已完成 / 100%」是否等于证据 | 申请 §3 的 5 条机验 **VERIFIED**；申请 §1「全部阻断项已完成代码与文档级物理闭环」对 A-P1-2/A-P1-4 **CONTRADICTED** |
| 3 | 确定性语言是否标注目标 | 申请 §4「物理闭环」「100% fail-closed」未标目标状态；用例 README:9「全面实装对账」同（B-P2-2） |
| 4 | 代码块是否可解析并过契约 | PRD 六节示例 + 八份 AEP 信封 **14/14 PASS**；211 份 Markdown **0 控制字符** |
| 5 | 每条 P1 是否附文件:行号与可复跑命令 | 是 |

### 0.4 证据类型适用性（GUIDELINES §3.1）

| 类型 | 状态 | 依据 |
|---|---|---|
| DOC | **CONTRADICTED** | A-P1-1：提案 §4.2 与 PRD §3.3 对 `HOLD` 的可停驻状态给出互斥答案 |
| SPEC | **CONTRADICTED** | A-P1-5：`vote_result.schema.json` 对同一实体同时收 `executor`/`executor_id`、`timestamp`/`generated_at`，违反 §5 唯一权威表 |
| CODE | **CONTRADICTED** | A-P1-2（活配置被自己的 Loader 拒绝）、A-P1-3（伪证快照）、A-P1-4（E4 绕过 disposition） |
| SIM | PARTIALLY_VERIFIED | §6 反例库 6 条可机验场景在**不加权**前提下 6/6 正确；加权反例判错（见 A-P1-3） |
| TEST | VERIFIED（有覆盖缺口） | 93/93 OK；未覆盖仓库根 `macao.yaml`、加权票型、带 issue 的 APPROVED |
| OPS | NOT_APPLICABLE | 本轮目标 L1，未申请 L4 |

---

## 一、申请 §3 自动化结论：独立重放

| 申请声明 | 本机实测 | 判定 |
|---|---|---|
| PRD 全量代码块 Draft-07 校验 100% PASS | §2.1/2.2/2.3/2.5/5.2/§13 各 1 块 **PASS**；§2.4 与 §6.1 的 8 份 AEP 信封 **8/8 PASS**（Schema + 递归预算双跑） | **VERIFIED** |
| 206 份 Markdown 0 控制字符 | 控制字节 **0**；份数本机 glob 得 **211** | 结论 **VERIFIED**；份数 **PARTIALLY_VERIFIED**（P3-3） |
| Fixtures 10/10 正例 + 20/20 反例 FAIL-CLOSED | 正例 10/10；反例在 `tests/test_schema.py:329-366` 的**混合校验器**下 20/20 REJECTED | **PARTIALLY_VERIFIED** —— 该条挂在标题「**Draft-07 Schema 与 Fixtures 双向校验**」之下，但其中 **3 份 `macao_config_*` 反例单跑 Draft-07 为 ACCEPTED**（仅由 `validate_config` 语义层拒绝），第 4 份 `aep_payload_oversized.json` 由 `validate_budget()` 拒绝。见 A-P2-1 |
| `docs/schemas/` 与 `src/macao/schemas/` 0 diff | 8 份契约 + 全部 fixtures 逐字节相同（差异仅 `README.md` / `__init__.py` / `__pycache__`） | **VERIFIED** |
| 93 tests 100% OK | `Ran 93 tests ... OK`（33.4s） | **VERIFIED** |
| `compileall -q src tests` 0 Errors | rc=0 | **VERIFIED** |

补充（申请未列，但属同一质量门）：`git diff --check cd285dd^ cd285dd` → `src/macao/core/schema.py:166: new blank line at EOF.`（A-P3-4，与 codex P2-2 同）。

---

## 二、我在 `a0123e8` 轮 2 条 P1 的闭环核验

### A-P1-1（E7 源态四处只改对两处）—— **完全闭环** ✓

| 位置 | `a0123e8` | `cd285dd` |
|---|---|---|
| `docs/MACAO_PRD_v2.md:881` | `HOLD`（`CONSENSUS_CHECK`） | 未变 ✓ |
| `docs/PRD_CHANGE_PROPOSAL_v2.5.md:230` | `HOLD`（`CONSENSUS_CHECK` 或 `REWORK`） | **`HOLD`（`CONSENSUS_CHECK`）** ✓ |
| `docs/v2.5_CODE_CHANGE_INVENTORY.md:85` | 从 HOLD（`CONSENSUS_CHECK` 或 `REWORK`） | **从 HOLD（`CONSENSUS_CHECK`）** ✓ |
| 提案 `:218` 超时停驻态 | 「`APPROVED` 停 `CONSENSUS_CHECK`，`REWORK_REQUIRED` 停 `REWORK`」 | **「超时停留在 `CONSENSUS_CHECK`（HOLD 态）」** ✓ |

验收命令（我上轮给出的）本机零命中：

```bash
grep -rn 'HOLD`（`CONSENSUS_CHECK` 或 `REWORK`）' docs/ --include=*.md | grep -v docs/reviews/
# -> 无输出（0 命中）
```

（自校：我上轮给出的宽松式 `CONSENSUS_CHECK.*或.*REWORK` 会命中 4 行**合法**文本 —— `INVENTORY:85`、`UC6:14`、`UC6:87`、`PRD:881` 中「`CONSENSUS_CHECK`」与「`REWORK`」本就并列出现且语义正确。故此处改用上面的精确串式，避免把噪声写成验收依据。）

**但**：该修复把 `HOLD` 收紧为「仅 `CONSENSUS_CHECK` 的子状态」（PRD:888 新句）后，提案 §4.2 中两行仍写「当前状态（HOLD）」，产生新的同类矛盾 —— 见 **A-P1-1（本轮）**。

### A-P1-2（D-6 公式从未成为机器约束）—— **主体闭环，活配置未跟** ⚠

`src/macao/core/schema.py:113-157` 现实现全部五项配置期检查，且 `ConfigManager.load()` 在派生默认值**之前**调用它。我上轮的反例已全部被拒：

```
weights=[5,1,1] (3*5=15 >= 2*7=14)      -> REJECTED: Dictator cap violation ...
seat_quorum=1 (N=3, 需 >= 2)            -> REJECTED: seat_quorum_required (1) is less than ... = 2
weight_quorum=1 (W=3, 需 >= 2)          -> REJECTED: weight_quorum_required (1) is less than ... = 2
minimum_winning_seats=1                  -> REJECTED（Draft-07 minimum:2）
dictator_cap_enabled=false               -> REJECTED（Draft-07 const:true）
minimum_winning_seats=4 (N=3)            -> REJECTED: cannot exceed number of reviewers (3)
```

三份新反例 fixture 的**拒因与文件名所称的那一维吻合**（我逐条打印了拒因，未止于 REJECTED）。剩余缺口两条：仓库自身配置（A-P1-2 本轮）与运行时计票（A-P1-3）。

---

## 三、轨 A：P1（5 项）

### A-P1-1　E7 源态统一后，提案 §4.2 仍把 HOLD 停驻在 `REWORK`，与 PRD 新增的 HOLD 定义及封闭条款互斥

**这是本轮修复引入的新缺陷，属「修复即引入同类缺陷」模式在 `a0123e8` 中断一轮后的复发。**

三处权威文本，对「disposition 超时发生在 `REWORK` 状态时停在哪、E7 从哪触发」给出互斥答案：

| 位置 | 原文 |
|---|---|
| `docs/MACAO_PRD_v2.md:888` | `HOLD` 为受控暂停子状态（任务处于 **`CONSENSUS_CHECK`** 等待处置/人工介入） |
| `docs/MACAO_PRD_v2.md:889` | 除本表所列来源外，**任何实现不得引入其他状态转移路径** |
| `docs/MACAO_PRD_v2.md:881` / 提案 `:230` / 清单 `:85` | E7 源态 = `HOLD`（`CONSENSUS_CHECK`），本轮刚统一 |
| `docs/PRD_CHANGE_PROPOSAL_v2.5.md:128` | disposition 超时 \| **当前状态（HOLD）** \| 发送 `HUMAN_OVERRIDE_REQUEST` \| **E7 管理员裁决** |
| `docs/PRD_CHANGE_PROPOSAL_v2.5.md:129` | disposition 标记 `NEEDS_ADMIN` \| **当前状态（HOLD）** \| 发送 `HUMAN_OVERRIDE_REQUEST` |
| `docs/PRD_CHANGE_PROPOSAL_v2.5.md:218` | 超时停留在 **`CONSENSUS_CHECK`**（HOLD 态等待管理员介入） |

**该分支可达，不是假想**：提案 `:124` 规定 `REWORK_REQUIRED` 走 E5 进入 `REWORK`，且「Executor 写本轮 issue disposition 并修复代码」；清单 `:85` 第 3 项规定 E5 同时发送 `REWORK_REQUEST` **与 `DISPOSITION_REQUIRED`；UC-6 `:14` 明确「任务处于 `CONSENSUS_CHECK` … **或 `REWORK`**（收到 `REWORK_REQUEST`）」；UC-6 `:87` 失败态写「维持原状态（`CONSENSUS_CHECK` HOLD **或 `REWORK`**）」。即：**任务在 `REWORK` 中欠着一份 disposition，此时 disposition 超时**。

于是实现者拿到三个互斥的下一动作：

1. 按提案 `:128`「当前状态（HOLD）」→ 在 `REWORK` 挂 HOLD 并由此触发 E7 —— 被 PRD:888（HOLD 只属 `CONSENSUS_CHECK`）与 PRD:889（封闭条款）**明文禁止**；
2. 按提案 `:218`「停留在 `CONSENSUS_CHECK`」→ 任务已因 E5 离开该状态，**物理上停不回去**；
3. 按 PRD:881 E7 源态 → 需先从 `REWORK` 逆行回 `CONSENSUS_CHECK`，而转移表中**不存在该边**。

**与上轮的同构性**：`a0123e8` 时缺陷是「E7 源态四处只改两处」；本轮把那两处改对了，却没有同步扫描**同一提案内部**另外两行同样承载 HOLD 语义的表格行。收紧动作与其影响面的核对仍未成为一道门。

**修复与验收**：把提案 `:128` / `:129` 的「当前状态（HOLD）」明确为 `CONSENSUS_CHECK`（HOLD），并对「`REWORK` 中 disposition 超时」补一条显式规则（回到 `CONSENSUS_CHECK` 需要一条新的转移边并进 PRD §3.3 表，或声明该情形由 E6 超时而非 E7 处理）。验收：

```bash
grep -n '当前状态（HOLD）' docs/PRD_CHANGE_PROPOSAL_v2.5.md
# 现状：2 命中（:128 / :129）——修复后期望 0 命中
```

（不要用 `grep HOLD | grep -v CONSENSUS_CHECK` 作验收：本机实测该式命中 8 行合法文本 —— `PRD:79/340/856/863`、提案 `:135/187/451`、`INVENTORY:76` 中的 HOLD 均为正确用法。**只有出现在状态停驻语义上的 HOLD 才受该约束**，故验收必须用上面的精确串式。）

### A-P1-2　仓库自身的 `macao.yaml` 通不过本轮宣称已落地的 D-6 配置期校验（grok 首报，本人复验成立）

PRD §13 把仓库根 `macao.yaml` 定为配置的**单一事实源**。本轮申请 §1.1 把 `validate_config()` / `ConfigManager.load()` 的 D-6 语义校验列为核心修复并称「100% fail-closed 拦截」。两者相撞：

```
macao.yaml:16,21,26,31  ->  N = 4（opencode / cursor / antigravity / codex），vote_weight 全 1 -> W = 4
macao.yaml:41-42        ->  seat_quorum_required: 2   weight_quorum_required: 2
公式要求                 ->  ⌈2·4/3⌉ = 3
```

```bash
PYTHONPATH=src python3 -c "import yaml;from macao.core.schema import validate_config;print(validate_config(yaml.safe_load(open('macao.yaml'))))"
# (False, 'seat_quorum_required (2) is less than required minimum ceil(2N/3) = 3')
PYTHONPATH=src python3 -c "from macao.core.config import ConfigManager;ConfigManager().load('macao.yaml')"
# ValueError: Invalid macao.yaml schema: seat_quorum_required (2) is less than required minimum ceil(2N/3) = 3
```

该文件 **Draft-07 为 ACCEPTED**（我上一遍就是这样漏掉的），93/93 用的是 `DEFAULT_CONFIG_TEMPLATE` 与独立 fixture，**不加载仓库根文件**。按现状，用本仓库自己的配置启动 MACAO 会在配置期被拒。

**为何是 P1 而非 P2**：`macao_config.schema.json`（交付物 #2）与该文件构成「契约 × 唯一事实源」这一对，本轮定级正是要认证这一对成立；且这与 `4027cce`（收紧 4 份契约后 5 处 PRD 示例失效）、`a0123e8`（引入 `remote_name: null` 后判据未跟）**是同一缺陷类的第三次出现**：收紧一侧，未回扫另一侧。

**修复与验收**：根 `macao.yaml` 两个 quorum 改为 ≥ 3（或席位减到 3 与 PRD §13 示例同构）；并把根文件纳入回归：

```bash
PYTHONPATH=src python3 -c "import yaml;from macao.core.schema import validate_config;ok,e=validate_config(yaml.safe_load(open('macao.yaml')));assert ok,e;print('OK')"
```

### A-P1-3　`vote_result.json` 写出的 `policy_snapshot` 与 `issues_index_sha256` 是与实际算法无关的伪证

D-1 规定 `vote_result.json` 是编排器单写的**不可变机器计票**；PRD §2.3 的权威示例把 `policy_snapshot` 定义为「本次计票所依据的政策冻结快照」。运行时写出的却是常量与错源计数：

| 字段 | 运行时取值 | 应为 | 证据 |
|---|---|---|---|
| `rule` | 常量 `"weighted_2/3_v1"` | 实际生效规则 | `vote.py:178` |
| `dictator_cap_enabled` | **硬编码 `True`** | 来自 `macao.yaml` 的 `policy` | `vote.py:185` |
| `minimum_winning_seats` | **硬编码 `2`** | 来自 `macao.yaml` 的 `policy` | `vote.py:184` |
| `configured_weight` | `sum(v.get("weight",1) for v in votes_list)` = **已响应票数** | 配置总权重 W | `vote.py:164,179` |
| `weight_quorum_required` | `ceil(2 × 已响应票数 / 3)` | `ceil(2W/3)` | `vote.py:181` |
| `issues_index_sha256` | **恒为 64 个 `0`** | issues_index 的真实摘要 | `vote.py:211` |
| `votes[i].weight` / `.source` | **从不写入**（`votes_list.append` 只有 4 个键） | PRD §2.3 示例含二者 | `vote.py:105-110,132-137` |

三条可复跑的反例（`VoteAggregator.generate_vote_result(..., write_to_disk=False)`）：

```
① 3 席全部响应 -> configured_seats=3, configured_weight=3, issues_index_sha256=000...0
② 3 席仅 2 席响应 -> configured_seats=3, configured_weight=2
   —— 契约要求 vote_weight >= 1，故 W >= N 恒成立；configured_weight < configured_seats 在数学上不可能。
      产物内部自相矛盾，且 weight_quorum_required 由「谁到场」反推，成为自我实现的法定人数。
③ 加权反例 [YES w=2, NO w=1, NO w=1]：PRD 门禁④ 3·2=6 < 2·4=8 两侧均不达标 -> 应 DEADLOCK
   实测 ConsensusEngine.evaluate -> REWORK_REQUIRED
```

**定级理由**：`ConsensusEngine` 尚未实现加权本身，是清单 `:112` 公开登记的**计划项**（`tests/unit/test_consensus_weighted.py` 待建），我不把「未实现」当作 L1 阻断（此点我与 grok P2-5 一致，与 codex 把它列 P1-1 不同）。**我列为 P1 的是另一件事**：代码在算法缺席的情况下，仍向不可变审计产物写入 `rule: weighted_2/3_v1`、`dictator_cap_enabled: true` 和一份恒零摘要 —— **签发一份声称门禁已生效的凭证，比不签发更糟**，它使 D-1 的「不可变机器计票」在审计上失去意义，且 `issues_index_sha256` 恒零使该封条对任何篡改都不敏感。这是 §9 模式 B（「已完成」≠ 证据）的产物级形态。

**修复与验收**：在加权引擎落地前，`policy_snapshot` 的每一项必须从**已通过 `validate_config` 的配置对象**传入而非硬编码，`configured_weight` 取 Σ 配置权重，`issues_index_sha256` 取 `issues_index` 规范序列化后的真实 SHA-256；`votes[i]` 必须带 `weight` 与 `source`。验收：断言 `configured_weight >= configured_seats`、`issues_index_sha256 != "0"*64`、且改一条 issue 标题后摘要随之变化。

### A-P1-4　E4 无条件放行，带 issue 的 APPROVED 绕过 disposition 直接进入 `MERGING`（codex 首报，本人复验成立）

PRD `:875` 的 E4 守卫：`decision == APPROVED` 且「**无 issue，或存在 FINAL `executor.disposition.yml` 精确覆盖全部 issue 且所有 `requires_new_checkpoint=false`**」。提案 `:126` 与 UC-5 同句。

`src/macao/workflow/orchestrator.py:695-696`：

```python
if decision == Decision.APPROVED:
    change = self.fsm.transition(task_id, AgentState.MERGING, "E4", vdata)
```

无 `requires_disposition` 读取，无 disposition 存在性/覆盖度校验，无 `AEPType.DISPOSITION_REQUIRED` 发布 —— 而同一函数产出的 `vdata` **就带着** `requires_disposition` 字段（`vote.py:213`）。任何「加权判 APPROVED 但存在 ADVISORY / 少数 BLOCKING」的检查点都可跳过执行者逐项处置、跳过 `vote_result_ref` 反向绑定（本轮刚设为必填的那条契约）直接合并。本轮把 `vote_result_ref` 提升为强制，正是为了让 disposition 与计票互锁；而消费侧根本不走这条路，**该必填约束在运行时无人执行**。

**修复与验收**：E4 前置 `vdata["requires_disposition"]` 分支；为真时停在 `CONSENSUS_CHECK` 并发 Type E `DISPOSITION_REQUIRED`；仅在 FINAL disposition 精确覆盖且全部 `requires_new_checkpoint=false` 时进 `MERGING`，任一为 true 走 E5a。验收用例：APPROVED + 1 条 ADVISORY，断言状态为 `CONSENSUS_CHECK` 而非 `MERGING`。

### A-P1-5　`vote_result.schema.json` 对同一实体保留双名与遗留枚举，违反 GUIDELINES §5「唯一权威表」

§5 明文禁止「同一实体/同一决策结果出现不同名字」。契约库现状：

| 行 | 内容 | 问题 |
|---|---|---|
| `vote_result.schema.json:25-26` | `"timestamp"` 与 `"generated_at"` 并存 | 同一时间戳两个名字；PRD §2.3 示例用 `generated_at`，运行时写 `timestamp` |
| `:29-30` | `"executor"` 与 `"executor_id"` 并存 | 同一实体两个名字；PRD 示例用 `executor_id`，运行时写 `executor` |
| `:144` | `"resolution": {"enum": ["automatic", "AUTO_WEIGHTED_CONSENSUS"]}` | `"automatic"` 在**全部交付物文档中零出现**，仅存于未列入清单的 `docs/EXECUTIVE_SUMMARY.md:207` |
| `required`（`:6-22`） | 不含 `generated_at` / `task_id` / `executor_id` | PRD §2.3 权威示例的三个字段在契约里全部可选 |

后果是可机验的：运行时产物（`version: "1.0"`、`timestamp`、`executor`、`input_artifacts[].kind/message_id`）与 PRD §2.3 权威示例（`version: "2.0"`、`generated_at`、`executor_id`、`input_artifacts[].reviewer/evidence_commit`）**字段集互不相同，却双双通过同一份契约**。契约因此无法判别哪一个才是 v2.5 的 `vote_result.json`，交付物 #2 声称的「机器契约库」在这一份上不成立。同一目录下 `aep_envelope` 与 `review_context` 均已 `additionalProperties: false`，`vote_result` 未跟。

**修复与验收**：择一命名（建议随 PRD §2.3 取 `generated_at` / `executor_id` / `task_id` 并进 `required`），删除别名与 `"automatic"`，加 `additionalProperties: false`，同步 `vote.py` 输出与 `EXECUTIVE_SUMMARY.md`。验收：以 PRD §2.3 示例为正例 fixture，以运行时旧字段名为反例 fixture，二者判定相反。

---

## 四、轨 A：P2（登记，不阻断）

| ID | 问题 | 证据 |
|---|---|---|
| **A-P2-1** | 申请 §3.3 把 20/20 反例拦截写在「**Draft-07 Schema 与 Fixtures 双向校验**」标题下，但 3 份 `macao_config_*`（`dictator_weight_violation` / `low_seat_quorum` / `low_weight_quorum`）单跑 Draft-07 **ACCEPTED**，第 4 份 `aep_payload_oversized.json` 由 `validate_budget()` 拒绝。`schemas/README.md` 末行的「跨项业务规则由运行时保证」在**方向上**是对的，但目录内未标注哪些反例走语义层。外部消费方按发布的契约库单跑 Draft-07 会静默接受违反独裁帽的配置 | `docs/schemas/fixtures/invalid/`；`tests/test_schema.py:355-365` 的混合校验器 |
| **A-P2-2** | `aep_envelope.schema.json` 的 `protocol` 枚举仍含 `"AEP/1.0"`；交付物全文声称 AEP/1.1 8 类 | 同 grok P2-2 |
| **A-P2-3** | `review_disposition.schema.json` 根对象未 `additionalProperties: false`：向合法 disposition 加 `unrecognized_control_field` 仍 `(True, None)`。提案 `:498-505` 把「收紧为封闭对象」列为实施第 2 步 | 同 codex P2-1，本人复跑确认 |
| **A-P2-4** | `generate_vote_result(human_resolution=...)` 分支 **100% 不可用**：`APPROVED`/`REWORK`/`RETRY_REVIEW`/`CANCEL` 四个 choice 全部抛 `ValueError`（前两个因 `resolution: human_override` 不在枚举，后两个因 `decision` 不在三值枚举）。副作用上它保住了 D-1 不可变，但作为 API 参数它是陷阱；E7 落地时须改为写 `admin_override.json` | 四次实测均 RAISED |
| **A-P2-5** | `ConsensusEngine` 按人数与浮点比例（`engine.py:58,63`，含 `1e-6` 容差）计票，与 D-6「纯整数」相斥；清单 `:112` 已登记为计划项。**不作为本轨 L1 阻断**，但禁止把 93/93 表述为 L2 | 与 grok P2-5 同级，与 codex P1-1 定级不同 |
| **A-P2-6** | `vote.py:173-174` `reviewers_responded` 与 `reviewers_accounted` 同为 `len(votes_list)`（含超时合成票），与提案 `:107-114` 的定义相反；`source` 亦未写入 | 同 codex P1-3 的一部分；我按 L1 定为 P2 |
| **A-P2-7** | 清单 `:94` Pre-merge 仍只写远端 `ls-remote`，未复述 §14.5 的纯本地分支 | 同 grok P2-4 |

## 五、轨 A：P3（可延期）

| ID | 问题 |
|---|---|
| **A-P3-1** | `docs/PRD_CHANGE_PROPOSAL_v2.5.md:514` 使用 `file:///home/debian/macao/docs/MACAO_PRD_v2.md` 绝对本机路径链接：对任何其他读者失效，且把作者机器路径写进了交付物。65 条相对链接中唯一一条断链。改为 `MACAO_PRD_v2.md` 即可 |
| **A-P3-2** | `STATUS.md` 头部第 6 行已更正为 130/32（与 `git ls-files` 完全吻合），但登记表标题 `:176`、对账说明 `:181`、治理条目 `:263` 仍写 **128/29**。文件内部三处自相矛盾。双向对账实质为 **0/0/0**（我复跑确认），仅计数字符串滞后 |
| **A-P3-3** | 申请称 206 份 Markdown，本机 glob 得 211（`git ls-files` 口径另计）。份数不可复算 |
| **A-P3-4** | `git diff --check cd285dd^ cd285dd` → `src/macao/core/schema.py:166: new blank line at EOF.`；建议把 `git diff --check` 纳入申请 §3 的自动化清单 |

---

## 六、GUIDELINES §6 反例库

不加权前提下 6 条可机验场景全部唯一可推导，无回退：

| 场景 | 实测 | 期望 |
|---|---|---|
| 全部弃权（N=3） | DEADLOCK | DEADLOCK ✓ |
| 1 超时(ABSTAIN) + 2 批准 | APPROVED | APPROVED ✓ |
| 1 超时 + 1 批准 + 1 缺席 | DEADLOCK | DEADLOCK（席位法定人数）✓ |
| 1:1 僵局 | DEADLOCK | DEADLOCK ✓ |
| 1:1:1 | DEADLOCK | DEADLOCK ✓ |
| 2:1 | APPROVED | APPROVED ✓ |

**加权场景不可推导**：`[YES w=2, NO w=1, NO w=1]` 实测 REWORK_REQUIRED，PRD 门禁④ 判 DEADLOCK（见 A-P1-3）。
**「接管超时默认动作」场景本轮由唯一可推导退化为三义**（见 A-P1-1）。
其余场景（同 reviewer 两份票、`signal=EXPLICIT` 缺字段、第二轮覆盖、Git 冲突、`review_context` 载体一致性）在 `a0123e8` 轮已核为可唯一推导，本轮相关文本未变，**结论沿用，未重新独立取证**（按 §3.2 记为 PARTIALLY_VERIFIED，不写成 VERIFIED）。

---

## 七、轨 B：用例体系（`YES_APPROVE`）

### 7.1 授予依据

1. 申请点名的唯一修复 **UC-6 `vote_result_ref`** 已落地：`docs/usercases/UC6-issue-triage-rework.md:44-48` 写入 `path` / `evidence_commit` / `sha256` 三元组；抽出该 YAML 块跑 `validate_review_disposition` → **PASS**；与 PRD §2.5 示例、`review_disposition.schema.json` 新的 `required` 集、`fixtures/valid/disposition.yml` 四处同构。
2. 13 份用例文档 **0 控制字符**；正文内嵌 YAML/JSON 经形状探测后逐块过对应契约，**0 失败**。
3. `UC1-init-gemini.md:126` 的 `macao.yaml` 规格示例 **既过 Draft-07 也过 `validate_config` 语义层**（N=3，权重全 1，quorum 2/2 = ⌈2·3/3⌉）—— 这正是根 `macao.yaml` 未能通过的那一关，用例侧写对了。
4. UC-7 与 PRD §3.3 E7 同句（源态 `HOLD (CONSENSUS_CHECK)`、`APPROVED` 两步流）；UC-8 六道关卡与 §14.5 同句且双轨（远端 `ls-remote` / 纯本地）齐备；UC-9 超时席位计入 `accounted` 但排除于 $E_N,E_W$ 与 PRD 同句。
5. 轨 A 的 5 条 P1 **无一落在 `docs/usercases/` 正文内**：A-P1-1 在提案，A-P1-2 在根配置，A-P1-3/A-P1-4 在 `src/`，A-P1-5 在契约库。

按 F-17，「有条件通过」在机器语义上等于阻断性不通过，故我**不把轨 A 的闭环设为本票条件**；下方跨轨依赖仅作登记。

### 7.2 轨 B：P2（登记，不构成条件）

| ID | 问题 | 证据 |
|---|---|---|
| **B-P2-1** | `UC5-consensus-tally.md:29` 保留浮点句「赞成加权占比 = Σ(approve 权重) / 有效权重」，紧接其后即为「加权五重门禁（**纯整数**）」。决策表只挂靠五重门禁，故**不构成决策规则冲突**（门禁④ `3W_win ≥ 2E_W` 正是该比值的整数形式），但与 D-6 的引入动机相斥，建议删除或标注为「仅供展示，不参与判定」。同节 `:104` 遗留决策点①亦建议 `decision_confidence` = 赞成加权占比 | 同 grok P2-3 |
| **B-P2-2** | `docs/usercases/README.md:9`「正文已与 PRD v2.5 全面实装对账，并通过自动化测试验证」。「实装对账」可读作「对照实装做了核对」，也可读作「实装已完成」；后一读法与 A-P1-3/A-P1-4 相斥。属 §9 模式 C（确定性语言未标注目标状态），建议改为「已与 PRD v2.5 文本对账；运行时实装状态见各 UC 的『待实现』标注」 | 同 grok P2-4 / codex 跨文档修订②，我按 L1 定为 P2 而非 P1：原句语义确有歧义，不宜按最坏读法定阻断 |
| **B-P2-3** | `UC8-merge-signoff.md:78` 验收标准第 2 条仍只写远端 `ls-remote` fail-closed，六条断言未覆盖纯本地分支（正文 `:32` 已覆盖，验收未跟） | 同 grok P2-1 |
| **B-P2-4** | D-9 的 `reconcile` 在 `docs/usercases/` 零命中 | 同 grok P2-2 |

### 7.3 跨轨依赖（登记，非条件）

UC-5 `:24-34`、UC-1、UC-10 均正确复述了 D-6 五重纯整数公式与静态 `vote_weight` 读取；实现侧 `ConsensusEngine` 尚未读取权重（A-P2-5），且带 issue 的 APPROVED 会绕过 UC-6 的整条处置流程（A-P1-4）。**用例文档写对了，实现未跟。** 这不影响本轨 L1（文档一致性）判定，但在轨 A 闭环前，这些用例的运行时可执行性未获证。

---

## 八、与其他 Reviewer 的交叉核对（GUIDELINES §8）

| 同行 | 其结论 | 我的复验 |
|---|---|---|
| **grok** DesignSync `NO_APPROVE` P1-1（根 `macao.yaml`） | 成立 | **独立复跑确认**，并推翻我自己「根配置过契约」的判断（§0.1）。已采为 A-P1-2 |
| **grok** UseCases `YES_APPROVE` P1×0 | 成立 | 我的轨 B 结论与其**独立一致**；P2 项目录基本重合 |
| **grok** P2-1（3 份反例仅语义层拒绝） | 成立 | 我独立跑出同一名单（`dictator_weight_violation`/`low_seat_quorum`/`low_weight_quorum`）。已采为 A-P2-1 |
| **grok** P2-2（`protocol` 含 `AEP/1.0`） | 成立 | 复验确认，采为 A-P2-2 |
| **codex** `REJECT` P1-2（E4 绕过 disposition） | 成立 | `orchestrator.py:695-696` 复读确认。已采为 A-P1-4 |
| **codex** P1-1（加权引擎未接入） | 事实成立，**定级我取 P2** | 反例 `[YES w2, NO w1, NO w1] → REWORK_REQUIRED` 我独立复现，与其一致。但清单 `:112` 已公开登记为计划项，「未实现」不构成 L1 文档一致性阻断；我把 P1 落在**产物伪证**（A-P1-3）这一相邻但不同的事实上 |
| **codex** P1-3（超时票 `source` 不可审计） | 成立，**定级我取 P2**（A-P2-6） | 同上理由：契约允许 `source` 可选是 SPEC 缺口，但不产生文档间矛盾 |
| **codex** P2-1（disposition 根未封闭）、P2-2（EOF 空行） | 均成立 | 两条我都本机复跑确认，采为 A-P2-3 / A-P3-4 |
| **qwen** DesignSync `NO_APPROVE` P1-1（根 `macao.yaml`） | 成立 | 与 grok、与我复验同源。qwen 另做了我没做的**对称探针**：合法 `[2,1,1]` + quorum=3 被**接受**，证明新校验无过度拦截 —— 该方向我未测，采信 |
| **qwen** UseCases `YES_APPROVE` P1×0 | 成立 | 轨 B 三方（claude / grok / qwen）**独立一致授予**，连续第二轮 |
| **qwen** 对 codex 代码层三项取「L1/L2 分层，不阻断 L1」立场 | **与我的定级有实质分歧**，见下 | — |

### 关于「代码层缺陷可否阻断 L1」的分歧登记

qwen 明确主张 codex 的三项代码层差距属 L2 实施域，不阻断 L1 文档定级；我把其中两项（A-P1-3、A-P1-4）判为 P1。两点理由：(1) 申请 §1.1/§3 **主动把代码闭环列为本次定级依据**，一旦提交为证据即进入本轮取证范围；(2) A-P1-3 的落点不是「算法未实现」（这点我同意 qwen 与 grok，已降为 A-P2-5），而是**已实现并已写盘的审计产物内容为伪**，这与 D-1「不可变机器计票」这一架构裁定直接冲突，属 §5/§9 模式 B 而非实施进度。

**但我的票不依赖这一分歧**：即便完全采纳 qwen 的严格分层口径、把 A-P1-3 / A-P1-4 降为 P2，轨 A 仍余 **A-P1-1（纯文档矛盾）、A-P1-2（配置事实源）、A-P1-5（契约违反 §5）** 三条 L1 域内的 BLOCKING，结论不变。请委员会按各自口径取用。

**三方均未报、由我本轮新提出的**：A-P1-1（提案 §4.2 HOLD 三义）、A-P1-3（`policy_snapshot` / `issues_index_sha256` 伪证）、A-P1-5（契约双名违反 §5）、A-P3-1（`file://` 绝对路径）、A-P3-2（STATUS 内部三处计数矛盾）。

**票型汇总（截至本文写作时盘面）**：

| 轨 | claude | grok | qwen | codex | 汇总 |
|---|---|---|---|---|---|
| A 设计同步 | `NO_APPROVE` | `NO_APPROVE` | `NO_APPROVE` | `REJECT` | **四方一致否决**；四方共同点名的唯一同一条缺陷是根 `macao.yaml`（我的 A-P1-2） |
| B 用例体系 | `YES_APPROVE` | `YES_APPROVE` | `YES_APPROVE` | （证据全部指向轨 A 交付物） | **三方一致授予，连续第二轮** |

按 §8「沉默 ≠ 同意」，未表态的 reviewer 不计入多数，**轨 B 的 PG-0 仍需委员会正式签署后方为授予**；本报告不代行该判定。

### 复发模式登记（第 8 轮）

「**修复即引入同类缺陷**」在 `a0123e8` 中断一轮后**本轮复发**：本轮 E7 源态修复（改对提案 `:230`、清单 `:85`、`:218`）未回扫同一提案内 `:128`/`:129` 两行同样承载 HOLD 语义的表格行 → A-P1-1。同时 A-P1-2 是「收紧一侧未回扫另一侧」的第三次出现（`4027cce` 契约 vs PRD 示例；`a0123e8` `remote_name: null` vs 用例判据；本轮 `validate_config` vs 根配置）。

我已**连续 6 轮**建议把三道门固化成脚本。本轮申请方已固化第一道（`tests/test_prd_snippets_schema.py`），另两道仍缺：

```bash
# 门 2（可拦 A-P1-2）：仓库根 macao.yaml 必须过语义层
PYTHONPATH=src python3 -c "import yaml,sys;from macao.core.schema import validate_config;ok,e=validate_config(yaml.safe_load(open('macao.yaml')));sys.exit(0 if ok else print(e) or 1)"

# 门 3（可拦 A-P1-1）：任何"停驻状态"字段不得写成 HOLD 而不指明宿主状态
! grep -rnE '当前状态（HOLD）|HOLD`（`CONSENSUS_CHECK` 或 `REWORK`）' docs/ --include=*.md \
    | grep -v docs/reviews/
```

---

## 九、建议闭环顺序与验收标准

**轨 A（阻断，按成本升序）**

1. **A-P1-1**（改 2 行）：提案 `:128`/`:129`「当前状态（HOLD）」→ `CONSENSUS_CHECK`（HOLD），并补「`REWORK` 中 disposition 超时」的显式规则。验收 = `grep -n '当前状态（HOLD）' docs/PRD_CHANGE_PROPOSAL_v2.5.md` 由 2 命中降为 0。
2. **A-P1-2**（改 2 行）：根 `macao.yaml:41-42` → ≥ 3；加根文件回归。验收 = 上文门 2 退出码 0。
3. **A-P1-5**（改契约 + 输出）：择一命名、删 `"automatic"`、加 `additionalProperties: false`，PRD §2.3 示例进正例 fixture。
4. **A-P1-3**：`policy_snapshot` 全项从已校验配置传入；`issues_index_sha256` 取真实摘要；`votes[i]` 带 `weight`/`source`。验收 = `configured_weight >= configured_seats` 且改标题后摘要变化。
5. **A-P1-4**：E4 前置 `requires_disposition` 分支 + Type E 发布 + E4/E5a 分流。验收 = 「APPROVED + 1 条 ADVISORY」停在 `CONSENSUS_CHECK`。
6. 固化门 2 / 门 3（连续第 6 轮登记）。

**P2 批次（不阻断）**：A-P2-1（反例目录标注语义层）、A-P2-3（disposition 封闭）、A-P2-2、A-P2-6、A-P2-7；B-P2-1～B-P2-4。

**表述修订**：在两份申请与 `docs/usercases/README.md:9` 中，把「已完成代码与文档级物理闭环」「全面实装对账」改为按 §3.2 标注状态的表述，或在 A-P1-2～A-P1-4 闭合后恢复。

**下一次申请**：建议在闭合 A-P1-1 与 A-P1-2（合计 4 行）后立即复审轨 A —— 这两条是唯一「文档/配置层」的阻断；A-P1-3～A-P1-5 若一并解决则可同时叩关 L2。

---

## 附：机器票与结构化 issue 索引

### 轨 A —— `vote: NO_APPROVE`

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/A-P1-1` | major | `BLOCKING` | 提案 `:128`/`:129`「当前状态（HOLD）」与 PRD `:888` HOLD 定义、`:889` 封闭条款、统一后的 E7 源态互斥，`REWORK` 中 disposition 超时有三个互斥下一动作 |
| `claude/A-P1-2` | major | `BLOCKING` | 仓库根 `macao.yaml:41-42`（N=4，quorum 2）被本轮落地的 `validate_config`/`ConfigManager.load` 拒绝（需 ≥ 3） |
| `claude/A-P1-3` | major | `BLOCKING` | `vote.py:164,179,181,184,185,211` 向不可变审计产物写入硬编码/错源的 `policy_snapshot` 与恒零 `issues_index_sha256`；`configured_weight < configured_seats` 可复现 |
| `claude/A-P1-4` | major | `BLOCKING` | `orchestrator.py:695-696` E4 无条件转 `MERGING`，带 issue 的 APPROVED 绕过 disposition 与刚设为必填的 `vote_result_ref` 互锁 |
| `claude/A-P1-5` | major | `BLOCKING` | `vote_result.schema.json:25-30,144` 同一实体双名 + 遗留 `"automatic"` 枚举，违反 GUIDELINES §5；PRD 示例与运行时产物字段集互异却双双过契约 |

### 轨 B —— `vote: YES_APPROVE`

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| （无 P1） | — | — | 13 份用例正文无机器可证的不一致；P2×4 见 §7.2，按 F-17 不作为票的条件 |
