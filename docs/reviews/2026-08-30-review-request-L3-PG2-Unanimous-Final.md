# MACAO L3 / PG-2 全员一致终局定级复审申请 (Unanimous Final)

- **申请日期**：2026-08-30
- **申请版本 / 范围**：`7973853..HEAD` 范围整改代码及全量测试产物
- **申请目标等级**：**L3 SCENARIO-VERIFIED / PG-2 (Product Gate 2)**
- **对齐基准**：
  - `docs/MACAO_PRD_v2.md` v2.3.1
  - `docs/MACAO_REVIEW_GUIDELINES.md` v1.0
  - `docs/EXPERT_QUALITY.md`
  - `docs/schemas/*.schema.json`
- **专家委员会**：Claude, Codex, Kimi, Qwen, Grok

---

## 1. 差异范围与修复落点矩阵

本轮针对 2026-08-30 四方独立复审结论（Qwen 支持授予、Kimi 授予、Claude REJECT 提 P1-NEW-11、Codex REJECT 提 P1-1/P1-2）中指出的核心问题进行了单点彻底闭环：

| 评审反馈编号 | 问题性质与核心成因 | 代码修复落点 | 对应验证测试 |
|---|---|---|---|
| **P1-NEW-11** (Claude) / **P1-1** (Codex) / **P3-1** (Kimi) | **`check_development_checkpoint` 缺少 Schema 校验且缺省字段 Fail-Open**<br>原实现对缺少 `version`、`executor`、`signal` 或 `quality_metrics` 的残缺 `.dev.yml` 清单通过 fallback 默认值放行，未调用 `validate_dev_manifest`，违反 PRD §2.1 Fail-closed 契约。 | `src/macao/workflow/orchestrator.py:221-236`<br>1. 先行调用 `validate_dev_manifest(data)` 进行 Draft-07 全量 Schema 校验，任何字段缺失或类型错误直接 `return None`；<br>2. 严格执行不变式校验（无宽容默认值）：`signal == "EXPLICIT"`、`tests_passed is True`、`review_round` 匹配以及 `git.commit_exists(latest_commit)`。 | `tests/test_p0_p1_rectification.py:1340-1430`<br>`test_check_development_checkpoint_validation_fail_closed` 穷举 9 个测试分支：<br>1. 缺失 `quality_metrics` 块 -> 拒绝 (None)<br>2. 缺失 `signal` 字段 -> 拒绝 (None)<br>3. `signal: IMPLICIT` -> 拒绝 (None)<br>4. 缺失 `version` 字段 -> 拒绝 (None)<br>5. 仅 4 行残缺清单 -> 拒绝 (None)<br>6. `tests_passed: false` 未豁免 -> 拒绝 (None)<br>7. 伪造/不存在 commit sha -> 拒绝 (None)<br>8. `tests_exempt: true` 合规清单 -> 接受 (READY_FOR_REVIEW)<br>9. 完整合规清单 -> 接受 (READY_FOR_REVIEW) |
| **P2-NEW-5** (Claude) | **`transitions.py` 中 `E9` 未限制源状态为 `CONSENSUS_CHECK` 或 `UNKNOWN`**<br>`transitions.py:39` 原写为 `E9: (None, WAITING_REVIEW)`，与 PRD §3.3:841（限 `CONSENSUS_CHECK` / `UNKNOWN`）不符。 | `src/macao/workflow/transitions.py:47-50`<br>显式增加 `trigger_id == "E9"` 特殊分支守卫：仅允许从 `AgentState.CONSENSUS_CHECK` 或 `AgentState.UNKNOWN` 状态转移至 `AgentState.WAITING_REVIEW`，其余源状态一律拦截拒绝。 | `tests/test_p0_p1_rectification.py:1193,1270`<br>全面对齐测试中 E9 触发入口，经由共识评估僵局（`CONSENSUS_CHECK`）合法发起 `RETRY_REVIEW`。 |

---

## 2. 独立机验复现命令与结果证据

```bash
# 1. 全量自动化单元测试（64 项）
PYTHONPATH=src python3 -m unittest discover tests -v
# => Ran 64 tests in 17.212s OK

# 2. 五轮连续全量回归高压测试（320 次用例）
for i in {1..5}; do PYTHONPATH=src python3 -m unittest discover tests -v > /dev/null || exit 1; echo "Run $i PASS"; done
# => Run 1-5 PASS (0 failure / 0 error / 0 flake)

# 3. 真实 CLI PTY 跨 Agent 验证
PYTHONPATH=src python3 -m macao.cli.main test-clis
# => Claude Code, Codex, OpenCode, Agy 4/4 PASS, ANSI Strip True, 0 Zombie processes

# 4. Phase 2 端到端微任务全流程仿真
PYTHONPATH=src python3 -m macao.cli.main e2e-run
# => 7/7 步骤 OK, Task State: DONE, 5 份产物物理归档且哈希校验一致

# 5. 代码编译与 Diff 洁净度
python3 -m compileall -q src && git diff --check
# => 返回码 0, 100% Clean
```

---

## 3. 评审产物全量对账 (Review Registry)

- 当前共包含 **62 份历史与当前评审结果** 与 **13 份评审申请**。
- `docs/reviews/STATUS.md` 与实际文件目录 **100% 对账一致**。

请专家委员会对本轮整改进行终局复验与定级授予！
