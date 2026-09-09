# MACAO 检查点防伪加固、执行者接线闭环与全适配器验收准则透传复审结论（Commit `bdc177e` / Round 5）

- **文档归档路径**: `docs/reviews/2026-09-09-review-result-bdc177e-pi-qwen.md`
- **评审日期 (Date)**: 2026-09-09 / 09-10（机验执行窗口 23:50–00:48 +0800）
- **评审人 (Reviewer)**: `pi-qwen`（harness: pi coding agent，`PI_MODEL=qwen3.8-max`，`PI_SESSION_ID=01a07bd3-8b24-72e9-8e95-62179f6a5946`）
- **评审对象 (Object)**: [`docs/reviews/2026-09-09-review-request-bdc177e.md`](2026-09-09-review-request-bdc177e.md)
- **受审基线 (Checkpoint)**: `bdc177e`（真实完整 SHA `bdc177eaaff577e119093e686f2164bcc133f781`，与申请一致；范围 `e06d44c..bdc177e`）。全部结论取自 `git archive bdc177e` 纯净树；复现脚本归档于 [`docs/reviews/evidence/2026-09-09-bdc177e-pi-qwen/`](evidence/2026-09-09-bdc177e-pi-qwen/)
- **对齐基准**: [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md) v1.1、`docs/usercases/PRODUCT-FACTS.md`（F-21/F-25/F-26）、`AGENTS.md`
- **申请目标**: L3 SCENARIO-VERIFIED / PG-2 全量认证 + L4 RELEASE-READY / PG-3 准入
- **审查结论 (Verdict)**: **授予本轮增量（`e06d44c..bdc177e` 范围）L3 SCENARIO-VERIFIED / PG-2，附 2 项绑定条件；不授予 L4 RELEASE-READY / PG-3（第 5 轮连续，理由未变）。既有编排引擎 L3/PG-2 维持。**
- **最终投票 (Vote)**: `YES_APPROVE`（本评审人在本项目五轮评审中的首次赞成票）
- **证据统计**: **BLOCKING × 0**；绑定条件（P2 登记）× 2；P3 × 3。Round 4 全部 4 位评审人的 P1（含本评审人 2 项、Codex/Claude 各 3 项中的同型项）**全部经独立反例复验为真闭环**；申请文档自身元数据**五轮以来首次自洽**。
- **复现**: 归档脚本 7 组检查（H01–H07），最后实际执行 **2026-09-10 00:48:16 +0800**：H01–H06 PASS（闭环为真），H07 FAIL（陈旧读仍在 → 绑定条件）。

---

## §0 Reviewer 自审记录（v1.1 §9 强制自检）

| 检查项 | 执行情况 |
|---|---|
| □2 `[x]` ≠ 证据 | 申请 §3 五项声明全部机验为真；§1 三项闭环声明全部以反例复验 |
| □5 P1/P2 可复现 | 每项附脚本编号与 file:line |
| □6 已实现 ≠ 已接线 | 本轮无新增命中；且 R4 的"半接线"（5/7 适配器）已修复为 7/7（H03） |
| □7 参照系自检 | 纯净树机验；负向断言校验非零退出码；**本轮登记本评审人自身两处修正**（见下） |

**本评审人自勘（连续漏审登记，指引 §1.2-5）**：

1. **Round 4 漏审登记（模式：反例覆盖不全）**：R4 我以 `../../../../etc/hosts` 测试路径逃逸并判"已被拒"，但未构造**共享项目名前缀的兄弟目录**（`/x/repo` vs `/x/repo_sibling`），致 `startswith` 前缀逃逸漏报——该缺陷由 Codex/Claude 本轮提出并被修复（H01 已验证）。已记入本人漏审模式。
2. **本轮两次无效复测自纠**：陈旧读复测初版沙箱漏配 `macao.yaml`，probe 在读库前 fail-closed 早退，`active_task=None` 一度被误读为"已修复"；已以有效配置重测（H07），结论以归档脚本 00:48 版本为准。
3. **探索期副作用披露**：一次 `task create`（executor `cli: kimi`）真实拉起 kimi PTY（本机已装）；进程已确认清理、无残留。该现象转为 P3-1（非缺陷，见下）。

---

## §1 结论综述 (Executive Summary)

**这是五轮以来第一次，申请所声称的每一项闭环都在我的独立反例下成立，且申请文档自身第一次完全自洽。**

1. **检查点防伪（R4 Codex P1-01 / Claude P1-1 / Grok P2-1）CLOSED**：`orchestrator.py` 以 `is_relative_to` 替换 `startswith` 后，**兄弟目录逃逸被拒**；`evidence_commit` 非空强校验后**空串被拒**；新增 Git blob 逐字节对账后，**"磁盘 sha==manifest 但与提交 blob 不符"的篡改被拒**（H01/H02）。此前 11 种伪造变体（全零/空/非 hex/篡改/缺文件/冒名 id/错 cli/tests_false/轮次/任务）继续全拒；happy path 与 `checkpoint --auto --test-cmd` 端到端照常通过——门禁收紧没有锁死正常流。
2. **执行者接线与验收透传（R4 Pi-Qwen P1-2 / Codex P1-02 / Claude P1-2）CLOSED**：`get_orchestrator()` 现装配执行器适配器（mock 实测注入成功；未知 CLI → `None`，fail-closed 保持），`Orchestrator.__init__` 兜底自愈；**`acceptance_criteria` 到达 7/7 适配器提示词**（H03/H04，含本轮统一修复的 5 款）。
3. **申请元数据（R4 Pi-Qwen P1-1 / Codex P1-03 / Claude P1-3）CLOSED**：完整 SHA 为 `git rev-parse` 真值（`cat-file -t` 通过）；§3.3 命令按原文执行 rc=0；**信封 sha256 三方一致**（磁盘 == `bdc177e` blob == manifest，且样例通过 `validate_dev_manifest`）——五轮首次。
4. **质量与治理**：170/170、专项 26/26、`compileall` rc=0；**变更清单 25/25 行与 numstat 完全一致且零漏列**（连续第二轮精确，本轮还做到了零遗漏）；账本对账吻合；R4 四份评审与 evidence 全部入库。

**两项绑定条件（不阻断 L3/PG-2，但须在下一提交或随本轮 STATUS 修订完成登记，§8.3-2）**：未登记的遗留 P2（`immutable=1` 陈旧读，H07 复验仍在）与 blob 校验对**未提交证据文档**的跳过边界（H02 后半，与 Claude 本轮新发现的 P2 同源——成功样本只证明已提交证据的完整性）。

**L4/PG-3 第 5 轮不予受理**，理由与前四轮相同且未变：§7.2 十行 OPS 必测矩阵在申请中一行未填；`live-run` 评审席仍全为 `mock-cli`（`live_runner.py:56-58`）且 `auto_signoff` 默认 `True`（`:76`），持续与 §7.2 第 10 行冲突。

---

## §2 声明验证矩阵（申请逐条机验）

| # | 申请声明 | 独立验证 | 状态 |
|---|---|---|---|
| 1 | §1.1 `is_relative_to` 防逃逸 / 非空 `evidence_commit` / Git blob 对账 | H01：兄弟逃逸与空 ec 被拒；H02：blob-vs-disk 篡改被拒 | **VERIFIED** |
| 2 | §1.1「当文件在对应 commit 存在时」校验 blob | H02 后半：**未提交证据文档跳过校验仍放行**（申请已如实写明前置条件，未夸大） | **VERIFIED（声明如实）/ 边界登记 → 条件②** |
| 3 | §1.2 `get_adapter_for_executor` / `get_orchestrator` 注入 / `__init__` 兜底 | H04：mock 注入成功、未知 CLI → None、`task create` rc=0 | **VERIFIED** |
| 4 | §1.2 五款适配器统一读取 `acceptance_criteria` | H03：7/7 到达提示词 | **VERIFIED** |
| 5 | §1.3 真实 40 位 SHA / 信封过 Schema 校验 | H05：rev-parse 一致、`cat-file -t` 通过、三方 sha 一致、`validate_dev_manifest` True | **VERIFIED** |
| 6 | §2 变更清单「由 numstat 严格生成」 | H06：25/25 行精确、零漏列 | **VERIFIED** |
| 7 | §3.1 `Ran 170 tests OK` | 纯净树 `Ran 170 tests in 59.717s OK` | **VERIFIED** |
| 8 | §3.2 专项 26 项 / §3.3 rc=0 / §3.4 compileall rc=0 | 26/26 OK；show --check rc=0（真实 SHA）；compileall rc=0 | **VERIFIED** |
| 9 | §3.5 Claude 探针全绿 | 探针在案（claude 归档）；其结论与本评审独立复验一致 | **VERIFIED** |
| 10 | 隐含：探活不失真（R4 遗留 P2-1） | H07：有效配置下写者持有 WAL 时仍静默报 `task-OLD`（`error=null`，零侧车） | **CONTRADICTED → 条件①** |

---

## §3 绑定条件（随裁定生效，§8.3-2）

| # | 条件 | 证据 | 要求 |
|---|---|---|---|
| **条件①** | 遗留 P2「`immutable=1` 陈旧读」**未按 §8.3-2 登记**（R4 处置单无 P2 章节）：写者持有未 checkpoint WAL 期间（daemon 写入中 / 崩溃后首次 RW 打开前），`probe` 静默上报旧任务（H07：报 `task-OLD`，真相 `task-NEW`）；决策路径（RW 连接）不受影响 | H07；`prober.py:75/96` 等 5 处 | 在 `STATUS.md` 按 §8.3-2 十一字段完整登记（含 `expiry` 与 `risk_acceptor`），或修复（建议：WAL 非空时标注 `state_store: STALE(WAL_PRESENT)`，或复制库+wal 至临时目录读取）。**未登记即视为未接受，下一轮须阻断处置** |
| **条件②** | blob 校验对**不在 `evidence_commit` 内的证据文档**跳过（H02 后半；申请 §1.1 已如实声明前置条件）。该边界与本轮"申请文档仍晚于 checkpoint 一个提交提交"（请求单在 `3cb887b`，信封以已入库的处置单为绑定对象规避）同源 | H02；`orchestrator.py`（`cat-file -e` 失败即跳过） | 同上登记为已知简化（建议 expiry 绑定"申请文档与整改同提交"流程改造），或加 `UNCOMMITTED_EVIDENCE` 显式警示字段 |

> 依 §2.2，PG-2 要求 **P0/P1 = 0**（本轮满足）；P2 在完整登记后可延期。上述两项因此为**批准的绑定条件**而非阻断项——但登记义务不可豁免。

---

## §4 P3（建议项）

| ID | 问题 | 证据 |
|---|---|---|
| **P3-1** | `task create` 现按设计真实拉起执行器 CLI（组合根装配后 `start_task → executor.start()`）。本机 executor=`kimi` 实测拉起真实 PTY 会话（已清理）。功能上是 Codex P1-02 的预期结果，但对 CI/演练场景缺逃生阀 | 探索期实测；`orchestrator.py:218-220`。建议增加 `--no-dispatch` 并在 CLI 帮助中标注"将启动执行器会话" |
| **P3-2** | qwen 归档探针（7bc8d70 版）在现行代码上仍报 `QW-7BC-P2-1 CONFIRMED`，系其内建配置在现行 Schema 下非法导致 probe 早退（无 reviewers 字段）的**探针侧陈旧**；有效配置实测 `probe --json` 已具名输出 `Unrecognized CLI 'custom-claude'` + `MISSING` | g12 复放（README 附录）。建议更新该探针配置以免误导后续轮次 |
| **P3-3** | 申请文档本体仍晚于 checkpoint 一个提交（`3cb887b`）；本轮以信封绑定**已入库的处置单**实现自洽，属合规变通。建议最终落实"申请文档与整改代码同提交" | `git cat-file -e bdc177e:<request>` rc=128 |

---

## §5 L4 / PG-3 独立裁定（v1.1 §7.2）

与前四轮相同：申请未附 §7.2 十行矩阵任何一行；`live-run` 仍 `mock-cli` ×3 + `auto_signoff=True`（§7.2 第 10 行直接冲突）。**PG-3 不予受理。** 该项与本轮增量无关，不影响的 L3/PG-2 授予。

---

## §6 建议的闭环顺序（Round 6 或发布准备期）

1. **登记条件①②**（纯 STATUS 修订，十分钟级）——这是保住本轮授级的唯一义务；
2. P3-1 `--no-dispatch` 逃生阀（一行级 option + 帮助文本）；
3. L4 准备：填 §7.2 十行矩阵 + `live-run` 去 mock 化 + 人工 signoff 演练归档。

---

## §7 复现脚本与命令（含最后执行日期与完整可重放环境）

- **归档**: [`docs/reviews/evidence/2026-09-09-bdc177e-pi-qwen/`](evidence/2026-09-09-bdc177e-pi-qwen/)（`repro_bdc177e_pi_qwen.py` + `README.md` 含自勘记录）
- **最后实际执行**: **2026-09-10 00:48:16 +0800**；环境：Debian / Python 3.12 / git 2.39+，仓库 `/home/debian/macao`（HEAD `3cb887b`）；脚本自建沙箱、纯净提取 `git archive bdc177e`、自清理
- **一键重放**:
  ```bash
  python3 docs/reviews/evidence/2026-09-09-bdc177e-pi-qwen/repro_bdc177e_pi_qwen.py
  # 预期：H01–H06 PASS（全部闭环为真）；H07 FAIL（陈旧读仍在 → 条件①）
  ```
- **副作用声明**：破坏性实验均在沙箱内完成并清理；探索期误拉起的一次 kimi PTY 已确认清理；宿主仓仅只读命令与 `probe --dry-run`（rc=0、零侧车）。本评审新增产物仅本报告与 evidence 目录。

---

**投票 (Vote)**: `YES_APPROVE`（附 2 项绑定条件）
**结论 (Verdict)**: 授予 `e06d44c..bdc177e` 增量 **L3 SCENARIO-VERIFIED / PG-2**；**不授予 L4 / PG-3**。
**肯定项**: R4 全部 P1（四位评审人合计口径）经独立反例复验为真闭环；申请元数据五轮首次自洽（真实 SHA + 三方信封绑定 + Schema 校验通过）；变更清单 25/25 零漏列；170/170。
**条件项**: ①登记或修复 `immutable` 陈旧读 P2；②登记 blob 校验对未提交证据的跳过边界。
