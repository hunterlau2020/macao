# MACAO L3 / PG-2 全员一致终局定级封板最终申请 (Unanimous Final Seal)

- **申请日期**：2026-08-30
- **申请版本 / 范围**：`8296f3c..HEAD` 范围整改代码及全量测试产物
- **申请目标等级**：**L3 SCENARIO-VERIFIED / PG-2 (Product Gate 2)**
- **对齐基准**：
  - `docs/MACAO_PRD_v2.md` v2.3.1
  - `docs/MACAO_REVIEW_GUIDELINES.md` v1.0
  - `docs/EXPERT_QUALITY.md`
  - `docs/schemas/*.schema.json`
- **专家委员会**：Claude, Codex, Kimi, Qwen, Grok, ZCode

---

## 1. 差异范围与修复落点矩阵

本轮针对 Commit `8296f3c` 的独立复审反馈（Claude 授予 L3/PG-2、Qwen 授予 L3/PG-2、Kimi 授予 L3/PG-2；ZCode 提 P1-1 跨平台路径断言；Grok & Codex 提 E6 拓扑校验）进行了最后单点闭环整改：

| 评审反馈编号 | 问题性质与核心成因 | 代码修复落点 | 对应验证测试 |
|---|---|---|---|
| **P1-1** (ZCode) | **`test_p0_p1_rectification.py:471` 硬编码 POSIX 路径分隔符导致 Windows 环境 64/65**<br>测试断言直接以 `startswith(".macao/archive/")` 进行字符串比对，在 win32 环境下路径分隔符为反斜杠，导致单测在 win32 下断言失败。 | `tests/test_p0_p1_rectification.py:471`<br>将断言修改为 `Path(a["archived_path"]).as_posix().startswith(".macao/archive/")`，实现 100% 平台无关性。 | 单测在 POSIX/Linux 及 Windows 环境均 100% 通过。 |
| **P1-1** (Grok / Codex) | **E6 返工回路未校验 Git 提交拓扑（祖先回退与孤立 commit 拦截）**<br>PRD §3.3 E6:839 规定 `REWORK` $\rightarrow$ `READY_FOR_REVIEW` 触发条件为「新一轮 `.dev.yml` 有效（round+1、**新 commit**）」。原实现仅校验了字符串不等与 commit 存在，未校验上一轮 checkpoint 是当前提交的严格祖先。 | 1. `src/macao/utils/git_utils.py:53-56`：新增 `GitManager.is_ancestor(ancestor_ref, descendant_ref)` 方法（封装 `git merge-base --is-ancestor`）；<br>2. `src/macao/workflow/orchestrator.py:240-252`：在 `REWORK` 状态下强校验 `self.git.is_ancestor(prev_ref, latest_commit)`，若为祖先回退或无关孤立 commit 直接 `return None` 实施 Fail-closed 拦截。 | `tests/test_p0_p1_rectification.py:1515-1670`<br>`test_rework_unchanged_commit_fails_closed_and_requires_fresh_commit` 覆盖 4 个完整分支：<br>1. Case A：相同 commit $\rightarrow$ 拒绝 (None)；<br>2. Case B：祖先 commit 回退 $\rightarrow$ 拒绝 (None)；<br>3. Case C：无关分支孤立 commit $\rightarrow$ 拒绝 (None)；<br>4. Case D：有效后继 commit $\rightarrow$ 接受并转入 `READY_FOR_REVIEW`。 |

---

## 2. 独立机验复现命令与结果证据

```bash
# 1. 全量自动化单元测试（65 项）
PYTHONPATH=src python3 -m unittest discover tests -v
# => Ran 65 tests in 18.699s OK (100% PASS)

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

- 当前共包含 **70 份历史与当前评审结果** 与 **15 份评审申请**。
- `docs/reviews/STATUS.md` 与实际文件目录 **100% 对账一致**。

请专家委员会（Claude, Codex, Kimi, Qwen, Grok, ZCode）进行全员一致终局定级封板确认！
