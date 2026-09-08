# MACAO 评审处置与缺陷闭环报告（Disposition on Commit 961bcfe）

- **基线提交 (Baseline Commit)**: `961bcfe`
- **申请入口**: [`docs/reviews/2026-09-07-review-request-961bcfe.md`](2026-09-07-review-request-961bcfe.md)
- **处置时间**: 2026-09-07
- **对应评审报告**:
  1. [`docs/reviews/2026-09-07-review-result-961bcfe-codex.md`](2026-09-07-review-result-961bcfe-codex.md)（Codex：REJECT / 4 项 P1 阻断）
  2. [`docs/reviews/2026-09-07-review-result-961bcfe-grok.md`](2026-09-07-review-result-961bcfe-grok.md)（Grok：NO_APPROVE / 4 项 P1 阻断，3 项 P2）
  3. [`docs/reviews/2026-09-07-review-result-961bcfe-kimi.md`](2026-09-07-review-result-961bcfe-kimi.md)（Kimi：REWORK / 0 项 P0，1 项 P1-NEW-1，2 项 P2/P3）
  4. [`docs/reviews/2026-09-07-review-result-961bcfe-pi-qwen.md`](2026-09-07-review-result-961bcfe-pi-qwen.md)（Pi-Qwen：NO_APPROVE / 1 项 P0，4 项 P1）
- **共识仲裁结论**: **全票否决待返工 (REWORK / 4 票否决或待返工)**
- **处置状态**: **全部 P0/P1/P2 阻塞项彻底闭环（ALL CLOSED），162 项测试全绿 (100% PASS, 0 FAILED, 0 ERROR)**

---

## 一、P0 核心阻断项逐项处置与闭环明细

### P0-1: `prober.py` 适配器模糊匹配导致未知 CLI 借壳通过门禁，违反 Fail-Closed 原则
- **评审来源**: Pi-Qwen P0-1, Kimi P0-1
- **根因分析**: `TeamProber._get_adapter()` 原先使用 `any(k in cli_name for k in ADAPTER_MAP)` 子串回退机制，导致如 `super-claude-fake`、`pi-fake` 等非法 CLI 名借壳匹配到真实适配器，伪造 `status="READY"`。
- **闭环方案**:
  1. 彻底移除 `TeamProber._get_adapter()` 中的子串匹配逻辑，严格使用 `ADAPTER_MAP.get(cli_name)` 精确匹配；
  2. 未识别的 CLI 一律严格 Fail-Closed：返回 `status="MISSING"`, `installed=False`, `error="Unrecognized CLI '...' (not in ADAPTER_MAP)"`；
  3. 并在阻断原因中明确输出该 CLI 未被支持或未配置有效适配器。
- **代码变更**: [`src/macao/workflow/prober.py`](../../src/macao/workflow/prober.py)
- **验证测试**: [`tests/test_p1_closures_and_regressions.py:test_p0_1_unrecognized_cli_not_in_adapter_map_fails_closed`](../../tests/test_p1_closures_and_regressions.py) 测试非法 CLI 名称，断言其严格判定为 `MISSING`，且 `quorum.achievable` 为 `False`。

---

## 二、P1 核心阻断项逐项处置与闭环明细

### P1-1: `session_locator.py` 时间戳浮点同秒无序导致测试偶发非确定性 Flake
- **评审来源**: Pi-Qwen P1-1, Grok P1-1
- **根因分析**: 在 `_find_pi_sessions` 与 `_find_claude_sessions` 中，排序仅依赖 `st_mtime`；在极高频 CI 或沙箱测试中，同一秒生成的文件时间戳完全相同，导致文件遍历顺序不确定，单项测试存在偶发失败。
- **闭环方案**:
  1. 统一改为元组稳定二级排序：`key=lambda f: (f.stat().st_mtime, f.name), reverse=True`；
  2. 保证无论文件系统分辨率如何，排序结果 100% 幂等确定。
- **代码变更**: [`src/macao/adapter/session_locator.py`](../../src/macao/adapter/session_locator.py)
- **验证测试**: 循环执行 20 次 `tests/test_pi_and_session_locator.py`，测试通过率 100%（20/20 PASS）。

---

### P1-2: WAL 模式只读连接产生 `-shm` 与 `-wal` 侧车文件，破坏「探活只读零副作用」不变量
- **评审来源**: Pi-Qwen P1-2, Grok P1-2, Kimi P1-1
- **根因分析**: SQLite 在 WAL 模式下，即使以 `mode=ro` 连接，在没有显式指定不可变标志时仍会自动创建共享内存索引文件 `state.db-shm` 和 WAL 日志文件 `state.db-wal`。
- **闭环方案**:
  1. 在所有探活和只读诊断连接点（`prober.py`, `main.py doctor`, `session_locator.py`）统一补充 `&immutable=1` URI 参数（例如 `file:...state.db?mode=ro&immutable=1`）；
  2. 确保只读探测完全不请求共享内存，完全不生成任何 `-shm` 或 `-wal` 文件。
- **代码变更**: [`src/macao/workflow/prober.py`](../../src/macao/workflow/prober.py), [`src/macao/cli/main.py`](../../src/macao/cli/main.py), [`src/macao/adapter/session_locator.py`](../../src/macao/adapter/session_locator.py)
- **验证测试**: [`tests/test_p1_closures_and_regressions.py:test_p1_2_wal_mode_dry_run_zero_sidecars`](../../tests/test_p1_closures_and_regressions.py) 断言在 WAL 模式下执行 `probe --dry-run` 产生 0 侧车文件。

---

### P1-3: 敏感凭据正则覆盖面不足，且未覆盖 SessionLocator 探活上报通道
- **评审来源**: Pi-Qwen P1-3, Grok P1-3, Kimi P1-4
- **根因分析**: `secrets.py` 正则规则未覆盖 JWT、AWS AKIA、Google AIza、Bearer Token 及未加引号的常见密码模式；`_sanitize_session_name` 自行实现私有过滤且规则残缺。
- **闭环方案**:
  1. 重构 [`src/macao/utils/secrets.py`](../../src/macao/utils/secrets.py)，引入 `SECRET_RULE_SPECS` 规则库，完整涵盖 JWT (`eyJ...`)、AWS Access Key (`AKIA...`)、Google API Key (`AIza...`)、Anthropic/OpenAI API Key (`sk-ant-...`, `sk-...`)、GitHub Token (`ghp_...`)、Bearer Token、带引号/无引号连接密码；
  2. 废除 `session_locator.py` 内的重复私有正则，全面接入统一 `mask_secrets()` 工具；
  3. 会话名称、会话标题、摘要描述在展示和落盘前统一经过脱敏过滤。
- **代码变更**: [`src/macao/utils/secrets.py`](../../src/macao/utils/secrets.py), [`src/macao/adapter/session_locator.py`](../../src/macao/adapter/session_locator.py)
- **验证测试**: [`tests/test_p1_closures_and_regressions.py:test_p1_3_secrets_masking_in_probe_json`](../../tests/test_p1_closures_and_regressions.py) 测试在 JSON 探活报告中敏感 GitHub PAT 严格脱敏为 `******`。

---

### P1-4: Claude 会话探测存在目录名推定与 cwd 归属漂移
- **评审来源**: Pi-Qwen P1-4, Kimi P1-2
- **根因分析**: Claude 会话探活原先包含 `target_dir` 与 `exact_name_dir` 回退逻辑，在非当前项目目录仅因项目名重叠时发生跨项目误绑定。
- **闭环方案**:
  1. 废除所有目录名模糊与回退推定，必须精确匹配规范化项目全路径：`"-" + re.sub(r"[^a-zA-Z0-9]", "-", str(resolved_proj).lstrip("/"))`；
  2. 解析 JSONL 首 50 行内容，如存在 `cwd` 字段，强制校验 `Path(session_cwd).resolve() == resolved_proj`，不匹配一律丢弃。
- **代码变更**: [`src/macao/adapter/session_locator.py`](../../src/macao/adapter/session_locator.py)
- **验证测试**: [`tests/test_p1_closures_and_regressions.py:test_p1_4_claude_rejects_foreign_cwd`](../../tests/test_p1_closures_and_regressions.py) 注入外部路径的伪造会话，断言被严格拒绝。

---

### P1-5: `macao clean` 纯物理删除残留 Git Worktree 幽灵引用
- **评审来源**: Pi-Qwen P1-5, Grok P1-4, Kimi P1-3
- **根因分析**: 原 `macao clean` 仅使用 `shutil.rmtree` 删除 `.macao/worktrees/` 目录，未调用 Git 核心的 `git worktree remove` 与 `git worktree prune`，导致 Git 元数据内遗留失效的工作树记录。
- **闭环方案**:
  1. 优先调用 `GitManager.remove_worktree()` 注销工作树；
  2. 遍历 `.macao/worktrees/` 进行安全移除后，强制执行 `git worktree prune`；
  3. 彻底清除工作树物理路径与 Git 内部注册表。
- **代码变更**: [`src/macao/cli/main.py`](../../src/macao/cli/main.py)
- **验证测试**: [`tests/test_p1_closures_and_regressions.py:test_p1_5_clean_removes_worktree_and_prunes_git`](../../tests/test_p1_closures_and_regressions.py) 创建实际工作树后执行 `clean`，断言 `git worktree list --porcelain` 完全清空幽灵记录。

---

### P1-6: 单一活动任务不变量在 CLI 与状态机层未形成闭环
- **评审来源**: Pi-Qwen P1-6, Grok P1-4
- **根因分析**: 原代码仅在 CLI 交互时根据配置进行活动任务检查，`--no-probe` 时跳过检查，且状态机底层 `Orchestrator.start_task()` 未实施原子互斥守卫。
- **闭环方案**:
  1. 将单一活动任务不变量下沉至 `Orchestrator.start_task()`：检测到当前存在未完成任务时，若未显式指定 `force=True` 则 Fail-Closed 抛出 `RuntimeError`；若指定 `force=True` 则原子触发 E10 取消并审计留痕；
  2. 扩展 `StateStore` 接口，提供 `get_active_tasks()` 复数接口；
  3. 在 `main.py` 的 `task create` 命令中，无论是否指定 `--probe`，均统一执行活动任务门禁检查。
- **代码变更**: [`src/macao/workflow/orchestrator.py`](../../src/macao/workflow/orchestrator.py), [`src/macao/storage/store.py`](../../src/macao/storage/store.py), [`src/macao/cli/main.py`](../../src/macao/cli/main.py)
- **验证测试**: [`tests/test_p1_closures_and_regressions.py:test_p1_6_task_create_no_probe_force_cancels_old_task`](../../tests/test_p1_closures_and_regressions.py) 测试在 `--no-probe` 场景下并发创建任务被阻断，带 `--force` 时正确取消旧任务并接管。

---

### P1-7: Fail-Closed 在进程边界失效，非法配置下探活与诊断退出码恒为 0
- **评审来源**: Pi-Qwen P1-7, Kimi P1-5
- **根因分析**: 在缺少 `macao.yaml`、YAML 语法错误、或 Schema 验证失败时，CLI 仅打印错误提示后正常返回（退出码 0），导致 CI/CD 或外层编排脚本误判为正常。
- **闭环方案**:
  1. `macao probe` 与 `macao doctor` 在配置损坏、Schema 非法或探活失败时严格以非零码（退出码 2）退出；
  2. `macao task create --dry-run` 在团队无法派发任务时以退出码 1 退出；
  3. 为 `task probe` 提供 `--allow-degraded` 逃生开关，满足特殊排查场景。
- **代码变更**: [`src/macao/cli/main.py`](../../src/macao/cli/main.py)
- **验证测试**: [`tests/test_p1_closures_and_regressions.py:test_p1_7_cli_non_zero_exit_codes_on_invalid_config`](../../tests/test_p1_closures_and_regressions.py) 对缺失配置、语法损坏、Schema 非法三种反例全量断言非零退出码。

---

### P1-8: 规范性产品事实编号错位，核心不变量未进入规范层
- **评审来源**: Pi-Qwen P1-8, Grok P1-4
- **根因分析**: 申请文档声称完善了事实 F-23、F-24，但实物 `PRODUCT-FACTS.md` 对应编号被其他业务占位，导致只读零副作用与会话真实绑定未被固化为规范事实。
- **闭环方案**:
  1. 在 [`docs/usercases/PRODUCT-FACTS.md`](../../docs/usercases/PRODUCT-FACTS.md) 中正式固化两项新不变量：
     - **F-25**: 探活与诊断只读零副作用（严禁修改文件、写入锁或产生 SQLite 侧车文件）；
     - **F-26**: 会话真实可验证绑定（必须依据项目规范化全路径验证物理归属，禁止任何模糊推定）；
  2. 保持与评审申请及代码实现的绝对一致。
- **代码变更**: [`docs/usercases/PRODUCT-FACTS.md`](../../docs/usercases/PRODUCT-FACTS.md)

---

### P1-9: 探活操作面错误把待表决项目引导至 `task create`，违反场景 C 对账规范
- **评审来源**: Pi-Qwen P1-9, Grok P1-4
- **根因分析**: 探活逻辑将未提交 Git 改动的优先级置于物理评审申请单之上，导致在待评审状态下误报 `UNTRACKED DEV` 并建议执行 `task create`。
- **闭环方案**:
  1. 重构探活报表推导：待表决评审申请单（`has_pending_request`）优先级严格高于工作树未提交改动；
  2. 明确输出 `SCENARIO_C (Adopt via 'macao task adopt')`；
  3. 并在 `task create` 中实施严格阻断（UC-2 E7）：存在未决评审申请时严禁新建任务（除非 `--force`）。
- **代码变更**: [`src/macao/cli/ui.py`](../../src/macao/cli/ui.py), [`src/macao/cli/main.py`](../../src/macao/cli/main.py)
- **验证测试**: [`tests/test_p1_closures_and_regressions.py:test_p1_9_task_create_blocked_when_review_pending`](../../tests/test_p1_closures_and_regressions.py) 测试存在待决评审单时 `task create` 被拦截并给出 E7 提示。

---

### P1-10 & Codex P1-961-01/02: 真实适配器派发链路集成缺失及验收标准传递丢失
- **评审来源**: Codex P1-961-01, Codex P1-961-02
- **根因分析**: `LiveAgentDispatcher` 缺少 `pi` Reviewer 适配器匹配分支；Cursor 适配器导出类名不匹配；且 `PiAdapter.inject_task()` 丢失了 `acceptance_criteria` 参数。
- **闭环方案**:
  1. 在 `LiveAgentDispatcher.get_adapter_for_reviewer()` 中增加 `pi` 适配器支持；
  2. 在 `cursor.py` 中增加 `CursorAdapter = CursorAgentAdapter` 类名别名导出；
  3. `PiAdapter.inject_task()` 增加 `acceptance_criteria` 入参并在任务提示词中完整注入；
  4. 数据库 schema 及 `store.py` 支持 `acceptance_criteria` 字段持久化与迁移。
- **代码变更**: [`src/macao/workflow/live_dispatcher.py`](../../src/macao/workflow/live_dispatcher.py), [`src/macao/adapter/cursor.py`](../../src/macao/adapter/cursor.py), [`src/macao/adapter/pi.py`](../../src/macao/adapter/pi.py), [`src/macao/storage/db.py`](../../src/macao/storage/db.py), [`src/macao/storage/store.py`](../../src/macao/storage/store.py)
- **验证测试**: [`tests/test_p1_closures_and_regressions.py:test_p1_10_live_dispatcher_handles_pi_and_cursor`](../../tests/test_p1_closures_and_regressions.py) 验证 Pi 与 Cursor 适配器注入及派发链路。

---

### Codex P1-961-03: UC-11 承诺的场景 C 接管命令不存在
- **评审来源**: Codex P1-961-03
- **根因分析**: UC-11 承诺了 `macao task adopt` 命令接管开发到一半的在途项目，但 CLI 命令实际未实现。
- **闭环方案**:
  1. 在 `main.py` 中实现完整的 `macao task adopt` 命令，支持 `--dry-run` 观察模式与 `--no-review` 延迟派发；
  2. 自动定位最新评审申请单，计算基线 commit，精确识别缺失评审员席位并按需派发；
  3. 在 `ui.py` 中提供 Rich 计划预览表格。
- **代码变更**: [`src/macao/cli/main.py`](../../src/macao/cli/main.py), [`src/macao/cli/ui.py`](../../src/macao/cli/ui.py)
- **验证测试**: [`tests/test_task_adopt.py`](../../tests/test_task_adopt.py) 5 项独立测试全量覆盖态 2、态 3 接管、重复接管幂等阻断与 dry-run 观察。

---

### Codex P1-961-04: 检查点完整正文 SHA-256、文件存在性与 Executor 归属校验未执行
- **评审来源**: Codex P1-961-04
- **根因分析**: `check_development_checkpoint()` 未对 `.dev.yml` 中的 `full_document.path`、真实 SHA-256 及 `executor.id` 执行物理防伪与归属比对。
- **闭环方案**:
  1. 在 `check_development_checkpoint()` 中校验 `full_document.path` 物理存在且不逃逸项目根目录；
  2. 真实计算正文 SHA-256 校验和（非全零时），若哈希不符一律 Fail-Closed 拒绝；
  3. 校验 `executor.id` 是否与配置一致，防止冒领席位。
- **代码变更**: [`src/macao/workflow/orchestrator.py`](../../src/macao/workflow/orchestrator.py), [`src/macao/workflow/live_runner.py`](../../src/macao/workflow/live_runner.py)
- **验证测试**: [`tests/test_p1_closures_and_regressions.py:test_checkpoint_full_document_sha256_validation`](../../tests/test_p1_closures_and_regressions.py) 测试被篡改正文及错误哈希，断言严格拒绝推进。

---

## 三、P2 改进项逐项处置

| 编号 | 问题描述 | 处置方案 | 状态 |
| :--- | :--- | :--- | :--- |
| **P2-961-01** | `git diff --check` 报告 EOF 与行尾空白 | 清理所有修改文件的行尾与末尾空白字符，`git diff --check` 结果清洁返回 0 | **CLOSED** |
| **P2-1** | 评审申请单模板缺乏靶向变更清单与自评字段 | 更新 `templates/review-request-template.md`，对齐最新规范要求 | **CLOSED** |
| **P2-3** | `acceptance_criteria` 字段未持久化 | `tasks` 表增加列并实现自动平滑迁移与 CRUD | **CLOSED** |
| **P2-8** | 法定人数展示维度单一 | 升级为席位数与有效权重双维度呈现 | **CLOSED** |

---

## 四、验证结果与回归测试全景

```bash
$ python3 -m compileall src tests
Listing 'src'...
Listing 'src/macao'...
Listing 'tests'...

$ git diff --check
(No output, exit code 0)

$ python3 -m unittest discover tests
..................................................................................................................................................................
----------------------------------------------------------------------
Ran 162 tests in 85.444s

OK
```

- **全量测试数**: **162 项测试全部通过 (0 failed, 0 error)**；
- **新增加专项测试**:
  - `tests/test_p1_closures_and_regressions.py`: 20 项严格边界与反例回归测试；
  - `tests/test_pi_and_session_locator.py`: 9 项 Pi CLI 与多 CLI 发现测试；
  - `tests/test_task_adopt.py`: 5 项场景 C 在途项目接管与 dry-run 观察测试；
- **静态质量**: `compileall` 与 `git diff --check` 均 100% 干净通过。
