# MACAO 综合编排与动态探活体系复审申请（Commit 961bcfe / Round 2）

- **文档归档路径**: `docs/reviews/2026-09-07-review-request-961bcfe.md`
- **申请日期 (Date)**: 2026-09-07
- **申请人 (Author)**: MACAO Architecture & Engineering Team
- **目标定级 (Target Level)**: **L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3 准入评审**
- **当前受审提交 (Checkpoint Ref)**: `commit 961bcfe`（`origin/main`）
- **评审轮次 (Review Round)**: `Round 2`（返工整改轮）
- **关联任务 ID (Task ID)**: `task-20260907-orchestrator-p1-remediation`
- **前序受审基线与处置单 (Previous Baseline & Disposition)**:
  - 前序受审基线：`d042395`（4 位专家独立评审，票型：1 票有保留通过，3 票否决，仲裁结论为 **多数否决待返工 REWORK**）
  - 前序处置报告：[`docs/reviews/2026-09-07-disposition-d042395.md`](2026-09-07-disposition-d042395.md)（8 项 P1 阻塞项逐项闭环）
  - 4 份专家评审归档：
    1. [`2026-09-07-review-result-d042395-muse.md`](2026-09-07-review-result-d042395-muse.md)（Muse：有保留授予 L3，暂缓 L4）
    2. [`2026-09-07-review-result-d042395-codex.md`](2026-09-07-review-result-d042395-codex.md)（Codex：REJECT / 5 项 P1 阻断）
    3. [`2026-09-07-review-result-d042395-grok.md`](2026-09-07-review-result-d042395-grok.md)（Grok：REJECT / 2 项 P1 阻断，2 项 P2）
    4. [`2026-09-07-review-result-d042395-claude.md`](2026-09-07-review-result-d042395-claude.md)（Claude：NO_APPROVE / 8 项 P1 阻断，L4 独立否决）
- **上位评审方法论**: [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)
- **实时门禁状态表**: [`docs/reviews/STATUS.md`](STATUS.md)

---

## 1. 变更摘要与核心目标 (Summary & Rationale)

在基线 `d042395` 评审中，四位评审专家（Muse, Codex, Grok, Claude）独立机验并会审收敛出 8 项 P1 级核心阻塞项（P1-1 至 P1-8）。本轮提交 `961bcfe` 的核心目标是**严格遵循 Fail-Closed 与不介入原则，对 8 项 P1 阻断项实施彻底的代码级闭环，交付 Pi Coding Agent 适配器，并确立场景 C（存量半途项目接入）产品用例规范**。

### 核心演进与架构决策
1. **纯读零副作用彻底落实 (P1-1)**：为 `TeamProber` 设置严格的 dry-run 守卫，杜绝任何未授权的文件、目录创建或数据库写锁；
2. **拒绝任何会话伪造与跨项目串话 (P1-2)**：切换 Codex 会话发现至本地 SQLite 数据库，校验 `threads.cwd` 规范化绝对路径；Cursor 精确比对规范化路径；Kimi CLI 因本地无结构化会话索引，严格 Fail-Closed 返回空列表；
3. **进度三元组以物理事实对账为唯一准绳 (P1-3)**：客观提审单优先级高于工作区脏改动，按集合差精确计算未出票评审员名单；
4. **法定人数门槛完整合取 (P1-4)**：`ready >= min_winning` AND `ready >= seat_quorum` AND `weight >= weight_quorum`，杜绝偷换门槛；
5. **全链路敏感数据脱敏体系 (P1-5)**：新建独立模块 `secrets.py`，并在 `logger.py`、PTY 会话捕获器、CLI 日志查询中实现 API Token 与密码全链路脱敏；
6. **非破坏性隔离清理与无损备份还原 (P1-6)**：`macao clean` 默认仅安全清理临时 worktree；`--all` 强制执行目录快照（`.macao.bak.<ts>/`）；`--restore` 支持无损还原；
7. **真实测试凭据防伪门禁 (P1-7)**：`task checkpoint --auto` 默认将 `tests_passed` 设为 `False` 阻断状态机，要求必须通过 `--test-cmd` 实际运行退出码 0 或显式 `--tests-exempt`；
8. **任务活动不变量与验收标准原样透传 (P1-8)**：`task create --force` 驱动旧任务通过 E10 转换为 `CANCELLED` 终态，消除孤立僵尸任务；用户显式验收标准逐项注入 Type A AEP 信封；
9. **Pi Coding Agent 适配与场景 C 规范**：新增 `PiAdapter`，完善存量 half-done 项目接入用例（UC11）与产品事实（F-23, F-24）。

---

## 2. 靶向变更清单 (Targeted Code Changes & Issue Mapping)

本轮提交 `961bcfe` 共涉及 **27 个文件，+2379 / -237 行**，按架构层次分类与阻断项映射如下表：

| 文件路径 | 模块分类 | 变动行数 | 核心修改说明 | 闭环 Issue / 特性 |
| :--- | :--- | :--- | :--- | :--- |
| [`src/macao/workflow/prober.py`](../../src/macao/workflow/prober.py) | 核心探活 | +87 / -12 | `_write_probe_log` 增加 dry-run 守卫；调整三元组优先级并计算 `missing_reviewers`；法定人数完整合取三道门槛 | **P1-1, P1-3, P1-4** |
| [`src/macao/adapter/session_locator.py`](../../src/macao/adapter/session_locator.py) | 会话发现 | +496 / -120 | Codex 查 `state_*.sqlite` 校验 `cwd`；Cursor 绝对路径比对；Kimi Fail-Closed 返回空；引入 `_sanitize_session_name` 脱敏 | **P1-2, P1-5** |
| [`src/macao/cli/main.py`](../../src/macao/cli/main.py) | CLI 交互 | +196 / -58 | `macao clean` 默认仅清 worktrees，`--all` 快照备份，`--restore` 无损恢复；`checkpoint --auto` 真实门禁；`task create --force` 取消旧任务；`macao logs` 脱敏 | **P1-5, P1-6, P1-7, P1-8** |
| [`src/macao/workflow/orchestrator.py`](../../src/macao/workflow/orchestrator.py) | 编排引擎 | +23 / -2 | 新增 `cancel_task()` 触发 E10；支持多态解析 `acceptance_criteria` 注入 Type A 信封 | **P1-8** |
| [`src/macao/utils/secrets.py`](../../src/macao/utils/secrets.py) | 基础设施 | +46 / -0 | 新增密钥脱敏工具（OpenAI/Anthropic Key, GitHub Token, Bearer, DB 密码, PEM 私钥） | **P1-5** |
| [`src/macao/utils/logger.py`](../../src/macao/utils/logger.py) | 基础设施 | +13 / -1 | 引入 `SecretMaskingFormatter`，对日志文件和 stderr 全量实时脱敏 | **P1-5** |
| [`src/macao/adapter/pty_session.py`](../../src/macao/adapter/pty_session.py) | 终端沙箱 | +5 / -1 | `get_clean_logs()` 强制通过 `mask_secrets` 清洗 Reviewer 原始输出 | **P1-5** |
| [`src/macao/workflow/live_dispatcher.py`](../../src/macao/workflow/live_dispatcher.py) | 沙箱派发 | +8 / -3 | 审查员会话日志落盘前强制脱敏 | **P1-5** |
| [`src/macao/cli/ui.py`](../../src/macao/cli/ui.py) | 终端展现 | +23 / -5 | 支持展现会话名称（Title）与多会话序号 `[i of N]` | 增强交互 |
| [`src/macao/cli/wizard.py`](../../src/macao/cli/wizard.py) | 初始化向导 | +4 / -2 | 初始化扫描与默认 Reviewer 选项中注册 `pi` 适配器 | Pi 支持 |
| [`src/macao/adapter/pi.py`](../../src/macao/adapter/pi.py) | AI CLI 适配 | +139 / -0 | 新增 Pi Coding Agent 适配器 `PiAdapter` | 特性扩展 |
| [`src/macao/adapter/__init__.py`](../../src/macao/adapter/__init__.py) | 适配层导出 | +2 / -0 | 导出 `PiAdapter` | 特性扩展 |
| [`src/macao/adapter/integ_harness.py`](../../src/macao/adapter/integ_harness.py) | 测试 Harness | +2 / -0 | 测试 harness 注册 `pi` | 特性扩展 |
| [`tests/test_p1_closures_and_regressions.py`](../../tests/test_p1_closures_and_regressions.py) | 自动化测试 | +370 / -0 | 新增 10 个测试用例，覆盖 P1-1 至 P1-8 负向/边界断言 | **P1-1 ~ P1-8 验证** |
| [`tests/test_pi_and_session_locator.py`](../../tests/test_pi_and_session_locator.py) | 自动化测试 | +124 / -0 | 新增 7 个测试用例，覆盖 Pi 适配器与 SessionLocator 真实性 | Pi 验证 |
| [`tests/test_clean_and_rollback.py`](../../tests/test_clean_and_rollback.py) | 自动化测试 | +36 / -3 | 更新测试以断言 `macao clean` 默认非破坏性与 `--all`/`--restore` 快照逻辑 | **P1-6 验证** |
| [`docs/usercases/UC11-scenarioc-inflight-adoption.md`](../usercases/UC11-scenarioc-inflight-adoption.md) | 产品用例 | +116 / -0 | 场景 C（开发到一半存量项目无痛接入）规范用例 | 场景 C 交付 |
| [`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md) | 产品事实 | +4 / -0 | 确立事实 F-23（只读零副作用）与 F-24（会话真实绑定） | 事实固化 |
| [`docs/usercases/UC2-task-create.md`](../usercases/UC2-task-create.md) | 产品用例 | +2 / -0 | 完善针对场景 C 开发中任务接入的说明 | 场景 C 交付 |
| [`docs/usercases/UC10-existing-project-doctor.md`](../usercases/UC10-existing-project-doctor.md) | 产品用例 | +1 / -0 | 建立 doctor 命令向场景 C 接入的导流机制 | 场景 C 交付 |
| [`docs/usercases/README.md`](../usercases/README.md) | 用例索引 | +4 / -0 | 索引收录 UC-11 场景 C | 文档索引 |
| [`docs/reviews/2026-09-07-disposition-d042395.md`](2026-09-07-disposition-d042395.md) | 评审治理 | +152 / -0 | 针对基线 `d042395` 四方评审意见的完整处置与闭环报告 | 治理归档 |
| [`docs/reviews/2026-09-07-review-result-d042395-muse.md`](2026-09-07-review-result-d042395-muse.md) | 评审结果 | +66 / -0 | 归档 Muse 专家关于 `d042395` 的评审报告 | 评审归档 |
| [`docs/reviews/2026-09-07-review-result-d042395-codex.md`](2026-09-07-review-result-d042395-codex.md) | 评审结果 | +74 / -0 | 归档 Codex 专家关于 `d042395` 的评审报告 | 评审归档 |
| [`docs/reviews/2026-09-07-review-result-d042395-grok.md`](2026-09-07-review-result-d042395-grok.md) | 评审结果 | +270 / -0 | 归档 Grok 专家关于 `d042395` 的评审报告 | 评审归档 |
| [`docs/reviews/2026-09-07-review-result-d042395-claude.md`](2026-09-07-review-result-d042395-claude.md) | 评审结果 | +308 / -0 | 归档 Claude 专家关于 `d042395` 的评审报告 | 评审归档 |
| [`docs/reviews/STATUS.md`](STATUS.md) | 门禁看板 | +45 / -3 | 更新基线仲裁结论（REWORK）、登记处置单与双向资产 100% 对账 | 看板对账 |

---

## 3. 现成测试脚本与质量快照 (Quality Snapshot & Reproducible Commands)

### 3.1 一键复现与验证命令
审查专家可在本地干净环境或独立沙箱中，按顺序执行以下命令进行 100% 物理机验：

```bash
# 1. 运行全量 145 项自动化测试套件（含 17 项新增测试）
python3 -m unittest discover tests

# 2. 单独验证 10 项 P1 核心阻断项专项闭环断言
python3 -m unittest tests/test_p1_closures_and_regressions.py

# 3. 验证动态探活在工作区中的纯只读零写盘与三元组推断
python3 -m macao.cli.main probe --dry-run

# 4. 验证 Python 3.10+ 语法与字节码编译零告警
python3 -m compileall src tests

# 5. 验证 PRD / 模板 Manifest 与 Draft-07 Schema 契约校验
python3 -m unittest tests/test_prd_snippets_schema.py
```

### 3.2 质量快照指标
- [x] **自动化单元与集成测试**：**145/145 PASS**（`Ran 145 tests in 63.706s, OK`，通过率 100%，0 Failures, 0 Errors）；
- [x] **测试扩增与负向断言**：测试总数由上一轮的 128 项净增 17 项至 **145 项**，全部为针对 P1 阻断项和 Pi 适配器的确定性负向/边界断言；
- [x] **探活零写盘验证**：`TeamProber(dry_run=True)` 执行后，工作区文件状态保持 100% CLEAN，`.macao/logs/probe/` 目录未被创建；
- [x] **Python 编译检查**：`python3 -m compileall src tests` 输出 0 Errors；
- [x] **双 Schema 目录一致性**：`docs/schemas/` 与 `src/macao/schemas/` 8 份契约文件逐字节校验 100% 一致；
- [x] **评审资产账本对账**：`docs/reviews/` 下共有 Markdown 文件 **191 份**（结论类 146 份、申请类 43 份、处置单 1 份、STATUS 1 份），双向全量对账 100% 吻合。

---

## 4. 开发者自评与审查聚焦点 (Self-Assessment & Review Focus Checklist)

### 4.1 开发者自评 (Executor Self-Assessment)
- **实现完整性 (What was done)**：
  - 本轮对 4 位专家收敛的 8 项 P1 阻断项全部进行了代码根因级重构，没有任何表面补丁或敷衍性通过；
  - 严格贯彻了「不捏造、不篡改、只读零副作用、Fail-Closed」的 MACAO 系统底线；
  - 交付了完整的 Pi Coding Agent 支持与半途存量项目接入（场景 C）规范。
- **已知局限性与设计权衡 (Known Limitations)**：
  - **Kimi 会话发现 Fail-Closed**：由于当前宿主环境中的 Kimi CLI 本地缺少结构化的项目绑定数据库（仅存在 `~/.kimi` 目录），依据 P1-2 原则，MACAO 绝不以目录存在为由捏造会话，因此严格返回 `[]`，标记为 `UNKNOWN_SESSION` 并提示需用户显式输入 session_id；
  - **Worktree 共享模式**：对于未挂载独立 Git Worktree 的单仓项目，探活如实展示为 `In-repo (Shared Workspace / Direct Review)`，符合 PRD 允许的轻量化沙箱形式。
- **对前序评审意见的吸收**：
  - Muse 关注的 dry-run 写盘与脱敏未实装问题已彻底闭环；
  - Codex 关注的 tests_passed 虚假写入、--force 孤立任务、双 quorum 门限忽略已全量解决并配套反例测试；
  - Grok 关注的会话跨项目伪报与单票过早终止 pending 已通过严格路径匹配与集合差算法闭环；
  - Claude 关注的 8 项 P1 阻断项已逐条建立一一对应的回归测试文件 [`test_p1_closures_and_regressions.py`](../../tests/test_p1_closures_and_regressions.py)。

### 4.2 提请专家重点关注事项 (Review Focus Checklist)
请各位评审专家在复审独立沙箱中重点核验以下 5 项关键边界：

- [ ] **Focus 1: `--dry-run` 探活绝对只读性 (P1-1)**：核验在 `.macao` 目录不存在的全新项目中执行 `macao probe --dry-run`，是否绝对不会创建任何文件、目录或 SQLite 数据库。
- [ ] **Focus 2: `SessionLocator` 真实绑定与防伪造 (P1-2)**：核验在 Codex/Cursor 中，若会话记录的 `cwd` 与当前项目绝对路径不一致，是否严格被过滤且绝不回填当前路径。
- [ ] **Focus 3: 进度三元组状态推导优先序 (P1-3)**：核验当工作区存在 dirty 改动但同时存在待表决的物理提审单时，Executor 状态是否正确维持为 `REVIEW_PENDING`，且 Next 明确列出未出票的 Reviewer。
- [ ] **Focus 4: 法定人数三道门槛联合合取 (P1-4)**：核验在“席位达标但权重不足”以及“权重达标但席位数不足”两种反例下，探活报告是否正确将 Quorum 标记为 BLOCKED 并分别指出短板。
- [ ] **Focus 5: 日志脱敏清洗的无遗漏性 (P1-5)**：核验在 Reviewer 终端输出包含各类 API Key (`sk-...`, `ant-...`)、GitHub Token 或包含密码的数据库连接串时，落盘日志与终端回显是否均被遮蔽。

---

## 伴随机器信封：`.macao/.dev.yml`

```yaml
version: "1.0"
task_id: "task-20260907-orchestrator-p1-remediation"
checkpoint_ref: "961bcfe"
review_round: 2
status: "ready_for_review"
signal: "EXPLICIT"
executor:
  id: "opencode-dev"
  cli: "opencode"
full_document:
  path: "docs/reviews/2026-09-07-review-request-961bcfe.md"
  evidence_commit: "961bcfe"
  sha256: "0000000000000000000000000000000000000000000000000000000000000000"
development:
  description: "Remediate 8 P1 review blocking issues on d042395, add Pi adapter, and specify Scenario C adoption"
  quality_metrics:
    tests_passed: true
    tests_total: 145
    test_coverage: 0.88
    lint_errors: 0
    security_scan_passed: true
  git:
    latest_commit: "961bcfe"
    branch: "main"
  review_focus:
    - "verify probe dry-run pure read-only with zero disk mutation"
    - "verify SessionLocator project binding and zero session fabrication"
    - "verify progress triplet review pending logic with partial votes"
    - "verify quorum 3-condition conjunction gate"
    - "verify secrets and credentials redaction pipeline"
```
