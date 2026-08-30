# MACAO L3/PG-2 终局认证申请 独立复审结论（qwen）

- **评审日期**：2026-08-29
- **评审人**：qwen（独立评审）
- **被评审范围**：`f41b9da..bf5ae2d`（申请 `2026-08-29-review-request-L3-Final-Certification.md`，HEAD `99526aa`）
- **评审方法**：独立复放——58 测试两轮、`test-clis`/`e2e-run` 实机、**24 项自研反例**（迟到票隔离、E9 重试后共识反例、签字代际绑定+审计洪水、非法转移前置校验、HOLD 轮询幂等、Adapter/Schema/parse_duration/task_id/sha256 六维加固逐项动态验证）、PRD 权威对照、注册表全量对账
- **结论**：**不予 L3 SCENARIO-VERIFIED / PG-2（差一项）。** 申请 5 项闭环中 4 项完全属实（含 GOV-1 治理项本轮真实落实），6 项主动加固全部属实，机验全绿——本轮工程质量为历轮最高；但 **P1-NEW-6（RETRY_REVIEW 活锁）修复不完备**：重派发属实，然而重试轮被旧超时处置毒化，**RETRY_REVIEW 后即使全员按时全票赞成仍永久 HOLD**，被超时者的新票被误标隔离——独立复现两次，构成新的 P1 阻断。

---

## 一、申请清单 5 项逐条独立复验

| 编号 | 申请声明 | 独立复验结果 | 判定 |
|---|---|---|---|
| **P1-NEW-5** | 签字绑定 checkpoint_ref 硬校验 | **动态属实**：R1 签字 + R2 checkpoint → 拒绝（报错含目标 SHA）；补 R2 签字 → 通过；注入 60 条审计洪水后签字仍可寻址（顺带闭环 claude P2-NEW-1 定向查询，申请未声明） | ✅ VERIFIED |
| **P1-NEW-7 / P1-Q2** | 迟到票据持久化隔离，不参与自动共识 | **动态属实**：1 赞成+1 超时 HOLD 后迟到者补交 → 仍 HOLD、无盘、`LATE_REVIEW_ISOLATED` 审计落库；人工 APPROVED 后终局 `opencode:ABSTAIN`、`resolution=human_override` | ✅ VERIFIED |
| **P1-NEW-6** | RETRY_REVIEW 清旧票+重派发新 deadline，"解决超时活锁" | **部分属实**：重派发真实（新 `REVIEW_REQUESTS_DISPATCHED` 审计、消息 2×2、`.reviews/` 清空、状态回 `WAITING_REVIEW`）；**但重试轮被旧轮 disposition 毒化——见 §三 P1-Q3，活锁未解，"解决"声明被证伪**；新测试断言止步于重派发，未覆盖重试后共识（测试盲区） | ⚠️ PARTIALLY_VERIFIED |
| **P2-NEW-2** | 非法转移前置校验，不写孤儿产物 | **动态属实**：`WAITING_REVIEW` 下 override APPROVED → `ValueError("Illegal state transition...")`、盘上无 `vote_result.json`、artifacts 无注册、`TRANSITION_REJECTED` 审计 | ✅ VERIFIED |
| **GOV-1** | 注册表更名勘误 | **属实**：git 显示 `ea536ab-zcode.md → ea536ab-qwen.md` 纯更名（0 行内容变化）；本人 f41b9da 报告以 `-qwen.md` 正确落库；STATUS:36 该轮登记修正为 claude/codex/grok/qwen（不再虚报 zcode）。**连续两轮追踪后真实闭环**。残留：STATUS 头部"47 份报告"计数过时（实际 **51 份**结果 + 10 份申请，P3 文档项） | ✅ VERIFIED（残留 P3） |

## 二、六项主动加固逐条独立复验（申请 §二）

| 加固项 | 独立复验 | 判定 |
|---|---|---|
| Adapter 契约一致化（codex P1-6） | `get_clean_logs(3)` 尾切 ✓ / 无参全量 ✓；`AgentAdapter` 抽象化后不可实例化 ✓；5 真实适配器 + Mock 均实现 `cancel()/get_logs()` 返回 str ✓——上轮确定性 TypeError 已消除 | ✅ |
| Schema 四级寻址 | `MACAO_SCHEMAS_DIR` 覆盖生效 ✓；默认解析到真实 `docs/schemas` 且 dev_manifest schema 存在 ✓（本人 R1 六轮追踪项闭环） | ✅ |
| `parse_duration` 显式校验 | 非法串 `ValueError` ✓；空串回落 default ✓；s/m/h/d 全单位 ✓（本人 N1 项闭环） | ✅ |
| Task ID 32-bit + 重试 | 50 任务同秒全唯一、后缀 8-hex ✓；5 次重试代码在（codex P2-1 项闭环） | ✅ |
| SHA256 归档自愈 | 注册时文件缺失→空；写文件后 `mark_artifact_consumed` 自动补齐 64 位哈希（与实测 sha256 一致）✓ | ✅ |
| EXPERT_QUALITY.md | 文件落地（bf5ae2d，+画像/攻击模型/十律） | ✅ |

## 三、P1 阻断项（独立复现两次，须先解决）

### P1-Q3：E9 重试轮被旧超时处置毒化——RETRY_REVIEW 后全票按时赞成仍永久 HOLD，且新票被误标"迟到"隔离

- **复现**（2 Reviewer，真实 1s 时钟，独立复现两次）：codex 赞成 + opencode 超时 → HOLD + 接管请求 ✓ → 人工 `RETRY_REVIEW` → `WAITING_REVIEW`、旧票清除、新 deadline 重派发（disp=2, msgs=4）✓ → **两位 Reviewer 均按时提交赞成票** → `collect_and_evaluate_consensus` → **仍 HOLD 于 `CONSENSUS_CHECK`**：opencode 的新票被记 `LATE_REVIEW_ISOLATED`（isolated=1）、合成 ABSTAIN、有效票 1/2 → DEADLOCK。再次 RETRY 同样结果——**该轮永远无法自动收敛，唯一出路是人工 APPROVED/REWORK/CANCEL**
- **根因**：`orchestrator.py` collect 将 `REVIEWER_TIMEOUT_ABSTAIN` **仅按 `review_round` 过滤**并入 `timed_out_reviewers` 并集；E9 按规定**不递增轮次**，旧 deadline 推导出的弃权处置跨越重派发生效，同时触发迟到票隔离（该隔离逻辑只看 reviewer 是否在 timed_out 集合）
- **PRD 依据**：§3.3 E9"**本轮已收意见作废**归档；重新发送 REVIEW_REQUEST（全新 message_id 与 deadline）"——"作废"应涵盖由已被作废意见/旧 deadline 推导的超时弃权处置；新 deadline 下按时提交的是合法新票而非"迟到票"
- **危害方向**：fail-closed（无不安全合并），但使 E9——超时后语义上最保守的推荐出口——在功能上仍是死路：本轮申请声称的"闭环 RETRY_REVIEW 超时活锁"仅在"重派发"半步成立，"活锁解除"半步被证伪
- **修复方向**（窄）：disposition 绑定派发代际（`REVIEWER_TIMEOUT_ABSTAIN` 记录 dispatch 标识/deadline，collect 仅采信**最新一次 dispatch 之后**的超时事件），或 RETRY_REVIEW 时写入轮次作废审计并令 collect 过滤；补"重试后全员按时赞成 → automatic APPROVED"与"重试后再次超时 → HOLD"两个正反例测试

## 四、机验独立复放

| 项目 | 结果 |
|---|---|
| 58 项测试 ×2 | Ran 58 / OK ×2（14.5s / 14.8s） |
| `test-clis` | 4/4 PASS |
| `e2e-run` | 7/7 OK、终态 DONE、5 份产物物理归档（PERSISTED） |
| 自研反例 24 检查 | 23/24 PASS（唯一 FAIL 即 §三 P1-Q3 活锁复现；另有 1 处本人脚本计数 bug 已排除，单独复跑 disp=2/msgs=4 属实） |
| `git diff --check f41b9da..HEAD` | exit 0 ✓（连续第二轮属实） |

## 五、定级分歧登记（独立定级，不随票）

| 项 | 提出方定级 | 本报告定级 | 理由 |
|---|---|---|---|
| E9 重试轮毒化活锁 | （本轮新发现，无人提出） | **P1**（§三） | 声明闭环被证伪 + PRD E9 语义违背 + L3 超时→重试场景证据链断裂 |
| timeout 无生产驱动/ping | codex P1-1（连续三轮） | P2 | 维持：L3 场景证据级已足；"任何超时必经人工"语义已落地；扫描器/ping 属 PG-3 OPS |
| publish 非事务 | codex P1-3 | P2 | 本轮 dispatch 已改"worktree 全成功→E2→发布"单向序，残余为 SQLite 极端故障 |
| push 后不确定态 | codex P1-4 | P2 | 维持历轮 |
| consumed≠物理消费（无 git 提交/不删源文件） | codex P1-5 | P2 | 维持；本轮 sha256 自愈改善账本一致性，物理语义未变（历史登记） |
| `.dev.yml` 最小校验不全 | kimi P1-2（7935da3 轮） | P2 | 静态属实未修，随下轮补齐 |
| test-clis ANSI 列无条件 True | claude P2-CARRY-1 | P2 | **仍开放**：`integ_harness.py:108` 硬编码，未随本轮加固清单声明 |
| STATUS"47 份"计数过时 | （本报告新发现） | P3 | 实际 51 结果 + 10 申请 |

## 六、P2/P3 登记（不阻断）

R2 E2E reviewer 主仓库产出；R3 脏树 untracked/TOCTOU；R5 历史系（ACK 全量误确认、归档 git 语义、signoff 之外的人工裁定审计粒度）；K-P2-1 `input_artifacts.kind` 术语；K-P3-1 跨轮编号混用（建议按轮次前缀）；STATUS 计数勘误（上表）。

## 七、定级判定

**不予 L3 SCENARIO-VERIFIED / PG-2。**

- 正向：P1-NEW-5/7、P2-NEW-2、GOV-1 全部真实闭环；六维加固逐项动态属实（其中 Schema/parse_duration/PTY 契约系本人及 codex 历史登记项的真实清偿）；机验全绿且洁净度连续第二轮属实；治理项首次无虚报——工程成熟度显著上升
- 阻断：**P1-Q3（E9 重试轮毒化活锁，独立复现两次）**；PG-1"P0/P1 清零"差此一项
- 修复面窄（disposition 代际化单点改动 + 2 个正反例测试 + ANSI 列可选），预计一轮内闭环；若修复属实且无新 P0/P1，本人将支持授予 L3/PG-2

## 八、全量对账声明

`reviews/` 现有 **51 份结果 + 10 份申请**。f41b9da 轮 4 份（claude 357 行 REJECT / codex 188 REJECT / grok 106 支持 / qwen 79 REJECT）已如实入库；kimi 未参加该轮（STATUS 如实登记）。本报告为本轮（bf5ae2d）第 1 份。STATUS"47 份"计数需更正为 51。

## Reviewer 自审记录

- 上轮"修复完备性反例"方法继续生效并直接命中 P1-Q3：对每个"强制 X"类修复主动构造修复后仍可绕过/无法到达正常终态的路径；本轮对 P1-NEW-6 补充了"修复后半程"推演（重派发之后共识能否达成）
- 一次本人脚本计数 bug（len(fetchall()) 数行数）产生过 1 个假 FAIL，已通过单独复跑定位并排除——该假象未进入任何结论
- GOV-1 涉及本人报告被冒名（利益相关）：仅陈述 git rename 证据与 STATUS 登记现状
- 分歧逐项举证（§五），未以专家数量代替证据；codex 历史三项 P1 维持 P2 定级并附理由
- 未覆盖：真实远端 push、真实 LLM 评审质量、Windows
