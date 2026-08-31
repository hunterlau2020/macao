# MACAO Phase 3（PG-3 / L4 RELEASE-READY）终审验收申请

- **申请日期**：2026-08-31
- **待审对象**：Commit 范围 `15e8918` .. `HEAD`（完整范围 `3c5ed32` .. `ac32dbb`）
- **申请目标**：**L4 RELEASE-READY / PG-3 (Product Gate 3)**
- **前序状态**：四方专家（Claude, Qwen, GLM, Grok）对 `15e8918` / `c44e54b` 进行独立复审，维持 L3/PG-2 有效；所提阻断项与加固项已全量在 Commit `ac32dbb` 中完成物理闭环修复与系统性加固。

---

## 一、专家复审结论对账与整改闭环清单

| 阻断/加固项编号 | 来源专家 | 涉及模块与问题描述 | 本轮物理闭环与加固方案 | 机验与测试支撑 |
|---|---|---|---|---|
| **P1-R-1 / P1-Q4 / P1-1 (Grok) / P1-R1 (GLM)** | Claude / Qwen / Grok / GLM | **`live-run` 真实协同与操作员签字真实性**<br>1. `live_runner.py` 未实际调用 `LiveAgentDispatcher`，由 runner 代写 YAML；<br>2. 自动写入 `HUMAN_MERGE_APPROVED` 包含虚假人类操作员声明。 | **真实 Worktree 派发与诚实签字机制**：<br>1. `LiveWorkflowRunner` 真实调用 `self.dispatcher.dispatch_review_in_worktree`，为每个 Reviewer 在 `.macao/worktrees/<id>/<task_id>/r1` 创建独立物理 Worktree，调度适配器生成评审产物，并在完成后物理原子清理；<br>2. 移除虚假人类证明，`--auto-signoff` 诚实记录 `signer: "system-runner"`，`note: "Automated runner signoff (--auto-signoff)"`。 | `test_live_workflow_runner_end_to_end_cycle`<br>`test_live_dispatcher_worktree_mock_execution`<br>`macao live-run` 7 步全绿实测 |
| **P1-R-2 / P2-1 (Grok)** | Claude / Grok | **`LiveAgentDispatcher` 与 `MockAgentAdapter` 契约接线**<br>`MockAgentAdapter` 缺少 `cli_name` 默认参数，导致免额度沙箱派发报 `TypeError`。 | **适配器工厂与 Mock 构造对齐**：<br>1. `MockAgentAdapter.__init__` 支持默认 `cli_name="mock-cli"`；<br>2. `get_adapter_for_reviewer` 准确构造并传递 `cli_type`。 | `test_live_dispatcher_worktree_mock_execution` 验证物理 Worktree 创建、提取与回收 |
| **P1-R-3 / P1-R-4 / A6 (Qwen)** | Claude / Qwen | **`ReviewExtractor` 候选块仲裁与矛盾票防御**<br>1. 首块匹配提前返回导致丢弃末尾真实修正意见；<br>2. 矛盾输入（`vote: NO_APPROVE` + `status: APPROVED`）被静默偏向调和为赞成；<br>3. 适配器提示词缺少 `review_round` 与 `diff`。 | **末块优先与严格 Fail-Closed 防御**：<br>1. 遍历所有 YAML 代码块，优先选取**最后出现的有效块**（最新评审结果）；<br>2. 增加矛盾校验：若 `vote` 与 `status` 存在逻辑矛盾，立即拒绝（Fail-Closed）；<br>3. 所有 CLI 适配器注入 `review_round`、`diff` 及有效投票指令。 | `test_review_extractor_last_valid_block_wins`<br>`test_review_extractor_rejects_contradictory_vote_and_status` |
| **P1-R-5 / P2-R3 (GLM)** | Claude / GLM | **三值投票 Schema 与 `ABSTAIN` 映射完备性**<br>`review_manifest.schema.json` 缺少 `ABSTAIN` 导致合法弃权无法提交。 | **Schema 与类型定义三值闭环**：<br>1. `review_manifest.schema.json`（src 与 docs）及 `types.py` 同步支持 `ABSTAIN` 投票与 `ABSTAINED` 状态；<br>2. `allOf` 约束增加 `ABSTAINED` $\leftrightarrow$ `ABSTAIN` 互锁。 | `test_review_manifest_schema`<br>`test_review_extractor_supports_abstain` |
| **P2-R-1 / P2-2 (Grok)** | Claude / Grok | **`.gitignore` 存量升级与单测覆盖**<br>向导遇到已有 `.macao/worktrees/` 时跳过后续规则追加。 | **逐行差量扫描与幂等升级**：<br>`wizard.py` 重构为逐条比对缺失规则，幂等追加 9 条运行时隔离规则，单测覆盖存量升级。 | `test_wizard_gitignore_isolation_upgrade` |
| **P2-R-5 / P2-3 (Grok)** | Claude / Grok | **2/3 多数票算术配置冲突**<br>`wizard.py` 写入 `min_effective_votes: len(reviewers)` 导致实际退化为全票否决。 | **多数票数学算术修正**：<br>`generate_smart_config` 修正 `min_effective_votes` 为 `math.ceil(2 * len(reviewers) / 3)`。 | `test_wizard_probes_and_smart_config` |
| **P1-5 (Qwen)** | Qwen / Codex | **`macao setup` 覆盖已有配置防护**<br>向导无条件覆盖已有 `macao.yaml`。 | **配置备份防护机制**：<br>`setup_wizard` 在覆写前自动对已有配置生成 `macao.yaml.bak.<timestamp>` 备份。 | `macao setup` 实机运行验证 |
| **P1-6 (Qwen) / P2-4 (Grok) / P2-6 (Grok)** | Qwen / Grok / GLM | **手册一致性、徽章对齐与空白洁净度**<br>1. FAQ 引用废弃的 `e2e-run`；<br>2. README 预授 L4 徽章；<br>3. `UC1-init-gemini.md` 尾随空格导致 diff check rc=2。 | **全量同步与格式规范化**：<br>1. FAQ 修正为 `live-run` 并对齐自愈机制；<br>2. README 徽章对齐为 `L3 SCENARIO-VERIFIED / PG-2` 与 `81/81 PASS`；<br>3. UC1 尾随空格已清除，`git diff --check` 0 警告。 | `git diff --check 3c5ed32..HEAD` 返回 0 |
| **OPS / 人工接管实机演练** | 四方共识 | **L4 硬判据：人工接管实机演练**<br>需验证超时/僵局 $\rightarrow$ `CONSENSUS_CHECK` (HOLD) $\rightarrow$ `override resolve` 完整闭环。 | **人工接管全流程实操测试**：<br>实现 1 赞成 + 1 反对 + 1 超时弃权触发 `DEADLOCK`（HOLD 于 `CONSENSUS_CHECK`），经 `resolve_override("APPROVED")` 解除并合入主分支。 | `test_manual_override_resolution` 100% PASS |

---

## 二、实机验证与测试指标

| 检验项 | 执行命令 | 预期标准 | 实测结果 | 结论 |
|---|---|---|---|---|
| **全量自动化测试** | `PYTHONPATH=src python3 -m unittest discover tests -v` | 81 项单测/集成测试全部通过，0 失败 | **Ran 81 tests, OK (100% PASS)** | ✅ PASS |
| **代码与差异洁净度** | `python3 -m compileall -q src tests && git diff --check 3c5ed32..HEAD` | 0 语法错误，0 尾随空白 | **Exit Code 0, 100% Clean** | ✅ PASS |
| **Phase 3 端到端协同** | `PYTHONPATH=src python3 -m macao.cli.main live-run` | 真实 Worktree 隔离派发，7 步全闭环，归档 5 份产物 PERSISTED | **7/7 步骤全绿，5/5 产物 PERSISTED，DONE** | ✅ PASS |
| **后台守护扫描** | `PYTHONPATH=src python3 -m macao.cli.main daemon --once` | 正常单次扫描并退出 | **Single scan completed, Exit Code 0** | ✅ PASS |
| **真实 CLI 探活与预检** | `PYTHONPATH=src python3 -m macao.cli.main preflight` | 6 款 CLI 及通信组件就绪 | **Preflight Report 全绿 (OK)** | ✅ PASS |
| **PTY 伪终端沙箱冒烟** | `PYTHONPATH=src python3 -m macao.cli.main test-clis` | PTY 会话拉起、ANSI 过滤、0 僵尸 | **Verdict: PASS (0 Zombie)** | ✅ PASS |

---

## 三、申请评审与定级建议

特此向专家委员会（Claude, Qwen, GLM, Grok, ZCode, Codex）申请对当前 Commit 开展 **Phase 3（PG-3 / L4 RELEASE-READY）终审验收**。
全部 4 份专家评审报告所提阻断项与加固项已全部完成物理代码闭环与测试验证。
