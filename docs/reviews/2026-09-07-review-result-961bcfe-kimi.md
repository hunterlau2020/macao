# MACAO 综合编排与动态探活体系复审结论（Commit 961bcfe / Round 2）

- **评审日期**：2026-09-07
- **评审人 (Reviewer)**：kimi（独立复审）
- **评审对象**：[`docs/reviews/2026-09-07-review-request-961bcfe.md`](2026-09-07-review-request-961bcfe.md)（返工整改轮，目标 L3 SCENARIO-VERIFIED / PG-2 全量认证 + L4/PG-3 准入评审）
- **评审范围**：`d042395..961bcfe`（29 个文件，+2594 / -228 行；申请文档自述"27 个文件 +2379/-237"，见 P3-2）
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.0；权威基准 `docs/MACAO_PRD_v2.md`；契约 `docs/schemas/*.schema.json`
- **受审提交**：`961bcfe`（`git rev-parse --short HEAD` 现场核实一致）

---

## 结论

**本轮暂缓授予 L3 SCENARIO-VERIFIED / PG-2 全量认证；L4 RELEASE-READY / PG-3 准入不予授予。结论：REWORK（轻量返工）。**

- 前序基线 `d042395` 的 8 项 P1 阻断项（P1-1 ~ P1-8）全部完成代码级闭环，本评审逐项独立机验通过，证据见"已确认项"；
- 但本轮**新引入**的 Pi 会话发现功能存在一处可复现的非确定性缺陷（P1-NEW-1）：测试套件在本评审独立复跑中 **17 轮出现 2 轮失败（约 12% 失败率）**，与申请文档"145/145 PASS、全部为确定性断言"的快照声明直接矛盾。依据指引 §2.2（PG-1/PG-2 要求 P0/P1 为零）与 §3.3（L3 要求 TEST 证据 VERIFIED），该缺陷未闭环前不能授予 L3/PG-2；
- L4/PG-3 另因缺少 OPS 级实机演练证据（指引 §2.1/§3.3）而不满足准入条件，本轮申请亦未提供此类证据。

缺陷根因已定位、修复面极小（一处排序决胜键 + 一行测试断言配套），预期一轮轻量返工即可达标。

---

## 已确认项（独立机验，全部 VERIFIED）

| # | 事项 | 证据 | 状态 |
|---|---|---|---|
| 1 | **P1-1 探活 dry-run 纯读零副作用** | `src/macao/workflow/prober.py:269`（`_write_probe_log` 首行 `if self.dry_run: return None`）与 `:860`（`if not self.dry_run:` 守卫落盘）。本评审在 `mktemp -d` 新建 git 仓（无 `.macao`）执行 `macao probe --dry-run`，结束后 `find` 确认零文件/目录/SQLite 创建；本仓库内复跑后 `.macao/logs/probe/` 最新日志时间戳（17:26:50）早于评审执行时刻（18:47），确认 dry-run 未写盘 | VERIFIED |
| 2 | **P1-2 会话发现防伪造/防串话** | `src/macao/adapter/session_locator.py:269-329` Codex 查 `state_*.sqlite` 并按 `Path(cwd).resolve() != resolved_proj` 严格过滤；`:345-349` Cursor 规范化路径精确比对；`:464-468` Kimi 严格 Fail-Closed 返回 `[]` 并注明不捏造。专项测试 `test_p1_2_*` 3 例通过 | VERIFIED |
| 3 | **P1-3 进度三元组物理对账** | `prober.py:255-263`：`missing_reviewers` 按集合差（`all_ids - submitted_reviewers`）计算，`has_pending_request` 与之一致；本仓库实跑 `probe --dry-run` 如实呈现 `REVIEW_PENDING` 且 Next 明确列出未出票评审员名单 | VERIFIED |
| 4 | **P1-4 法定人数三道门槛合取** | `prober.py:795-825`：`ready >= min_winning AND ready >= seat_quorum AND weight >= weight_quorum`，且逐项输出短板原因；`test_p1_4_quorum_achievable_boundary_matrix` 边界矩阵通过 | VERIFIED |
| 5 | **P1-5 全链路脱敏** | 新模块 `src/macao/utils/secrets.py`（8 类模式：sk-/ant-/ghp_/gho_/github_pat_/xox*/Bearer/URL 密码/kv 密码/PEM）；`logger.py:19-24` `SecretMaskingFormatter`；`pty_session.py:94,104`、`live_dispatcher.py:353`、`cli/main.py:666,690,714,732,739` 日志查询与落盘均经 `mask_secrets`。`test_p1_5_secrets_masking` 通过 | VERIFIED |
| 6 | **P1-6 非破坏性清理与快照还原** | `cli/main.py:929-1004`：`clean` 默认仅清 worktrees；`--all` 先建 `.macao.bak.<ts>/` 快照再重置；`--restore` 支持还原。`test_p1_6` 与更新后的 `test_clean_and_rollback.py` 通过 | VERIFIED |
| 7 | **P1-7 真实测试凭据门禁** | `cli/main.py:497-520`：`checkpoint --auto` 默认 `tests_passed=False` 并明确告警；`--test-cmd` 实际运行取退出码；`--tests-exempt` 显式豁免落账。`test_p1_7` 通过 | VERIFIED |
| 8 | **P1-8 任务活动不变量与验收标准透传** | `orchestrator.py:227-229` `cancel_task()` 走 E10 转 `CANCELLED`；`cli/main.py:388-401` `--force` 先取消旧任务再建新建；`orchestrator.py:194-217` `acceptance_criteria` 多态解析注入 Type A 信封。`test_p1_8` 通过 | VERIFIED |
| 9 | Pi 适配器交付 | `src/macao/adapter/pi.py` `PiAdapter`（capabilities/preflight/binary 解析），`adapter/__init__.py`、`integ_harness.py`、`wizard.py` 完成注册 | VERIFIED（但见 P1-NEW-1） |
| 10 | 测试规模与通过率 | `python3 -m unittest discover tests`：`Ran 145 tests ... OK`（51.2s）；`tests.test_p1_closures_and_regressions` 10/10 OK；`tests.test_prd_snippets_schema` 6/6 OK。**注：通过率声明受 P1-NEW-1 影响，非稳定成立** | PARTIALLY_VERIFIED |
| 11 | 编译与契约一致性 | `python3 -m compileall -q src tests` 零告警；`docs/schemas/` 与 `src/macao/schemas/` 8 份契约逐字节 `cmp` 一致 | VERIFIED |
| 12 | dry-run 实机行为 | 本仓库 `macao probe --dry-run` 正常渲染团队/评审员/三元组报告，且未新增探活日志文件 | VERIFIED |
| 13 | 评审资产对账 | `docs/reviews/` 实测 191 份 Markdown（142 `review-result-*` + 43 `review-request-*` + 2 `review-2.5-*` + 2 `REVIEW_METHODOLOGY_*` + 1 处置单 + 1 STATUS），与 STATUS.md 登记口径 100% 吻合；前轮遗留的"计数差 1"问题本轮已闭环 | VERIFIED |

---

## P0：必须先解决

无。

---

## P1：发布/进入下一阶段前应修正

### P1-NEW-1：Pi 会话发现排序无决胜键，导致"最近会话"选择非确定且配套测试 flaky（可复现）

- **现象（TEST 证据）**：本评审对全量套件独立复跑共 17 轮，其中 2 轮失败（失败率约 12%）。已捕获的失败现场：
  ```text
  FAIL: test_pi_session_discovery_and_names (tests/test_pi_and_session_locator.py:107)
  AssertionError: 'Implement feature X' != 'qwen-review-eng'
  ```
  （另 1 轮失败发生在首轮 5 连跑的第 3 轮，输出被重定向未留存，但同一套件、同一机制，高度置信同源。）
- **根因（CODE 证据）**：`src/macao/adapter/session_locator.py` `_find_pi_sessions()` 中
  ```python
  jsonl_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
  ```
  仅以 mtime 单键排序。两个会话文件 mtime 相同（或在文件系统时间粒度内先后倒置）时，Python 稳定排序退化为 `glob()` 的目录枚举序——**顺序不确定**。`find_session()` 默认取 `sessions[0]` 作为"最近会话"，因此默认会话绑定在该边界下非确定。
- **影响面**：① 测试断言 `sessions[0]` 顺序，固有 flaky——申请文档"145/145 PASS、全部为确定性负向/边界断言"的快照声明不成立（指引 Checklist B/C：把不稳定的实测结果陈述为确定性事实）；② 生产侧在 mtime 并列时会将会话绑定到非最新会话，属于接口行为的非确定性。
- **修复建议（一行级）**：文件名本身内嵌可排序时间戳前缀（`2026-09-07T10-00-00_sid1.jsonl`），加决胜键即可同时消除生产非确定性与测试 flaky：
  ```python
  jsonl_files.sort(key=lambda f: (f.stat().st_mtime, f.name), reverse=True)
  ```
  或在测试中显式错开两个 fixture 文件的 mtime（`os.utime`）。建议两者并施。
- **闭环验收**：修复后全量套件连续 ≥10 轮零失败，且 `test_pi_session_discovery_and_names` 不再依赖文件创建时序。

---

## P2/P3：可延期但需登记

- **P2-1：`PiAdapter` 引用不存在的 PRD 章节，且 Pi 未登记进权威能力矩阵**。`src/macao/adapter/pi.py:1` docstring 标注 "(PRD §12.3)"，但 `docs/MACAO_PRD_v2.md` 第十二部分仅含 §12.1/§12.2，且 §12.2 能力矩阵表（1377 行起）未收录 `pi` 行。新增适配器属于超出现行权威基准的扩展，建议修订 PRD §12.2 矩阵登记 Pi，或修正 docstring 引用。
- **P3-1：`git diff --check d042395..961bcfe` 报 3 处格式瑕疵**：`session_locator.py:469` 与 `logger.py:78` 文件末尾多余空行、`tests/test_pi_and_session_locator.py:75` 行尾空白。
- **P3-2：申请文档自述变更规模与实际不符**：声称"27 个文件，+2379 / -237 行"，实测 29 个文件、+2594 / -228（`AGENTS.md` 与 `2026-09-07-review-request-d042395.md` 未列入变更清单表）。
- **P3-3：申请文档对产品事实的描述与文档本体不符**：§62-63 称 F-23 为"只读零副作用"、F-24 为"会话真实绑定"，但 `docs/usercases/PRODUCT-FACTS.md:53-55` 实际新增的 F-23 为"角色职责对称性"、F-24 为"场景 C 接管对账、严禁强制倒退 IDLE"。
- **P3-4：`AGENTS.md` 测试计数过期**：正文仍写"126/128 tests passing"，实际 145 项。建议随本轮修复一并刷新。

---

## 交叉文档需做的文字修订

1. `docs/MACAO_PRD_v2.md` §12.2 能力矩阵：登记 `pi` 适配器行（或调整 `pi.py` 的章节引用）——对应 P2-1；
2. `docs/reviews/2026-09-07-review-request-961bcfe.md`：变更清单表补齐 2 份遗漏文件、修正行数统计；F-23/F-24 描述对齐 `PRODUCT-FACTS.md` 本体——对应 P3-2/P3-3（下一轮申请文档中避免复述偏差即可，历史申请为不可变归档，不改动原文）；
3. `AGENTS.md`：测试计数更新为 145（修复后应为修复时点实测值）。

## 建议的闭环顺序与验收标准

1. 修复 P1-NEW-1（排序决胜键 + 测试去时序依赖）；
2. 全量套件连续 ≥10 轮零失败（建议纳入 CI 门禁，呼应 `STATUS.md` 中"三段门禁脚本落 CI"的既有建议）；
3. 顺手清理 P3-1 三处 `diff --check` 瑕疵、刷新 `AGENTS.md` 计数；
4. 登记 P2-1（PRD §12.2 矩阵收录 pi）后，重提 L3/PG-2 认证；
5. L4/PG-3 准入需另行补齐：OPS 级实机演练证据（人工接管路径演练、崩溃恢复实演）与用户手册齐备性说明，本轮申请未包含此类证据。

## Reviewer 自审记录（指引 §9 Checklist A–D 自检）

- □ 1. 字段名 vs 实际读取路径：已核（`missing_reviewers`、`quorum.*`、`tests_passed`/`tests_exempt`、`acceptance_criteria` 读取路径与声明一致）。无漏审。
- □ 2. `[x]`/"已完成"是否有证据：本轮申请"145/145 PASS"经 17 轮独立复跑证伪其**稳定性**（2 轮失败），已据此将质量快照降级为 PARTIALLY_VERIFIED 并立 P1-NEW-1——本轮未采信作者自述。
- □ 3. 确定性用语："100% 物理机验""全部确定性断言"经实测为不稳定成立，已按"目标/待验证"处理。
- □ 4. 代码块可解析性：申请文档 `.dev.yml` 信封字段与 Schema 结构一致；`sha256` 为占位全零值（信封自声明，未作为事实采信）。
- □ 5. P1 证据可复现：P1-NEW-1 给出失败现场、文件:行号根因与最小修复路径，可在 10-20 轮全量复跑内重现。
- **连续漏审登记**：前轮（`3ea5256` 轮）我执行了 5 轮回归且全部通过；本轮首次出现单轮失败时未止步于"重跑通过"，而是追加 14 轮复跑完成根因定位。无新增漏审模式登记。

---

**评审签字**：kimi（独立复审）｜ 2026-09-07 ｜ 受审提交 `961bcfe`
