# MACAO L3 / PG-2 全员一致终局定级封板申请 (Unanimous Seal)

- **申请日期**：2026-08-30
- **申请版本 / 范围**：`3ea5256..HEAD` 范围整改代码及全量测试产物
- **申请目标等级**：**L3 SCENARIO-VERIFIED / PG-2 (Product Gate 2)**
- **对齐基准**：
  - `docs/MACAO_PRD_v2.md` v2.3.1
  - `docs/MACAO_REVIEW_GUIDELINES.md` v1.0
  - `docs/EXPERT_QUALITY.md`
  - `docs/schemas/*.schema.json`
- **专家委员会**：Claude, Codex, Kimi, Qwen, Grok

---

## 1. 差异范围与修复落点矩阵

本轮针对 2026-08-30 四方独立复审结论（Qwen 支持授予、Kimi 授予、Claude 提 P1-NEW-12、Codex 提 P1-1/P2-1）中指出的核心单点进行了彻底闭环整改：

| 评审反馈编号 | 问题性质与核心成因 | 代码修复落点 | 对应验证测试 |
|---|---|---|---|
| **P1-NEW-12** (Claude) / **P1-1** (Codex) | **E6 返工回路未校验「新 commit」及「未被消费」不变式**<br>PRD §3.3 E6:839 规定 `REWORK` $\rightarrow$ `READY_FOR_REVIEW` 条件为「新一轮 `.dev.yml` 有效（round+1、**新 commit**）」；PRD §2.1:216 规定 `latest_commit` 必须「未被消费过」。原实现未对比 `latest_commit != task["checkpoint_ref"]`，导致无改动重交可被放行。 | `src/macao/workflow/orchestrator.py:237-251`<br>1. 在 `current_st == AgentState.REWORK` 下，强校验 `latest_commit != task.get("checkpoint_ref")`，相同 commit 直接 `return None` 实施 Fail-closed 拦截；<br>2. 检查 `store.list_artifacts(task_id)` 中该 commit 是否已作为 `consumed=1` 的 `dev_manifest` 记录存在，已消费 commit 一律拒绝。 | `tests/test_p0_p1_rectification.py:1510-1620`<br>`test_rework_unchanged_commit_fails_closed_and_requires_fresh_commit`：<br>1. Case A：REWORK 下以相同 commit 重交 round 2 清单 $\rightarrow$ 拒绝 (None)，状态保持 `REWORK`；<br>2. Case B：产生新 git commit 后提交 round 2 清单 $\rightarrow$ 接受并成功转入 `READY_FOR_REVIEW`。 |
| **P2-1** (Codex) | **`transitions.py` 中 `E9` 源状态额外包含了 `UNKNOWN`**<br>PRD §3.3:841 权威转换表中，`E9` 重试转换的源状态唯有 `CONSENSUS_CHECK`。 | `src/macao/workflow/transitions.py:48-51`<br>将 `E9` 守卫分支严格收敛为 `if from_state == AgentState.CONSENSUS_CHECK`，对齐 PRD 权威表。 | `tests/test_p0_p1_rectification.py` 现有 E9 用例全量通过。 |

---

## 2. 独立机验复现命令与结果证据

```bash
# 1. 全量自动化单元测试（65 项）
PYTHONPATH=src python3 -m unittest discover tests -v
# => Ran 65 tests in 17.693s OK

# 2. 五轮连续全量回归高压测试（325 次用例）
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

- 当前共包含 **66 份历史与当前评审结果** 与 **14 份评审申请**。
- `docs/reviews/STATUS.md` 与实际文件目录 **100% 对账一致**。

请专家委员会对本轮整改进行终局复验与授予定级认证！
