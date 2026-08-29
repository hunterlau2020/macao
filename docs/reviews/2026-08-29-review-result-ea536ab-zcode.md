# MACAO L3 全量闭环申请 独立复审结论（qwen）

- **评审日期**：2026-08-29
- **评审人**：qwen（独立评审）
- **被评审范围**：`4df059e..ea536ab`（申请 `2026-08-29-review-request-L3-All-Items-Closed.md`，目标 **L3 SCENARIO-VERIFIED / PG-2**）
- **评审方法**：独立复放，不采信申请与他方报告结论——49 项测试两轮重跑、`test-clis`/`e2e-run` 实机重放、**23 项自研反例脚本**（task_id 并发 / max-round 写盘守卫+崩溃恢复 / 超时降级全链路 / 脏工作区防护 / worktree 物理清理 / vote fail-fast / artifacts 账本）、PRD 权威基准逐条对照
- **结论**：**不予 L3 SCENARIO-VERIFIED / PG-2。** 申请清单 8 项中 6 项安全/正确性修复经独立复放属实闭环；但 **REQ-TIMEOUT（本轮 L3 唯一新增判据）半闭环**——超时弃权未随 E7 终局 `vote_result.json` 落盘，与 PRD 明文直接矛盾（独立复现 CONTRADICTED）。该项构成 P1 阻断。

---

## 一、申请清单 8 项逐条独立复验

| 编号 | 申请声明 | 独立复验方法与结果 | 判定 |
|---|---|---|---|
| **REQ-TIMEOUT** | 超时→弃权→死锁→人工接管"全流程"闭环 | 死锁/接管链路属实：1 YES + opencode 超时 → HOLD 不写盘、状态 `CONSENSUS_CHECK`、`HUMAN_OVERRIDE_REQUEST` 发布、`REVIEWER_TIMEOUT_ABSTAIN` 审计、人工 APPROVED → MERGING ✓。**但终局 `vote_result.json` 票面无 ABSTAIN**：`votes=[{codex, YES_APPROVE}]`、`reviewers_responded=1`、`abstain=0`——违反 PRD §2.2:318「由 Orchestrator 记入本轮票面，在终局 vote_result.json 落盘时写入对应 ABSTAIN 票据并计入 reviewers_responded」与 §3.3:834「随 E7 终局 vote_result.json 一并落盘」。根因：超时 ABSTAIN 仅进内存 `votes_list` 做死锁判定（orchestrator.py:373-388），`resolve_override` 重新 `collect_reviews` 时丢失弃权记录。**测试盲区**：`test_reviewer_timeout_degradation_scenario` 不断言 ABSTAIN 票面与审计事件；1 YES + N=2 本身即死锁，合成弃权逻辑删掉测试仍绿 | ❌ **PARTIALLY_VERIFIED / CONTRADICTED**（P1 阻断） |
| **P0-1** task_id 高熵 | 同秒 100 任务 0 碰撞 | 独立复放 100 个同秒任务全唯一（`task-<ts>-<6hex>`）✓。但熵仅 24-bit：同秒 1000 任务生日碰撞 ≈2.9%，且 `IntegrityError` 无有界重试。申请"保证并发唯一性"措辞过强 | ✅ VERIFIED（P3 残余） |
| **P0-2** max-round 不写盘 | HOLD 不提前写盘 + 崩溃恢复稳固 | 独立复放：rnd≥max 且双 REJECT → 磁盘无 `vote_result.json`、状态 `CONSENSUS_CHECK`、`HUMAN_OVERRIDE_REQUEST` 发布；`StateReconciler` 恢复后仍 `CONSENSUS_CHECK` 且无盘文件（codex 上轮"恢复绕过人工接管"反例归零） | ✅ VERIFIED |
| **P0-3** 脏工作区防护 | 未提交已跟踪修改 Fail-closed | 独立复放：tracked 修改 → "Refusing to merge (Fail-closed)"、用户内容原样保留、HEAD 不动 ✓。untracked 不设防（`reset --hard` 不删 untracked，无数据丢失）+ 仍于用户工作区执行流水线（TOCTOU 窗口）→ P2 | ✅ VERIFIED（P2 残余） |
| **P1-1** worktree 物理清理 | 失败时物理清除已建 worktree | 独立故障注入（第 2 reviewer 失败）：rev1 目录物理消失、`git worktree list` 注册表干净、FSM 保持 `READY_FOR_REVIEW` ✓（claude 上轮 A 关闭） | ✅ VERIFIED |
| **P1-2** artifact 追踪 | artifacts 表 5 份记录 | 注册路径恢复属实：三处调用点（dev/review/vote_result），`ON CONFLICT DO UPDATE` 幂等，e2e PASS 判定新增 `tracked>0` 硬门禁 ✓。**但**独立复验账本消费语义：`review_manifest` 行 `consumed=0`、`archived_path=null`——`fsm.py:111` 用 `rev_file.stem`（`codex.review`）匹配注册 `reviewer_id`（`codex`），UPDATE 0 行；且注册时未传 `content=`，`sha256` 恒空 → P2（磁盘归档与账本不一致） | ✅ 注册 VERIFIED（消费 P2 残余，与 codex P2-1/grok P2-NEW-1 一致） |
| **P2-1** 先校验后写盘 | validate 前置于 write | `vote.py:174-183`：DEADLOCK 早退不写盘；否则先 `validate_vote_result` 再落盘 ✓ | ✅ VERIFIED |
| **P2-2** human_resolution fail-fast | 非法输入 ValueError | 独立复放：`"YOLO_INVALID"` → ValueError 且磁盘无部分文件 ✓。**本人三轮追踪项（R1）就此关闭** | ✅ VERIFIED |

另确认本轮**顺带修复**（未列入申请）：codex 上轮 P0-4 前半——e2e 注入路径改用 GitManager 权威布局 `<task_id>/r1` 且不存在即 RuntimeError（e2e_runner.py:207-209）；ls-remote 空输出/失败 fail-closed（controller.py:121-126）。

## 二、机验独立复放

| 项目 | 结果 |
|---|---|
| 49 项全量测试 ×2 | Ran 49 / OK ×2（13.08s / 13.17s，0 flake） |
| `test-clis --cli all` | claude 2.1.251 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22 **4/4 PASS**，0 孤儿进程 |
| `e2e-run` | 7 步 OK、votes_yes=3、Archived 5、终态 DONE（task_id 已带高熵后缀） |
| 自研反例脚本 23 检查 | **23/23 PASS**（超时链路、max-round 恢复、脏树、worktree 清理、fail-fast、并发 ID、账本） |
| `git diff --check 4df059e..ea536ab` | **1 处尾随空白**（POC_VERIFICATION_REPORT.md:25，本轮范围内修改行）；src/tests 干净 |

## 三、P1 阻断项（须先解决）

### P1-Q1：超时弃权未写入 E7 终局 `vote_result.json`（REQ-TIMEOUT 核心语义缺失）

- **证据**：独立复现（见 §一 REQ-TIMEOUT 行）；PRD §2.2:305,318、§3.3:834、§5:396-411（弃权计入票面口径）；`orchestrator.py:373-388`（弃权仅内存）、`orchestrator.py:577-588`（resolve_override 重收集磁盘 review，弃权丢失）
- **后果**：终局权威产物少记弃权票与 `reviewers_responded`，审计链与 PRD 权威口径不一致；申请"标记弃权…全流程（PASS）"声明不实
- **验收标准**：E7/E9/E10 任一写盘路径将本轮已审计超时弃权以 `vote=ABSTAIN` 写入 `votes`，`reviewers_responded`/`vote_breakdown.abstain` 同口径；专项测试正向断言弃权票面与 `REVIEWER_TIMEOUT_ABSTAIN` 审计，且删除合成逻辑后测试必须失败
- **与 codex P1-2 / grok P1-NEW-1 同源一致**（三方独立复现）

## 四、定级分歧登记（按 §8"真理不等于投票"，各自举证）

| 项 | codex 定级 | 本报告定级 | 理由 |
|---|---|---|---|
| 超时无生产触发源（`timed_out_reviewers` 全仓库仅测试传入；无 deadline 持久化/扫描/ping） | P1 | **P2** | L3 判据为"场景可复现推演或测试证据"，注入式 API + 测试满足场景验证；生产接线属 OPS/PG-3 范畴。grok 同定 P2。但 PRD §6.1 ping/人工确认未实现须登记 |
| push 成功后 ls-remote 失败 → 本地 reset + REWORK（远端/本地/状态三分叉） | P1 | **P2** | 窗口极端（push 成功后紧邻 ls-remote 瞬时失败）、可人工恢复、无用户数据丢失路径；claude 上轮同类观察亦未列阻断。建议建 HOLD 不确定态，随下轮修 |

## 五、P2/P3 登记（不阻塞本轮判定，随下轮闭环）

| # | 级别 | 内容 |
|---|---|---|
| R1 | P2 | `review_manifest` 消费账本错配（stem `codex.review` vs `reviewer_id` `codex`）→ `consumed` 恒 0、`archived_path` 空；注册未传 `content=` → `sha256` 恒空（双账本无法对账） |
| R2 | P2 | 超时降级无运行时触发源（无 deadline 持久化/扫描器/CLI 入口；PRD §6.1 ping 未实现） |
| R3 | P2 | E2E reviewer 仍在主仓库产出 `.review.yml`，worktree 内 0 份产物（codex 上轮 P0-4 后半；路径真实性已修复） |
| R4 | P2 | 脏树守卫不覆盖 untracked；合并流水线仍在用户工作区执行（TOCTOU） |
| R5 | P2 | `get_schemas_dir()` 向上遍历（**本人第 4 轮追踪**，本轮未触及，pip 分发前必修） |
| R6 | P3 | task_id 24-bit 熵 + IntegrityError 无有界重试（同秒千级任务碰撞 ≈2.9%） |
| R7 | P3 | POC_VERIFICATION_REPORT.md:25 尾随空白；**申请 §二.5 连续第三轮用裸 `git diff --check`（仅证工作区干净）替代范围检查** |
| R8 | P3 | `integ_harness.py:109` `ansi_stripped_ok=True` 常量；真实 Adapter `get_logs(tail_lines)` 签名不匹配 |
| R9 | 历史 | codex 系 P1 未入任何闭环清单且仍开放：ACK 全量误确认（bus.py:91-106）、签字未绑定 checkpoint、归档 git 消费语义、PTY 真实合同。注：zcode/claude 历轮未将其列为阻断，面板定级分歧，修复前不得宣称"全部阻断项已闭环" |

## 六、定级判定

**不予 L3 SCENARIO-VERIFIED / PG-2。**

- 6 项安全修复真实闭环（含上轮全部数据丢失/恢复绕过风险归零），49/49×2 + 4/4 + e2e 全绿复现；
- 但 REQ-TIMEOUT 作为本轮 L3 唯一新增判据，其权威产物（终局弃权票面）与 PRD 直接矛盾且测试无法证伪——按"申报证据与权威产物不一致即 CONTRADICTED"的历轮标准，构成 P1；
- PG-1"P0/P1 为零"未满足。修复面窄（单一写盘路径 + 测试断言强化），预计一轮内可闭环。

## 七、全量对账声明

`reviews/` 目录现有 **42 份评审报告**（含本轮未提交的 codex/grok ea536ab 2 份；本人本报告为第 43 份）+ **7 份申请**；STATUS.md 已登记本轮申请与"四方（Claude/Qwen/ZCode/Codex）待出"状态，grok 为面板外第 5 份报告（建议 STATUS 下轮说明其席位归属）。截至本报告，本轮已出 codex（REJECT）/ grok（REJECT）/ qwen（REJECT，本报告），claude/zcode 待出——**已出三份独立结论一致：不予 L3**。

## Reviewer 自审记录

- 重点补查了本人上轮未覆盖的盲区：终局产物票面内容（上轮只验证了"写盘发生"，未核对"写了什么"——本轮 codex/grok 的弃权指控正是在此盲区，已独立复现坐实并吸收为检查惯例）
- 连续漏审登记：本人连续三轮将"超时弃权落盘"归入 zcode/codex 责任域而未自查产物口径，本轮起将"权威产物字段级核对"列入固定检查项
- 分歧不掩盖：对 codex 两项 P1 定级持异议并逐项举证（§四），未以多数票代替证据
- 未覆盖：真实远端 push 动态复现、真实 LLM 评审质量、Windows 平台
