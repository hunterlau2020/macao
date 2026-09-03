# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-09-03（提交 `404ebd2` 轮 3 份复审申请；总计结论类 **142 份**（138 `review-result-*` + 2 `review-2.5-*` + 2 `REVIEW_METHODOLOGY_*`）、申请类 **38 份**，双向对账 100% 吻合）
- **当前并行评审轨道**：
  - **文档轨（`404ebd2` 轮复审申请中，全面闭环 `73576c5` 轮 5 项阻断）**：
    1. [`2026-09-03-review-request-404ebd2.md`](2026-09-03-review-request-404ebd2.md) → 总入口申请（目标 **L1 DOC-ALIGNED / PG-0**；被审提交 **`404ebd2`**）
    2. [`2026-09-03-review-request-404ebd2-PRD-v2.5-Design-Sync.md`](2026-09-03-review-request-404ebd2-PRD-v2.5-Design-Sync.md) → PRD 设计同步专项（被审提交 **`404ebd2`**）
    3. [`2026-09-03-review-request-404ebd2-UseCases-v2.5-Alignment.md`](2026-09-03-review-request-404ebd2-UseCases-v2.5-Alignment.md) → 用例体系对齐专项（被审提交 **`404ebd2`**）
  - **代码轨（挂起复审）**：[`2026-09-01-review-request-Phase3-PG3-L4-Certification.md`](2026-09-01-review-request-Phase3-PG3-L4-Certification.md) → 目标 **L4 / PG-3**，被审提交 `42b5c07`
- **当前定级状态**：
  - **文档轨 · PRD 设计同步（轨 A）**：**`73576c5` 轮未获授予**。票型 3 否决（Claude `NO_APPROVE` P1×3、Grok `NO_APPROVE` P1×1、Codex `REJECT` P1×4）+ 1 授予（Muse `YES_APPROVE`）。
  - **文档轨 · 用例体系（轨 B）**：**`73576c5` 轮改判为未获授予**，连续两轮全票授予的态势中断。Claude 与 Grok 均**推翻自己前两轮的 `YES_APPROVE`**——用例正文相对 `cd285dd` 零变更（已 diff 证实），但本轮轨 A 把 `review_disposition.schema.json` 收成 `additionalProperties: false`，UC-6 `:36` 的 `generated_at` 随之不再合法，轨 B 申请 §3.2「UC6 → PASS」经两方独立机验为 **FAIL**。
  - **历史文档定级**：维持 **PRD v2.3.1 的 L1 / PG-0**。
  - **代码轨**：**维持 L3 SCENARIO-VERIFIED / PG-2**；L4 / PG-3 终局认证仍在复审中（仅 GLM 1 份，按 GUIDELINES §8「沉默 ≠ 同意」不计多数）。


### 文档轨：PRD v2.5 设计同步轨 与 用例体系轨（`cd285dd` → `73576c5`，当前轮）

- **被审提交**：`73576c5`；工作区 HEAD `34a1077`（差量 = 三份申请 + `STATUS.md` + 6 份评审结论，正文与 `73576c5` 一致）
- **本轮票型（6 份报告 / 4 位专家，两轨合计）**：**多数否决，未获授予**。
  - **Claude**：两轨均 `NO_APPROVE`（轨 A P1×3、轨 B P1×1）—— [`…-73576c5-claude.md`](2026-09-03-review-result-73576c5-claude.md)
  - **Grok**：两轨均 `NO_APPROVE`（轨 A P1×1、轨 B P1×1）—— [`…-73576c5-DesignSync-grok.md`](2026-09-03-review-result-73576c5-DesignSync-grok.md)、[`…-73576c5-UseCases-grok.md`](2026-09-03-review-result-73576c5-UseCases-grok.md)
  - **Codex**：不分轨合并 `REJECT`（P1×4，全部指向运行时/编排器层）—— [`…-73576c5-codex.md`](2026-09-03-review-result-73576c5-codex.md)
  - **Muse**：两轨均 `YES_APPROVE`（轨 A ADVISORY×4、轨 B ADVISORY×2）—— [`…-73576c5-DesignSync-muse.md`](2026-09-03-review-result-73576c5-DesignSync-muse.md)、[`…-73576c5-UseCases-muse.md`](2026-09-03-review-result-73576c5-UseCases-muse.md)
- **三方一致确认的实质进展（各方独立机验，非采信自述）**：
  - `cd285dd` 轮阻断中的 3 项真实闭环：提案「当前状态（HOLD）」表述清理、根 `macao.yaml` 双 quorum 提至 3 且 `test_root_macao_yaml_passes_semantic_validation` 入库、`vote_result.schema.json` 遗留小写枚举 `"automatic"` 全库归零。
  - **纯整数加权五道门禁在引擎单元层完全正确**：`ConsensusEngine.evaluate()` 门禁比较全为整数交叉乘法，`test_weighted_counterexample_deadlock`（`[YES w=2, NO w=1, NO w=1]` → `DEADLOCK`）与 `test_weighted_minimum_winning_seats_enforcement` 通过；Claude 另用 11 组独立反例逐格复算全部正确。
  - `review_disposition.schema.json` 根 / `executor` / `full_document` / `dispositions.items` 全量 `additionalProperties: false`，`disposition_unrecognized_property.yml` 精确拦截；`votes[].source` 必填且拦截精确；双 Schema 目录 8/8 契约 + 32/32 fixtures 逐字节一致；97/97 测试 PASS；compileall 0 Errors。
  - 用例正文相对 `cd285dd` **零变更**（`git diff` 证实）。
- **未获授予的阻断项（按独立收敛方数排序）**：

  | # | 阻断项 | 收敛方 |
  |---|---|---|
  | 1 | **`review_disposition` 契约本轮收紧为 `additionalProperties: false` 后，未回扫引用该契约的权威示例**：提案 §4.3（`:159`）与 UC-6（`:36`）的处置信封仍写 `generated_at`，该键契约中不存在，两处示例现均被拒。轨 B 申请 §3.2 明写「UC6 → PASS」，实测 FAIL。同一处修复对两轨均构成 L1 阻断（「所有 YAML/JSON 示例是合法可解析格式」） | **两方独立同结论**（Claude A-P1-1/B-P1-1 = Grok 轨 A P1-1/轨 B P1-1） |
  | 2 | **编排器决策路径未加权、`policy_snapshot` 记录伪证**：`Orchestrator.__init__` 归一化丢弃 `team`/`policy` 整段，`vote_weight` 与全部 policy 参数运行时永不生效；`vote_result.json.policy_snapshot`（D-1 不可变记录自称的算法参数）实测记录派生默认值而非配置值。本轮头条修复①④在集成层不可达 | **三方独立收敛**（Claude A-P1-2 / Codex P1-1 / Grok P2-5，Grok 判 P2 未升级） |
  | 3 | **`submit_disposition()` E4 守卫可被空处置或伪造引用穿透**：`DEADLOCK` + `dispositions: []` + 伪造 `vote_result_ref`/`issues_index_sha256` 可直推 `MERGING`；未校验 task/ref/round/executor 与当前轮绑定，未校验 issue_id 集合精确覆盖 | **两方独立收敛**（Claude A-P1-3 / Codex P1-2，Codex 另补 task/ref/round 绑定维） |
  | 4 | **超时终局产物缺 `deadline`/`last_ping_at`，且计票调用缺上下文**：D-3 明定超时合成 `ABSTAIN` 必须记录 deadline 与最后 ping，`vote.py` 只写 `source`；DEADLOCK 分支不传 `task_id`/`reviewer_weights`/`policy` | 单方（Codex P1-3） |
  | 5 | **`vote_result.json` 非真正不可变**：`vote.py:282-286` 无条件 `open(..., "w")` 重写，无存在性检查、无 round/sha 冲突拒绝，同轮重复调用可覆盖 D-1 声称的不可变记录 | 单方（Codex P1-4） |
- **Claude 另登记的单方 P2/P3（不阻断本轮定级判断，Phase 1 前应处理）**：`state_engine.py` Layer 1c 与 E7 `resolve_override(APPROVED)` 直跳 `MERGING`（当前均未审慎接线的次要路径）；`EXTEND` override 选项三处文档声明但机器契约无该值；`vote_result` 双别名 `generated_at`/`timestamp`、`executor_id`/`executor` 并存；D-9 的 `reconcile` 在用例体系零命中；Markdown 份数口径连续第 3 轮不一致（205/209 均非申请所称 212）。
- **本轮结构性观察**：「修复即引入同类缺陷」连续第 2 轮复发——`cd285dd` 轮 E7 收敛改对三处漏两行；本轮封闭 `review_disposition` 契约漏回扫提案与用例示例。围栏抽检门禁（`tests/test_prd_snippets_schema.py`）已固化但只覆盖 `MACAO_PRD_v2.md` 六节，连续第 6 轮建议扩面到提案与用例文件，本轮两条 P1 恰好落在缺口内。
- **本次机验（本文件更新时复跑，非采信申请自述）**：`git ls-files '*.md'` **205** 份（申请称 212，口径不符，「0 控制字符」结论本身为真）；`Ran 97 tests … OK`；`compileall` rc=0；双 Schema 目录 8 份契约 + 32 份 fixtures 逐字节一致；根 `macao.yaml` 语义校验通过（`validate_config`/`ConfigManager.load` 均 PASS）但编排器归一化丢弃其 `policy`（见阻断项 2）。

---

### 文档轨：PRD v2.5 设计同步轨 与 用例体系轨（`a0123e8` → `cd285dd`，已被 `73576c5` 轮取代）

- **被审提交**：`cd285dd`
- **前序轮票型（`a0123e8` 轮，6 份报告 / 4 位专家）**：
  - **Claude**：轨 A `NO_APPROVE`（P1×2）／轨 B **`YES_APPROVE`** —— [`…-a0123e8-claude.md`](2026-09-02-review-result-a0123e8-claude.md)
  - **Grok**：轨 A `NO_APPROVE`（P1×1）／轨 B **`YES_APPROVE`** —— [`…-a0123e8-DesignSync-grok.md`](2026-09-02-review-result-a0123e8-DesignSync-grok.md)、[`…-a0123e8-UseCases-grok.md`](2026-09-02-review-result-a0123e8-UseCases-grok.md)
  - **Qwen**：轨 A `NO_APPROVE`（BLOCKING×3）／轨 B **`YES_APPROVE`** —— [`…-a0123e8-DesignSync-qwen.md`](2026-09-02-review-result-a0123e8-DesignSync-qwen.md)、[`…-a0123e8-UseCases-qwen.md`](2026-09-02-review-result-a0123e8-UseCases-qwen.md)
  - **Codex**：不分轨合并 `REJECT`（P1×3，三条全部指向契约库、权重校验与 AEP 预算）—— [`…-a0123e8-codex.md`](2026-09-02-review-result-a0123e8-codex.md)
- **三方一致确认的实质进展（各方独立机验，非采信自述）**：
  - **PRD 正式示例 14/14 通过自家契约**（§2.1/2.2/2.3/2.5/5.2/§13 六处 + §2.4 全部 8 个 AEP 信封），**仓库根 `macao.yaml` 亦 PASS**。这条「权威文档的规范示例通不过自己指定的契约」的缺陷链自 `0bc6247` P0-2 起复发四次（P0-2 → N-6 → M-1 → `4027cce` A-P1-1），本轮是**第一次在契约被大幅收紧之后仍全部成立**；团队已把该检查固化为 `tests/test_prd_snippets_schema.py`，正是评审方连续三轮建议的三段门禁中的第一段。
  - `remote_name: null` 全链路打通：两份契约放开 null、新增 `fixtures/valid/macao_config_local_only.yaml` 正例、PRD §14.5 第 1 步写成「远端共享 / 纯本地」双分支，与 UC-8 关卡 1 同措辞。
  - `STATUS.md` 双向对账在被审基线上为 **0/0/0**（`4027cce` 轮 Claude A-P1-4 闭环）。
  - 用例侧：UC-7 的 P1–P4 与 PRD 修正后的 E7 源态一致；13 份用例的 3 处内嵌围栏对全部 8 份契约交叉验证全部 PASS；§6 反例库 **11/11** 可唯一推导，无回退。
  - 申请 §3/§4 机验各方复跑成立：正例 10/10、反例 16/16、双副本（含 fixtures 目录）0 diff、92/92 PASS、0 控制字符。**92/92 不构成 L2 证据**——其覆盖的仍是 v2.3.1 引擎主体。
- **轨 A 未获授予的阻断项**：

  | # | 阻断项 | 收敛方 |
  |---|---|---|
  | 1 | **E7 源态四处权威位置只改对两处**：PRD `:881` 与提案 `:135` 已收敛为 `HOLD`（`CONSENSUS_CHECK`），但**提案 `:226`（§4.5 状态转移表修订）与 `v2.5_CODE_CHANGE_INVENTORY.md:85`（交付物 #4，Phase 1 施工图）仍写 `CONSENSUS_CHECK 或 REWORK`**。PRD `:889` 明文「除本表所列来源外，任何实现不得引入其他状态转移路径」——按清单施工会实现一条被禁止的边，且现有代码本来是对的。申请 §1.3 称「PRD §3.3 状态机表与提案彻底清理」不成立 | **两方**（Claude A-P1-1 / Grok P1-1） |
  | 2 | **D-6 的独裁帽与两个 quorum 公式从未成为机器约束**：`dictator_cap_enabled: {"const": true}` 锁死的是「这面旗子必须写 true」，不校验任何权重。实测权重 `[5,1,1]`（$3\cdot5=15 \ge 2\cdot7=14$，违反 $\forall i, 3w_i < 2W$）被契约与产品自身 `validate_config()` **同时放行**；`seat_quorum_required` / `weight_quorum_required` 可声明为低于 $\lceil 2N/3 \rceil$ / $\lceil 2W/3 \rceil$ 的值。`ConfigManager.load()` 只上调 seat quorum，不校验独裁帽与权重 quorum。提案 `:410` 的措辞是「不满足则**拒绝启动**」。申请 §1.2 称「D-6 反支配门禁 Schema 物理锁死」不成立 | **两方**（Codex P1-1 / Claude A-P1-2） |
  | 3 | `vote_result_ref` 加为 property 但未进 `required`，提案 `:193`「disposition **必须**反向引用冻结的 vote result」仍未编码；valid fixture 亦不含该字段 | 两方（Codex P1-2 / Claude P2-3，严重度判定不同） |
  | 4 | 「8 类封闭 Payload + 2048 字节双向严格校验」不是实际契约：8 个分支均未设 `additionalProperties: false`，`protocol` 仍接受 `AEP/1.0`；反例 `aep_payload_oversized.json` 名不副实（44 字符 / 298 字节，拒因是空数组，补齐该维后被接受）。16 KiB 与逐字段预算已在 `src/macao/msg/envelope.py` 实现并接入 `create()`/`parse()`，Draft-07 无法表达整文档字节长度，落运行时属正确分工 | 两方（Codex P1-3 / Claude P2-2+P2-4，严重度判定不同） |
  | 5 | `aep_envelope.schema.json:72` 的 `$ref` 仍解析为网络 URL，契约库不自包含；`schemas/README.md:26` 宣称禁 base64 但 `diff_policy` 无枚举实际不拦；`macao_config` 的 `policy`/根级未设 `additionalProperties: false` | 单方（Claude P2-1 / P2-6 / P2-7） |

- **轨 B 获得授予票的依据（两方各自独立给出）**：轨 B 申请 §2 列出的 13 份交付物全部在 `docs/usercases/` 之内；两方均未在其中找出与 PRD、契约或 D-1～D-9 的机器可证不一致。上表阻断项 1 的冲突不在 13 份用例正文内（UC-7 与 PRD 同句），阻断项 2～5 全部落在契约库与运行时（轨 A 交付物 #2）。**两方均按 F-17 明确声明该票不是「有条件通过」。**
- **跨轨依赖（两方均已写明，不作为轨 B 的投票条件）**：UC-5 §2.b、UC-1 h0(3)、UC-10 §2.b 正确写下了 D-6 五重公式，但当前实现中独裁帽与双 quorum 三道门禁**并不存在**（阻断项 2）。轨 B 若最终获授予并用作 Phase 1~5 操作基准，照它验收将验不出这三道门禁。**建议把阻断项 2 的闭环列为 Phase 1 编码启动的前置条件。**
- **本轮结构性观察**：连续三轮出现的「修复动作本身是新缺陷的成因」模式，**本轮未再出现**——`a0123e8` 改动 4 份契约、PRD 69 行、提案、变更清单与 6 个源文件，三方逐项复跑后未发现新引入的机器可证缺陷；两条阻断均为旧项未改净。这是六轮以来第一次。合理推断与团队把第一段门禁（PRD 示例 × 契约）固化进 CI 有关；另两段（「用例/提案判据 × 契约与 §3.3 转移表」「`reviews/` 双向对账」）仍未入 CI，而本轮阻断项 1 恰是第二段能自动捕获的类型。
- **一处评审方自我更正（GUIDELINES §9 记录）**：Claude 初稿把上轮 A-P1-2（D-6）判为「完全闭环」，仅复测了自己上轮写下的两个探针；经 Codex P1-1 提示后本机复验推翻该判定，轨 A 的 P1 计数由 1 更正为 2。该更正已写入其报告 §0.1b。

---

### 文档轨：PRD v2.5 设计同步轨 与 用例体系轨（`6e35a71` → `4027cce`，已被 `a0123e8` 轮取代）

- **被审提交**：`4027cce`（工作区 HEAD `be5ee25`，差量仅为申请文件改名 + `MACAO_REVIEW_GUIDELINES.md` §1.3 命名条款 + 本文件；交付物正文与 `4027cce` 一致，四方均已核对）
- **本轮票型（5 份报告 / 4 位专家，两轨合计）**：**四方一致不通过，无一方投赞成**——`caf3473` 以来首次全体否决。
  - **Claude**：`NO_APPROVE`（两轨；轨 A P1×4、轨 B P1×1、P2×9、P3×3）—— [`…-4027cce-claude.md`](2026-09-02-review-result-4027cce-claude.md)
  - **Codex**：`REJECT`（P1×5）—— [`…-4027cce-codex.md`](2026-09-02-review-result-4027cce-codex.md)
  - **Grok**：`NO_APPROVE`（P1×2；前轮双轨 `APPROVE`，本轮改判）—— [`…-4027cce-grok.md`](2026-09-02-review-result-4027cce-grok.md)
  - **Qwen**：`NO_APPROVE`（两轨；Design-Sync BLOCKING×5 / ADVISORY×4，UseCases BLOCKING×2 / ADVISORY×3；**前两轮均投 APPROVE，本轮发现新证据后改判**）—— [`…-4027cce-DesignSync-qwen.md`](2026-09-02-review-result-4027cce-DesignSync-qwen.md)、[`…-4027cce-UseCases-qwen.md`](2026-09-02-review-result-4027cce-UseCases-qwen.md)
- **四方一致确认的实质进展（非采信自述，各方独立机验）**：`6e35a71` 轮 Claude 9 条 P1 中 **7 条真实闭环**，Codex 8 条中多条闭环——E4 六关卡顺序与 §14.5 对齐；E7 伴随动作写成 override → `SHOULD_DISPOSE` → FINAL → E4/E5a；E6 与变更清单补齐拓扑子孙守卫（`git merge-base --is-ancestor`）；`review_disposition` 枚举联动与 `issues_index_sha256` 必填；`macao_config` 根级 `policy`/`vote_weight` 必填；`dev_manifest` 核心引用必填；AEP Type A/B/E/H per-type payload；SRS 更正为 8 类 AEP/1.1；UC-7 触发域收敛为 P1–P4 且 Git Conflict 归 `E4b`；UC-6/UC-7 补齐 §5–§8。申请 §3/§4 机验各方复跑成立（正例 9/9、反例 13/13、双副本 0 diff、86/86 PASS、0 控制字符）。
- **未获授予的阻断项（按独立收敛方数排序）**：

  | # | 阻断项 | 收敛方 |
  |---|---|---|
  | 1 | **UC-8 纯本地模式 `remote_name: null` 通不过 `macao_config` 契约**（必填且 `minLength:1` 字符串），分支不可达；PRD §14.5 无该模式。**本轮为闭合上轮阻断而新引入** | **四方全体**（Claude B-P1-1 / Codex P1-4 / Grok P1-2 / Qwen UC B-1） |
  | 2 | **PRD 正式示例与刚收紧的 Schema 五处失配**：§2.5、第十三部分、§2.4 Type A/B/E 通不过 PRD 自己指定的契约；**仓库根 `macao.yaml` 通不过产品自己的 `validate_config()`** | 三方（Claude A-P1-1 / Codex P1-1 / Qwen DS B-1、B-5） |
  | 3 | **D-6 两道反支配门禁在契约层仍可关闭**：`minimum_winning_seats: 1` 与 `dictator_cap_enabled: false` 均被接受，反例可让**单一席位批准合并**（提案 `:414` 明定 $2 \le mws \le N$、`:410` 明定独裁帽无条件） | 三方（Claude A-P1-2 / Grok P1-1 / Qwen DS B-4、UC B-2） |
  | 4 | **E7 源态 `REWORK` 下 5 个闭合选项中 3 个无可达边**（E4/E5/E5a/E9 的「当前状态」均只有 `CONSENSUS_CHECK`）；提案 `:135` 另给「直接推进至 `MERGING`」与 PRD/UC-7「严禁无 FINAL 直跳」互斥 | 三方（Claude A-P1-3 / Codex P1-5 / Qwen DS B-3） |
  | 5 | **AEP 16 KiB / 2048 字节预算未入契约；per-type payload 仅覆盖 4/8 类**；`protocol` 仍接受 `AEP/1.0` | 三方（Codex P1-2 / Qwen DS B-2 / Claude A-P2-2，Claude 判 P2） |
  | 6 | **`STATUS.md` 双向对账不平**：@`4027cce` 存在但未登记 12 份（含本申请据以论证「已修复」的全部 7 份 `6e35a71` 轮报告）；三处计数互斥 | 单方（Claude A-P1-4）—— **本次更新已闭环，见下方对账说明** |
  | 7 | **`aep_envelope.schema.json:64` 的 `$ref` 解析为网络 URL** `https://macao.dev/schemas/v2.5/review_context.schema.json`，无 store 的 stock 校验器抛 `RefResolutionError` 并发起出站请求；契约库不再自包含，申请的机验声明离线复现不出（`src/macao/core/schema.py:76` 预置 store 故运行期正常，但该映射未见于 `docs/schemas/README.md`） | 单方（Claude A-P2-1） |
  | 8 | **AEP/1.1 与 `DISPOSITION_REQUIRED` 在实现层不可用，现有测试固化旧协议** | 单方（Codex P1-3）——属 **L2 判据**，本轮 L1 定级不计入 |

- **本轮结构性观察（三方均有记载，Claude 列为连续第 6 轮登记）**：阻断项 1 与 2 同源——**本轮的修复动作本身是新缺陷的成因**。收紧 4 份 Schema 时未回跑「PRD 示例 × 契约」，一次性打破 5 处规范示例与仓库根配置；引入 `remote_name: null` 判据时未回跑「用例判据 × 配置契约」，造出不可达分支。此前「每轮闭上一轮、同类再开一处」的模式已演进为「修复即引入同类缺陷」。三段共约 60 行的门禁脚本（PRD 示例×契约、用例判据×契约、`reviews/` 双向对账）已在 Claude 报告 §一 / §四 / §三 中给出可直接复用的实现，**建议本轮务必落进 CI**。
- **本次机验（本文件更新时复跑，非采信申请自述）**：`docs/**/*.md` **0 控制字符**；`fixtures/valid` **9/9 PASS**、`fixtures/invalid` **13/13 FAIL-CLOSED**（须预置本地 `$ref` store，见阻断项 7）；`docs/schemas/` ↔ `src/macao/schemas/` **8 份契约 + fixtures 目录全部一致**；`PYTHONPATH=src python3 -m unittest discover tests` **86/86 PASS**；`compileall` rc=0。**86/86 不构成 L2 证据**：其覆盖的是 v2.3.1 引擎，v2.5 计票、E5a、`admin_override` 命令路径在变更清单中仍标「待实施」。
- **申请侧计数勘误**：申请 §3.1 称「`git ls-files "*.md"` 169 份、`docs/` 175 份」，本机实测 **179 / 180 / 193**（末者跟随 `docs/usecases` 软链）；四份口径无一相符。「0 控制字符」的结论本身各方复现为真。

---

### 文档轨：PRD v2.5 设计同步与用例体系 Round 2 评审轮（`6e35a71`，已被 `4027cce` 轮取代）

> **本节的闭环声明已在 `4027cce` 轮被部分证伪**，保留作历史履历，不得作为定级依据。具体：下列「Schema 机器契约全面加固」条目在收紧契约的同时**未同步 PRD 正文与仓库根配置**，导致 5 处 PRD 规范示例与根 `macao.yaml` 反被自家契约拒绝（`4027cce` 轮阻断项 2）；「UC-8 显式本地模式（`remote_name: null`）」在机器契约上不可表达（阻断项 1）；`aep_envelope` 的「离线 `$ref` 解析 100% 稳定」仅对 `src/macao/core/schema.py` 的预置 store 成立，`docs/schemas/` 契约库本身已不自包含（阻断项 7）。

- **本轮票型（7 份独立出具：2 专家 APPROVE，2 专家 NO_APPROVE / REJECT）**：
  - **Grok**：`APPROVE`（DesignSync 与 UseCases 双轨均授予 **L1 DOC-ALIGNED / PG-0**，确认 P1-1 E7 豁免流唯一边、P1-2 D-1～D-9 逐字对齐、P2/P3 清理全部闭环）；
  - **Qwen**：`APPROVE`（DesignSync 与 UseCases 双轨均授予 **L1 DOC-ALIGNED / PG-0**，独立机验 0 控制字符、Schema 双副本 0 diff、测试 86/86 PASS 全部属实）；
  - **Claude**：`NO_APPROVE`（DesignSync P1×5 / UseCases P1×4：P1-1 `macao.yaml` 策略面 required 与独裁帽反例、P1-2 PRD 统一表 E4 关卡顺序与 §14.5 漂移、P1-3 返工检查点拓扑子孙守卫一致性、P1-4 STATUS 计数审计、P1-5 `review_disposition` 条件枚举联动；UC-7 接管触发与 PRD 可达边、UC-6/7 缺失标准章节、UC-8 远端不可达降级冲突）；
  - **Codex**：`REJECT`（P1×8：AEP payload 契约与 2048 字节预算、dev_manifest 核心引用必填、macao_config 封闭与必填、review_disposition 条件联动与 `issues_index_sha256`、E7 唯一出口与单写者、UC-7 init 与 MERGING 混塞、UC-8 远端模式与本地模式、SRSv1 7 类更名提示）。
- **全量阻断项闭环实装**：
  1. **Schema 机器契约全面加固（Fail-Closed）**：
     - `dev_manifest.schema.json`：根级 `required` 补齐 `task_id`、`checkpoint_ref`、`full_document`；
     - `macao_config.schema.json`：根级强制 `required: ["version", "project", "team", "policy"]`，reviewer 强制 `required: ["id", "cli", "adapter", "vote_weight"]`，policy 强制全部 6 字段必填且封闭为 `weighted_2/3_v1`；
     - `review_disposition.schema.json`：根级增加 `issues_index_sha256` 必填约束；增加 `allOf` 联动（`DEFERRED`、`REJECTED`、`EXEMPTED_BY_ADMIN` 强制 `requires_new_checkpoint: false`，`FINAL` 状态严禁 `NEEDS_ADMIN`）；
     - `aep_envelope.schema.json`：为 8 类 AEP 消息建立 per-type payload 校验（Type A/B/E/H 等），Type B 深度组合 `review_context.schema.json`，内联长正文硬约束 `maxLength: 2048` 字符预算；
     - `src/macao/core/schema.py`：升级 `SchemaValidator` 集成本地 RefResolver 映射池，保障离线 `$ref` 解析 100% 稳定；
     - **Fixtures 双向验证**：正例 9/9 PASS，反例 13/13 FAIL-CLOSED（新增 AEP 空 payload、dev 缺核心字段、disposition 非法 true 组合、config 缺 policy 等 6 项反例）。
  2. **PRD、提案与 SRS 权威文档严密自洽**：
     - PRD §3.3 统一状态转移表 E4 伴随动作严格同步为六道关卡顺序；
     - PRD §3.3 E7 伴随动作全面同步两步流转：落盘 `admin_override.json`（解 HOLD，投影 `SHOULD_DISPOSE`）$\rightarrow$ 执行者提交带 `EXEMPTED_BY_ADMIN`+`override_id` 的 FINAL disposition 校验通过后分流 E4 `MERGING` 或 E5a `REWORK`；
     - 提案 §4.5 彻底消除管理员代写 disposition 表述，严格落实单一垄断写者；
     - 变更清单与 PRD §15.2 严格互锁：返工新 commit 必须为上一轮 `checkpoint_ref` 之严格拓扑子孙（`git merge-base --is-ancestor <prev> <new>`）；
     - `docs/SRSv1.md:612-613` 现行迁移提示更新为 8 类 AEP/1.1 消息（Type A～Type H）。
  3. **用例体系（UseCases）规格与结构标准化**：
     - UC-7：剥离 init 向导歧义选择（归入 UC-1 步骤 3 `ADMIN_STATE_RESOLVED`）与 Git conflict 合并冲突（关卡 3 失败触发 `E4b` $\rightarrow$ `REWORK`），运行期 E7 严格收敛于 P1～P4；补齐标准 5～8 节（含设计自审）；
     - UC-6：补齐标准 5～8 节（含设计自审与覆盖率/枚举互锁断言）；
     - UC-8：明确远端共享模式（`remote_name` 非空）Gate 1 执行 `ls-remote` 严格 100% fail-closed 拦截，显式本地模式（`remote_name: null`）跳过远端推送；
     - README：修复首次检查点（无编号产物触发）与返工检查点（E6）标识。
- **本轮机验结果**：`docs/usercases/*.md` **13 份、控制字符 0**；全部 YAML/JSON 示例 **Draft-07 校验 100% PASS**；`fixtures/valid` **9/9 PASS**、`fixtures/invalid` **13/13 准确拦截**；`docs/schemas/` ↔ `src/macao/schemas/` **8 份逐字节一致**；`PYTHONPATH=src python3 -m unittest discover tests` **86/86 PASS**；`compileall` rc=0。

---

### 文档轨：PRD v2.5 第三轮复核（`2766c69` → `2da1bc2`）

- **本轮票型（2 份，独立出具）**：
  - **Claude**：`NO_APPROVE`（确认 N-1 公式控制字符、N-2 vote_result 决策枚举、Codex P1-4/P1-6/P1-7 等前序阻断全部闭环；提出 3 项 P1：M-1 review_context additionalProperties 未放行 `required_blocks`、M-2 macao_config 未单向封闭为 `weighted_2/3_v1`、M-3 PRD §2.5 未提 `override_id`）；
  - **Grok**：`NO_APPROVE`（确认 P0-1 状态机主流程闭环、8 份 Schema 双副本一致、86/86 测试通过；提出 3 项 P1：P1-1 封闭 consensus_rule、P1-2 UC-6 示例 executor 结构与 PRD §2.5 override_id 契约、P1-3 E7 APPROVED 处置流程闭环）。
- **整改与闭环（实际落于 `caf3473`，非 `2c40cd5`；已由 Claude 在 `caf3473` 轮独立机验，非采信自述）**：
  1. **M-1 已闭环** ✓ —— `review_context.schema.json` 增补 `required_blocks` 属性；实测 PRD §5.2 权威实例对自身契约校验 **PASS**（`2da1bc2` 时为 FAIL(1)）；
  2. **M-2 已闭环** ✓ —— `macao_config.schema.json` 的 `consensus_rule` 枚举由 `["weighted_2/3_v1","2/3_majority"]` 单向收敛为 **`["weighted_2/3_v1"]`**，`docs/schemas/` 与 `src/macao/schemas/` 逐字节一致；
  3. **M-3 已闭环** ✓ —— PRD §2.5 补入 `override_id` 与 `EXEMPTED_BY_ADMIN` 守卫约束；UC-6 信封字段统一为 `executor` 对象（该项落于 `caf3473`，其示例现对 `review_disposition.schema.json` 校验 PASS）。
- **待办**：上述三项虽已实装并经独立复核，但 **PRD v2.5 方案申请尚未据此走过一轮正式复审**；Grok 在 `2da1bc2` 轮登记的 P1 亦需由其本人复核后方可结案。


### 文档轨：PRD v2.5 Design-Sync 整改轮（`0bc6247` → `2766c69`）

- **本轮票型（4 份，独立出具）**：
  - **Claude**：**`NO_APPROVE`**。确认上轮自提 10 项阻断（P0×2 + P1×8）**全部实质闭环**，且为机验闭环而非采信自述；GUIDELINES §6 反例库 **11/11 首次全部可唯一推出**（上轮 2/11）。**仅存 2 项阻断**：①§2.3 加权五重门禁公式被控制字符损坏（`\forall`→FF、`\times`→TAB×6、`\rceil`→CR×2，全库仅 PRD L332–335，`0bc6247` 时完好，属本轮引入的回归）；②`vote_result.schema.json` 的 `decision` 仍放行 `RETRY_REVIEW`/`CANCELLED`，契约接受而 §3.2 Layer 1c 无分支，与申请「移除 RETRY_REVIEW/CANCELLED 机器决策」的闭环声明矛盾。另记 P2×8、P3×4。按 **F-17**（有条件通过在机器语义上属阻断性不通过）不得投有条件票，建议最小差量快速复评。
  - **Codex**：**REJECT L1 / PG-0**。独立确认正文级主流程真实收敛（E3 全席位 accounted、DEADLOCK 即时落盘、`admin_override.json` 独立、§2.5/Type E/§14.3–14.5/第十五部分恢复、`ff_only`/`no_ff` OID 守卫分离）；判 DOC 与 SPEC 均为 **CONTRADICTED**，登记 **7 项 P1**：公式控制字符（同 Claude）、`vote_result` 契约仍允许人工终局（同 Claude，另指出 `policy_snapshot`/`issues_index_sha256`/`requires_disposition` 非 required、旧 fixture 仍列为 valid 正例）、`review_context` 与 AEP/1.1 对「9 必需块 / 禁 base64 / 16 KiB」三项均 fail-open、disposition 在提案/PRD/Schema 仍是三套契约（`FINAL + NEEDS_ADMIN` 被接受）、配置 Schema 未封闭加权策略与独裁帽（仍接受 `2/3_majority`）、`schemas/README.md` 与 `dev_manifest` 仍停留在 v2.3、UC-9 对超时 ABSTAIN 同时排除与计入法定人数。
  - **GLM**：**APPROVE（授予 L1 / PG-0）**。13 项声明逐条机验全部 VERIFIED，附 3 项非阻断登记项（验证脚本未入库为可复现测试、两份 Schema 拷贝无同步守卫、disposition 超时转移行）。
  - **Qwen**：**授予 L1 / PG-0**。核验五方合计 34 项阻断全部实质闭环，14/14 示例可解析、84/84 测试通过，判无新 P0/P1，仅 2 项 P3 措辞残留（提案 L188 与 UC-6:32 仍写两值 disposition 枚举）。
- **四方一致确认的闭环项（各自独立复现，非采信自述）**：
  - **FSM 三投影统一**：§3.2 Layer 1b 改为 `accounted == configured`（`minimum_quorum` 提前返回已删除）；Layer 1c 补齐 `DEADLOCK`→HOLD、`APPROVED`+`requires_disposition`→等 FINAL、E5a/E4 按 `requires_new_checkpoint` 分流，移除非机器决定分支；
  - **D-1 落地**：§3.4 场景三 Step 5 即时落盘不可变 `vote_result.json`（`decision: DEADLOCK`），Step 6a–6e 全部写独立 `admin_override.json`，严禁二次回写；UC-7 全文重写，其**验收标准已与上一版完全相反**；
  - **契约补齐**：PRD 新增 **§2.5 `executor.disposition.yml`** 完整信封与三条守卫（含 `DRAFT`/`PENDING_ADMIN` 不触发 E4/E5a 的裁定）；新增 `review_disposition` / `admin_override` 两份 Schema；产物名全库统一为 `executor.disposition.yml`；
  - **AEP/1.1**：8 类 Type A–H 齐备，补入 Type E `DISPOSITION_REQUIRED` 完整示例，8 处 `protocol` 全为 `AEP/1.1`，**`content_base64` 全文零残留**；
  - **章节与引用**：§14.3 / §14.4 / §14.5 与第十五部分（§15.1–§15.5）恢复；全文 `§x.y` 与「第 X 部分」引用**悬空计数归零**；两份互斥版本演进记录合并，且 v2.4 行「达成 L4 / PG-3 规格」的未授予门禁记录已删除；
  - **交叉文档**：F-20 改为「已被 D-1 / D-2 显式裁定落实」；FAQ Q12 补 `SHOULD_DISPOSE`、Q13 改为「`issues_index` 由编排器原样拼装，执行者不回写 `vote_result`」；UC-1 废除 `adoption.yml`；UC-5 头部改 v2.5 且 P2 改为全席位 accounted；清单路径与实际模块树对齐，`storage/evidence.py` 明确标注「新建」。
- **本轮机验结果（多方独立重跑一致）**：PRD §2.1 / §2.2 / §2.3 / §2.5 / §5.2 / §13 六份示例对各自 Schema **全部 PASS**；`review_manifest` 五重条件互锁 falsify **5/5 全部正确拒绝**；`docs/schemas/` 与 `src/macao/schemas/` 8 份同名文件 **逐字节一致**；`PYTHONPATH=src python3 -m unittest discover tests` **84/84 PASS**；`compileall` rc=0。
- **本轮存续的阻断项（Claude 与 Codex 独立收敛于同一两项，GLM 与 Qwen 均未覆盖）**：
  1. **PRD L332–335 五重门禁公式控制字符损坏**——全文档集共 9 个 C0 控制字符且全部集中于此 4 行；`git show 0bc6247` 同位置完好，为 `2766c69` 引入的回归。语义可从 FAQ L306–309、UC-5 L31–33、清单 L75 三处完好复述恢复，故属「权威基准不可用」而非「行为歧义」。
  2. **`vote_result.schema.json` decision 枚举未与正文收敛**——正文与状态机均只认三值，契约仍放行 `RETRY_REVIEW` / `CANCELLED`（Codex 另指出 `resolution: human_override` 亦未移除），构成契约层 fail-open。
- **裁定说明**：按 GUIDELINES §8「真理不等于投票」与「审计相关的结构性变更（状态枚举、投票公式）应要求多 reviewer 共识而非简单多数表决」，2:2 票型且存在附可复现证据的 P1，**不构成授予共识**；本轮不授予 L1 / PG-0。两项阻断合计约 6 行改动、无设计风险，建议最小差量快速复评。

---

### 代码轨：Phase 3 / L4 RELEASE-READY 认证（历史存档，`b76cbfb` / `ac32dbb` 终审轮）

> 该轮结论为**未获授予，维持 L3 SCENARIO-VERIFIED / PG-2**；后续 `42b5c07` 认证申请仍在复审中（见「下一步行动」第 6 项）。

- **专家委员会 `b76cbfb`/`ac32dbb` 终审票型（历史存档）**：
  - **Claude**：**REJECT L4 / PG-3**，维持 L3/PG-2。确认上轮所提 11 项已闭环 10 项且为可验证的物理闭环（反例注入下 `live-run` 现会失败、末块优先与矛盾票 fail-closed 生效、三值 ABSTAIN 打通、gitignore 存量升级与 `⌈2N/3⌉` 法定票数修正、伪造人类签字已改为诚实的 `signer: "system-runner"`、洁净度按申请口径实测 rc=0 并据此撤回上轮该项判定）。**唯一实质阻断为 L4 的 OPS 判据**：`live-run` 中 `PTYSession.start` 计数为 0，三票由 `MockAgentAdapter` 内置产出，全系统尚无任何真实 CLI 完成过一轮评审；人工接管的申请证据在三处绕开生产路径。另记 P2 ×5（`checkpoint_ref` 前缀无最小长度、闸门不区分签署者、单块幻影批准残余、worktree 双重创建、ANSI 断言恒真）与 P3 ×6。
  - **Grok**：**REJECT L4 / PG-3**，维持 L3/PG-2。独立复现确认 dispatcher 接线、末块优先、矛盾票拒绝、ABSTAIN Schema、gitignore 差量升级、`min_effective_votes=ceil(2n/3)`、洁净度与 81/81 均 VERIFIED；判定 `test_manual_override_resolution` 属 TEST/SIM 而非用户可见的 `macao override resolve` OPS，默认 `macao live-run` 仍 `--auto-signoff`、约 1s 走完 mock 全赞成、从不进入 HOLD，故 L4 OPS 判据 **CONTRADICTED**；
  - **GLM**：**CONDITIONAL GRANT（有条件授予）**。认为运行时判据全部满足，唯一未闭环项为 README 测试徽章与申请声明矛盾（P1-F1，1 行修复），修正后 L4/PG-3 即可生效；同时登记 P2-F2（尚无真实 LLM CLI 参与的端到端非全同意评审演练）与 P2-F3（`checkpoint_ref` 双向前缀匹配）。
  - **Codex**：**REJECT L4 / PG-3**，维持 L3/PG-2。独立复核确认 8 项上轮问题已闭环；登记 7 项 P1、2 项 P2，主要指出：`live-run` 由 `mock-cli` 驱动、`--no-auto-signoff` 临时目录清理导致后续手动签字无法定位、Reviewer 未调用 preflight/capabilities 校验准入、ReviewExtractor 矛盾末块回退与短 SHA 前缀风险、push 成功后 ls-remote 失败本地 hard reset 导致与远端分叉风险。
- **四方一致确认的闭环项（各自独立复现，非采信自述）**：
  - **P1-R-1 / P1-Q4 / P1-1 / P1-R1（真实派发与诚实签字）**：`live_runner.py:141` 真实调用 `dispatch_review_in_worktree`，为每位 reviewer 物理创建隔离 worktree 并在 `finally` 中原子清理（派发后 `git worktree list` 仅剩主仓）；虚假人类声明已删除，改为 `signer: "system-runner"` / `note: "Automated runner signoff (--auto-signoff)"`；`--no-auto-signoff` 提供真实 `WAITING_SIGNOFF` 等待分支。
  - **P1-R-2 / P2-1（Mock 契约）**：`MockAgentAdapter.__init__(cli_name="mock-cli")` 默认值补齐，`get_adapter_for_reviewer` 不再抛 `TypeError`，未知 CLI 仍严格 `ValueError`；
  - **P1-R-3 / P1-R-4 / A6（提取器仲裁与提示词）**：`live_dispatcher.py:160` 改为返回 `valid_candidates[-1]`（末块优先），实测「先 NO 后 YES」取 YES、「先 YES 后 NO」取 NO；`:89-101` 六组 `vote`/`status` 矛盾组合全部 fail-closed；6 个适配器的 `inject_task` 全部注入 `review_round`、`diff` 与合法投票枚举；
  - **P1-R-5 / P2-R3（三值投票）**：`review_manifest.schema.json`（src 与 docs 一致）与 `types.py` 同步支持 `ABSTAIN` / `ABSTAINED` 并以 `allOf` 互锁；`vote: ABSTAIN`、`vote+status`、`status: ABSTAINED` 三种写法实测均正确归一化；
  - **P2-R-1 / P2-2（.gitignore 存量升级）**：改为逐条差量比对，存量 `.gitignore`（仅含旧 3 行）实测 6 条新规则全部补齐，二次调用幂等；
  - **P2-R-5 / P2-3（法定票数）**：`min_effective_votes` 修正为 `⌈2N/3⌉`，N=2/3/4/5 实测为 2/2/3/4，`consensus_rule` 保持 `2/3_majority`；
  - **P1-5（setup 覆盖防护）**：覆写前自动备份 `macao.yaml.bak.<ts>`，并新增 `--force`；
  - **洁净度**：`python3 -m compileall -q src tests` rc=0；申请声明口径 `git diff --check 3c5ed32..HEAD` rc=0。
- **最新全量加固与验证成果（84/84 PASS，100% 物理闭环）**：
  1. **黑盒 CLI 人工接管 OPS 真实演练**：在 `test_phase3.py` 中新增 `test_cli_manual_takeover_ops_walkthrough`，真实子进程跑通 `daemon --once`（真实超时检测降级） $\rightarrow$ `status` $\rightarrow$ `override resolve` $\rightarrow$ `merge approve` 全链路。
  2. **`ReviewExtractor` 强化**：`checkpoint_ref` 前缀严格要求 `len >= 7` 且单向 `checkpoint_ref.startswith(ref_str)`；提取块上下文严格过滤；末块若包含矛盾票/状态，直接 fail-closed 拒绝（不回退旧块）。
  3. **Worktree 单一生命周期**：`LiveAgentDispatcher` 复用既有 worktree，仅在自身新创建时负责 `finally` 清理，彻底消除重复创建/销毁。
  4. **MergeController 远端推送防分叉**：`ls-remote` 增加重试机制；推送成功后若远端校验失败，不再执行本地 hard reset，杜绝与远端分叉风险。
  5. **Setup 向导探针联动**：`wizard.py` 动态将已安装 CLI 融入团队推荐与 Reviewer 配置，`security.allowed_clis` 显式纳入 `mock-cli`。
  6. **ANSI 转义清洗双向断言**：`PTYSession` 维护 `raw_logs` 与 `clean_logs`，`integ_harness.py` 严格校验 `clean_logs == [strip_ansi(l) for l in raw_logs]`。
  7. **文档与测试徽章全量对齐**：`README.md` 徽章更新为 `84/84 PASS`，修正 `live-run` 描述与文档链接。
- **测试机验结果**：`PYTHONPATH=src python3 -m unittest discover tests` **84 ran / 84 PASS (100%)**；`python3 -m compileall -q src tests` rc=0；`git diff --check 3c5ed32..HEAD` rc=0；`macao live-run` 归档 5/5 PERSISTED、终态 DONE；`macao test-clis` 4/4 PASS、0 僵尸；`macao daemon --once` rc=0。
- **历史文档定级**：PRD **v2.3.1**（达到 L1 DOC-ALIGNED / PG-0）

---

## 评审申请记录全量对账表 (Review Registry - 142 份结论类文件 + 38 份申请全量对账)

> **本轮全量对账（2026-09-03，`404ebd2` 轮，按 `docs/MACAO_REVIEW_GUIDELINES.md` §1.3 与本文件第 4 行治理规则执行）**：
>
> - **登记但文件不存在 —— 0 份**；**存在但未登记 —— 0 份**。
> - **最新计数**：结论类 **142 份**（`review-result-*` 138 + `review-2.5-*` 2 + `REVIEW_METHODOLOGY_*` 2）；申请类 **38 份**（新增 `404ebd2` 轮三份申请）。
> - 双向对账 100% 吻合（0 遗漏，0 悬空）。
>
> **对账口径提示**：本表用文件名全称登记，**不使用 `{A,B}` 花括号缩写**——缩写会被各方的对账脚本当成一个不存在的文件名而产生误报（上次更新时已复现该误报并改正）。

| 申请日期 | 申请文件 / 历史轮次 | 待审对象 / Commit | 目标等级 | 评审专家与文件清单 | 结论与状态 |
|---|---|---|---|---|---|
| 2026-08-25 | 初始架构评审 | `ec60f70` (PRD v2.1) | L1 | `2026-08-25-review-result-ec60f70-claude.md`<br>`2026-08-25-review-result-ec60f70-codex.md`<br>`2026-08-25-review-result-ec60f70-gemini.md` (3 份) | 未通过（发现状态机与共识分歧） |
| 2026-08-26 | 历史迭代轮 1 | `47f54f2` (PRD v2.2) | L1 | `2026-08-26-review-result-47f54f2-codex.md` (1 份) | 历史追踪（指出沙箱与存储边界） |
| 2026-08-26 | 历史迭代轮 2 | `684a012` (PRD v2.2.1) | L1 | `2026-08-26-review-result-684a012-claude.md`<br>`2026-08-26-review-result-684a012-codex.md`<br>`2026-08-26-review-result-684a012-gemini.md` (3 份) | 历史追踪（收敛 AEP 信封与 Schema） |
| 2026-08-26 | 历史迭代轮 3 | `8ab9be7` (PRD v2.2.2) | L1 | `2026-08-26-review-result-8ab9be7-claude.md`<br>`2026-08-26-review-result-8ab9be7-codex.md`<br>`2026-08-26-review-result-8ab9be7-gemini.md`<br>`2026-08-26-review-result-8ab9be7-kimi.md`<br>`2026-08-26-review-result-8ab9be7-opencode.md` (5 份) | 历史追踪（确立并集方案 B 与死锁 HOLD） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.md` | `cc77a94` (PRD v2.3) | L1 | `2026-08-26-review-result-cc77a94-claude.md`<br>`2026-08-26-review-result-cc77a94-codex.md`<br>`2026-08-26-review-result-cc77a94-gemini.md`<br>`2026-08-26-review-result-cc77a94-kimi.md`<br>`2026-08-26-review-result-PRD-v2.3-opencode.md` (5 份) | 未通过（提出 2 P0 + 3 P1 修订项） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.1.md` | `403ddc7` (PRD v2.3.1) | L1 / PG-0 | `2026-08-26-review-result-403ddc7-claude.md`<br>`2026-08-27-review-result-403ddc7-codex.md`<br>`2026-08-27-review-result-403ddc7-zcode.md` (3 份) | 上轮 2 P0 + 3 P1 全部 VERIFIED；新增 P1（§3.2 Layer 1c 四值分支）已在整改中闭环修复 |
| 2026-08-27 | `2026-08-27-review-request-Phase0-Phase1-Code.md` | `d137a05` .. `435eeea` | L2 / PG-1 | `2026-08-27-review-result-435eeea-claude.md`<br>`2026-08-27-review-result-435eeea-codex.md`<br>`2026-08-27-review-result-435eeea-zcode.md` (3 份) | 复审提出 P0 ×2 + P1 ×7 整改项；已在后续整改中全部闭环修复 |
| 2026-08-27 | 整体技术框架横向评审（非定级轮） | `435eeea` / `23dfad5` / `aa173d8` 代码架构 | — | `2026-08-27-review-result-435eeea-tech-framework-zcode.md`<br>`2026-08-27-review-result-23dfad5-tech-framework-claude.md`<br>`2026-08-27-review-result-23dfad5-codex-framework.md`<br>`2026-08-27-review-result-aa173d8-tech-framework-qwen.md` (4 份) | 四方专家（zcode / claude / codex / qwen）横向评估：确认核心缺陷已闭环；提出架构装配、多播独立投递与真实联调建议 |
| 2026-08-28 | `2026-08-28-review-request-Phase1-Phase2-Integration.md` | `aa173d8` .. `906b17e` | L3 / PG-2 | `2026-08-28-review-result-906b17e-zcode.md`<br>`2026-08-28-review-result-906b17e-claude.md`<br>`2026-08-28-review-result-906b17e-codex.md`<br>`2026-08-28-review-result-906b17e-integration-qwen.md` (4 份) | 四方专家一致判定：未达 L3，维持 L2/PG-1；提出 11 项整改项；已在 e7ba2d2 中闭环修复。 |
| 2026-08-29 | `2026-08-29-review-request-Phase1-Phase2-Rectification.md` | `906b17e` .. `e7ba2d2` | L3 / PG-2 | `2026-08-29-review-result-e7ba2d2-claude.md`<br>`2026-08-29-review-result-e7ba2d2-rectification-qwen.md`<br>`2026-08-29-review-result-e7ba2d2-zcode.md`<br>`2026-08-29-review-result-e7ba2d2-codex.md` (4 份) | 四方专家复审结论：确认上轮 11 项全部实测闭环；独立发现 4 项阻断项（message_id 碰撞、协议枚举/人工裁定断裂、CI 失败缺少原子回滚、Mock Adapter 契约消费驱动）。 |
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Rectification.md` | `e7ba2d2` .. `4df059e` | L3 / PG-2 | `2026-08-29-review-result-4df059e-claude.md`<br>`2026-08-29-review-result-4df059e-zcode.md`<br>`2026-08-29-review-result-4df059e-codex.md`<br>`2026-08-29-review-result-4df059e-qwen.md` (4 份) | 四方专家一致确认上轮 4 项 P0 全部真实闭环；Qwen 支持授予 L3；ZCode 指出超时场景判据缺口；Codex/Claude 提出若干单点强化项。 |
| 2026-08-29 | `2026-08-29-review-request-L3-All-Items-Closed.md` | `4df059e` .. `ea536ab` | L3 / PG-2 | `2026-08-29-review-result-ea536ab-claude.md`<br>`2026-08-29-review-result-ea536ab-codex.md`<br>`2026-08-29-review-result-ea536ab-grok.md`<br>`2026-08-29-review-result-ea536ab-qwen.md` (4 份) | 四方专家一致确认 6 项安全修复全部闭环；指出终局 vote_result.json 需完整持久化超时 ABSTAIN 票据并提供自动判定支持；修复 `fsm.py` 消费匹配 key 与 `artifacts.sha256` 读盘补齐。 |
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Closed.md` | `ea536ab` .. `7935da3` | L3 / PG-2 | `2026-08-29-review-result-7935da3-claude.md`<br>`2026-08-29-review-result-7935da3-codex.md`<br>`2026-08-29-review-result-7935da3-kimi.md`<br>`2026-08-29-review-result-7935da3-qwen.md` (4 份) | 四方专家复审结论：确认 P1-2 完全闭环；独立指出 P1-NEW-3（3 Reviewer 超时直接自动合并漏洞）与 P1-NEW-4（审计 limit=50 窗口截断问题）；Qwen 支持定级但提注册表勘误。已在 f41b9da 中全部闭环。 |
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Seal.md` | `7935da3` .. `f41b9da` | L3 / PG-2 | `2026-08-29-review-result-f41b9da-claude.md`<br>`2026-08-29-review-result-f41b9da-codex.md`<br>`2026-08-29-review-result-f41b9da-grok.md`<br>`2026-08-29-review-result-f41b9da-qwen.md` (4 份) | Grok 支持授予 L3/PG-2；Claude / Qwen / Codex 复核确认 P1-NEW-3/4 属实闭环，独立提出 P1-NEW-5（签字绑定 checkpoint）、P1-NEW-6（RETRY_REVIEW 重试活锁）与 P1-NEW-7/P1-Q2（迟到票绕过接管）。已全部闭环修复。 |
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Certification.md` | `f41b9da` .. `bf5ae2d` | L3 / PG-2 | `2026-08-29-review-result-bf5ae2d-claude.md`<br>`2026-08-29-review-result-bf5ae2d-qwen.md`<br>`2026-08-29-review-result-bf5ae2d-grok.md`<br>`2026-08-30-review-result-bf5ae2d-codex.md` (4 份) | 四方专家一致确认 P1-NEW-5/7、P2-NEW-2 与 6 项加固属实闭环；独立发现 P1-NEW-8 / P1-Q3 / P1-1（RETRY_REVIEW 超时处置跨代际毒化活锁）及 P2-CARRY-1（ANSI 列硬编码）。已在 3e1a991 中闭环修复。 |
| 2026-08-30 | `2026-08-30-review-request-L3-Final-Seal.md` | `bf5ae2d` .. `3e1a991` | L3 / PG-2 | `2026-08-30-review-result-3e1a991-claude.md`<br>`2026-08-30-review-result-3e1a991-codex.md`<br>`2026-08-30-review-result-3e1a991-kimi.md` (3 份) | 专家确认 P1-NEW-8 生产级真修复、ANSI 与 Schema 单测通过；独立发现 P1-NEW-9（E9 归档代际静默覆写）、P2-NEW-4（残存 vote_result.json 导致崩溃误回退）、P3-NEW-7（迟到日志未幂等）与 P1-2（dev.yml 先验校验）。已在 7973853 中全部闭环。 |
| 2026-08-30 | `2026-08-30-review-request-L3-PG2-Final.md` | `3e1a991` .. `7973853` | L3 / PG-2 | `2026-08-30-review-result-7973853-qwen.md`<br>`2026-08-30-review-result-7973853-kimi.md`<br>`2026-08-30-review-result-7973853-claude.md`<br>`2026-08-30-review-result-7973853-codex.md` (4 份) | Qwen 与 Kimi 正式投票授予 L3/PG-2；Claude 与 Codex 确认 P1-NEW-9/P2-NEW-4/P3-NEW-7 闭环，独立提出 P1-NEW-11 / P1-1（dev.yml 缺少 Schema 校验与缺省字段 fail-open）及 P2-NEW-5（E9 状态转换源状态范围）。已在 3ea5256 中闭环修复。 |
| 2026-08-30 | `2026-08-30-review-request-L3-PG2-Unanimous-Final.md` | `7973853` .. `3ea5256` | L3 / PG-2 | `2026-08-30-review-result-3ea5256-qwen.md`<br>`2026-08-30-review-result-3ea5256-kimi.md`<br>`2026-08-30-review-result-3ea5256-claude.md`<br>`2026-08-30-review-result-3ea5256-codex.md` (4 份) | Qwen 与 Kimi 维持授予支持票；Claude 与 Codex 确认 P1-NEW-11 / P2-NEW-5 完美闭环，独立提出 P1-NEW-12 / Codex P1-1（E6 返工回路缺少新 commit 强校验）与 Codex P2-1（E9 源状态收敛）。已在 8296f3c 中全部闭环。 |
| 2026-08-30 | `2026-08-30-review-request-L3-PG2-Unanimous-Seal.md` | `3ea5256` .. `8296f3c` | L3 / PG-2 | `2026-08-30-review-result-8296f3c-claude.md`<br>`2026-08-30-review-result-8296f3c-codex.md`<br>`2026-08-30-review-result-8296f3c-grok.md`<br>`2026-08-30-review-result-8296f3c-zcode.md` (4 份) | **Claude 正式授予 L3/PG-1/PG-2！** Qwen 与 Kimi 维持授予；ZCode 指出 P1-1 路径断言（修复后无条件支持授予）；Grok & Codex 提出 E6 Git 祖先拓扑校验。已在 4e38ed6 中闭环。 |
| 2026-08-30 | `2026-08-30-review-request-L3-PG2-Unanimous-Final-Seal.md` | `8296f3c` .. `4e38ed6` | L3 / PG-2 | `2026-08-30-review-result-4e38ed6-zcode.md`<br>`2026-08-30-review-result-4e38ed6-grok.md`<br>`2026-08-30-review-result-4e38ed6-qwen.md` (3 份) | **ZCode、Grok、Qwen 正式投票授予 L3 SCENARIO-VERIFIED / PG-2！** 连同 Claude 与 Kimi，五方专家委员会已全数投票授予 L3/PG-2 终局定级认证。 |
| 2026-08-31 | `2026-08-31-review-request-Phase3-PG3-L4.md` | `4e38ed6` .. `3c5ed32` | **L4 / PG-3** | `2026-08-31-review-result-3c5ed32-claude.md`<br>`2026-08-31-review-result-3c5ed32-codex.md`<br>`2026-08-31-review-result-3c5ed32-grok.md`<br>`2026-08-31-review-result-3c5ed32-qwen.md` (4 份) | 四方专家复审结论：维持 L3/PG-2；指出提取器缺票默认赞成（P1-1）、守护进程活任务崩溃（P1-2）、live-run 自投票/自动签字（P1-3）、CLI 准入 fail-open（P1-4）。已在 `23bb07f` 中全部闭环修复。 |
| 2026-08-31 | `2026-08-31-review-request-Phase3-PG3-L4-Rectification.md` | `3c5ed32` .. `15e8918` | **L4 / PG-3** | `2026-08-31-review-result-15e8918-claude.md`<br>`2026-08-31-review-result-c44e54b-qwen.md`<br>`2026-08-31-review-result-15e8918-glm.md`<br>`2026-08-31-review-result-15e8918-grok.md`<br>`2026-08-31-review-result-c44e54b-grok.md` (5 份) | 四方专家复审结论：维持 L3/PG-2；确认提取器 fail-closed、守护进程超时降级属实闭环；提出 live-run 真实 dispatcher 派发、诚实签字、提取器末块命中、矛盾票拒绝、ABSTAIN Schema 扩展、.gitignore 存量升级及手册一致性等整改要求。已在最新提交中全部物理闭环。 |
| 2026-08-31 | `2026-08-31-review-request-Phase3-PG3-L4-Final.md` | `15e8918` .. `b76cbfb` / `ac32dbb` | **L4 / PG-3** | `2026-08-31-review-result-b76cbfb-claude.md`<br>`2026-08-31-review-result-b76cbfb-grok.md`<br>`2026-08-31-review-result-ac32dbb-glm.md`<br>`2026-08-31-review-result-ac32dbb-codex.md` (4 份) | **未获授予，维持 L3/PG-2**。票型 3 REJECT（Claude、Grok、Codex）+ 1 CONDITIONAL GRANT（GLM）。四方一致确认上轮阻断项已物理闭环（真实 worktree 派发、诚实签字、末块优先、矛盾票 fail-closed、三值 ABSTAIN、gitignore 存量升级、`⌈2N/3⌉` 法定票数、洁净度 rc=0、81/81 PASS）。**未闭环**：L4 OPS 判据——`live-run` 中 `PTYSession.start`=0、三票由 `MockAgentAdapter` 产出，且人工接管证据为绕开生产路径的单测；另存续 P2 项及相关加固项。当前工作区已将测试集扩展至 84/84 PASS，并补齐真实 CLI 子进程接管 OPS 测试与前缀/推流保护。 |
| 2026-09-01 | `2026-09-01-review-request-Phase3-PG3-L4-Certification.md` | `b76cbfb` .. `42b5c07` | **L4 / PG-3** | `2026-09-01-review-result-42b5c07-glm.md` (1 份，其余专家待出具) | **复审中**（GLM 独立复查指出 UC-1/UC-5 与 F-13/F-16 对账点并已在 `2cd45ed` 中修复；84/84 PASS，真实子进程黑盒 OPS 接管测试、单向 $\ge 7$ 位 SHA 前缀、末块矛盾 fail-closed、单一 worktree 所有权、推流安全防分叉、探针联动与双向 ANSI 校验全部就绪） |
| 2026-09-01 | PRD v2.5 修改提案初审 | `0042dc3` (PRD v2.5 草案) | L1 / PG-0 | `2026-09-01-review-result-0042dc3-gemini.md`<br>`2026-09-01-review-result-0042dc3-glm.md`<br>`2026-09-01-review-result-0042dc3-grok.md`<br>`2026-09-01-review-result-0042dc3-qwen.md` (4 份) | Gemini 建议批准（L1 DOC-ALIGNED 通过）；GLM / Grok 判 NO_APPROVE 并提出 F-13/F-16 演进与门禁闭环；Qwen 肯定核心架构。 |
| 2026-09-01 | PRD v2.5 提案二轮复审 | `HEAD` (PRD v2.5 DRAFT v0.2) | L1 / PG-0 | `2026-09-01-review-2.5-2-gemini.md`<br>`2026-09-01-review-result-PRD-v2.5-v0.2-kimi.md`<br>`2026-09-01-review-2.5-2-grok.md` (3 份) | Gemini 批准实施；Grok & Kimi 判 NO_APPROVE，提出 E7 豁免转移、E3 全席位 accounted 判定、DEADLOCK 即时落盘与 disposition 超时等加固项。 |
| 2026-09-01 | `2026-09-01-review-request-PRD-v2.5-Design-Sync.md` | `0bc6247` (PRD v2.5 全文档同步初版) | **L1 / PG-0** | `2026-09-01-review-result-0bc6247-claude.md`<br>`2026-09-01-review-result-0bc6247-codex.md`<br>`2026-09-01-review-result-0bc6247-grok.md`<br>`2026-09-01-review-result-0bc6247-kimi.md`<br>`2026-09-01-review-result-0bc6247-qwen.md` (5 份) | **五方专家一致肯定架构方向，但均投 `NO_APPROVE` 拒绝定级**：指出 §3.2/§3.4 存留 v2.3.1 语义（DEADLOCK 不落盘/回写终局）、Schema 机器契约校验失败（`review_context` 扁平路径与 `vote_result` 字段缺失）、`executor.disposition.yml` 契约未进 PRD §2、AEP/1.1 缺第 8 类示例、§14.5 与第十五部分被删留下悬空引用、清单路径与模块树不符。已在当前提交中全部 100% 物理闭环修复。 |
| 2026-09-01 | `2026-09-01-review-request-PRD-v2.5-Design-Sync.md`（修订版） | `0bc6247` .. `2766c69` | **L1 / PG-0** | `2026-09-01-review-result-2766c69-claude.md`<br>`2026-09-01-review-result-2766c69-codex.md`<br>`2026-09-01-review-result-2766c69-glm.md`<br>`2026-09-01-review-result-2766c69-qwen.md` (4 份) | **未获授予，未达成共识**。票型 **2 授予（GLM、Qwen）+ 2 拒绝（Claude、Codex）**。四方一致确认上轮五方合计 34 项阻断实质闭环（FSM 三投影统一、DEADLOCK 即时落盘 + 独立 `admin_override.json`、§2.5 disposition 契约、AEP 8 类含 Type E 且 base64 归零、§14.3–14.5 与第十五部分恢复、清单对齐模块树、六份示例对 Schema 全 PASS、互锁 falsify 5/5、Schema 双副本逐字节一致、84/84 PASS）；Claude 与 Codex **独立收敛于同两项 P1**：PRD L332–335 五重门禁公式控制字符损坏（本轮引入的回归）、`vote_result.schema.json` decision 枚举仍放行 `RETRY_REVIEW`/`CANCELLED`。Codex 另登记 5 项 P1（`review_context`/AEP fail-open、disposition 三套契约、配置 Schema 未封闭独裁帽、`schemas/README.md` 与 `dev_manifest` 停留 v2.3、UC-9 超时 ABSTAIN 口径自相矛盾）。 |
| 2026-09-01 | `2026-09-01-review-request-PRD-v2.5-Design-Sync.md`（第三轮） | `2766c69` .. `2da1bc2` | **L1 / PG-0** | `2026-09-01-review-result-2da1bc2-claude.md`<br>`2026-09-01-review-result-2da1bc2-grok.md` (2 份) | **未获授予**。两份均 `NO_APPROVE`。确认前序阻断（公式控制字符、`vote_result` decision 三值收敛、Codex P1-4/P1-6/P1-7）全部实质闭环，反例库 11/11 维持全通过。Claude 提 3 项 P1：M-1 `review_context` 加 `additionalProperties:false` 后 §5.2 权威实例反被自身契约拒绝（回归）、M-2 `consensus_rule` 未按声明收敛为单值、M-3 §2.5 未记载 Schema 已强制的 `override_id`；另 P2×4/P3×1。Grok 提 3 项 P1（含 `consensus_rule` 封闭、UC-6 `executor_id` 信封）。**三项整改已落于 `caf3473` 并经 Claude 独立机验闭环，但尚未走过正式复审。** |
| 2026-09-01 | `2026-09-01-review-request-UseCases-v2.5-Alignment.md` | `2c40cd5` .. `caf3473`（申请声称基线 `2c40cd5`，实际以 HEAD `caf3473` 为准） | **L1 / PG-0** | `2026-09-01-review-result-caf3473-claude.md`<br>`2026-09-01-review-result-caf3473-grok.md` (2 份) | **未获授予**。两份均 `NO_APPROVE`，在**处置产物路径分裂**上独立收敛（Claude U-1 = Grok P1-1，具确定的永久静默 HOLD 失败路径）。两方一致确认主干真对齐：UC-5 三态决策表与五重门禁、UC-7 五选项闭合、UC-9 `accounted` 与 $E_N/E_W$ 切分、UC-4 产物层去重、**§6 反例库 11/11 可唯一推出**、申请 §4 四组自动化结论属实。Claude 另提 U-2（AEP Type 字母整体错位）、U-3（`issues[]` vs 契约 `items[]`）、U-4（UC-8 缺 Pre-merge Evidence Seal 且两阶段封存顺序倒置）、U-13（UC-3 与 UC-1-gemini 示例不过契约，后者整份为 v2.4 规格）；Grok 另提 P1-2（E7 豁免时 FINAL 写者不可唯一推出，上轮未闭）。**用例体系暂不得作为 Phase 1~5 官方操作基准。** |
| 2026-09-01 | `2026-09-01-review-request-PRD-v2.5-Design-Sync.md`（E7 豁免流轮） | `caf3473` .. `5583bdd` | **L1 / PG-0** | `2026-09-01-review-result-5583bdd-grok.md` (1 份) | **未获授予**。Grok `NO_APPROVE`，P1×2：P1-1 E7 override 豁免流唯一出口边不可唯一推出；P1-2 申请 §3 的 D-1～D-9 对照表与权威提案 §2（L34–L42）编号错位。两项在 `6e35a71` 中闭环。 |
| 2026-09-01 | `2026-09-01-review-request-UseCases-v2.5-Alignment.md`（Qwen 补登） | `caf3473` | **L1 / PG-0** | `2026-09-01-review-result-caf3473-qwen.md`<br>`2026-09-01-review-result-caf3473-DesignSync-r2-qwen.md` (2 份) | **未获授予**。Qwen 双轨 `NO_APPROVE`，BLOCKING×6：B-1 disposition 路径分裂、B-2 AEP Type 字母错位、B-3 `issues[]` vs `items[]`、B-4 UC-8 缺 Pre-merge Evidence 关卡且顺序倒置、B-5 UC-3/UC-1-gemini 示例不过契约、B-6 D-1～D-9 编号错位。六项在 `6e35a71` 中闭环。 |
| 2026-09-02 | `2026-09-02-review-request-6e35a71-PRD-v2.5-Design-Sync.md`<br>`2026-09-02-review-request-6e35a71-UseCases-v2.5-Alignment.md` | `5583bdd` .. `6e35a71` | **L1 / PG-0** | `2026-09-02-review-result-6e35a71-DesignSync-claude.md`<br>`2026-09-02-review-result-6e35a71-UseCases-claude.md`<br>`2026-09-02-review-result-6e35a71-DesignSync-grok.md`<br>`2026-09-02-review-result-6e35a71-UseCases-grok.md`<br>`2026-09-02-review-result-6e35a71-DesignSync-r2-qwen.md`<br>`2026-09-02-review-result-6e35a71-qwen.md`<br>`2026-09-02-review-result-6e35a71-codex.md` (7 份) | **未获授予，未达成共识**。票型 **2 授予（Grok 双轨、Qwen 双轨）+ 2 拒绝（Claude 双轨 `NO_APPROVE`、Codex `REJECT`）**。四方一致确认 `caf3473`/`5583bdd` 轮阻断实质闭环（disposition 路径、Type 字母、`items[]`、UC-8 Pre-merge 关卡、示例过契约、D-1～D-9 对齐、§6 反例库 11/11）。Claude 双轨 P1×5 / P1×4（policy 配置面与 D-6 冲突、E4 关卡顺序与 §14.5 倒置、拓扑守卫四种强度、STATUS 对账、`DEFERRED`/`REJECTED` 枚举联动；UC-7 触发无 E7 可达边、UC-6/7 缺模板小节、UC-8 远端不可达双结果）；Codex P1×8（AEP payload 与字节预算、`dev_manifest` 必填、`macao_config` 封闭、disposition 联动、E7 唯一出口、UC-7 起态混塞、UC-8 远端模式、SRS 7 类）。**多数项已在 `4027cce` 闭环，但闭环动作引入新阻断，见下一行。** |
| 2026-09-02 | `2026-09-02-review-request-4027cce.md`（总入口）<br>`2026-09-02-review-request-4027cce-PRD-v2.5-Design-Sync.md`<br>`2026-09-02-review-request-4027cce-UseCases-v2.5-Alignment.md` | `6e35a71` .. `4027cce` | **L1 / PG-0** | `2026-09-02-review-result-4027cce-claude.md`<br>`2026-09-02-review-result-4027cce-codex.md`<br>`2026-09-02-review-result-4027cce-grok.md`<br>`2026-09-02-review-result-4027cce-DesignSync-qwen.md`<br>`2026-09-02-review-result-4027cce-UseCases-qwen.md` (5 份) | **未获授予。四方一致否决（`caf3473` 以来首次全体不通过）**：Claude `NO_APPROVE`×2 轨、Codex `REJECT`、Grok `NO_APPROVE`（前轮 APPROVE 改判）、Qwen `NO_APPROVE`×2 轨（前两轮 APPROVE 改判）。四方一致确认上轮 Claude 9 条 P1 中 **7 条真实闭环**、Codex 多条闭环、申请 §3/§4 机验全部复跑成立。**未获授予的阻断（按收敛方数）**：①UC-8 `remote_name: null` 通不过 `macao_config` 契约、PRD §14.5 无该模式（**四方全体**，本轮修复引入）；②PRD §2.5/§13/§2.4 Type A·B·E 五处示例 + 仓库根 `macao.yaml` 通不过自家契约（三方）；③D-6 两道反支配门禁契约层仍可关，反例可单席位批准合并（三方）；④E7 源态 `REWORK` 下 3/5 选项无可达边 + 提案 `:135` 互斥边（三方）；⑤AEP 16 KiB 预算与 8 类 payload 未完成（三方）；⑥STATUS 双向对账不平（Claude，**已于本次更新闭环**）；⑦`aep_envelope` `$ref` 指向网络 URL 致契约库不自包含（Claude）；⑧AEP 实现层不可用（Codex，属 L2 不计入）。 |
| 2026-09-02 | `2026-09-02-review-request-a0123e8.md`（总入口）<br>`2026-09-02-review-request-a0123e8-PRD-v2.5-Design-Sync.md`<br>`2026-09-02-review-request-a0123e8-UseCases-v2.5-Alignment.md` | `4027cce` .. `a0123e8` | **L1 / PG-0** | `2026-09-02-review-result-a0123e8-claude.md`<br>`2026-09-02-review-result-a0123e8-DesignSync-grok.md`<br>`2026-09-02-review-result-a0123e8-UseCases-grok.md`<br>`2026-09-02-review-result-a0123e8-DesignSync-qwen.md`<br>`2026-09-02-review-result-a0123e8-UseCases-qwen.md`<br>`2026-09-02-review-result-a0123e8-codex.md` (6 份) | **轨 B 首获三张授予票（Claude / Grok / Qwen 全部 YES_APPROVE），轨 A 三方一致不授予；委员会共识尚未形成**。票型：Claude（轨 A `NO_APPROVE` P1×2 / 轨 B **`YES_APPROVE`**）、Grok（轨 A `NO_APPROVE` P1×1 / 轨 B **`YES_APPROVE`**）、Qwen（轨 A `NO_APPROVE` BLOCKING×3 / 轨 B **`YES_APPROVE`**）、Codex（不分轨合并 `REJECT` P1×3）。三方一致确认实质进展：**PRD 正式示例 14/14 + 根 `macao.yaml` 过契约**（已固化为 `tests/test_prd_snippets_schema.py`）、`remote_name: null` 全链路、STATUS 对账 0/0、§6 反例库 11/11、正例 10/10 反例 16/16、92/92 PASS。轨 A 阻断项已在 `cd285dd` 修复。 |
| 2026-09-03 | `2026-09-03-review-request-cd285dd.md`（总入口）<br>`2026-09-03-review-request-cd285dd-PRD-v2.5-Design-Sync.md`<br>`2026-09-03-review-request-cd285dd-UseCases-v2.5-Alignment.md` | `a0123e8` .. `cd285dd` | **L1 / PG-0** | `2026-09-03-review-result-cd285dd-claude.md`<br>`2026-09-03-review-result-cd285dd-codex.md`<br>`2026-09-03-review-result-cd285dd-DesignSync-grok.md`<br>`2026-09-03-review-result-cd285dd-UseCases-grok.md`<br>`2026-09-03-review-result-cd285dd-DesignSync-qwen.md`<br>`2026-09-03-review-result-cd285dd-UseCases-qwen.md` (6 份) | **轨 B 连续两轮获全票一致授予通过（Claude / Grok / Qwen 全部 YES_APPROVE）；轨 A 问题高度收敛**。票型：Claude（轨 A `NO_APPROVE` P1×2 / 轨 B `YES_APPROVE`）、Grok（轨 A `NO_APPROVE` P1×1 / 轨 B `YES_APPROVE`）、Qwen（轨 A `NO_APPROVE` P1×1 / 轨 B `YES_APPROVE`）、Codex（合并 `REJECT` P1×3，仅评轨 A）。实质进展：D-6 配置期语义校验、`vote_result_ref` 必填契约、E7 源态清理全部闭环。轨 A 阻断项：①根 `macao.yaml` Quorum 低于法定人数触发自身校验失败；②提案 §4.2 残余“当前状态（HOLD）”与链接；③`review_disposition.schema.json` 缺少封闭；④计票引擎未实装纯整数五道门禁；⑤`vote_result.schema.json` 与 `vote.py` 字段不全；⑥编排器 E4 缺少 disposition 检查直接进入 MERGING。已在 `73576c5` 中全部闭环。 |
| 2026-09-03 | `2026-09-03-review-request-73576c5.md`（总入口）<br>`2026-09-03-review-request-73576c5-PRD-v2.5-Design-Sync.md`<br>`2026-09-03-review-request-73576c5-UseCases-v2.5-Alignment.md` | `cd285dd` .. `73576c5` | **L1 / PG-0** | `2026-09-03-review-result-73576c5-claude.md`<br>`2026-09-03-review-result-73576c5-codex.md`<br>`2026-09-03-review-result-73576c5-DesignSync-grok.md`<br>`2026-09-03-review-result-73576c5-UseCases-grok.md`<br>`2026-09-03-review-result-73576c5-DesignSync-muse.md`<br>`2026-09-03-review-result-73576c5-UseCases-muse.md` (6 份) | **未获授予**。票型：Claude（两轨 `NO_APPROVE`，轨 A P1×3 / 轨 B P1×1）、Grok（两轨 `NO_APPROVE`，轨 A P1×1 / 轨 B P1×1）、Codex（合并 `REJECT`，P1×4）、Muse（两轨 `YES_APPROVE`）。三方一致确认 `cd285dd` 阻断 3 项真实闭环、纯整数五门禁引擎层 11/11 正确、97/97 PASS。**未获授予的阻断**：①契约本轮收紧后未回扫提案 §4.3 与 UC-6 处置示例（`generated_at` vs `timestamp`，两方收敛）；②编排器归一化丢弃 `team`/`policy`，加权与 `policy_snapshot` 集成层不生效（三方收敛）；③`submit_disposition()` 可被空处置/伪造引用穿透（两方收敛）；④超时终局产物缺 deadline/ping（Codex 单方）；⑤`vote_result.json` 非真正不可变可被覆盖（Codex 单方）。 |
| 2026-09-03 | `2026-09-03-review-request-404ebd2.md`（总入口）<br>`2026-09-03-review-request-404ebd2-PRD-v2.5-Design-Sync.md`<br>`2026-09-03-review-request-404ebd2-UseCases-v2.5-Alignment.md` | `73576c5` .. `404ebd2` | **L1 / PG-0** | 待专家委员会出具 | **复审中**。前序 `73576c5` 轮 5 项阻断已在 `404ebd2` 物理闭环：①修正提案与 UC-6 示例中的 `generated_at:` 为 `timestamp:` 并增设全量抽检测试（3/3 PASS）；②编排器 `__init__` 全量保留 `team`/`policy`，早期门禁与落盘全链路纯加权并动态记录 `policy_snapshot`；③`submit_disposition()` 实装任务四元组强绑定、vote_result 哈希比对、共识 APPROVED 状态校验与 100% 缺陷穷尽覆盖八重防伪守卫；④超时弃权选票注入 `deadline` 与 `last_ping_at` 且全部分支对称传参；⑤`vote_result.json` 实装 D-1 不可变性守卫（重复调用只读复用，决策冲突 fail-closed）。全库 101/101 测试 PASS。 |
| 2026-08~09 | 评审方法论横向评审（非定级轮） | `docs/MACAO_REVIEW_GUIDELINES.md` / `docs/reference/REVIEW_METHODOLOGY.md` | — | `REVIEW_METHODOLOGY_review_cc.md`<br>`REVIEW_METHODOLOGY_review_glm.md` (2 份) | 方法论本身的横向评审（cc / glm），不参与任何定级轮次；本次对账补登，避免再次落在登记表之外。 |

---

## 下一步行动

> 依据 `73576c5` 轮 6 份专家报告（Claude / Grok / Codex / Muse）。**本轮五条阻断，两条为两方以上独立收敛的高优先级项**（均是「本轮修复动作本身收紧了契约，但未回扫引用该契约的既有示例」这一复发模式的最新实例）。

### 优先级 0 · 两方以上收敛的阻断（闭环后可重新申请两轨 L1/PG-0）

1. **[Claude A-P1-1 = Grok 轨 A/B P1-1] `review_disposition` 契约收紧后，提案 §4.3 与 UC-6 处置示例未跟进**：`docs/PRD_CHANGE_PROPOSAL_v2.5.md:159` 与 `docs/usercases/UC6-issue-triage-rework.md:36` 的 `generated_at` 键在 `review_disposition.schema.json` 中不存在（契约只声明 `timestamp`），两处示例现均被拒。
   *验收*：两处键改为 `timestamp`（与 PRD §2.5、正例 fixture 一致）后，`validate_review_disposition(...)` 对两个抽出对象均返回 `(True, None)`；`grep -rn '^generated_at:' docs/PRD_CHANGE_PROPOSAL_v2.5.md docs/usercases/` 零命中。
2. **[Claude A-P1-2 / Codex P1-1] 编排器归一化丢弃 `team`/`policy`，加权与 policy 参数运行时不生效**：`src/macao/workflow/orchestrator.py:122-134` 的 `self.config` 归一化字典不含 `team`/`policy`，导致 `:677-682` 计算的 `reviewer_weights`/`policy_cfg` 恒为空；决策路径 `:566-600` 的票面无 `weight`；`vote_result.json.policy_snapshot`（D-1 不可变记录）因此写入派生默认值而非 `macao.yaml` 实际配置。
   *验收*：`Orchestrator.__init__` 保留 `team`/`policy`；两处 `ConsensusEngine.evaluate()`/`generate_vote_result()` 调用均传入 `configured_weight`+`policy`+`reviewer_weights`；新增集成测试断言 `vote_result["policy_snapshot"]` 与 `macao.yaml` `policy` 逐字段相等，且 `vote_weight=[1,1,2]` + 票型 `[YES,YES,NO]` ⇒ `DEADLOCK`。
3. **[Claude A-P1-3 / Codex P1-2] `submit_disposition()` 缺少与当前轮计票的绑定与穷尽覆盖校验**：`orchestrator.py:784-830` 只校验 Draft-07 Schema 与 `disposition_status == "FINAL"`，`dispositions: []` 或伪造的 `vote_result_ref`/`issues_index_sha256` 均可放行并直推 `MERGING`。Codex 另指出未校验 `task_id`/`checkpoint_ref`/`review_round`/`executor` 与当前轮一致。
   *验收*：补齐三项前置断言（决策为 `APPROVED` 或合法 override；`dispositions` 的 issue_id 集合与 `vote_result.issues_index` 严格相等；`vote_result_ref.sha256`/`issues_index_sha256` 与重算值一致），每项各配一条否定测试。

### 优先级 1 · Codex 单方发现，建议本轮一并处理

4. **超时终局产物缺 `deadline`/`last_ping_at`**（Codex P1-3）：`vote.py:136-148` 合成的 timeout 票只写 `source`，提案 `:113`（D-3）明定必须记录 deadline 与最后一次 ping；`vote_result.schema.json:50-51` 两字段仅为可选，与「必须记录」矛盾。DEADLOCK 分支 `:607-615` 亦未传 `task_id`/`reviewer_weights`/`policy`，与正常分支 `:685` 输入不对称。
   *验收*：timeout 票补齐两字段并设为 `source: timeout` 时的必填条件；DEADLOCK 分支与正常分支使用同一套（task/policy/weights）调用参数。
5. **`vote_result.json` 非真正不可变**（Codex P1-4）：`vote.py:282-286` 每次无条件 `open(..., "w")` 重写，无存在性检查、无 round/sha 冲突拒绝。
   *验收*：改为按 task/ref/round 隔离路径的原子 create-if-absent；已存在则只读复用，内容不一致 fail-closed；补同轮重复调用不变性测试。

### 优先级 2 · P2/P3 批次（不阻断定级，Phase 1 前处理）

6. **`state_engine.py:102` Layer 1c 与 `orchestrator.py:913` E7 `APPROVED` 直跳 `MERGING`**（Claude A-P2-1/A-P2-2）：均绕开 disposition 守卫；Layer 1c 当前无调用方，E7 路径已由 CLI 接线，优先处理后者。
7. **`EXTEND` override 选项文档三处声明（PRD `:881`、提案 `:230`、UC-7 `:31,:81`）但机器契约无该值**（Claude A-P2-3 / B-P2-2）：`OverrideChoice` 与 CLI `click.Choice` 均只有 4 个成员，UC-7 `:81` 的验收标准在现行契约下不可满足。二选一：补齐 `EXTEND` 或删除文档声明。
8. **`vote_result` 双别名并存**（Claude A-P2-4）：`generated_at`/`timestamp`、`executor_id`/`executor` 仍同时声明且同时写出，是本轮阻断项 1 的直接成因；建议全库统一为 `timestamp`。
9. **围栏抽检门禁扩面**（Claude A-P2-6，连续第 6 轮登记）：`tests/test_prd_snippets_schema.py` 只覆盖 `docs/MACAO_PRD_v2.md` 六节，不含提案与用例文件；本轮两条 P1 恰好落在缺口内。
10. **D-9 的 `reconcile` 在用例体系零命中**（Claude B-P2-1）：`init`/`adopt` 有 UC-1、`doctor` 有 UC-10，`reconcile` 无任何用例，「全量用例体系」存在覆盖缺口。
11. **Markdown 份数口径连续第 3 轮不一致**（Claude A-P3-2）：`git ls-files '*.md'` = 205、工作区 = 209，申请称 212，两种口径均不符；建议固定为 `git ls-files '*.md' | wc -l`。
12. **反例 fixture 拒因归属需精确标注**（Claude A-P3-3，第 2 轮登记）：3 份 `macao_config_*` 反例在 Draft-07 单独下 ACCEPT，仅由 `validate_config` 语义层拒绝，不得表述为 Schema 物理锁死。

### 跨轨治理

13. **申请正文的完成式措辞需降级**：两份申请多处使用「彻底打通」「严密驻留」「全面对齐」「全部阻断项均已完成代码、契约与文档级的物理闭环」，其中集成层（编排器加权、`submit_disposition` 守卫）与文档层（提案/UC-6 示例）均被证伪。Codex 建议改为「目标实现中/待 P1 验收」直至上述反例被覆盖。
14. **契约任何一次收紧后，必须重抽全部引用该契约的文档围栏**——不能仅凭「正文相对上轮无 diff」沿用历史授予结论。本轮两方（Claude、Grok）据此推翻了各自对轨 B 连续两轮的 `YES_APPROVE`。
15. **两轨 P1 闭合前不建议单独推进轨 B 授予**：轨 B 的唯一 P1（B-P1-1）与轨 A 的 A-P1-1 同源，且轨 B 用例体系引用的运行时闭环（UC-5 加权门禁、UC-6/UC-7 E4 守卫）与轨 A 阻断项 2、3 直接相关，同一次修复即可解两轨。

### 代码轨（L4 / PG-3）

16. **`42b5c07` 终局定级认证仍在复审中**：目前仅 GLM 1 份报告，Claude / Codex / Grok / Kimi / Qwen / ZCode 尚未出具。按 §8「沉默 ≠ 同意」，**维持 L3 / PG-2**。

### 登记与治理

17. **本文件对账已于本次执行**：补入 `73576c5` 轮 6 份结论，计数由 132/35 更正为 **138/35**（申请份数不变，`review-request-73576c5*` 三份此前已计入），结论类由 132 更正为 138（`review-result-*` 138 + `review-2.5-*` 2 + `REVIEW_METHODOLOGY_*` 2 = 142，见文件头行），双向均为 0。**下一轮申请复审前须再次全量对账**；申请方不得以 STATUS 的登记子集作为闭环核验边界（本文件第 4 行）。
