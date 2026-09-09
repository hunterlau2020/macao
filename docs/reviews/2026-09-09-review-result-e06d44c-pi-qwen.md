# MACAO 检查点防伪闭环、UC-11 E1 守卫与 Provider 扩展复审结论（Commit `e06d44c` / Round 4）

- **文档归档路径**: `docs/reviews/2026-09-09-review-result-e06d44c-pi-qwen.md`
- **评审日期 (Date)**: 2026-09-09（机验执行窗口 00:10–00:44 +0800）
- **评审人 (Reviewer)**: `pi-qwen`（harness: pi coding agent，`PI_MODEL=qwen3.8-max`，`PI_SESSION_ID=01a07bd3-8b24-72e9-8e95-62179f6a5946`；与已归档 `qwen` 报告为不同评审人，结论独立作出）
- **评审对象 (Object)**: [`docs/reviews/2026-09-09-review-request-e06d44c.md`](2026-09-09-review-request-e06d44c.md)
- **受审基线 (Checkpoint)**: 短 SHA `e06d44c`，**真实完整 SHA `e06d44cb31a0dbcbe199e6bb124430e9701e087f`**（申请文档自称的完整 SHA 不存在于仓库，见 P1-1）。全部结论取自 `git archive e06d44c` 纯净树（§3.4）；复现脚本归档于 [`docs/reviews/evidence/2026-09-09-e06d44c-pi-qwen/`](evidence/2026-09-09-e06d44c-pi-qwen/)
- **对齐基准**: [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md) v1.1（§3.4/§3.5/§5.2/§7.2/§8.1-8.3）、`docs/usercases/PRODUCT-FACTS.md`、`AGENTS.md`
- **申请目标**: L3 SCENARIO-VERIFIED / PG-2 全量认证 + L4 RELEASE-READY / PG-3 准入
- **审查结论 (Verdict)**: **不授予本轮增量 L3 SCENARIO-VERIFIED / PG-2 全量认证；拒绝 L4 / PG-3 准入。判定：REWORK（第 5 轮，收窄为 2 项 P1）**
- **最终投票 (Vote)**: `NO_APPROVE`
- **证据统计**: P0 × 0、**P1 × 2**、P2 × 3、P3 × 2。**Round 3 的 3 项 P1 中 2 项经独立机验彻底闭环**（检查点防伪、adopt 守卫——含 13 种伪造变体全拒与端到端 `checkpoint --auto` 走通），Round 3 的 4 项 P2 中 **4 项全部闭环**（变更清单 21/21 精确、Kimi 勘误、§5.2 常设表、验收标准 PTY 透传）；新增 1 项 P1（执行器适配器丢弃验收标准）与 1 项 P1（申请元数据证据链第三轮未闭合）。
- **复现**: 归档脚本 6 组检查（G01–G06），最后实际执行 **2026-09-09 00:43:40 +0800**：G01/G02a/G02b/G06 PASS（闭环为真），G03/G04/G05 FAIL（缺陷按预期复现）。

---

## §0 Reviewer 自审记录（v1.1 §9 强制自检）

| 检查项 | 执行情况 |
|---|---|
| □1 字段声明 vs 读取位置 | 已查：`orchestrator.py:211-215` 注入 `acceptance_criteria`，而 5 个执行器适配器只读 `success_criteria`（P1-2 根因，G03） |
| □2 `[x]` ≠ 证据 | §3.2 七项声明六项机验为真；「真实 64 位 SHA-256 签名」与「`git show --check <完整 SHA>` rc=0」两项被 G05 推翻 |
| □3 确定性用语 | 「严格生成」「真实 SHA-256」「彻底闭环」与实现/实物的出入集中于申请元数据（P1-1），代码侧声明全部属实 |
| □5 P1 可复现 | P1-1/P1-2 各附命令与 file:line |
| □6 已实现 ≠ 已接线（模式 E） | **命中**：本轮 §1.3 修复了 reviewer 侧与 pi/cursor 两个适配器的验收透传，但同一不变量在其余 5 个执行器适配器上零接线（G03）——正是模式 E 的镜像形态（「修了一半的接线」） |
| □7 参照系自检 | 全部机验在纯净树；`git show --check` 用**可解析的短 SHA**复测（申请给的 40 位 SHA `fatal: bad object`）；负向断言校验非零退出码（G02a rc=1） |

**过程记录**：评审窗口内工作树新增了 codex、grok 两位评审人的未跟踪 evidence 目录（00:36、00:41），无任何 `src/` 改动，不影响本评审参照系。本评审自身的一次工具误差已按 §3.5 勘误归档：G05 首版误用 `git rev-parse --verify`（对 40 位 hex 仅查语法不查存在），已改 `git cat-file -t` 并复跑修正。

---

## §1 结论综述 (Executive Summary)

**这是四轮以来工程质量最高的一轮。** Round 3 的两项代码级 P1 均被彻底闭环且经得起反例轰击：

1. **检查点防伪（R3 P1-A）CLOSED**：`orchestrator.py:326-…` 的 8 步门禁对 G01 的 **13 种伪造变体全部拒绝**——全零/空/非 hex/长度 63/篡改正文/文件缺失/路径穿越/冒名 `executor.id`/错 `executor.cli`/`tests_passed: false`/轮次错/任务错/`evidence_commit` 错配；happy path 正常推进；且 `task checkpoint --auto --test-cmd` **端到端走通严格门禁**（生成器与门禁一致，无自我锁死）。Grok/Claude/Qwen 三方归档探针在纯净树复跑全部绿灯。
2. **`task adopt` 守卫（R3 P1-B）CLOSED**：幽灵基线 → `UC-11 E1 Error` 明确报错、**rc=1、state.db 零落盘**（G02a）；合法接管 → `CODING`，审计链含 `STATE_TRANSITION_E1_ADOPT`/`TASK_ADOPTED`，`E1_ADOPT`/`E2_ADOPT` 已入 `transitions.py:30/33` 白名单（G02b）。
3. Round 3 的 4 项 P2 全部闭环：变更清单 **21/21 行与 numstat 完全一致**（G06，且诚实标注"由 git diff --numstat 严格生成"）；Kimi 勘误落地（STATUS.md:97 现为「0 项 P0；1 项 P1…其他 P0/P1 项由 Pi-Qwen 与 Grok 独立提出」，与归档原文一致）；§5.2 常设表落地且**六列齐全含 expiry**（`v3.0` / `v2.6.0-rc1`）；reviewer 侧 `acceptance_criteria` 透传入 payload 与提示词（`live_dispatcher.py:278-288`）。
4. **Provider 特性为真**：双侧 Schema 逐字节一致（`cmp` 全 SAME），`pi.py:91-93` 拼接 `--provider`，`opencode.py:64-69` 组合 `-m provider/model`（含防重复斜杠），prober 记录、dispatcher 透传（`:207-209`）、UI 呈现齐备。
5. 质量快照属实：**165/165**、`test_schema` 8/8、`compileall` rc=0、`git show --check e06d44c` rc=0、AGENTS.md 计数同步、账本 204/151/45/3 双向吻合、Round 3 全部评审资产与 evidence 已入库。

**但认证仍被两项 P1 阻断，且都极具讽刺性：**

- **P1-1（申请证据链，第三轮）**：本轮主题是「SHA 防伪与逐字节对账」，而申请文档自身：自称的 40 位完整 SHA **在仓库中不存在**（`git cat-file -t` → fatal；`--batch-all-objects` 0 命中；真实 SHA 为 `e06d44cb31…`）；其 §3.3 给出的验证命令**按原文执行即失败**（`fatal: bad object`，rc=128，声称为 0）；信封样例 `sha256: d599dca0…` 与正文实际哈希 `e13b9bdf…` **不符**（与仓库内任何候选文件均不匹配）；`.macao/.dev.yml` 磁盘上仍不存在（「物理信封由主执行席位签署」无从谈起）；申请文档不在其 `evidence_commit: e06d44c` 内（首次提交于 `b8d8e9e`）。处置单声称 P1-3「消灭信封占位符」已闭环——实测是把占位符**换成了一个对不上的真值哈希**：在本轮自己引入的 8 步门禁下，该信封会被自己的门禁拒绝。
- **P1-2（执行器验收标准丢失）**：`Orchestrator.start_task` 向执行器注入 `acceptance_criteria`（`orchestrator.py:211-215`），但 **7 个执行器适配器中 5 个只读 `success_criteria`**（`antigravity.py:88`、`claude.py:87`、`codex.py:76`、`kimi.py:75`、`opencode.py:92`），提示词渲染为 `Acceptance Criteria: {}`——用户显式验收标准（Round 2 P1-8 建立的不变量）在 5/7 的生产执行路径上被静默丢弃。本轮只修了 `pi.py:114` 与 `cursor.py:91` 两个适配器，属「修了一半的接线」（模式 E 镜像）。

L4/PG-3 第三轮不予受理：§7.2 十行 OPS 矩阵仍未填写；`live-run` Reviewer 仍全为 `mock-cli`（`live_runner.py:56-58`）且 `auto_signoff` 默认 `True`（`:76`），持续触犯 §7.2 第 10 行。

---

## §2 声明验证矩阵（申请逐条机验）

| # | 申请声明 | 独立验证 | 状态 |
|---|---|---|---|
| 1 | §1.1 检查点 8 步防伪（sha 64-hex、禁全零、物理存在、防穿越、逐字节对账、executor id+cli 吻合） | G01：13 变体全拒 + happy 推进 + e2e `--auto` 走通 | **VERIFIED** |
| 2 | §1.2 adopt E1 守卫（commit 存在性、rc=1 不脏写、TransitionTable 注册、审计下沉） | G02a/G02b + `transitions.py:30/33` | **VERIFIED** |
| 3 | §1.3 reviewer PTY 验收标准全量透传 | `live_dispatcher.py:278/283/288`（payload+提示词） | **VERIFIED** |
| 4 | §1.4 Claude 会话强制 `cwd` 校验 | `session_locator.py:184-185/202-205`；功能测试：无 cwd 孤儿被排除、匹配者保留 | **VERIFIED** |
| 5 | §1.5 Provider 支持（双侧 Schema、pi/opencode、调度器与 UI） | cmp 双侧一致；`pi.py:91-93`、`opencode.py:64-69`、prober/dispatcher 接线齐备 | **VERIFIED** |
| 6 | §1.6 Kimi 勘误 / §5.2 常设表 / 消灭占位符 | 前两项 VERIFIED（STATUS.md:97、:29-… 六列含 expiry）；「消灭占位符」**CONTRADICTED**：信封哈希对不上正文（G05） | **PARTIAL → P1-1** |
| 7 | §2 变更清单「由 numstat 严格生成」 | G06：21/21 行逐行一致 | **VERIFIED**（漏列 15 个文件见 P3-2） |
| 8 | §3.1 `Ran 165 tests OK` | 纯净树 `Ran 165 tests in 62.660s OK` | **VERIFIED** |
| 9 | §3.2 `test_schema` 8/8、`compileall` rc=0 | 两者均复现 | **VERIFIED** |
| 10 | §3.3 `git show --check <40 位 SHA>` rc=0 | **按原文执行 rc=128 `fatal: bad object`**；短 SHA `e06d44c` rc=0 | **CONTRADICTED → P1-1** |
| 11 | §3.4 三方探针反向回归 | grok `ALL_MATCH_CLAIM` 空 fail-open；claude 全拦截 + adopt rc=1；qwen V-2..V-5 良好 | **VERIFIED**（qwen P2-1/P3-1 仍 CONFIRMED，见 P2-2） |
| 12 | §4 信封「真实 64 位 SHA-256」 | `d599dca0…` ≠ 实际 `e13b9bdf…`；`.macao/.dev.yml` 不存在；文档不在 `evidence_commit` | **CONTRADICTED → P1-1** |
| 13 | 隐含：验收标准送达**执行器**（R2 P1-8 不变量） | G03：5/7 适配器丢弃（只读 `success_criteria`） | **CONTRADICTED → P1-2** |
| 14 | 隐含：探活不失真（R3 P2-A） | G04：WAL 持有写者时仍静默报旧任务 | **CONTRADICTED → P2-1** |

---

## §3 P1：进入下一阶段前必须修正

### P1-1 申请证据链第三轮未闭合：自称完整 SHA 不存在、§3.3 命令自败、信封哈希对不上正文

- **四项事实**（全部可复现）：
  1. 申请头部「完整 SHA：`e06d44c77c688bb715bb997a3cf556bc91f6920f`」——`git cat-file -t` → `fatal: could not get object info`；`git cat-file --batch-all-objects` 全库 0 命中；真实完整 SHA 为 **`e06d44cb31a0dbcbe199e6bb124430e9701e087f`**（仅前 7 位相同，其余 33 位全错——系手写/臆造，非誊抄笔误）。
  2. §3.3 验证命令 `git show --check e06d44c77c…920f` 按原文执行 → **rc=128 `fatal: bad object`**，申请声称「返回码 0」。
  3. §4 信封样例 `sha256: d599dca03ec1…246222` ≠ 正文实际 `e13b9bdf0741…2b695`；与仓库内处置单/STATUS/模板等候选文件均不匹配；`.macao/.dev.yml` 磁盘不存在（「物理信封由主执行席位签署并逐字节对账」无实物支撑）。
  4. 申请文档不在 `evidence_commit: e06d44c` 内（首次提交于 `b8d8e9e`）——与 R2/R3 同型，第三次出现。
- **定级（§8.1/§8.2）**：影响域=审计链在哈希/提交层面断裂（属 §8.1 P0 域；因位于申请侧元数据而非生产代码路径，按 §8.2 降一级记 **P1**）；可达性=在线（认证申请本身即载体）；**连续第三轮**，且本轮主题恰是「SHA 防伪」——若放行，等于以一份哈希对不上的申请为「哈希防伪」授证。
- **验收标准**：完整 SHA 以 `git rev-parse` 输出誊抄；信封 sha256 = `sha256sum` 实测值（或明确标注"样例"且不含真实 task_id/checkpoint）；§3.3 命令改用可解析 SHA 并由作者实际执行记录 rc；申请文档与整改代码同提交；为申请侧元数据建立「提交前自检清单」（rev-parse 校验、sha256sum 比对）。

### P1-2 执行器适配器丢弃 `acceptance_criteria`（5/7 生产路径，模式 E 镜像）

- **机理**：`orchestrator.py:211-215` 注入 `{"task_description", "acceptance_criteria"}`；而
  ```text
  antigravity.py:88 / claude.py:87 / codex.py:76 / kimi.py:75 / opencode.py:92:
      criteria = task_payload.get("success_criteria", {})      # ← 只读旧键名
  pi.py:114 / cursor.py:91（本轮已修）:
      criteria = task_payload.get("acceptance_criteria") or task_payload.get("success_criteria") or []
  ```
  G03（捕获式 PTY 替身）实测：`MUST_REACH_EXECUTOR` 标记到达情况 =
  ```text
  AntigravityAdapter False | ClaudeCodeAdapter False | CodexAdapter False
  KimiAdapter False | OpenCodeAdapter False | PiAdapter True | CursorAgentAdapter True
  ```
- **影响**：用户显式验收标准（R2 P1-8 确立、本轮 §1.3 部分修复的不变量）在 5/7 执行器提示词中渲染为 `Acceptance Criteria: {}`——执行者自评与后续审查围绕的不是用户的验收契约。AEP 信封侧（消息总线）虽携带标准，但 PTY 交互路径即执行 Agent 的唯一任务来源。
- **定级**：影响域=验收契约投递失真（与 R2 P1-8 同一不变量的生产路径违约）；可达性=在线真实可达（`task create` → `start_task` → 适配器 `inject_task` 主路径）。**P1**。（与另一评审人 codex 同窗口独立发现，脚本各自独立，结论互证。）
- **验收标准**：5 个适配器统一改为 `acceptance_criteria or success_criteria` 语义（或下沉到基类单点解析）；新增参数化回归测试断言标记经**真实 `inject_task` 入口**到达全部 7 个适配器的提示词；顺带复核其他 payload 键名漂移（`task_description` 等是否同样存在新旧键不一致）。

---

## §4 P2 / P3

### P2（须按 §8.3-2 完整登记风险接受，或修复）

| ID | 问题 | 证据 | 备注 |
|---|---|---|---|
| **P2-1** | `immutable=1` 陈旧读（R3 P2-A）：写者持有未 checkpoint WAL 时（daemon 写入中 / 崩溃后首次 RW 打开前），`probe` **静默**上报旧任务；决策路径（`main.py` 守卫走 RW）不受影响 | G04（本轮在 e06d44c 纯净树复现 `reported=task-OLD`）；`prober.py:75/96` 等 5 处 | R3 处置单未列该项；未登记即视为未接受（§8.3-2）。建议：WAL 非空时标注 `STALE(WAL_PRESENT)` 或读副本 |
| **P2-2** | QW-7BC-P2-1（未知 CLI 诊断静默）仍在：qwen 归档探针于 e06d44c 复跑输出 `CONFIRMED QW-7BC-P2-1` | 探针输出（evidence/2026-09-08-7bc8d70-qwen） | R3 处置单未列；同上须登记或修复 |
| **P2-3** | L4 证据缺口：§7.2 十行矩阵本申请仍未填写；`live-run` Reviewer 全 `mock-cli` + `auto_signoff=True` 默认，触犯 §7.2 第 10 行 | `live_runner.py:56-58/76` | 仅阻断 L4/PG-3，不阻断 L3/PG-2 |

### P3（登记即可）

| ID | 问题 | 证据 |
|---|---|---|
| **P3-1** | `evidence_commit: ""`（空串）通过门禁（`if evidence_commit and …` 对 falsy 跳过），与申请「非空 path、sha256、evidence_commit」表述不符；缺失键已被 Schema 拦截，仅空串边缘 | 纯净树实测：missing→rejected，`""`→ADVANCED |
| **P3-2** | 变更清单表列 21 行、漏列 15 个文件（全部为评审归档/evidence/请求文档与 1 处旧处置单微调）；数字本身 21/21 精确（较 R3 实质改善），建议表尾注明「另含 15 个治理归档文件，见 numstat」 | G06 输出 |

---

## §5 交叉文档修订建议

1. 申请头部完整 SHA、§3.3 命令、§4 信封哈希三处按 P1-1 验收标准更正；建议在 `templates/review-request-template.md` 增设「提交前元数据自检」小节（`git rev-parse <checkpoint>` 誊抄、`sha256sum` 实测、命令逐条实际执行并记录 rc）。
2. §1.3 措辞由「验收标准全量透传」改为「reviewer 侧与 pi/cursor 已透传；执行器侧 5 适配器待修」——或直接完成 P1-2 修复后维持原文。
3. `docs/PROBE_TECHNICAL_DESIGN.md`：补 `immutable=1` 权衡与 `STALE(WAL_PRESENT)` 方案（P2-1）。

---

## §6 建议的闭环顺序与验收标准（Round 5）

| 序 | 项 | 验收标准 |
|---|---|---|
| 1 | **P1-2** | 7/7 适配器经真实 `inject_task` 入口的参数化回归（标记到达断言）；键名解析下沉基类单点 |
| 2 | **P1-1** | 元数据自检清单落地；申请提交时 `rev-parse`/`sha256sum` 输出随附；文档与代码同提交 |
| 3 | P2-1/P2-2 | 修复，或按 §8.3-2 十一字段完整登记风险接受（含 expiry） |
| 4 | L4（如仍申请） | §7.2 十行逐项 VERIFIED；`live-run` 去 mock 化并默认人工 signoff |

**展望**：R3 的 2 项代码级 P1 已高质量闭环、4 项 P2 全闭环、质量快照全部属实。剩余 2 项 P1 均为窄口径（一处 5 行级键名对齐、一处申请元数据流程），**不构成架构性返工**；完成后本评审人预期可投出赞成票。

---

## §7 复现脚本与命令（含最后执行日期与完整可重放环境）

- **归档**: [`docs/reviews/evidence/2026-09-09-e06d44c-pi-qwen/`](evidence/2026-09-09-e06d44c-pi-qwen/)（`repro_e06d44c_pi_qwen.py` + `README.md`）
- **最后实际执行**: **2026-09-09 00:43:40 +0800**；环境：Debian / Python 3.12 / git 2.39+，仓库 `/home/debian/macao`（HEAD `b8d8e9e`）；脚本自建沙箱、自行提取 `git archive e06d44c` 纯净树、自清理
- **一键重放**:
  ```bash
  python3 docs/reviews/evidence/2026-09-09-e06d44c-pi-qwen/repro_e06d44c_pi_qwen.py
  # 预期：G01/G02a/G02b/G06 PASS；G03/G04/G05 FAIL（三项缺陷按预期复现）
  # 关键单项复核（P1-1 存在性证明，勿用 rev-parse --verify——它只查语法）：
  git cat-file -t e06d44c77c688bb715bb997a3cf556bc91f6920f   # -> fatal: 不存在
  git rev-parse e06d44c                                      # -> e06d44cb31a0dbcbe199e6bb124430e9701e087f
  sha256sum docs/reviews/2026-09-09-review-request-e06d44c.md  # -> e13b9bdf…（信封称 d599dca0…）
  ```
- **副作用声明**：一切实验在沙箱内完成并清理；宿主仓仅只读命令与 `probe --dry-run`（rc=0，`.macao` 零侧车）；本评审新增产物仅本报告与 evidence 目录。

---

**投票 (Vote)**: `NO_APPROVE`
**结论 (Verdict)**: REWORK — 不授予 `e06d44c` 增量 L3 SCENARIO-VERIFIED / PG-2；L4 / PG-3 不予受理。
**阻断项**: P1 × 2（申请元数据证据链第三轮未闭合；5/7 执行器适配器丢弃 `acceptance_criteria`）。
**肯定项**: R3 全部代码级 P1 与全部 P2 实质闭环且经反例轰击成立；165/165；Provider 特性端到端为真；变更清单、勘误、§5.2 表全部落地。
