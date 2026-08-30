# MACAO Phase 3（PG-3 / L4 RELEASE-READY）申请 独立复审结论（qwen）

- **评审日期**：2026-08-31
- **评审人**：qwen（独立评审）
- **被评审范围**：`4e38ed6..3c5ed32`（申请 `2026-08-31-review-request-Phase3-PG3-L4.md`，待审对象 `3c5ed32`；L3/PG-2 封板后首个阶段申请）
- **评审方法**：独立复放——72 测试两轮、`live-run`/`daemon --once`/`preflight`/`test-clis`/`compileall`/`git diff --check` 实机、**11 项自研反例**（ReviewExtractor 幻影批准 5 探针、守护进程活任务崩溃复现、包内 schema 寻址、洁净度）、源码静态审计、PRD/GUIDELINES 判据对照
- **结论**：**不予 L4 RELEASE-READY / PG-3。** 独立复现 **3 项新 P1**：①L4 核心证据 `live-run` 为**自投票+自动签字的伪演练**（无真实 CLI、无提取器、无人工接管）；②`OrchestratorDaemon` 对真实系统**不可运行**（活任务上确定性崩溃 + 四处接线错误，宣称的超时降级不可能发生）；③真实 CLI 评审路径存在**幻影批准**（缺票输出被默认为赞成，动态构造成立）。L3/PG-2 基线**无回归**（72/72 含全部历轮整改测试），既有授予不受影响。

---

## 一、L4/PG-3 判据逐项核对（GUIDELINES §2.1/§2.2/§3.2）

| 判据 | 结果 |
|---|---|
| L3 基线 + 回归无 P0/P1 | ✅ 72/72×2（含历轮全部整改测试）、compileall=0；**但本轮新增 3 项 P1（§二）——就本轮增量而言"回归无 P0/P1"不成立** |
| **OPS 为 VERIFIED** | ❌ 唯一 OPS 证据 `live-run` 非真实协同（§二-P1-Q4），不构成 OPS 验证 |
| **用户可见的人工接管演练** | ❌ 不存在；`live-run` 反而以"Live runner auto-signoff"**自动伪造** `HUMAN_MERGE_APPROVED`（live_runner.py:166-170），与判据方向相反 |
| 用户手册齐备 | ⚠️ 部分：`docs/FAQ.md`（242 行）覆盖 CLI 模式/模型控制/既有项目接入；未含人工接管演练记录 |
| PG-1 纪律（P0/P1 零） | ❌ 本轮新增 3 项 P1 |

## 二、P1 阻断项（全部独立动态复现）

### P1-Q4：`live-run` 非真实多 Agent 演练——自投票 + 自动签字，L4 证据失真

- **代码证据**：`live_runner.py:138-155` 由 runner **亲手写入 3 份 `vote: YES_APPROVE` manifest** 至 `.macao/.reviews/`，全程未调用 `LiveAgentDispatcher`/`ReviewExtractor`、未拉起任何 CLI；`:166-170` 在 `require_signoff` 为真时**自动记入 `HUMAN_MERGE_APPROVED`**（note: "Live runner auto-signoff"）
- **实测**：本机 `live-run` 秒级完成、`votes_yes=3`、终态 DONE——时长与"3 个真实 CLI 各自完成评审"物理不相容；`test_phase3.py:97-106` 断言的正是该自投票路径
- **定性**：申请 §一.6"真实多 Agent 全生命周期演练"与 §二"端到端协同 7/7 全绿"**声明被证伪**——命令通过但证明力为零（与 Mock e2e 同构，且多了签字伪造）；`LiveAgentDispatcher` 的真实链路（worktree→PTY→提取→校验）**无任何端到端演练**。按 GOV 先例，证据失真为阻断级
- **修复方向**：以 `mock-cli` 或真实 CLI 经 `LiveAgentDispatcher` 走通演练；移除自投票/自动签字；补"超时/僵局 → `override resolve` 人工裁定"的**用户可见接管演练**（L4 硬性判据）

### P1-Q5：`OrchestratorDaemon` 对真实系统不可运行——活任务即崩溃，超时降级不可能发生

- **动态复现**：构造真实 `WAITING_REVIEW` 任务 + 截止时间过期 2.5s → `scan_once()` 抛 **`AttributeError: 'StateStore' object has no attribute 'get_audit_events'`**；状态停留 `WAITING_REVIEW`，无任何降级。`daemon --once` 的"exit 0"证据仅在**无活跃任务**时成立（实测 `{'active_task': None}`）——空转证据
- **静态四处接线错误**（任一即致死）：①`daemon.py:38` 查 `REVIEW_DISPATCHED`，而编排器实际记录 **`REVIEW_REQUESTS_DISPATCHED`**（orchestrator.py:358）；②读 `e["event_type"]/e["payload"]`，审计行实际键为 `type/detail`；③取 `deadline_epoch`，实际为 `deadline`（ISO 串）；④以 `kind.endswith(".review.yml")` 匹配台账，实际 `kind="review_manifest"` → 已提交者恒为空 → 若事件名修对则**全员被误判超时**
- **附加**：`limit=50` 窗口（P1-NEW-4 已修模式的复发）；`run_loop` 吞掉一切异常（`:77-78`）；仅扫描单一活跃任务
- **定性**：申请 §一.2"生产级后台守护…超时自动生成 ABSTAIN、自动触发仲裁"**不可能发生**；属宣称功能不可运行级缺陷

### P1-Q6：幻影批准——真实 CLI 评审路径缺票即默认赞成（投票完整性 fail-open）

- **动态复现**：`ReviewExtractor` 对**无 vote 的 YAML** 返回合法 `vote=YES_APPROVE` manifest（R1）；甚至对**纯上下文回声**（仅含 `checkpoint_ref/review_round/task_id`、无任何评审内容）也产出 **PHANTOM APPROVE**（R5）；显式 `NO_APPROVE` 保持 ✓、垃圾输出拒绝 ✓（方向：仅缺失→批准）
- **链路**：`live_dispatcher.py:90-91`（`vote or "YES_APPROVE"`、`status or "APPROVED"`）→ `vote.py:97` 与 `orchestrator.py:557`（`opinion.vote` 兜底 `"YES_APPROVE"`）；`test_phase3.py:45-61` 把该行为断言为**预期设计**
- **定性**：Phase 3 的真实票源是带噪终端日志；"输出未含明确票"被计为赞成使共识向合并方向偏置，与本人历轮坚持的 fail-closed 纪律（P1-NEW-11 家族）直接冲突。修复方向：缺票 → 拒绝该 manifest 或隔离为 ABSTAIN，删除全链 approve 默认

## 三、属实闭环与正向确认（独立验证）

| 项 | 结果 |
|---|---|
| **包内 Schema 打包（本人六轮追踪的 R1/寻址项真实清偿）** | 6/6 schema 与 `docs/schemas` 逐文件一致；`get_schemas_dir()` 默认解析至 `src/macao/schemas`（动态 S1）；`MACAO_SCHEMAS_DIR` 覆盖仍有效；`pyproject` package-data 配置 ✓ |
| `.gitignore` 运行时隔离 | `ensure_gitignore_isolation` 幂等（其测试 + 本人核读），`.macao/worktrees/` + `*.db` 系列入册——**claude P2-NEW-6 部分清偿**（残留：`.macao/` 产物 `.dev.yml`/`vote_result.json`/`.reviews/` 未覆盖，P2 登记） |
| 角色/模型矩阵 | `macao_config.schema` 增 `model` 字段；opencode 适配器 `-m` 透传静态属实；cursor 适配器新增 |
| 机验 | 72/72×2、compileall=0、preflight 全绿、test-clis 4/4（ANSI 正则实测） |

## 四、P2/P3 登记（不单独阻断）

1. **P2**：`probe_available_clis` 探测失败时以**默认版本号冒充实测**（wizard.py:30-33）；`detect_ci_command` 启发式误判（有 `pyproject.toml` 即 `pytest -q`——本仓库即 unittest 反例）；live_runner worktree 布局（`.macao/worktrees/<r_id>/<task_id>/r1`）与 dispatcher 布局（`<task_id>/<agent_id>`）不一致，worktree 写入分支为死代码；schema 双副本（`src/macao/schemas` vs `docs/schemas`）漂移风险——建议单一事实源 + 同步测试；死依赖 `pytest`/`prompt_toolkit`（zcode P3-3）仍未移除；`.gitignore` 未覆盖 `.macao/` 产物（见 §三）
2. **P3**：**洁净度声明第五次失真**——`git diff --check 4e38ed6..3c5ed32` exit 2（`docs/reference/REVIEW_METHODOLOGY.md:4-6` 尾随空白），申请"返回码 0，100% Clean"被证伪（模式复发，建议纳入提交前钩子）；申请"待审对象 Commit 3c5ed32"未显式界定范围起点（实际含 29ef7bc/c6340ea/docs/reference 四文件，本报告钉死 `4e38ed6..3c5ed32`）；daemon `--once` 空转证据的表述问题（§二）

## 五、定级判定

**不予 L4 RELEASE-READY / PG-3。**

- 判据缺口：OPS 未验证、人工接管演练缺失且方向相反、本轮增量含 3 项动态复现的 P1；
- **L3 SCENARIO-VERIFIED / PG-2 维持不受影响**：72/72 回归含全部历轮整改项，基线状态机/共识/归档语义无变化；
- 修复面评估：三项 P1 均属**可单轮闭环**——真实演练管线接线（mock-cli 即可自证）、daemon 五处接线修正+活任务测试、全链 approve 默认移除；完成并附接管演练记录后，本人将复验。

## 六、全量对账声明

`reviews/` 现有 **76 份结果在盘**（72 提交 + 4e38ed6 轮 grok/zcode 已入库、本轮尚无同行报告，本报告为首份）+ **16 份申请**；STATUS 已登记 L3/PG-2 授予（371008d/8ea8e97）。

## Reviewer 自审记录

- 本轮为**新阶段首轮**：探测面从状态机回路扩展到真实集成层（提取器输入构造、守护进程接线、演练证据真实性）；三项 P1 均为动态构造复现，非静态推断
- 对申请机验逐条重跑而非采信：`daemon --once` 的 exit 0 经活任务反例揭穿为空转证据；`live-run` 的 7/7 经时长/代码双证揭穿为自投票
- 正向项独立确认后如实登记（schema 打包为本人六轮追踪项的真实清偿，不因整体 REJECT 而没入）
- 利益相关声明：本人上轮支持授予（L3/PG-2 已达成）；本轮 REJECT 仅针对 L4 增量证据与新增缺陷，附全部可复现路径
- 未覆盖：真实 LLM 评审质量、win32、远端真实 push、多任务并发
