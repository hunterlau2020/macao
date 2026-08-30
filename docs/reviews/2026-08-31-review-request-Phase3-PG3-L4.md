# MACAO Phase 3（PG-3 / L4 RELEASE-READY）多 Agent 真实协同与发布就绪评审申请

- **申请日期**：2026-08-31
- **待审对象**：Commit `3c5ed32`
- **申请目标**：**L4 RELEASE-READY / PG-3 (Product Gate 3)**
- **前序状态**：已全票获得五方专家委员会（Claude, Qwen, Kimi, Grok, ZCode）授予 **L3 SCENARIO-VERIFIED / PG-2** 终局认证

---

## 一、Phase 3 核心交付物与架构演化

### 1. 真实多 Agent Worktree 派发与两级输出自愈器 (`src/macao/workflow/live_dispatcher.py`)
- **`LiveAgentDispatcher`**：
  - 自动为每个配置的 Reviewer 在 `.macao/worktrees/<task_id>/<reviewer_id>` 动态创建独立的 Git Worktree；
  - 在独立 Worktree 内通过 PTY 隔离拉起真实 AI CLI 进程（支持 `opencode`, `claude-code`, `codex`, `agy`, `cursor`/`agent`, `kimi`）；
  - 注入 Diff 审查上下文，并监控进程输出与超时倒计时。
- **`ReviewExtractor`（两级自愈解析器）**：
  - **Level 1**：自动剥离 ANSI 颜色码，通过正则表达式提取 Markdown 代码块（```yaml ... ```）或文本 YAML；
  - **Level 2**：对提取的 YAML 实施 Draft-07 先验 Schema 强校验，自动对齐 `opinion.status` 与 `vote` 映射关系，自动补齐缺省元数据（`reviewer.id`, `checkpoint_ref`, `review_round`）。

### 2. 生产级后台守护轮询器与超时降级 (`src/macao/workflow/daemon.py`)
- **`OrchestratorDaemon`**：
  - 监控活跃任务与各审查员截止时间（Deadline Epoch）；
  - 遇到审查员超时自动生成 `REVIEWER_TIMEOUT_ABSTAIN` 审计事件，将超时成员置为 `ABSTAIN` 弃权票；
  - 自动触发共识仲裁，安全流转至 `CONSENSUS_CHECK` (HOLD)，通知人类干预或重试；
  - 提供单次安全扫描模式（`macao daemon --once`）与持续后台守护模式。

### 3. 智能初始化向导与 Git 运行时隔离保护 (`src/macao/cli/wizard.py`)
- **`macao setup` 智能向导**：
  - `probe_available_clis`：自动扫描系统 PATH 中安装的 AI CLI 及其真实版本与可用模型；
  - `detect_git_context` & `detect_ci_command`：自动推断 Git 目标分支与项目测试命令（`pytest -q`, `npm test`, `cargo test`, `go test` 等）；
  - `ensure_gitignore_isolation`：自动在被管项目的 `.gitignore` 中追加 `.macao/worktrees/` 与 `*.db` 隔离项，彻底杜绝审查工作区与状态数据污染主代码库。

### 4. Python 包资源打包改造 (`src/macao/schemas/` & `pyproject.toml`)
- **包资源内嵌**：
  - 将 6 款 Draft-07 JSON Schema 文件直接打包至 `src/macao/schemas/` Python 模块中；
  - 在 `pyproject.toml` 中配置 `tool.setuptools.package-data`；
  - `SchemaValidator` 优先加载包内内置 schemas，彻底解决 `pip install` 后的路径脱钩问题（永久关闭历史遗留 P2/P3）。

### 5. 细粒度模型控制与多元团队角色矩阵
- **全角色互通**：OpenCode, Google Antigravity (agy), Cursor Agent (agent), Claude Code, Codex, Kimi 均已支持作为 **Executor** 或 **Reviewer**；
- **细粒度模型指定**：在 `macao.yaml` 的 `team.executor.model` 与 `team.reviewers[].model` 中直接声明具体模型（如 `GLM 5.3 max`, `Qwen3.8 max`, `claude-3-7-sonnet`, `gemini-2.0-pro` 等），底层 PTY 进程自动透传 `-m / --model` 参数。

### 6. Phase 3 真实微任务全闭环协同实机演练 (`src/macao/workflow/live_runner.py` & `macao live-run`)
- 实现了真实多 Agent 全生命周期演练流水线：
  1. `1. Task Start` (FSM `CODING`)
  2. `2. Development Commit` (Git Commit + `.dev.yml` 生成)
  3. `3. Checkpoint Validation` (Schema 强校验 + `is_ancestor` 拓扑门禁 $\rightarrow$ `READY_FOR_REVIEW`)
  4. `4. Worktree Dispatch` (动态为 3 位 Reviewer 创建物理隔离工作区 $\rightarrow$ `WAITING_REVIEW`)
  5. `5. Consensus Evaluation` (提取 3 份审查意见 $\rightarrow$ 2/3 多数票仲裁 $\rightarrow$ `MERGING`)
  6. `6. Fast-Forward Merge` (CI 门禁 + 人工签字 + `git merge --ff-only` $\rightarrow$ `DONE`)
  7. `7. Final State` (状态库标记消费，多代际证据归档)

---

## 二、实机验证与测试指标

| 检验项 | 命令 | 预期标准 | 实测结果 | 结论 |
|---|---|---|---|---|
| **全量单元与集成测试** | `PYTHONPATH=src python3 -m unittest discover tests -v` | 72 项全部通过，0 失败 | **Ran 72 tests in 21.55s, OK (100% PASS)** | ✅ PASS |
| **代码与配置编译检查** | `python3 -m compileall -q src tests && git diff --check` | 0 语法错误，0 差异警告 | **Exit Code 0, 100% Clean** | ✅ PASS |
| **Phase 3 端到端协同** | `PYTHONPATH=src python3 -m macao.cli.main live-run` | 7 步全闭环，最终状态 DONE | **7/7 步骤全绿，Task State: DONE** | ✅ PASS |
| **后台守护扫描** | `PYTHONPATH=src python3 -m macao.cli.main daemon --once` | 正常单次扫描并退出 | **Single scan completed, Exit Code 0** | ✅ PASS |
| **真实 CLI 探活与预检** | `PYTHONPATH=src python3 -m macao.cli.main preflight` | 6 款 CLI 及通信组件就绪 | **Preflight Report 全绿 (OK)** | ✅ PASS |
| **PTY 伪终端沙箱冒烟** | `PYTHONPATH=src python3 -m macao.cli.main test-clis` | PTY 会话拉起、ANSI 过滤、0 僵尸 | **Verdict: PASS (0 Zombie)** | ✅ PASS |

---

## 三、申请评审与定级建议

特此向专家委员会（Claude, Qwen, Kimi, Grok, ZCode, Codex）申请对 Commit `3c5ed32` 开展 **Phase 3（PG-3 / L4 RELEASE-READY）发布就绪定级评审**，请各位专家重点审查：
1. `LiveAgentDispatcher` 与 `ReviewExtractor` 的输出自愈、Schema 校验与 Git Worktree 隔离安全性；
2. `OrchestratorDaemon` 的超时自动降级与状态机驱动一致性；
3. `macao setup` 智能向导与 `.gitignore` 运行时环境隔离机制；
4. `src/macao/schemas/` 包数据资产的打包规范与 Draft-07 强校验完整性。
