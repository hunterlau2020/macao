# MACAO Phase 3（PG-3 / L4 RELEASE-READY）加固整改复审申请

- **申请日期**：2026-08-31
- **待审对象**：Commit 范围 `3c5ed32` .. `HEAD`
- **申请目标**：**L4 RELEASE-READY / PG-3 (Product Gate 3)**
- **前序状态**：四方专家（Claude, Codex, Grok, Qwen）对 `3c5ed32` 进行审查并维持 L3/PG-2 有效；所提 10 项阻断性与加固性问题（P1-1~P1-4 / P2-7/8/9 / P1-Q4/5/6）已全部在本次提交中完成物理闭环修复与全量加固。

---

## 一、对账与整改闭环清单

| 阻断/加固项编号 | 来源专家 | 涉及模块与问题描述 | 本轮闭环与加固方案 | 机验与测试支撑 |
|---|---|---|---|---|
| **P1-1 / P1-NEW-13 / P1-Q6** | Claude / Codex / Grok / Qwen | **`ReviewExtractor` 缺票默认赞成与幻影批准风险**<br>缺失 vote/status 或无关 YAML 默认回退为 `YES_APPROVE`/`APPROVED`。 | **彻底 Fail-Closed 防御**：<br>1. 若 YAML 缺失显式 `vote` 且缺失 `opinion.status`，立即判定提取失败返回 `False`；<br>2. 强上下文匹配：若包含 `checkpoint_ref`、`review_round`、`reviewer.id`，必须与派发目标逐字节强一致，否则直接拒绝；<br>3. `vote.py` 与 `orchestrator.py` 移除所有软 fallback 默认值。 | `test_review_extractor_rejects_missing_vote_and_status`（5 款非评审文本均失败）<br>`test_review_extractor_rejects_mismatched_context`（3 维上下文不符均拒绝） |
| **P1-2 / P1-NEW-14 / P1-Q5** | Claude / Codex / Grok / Qwen | **`OrchestratorDaemon` 活跃超时扫描崩溃与契约错配**<br>审计事件名、`detail` 键名、产物 kind 错配，导致活跃任务无法自动降级弃权。 | **单一事实源收敛与超时流转**：<br>1. 直接复用 `Orchestrator.detect_timed_out_reviewers`；<br>2. 自动记录 `REVIEWER_TIMEOUT_ABSTAIN` 审计事件，并将超时人员作为 `timed_out_reviewers` 显式驱动 FSM 仲裁（进入 HOLD）；<br>3. `run_loop` 异常可见（输出至 stderr，杜绝裸 pass）。 | `test_daemon_active_task_timeout_degradation`（验证 0s 超时任务自动识别、记入 ABSTAIN 并流转） |
| **P1-3 / P1-NEW-15 / P1-Q4** | Claude / Codex / Grok / Qwen | **`LiveWorkflowRunner` 与 UI 界面展示对齐**<br>未走 feature 分支开发、未真实通过 Extractor 解析、UI 归档状态因字段错配变红、耗时硬编码。 | **真实协同流程重塑**：<br>1. 真实切换 `feature/calc-live` 分支执行开发提交；<br>2. 评审输出严格通过 `ReviewExtractor` 提取与 Draft-07 强校验；<br>3. `ui.py` 修复物理归档字段统计（5 份产物全部匹配渲染绿色 `PERSISTED`）；<br>4. 计时改为系统级高精耗时，记录真实操作员签字。 | `test_live_workflow_runner_end_to_end_cycle`<br>`macao live-run` 7 步全绿实机演练 |
| **P1-4 / P1-2 (Grok)** | Codex / Grok | **`LiveAgentDispatcher` 准入 Fail-Closed 与 API 接线**<br>未知 CLI 软回退、Worktree 创建方法名未对齐 `GitManager`。 | **标准 Worktree API 与 Fail-Closed 准入**：<br>1. 对接 `GitManager.create_isolated_worktree`（路径 `.macao/worktrees/<agent_id>/<task_id>/r<round>`）；<br>2. `get_adapter_for_reviewer` 对未知 CLI 严格抛出 `ValueError`。 | `live_dispatcher.py:215` 准入强校验 |
| **P2-NEW-8** | Claude | **向导单测环境解耦**<br>`assertTrue(len(clis) > 0)` 强依赖宿主 PATH 已安装 CLI。 | **解耦环境依赖**：<br>改为 `assertIsInstance(clis, list)`，保障任何裸机/容器构建环境均能稳定通过。 | `test_wizard_probes_and_smart_config` 跨环境 100% 稳定 PASS |
| **P2 (Git 隔离)** | Codex / Claude | **`.gitignore` 隔离规则不完备**<br>未能完全覆盖 `.macao/` 临时文件与 SQLite Journal。 | **完备运行时隔离**：<br>向导自动注入 `.macao/worktrees/`, `.macao/.reviews/`, `.macao/.dev.yml`, `.macao/vote_result.json`, `.macao/archive/`, `.macao/*.db*`。 | `test_wizard_probes_and_smart_config` 验证 6 项规则注入与幂等性 |
| **PRD / 架构对齐** | 用户特别关注项 | **`agmsg` 映射与团队配置一致性**<br>避免配置分裂（Split-Brain），同时保留与 `agmsg` 总线通信桥梁。 | **配置桥接与架构文档同步**：<br>1. Schema 增加 `team.name` 与 `agmsg_member_id` 映射；<br>2. PRD v2.4 补齐 §17~§20 规范；<br>3. `README.md` 与 `docs/FAQ.md` 全量更新。 | `test_config.py` Schema 校验单测 100% PASS |

---

## 二、实机验证与测试指标

| 检验项 | 执行命令 | 预期标准 | 实测结果 | 结论 |
|---|---|---|---|---|
| **全量自动化测试** | `PYTHONPATH=src python3 -m unittest discover tests -v` | 75 项单测/集成测试全部通过，0 失败 | **Ran 75 tests in 23.82s, OK (100% PASS)** | ✅ PASS |
| **代码与差异洁净度** | `python3 -m compileall -q src tests && git diff --check` | 0 语法错误，0 尾随空白 | **Exit Code 0, 100% Clean** | ✅ PASS |
| **Phase 3 端到端协同** | `PYTHONPATH=src python3 -m macao.cli.main live-run` | 7 步全闭环，归档 5 份产物全部 PERSISTED | **7/7 步骤全绿，5/5 产物 PERSISTED，DONE** | ✅ PASS |
| **后台守护扫描** | `PYTHONPATH=src python3 -m macao.cli.main daemon --once` | 正常单次扫描并退出 | **Single scan completed, Exit Code 0** | ✅ PASS |
| **真实 CLI 探活与预检** | `PYTHONPATH=src python3 -m macao.cli.main preflight` | 6 款 CLI 及通信组件就绪 | **Preflight Report 全绿 (OK)** | ✅ PASS |
| **PTY 伪终端沙箱冒烟** | `PYTHONPATH=src python3 -m macao.cli.main test-clis` | PTY 会话拉起、ANSI 过滤、0 僵尸 | **Verdict: PASS (0 Zombie)** | ✅ PASS |

---

## 三、申请评审与定级建议

特此向专家委员会（Claude, Qwen, Kimi, Grok, ZCode, Codex）申请对当前 Commit 开展 **Phase 3（PG-3 / L4 RELEASE-READY）发布就绪定级加固复审**。
所有评审专家在上一轮指出的阻断性问题已全部实测闭环，全套系统具备生产级鲁棒性。
