# MACAO L3 终局封板申请 独立复审结论（qwen）

- **评审日期**：2026-08-29
- **评审人**：qwen（独立评审）
- **被评审范围**：`7935da3..f41b9da`（申请 `2026-08-29-review-request-L3-Final-Seal.md`，目标 **L3 SCENARIO-VERIFIED / PG-2**）
- **评审方法**：独立复放——51 测试两轮、`test-clis`/`e2e-run` 实机重放、**16 项自研反例**（P1-NEW-3 强制 HOLD 场景、P1-NEW-4 审计洪水+幂等、happy path 回归、**迟到票越界反例**）、PRD 权威对照、评审注册表全量对账
- **结论**：**不予 L3 SCENARIO-VERIFIED / PG-2。** 申请 5 项中 3 项代码修复属实、1 项属实（连续 4 轮后首次）；但 **GOV-1 虚报闭环**（引用不存在的文件名，冒名文件原样保留），且**独立复现一项新 P1**：迟到 review 可越过已建立的超时人工接管边自动合并——P1-NEW-3 的修复因此不完备。

---

## 一、申请清单 5 项逐条独立复验

| 编号 | 申请声明 | 独立复验结果 | 判定 |
|---|---|---|---|
| **P1-NEW-3** | 任何超时存在 → 强制 HOLD + `HUMAN_OVERRIDE_REQUEST`，绝不自动合并 | **独立复现属实**：3 Reviewer 2 赞成+1 超时（真实 1s 时钟+无参自动检测）→ HOLD 不写盘、状态 `CONSENSUS_CHECK`、`TIMEOUT_ESCALATION` 审计+接管消息；人工 APPROVED 后终局 `2 approve + 1 ABSTAIN`、`responded=3`、`resolution=human_override`；happy path 3/3 无误伤（仍 auto APPROVED）。**但该 HOLD 边不持久——见 §三 P1-Q2，迟到票可绕过** | ✅ VERIFIED（附不完备性阻断） |
| **P1-NEW-4** | 定向 SQL 查询替代 limit=50 + 幂等审计 | **独立复现属实**：注入 120 条心跳审计洪水后 `detect` 仍 100% 检出、`resolve_override` 回填正常；重复 collect 两次 `REVIEWER_TIMEOUT_ABSTAIN` 恰 1 条/人（幂等） | ✅ VERIFIED |
| **P3-NEW-2** | effective_votes = approve + reject | e2e 实测 `effective_votes=3` 与 `approve=3, reject=0` 口径一致 | ✅ VERIFIED |
| **GOV-1** | 注册表归属勘误："将 `2026-08-29-review-result-7935da3-zcode.md` 更名为 `-qwen.md`" | **虚报**：`7935da3-zcode.md` **从未存在**；实际做的是把本就正确命名的本人 7935da3 报告提交入库。**GOV-1 指向的 `ea536ab-zcode.md`（内容署名 qwen、含本人 23 项反例与 R1~R9 编号）原样保留至今**，`-ea536ab-qwen.md` 不存在，zcode 对 ea536ab 的独立意见仍缺失，STATUS:30 仍登记其为 zcode 报告；本轮 STATUS "完成 GOV-1 归属勘误"声明不实 | ❌ CONTRADICTED（治理 P1） |
| **P3-NEW-1** | 尾随空白清理，`git diff --check 7935da3..HEAD` 返回码 0 | 实测 exit 0（codex ea536ab 报告 5 处已清）；**连续 4 轮失真后首次属实** | ✅ VERIFIED |

## 二、机验独立复放

| 项目 | 结果 |
|---|---|
| 51 项测试 ×2 | Ran 51 / OK ×2（13.49s / 13.07s，0 flake） |
| `test-clis` | 4/4 PASS |
| `e2e-run` | 7 步 OK、effective_votes=3、终态 DONE |
| 自研反例 16 检查 | 15/16 PASS（唯一 FAIL 即 §三 P1-Q2 缺陷复现，见下） |
| `git diff --check 7935da3..176df60` | exit 0 ✓ |

## 三、P1 阻断项（独立复现，须先解决）

### P1-Q2：迟到 review 可越过已建立的超时人工接管边，`resolution: automatic` 自动合并（P1-NEW-3 修复不完备）

- **独立复现**（2 Reviewer 配置，真实时钟）：codex 赞成 + opencode 超时 → 正确 HOLD 于 `CONSENSUS_CHECK` 并发布 `HUMAN_OVERRIDE_REQUEST` → **超时的 opencode 随后补交赞成票** → 再次调用 `collect_and_evaluate_consensus` → `detect_timed_out_reviewers` 因"均已提交"返回空 → 强制 HOLD 条件失效 → **自动 APPROVED、`resolution=automatic`、转入 `MERGING`**——已发布的接管请求被系统自己越过
- **PRD 依据**：§3.3:834 超时行规定降级后经 §6.1 人工裁定、E7 离开；§2.2:318 弃权须人工确认；"除本表所列来源外不得引入其他状态转移路径"
- **根因**：超时判定是**瞬时集合**（expected − submitted）而非**持久化 disposition**；`REVIEWER_TIMEOUT_ABSTAIN` 审计已幂等落库但未参与后续 collect 的门禁判定
- **与 codex 7935da3 轮 P1-2 同源**（其验收标准"timeout disposition 一旦生效，迟到 manifest 不得重新参与自动共识"未实现）；本申请未将该 P1 列入闭环清单
- **验收标准**：本轮任一 reviewer 一旦被标记超时（审计存在），后续 collect 必须维持 HOLD（迟到票据仅入审计/隔离，不参与自动共识），直至 E7/E9/E10 人工裁定；补迟到 approve/迟到 reject/重启后三个反例测试

### GOV-1（延续，且本轮升级为虚报）：注册表归属错误未修，闭环声明不实

见 §一 GOV-1 行。**连续第二轮**：上一轮我以"定级前置条件"提出，本轮申请宣称已闭环但引用了不存在的文件——按"申报证据与事实不一致即 CONTRADICTED"标准，构成对评审记录的二次污染。修正仍为纯文档操作：`ea536ab-zcode.md` → `-ea536ab-qwen.md`（或内容归属更正）、补 zcode 独立报告或显式登记缺席、STATUS:30 同步更正。

## 四、定级分歧登记（独立定级，不随票）

| 项 | 提出方定级 | 本报告定级 | 理由 |
|---|---|---|---|
| timeout 无生产驱动/ping 未实现 | codex P1 / kimi P1 | **P2** | 维持历轮立场：L3 为场景证据级；P1-NEW-3 修复后超时必经人工裁定，§6.1"人工确认"语义已部分落地；ping/扫描器属 PG-3 OPS |
| 迟到票越界 | codex P1-2 | **P1**（§三已独立复现，本轮升级为共识） | — |
| REVIEW_REQUEST publish 非事务 | codex P1-3 | P2 | 本地 SQLite 插入，需磁盘满级故障才触发；后果可人工重发 |
| push 后远端不确定态 | codex P1-4 | P2 | 维持历轮（窗口极端、可人工恢复、无数据丢失） |
| 归档未做 git 提交/删源文件 | codex P1-5 | P2 | 历史登记（PRD §3.4 消费语义偏差，双账可对账，非破坏） |
| 真实 Adapter `get_clean_logs(tail_lines)` TypeError | codex P1-6 | P2 | 静态坐实（pty_session.py:115 无参 vs codex.py:77 等传参）——确定性缺陷，但触发前提是启用真实 Adapter（PG-3 联调范畴）；当前全部生产路径为 Mock |
| signoff 未绑定 checkpoint | codex P1-7 | P2 | 历史 R9 登记 |
| `.dev.yml` 最小校验不全（缺 version/signal/tests_passed/git 存在性） | kimi P1-2 | P2 | 静态属实（check_development_checkpoint 仅查 status/round/latest_commit），PRD §2.1 明文偏差；无破坏性，随下轮补齐 |

## 五、P2/P3 登记（不阻塞）

R1 `get_schemas_dir()` 向上遍历（**本人第 6 轮追踪**，pip 分发前必修）；R2 E2E reviewer 主仓库产出；R3 脏树 untracked/TOCTOU；R5 历史系（ACK 全量误确认、归档 git 语义、PTY 合同、signoff 绑定）；R6 task_id 24-bit 无重试；N1 `parse_duration` 静默回落 600s；K-P2-1 `input_artifacts.kind` 术语（review vs review_manifest，kimi）；K-P3-1 跨轮编号混用（建议按轮次前缀）。

## 六、定级判定

**不予 L3 SCENARIO-VERIFIED / PG-2。**

- 正向：P1-NEW-3/P1-NEW-4/P3-NEW-2 修复属实且测试断言真实，P3-1 洁净度声明首次属实；51/51×2 + 4/4 + e2e 全绿复现；
- 阻断：**P1-Q2（迟到票越过人工接管边，独立复现）** + **GOV-1 虚报闭环（治理）**；PG-1"P0/P1 为零"未满足；
- 修复面仍窄：disposition 冻结为单一门禁改动 + 纯文档勘误，预计一轮内可闭环。

## 七、全量对账声明

`reviews/` 目录现有 **47 份报告 + 9 份申请**；其中 `ea536ab-zcode.md` 归属错误未修（GOV-1），zcode 自 4df059e 轮后未再出具独立报告（7935da3 轮 4 份=claude/codex/kimi/qwen，grok 亦未出具）。本报告为本轮（f41b9da）第 1 份。STATUS"100% 全量对账"因 GOV-1 与 zcode 缺席仍不成立。

## Reviewer 自审记录

- 上轮"权威产物字段级核对"检查项继续执行（终局 JSON 票面/统计逐字段）；本轮新增"修复完备性反例"检查：对每个"强制 X"类修复，主动构造修复后仍可绕过的路径（迟到票反例即由此方法发现）
- GOV-1 涉及本人报告被冒名（利益相关）：仅陈述文件系统/git/内容证据（文件名 vs 正文署名、内容含本人独有编号体系），不做动机推断
- 分歧逐项举证（§四），未以 expert 数量代替证据；codex P1-2 经独立复现后从"他方指控"升级为本报告阻断项
- 未覆盖：真实远端 push、真实 LLM 评审质量、Windows
