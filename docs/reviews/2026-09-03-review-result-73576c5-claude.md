# MACAO `73576c5` 双轨独立评审结论（轨 A 设计同步 / 轨 B 用例体系）

- **评审日期**：2026-09-03
- **评审人**：claude（独立评审）
- **评审对象**：
  - [`2026-09-03-review-request-73576c5-PRD-v2.5-Design-Sync.md`](2026-09-03-review-request-73576c5-PRD-v2.5-Design-Sync.md)（轨 A）
  - [`2026-09-03-review-request-73576c5-UseCases-v2.5-Alignment.md`](2026-09-03-review-request-73576c5-UseCases-v2.5-Alignment.md)（轨 B）
- **受审基线**：`73576c5`；**工作区 HEAD**：`34a1077`（差量 = 三份申请 + `STATUS.md` + 5 份未跟踪同行报告，正文与 `73576c5` 一致）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§8、§9、§11；`docs/MACAO_PRD_v2.md`（权威基准）；提案 §2 D-1～D-9；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22

| 轨 | 目标定级 | 机器票 | BLOCKING | ADVISORY |
|---|---|---|---|---|
| 轨 A · PRD v2.5 设计同步 | L1 DOC-ALIGNED / PG-0 | **`NO_APPROVE`** | P1 × 3 | P2 × 6、P3 × 3 |
| 轨 B · 全量用例体系 | L1 DOC-ALIGNED / PG-0 | **`NO_APPROVE`** | P1 × 1 | P2 × 2、P3 × 1 |

**结论：两轨均不授予 L1 DOC-ALIGNED / PG-0。**

本轮相对 `cd285dd` 的进展是实质的：我上轮的 5 项 P1 中有 3 项（A-P1-1 提案「当前状态（HOLD）」、A-P1-2 根 `macao.yaml` quorum、A-P1-5 `resolution` 遗留枚举）已真实闭环，纯整数五道门禁在**引擎单元层**完全正确（我用 11 组反例逐格复算，含 codex 反例与胜方最少席位边界，全部与 PRD §2.3 一致）。

不授予的原因有两类，都由本轮自身的改动引入或暴露：

1. **本轮把 `review_disposition.schema.json` 收成 `additionalProperties: false`，却没有回扫用同一契约的权威示例。** 提案 §4.3（`:159`）与 UC-6（`:36`）的处置信封仍写 `generated_at`，该键在契约中不存在 —— 两处示例现在都被拒。轨 B 申请 §3.2 明写「UC6 … **PASS**」，本机为 **FAIL**。这是 L1 最低条件（「所有 YAML/JSON 示例是合法可解析格式」）的直接违反。
2. **`Orchestrator.__init__` 的配置归一化把 `team` 与 `policy` 整段丢弃**，导致 `macao.yaml` 的 `vote_weight` 与全部 policy 参数在运行时**永不生效**：本轮头条修复①（根配置 quorum）与④（加权五门禁）在集成层不可达，且 D-1 不可变机器记录 `policy_snapshot` 写入的是派生默认值而非配置值（实测配置权重 4 被记为 3）。同时本轮新增的 `submit_disposition()` E4 守卫可被 `dispositions: []` + 伪造 ref 从 `DEADLOCK` 直推 `MERGING`。

第 1 类是纯 L1 阻断，与任何 L1/L2 分层立场无关。第 2 类的定级理由见 §3.0。

同轨同行报告：grok（两轨 `NO_APPROVE`，P1 与本人第 1 类同源、独立同结论）、codex（合并 `REJECT`，P1×4，与本人第 2 类两处独立收敛）、muse（两轨 `YES_APPROVE`）。交叉核对与分歧登记见 §7。

---

## 0. Reviewer 自审

### 0.1 撤回（本轮我自己出的错）

**撤回一项**：初次全库抽检时，我把 `docs/MACAO_PRD_v2.md:1003`（§5.2 `review_context` 权威模型）判为 FAIL（`'repository' is a required property`）。原因是该围栏以 `review_context:` 为**外层包裹键**，我的分流器把包裹对象直接送去校验，而契约描述的是**内层**对象。解包后：

```
PRD §5.2 review_context (unwrapped): PASS
```

**该 FAIL 不成立，已在写入本报告前撤回，未计入任何 issue。** 这是 GUIDELINES §9 模式 A（声明位置 vs 实际读取位置不一致）在我自己身上的复现 —— 与我上一轮误把结构校验当语义校验（`validate_config` 漏跑）属同一族：**校验器跑了，但跑在了错误的对象上**。本轮我对每一条 FAIL 都做了「换一种取值路径复算」再入册。

### 0.2 对同行结论的修正（向上，不是照抄）

grok 轨 A P2-5 写：「`orchestrator.py:597-600` 第一次 `evaluate()` 不传 `weight`/`policy`；**DEADLOCK 分支随后 `generate_vote_result` 亦不传 `reviewer_weights`**」。前半段成立；但其表述隐含「非 DEADLOCK 分支的 `:685` 是接线好的」。

实测**不成立**：`:685` 确实写了 `reviewer_weights=reviewer_weights, policy=policy_cfg`，但这两个变量在 `:677-682` 恒为空 —— 因为 `self.config` 里根本没有 `team` 和 `policy` 键（`__init__` `:122-134` 只保留 11 个扁平标量 + `reviewers`）。故**加权与 policy 在两条分支上都从未生效**，而非只在 DEADLOCK 分支缺失。据此我将其从 P2 升为 A-P1-2，并补上 `policy_snapshot` 伪证这一维（§3.2）。

### 0.3 已复跑为真的项（不只报负例）

| 申请声明 | 本机结果 | 判定 |
|---|---|---|
| 根 `macao.yaml` 语义校验 | `validate_config` → `(True, None)`；`ConfigManager().load('macao.yaml')` → OK；`:41-42` 均为 3（$N=4 \Rightarrow \lceil 8/3\rceil=3$）；`test_config` 10/10 | **VERIFIED**（我上轮 A-P1-2 真闭环） |
| 提案「当前状态（HOLD）」清理 | `grep '当前状态（HOLD）' docs/ --include=*.md`（排除 `reviews/`）**0 命中**；`:126-129` 统一为 `` `CONSENSUS_CHECK`（HOLD） `` | **VERIFIED**（我上轮 A-P1-1 真闭环） |
| 绝对路径链接 | `grep 'file:///' docs/`（排除 `reviews/`）**0 命中**；全库相对链接 **64 条 0 断链** | **VERIFIED**（我上轮 A-P3-1 真闭环） |
| `resolution` 枚举收敛 | 仅 `["AUTO_WEIGHTED_CONSENSUS","HUMAN_OVERRIDE"]`；遗留 `"automatic"` 全库 0 命中 | **VERIFIED**（我上轮 A-P1-5 之枚举维闭环，别名维未闭见 A-P2-4） |
| `votes[].source` 与真实 `issues_index_sha256` | `source` 必填且枚举封闭；`vote_result_missing_source.json` 拒因精确；哈希为 canonical JSON 的真实 SHA-256（非 64 个 0） | **VERIFIED**（我上轮 A-P1-3 之两维闭环） |
| `review_disposition` 全量封闭 | 根 / `executor` / `full_document` / `dispositions.items` 四处均 `additionalProperties: false`；`disposition_unrecognized_property.yml` 拒因精确 | **VERIFIED**（契约本身；示例未跟见 A-P1-1） |
| 双 Schema 目录 0 diff | 8 份契约 **8/8 逐字节相同**；32 份 fixtures **32/32 逐字节相同**，0 缺失 | **VERIFIED** |
| 97/97 与 compileall | `Ran 97 tests … OK`；`compileall` rc=0 | **VERIFIED** |
| 用例正文稳定 | `git diff cd285dd..73576c5 -- docs/usercases` **空** | **VERIFIED** |
| 控制字符 | `docs/usercases/*.md` 13/13 共 0 字节；全库 md 0 字节 | **VERIFIED**（份数见 A-P3-2） |
| UC-3 `.dev.yml` / UC-1-gemini `macao.yaml` 示例 | `validate_dev_manifest` → `(True, None)`；`validate_config` → `(True, None)`（含语义层） | **VERIFIED** |
| PRD §2.5 处置示例 | 用 `timestamp`，过契约 | **VERIFIED**（错的只有提案与 UC-6，PRD 本身是对的） |

### 0.4 强制自检五项

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 实际读取路径 | 契约读 `timestamp`；提案 `:159` / UC-6 `:36` 写 `generated_at` → **CONTRADICTED**（A-P1-1 / B-P1-1）。`macao.yaml` 写 `policy`/`vote_weight`；`Orchestrator` 读 `self.config['policy']`（恒 `None`）→ **CONTRADICTED**（A-P1-2） |
| 2 | 「已完成 / 100%」 | 轨 A §1.1/§1.2/§1.3(契约)/§1.5(枚举与哈希) **VERIFIED**；§1.4「五门禁实装」在**引擎层** VERIFIED、**集成层** CONTRADICTED；§1.6「E4 守卫」**PARTIALLY_VERIFIED**（一条路径设了守卫，另三条未设）；轨 B §3.2「UC6 PASS」**CONTRADICTED** |
| 3 | 确定性语言未标目标 | 申请「全部阻断项均已完成代码、契约与文档级的物理闭环」未标目标层级；本报告全部 P1 均附文件:行号与可复跑命令 |
| 4 | YAML/JSON 过 Schema | PRD 六节 + 8 类 AEP 信封 **全 PASS**；提案 §4.3 **FAIL**；UC-6 **FAIL** |
| 5 | 代码块可执行 | 本报告 §8 三条验收命令均已在本机实跑通过后才写入 |

### 0.5 复发模式登记

- **「修复即引入同类缺陷」连续第 2 轮复发**：`cd285dd` 轮 E7 收敛改对三处漏 `:128/:129`；本轮封闭 `review_disposition` 契约漏回扫提案 `:159` 与 UC-6 `:36`。
- **「收紧一侧不回扫另一侧」第 4 例**：`4027cce` 契约 vs PRD 示例 → `a0123e8` `remote_name: null` vs 用例验收 → `cd285dd` `validate_config` vs 根配置 → 本轮 `additionalProperties: false` vs 处置示例。
- **门禁扩面建议连续第 6 轮未采纳**：`tests/test_prd_snippets_schema.py` 已固化（第 1 条建议兑现），但只读 `docs/MACAO_PRD_v2.md` 的六个命名小节，不覆盖提案与用例围栏 —— 本轮两条 P1 恰好落在该缺口内（A-P2-6）。

---

## 1. 申请 §3 机验独立复跑（轨 A）

| # | 声明 | 本机 | 判定 |
|---|---|---|---|
| 1 | PRD 全量代码块 100% PASS | `tests.test_prd_snippets_schema` 2/2 OK；我自建分流器抽全库 16 块可判定围栏，14 PASS + 2 FAIL（FAIL 均在**提案**，不在 PRD） | **VERIFIED**（限 PRD 文件；见 A-P2-6） |
| 2 | 根配置语义与 Schema 10/10 | 10/10 OK | **VERIFIED** |
| 3 | 加权五门禁与反例 5/5 | 5/5 OK；我另跑 11 组独立反例全部与 PRD §2.3 一致 | **VERIFIED**（引擎层；集成层见 A-P1-2） |
| 4 | 212 份 Markdown 0 控制字符 | 控制字节 **0**；份数 `git ls-files '*.md'` = **205**，工作区 = **209** | 结论 **VERIFIED**；份数 **PARTIALLY_VERIFIED**（A-P3-2） |
| 5 | 正例 10/10、反例 22/22、双副本 0 diff | 正例 10/10；反例 22/22 在**项目校验器**下全部拒绝，其中 3 份 `macao_config_*` 在 **Draft-07 单独下 ACCEPT** | **PARTIALLY_VERIFIED**（A-P3-3） |
| 6 | 97 tests 100% OK | `Ran 97 tests … OK` | **VERIFIED** |
| 7 | compileall 0 Errors | rc=0 | **VERIFIED** |

**97/97 不构成 L2 证据**：集成层的加权接线、E4 守卫完整性、E7 两步式均无测试覆盖 —— 本报告 §3 的三条 P1 全部在 97 个绿测之外可复现。

---

## 2. 我在 `cd285dd` 轮 5 项 P1 的闭环核验

| 上轮 ID | 判定 | 证据 |
|---|---|---|
| A-P1-1 提案 `:128/:129`「当前状态（HOLD）」 | **CLOSED** | 0 命中；`:126-129` 四行统一 `` `CONSENSUS_CHECK`（HOLD） ``；与 PRD `:888/:889` 同句 |
| A-P1-2 根 `macao.yaml` 被自身校验拒绝 | **CLOSED** | `validate_config`/`ConfigManager.load` 均 PASS；`test_root_macao_yaml_passes_semantic_validation` 入库 |
| A-P1-3 `policy_snapshot` / `issues_index_sha256` 伪证 | **PARTIALLY CLOSED** | `weight`/`source` 已写入投票项；哈希已真实计算 → 闭。**但 `policy_snapshot` 的伪证维未闭且已定位到根因**：见 A-P1-2 |
| A-P1-4 E4 直跳 `MERGING` | **PARTIALLY CLOSED** | `collect_and_evaluate_consensus` 路径已设守卫并发布 Type E → 闭。**另三条通往 `MERGING` 的路径未设守卫**：见 A-P1-3、A-P2-1、A-P2-2 |
| A-P1-5 `vote_result` 双别名 + 遗留枚举 | **PARTIALLY CLOSED** | `"automatic"` 已删、`generated_at`/`task_id`/`executor_id` 已必填 → 闭。**双别名仍在且仍被同时写出**：见 A-P2-4（且此项即 A-P1-1/B-P1-1 的成因） |

`4027cce`/`a0123e8` 已闭项（单键 D-6 下界、`remote_name: null`、E7 源态三处）**未回退**。

---

## 3. 轨 A · P1

### 3.0 定级理由（先说清楚，避免与分层立场之争纠缠）

A-P1-1 是**纯文档—契约不一致**，落在 L1 定义（「设计文档之间、与权威基准之间一致；所有 YAML/JSON 示例是合法可解析格式」）正中，任何分层立场下都是本轨阻断。

A-P1-2 与 A-P1-3 我定 P1，理由是**申请自身把这两项作为本轮闭环证据提交**（§1.1、§1.4、§1.5、§1.6 与 §3 全部以代码与测试为凭），而两项都**证伪了申请写下的闭环陈述**，且都以 PRD/清单的权威条款为对照基准 —— 这不是「算法尚未实现」，而是「已写下的完成度陈述与机器事实相反」（§9 模式 B）。

grok 在同轮把相邻问题列为 P2，理由是「L1 看文档」。该立场我尊重并登记。**我的票不依赖这一分歧**：仅 A-P1-1 一项即足以使本轨 `NO_APPROVE`。

### 3.1 A-P1-1　提案 §4.3 处置信封示例被本轮刚封闭的 `review_disposition` 契约拒绝

> 与 grok 轨 A P1-1 独立同结论。muse 未抽出该围栏。

申请 §1.3 把「为根对象、`executor`、`full_document`、`dispositions.items` 全量追加 `additionalProperties: false`」列为本轮核心修复之一；申请 §2 表格第 3 项交付物即 `docs/PRD_CHANGE_PROPOSAL_v2.5.md`。

**证据：**

1. `docs/schemas/review_disposition.schema.json:20` 声明的时间字段名是 `timestamp`；`properties` 中**无** `generated_at`；根对象 `additionalProperties: false`。
2. `docs/PRD_CHANGE_PROPOSAL_v2.5.md:159`：`generated_at: "2026-09-01T12:10:00Z"`。
3. 抽出该围栏送校验：

```
docs/PRD_CHANGE_PROPOSAL_v2.5.md:149 -> review_disposition
  FAIL: Additional properties are not allowed ('generated_at' was unexpected)
```

4. **权威对照**：`docs/MACAO_PRD_v2.md` §2.5 的同类示例用 `timestamp` 且 PASS；正例 fixture `docs/schemas/fixtures/valid/disposition.yml` 亦用 `timestamp`（10/10 之一）。删除或改名后同一对象 PASS。
5. `tests/test_prd_snippets_schema.py` 只读 `docs/MACAO_PRD_v2.md`，不解析提案围栏 —— 97/97 全绿不能覆盖此处。

**影响**：实现者若按提案 §4.3 照抄产出 `executor.disposition.yml`，将被本轮宣称已落地的 fail-closed 契约拒绝，直接卡死 E4/E5a。

**验收**：提案 §4.3 示例的时间键与契约 `properties` 同名（建议 `timestamp`，与 PRD §2.5 及正例 fixture 一致）；或把 `generated_at` 写进契约并同步改掉 PRD 与 fixture（**禁止双名并存**，见 A-P2-4）。抽出后 `validate_review_disposition(...) == (True, None)`。

### 3.2 A-P1-2　`Orchestrator` 归一化丢弃 `team`/`policy`：`vote_weight` 与全部 policy 参数在运行时永不生效，`policy_snapshot` 因此写入伪证

> 本人独立发现。grok 轨 A P2-5 触及第一条分支，但未定位根因，且其表述隐含 `:685` 已接线（见 §0.2）。

**根因**：`src/macao/workflow/orchestrator.py:122-134` 把 `raw_config` 归一化为一个只含 11 个扁平标量 + `reviewers` 的新字典，**`team` 与 `policy` 两个整段被丢弃**。而 `:677-682` 恰恰按 `team`/`policy` 取值：

```python
reviewer_weights = {}
for r_cfg in self.config.get("team", {}).get("reviewers", []):   # 恒为 []
    reviewer_weights[r_cfg["id"]] = r_cfg.get("vote_weight", 1)
policy_cfg = self.config.get("policy", {})                       # 恒为 {}
```

**用仓库真实的根 `macao.yaml` 实测：**

```
macao.yaml policy: {'consensus_rule': 'weighted_2/3_v1', 'dictator_cap_enabled': True,
                    'minimum_winning_seats': 2, 'seat_quorum_required': 3, 'weight_quorum_required': 3, ...}
macao.yaml weights: {'opencode': 1, 'cursor': 1, 'antigravity': 1, 'codex': 1}
--- after Orchestrator normalization ---
self.config.get('team')   -> None
self.config.get('policy') -> None
reviewer_weights (orchestrator.py:677-681) -> {}
policy_cfg       (orchestrator.py:682)     -> {}
```

**三重后果，逐条实测：**

**(a) 决策路径完全不加权。** `:572-576` 构造的票面只有 `reviewer/vote/confidence`，**没有 `weight` 键**；`:597-600` 调用 `evaluate()` **不传 `configured_weight`、不传 `policy`**。FSM 依据的是这一次计票，而 `vote_result.json` 由 `:685` 另算一次。

**(b) 权威产物记录伪证。** 端到端跑 N=3、`vote_weight=[1,1,2]`（$W=4$）、票型 `[YES, YES, NO(w2)]`：

```
FSM transition: CONSENSUS_CHECK -> MERGING via E4
task state    : MERGING
vote_result.json (D-1 immutable) decision: APPROVED
  weighted breakdown: reject_weight=1   (配置值应为 2)
  policy_snapshot configured_weight: 3  (配置值应为 4)
```

`policy_snapshot` 是 `vote_result.json` 内**自称记录本次计票所用政策**的块。它记录的 `configured_weight`、`seat_quorum_required`、`weight_quorum_required`、`minimum_winning_seats`、`dictator_cap_enabled` 全部来自 `vote.py:190-193` 的派生默认值，与 `macao.yaml` 无关。D-1 规定 `vote_result.json` 是不可变机器计票记录 —— **一份对自己所用参数作出不实陈述的记录，不满足 D-1 的证据地位**。这与我上轮 A-P1-3 是同一缺陷，本轮修好了 `weight`/`source`/哈希三维，未修 `policy_snapshot` 维，且根因在编排器而非 `vote.py`。

**(c) 本轮头条修复①在运行时不可达。** 申请 §1.1 的全部价值是把根 `macao.yaml` 的 `seat_quorum_required` 提到 3。该值**从未被编排器读取**；计票用的是 `ceil(2N/3)` 派生默认。$N=4$ 时两者恰好都等于 3，所以现在看不出差别 —— 但这是巧合，不是构造保证：`minimum_winning_seats`、`dictator_cap_enabled` 以及任何非默认 `vote_weight` 一律失效。同理申请 §1.4「纯整数五门禁实装」在引擎层为真、在集成层为假。

**验收**：
1. `Orchestrator.__init__` 保留 `team` 与 `policy`（或改 `:677-682` 从 `raw_config` 取值）；
2. `:572-576` 票面写入每席 `weight`；`:597-600` 与 `:607` 两处 `evaluate()`/`generate_vote_result()` 均传 `configured_weight` + `policy` + `reviewer_weights`；
3. 断言 `vote_result["policy_snapshot"]` 与 `macao.yaml` `policy` 逐字段相等、`configured_weight == Σ vote_weight`；
4. 加一条集成测试：`vote_weight=[1,1,2]` + 票型 `[YES,YES,NO]` $\Rightarrow$ `decision == DEADLOCK` 且**不发生** E4。

### 3.3 A-P1-3　`submit_disposition()` 的 E4 守卫空洞：`DEADLOCK` + 空处置 + 伪造 ref 可直推 `MERGING`

> 本人独立发现。同行两方均未探测该接口的越权维（muse 复述了申请自带的集成测试）。

申请 §1.6 把 `submit_disposition()` 列为本轮新增闭环。`src/macao/workflow/orchestrator.py:784-830` 的全部前置校验只有两条：Draft-07 `validate_review_disposition` 通过，且 `disposition_status == "FINAL"`；随后按 `any(requires_new_checkpoint)` 分流 E5a / **E4 → `MERGING`**。

**权威条款要求的三个合取项（PRD `:875`、`:714`；提案 `:226`；清单 `:85`②；UC-6「精确穷尽」）：**
① 机器决策为 `APPROVED`（或经合法 E7 override 裁决）；② FINAL disposition **精确覆盖 100% issue**、无未豁免 BLOCKING；③ 全部 `requires_new_checkpoint == false`。

**代码只实现了 ③。** 端到端复现（N=2，票型 `[YES, NO(1 项 BLOCKING)]`）：

```
after tally: state= CONSENSUS_CHECK   vote_result.decision= DEADLOCK   requires_disposition= True
submit_disposition -> True | Disposition accepted, transitioned via E4 to MERGING
FINAL state: MERGING
vote_result.decision (immutable, unchanged): DEADLOCK
```

提交的处置体是 `"disposition_status": "FINAL", "dispositions": []` —— 对已记录的那 1 项 BLOCKING issue **一条处置都没有**（`all()` 对空列表恒真，守卫被空集穿透）。

**同一探针换成伪造引用，同样放行：**

```
vote_result_ref.sha256   = "ffff…"  (与磁盘上 vote_result.json 无关)
issues_index_sha256      = "eeee…"  (与 vote_result.issues_index 无关)
submit_disposition -> True | transitioned via E4 to MERGING
```

即：`cd285dd` 轮把 `vote_result_ref` 改为**必填**所建立的互锁，在消费端**只校验了字段存在，未做任何绑定校验**。执行者可凭一份与本轮计票毫无关系的处置书推进合并。

**影响**：三条被同时绕过的规则 —— DEADLOCK 必须经 E7 人工裁定（UC-7、PRD `:873`）；BLOCKING issue 必须逐项处置（F-17、D-5）；评审对象 = 合并对象的证据链（D-1/D-2）。

**验收**：`submit_disposition` 增加三项前置断言并各配一条**否定测试**：
1. 读取磁盘 `vote_result.json`，要求 `decision == "APPROVED"` 或存在合法 `admin_override.json`；否则拒绝；
2. `{d["issue_id"] for d in dispositions} == {i["issue_id"] for i in vote_result["issues_index"]}`（无差集、无未知 id），且无 `disposition_type == "NEEDS_ADMIN"` 残留；
3. `sha256(vote_result.json) == vote_result_ref.sha256` 且 `issues_index_sha256` 与重算值相等。

---

## 4. 轨 A · P2 / P3

| ID | 级 | 问题 | 证据 |
|---|---|---|---|
| A-P2-1 | P2 | `state_engine.py:102-103` Layer 1c 由 `vote_result.decision == "APPROVED"` 直接推出 `(MERGING, "E4")`，**完全不看 `requires_disposition`**。实测：`requires_disposition: true` + 1 项未处置 BLOCKING + 磁盘上无任何 `executor.disposition.yml` $\Rightarrow$ 返回 `(AgentState.MERGING, 'E4', …)`。**当前 `recognize_state` 在 `src/`、`tests/` 中零调用方**（清单 `:84` 将该文件列为 Phase 1 变更项），故登记为**潜在**缺陷不升 P1；但守卫只加在四条 E4 生产路径中的一条，daemon 接线时会直接继承该绕过 |
| A-P2-2 | P2 | `orchestrator.py:913` `OverrideChoice.APPROVED: (AgentState.MERGING, "E7", …)` 直跳 `MERGING`。PRD `:881` 明写 APPROVED override 应「解除 HOLD，执行者角色投影 `SHOULD_DISPOSE`，待执行者出具带 `EXEMPTED_BY_ADMIN`+`override_id` 的 FINAL disposition **校验通过后**分流 E4/E5a」；提案 `:135` 更写明「严禁无 FINAL disposition 直跳 `MERGING`」。已由 `cli/main.py:294` 接线，属活路径。本轮未声称闭合，故不升 P1 |
| A-P2-3 | P2 | `EXTEND` 是 PRD `:881`、提案 `:230`、UC-7 `:31`（「选项闭合，无其他值」）三处一致声明的第五个 override 选项。`core/types.py:65-70` `OverrideChoice` 只有 4 个成员；`cli/main.py:280` `click.Choice([...])` 亦只有 4 个。实测 `OverrideChoice('EXTEND')` → `ValueError`。文档声明的闭合集合与机器契约不一致 |
| A-P2-4 | P2 | §5 唯一权威表残留（我上轮 A-P1-5 的未闭维）：`vote_result.schema.json:28,32` 仍声明 `timestamp` 与 `executor` 别名，`vote.py:217-219` 仍**同时写出** `generated_at`+`timestamp`、`executor_id`+`executor`。横向扫描 8 份契约：**只有 `vote_result` 用 `generated_at`，其余 7 份一律 `timestamp`** —— 这正是 A-P1-1 与 B-P1-1 的成因（文档作者按 `vote_result` 的必填名写进了处置书）。建议全库统一为 `timestamp` 并删除别名 |
| A-P2-5 | P2 | `vote.py:173-176` 的 `human_resolution` 分支可产出 `RETRY_REVIEW`/`CANCELLED`，但 `vote_result.schema.json:158` `decision` 枚举只有三值，实测两者均 `ValueError: … is not one of ['APPROVED','REWORK_REQUIRED','DEADLOCK']`（`APPROVED`/`REWORK` 已可通过，较上轮四路全死有改善）。生产路径 `resolve_override` 走 `admin_override.json`、不调用此参数，故为死码不一致；建议删除该参数或补齐枚举 |
| A-P2-6 | P2 | `tests/test_prd_snippets_schema.py:25` 只打开 `docs/MACAO_PRD_v2.md` 且只抽六个命名小节，不覆盖 `docs/PRD_CHANGE_PROPOSAL_v2.5.md` 与 `docs/usercases/*.md`。申请 §3.1 写「PRD 全量代码块」对该文件成立，但被用作全体交付物的契约闭环凭据则窄于事实 —— 本轮两条 P1 恰好落在缺口内。**连续第 6 轮建议扩面** |
| A-P3-1 | P3 | `orchestrator.py:483-486` docstring 双重失真：既写「`APPROVED` -> … moves to MERGING (E4)」（与 `:708-757` 新守卫冲突），又写「DEADLOCK / TIMEOUT ABSTAIN -> **DOES NOT WRITE** vote_result.json（PRD §3.3 E3 …）」—— 而 `:607-615` 恰恰 `write_to_disk=True`，PRD `:873` 也明写 DEADLOCK「即时落盘不可变 `vote_result.json`」。该注释引用 PRD 条款为其反面背书 |
| A-P3-2 | P3 | 申请 §3.4「212 份 Markdown」：`git ls-files '*.md'` = **205**，工作区含 4 份未跟踪同行报告 = **209**。任一口径都不是 212。**第 3 轮复发**，建议固定为 `git ls-files '*.md' \| wc -l` |
| A-P3-3 | P3 | 申请 §3.5 标题为「Schema 契约与 Fixtures 双向校验」而正文写「22 份反例 22/22 准确拦截」：其中 `macao_config_dictator_weight_violation` / `low_seat_quorum` / `low_weight_quorum` 三份在 **Draft-07 单独校验下 ACCEPT**，仅由 `validate_config` 语义层拒绝。项目自带测试确实走 `validate_config`（`tests/test_schema.py:363`），故系统级结论为真，但不得表述为 Draft-07 物理锁死。**第 2 轮登记** |

---

## 5. 轨 B · 用例体系

### 5.1 B-P1-1　UC-6 处置信封含 `generated_at`，通不过现行 `review_disposition` 契约；申请 §3.2 写 PASS

> 与 grok 轨 B P1-1 独立同结论。

轨 B 申请 §3.2 逐条列出三份内嵌示例的校验结论，其中第一条为：「`UC6-issue-triage-rework.md` 处置示例 → `review_disposition.schema.json`：**PASS**」。

**证据：**

1. `docs/usercases/UC6-issue-triage-rework.md:36`：`generated_at: "2026-09-01T12:10:00Z"`。
2. 抽出 UC 语料全部 3 个 YAML 围栏（该语料共且仅有 3 个 `yaml` 围栏，与申请 §3.2 列举完全对应）逐一送对应契约：

```
UC3-dev-checkpoint.md      -> dev_manifest       PASS
UC1-init-gemini.md:126     -> macao_config       PASS (含 validate_config 语义层)
UC6-issue-triage-rework.md -> review_disposition FAIL
   Additional properties are not allowed ('generated_at' was unexpected)
```

3. 删除该键或改名 `timestamp` 后同一对象 PASS（`vote_result_ref` 三元组本身合法）。

**「用例正文零变更」不能推出「示例仍合法」**：我实测 `git diff cd285dd..73576c5 -- docs/usercases` 为空，申请的稳定性陈述属实；但契约在 `73576c5` 被轨 A 收紧了，判据随之改变。这也是我本轮**推翻自己前两轮 `YES_APPROVE`** 的全部理由 —— 前两轮的授予不是本轮证据。若我本轮只做 diff 比对（如同行 muse 的路径）就会漏掉此项，故在此明确登记方法：**契约任何一次收紧后，必须重抽全部引用该契约的文档围栏**。

**验收**：UC-6 信封时间键与契约 `properties` 同名（建议 `timestamp`，与 PRD §2.5、正例 fixture 一致）；`tests/` 增加「抽出 `docs/usercases/*.md` 全部 YAML/JSON 围栏并送对应契约」的用例（同时可覆盖 A-P1-1）。

### 5.2 轨 B · P2 / P3

| ID | 级 | 问题 | 证据 |
|---|---|---|---|
| B-P2-1 | P2 | D-9 定义的四个命令中，`reconcile`（「确定性恢复执行器」，提案 `:42`）在 `docs/usercases/` **零命中**。`init`/`adopt` 有 UC-1、`doctor` 有 UC-10，`reconcile` 无任何用例。申请 §2 自称「全量用例体系」，与 D-9 存在覆盖缺口。与 grok 轨 B P2-2 一致 | `grep -rn reconcile docs/usercases/` → 0 |
| B-P2-2 | P2 | UC-7 `:31` 声明 override 选项「闭合，无其他值」共 5 项含 `EXTEND`；`:81` 更把「五选项各自转移正确（E4/E5/E9/E10/EXTEND 映射）」写为验收标准。该验收在现行机器契约下**不可满足**（见 A-P2-3）。UC-7 与 PRD `:881` 相互一致，故不是文档间矛盾，但作为**可执行验收标准**它是伪的 | `OverrideChoice` 4 成员；`click.Choice` 4 值 |
| B-P3-1 | P3 | UC-5 `:29`「**赞成加权占比** = Σ(approve 权重) / 有效权重」与紧随其后的「加权五重门禁（纯整数）」并列，易被误读为门禁含除法。建议加一句「该占比仅为报告量，不参与门禁判定」 | 见 §7 对 grok 的分歧登记 |

---

## 6. §6 反例库独立复算（11 组，全部为本人构造）

对 `ConsensusEngine.evaluate` 逐格复算，逐条对照 PRD §2.3 五道门禁：

| 场景 | 结果 | $E_N$ / $E_W$ | 期望 | 判定 |
|---|---|---|---|---|
| 全部弃权（N=3） | `DEADLOCK` | 0 / 0 | 门②不过 | ✅ |
| 1 超时 ABSTAIN + 2 批准 | `APPROVED` | 2 / 2 | $3\cdot2\ge2\cdot2$，席位 2≥2 | ✅ |
| 1 超时 + 1 批准 + 1 缺席 | `DEADLOCK` | 1 / 1 | 门②不过 | ✅ |
| 1:1（N=2） | `DEADLOCK` | 2 / 2 | 双方 $3\cdot1<2\cdot2$ | ✅ |
| 1:1:1（N=3） | `DEADLOCK` | 2 / 2 | 同上 | ✅ |
| 2:1（N=3） | `APPROVED` | 3 / 3 | $3\cdot2\ge2\cdot3$ | ✅ |
| **codex 反例** `[Y w2, N w1, N w1]`，$W=4$ | `DEADLOCK` | 3 / 4 | $3\cdot2=6<8$ 双方均不过门④ | ✅ |
| 独裁帽边界 `[Y w2, Y w1, N w1]` | `APPROVED` | 3 / 4 | $3\cdot3=9\ge8$ 且席位 2≥2 | ✅ |
| **门⑤边界** `[Y w3, N w1]`，$W=4$ | `DEADLOCK` | 2 / 4 | 门④过（9≥8）但胜方席位 1<2 | ✅ |
| 根配置 4 审 3:1 | `APPROVED` | 4 / 4 | 门②③④⑤全过 | ✅ |
| 根配置 4 审 2 批准 + 2 超时 | `DEADLOCK` | 2 / 2 | $E_N=2<\lceil8/3\rceil=3$ | ✅ |

**引擎层 11/11 全部正确，纯整数交叉乘法无浮点参与门禁**（`conf` 的除法仅用于 `decision_confidence` 展示位）。这是本轮最扎实的一处进展，也是我上轮 A-P1-3 之「加权算法未实装」维的真实闭环。**问题不在引擎，在于它没有被接到决策路径上**（A-P1-2）。

---

## 7. 交叉核对与分歧登记

**与 grok（两轨 `NO_APPROVE`）**

- **一致（独立同结论，非转述）**：A-P1-1 / B-P1-1 同源。我与 grok 各自从「契约本轮收紧 → 回扫引用该契约的围栏」这一路径独立命中，两份报告的行号、拒因字符串、修复方向一致。
- **修正其表述**：grok 轨 A P2-5 的 DEADLOCK 分支判断成立，但未覆盖 `:685` 主分支同样失效的事实（根因在 `__init__` 归一化）。见 §0.2，我据此升级为 A-P1-2。
- **分歧（定级）**：grok 将编排器接线与 E7 直跳列为 P2（「L1 看文档」）。我按 §3.0 的理由列 P1。**登记为立场分歧，不影响任一方的票**。
- **分歧（内容）**：grok 轨 B P2-3 认为 UC-5 `:29` 的浮点占比与纯整数门禁并列构成 P2。我**不同意**：该行是 `decision_confidence` 的定义（UC-5 `:104` 自述为「遗留决策点：`decision_confidence` 语义（建议 = 赞成加权占比，纯算术）」），紧随其后的门禁列表已明确标注「纯整数」，且 `engine.py:96,101` 中该除法确实只赋给 `conf` 不参与任何比较。我降为 P3（B-P3-1，建议加一句限定语）。

**与 muse（两轨 `YES_APPROVE`）**

- muse 的 A-2 已指出 `vote_result` 保留 `timestamp`/`executor` 别名（与我 A-P2-4 同），但**定为 P3 且未继续抽出使用该别名的处置示例** —— 该别名正是两条 P1 的成因。muse 的 A-3 与我 A-P3-1 同源，我另补出其第二处失真（DEADLOCK 落盘）。
- muse 对 E4 守卫的核验路径是复述申请自带的集成测试 `test_approved_with_advisory_holds_and_requires_disposition`。该测试确实通过；但它只走「APPROVED + 1 项 advisory」这一条正例。**顺带一提，该测试本身即可佐证 A-P1-3 的覆盖维**：其提交的处置 `issue_id` 为 `"codex/ISSUE-01"`，而同一轮 `vote_result.issues_index` 中生成的 id 是 `"issue-codex-1"`（`vote.py:129,201`）—— 两者不相等，`submit_disposition` 照样放行。
- **登记分歧**：我不同意「本轮双轨授予」。muse 的 §3 复跑结论我逐条复现均为真，分歧不在事实层，而在**抽检面**：契约收紧后未重抽引用该契约的文档围栏，以及未对 `submit_disposition` 构造越权反例。

**与 codex（合并 `REJECT`，P1×4 —— 报告晚于本报告落盘，以下为落盘后补记）**

- **独立收敛（两处）**：codex P1-1 与我 A-P1-2 (a)、codex P1-2 与我 A-P1-3 完全同源，双方均以自建反例得出，互不引用。codex P1-2 另补出我未检查的一维 —— disposition 的 `task_id` / `checkpoint_ref` / `review_round` / `executor` 与当前轮**均无绑定校验**（改成 `foreign-task` / `foreign-ref` 亦放行）。我接受该补充，已并入 A-P1-3 验收第 1 项的检查清单。
- **同一处修正也适用于 codex**：codex P1-1 写「676-697 行之后调用生成器时才传入权重与 policy」，同样隐含 `:685` 已接线。实测该处传入的两个变量恒为空（根因在 `__init__:122` 丢弃 `team`/`policy`），故**两条分支同为未加权**，且 `policy_snapshot` 因此记录伪证 —— 这一维 codex 与 grok 均未覆盖。见 §0.2。
- **codex 独有、我未发现的两项（本机复读源码确认成立，不据为己有）**：
  - codex P1-3：`vote.py:141-148` 合成的 timeout 票只写 `source`，**未写 `deadline` 与 `last_ping_at`**，而提案 `:113`（D-3）明定「由 Orchestrator 记录 `source: timeout`、deadline 和最后一次 ping」；`vote_result.schema.json:50-51` 把两字段设为可选，「必须记录」与契约相冲突。另：DEADLOCK/超时分支 `:607-615` 连 `task_id` 都不传，终局产物回退为 `task-<ref前缀>`。
  - codex P1-4：`vote.py:282-286` 每次 `open(..., "w")` 无条件重写 `.macao/vote_result.json`，无存在性检查、无 round/sha 冲突拒绝、无 evidence-ref 封存 —— 同轮重复调用 `collect_and_evaluate_consensus()` 即可覆盖 D-1 声称「不可变」的记录。
  - 我在本轮聚焦于「记录内容是否属实」（`policy_snapshot` 伪证）与「守卫是否可穿透」，**未检查记录的写入是否幂等/不可覆盖**，这是我本轮的抽检盲区，登记备查。
- codex 与 muse 均未抽出 `generated_at` 一项（A-P1-1 / B-P1-1）；该项由 grok 与我各自独立命中。

**票型汇总（截至本报告落盘）**

| 轨 | claude | grok | codex | muse |
|---|---|---|---|---|
| 轨 A 设计同步 | `NO_APPROVE` | `NO_APPROVE` | `REJECT`（不分轨合并） | `YES_APPROVE` |
| 轨 B 用例体系 | `NO_APPROVE` | `NO_APPROVE` | `REJECT`（不分轨合并） | `YES_APPROVE` |

按 GUIDELINES §8「真理不等于投票」「沉默 ≠ 同意」与 F-17（有条件通过在机器语义上即为阻断否决）：**两轨均未达成授予条件，本人不宣告 PG-0 成立**。四位评审中三位否决，且三份否决报告的 BLOCKING 无一重合于「同一项被误判」—— A-P1-1/B-P1-1（claude+grok）、编排器加权接线（claude+codex+grok）、disposition 守卫（claude+codex）三组均为多方独立收敛。轨 B 连续两轮全票通过的历史不构成本轮证据 —— 我本轮明确推翻自己前两轮的 `YES_APPROVE`，理由见 §5.1。

---

## 8. 建议闭环顺序（含已在本机实跑通过的验收命令）

**第一优先（两轨 P1，一处改动同时解两条）**

1. 统一处置信封时间键：`docs/PRD_CHANGE_PROPOSAL_v2.5.md:159` 与 `docs/usercases/UC6-issue-triage-rework.md:36` 的 `generated_at` → `timestamp`（与 PRD §2.5、正例 fixture、其余 7 份契约一致）。

```bash
# 门 1：全库处置类围栏必须过契约（可拦 A-P1-1 与 B-P1-1）
! grep -rn '^generated_at:' docs/PRD_CHANGE_PROPOSAL_v2.5.md docs/usercases/
```

2. 顺手收敛 A-P2-4：删除 `vote_result.schema.json` 的 `timestamp`/`executor` 别名与 `vote.py:218-219` 的双写，全库统一 `timestamp`（此项不做，同类缺陷仍会第 5 次复发）。

**第二优先（轨 A P1 之集成层）**

3. A-P1-2：`Orchestrator.__init__` 保留 `team`/`policy`；两处计票均传 `configured_weight`+`policy`+`reviewer_weights`；断言 `policy_snapshot` 与 `macao.yaml` 逐字段相等。

```bash
# 门 2：政策必须真正抵达编排器（当前失败）
PYTHONPATH=src python3 -c "
import yaml,sys
from macao.workflow.orchestrator import Orchestrator
o=Orchestrator(project_root='.',config=yaml.safe_load(open('macao.yaml')))
sys.exit(0 if o.config.get('policy') and o.config.get('team') else print('policy/team dropped by __init__') or 1)"
```

4. A-P1-3：`submit_disposition` 补齐 PRD `:875` 的三个合取项（决策前置、精确穷尽覆盖、ref 绑定），每项配一条否定测试。

**第三优先（P2）**

5. A-P2-1 / A-P2-2：`state_engine.py` Layer 1c 与 `resolve_override(APPROVED)` 与 E4 守卫**同句**（四条通往 `MERGING` 的路径共用一个守卫函数）。
6. A-P2-3 / B-P2-2：补 `OverrideChoice.EXTEND` 与 CLI `click.Choice`，或从 PRD `:881`、提案 `:230`、UC-7 `:31,:81` 三处同步删除该选项 —— 二选一，不得并存。
7. A-P2-6：把契约围栏抽检扩到 `docs/PRD_CHANGE_PROPOSAL_v2.5.md` 与 `docs/usercases/*.md`。

```bash
# 门 3：扩面后的围栏抽检（当前 2 处 FAIL，修好后应为 0）
PYTHONPATH=src python3 -c "
import re,yaml,sys
from macao.core.schema import validate_review_disposition
bad=0
for p in ['docs/PRD_CHANGE_PROPOSAL_v2.5.md','docs/usercases/UC6-issue-triage-rework.md']:
    t=open(p,encoding='utf-8').read()
    for m in re.finditer(r'\`\`\`yaml\n(.*?)\`\`\`',t,re.S):
        o=yaml.safe_load(m.group(1))
        if isinstance(o,dict) and 'disposition_status' in o:
            ok,e=validate_review_disposition(o)
            if not ok: print(p,'FAIL:',e); bad+=1
sys.exit(1 if bad else 0)"
```

8. B-P2-1：为 D-9 的 `reconcile` 补用例，或在 `docs/usercases/README.md` 显式登记该缺口与计划轮次。

**闭合两轨 P1 后重新申请 L1 / PG-0。** A-P1-2 / A-P1-3 及 A-P2-1/2 建议单列 **L2 SPEC-CODE-ALIGNED** 申请，与 L1 分开受审。

---

## 附：机器票与结构化 issue 索引

### 轨 A · `vote: NO_APPROVE`

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/A-P1-1` | major | `BLOCKING` | 提案 `:159` 处置示例 `generated_at` 被本轮封闭的 `review_disposition` 契约拒绝 |
| `claude/A-P1-2` | critical | `BLOCKING` | `Orchestrator.__init__:122` 丢弃 `team`/`policy`；`vote_weight` 与全部 policy 参数运行时永不生效；`policy_snapshot` 记录伪证（实测 $W=4$ 记为 3） |
| `claude/A-P1-3` | critical | `BLOCKING` | `submit_disposition:784` 仅校验 FINAL 与 Schema；`DEADLOCK` + `dispositions: []` + 伪造 `vote_result_ref` 可直推 E4 → `MERGING` |
| `claude/A-P2-1` | major | `ADVISORY` | `state_engine.py:102` Layer 1c `APPROVED → E4` 不看 `requires_disposition`（当前无调用方） |
| `claude/A-P2-2` | major | `ADVISORY` | `orchestrator.py:913` E7 `APPROVED` 直跳 `MERGING`，违反 PRD `:881` 两步式 |
| `claude/A-P2-3` | major | `ADVISORY` | `EXTEND` 为三处文档声明的闭合选项，`OverrideChoice` 与 CLI 均无该值 |
| `claude/A-P2-4` | major | `ADVISORY` | `vote_result` 双别名 `generated_at`/`timestamp`、`executor_id`/`executor` 仍并存并同时写出（§5 唯一权威表） |
| `claude/A-P2-5` | minor | `ADVISORY` | `human_resolution` 的 `RETRY_REVIEW`/`CANCEL` 仍被 `decision` 三枚举拒死（死码不一致） |
| `claude/A-P2-6` | major | `ADVISORY` | 围栏抽检门禁只覆盖 `MACAO_PRD_v2.md` 六节，两条 P1 落在缺口内（连续第 6 轮） |
| `claude/A-P3-1` | minor | `ADVISORY` | `orchestrator.py:483-486` docstring 双重失真（E4 直跳 + DEADLOCK 不落盘） |
| `claude/A-P3-2` | minor | `ADVISORY` | 「212 份 Markdown」与 205/209 两种口径均不符（第 3 轮复发） |
| `claude/A-P3-3` | minor | `ADVISORY` | 「Draft-07 22/22 拦截」含 3 份仅语义层拒绝（第 2 轮登记） |

### 轨 B · `vote: NO_APPROVE`

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/B-P1-1` | major | `BLOCKING` | UC-6 `:36` 处置示例 `generated_at` 被 `review_disposition` 契约拒绝；申请 §3.2 写 PASS，实测 FAIL |
| `claude/B-P2-1` | major | `ADVISORY` | D-9 的 `reconcile` 在 `docs/usercases/` 零命中，「全量用例体系」存在覆盖缺口 |
| `claude/B-P2-2` | major | `ADVISORY` | UC-7 `:81` 验收「五选项各自转移正确（含 EXTEND）」在现行机器契约下不可满足 |
| `claude/B-P3-1` | minor | `ADVISORY` | UC-5 `:29` 浮点占比与纯整数门禁并列易误读，建议加限定语（对 grok 的 P2 定级持异议，降为 P3） |

---

**证据类型汇总（§3.1）**：DOC（提案/PRD/UC/清单行号引用）、SPEC（8 份 Draft-07 契约与 32 份 fixtures）、CODE（`orchestrator.py`、`vote.py`、`engine.py`、`state_engine.py`、`config.py`、`types.py`、`cli/main.py` 读码）、SIM（本机构造的 11 组门禁反例、4 组端到端编排器探针、2 组 Layer 1c 探针）、TEST（`unittest discover` 97/97、`test_config` 10/10、`test_consensus` 5/5、`test_prd_snippets_schema` 2/2、`compileall` rc=0）。**未覆盖**：win32 平台、真实多 CLI 适配器运行、Phase 1～5 实施产物。
