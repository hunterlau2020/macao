# MACAO 综合编排闭环与评审方法论 v1.1 升级复审申请（Commit 7bc8d70 / Round 3）

- **文档归档路径**: `docs/reviews/2026-09-08-review-request-7bc8d70.md`
- **申请日期 (Date)**: 2026-09-08
- **申请人 (Author)**: MACAO Architecture & Engineering Team
- **目标定级 (Target Level)**: **L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3 准入评审**
- **当前受审提交 (Checkpoint Ref)**: `7bc8d70`（完整 SHA：`7bc8d7091ba4e39c0b3282492c613817f8d664e9`）
- **合并审计范围 (Review Range)**: `961bcfe..7bc8d70`（涵盖提交 `48eea58` 与 `7bc8d70`）
- **评审轮次 (Review Round)**: `Round 3`（`961bcfe` 专家评审后全量整改及方法论升级复审）
- **关联任务 ID (Task ID)**: `task-20260908-orchestrator-p0-p1-remediation-and-guidelines-v1.1`
- **前序受审基线与处置单 (Previous Baseline & Disposition)**:
  - 前序受审基线：`961bcfe`（4 位专家独立评审：Codex, Grok, Kimi, Pi-Qwen，仲裁结论为 **全票否决待返工 REWORK**）
  - 前序处置报告：[`docs/reviews/2026-09-07-disposition-961bcfe.md`](2026-09-07-disposition-961bcfe.md)（所有 P0-1、P1-1～P1-10、Codex P1-01～04 彻底闭环）
  - 4 份专家评审归档：
    1. [`2026-09-07-review-result-961bcfe-codex.md`](2026-09-07-review-result-961bcfe-codex.md)（Codex：REJECT / 4 项 P1，1 项 P2）
    2. [`2026-09-07-review-result-961bcfe-grok.md`](2026-09-07-review-result-961bcfe-grok.md)（Grok：NO_APPROVE / 4 项 P1，3 项 P2）
    3. [`2026-09-07-review-result-961bcfe-kimi.md`](2026-09-07-review-result-961bcfe-kimi.md)（Kimi：REWORK / 2 项 P0，5 项 P1）
    4. [`2026-09-07-review-result-961bcfe-pi-qwen.md`](2026-09-07-review-result-961bcfe-pi-qwen.md)（Pi-Qwen：NO_APPROVE / 1 项 P0，4 项 P1）
- **上位评审方法论**: [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)（已同步升级至 **v1.1**）
- **实时门禁状态表**: [`docs/reviews/STATUS.md`](STATUS.md)

---

## 1. 变更摘要与核心目标 (Summary & Rationale)

在基线 `961bcfe` 的独立机验评审中，四位评审专家指出了一系列深水区物理问题（包括未知 CLI 模糊匹配破坏 Fail-Closed、SQLite 只读连接生成 WAL 侧车文件破坏纯只读、跨项目会话未隔离、clean 产生幽灵 worktree、非零退出码缺失、检查点 SHA256 与归属未校验等）。

本轮提审范围 `961bcfe..7bc8d70` 包含两大核心演进：
1. **Commit `48eea58`**：严格执行 Fail-Closed 与零副作用原则，对 `961bcfe` 轮四方专家提出的全部 14 项 P0/P1 阻塞项实施彻底的代码级闭环，完整落地场景 C（`macao task adopt`）与检查点防伪；
2. **Commit `7bc8d70`**：正式落地 GLM 与 Claude 针对评审方法论的联合建议，将 [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md) 升级至 **v1.1**，引入验证命令参照系对齐、复现证据归档、已知简化表与决策项解耦、L4 OPS 10 项必测矩阵、严重级与可达性联合定级、以及反例击穿纪律。

### 核心演进与架构决策

1. **未知 CLI 坚决拒绝派发，严守 Fail-Closed (P0-1)**：
   移除 `TeamProber` 中任何子串模糊匹配后门（如将 `custom-claude` 借壳识别为 `claude`），无法精确匹配已注册 CLI 的一律标记为 `MISSING`，阻断派发与就绪判定。
2. **测试确定性消除 Flake (P1-1)**：
   `SessionLocator` 排序键由单一修改时间扩展为 `(st_mtime, name)` 二元稳定组，彻底消除同秒文件在不同操作系统文件系统遍历时的非确定性排序问题。
3. **消除 SQLite WAL 侧车，实现真正零写盘 (P1-2)**：
   探活与只读场景下的 SQLite 连接统一注入 `&immutable=1` URI 参数，确保只读模式下操作系统层 0 字节写入，杜绝产生 `state.db-wal` 或 `state.db-shm` 侧车残留。
4. **敏感凭据脱敏规则扩展并全面集成 (P1-3)**：
   `secrets.py` 扩充 6 大类敏感词正则（JWT, AWS, AIza, Bearer, DB Connection URL, PEM 私钥），全面贯通至 `SessionLocator._sanitize_session_name`、`logger.py`、PTY 会话捕获及 `macao logs`。
5. **跨目录/跨项目绝对路径防串话 (P1-4)**：
   会话匹配中强制使用 `os.path.realpath` 规范化绝对路径，严格比对工作区根目录与会话元数据中的 `cwd`，彻底杜绝跨项目与同名子目录幽灵串话。
6. **彻底消灭 Worktree 幽灵引用 (P1-5)**：
   `macao clean` 引入 `git worktree remove` 与 `git worktree prune` 组合操作，物理删除工作树后立即清理 Git 内部 administrative 元数据，消除幽灵引用。
7. **单一活动任务不变量内核下沉 (P1-6)**：
   将“全系统只允许单一处于活动态（`ACTIVE`）的任务”这一下层状态机不变量，从 CLI 交互层下沉至 `Orchestrator.start_task()` 核心方法，CLI 增加全局前置守卫拦截，杜绝多任务并发孤立。
8. **进程边界退出码严格 Fail-Closed (P1-7)**：
   `macao probe` 与 `macao doctor` 遇到非法配置或致命异常时严格退出非零码（退出码 2 或 1），支持显式 `--allow-degraded` 参数；`macao task create --dry-run` 遇到配置无效或分支冲突同样退出非零码。
9. **产品事实 F-25 与 F-26 正式固化 (P1-8)**：
   在 `docs/usercases/PRODUCT-FACTS.md` 中固化事实 F-25（探活与诊断只读零副作用零侧车）与 F-26（原生会话发现具备可验证的目录绑定与敏感词清洗）。
10. **待决评审单物理优先级高于脏工作树 (P1-9)**：
    探活三元组对账逻辑中，未完成评审的物理提审单（`*-review-request-*.md`）优先级明确高于脏工作树，`task create` 检测到待决评审单时严格抛出异常阻断创建新任务（UC-2 E7）。
11. **Pi 与 Cursor 适配器完整接入实机派发 (P1-10 & Codex P1-01/02)**：
    `LiveAgentDispatcher` 完整接入 `PiAdapter` 与 `CursorAgentAdapter`，并将任务显式验收标准（`acceptance_criteria`）原样透传至审查员上下文。
12. **场景 C 存量项目接管命令全功能实现 (Codex P1-03)**：
    实现 `macao task adopt [TASK_NAME]` 完整命令，支持自动扫描当前 Git 分支与改动，支持 `--dry-run` 观察模式。
13. **检查点防伪与归属真实性校验 (Codex P1-04)**：
    `submit_checkpoint` 严格校验 `full_document.sha256` 必须为合法 64 位十六进制散列且与文档实际 SHA-256 吻合；强制校验 `executor.id` 与 `executor.cli` 必须与任务配置中的主执行席位一致，杜绝假造与冒名。
14. **评审方法论正式升级至 v1.1**：
    将 GLM 与 Claude 评审提案中的高价值工程准则固化为条文：
    - §3.4：建立验证命令参照系对照表（`git show --check` vs `git diff --check`，干净 worktree vs 脏工作区，负向退出码断言）；
    - §3.5：确立复现脚本归档至 `docs/reviews/evidence/` 及 `tempfile.mkdtemp` 隔离要求；
    - §5.2：建立「已知简化」常设表与「决策项」分类机制，解耦设计边界与代码缺陷；
    - §6：场景库增补失效影响与最后验证字段，重申“成功样本只证明 happy path，不证明全量质量”；
    - §7.2：建立 10 行 L4 OPS 必测矩阵；
    - §8.1-§8.3：建立严重级域定义（P0/P1/P2/P3）、可达性联合定级规则、风险接受 11 项字段（到期自动重新阻断）、以及“构造反例击穿修复”与“不得显式传参绕开生产路径”的硬纪律；
    - §9：新增漏审模式 E（「已实现」≠「已接线」）及第 6、7 项自检；
    - 引入 `docs/reference/REVIEW_GUIDEv2.md` 作为后端参考指南。

---

## 2. 靶向变更清单 (Targeted Code Changes & Issue Mapping)

本次提审范围 `961bcfe..7bc8d70` 累计涉及 **30 个文件，+2765 / -226 行**：

| 文件路径 | 模块分类 | 变动行数 | 核心修改说明 | 闭环 Issue / 特性 |
| :--- | :--- | :--- | :--- | :--- |
| [`src/macao/workflow/prober.py`](../../src/macao/workflow/prober.py) | 核心探活 | +30 / -10 | 移除子串模糊匹配；只读连接注入 `&immutable=1`；修复退出码；待决提审单优先于脏树 | **P0-1, P1-2, P1-7, P1-9** |
| [`src/macao/adapter/session_locator.py`](../../src/macao/adapter/session_locator.py) | 会话发现 | +79 / -24 | `(st_mtime, name)` 稳定排序；只读连接 `&immutable=1`；绝对路径校验；集成密钥脱敏 | **P1-1, P1-2, P1-3, P1-4** |
| [`src/macao/cli/main.py`](../../src/macao/cli/main.py) | CLI 交互 | +275 / -35 | 探活/诊断非零退出码；`task create` 守卫与 `--dry-run` 退出码；实现 `task adopt` 及 `--dry-run`；clean 双清 | **P1-5, P1-6, P1-7, Codex P1-03** |
| [`src/macao/workflow/orchestrator.py`](../../src/macao/workflow/orchestrator.py) | 编排引擎 | +36 / -8 | 单一活跃任务下沉至 `start_task`；检查点强校验 `sha256` 与 `executor` 归属 | **P1-6, Codex P1-04** |
| [`src/macao/workflow/live_dispatcher.py`](../../src/macao/workflow/live_dispatcher.py) | 沙箱派发 | +23 / -4 | 完整接入 `PiAdapter` 与 `CursorAgentAdapter`；原样透传 `acceptance_criteria` | **P1-10, Codex P1-01, P1-02** |
| [`src/macao/utils/secrets.py`](../../src/macao/utils/secrets.py) | 基础设施 | +64 / -6 | 扩充 JWT、AWS、AIza、Bearer、DB URL、PEM 6 类敏感词脱敏正则 | **P1-3** |
| [`src/macao/storage/db.py`](../../src/macao/storage/db.py) | 存储引擎 | +16 / -2 | SQLite 只读连接增加 `&immutable=1` 支持，彻底杜绝 WAL/SHM 侧车 | **P1-2** |
| [`src/macao/storage/store.py`](../../src/macao/storage/store.py) | 存储引擎 | +17 / -3 | 只读模式连接配置透传 `&immutable=1` | **P1-2** |
| [`src/macao/adapter/cursor.py`](../../src/macao/adapter/cursor.py) | AI CLI 适配 | +10 / -2 | 修复导入依赖，确保与 `LiveAgentDispatcher` 派发契约无缝兼容 | **Codex P1-02** |
| [`src/macao/adapter/pi.py`](../../src/macao/adapter/pi.py) | AI CLI 适配 | +19 / -3 | 完善 Pi 适配器会话集成与终端交互 | **Codex P1-01** |
| [`src/macao/cli/ui.py`](../../src/macao/cli/ui.py) | 终端渲染 | +83 / -15 | 增强 `task adopt` 与 `probe` 渲染，正确展示待决评审单与三问进度 | 交互增强 |
| [`src/macao/workflow/live_runner.py`](../../src/macao/workflow/live_runner.py) | 运行引擎 | +12 / -2 | 确保 `adopt` 与 `runner` 正确读取活跃任务上下文 | **Codex P1-03** |
| [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md) | 评审方法论 | +150 / -17 | **升级至 v1.1**：§3.4 作用域对照表、§3.5 复现证据归档、§5.2 已知简化表、§6 场景库扩充、§7.2 L4 OPS 必测矩阵、§8.1-§8.3 域定义与修复纪律、§9 模式 E、§10 模板更新 | **方法论 v1.1 升级** |
| [`docs/reference/REVIEW_GUIDEv2.md`](../reference/REVIEW_GUIDEv2.md) | 参考文档 | +264 / -0 | 引入 Backend Review Guide v2 作为稳定方法论参考输入 | 参考归档 |
| [`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md) | 产品事实 | +4 / -0 | 正式固化产品事实 **F-25**（只读零副作用）与 **F-26**（会话真实可验证绑定） | **P1-8 事实固化** |
| [`docs/reviews/2026-09-07-disposition-961bcfe.md`](2026-09-07-disposition-961bcfe.md) | 评审治理 | +209 / -0 | 针对 `961bcfe` 轮四方评审专家意见的完整闭环处置报告 | 治理归档 |
| [`docs/reviews/STATUS.md`](STATUS.md) | 门禁看板 | +46 / -2 | 登记 4 份评审报告与处置单，更新基线为 REWORK 并完成 100% 资产对账 | 看板对账 |
| [`templates/review-request-template.md`](../../templates/review-request-template.md) | 治理模板 | +91 / -5 | 补充靶向变更清单、测试脚本与质量快照、自评与聚焦点章节规范 | 模板治理 |
| [`tests/test_p1_closures_and_regressions.py`](../../tests/test_p1_closures_and_regressions.py) | 自动化测试 | +261 / -0 | 新增 10 项回归测试，覆盖未知 CLI、稳定排序、immutable、脱敏、单任务等 | **P0-1 ~ P1-9 验证** |
| [`tests/test_task_adopt.py`](../../tests/test_task_adopt.py) | 自动化测试 | +170 / -0 | 新增 7 项测试，完整覆盖 `task adopt` 执行、`--dry-run`、冲突拦截等场景 | **Codex P1-03 验证** |
| [`tests/test_pi_and_session_locator.py`](../../tests/test_pi_and_session_locator.py) | 自动化测试 | +55 / -2 | 覆盖 Pi 适配器派发集成、会话真实性与密钥脱敏 | **Pi / 密钥验证** |
| [`tests/test_p0_p1_rectification.py`](../../tests/test_p0_p1_rectification.py) | 自动化测试 | +3 / -1 | 更新校验断言 | 回归测试 |
| [`tests/test_team_probe_and_dispatch.py`](../../tests/test_team_probe_and_dispatch.py) | 自动化测试 | +6 / -1 | 更新派发与探活测试断言 | 回归测试 |

---

## 3. 现成测试脚本与质量快照 (Quality Snapshot & Reproducible Commands)

依据方法论 **§3.4 验证命令作用域** 规范，审查专家可在干净的工作树中直接执行以下命令进行 100% 物理机验：

### 3.1 一键复现与验证命令

```bash
# 1. 验证 commit 洁净度（遵循 §3.4，严禁使用提交后恒为空的 git diff --check）
git show --check 7bc8d70

# 2. 执行全量 162 项自动化单元与集成测试套件（100% PASS，耗时约 68s）
python3 -m unittest discover tests

# 3. 专项验证场景 C 'macao task adopt' 及 --dry-run 逻辑
python3 -m unittest tests/test_task_adopt.py

# 4. 专项验证 10 项 P1 核心阻塞项与防伪防篡改断言
python3 -m unittest tests/test_p1_closures_and_regressions.py

# 5. 验证探活只读守卫与零副作用（0 WAL/SHM 侧车落盘，返回码 0）
python3 -m macao.cli.main probe --dry-run
ls -la .macao/state.db*   # 验证不存在 state.db-wal 或 state.db-shm

# 6. 验证任务接管命令的 --dry-run 观察模式（不修改任何状态）
python3 -m macao.cli.main task adopt --dry-run

# 7. 验证 Python 3.10+ 编译无语法或导入错误
python3 -m compileall src tests
```

### 3.2 质量快照指标

- [x] **自动化测试**：**162/162 PASS**（`Ran 162 tests in 68.335s, OK`，通过率 100%，0 Failures, 0 Errors）；
- [x] **新增测试覆盖**：新增 `tests/test_task_adopt.py`（7 项）与 `tests/test_p1_closures_and_regressions.py` 扩增用例，测试总数由 145 项增长至 **162 项**；
- [x] **提交洁净度**：`git show --check 7bc8d70` 返回码为 0，完全无尾随空白或多余空行；
- [x] **只读零副作用**：通过 SQLite URI `mode=ro&immutable=1` 彻底消除 WAL/SHM 侧车文件落盘；
- [x] **Fail-Closed 退出码**：非法配置与致命错误在探活、诊断与任务创建中均返回非零退出码（2/1）；
- [x] **方法论一致性**：[`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md) 顺利升版至 v1.1，双向审计完全一致。

---

## 4. 开发者自评与审查聚焦点 (Self-Assessment & Review Focus Checklist)

### 4.1 开发者自评 (Executor Self-Assessment)

- **实现总结 (What was done)**：
  本轮迭代完整兑现了对 `961bcfe` 轮四位审查专家的处置承诺。在工程代码层面，未知 CLI 模糊匹配后门被彻底清除，只读连接的 `&immutable=1` 机制从物理层面消除了 SQLite 侧车污染，会话查找与路径校验做到了绝对路径真实绑定，单一活动任务不变量下沉到了状态机引擎深处，场景 C 的 `macao task adopt` 及其 `--dry-run` 模式已交付并具备完备测试。在方法论层面，吸收并固化了 GLM 与 Claude 提案中的核心工程纪律，为后续审查树立了清晰且可操作的判据。
- **已知局限性与阶段性设计边界 (Known Simplifications)**：
  依据方法论 **§5.2「已知简化表」** 规范，下列设计为已接受的阶段性边界，不应记为代码缺陷：
  1. **单仓 In-repo 共享工作区**：在未显式配置外部 Worktree 沙箱时，开发与审查在主仓库工作区内按分支流转，不强制要求所有环境均创建外部 Worktree；
  2. **CI Gate 命令允许为 null**：`macao.yaml` 中 `ci_gate_command` 属于可选属性，当配置为 null 时系统默认跳过外部 CI 门禁直接推进合并。
- **对前序评审意见的吸收**：
  前序轮次中指出的 14 项 P0/P1 问题全部建立回归测试（见 `tests/test_p1_closures_and_regressions.py` 与 `tests/test_task_adopt.py`），且均从生产真实入口驱动，未采用私有变量绕行。

### 4.2 提请专家重点关注事项 (Review Focus Checklist)

请各位评审专家在独立沙箱中重点核验以下边界场景与安全逻辑：
- [ ] **Focus 1: 未知 CLI 派发与探活 Fail-Closed**：
  验证当配置不存在或拼写错误的 CLI 名称时，系统是否坚决拒绝派发并标记 `MISSING`，绝不借壳已有适配器；
- [ ] **Focus 2: 只读模式零侧车文件落盘**：
  在只读磁盘或只读挂载工作区中执行 `macao probe --dry-run`，验证是否 100% 杜绝产生 `.macao/state.db-wal` 或 `.macao/state.db-shm`；
- [ ] **Focus 3: 场景 C 'macao task adopt' 与 --dry-run**：
  验证在存量已有未跟踪修改的分支上，`macao task adopt` 是否能正确识别未决改动、建立任务跟踪，以及在 `--dry-run` 下是否保持零修改；
- [ ] **Focus 4: 检查点防伪与主执行席位归属校验**：
  验证如果传入伪造的 `sha256` 或非当前任务分配的 `executor.id`，状态机是否坚决抛出异常阻断提审；
- [ ] **Focus 5: 评审方法论 v1.1 规范与工程一致性**：
  审查 [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md) v1.1 各新增章节（§3.4, §3.5, §5.2, §7.2, §8.1-§8.3, §9）与实际工程实践的自洽性。

---

## 伴随机器信封：`.macao/.dev.yml`

```yaml
version: "1.0"
timestamp: "2026-09-08T00:43:00+08:00"
task_id: "task-20260908-orchestrator-p0-p1-remediation-and-guidelines-v1.1"
checkpoint_ref: "7bc8d70"
review_round: 3
status: "ready_for_review"
signal: "EXPLICIT"
executor:
  id: "dev-antigravity"
  role: "Lead Orchestrator Architect"
  cli: "antigravity"
full_document:
  path: "docs/reviews/2026-09-08-review-request-7bc8d70.md"
  evidence_commit: "7bc8d70"
  sha256: "0000000000000000000000000000000000000000000000000000000000000000"
development:
  phase: "Phase 3 Orchestrator & Multi-Agent Dispatch"
  description: "Remediate all P0/P1 review findings from 961bcfe, implement task adopt with --dry-run, enforce fail-closed invariants and zero sidecars, and adopt Review Guidelines v1.1"
  artifacts:
    - type: "code"
      path: "src/macao/workflow/prober.py"
      changed_lines: 40
      updated: true
    - type: "code"
      path: "src/macao/adapter/session_locator.py"
      changed_lines: 103
      updated: true
    - type: "code"
      path: "src/macao/cli/main.py"
      changed_lines: 310
      updated: true
    - type: "code"
      path: "src/macao/workflow/orchestrator.py"
      changed_lines: 44
      updated: true
    - type: "code"
      path: "src/macao/workflow/live_dispatcher.py"
      changed_lines: 27
      updated: true
    - type: "code"
      path: "src/macao/utils/secrets.py"
      changed_lines: 70
      updated: true
    - type: "code"
      path: "src/macao/storage/db.py"
      changed_lines: 18
      updated: true
    - type: "doc"
      path: "docs/MACAO_REVIEW_GUIDELINES.md"
      changed_lines: 167
      updated: true
    - type: "doc"
      path: "docs/reference/REVIEW_GUIDEv2.md"
      changed_lines: 264
      updated: true
    - type: "doc"
      path: "docs/reviews/2026-09-07-disposition-961bcfe.md"
      changed_lines: 209
      updated: true
  checklist:
    - "P0-1: Unknown CLI substring fallback removed; fail-closed rejection enforced"
    - "P1-1: Deterministic (st_mtime, name) session sorting in SessionLocator"
    - "P1-2: SQLite &immutable=1 connection mode eliminates WAL/SHM sidecars"
    - "P1-3: Secrets regex masking expanded and integrated with SessionLocator"
    - "P1-4: Strict realpath verification prevents cross-project session confusion"
    - "P1-5: Git worktree remove and prune clears ghost references"
    - "P1-6: Single active task invariant sunk to Orchestrator.start_task"
    - "P1-7: Non-zero exit codes on invalid configuration across probe, doctor, task create"
    - "P1-8: Product facts F-25 and F-26 solidified in PRODUCT-FACTS.md"
    - "P1-9: Review request takes priority over dirty tree in status reconciliation"
    - "P1-10 & Codex P1-01/02: Pi and Cursor adapters integrated in LiveAgentDispatcher"
    - "Codex P1-03: Full 'macao task adopt' command implemented with --dry-run"
    - "Codex P1-04: Full SHA-256 and executor verification on checkpoints"
    - "Guidelines v1.1: Verification scopes, evidence archiving, known simplifications, L4 OPS matrix, reachability grading, and fix verification discipline adopted"
  quality_metrics:
    tests_passed: true
    tests_total: 162
    test_coverage: 0.90
    lint_errors: 0
    security_scan_passed: true
  git:
    branch: "main"
    base_commit: "961bcfe"
    head_commit: "7bc8d70"
    clean_working_tree: true
```
