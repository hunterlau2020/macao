# MACAO L3 终局闭环申请 独立复审结论（qwen）

- **评审日期**：2026-08-29
- **评审人**：qwen（独立评审）
- **被评审范围**：`ea536ab..7935da3`（申请 `2026-08-29-review-request-L3-Final-Closed.md`，目标 **L3 SCENARIO-VERIFIED / PG-2**）
- **评审方法**：独立复放，不采信申请与他方报告——49 测试两轮、`test-clis`/`e2e-run` 实机重放、**20 项自研反例**（**全生产路径**：.dev.yml → check → dispatch → 真实时钟 1s 超时 → 无参自动检测 → 人工裁定 → 终局票面/账本/物理文件三级核对）、PRD 逐条对照、评审注册表全量对账
- **结论**：**代码判据满足，支持授予 L3 SCENARIO-VERIFIED / PG-2；但定级宣告设一项强制前置条件**——评审注册表存在归属错误（本人上轮报告被以 zcode 名义提交，zcode 独立意见缺失），须先修正并补齐 zcode 报告方可由 STATUS 宣告定级。

---

## 一、申请清单 3 项逐条独立复验

| 编号 | 申请声明 | 独立复验方法与结果 | 判定 |
|---|---|---|---|
| **P1-1** | 超时 ABSTAIN 写入终局 vote_result + deadline 记录 + 时钟自动检测 | **独立复现（生产默认分支，申请测试未覆盖）**：配置 `per_reviewer: 1s`，走完整生产路径（dispatch 后 message_queue 两条 REVIEW_REQUEST `deadline` 均非空——claude 上轮 P1-NEW-1 证据 3 归零）；真实时钟 2.5s 后**不传参调用** `collect_and_evaluate_consensus` → 内部 `detect_timed_out_reviewers()` 自动检出 `["opencode"]` → DEADLOCK HOLD 不写盘、状态 `CONSENSUS_CHECK`、`REVIEWER_TIMEOUT_ABSTAIN`+`DEADLOCK_DETECTED` 审计、`HUMAN_OVERRIDE_REQUEST` 发布；人工 APPROVED → 终局 JSON `votes={codex: YES_APPROVE, opencode: ABSTAIN}`、`reviewers_responded=2`、`approve=1/abstain=1`、`resolution=human_override`——**PRD §2.2:318/§3.3:834 全口径符合**。测试断言已强化（盘上 JSON 票面/统计/审计正向断言，删除合成逻辑必挂，满足变异杀死） | ✅ VERIFIED |
| **P1-2** | 消费 key 修正 + sha256 自动补齐 | `fsm.py` 改 `name.replace(".review.yml","")` 提取 reviewer_id；`store.py` content 为空时读盘计算哈希（project_root 拼接）。独立复验：E7 裁定后 artifacts **3/3 `consumed=1`**、`archived_path` 均为 `.macao/archive/<40位SHA>/r1/...`、sha256 均 64 位，且**与归档物理文件内容逐一重算一致**（比申请测试更强的双向核对）；e2e 测试断言 5/5 同口径 | ✅ VERIFIED |
| **P3-1** | 尾随空白清理，`git diff --check 4df059e..HEAD` 返回码 0 | POC 报告 25 行已清理 ✓；**但实际返回码 2**：`4df059e..7935da3` 范围内 0c8bf11 同步的 codex 报告含 5 处尾随空白（markdown 硬换行）——申请声明**不实**。本轮终用范围形式检查（进步），但仍未实际核返回码（**连续第 4 轮洁净度声明失真**）。src/tests 范围干净 | ⚠️ 部分 VERIFIED（P3） |

## 二、机验独立复放

| 项目 | 结果 |
|---|---|
| 49 项测试 ×2 | Ran 49 / OK ×2（12.40s / 12.00s，0 flake） |
| `test-clis` | 4/4 PASS，0 FAIL 行 |
| `e2e-run` | 7 步 OK、Archived 5、终态 DONE |
| 自研反例 20 检查 | **20/20 PASS**（含申请测试未覆盖的无参自动检测分支、sha256↔物理文件一致性） |
| 评审场景（GUIDELINES §6） | 超时弃权→死锁→接管链路（本轮核心）实测闭合；此前轮已验的全同意/返工循环/崩溃恢复/1:1 保持绿 |

## 三、本轮新发现

### GOV-1（P1·评审注册表完整性）：本人 ea536ab 轮报告被以 `zcode` 名义提交，zcode 独立意见缺失

- **证据**：目录无 `2026-08-29-review-result-ea536ab-qwen.md`；`-zcode.md`（83 行）内容**逐字为本人报告**（含本人独有的"23 项自研反例脚本"、R1~R9 编号、§四与 codex 的定级分歧表）；该文件由 0c8bf11（hunterlau）提交，STATUS:30 据此登记"zcode (4 份)"并概括"四方专家一致确认"
- **影响**：(a) qwen 报告归属被冒名，审计链失真（GUIDELINES §1.3/§10）；(b) **zcode 对 ea536ab 的独立意见实际不存在**——上一轮"四方一致 REJECT"实为三方（claude/codex/grok）+ 被误标的 qwen；(c) "100% 全量对账"声明不成立
- **修正要求**（纯文档，无代码变更）：将该文件重命名/恢复为 `-qwen.md`；补 zcode 本人独立出具的 ea536ab 报告（或在 STATUS 显式登记"zcode 未出具"）；STATUS:30 行同步更正
- **定级影响**：不否定本轮代码修复的真实性；但按"定级须四方/五方真实对账"的既定纪律，**STATUS 宣告定级前必须完成本修正并取得 zcode 独立意见**

### P3 新登记

| # | 内容 |
|---|---|
| N1 | `parse_duration` 非法输入静默回落 600s（应 fail-fast 或告警） |
| N2 | `vote_breakdown` 裁剪为 approve/reject/abstain 后，e2e_runner `effective_votes` 回落为 approve 数（纯展示语义，弃权场景下显示口径变化） |

## 四、残余登记（P2/P3，不阻塞，随分发/下轮闭环）

| # | 级别 | 内容 |
|---|---|---|
| R1 | P2 | `get_schemas_dir()` 向上遍历（**本人第 5 轮追踪**；pip 分发前必修） |
| R2 | P2 | E2E reviewer 仍于主仓库产出 `.review.yml`，worktree 内消费未闭环（codex 系） |
| R3 | P2 | 脏树守卫不覆盖 untracked；合并流水线于用户工作区执行（TOCTOU） |
| R4 | P2 | push 成功后 ls-remote 失败的远端不确定态（本地 reset+REWORK 三分叉；建议 HOLD 不确定态） |
| R5 | 历史 | ACK 全量误确认、签字未绑定 checkpoint、归档 git 消费语义、PTY 真实合同（codex 系，面板定级分歧，STATUS 应显式列为已知限制） |
| R6 | P3 | task_id 24-bit 熵 + IntegrityError 无有界重试 |
| R7 | P3 | 范围洁净度声明第 4 轮失真（本轮实据：codex 报告 5 处尾随空白） |

## 五、定级判定

**支持授予 L3 SCENARIO-VERIFIED / PG-2（附一项强制前置条件）。**

- ea536ab 轮全部代码级阻断（超时 ABSTAIN 落盘+自动检测+deadline、消费账本+sha256）经独立复放真实闭环，且修复质量高于申请测试声称（生产默认分支、物理文件哈希一致性均独立补验）；
- L3 判据场景（全同意/僵局/超时/弃权/恢复/返工循环）经历轮+本轮全部具备可复现测试证据；
- 仅余 P2/P3（§四）+ 一项治理修正（GOV-1）。

**前置条件（STATUS 宣告定级前必须完成）**：GOV-1 注册表修正 + zcode 独立报告补齐（若 zcode 复审提出新的代码级 P0/P1，则回归整改流程）。

## 六、全量对账声明

`reviews/` 目录现有 **43 份评审报告**（其中 ea536ab 轮 4 份中 1 份归属错误，见 GOV-1）+ **8 份申请**；STATUS 已登记本轮申请（五方面板待出）。截至本报告，本轮（7935da3）已出：qwen（本报告，支持附条件）。其余 claude/codex/grok/zcode 待出。

## Reviewer 自审记录

- 上轮登记的"权威产物字段级核对"检查项本轮已执行（终局 JSON 票面逐字段断言 + sha256 重算比对），闭环了本人上轮盲区
- 主动暴露并举证 GOV-1（涉及本人报告被冒名——利益相关，仅陈述文件系统与 git 证据，不做动机推断，修正方案留待申请方与 zcode 执行）
- 对申请"返回码 0"的证伪基于实际执行而非推断；src/tests 范围独立复核确认干净
- 未覆盖：真实远端 push、真实 LLM 评审质量、Windows
