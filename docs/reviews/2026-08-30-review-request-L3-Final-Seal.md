# MACAO L3 / PG-2 终局封板认证复审申请 (commit `99526aa..HEAD`)

- **申请日期**：2026-08-30
- **申请目标**：**L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)**
- **待审范围**：`99526aa..HEAD`
- **依据基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/EXPERT_QUALITY.md`、`docs/schemas/*.schema.json`
- **全量机验结果**：
  - `PYTHONPATH=src python3 -m unittest discover tests -v`：**60 ran / 60 PASS (100%)**；
  - 5 轮连续全量高压回归（300 次用例执行）：**0 flake / 0 碰撞 / 0 崩溃 (100% PASS)**；
  - `macao test-clis`：**4/4 真实 CLI PTY 验证 PASS**（Claude Code / Codex / OpenCode / AGY），ANSI Escape 序列真实无残留检测通过，0 孤儿/0 僵尸残留；
  - `macao e2e-run`：**7/7 步骤全绿，终态 DONE**，5 份物理产物与 SQLite 账本（全 `consumed=1`、`archived_path` 真实非空、`sha256` 64 位哈希非空）双向核对 100% 一致；
  - 差异洁净度：`git diff --check 99526aa..HEAD` **返回码 0，无任何告警**。

---

## 一、针对 `bf5ae2d` 专家评审意见全量闭环清单

| 编号 | 严重度 | 专家来源 | 复审问题描述 | 根因与修复落点 | 对应测试与验证 |
|---|---|---|---|---|---|
| **P1-NEW-8 / P1-Q3 / P1-1** | **阻断** | Claude, Qwen, Grok, Codex | **`RETRY_REVIEW`（E9）重试轮被旧超时处置毒化：重试后全员按时提交赞成票仍被当迟到票隔离，导致永久活锁** | 修复 `src/macao/workflow/orchestrator.py:454-464, 750-762`：在 `collect_and_evaluate_consensus` 与 `resolve_override` 中，超时处置一律**绑定当前轮次最新一次派发代际（`sequence_id >= latest_dispatch_seq`）**。一旦管理员执行 `RETRY_REVIEW` 触发重新派发，新生成的 `sequence_id` 自动使上一代际的超时记录失效；重试窗口内如期提交的新票正常参与共识，完全对齐 PRD §3.3 E9。 | 新增 `test_retry_review_override_full_recovery_and_consensus`：<br>1. 真实模拟 Timeout -> HOLD -> RETRY_REVIEW；<br>2. 新代际内全员如期提交 YES_APPROVE；<br>3. 强断言 `change.to_state == AgentState.MERGING`，`decision == APPROVED`，`resolution == automatic`，票面 2 approve / 0 abstain，无迟到隔离。<br><br>新增 `test_retry_review_override_repeated_timeout_holds`：<br>断言若重试轮次内再次超时，系统正确捕获新代际超时并稳定 HOLD。 |
| **P2-CARRY-1** | **规范** | Claude, Grok | **`test-clis` 中 ANSI Strip 列为硬编码字面量 `True`** | 修复 `src/macao/adapter/integ_harness.py:108`：引入 `ANSI_ESCAPE_RE`，真实逐行扫描捕获的 `clean_logs`，断言 0 残留 ANSI 控制转义符。 | `macao test-clis` 实测 4/4 真实 ANSI 转义清洗检测通过。 |
| **Schema 单测覆盖** | **规范** | Grok, Qwen | **`test_schemas_dir_lookup_and_env_override` 未真实设置 `MACAO_SCHEMAS_DIR` 环境变量** | 修复 `tests/test_config.py:116-128`：使用 `tempfile.TemporaryDirectory()` 真实注入环境变量，验证多级寻址与环境变量覆盖行为。 | 单测 100% 覆盖并通过。 |
| **GOV-1 治理与对账** | **治理** | Qwen, Claude, Grok | **注册表报告更名与台账总数勘误** | 将 `2026-08-29-review-result-bf5ae2d-zcode.md` 更名为以 `-qwen.md` 命名，并在 `STATUS.md` 中修正历史累计总数为 **55 份结果 + 11 份申请**。 | 评审注册表与文件目录 100% 对账。 |

---

## 二、代码与系统机验命令清单

```bash
# 1. 全量 60 项单元与场景测试（60/60 全部 PASS，100% 通过）
PYTHONPATH=src python3 -m unittest discover tests -v

# 2. 五轮连续全量高压回归（300 次用例执行，0 flake / 0 碰撞 / 0 崩溃）
for i in {1..5}; do PYTHONPATH=src python3 -m unittest discover tests -v > /dev/null || exit 1; echo "Run $i PASS"; done

# 3. 4 款真实 AI CLI 进程生命周期与 PTY/ANSI 强杀机验
PYTHONPATH=src python3 -m macao.cli.main test-clis

# 4. Phase 2 端到端微任务协同仿真（Adapter 契约驱动、5 份产物归档、5 份数据库账本全 consumed=1 / 全 64 位 sha256）
PYTHONPATH=src python3 -m macao.cli.main e2e-run

# 5. 代码差异洁净度
git diff --check 99526aa..HEAD
```

---

## 三、申请定级结论请求

本轮提交已彻底闭环四方专家一致指出的 `P1-NEW-8 / P1-Q3 / P1-1`（E9 重试代际超时解绑与自动共识恢复），并完成了 ANSI 真实校验与单测覆盖。

全量 60 项测试、5 轮连续回归（300/300）、真实 CLI PTY 及 E2E 全流程仿真均 100% 通过且零告警。

特此向专家委员会（Claude / Codex / Qwen / Grok / Kimi）正式发起 **L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)** 终局封板认证复审申请，请求专家委员会开展复验并授予定级认证。
