# MACAO L3 / PG-2 终局定级复审申请

- **申请日期**：2026-08-30
- **申请版本 / 范围**：`3e1a991..HEAD` 范围全量整改代码及测试产物
- **申请目标等级**：**L3 SCENARIO-VERIFIED / PG-2 (Product Gate 2)**
- **对齐基准**：
  - `docs/MACAO_PRD_v2.md` v2.3.1
  - `docs/MACAO_REVIEW_GUIDELINES.md` v1.0
  - `docs/EXPERT_QUALITY.md`
  - `docs/schemas/*.schema.json`
- **专家委员会**：Claude, Codex, Kimi, Qwen, Grok

---

## 1. 差异范围与修复落点矩阵

本轮针对 2026-08-30 三方独立复审结论（`3e1a991-claude`、`3e1a991-codex`、`3e1a991-kimi`）中指出的核心问题进行了单点闭环整改：

| 评审反馈编号 | 问题性质与核心成因 | 代码修复落点 | 对应验证测试 |
|---|---|---|---|
| **P1-NEW-9** (Claude) / **P1-1** (Codex) | **E9 `RETRY_REVIEW` 代际归档覆写与证据销毁**<br>重试后第二代际（Gen 2）产物在归档时使用固定路径覆盖第一代际（Gen 1），导致作废的历史反对票和人工裁定被物理销毁，破坏审计链哈希完整性（PRD §14.5）。 | `src/macao/workflow/fsm.py:80-135`<br>1. 引入 `_get_generation(task_id, review_round)` 计算派发代际；<br>2. `_archive_file` 与 `_archive_reviews` 检测已有文件哈希，若存在异动则以代际版本另存（`g{gen}_{name}`），彻底杜绝静默覆盖；<br>3. 每次归档触发不可变 `ARTIFACT_ARCHIVED` 审计日志，留存代际、路径与 SHA256。 | `tests/test_p0_p1_rectification.py:1141-1224`<br>`test_multi_generation_archiving_preserves_gen1_evidence_immutable`：实测 Gen 1 反对票（`GEN1-DISSENT`）在重试并达成共识后，在磁盘归档与 `ARTIFACT_ARCHIVED` 审计日志中 100% 完整留存。 |
| **P2-NEW-4** (Claude) | **`RETRY_REVIEW` 活跃目录残存 `vote_result.json`**<br>重试时生成的人工裁定 `vote_result.json` 在归档后留在活跃目录，若 Gen 2 随后崩溃，`reconcile.py` 会误将任务回退为 `WAITING_REVIEW`。 | `src/macao/workflow/orchestrator.py:811-820`<br>在 `resolve_override("RETRY_REVIEW")` 中，归档并重新派发后，主动从活跃 `.macao/` 目录中清理 `vote_result.json`。 | `tests/test_p0_p1_rectification.py:1226-1268`<br>`test_retry_review_cleans_active_vote_result_file`：断言 E9 重试后活跃目录不再残留 `vote_result.json`。 |
| **P3-NEW-7** (Claude) | **`LATE_REVIEW_ISOLATED` 审计日志缺少幂等**<br>轮询调用 `collect_and_evaluate_consensus` 时，超时后的迟到票会反复记录审计日志。 | `src/macao/workflow/orchestrator.py:510-525`<br>增加代际内 `already_logged` 幂等守卫，单代际内单 Reviewer 仅记录一次隔离日志。 | `tests/test_p0_p1_rectification.py:1270-1317`<br>`test_late_review_isolated_audit_is_idempotent`：连续轮询 20 次，断言 `LATE_REVIEW_ISOLATED` 审计记录严格为 1 条。 |
| **P1-2** (Kimi) | **`check_development_checkpoint` 先验校验不完整**<br>原实现未强校验 `signal == EXPLICIT`、`tests_passed` 及 git commit 物理存在性。 | `src/macao/workflow/orchestrator.py:221-236`<br>强校验 `signal == "EXPLICIT"`、`tests_passed`（或 `tests_exempt`）以及 `git.commit_exists(latest_commit)`，不合规清单 Fail-closed 拒绝转移。 | `tests/test_p0_p1_rectification.py:1319-1372`<br>`test_check_development_checkpoint_validation_fail_closed`：覆盖测试失败、伪造 commit、有效清单三分支。 |

---

## 2. 独立机验复现命令与结果证据

```bash
# 1. 全量自动化单元测试（64 项）
PYTHONPATH=src python3 -m unittest discover tests -v
# => Ran 64 tests in 16.924s OK

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

- 当前共包含 **58 份历史评审结果** 与 **12 份评审申请**。
- `docs/reviews/STATUS.md` 与实际文件目录 **100% 对账一致**。

请专家委员会对本轮整改进行终局复验！
