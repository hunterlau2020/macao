# Evidence archive — pi-qwen Round 4 review of `e06d44c`

- **Reviewer**: pi-qwen（harness: pi coding agent `PI_CODING_AGENT=true`；model `qwen3.8-max`；session `01a07bd3-8b24-72e9-8e95-62179f6a5946`）
- **Review object**: `docs/reviews/2026-09-09-review-request-e06d44c.md`
- **Verified commit**: 短 SHA `e06d44c`（**真实完整 SHA `e06d44cb31a0dbcbe199e6bb124430e9701e087f`**；申请文档自称的 40 位完整 SHA 经 `git cat-file -t` 与 `--batch-all-objects` 双重证明**不存在于仓库**，见 G05）
- **Range**: `7bc8d70..e06d44c`（涵盖 `972e0d0`、`080720c`、`e06d44c`）
- **Script**: `repro_e06d44c_pi_qwen.py`（自建 `tempfile.mkdtemp` 沙箱 + 自行 `git archive e06d44c` 纯净提取 + 自清理）
- **外部前提**: python3（3.10+，本机 3.12）、git、含 `e06d44c` 的本仓库检出。无网络、无厂商账号、无沙箱外写入。
- **最后实际执行**: **2026-09-09 00:43:40 +0800**，结果：**G01/G02a/G02b/G06 PASS**（闭环复核为真），**G03/G04/G05 FAIL**（即 P1-2 / P2-1 / P1-1 三项缺陷按预期复现）。

## 检查 ↔ issue 映射

| 检查 | 内容 | 对应结论 |
|---|---|---|
| G01 | 检查点防伪 13 种伪造变体（全零/空/非 hex/短 hex/篡改正文/缺文件/路径穿越/冒名 id/错 cli/tests_false/轮次错/任务错/ec 错配）全部拒绝；happy path 推进；`task checkpoint --auto --test-cmd` 端到端通过严格门禁 | R3 P1-A **CLOSED** |
| G02a | `task adopt` 幽灵基线 → rc=1 且 **state.db 未落盘** | R3 P1-B **CLOSED** |
| G02b | 合法 adopt → CODING，审计含 `STATE_TRANSITION_E1_ADOPT` + `TASK_ADOPTED`（E2_ADOPT 同在 `transitions.py:30/33` 注册） | R3 P1-B **CLOSED** |
| G03 | **5/7 执行器适配器丢弃 `acceptance_criteria`**（antigravity/claude/codex/kimi/opencode 仅读 `success_criteria`；orchestrator.py:211-215 发送的是 `acceptance_criteria`；本轮仅 pi.py:114 / cursor.py:91 修复） | **本轮 P1-2** |
| G04 | `immutable=1` 陈旧读：写者持有未 checkpoint WAL 时 probe 静默报 `task-OLD`（真相 `task-NEW`） | **R3 P2-A 未处置、仍在（P2-1）** |
| G05 | 申请元数据：自称完整 SHA `e06d44c77c68…` 不存在（`cat-file -t` fatal / `--batch-all-objects` 0 命中；真实为 `e06d44cb31a0…`）；§3.3 命令按原文执行 rc=128（声称 0）；信封 sha256 `d599dca0…` ≠ 实际 `e13b9bdf…`（与仓库内任何候选文件均不符）；`.macao/.dev.yml` 磁盘不存在；申请文档不在 `evidence_commit` 内（首次提交于 `b8d8e9e`） | **本轮 P1-1** |
| G06 | 变更清单 21/21 行与 `git diff --numstat 7bc8d70..e06d44c` **完全一致** | R3 P2-B **CLOSED** |

> 勘误记录（§3.5 纪律）：G05 首版误用 `git rev-parse --verify` 作存在性证明（该命令对 40 位 hex 仅校验**语法**，不校验存在，曾误报 resolves=True）；已改为 `git cat-file -t` 并复跑，结论以 00:43:40 版本为准。

## 另行执行、未入脚本的机验（§3.4 参照系声明，2026-09-09 00:10–00:44 +0800，纯净树 `/tmp/v4`）

```bash
python3 -m unittest discover tests            # Ran 165 tests in 62.660s, OK
python3 -m unittest tests.test_schema         # Ran 8 tests, OK
python3 -m compileall -q src tests            # rc=0
git show --check e06d44c                      # rc=0（短 SHA；申请所载 40 位 SHA 则 fatal: bad object）
# 申请 §3.4 所列三方探针（grok/claude/qwen 归档脚本）在纯净树复跑：
#   grok  -> ALL_MATCH_CLAIM, fail_open_cases=空
#   claude-> 全部 advanced=False；adopt nonexistent -> cli_exit=1
#   qwen  -> V-2..V-5 CONFIRMED（行为良好）；P2-1/P3-1 仍 CONFIRMED（见本报告 P2-2）
# Claude cwd 过滤功能测试：无 cwd 孤儿会话被排除、匹配 cwd 会话被保留（session_locator.py:202-205）
# Provider 链路：双侧 schema cmp 逐字节一致；pi.py:91-93 --provider；opencode.py:64-69 -m provider/model；
#   prober 记录 provider；dispatcher :207-209 透传
# 宿主仓 probe --dry-run：rc=0，.macao 前后集合相等（logs, state.db），零侧车
```
