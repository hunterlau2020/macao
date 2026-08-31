# Phase 3 PG-3 / L4 Final 独立复审结论

- **评审日期**：2026-08-31
- **Reviewer**：Codex
- **评审对象**：`ac32dbb04de7bd4ca46be38191707e08e875519a`（短 SHA：`ac32dbb`）
- **申请文件**：`docs/reviews/2026-08-31-review-request-Phase3-PG3-L4-Final.md`
- **增量范围**：`15e8918..ac32dbb`；同时复核申请声明的完整 Phase 3 范围 `3c5ed32..ac32dbb`
- **权威基准**：`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/MACAO_PRD_v2.md`
- **方法**：冻结提交静态审读、81 项回归、CLI 实跑、隔离临时仓库、fault injection、文档交叉核验
- **独立性**：未将其他 Reviewer 的结论或票数作为证据；未修改工作区既有评审报告

## 1. 结论

**REJECT：不授予 L4 RELEASE-READY，不授予 PG-3。最高维持既有 L3 SCENARIO-VERIFIED / PG-2。**

本轮整改确实关闭了 daemon 活跃超时接线、任意 YAML 默认赞成、未知 CLI 静默回退、Mock 构造、三值 ABSTAIN Schema、feature branch、gitignore 存量升级和差异洁净度等问题；但 L4 要求的真实 OPS、用户可见人工接管、生产 Reviewer 安全准入和零 P0/P1 尚未达成。

本次独立复核登记 **7 项 P1、2 项 P2**。其中最直接的发布阻断证据是：

1. `live-run` 的三名 Reviewer 全是 `mock-cli`；将所有真实 PTY 启动替换为必抛异常后仍然 `PASS`，真实 PTY 调用数为 0。
2. `live-run --no-auto-signoff` 返回任务正在等待签字，但 CLI 的 `finally` 随即删除承载任务数据库的临时仓库；紧接着执行 `macao merge approve` 得到 `No active task found`。
3. dispatcher 从不调用 `preflight()` / `capabilities()`；一个未安装、未认证、`can_review=False`、`supports_worktree=False`、`execution_mode=FULL` 的故障注入 Adapter 仍成功提交批准票。
4. ReviewExtractor 在最后的修正块无效时会退回更早的批准草稿；一字符 SHA 前缀也会被接受并重写成当前 checkpoint。
5. push 已成功而 `ls-remote` 暂时失败时，MergeController 仍仅 reset 本地并返回失败，远端、目标分支与 FSM 可能分叉。

## 2. 证据矩阵

| 申请声明 / 门禁 | 独立结果 | 状态 |
|---|---|---|
| 81 项测试 | `PYTHONPATH=src python3 -m unittest discover tests -v`：`Ran 81 tests ... OK` | VERIFIED |
| 编译与差异洁净度 | `compileall` exit 0；`git diff --check 3c5ed32..ac32dbb` exit 0 | VERIFIED |
| daemon 活跃超时 | 新增活任务测试通过；实现复用 `detect_timed_out_reviewers()` 并传入 timeout IDs | VERIFIED |
| ABSTAIN Schema | src/docs Schema 与类型支持 `ABSTAIN / ABSTAINED`，映射约束存在 | VERIFIED |
| `live-run` 真实多 Agent | 配置明确使用三个 `mock-cli`；禁用真实 PTY 后仍 PASS、PTY calls=0 | CONTRADICTED |
| 操作员签字 | 默认由 `system-runner` 写入 `HUMAN_MERGE_APPROVED`；无自动签字路径无法在 CLI 返回后继续 | CONTRADICTED |
| 人工接管实机演练 | 测试直接调用内部方法并直接写票、timeout 列表与签字事件；未走用户 CLI/daemon | CLAIM_ONLY |
| Reviewer 安全准入 | FULL/未安装/不可 review Adapter 在从未调用 preflight/capabilities 的情况下返回 SUCCESS | CONTRADICTED |
| 提取器严格末块语义 | 最终矛盾块被忽略，早先批准块被接受 | CONTRADICTED |
| setup 智能推荐 | 模拟系统无任何 CLI 时，仍生成 OpenCode Executor + Cursor/Claude/AGY Reviewer | CONTRADICTED |
| 六 CLI 联调 | preflight 表显示六 CLI；`test-clis` 实际只跑四个 CLI 的 `--version` | PARTIALLY_VERIFIED |
| 发布手册齐备 | README/FAQ/PRD 仍存在真实、沙箱、探活、路径、测试数及规范来源矛盾 | CONTRADICTED |

## 3. 上轮问题闭环确认

### 已关闭

1. **daemon API/字段接线**：`src/macao/workflow/daemon.py:32-54` 已改为调用 Orchestrator 的统一 timeout API，并把 `timed_out_reviewers` 传入共识计算；活跃任务测试通过。
2. **缺票默认赞成与基本上下文错绑**：`src/macao/workflow/live_dispatcher.py:68-128` 要求显式 vote/status，并拒绝常见矛盾组合；Reviewer 与 review round 的显式错绑测试通过。
3. **未知 CLI 回退**：`live_dispatcher.py:173-181` 现在对未知 CLI 抛错，不再回退 OpenCode。
4. **Mock Adapter 构造与工作树调用**：Mock 具备默认 `cli_name`，dispatcher 测试能够创建、消费并清理 worktree。
5. **ABSTAIN**：两份 review manifest Schema 与类型定义同步支持三值投票。
6. **Runner 分支与 dispatcher 调用**：runner 现在创建 feature branch，并确实调用 `dispatch_review_in_worktree()`；耗时也不再硬编码。
7. **setup 局部整改**：已有 `macao.yaml` 会先备份；gitignore 逐规则补齐；生成配置的 2/3 数值改为 `ceil(2N/3)`。
8. **文档局部整改**：FAQ 的废弃 `e2e-run` 已改成 `live-run`；冻结增量无 trailing whitespace。

### 仅部分关闭

- 上轮 Codex P1-1（真实协同）只从“runner 直接写票”提升到“runner 调用 Mock Adapter”；没有真实 Agent CLI 产出。
- 上轮 Codex P1-4（安全准入与 conformance）只修复未知 CLI 回退；preflight/capability/security 门禁和真实命令场景未实现。
- 上轮 Codex P1-5（setup）只增加备份；探测结果仍不驱动团队选择，CLI/model 可用性仍不校验。
- 上轮 Codex P1-6（手册）只修了部分字面项；用户操作流程和强声明仍与代码不一致。

## 4. P0

本轮未登记 P0。以下 P1 均为 L4 / PG-3 不可豁免项。

## 5. P1：发布前必须关闭

### P1-1：`live-run` 仍是 Mock 仿真，不是六 CLI 的真实协同或生产消费链

**代码证据**：

- `src/macao/workflow/live_runner.py:49-58` 把三位 Reviewer 全部配置为 `cli: mock-cli`。
- `live_runner.py:94-119` 仍由 runner 自己写业务代码、commit 和 `.dev.yml`，没有调度真实 Executor。
- `live_runner.py:135-151` 虽接通 dispatcher，但实际实例化的是 MockAgentAdapter；Mock 在 `src/macao/adapter/mock.py:66-101` 自己生成固定批准 YAML。
- 生产工作流中只有 demo runner 调用 `dispatch_review_in_worktree()`；普通 `macao task create`、Orchestrator 和 daemon 没有消费者把 AEP REVIEW_REQUEST 接到 LiveDispatcher。
- fault injection 将 `PTYSession.start()` 改为必抛异常，runner 仍 `PASS`，真实 PTY 调用数为 0。
- `src/macao/adapter/integ_harness.py:83-95,153-159` 的批量联调只运行 Claude/Codex/OpenCode/AGY 的 `--version`；没有 Cursor/Kimi，也没有生产 start 命令、任务注入、manifest、ACK 或恢复。

申请 `docs/reviews/2026-08-31-review-request-Phase3-PG3-L4-Final.md:14,32,34-35` 至多证明 Mock Adapter + 物理 worktree 的受控集成，不能作为 L4 真实多 Agent OPS 证据。

**验收标准**：至少用申请声明支持的真实 CLI 组合完成 Executor→checkpoint→Reviewer prompt→manifest→ACK→consensus→merge；普通产品入口而非仅 demo runner 能消费 AEP 并调起 dispatcher；保存命令、版本、模型、PID、cwd、退出码、产物 SHA 和会话日志；限流、凭据失效、PTY 断开与超时均有失败路径。

### P1-2：人工签字门禁可被系统事件绕过，真正的 CLI 签字流程不可继续

**代码与实跑证据**：

- `src/macao/cli/main.py:401-403` 的 `live-run` 默认 `auto_signoff=True`。
- `src/macao/workflow/live_runner.py:171-178` 由系统写入事件类型 `HUMAN_MERGE_APPROVED`，只是把 signer 改名为 `system-runner`。
- `src/macao/merge/controller.py:48-61` 只检查事件类型和 checkpoint，不验证 signer 是否人类、来源是否受信、是否允许自动签字；因此 system-runner 完全满足“require_human_signoff”。
- `live_runner.py:179-189` 在 `--no-auto-signoff` 下返回临时任务；但 `src/macao/cli/main.py:411-422` 随后无条件 `runner.cleanup()`，删除该临时仓库和 state.db。
- 独立 CLI 重放：`live-run --no-auto-signoff` 提示任务进入 MERGING 并要求运行 `macao merge approve`；紧接着执行该命令得到 `No active task found for merge approval`。
- `tests/test_phase3.py:356-439` 的“人工接管”测试由测试代码直接写 review manifests、直接传 `timed_out_reviewers`、直接调用 `resolve_override()`、直接写 `HUMAN_MERGE_APPROVED` 和直接执行 merge；没有 daemon、Click CLI 或真实操作员参与。

这不满足评审指引 `docs/MACAO_REVIEW_GUIDELINES.md:62,108` 的“用户可见人工接管实机演练”。

**验收标准**：自动签字不得产生或满足 HUMAN 门禁；`--no-auto-signoff` 必须在持久项目中保留任务，真实用户另一次 CLI 调用完成 override/signoff/merge；签字记录包含可验证主体、来源与 checkpoint；用 subprocess/CLI 黑盒测试完整演练，不能直接写审计事件代替人类动作。

### P1-3：dispatcher 仍未执行 Reviewer capability、认证、版本和安全边界门禁

**证据**：

- `src/macao/workflow/live_dispatcher.py:203-239` 直接创建 Adapter、worktree、start、inject；没有调用 `preflight()` / `capabilities()`，也不检查 `can_review`、`supports_worktree`、`supports_noninteractive`、`execution_mode` 或 `security.allowed_clis`。
- 独立注入 Adapter：`installed=False`、`auth_valid=False`、`in_matrix=False`、`can_review=False`、`supports_worktree=False`、`execution_mode=FULL`；dispatcher 仍返回 `SUCCESS`，preflight/capability 调用数均为 0。
- Claude Adapter 仍声明 `FULL`（`src/macao/adapter/claude.py:19-27`），以 `--dangerously-skip-permissions` 启动（`:60-69`），但 registry 允许其担当 Reviewer；违反 PRD `docs/MACAO_PRD_v2.md:1405-1418` 的 Reviewer sandboxed 硬门禁。
- 所谓 sandboxed 对多数 Adapter 只是枚举声明加独立 cwd，没有 PRD `:1407-1410` 所定义的容器/受限环境、网络默认禁止或命令白名单。
- preflight 在发现二进制后普遍把 `auth_valid` / `in_matrix` 设为常量；并未执行 PRD `:1422-1427` 的凭据、版本矩阵、限流、断线、幂等和 producer→consumer conformance。

**验收标准**：dispatcher 在创建/启动前强制校验安装、认证、版本矩阵、Reviewer 能力和受限执行模式；任何失败均无 worktree、无任务注入、无票；真实沙箱边界可测；六 CLI 支持矩阵逐项由统一 conformance suite 证明。

### P1-4：ReviewExtractor 的“最后有效块”策略仍可能把已撤回的批准草稿计票，checkpoint 绑定也过宽

**证据**：

- `src/macao/workflow/live_dispatcher.py:63-160` 收集所有“有效”块并返回最后一个有效块；如果最终修正块因矛盾、截断或 Schema 错误无效，会静默回退到更早草稿。
- 独立反例：首块为 `YES_APPROVE/APPROVED`，末块明确标注 final 但为 `NO_APPROVE/APPROVED` 矛盾；函数返回 `ok=True, vote=YES_APPROVE`。这把最终失败/纠正信号变成先前批准。
- `live_dispatcher.py:134-137` 接受任一方向的字符串 prefix；`checkpoint_ref: a` 会匹配 `abcdef123456`，然后在 `:143-144` 被重写成完整当前 ref。Schema 又没有最短安全 SHA 长度。
- PRD `docs/MACAO_PRD_v2.md:1431-1436` 要求 Schema 失败时同一会话 local re-prompt 一次；当前 dispatcher 不发送任何纠错提示，只会重复读取日志并可能回退旧块。PRD 同处写“首个合法块”，Phase 3 申请又写“最后有效块”，规范也未统一。

**验收标准**：以最后一个候选块作为最终意图；若最后候选无效则 re-prompt 或 fail-closed，禁止回退旧批准；checkpoint 必须精确等于规范化 full SHA，或经 Git 唯一解析后等值且满足最小长度；加入最终截断、最终矛盾、短/歧义 SHA、多块撤回测试。

### P1-5：setup 仍未根据探测结果生成可运行团队

**证据**：

- `src/macao/cli/wizard.py:14-40` 仅探测 PATH/`--version`，不探测可用模型；命令异常时还用默认版本伪装成功。
- `wizard.py:122-127` 无条件选择 Cursor、Claude、AGY Reviewer，与 probe 结果无关；Executor 参数也不验证安装、认证、角色或 model。
- 独立反例把所有 `shutil.which` 设为 None：probe 返回 0 个 CLI，但 `generate_smart_config()` 仍生成 OpenCode Executor 和 Cursor/Claude/AGY Reviewer。
- `src/macao/cli/main.py:354-369` 探测结果只用于打印，未传给 config generator。
- README `:39-48` 仍声称自动探测并“智能推荐团队配置”，与行为相反。

备份已有配置是正向整改，但无法使生成的新配置变得可运行。

**验收标准**：探测结果驱动候选列表；未安装/未认证/不支持角色或模型的 CLI 不得入选；用户显式选择并确认；生成后执行 conformance，失败不替换原配置；加入零 CLI、单 CLI、模型无效及备份恢复黑盒测试。

### P1-6：push 后验证失败仍执行本地-only rollback，制造远端/本地/FSM 分叉

**证据**：

- `src/macao/merge/controller.py:123-127` push 成功后，远端已经可能前进。
- `merge/controller.py:129-140` 若随后 `ls-remote` 暂时失败、为空或返回不一致，代码只执行本地 `reset --hard pre_merge_head` 并返回失败。
- 独立 fault injection：push 返回成功、`ls-remote` 返回瞬时失败；结果为 `ok=False, push_succeeded=True, local_reset_after_push=True`。

调用方随后可能把任务转入 REWORK，但远端目标分支已包含 checkpoint；所谓 rollback 并未回滚远端，也未把状态标为 UNKNOWN/NEEDS_RECONCILIATION。

**验收标准**：push 后验证失败视为不确定提交，进行有界重试和权威远端查询；不能宣称本地 reset 是回滚；无法确认时保持本地 checkpoint、冻结自动状态转换并进入人工 reconciliation；补充 push-success/verify-timeout、远端 mismatch 和重启恢复测试。

### P1-7：用户手册与权威 PRD 仍不足以唯一推出真实行为

**证据**：

- README `:72` 把 Mock runner 称为“生产级多 Agent 真实协同”；FAQ `:29-52` 也把它列为真实 CLI 完整流程。
- FAQ `:234-235` 声称派发前检测 Session Lock、API Token 和 PTY 延迟；代码没有这些探针。
- FAQ `:242` 与 PRD `:1703-1706` 使用 `.macao/worktrees/<task>/<reviewer>`；实现使用 `.macao/worktrees/<reviewer>/<task>/r<round>`（`src/macao/workflow/live_dispatcher.py:194-201`、`src/macao/utils/git_utils.py:96-122`）。
- PRD `:1431-1436` 声称 local re-prompt，代码没有；同一 PRD `:1433` 称首个合法块，终审申请称最后有效块。
- PRD `:1405-1418` 限定 Reviewer 安全矩阵，而 `:1722-1725` 又称六 CLI 全角色自由组合，没有说明后者如何满足前者硬门禁。
- README `:45-48` 的 setup 智能推荐声明不实；README `:175` 链接已删除的 `docs/reference/MACAO_REVIEW_GUIDELINES.md`。

因此 L1 文档一致性和 L4“用户手册齐备”均未达到 VERIFIED。

**验收标准**：统一路径、候选块、角色矩阵与沙箱定义；按 Mock 演练、真实 CLI OPS 分层命名；删除未实现的探活/re-prompt/智能推荐声明或补实现；从干净安装开始由非开发者按文档完成 setup、真实 review、HOLD、override、signoff、merge 和恢复。

## 6. P2 / P3

### P2-1：测试数徽章与终审申请不一致

终审申请 `:21,30` 声称 README 已更新为 `81/81 PASS`，但 `README.md:5` 实际仍是 `75/75 PASS`。该项直接证明申请对账表并未逐文件核实。

### P2-2：所谓并行评审实际串行执行

PRD `docs/MACAO_PRD_v2.md:1604` 定义“并行评审”，但 `src/macao/workflow/live_runner.py:139-151` 用普通 for-loop 逐一等待每位 Reviewer 完成。每位 Reviewer 获得新的独立 15 秒计时，同时忽略 Orchestrator 已发布的共享 deadline；这会改变后序 Reviewer 的实际截止语义。若产品选择串行，应修订规范与 deadline 模型；若保持并行规范，应加入并发调度、独立失败隔离与清理测试。

## 7. Known Issues 登记

| issue_id | 级别 | owner | due_date | resolution_commit | status |
|---|---|---|---|---|---|
| P3-FINAL-CODEX-01 | P1 | Live Runtime owner | PG-3 重审前 | TBD | OPEN |
| P3-FINAL-CODEX-02 | P1 | CLI / Human Gate owner | PG-3 重审前 | TBD | OPEN |
| P3-FINAL-CODEX-03 | P1 | Adapter Security owner | PG-3 重审前 | TBD | OPEN |
| P3-FINAL-CODEX-04 | P1 | Review Protocol owner | PG-3 重审前 | TBD | OPEN |
| P3-FINAL-CODEX-05 | P1 | Setup owner | PG-3 重审前 | TBD | OPEN |
| P3-FINAL-CODEX-06 | P1 | Merge / Recovery owner | PG-3 重审前 | TBD | OPEN |
| P3-FINAL-CODEX-07 | P1 | Docs / OPS owner | PG-3 重审前 | TBD | OPEN |
| P3-FINAL-CODEX-08 | P2 | Docs owner | 下一整改提交 | TBD | OPEN |
| P3-FINAL-CODEX-09 | P2 | Runtime owner | 下一整改提交 | TBD | OPEN |

## 8. 建议闭环顺序与终审门槛

1. 先修 P1-3、P1-4、P1-6：安全准入、最终票语义与 push 后不确定状态属于误合并/状态分叉风险。
2. 建立普通生产入口的 dispatcher 消费循环，以真实 CLI 而非 Mock 跑通最小团队；保存不可变 OPS 证据。
3. 重构 human gate：系统签字不能满足人类事件；修复持久工作区并用黑盒 CLI 完成 HOLD→override→signoff→merge。
4. 让 setup 由真实 probe/conformance 驱动，不得生成已知不可运行的默认团队。
5. 修订 PRD、README、FAQ，统一路径、角色、安全边界、候选块和 Mock/真实措辞。
6. 完成真实凭据失效、限流、PTY 断开、超时、push 后验证不确定、重启恢复和人工接管演练后，再申请 L4/PG-3。

终审证据至少包括：

- 实际真实 CLI 命令、版本/模型、认证结果、PID、cwd、checkpoint、round、deadline、退出码与日志；
- 非 runner 代写的 Executor `.dev.yml` 与真实 Reviewer `.review.yml`；
- 由两个独立 CLI 进程完成的用户接管记录，而非测试代码直接调用内部 API；
- dispatcher capability/preflight 的正反 conformance 报告；
- 远端 push 不确定状态的恢复与对账证据；
- 干净安装环境按最终手册完整重放的结果。

## 9. Reviewer 自审记录

- 已按字段实际读取位置复核：security.allowed_clis、capabilities、preflight、signer 均未进入关键门禁。
- 已逐条检查 `PASS`、`真实`、`生产级`、`全量闭环`、`81/81` 等强声明，没有以作者对账表替代证据。
- 已测试正常、最终块无效、短 SHA、无真实 PTY、安全准入、人工签字丢失与 push 后验证失败路径。
- 每项 P1 均给出文件/行号、可复现反例和验收标准。
- 本轮没有沿用其他 Reviewer 票数；未发现需要登记的连续同类漏审。
