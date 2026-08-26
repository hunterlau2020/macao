# MACAO 文档门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。

- 更新时间：2026-08-26（PRD v2.2 复审后）
- 最近复审对象：commit `8ab9be7`（PRD v2.2），一份独立评审：
  - `reviews/2026-08-26-review-result-8ab9be7-kimi.md`：v2.2 关闭上一轮全部 P0/P1，但发现 1 个新 P0（PRD 内部 `review_context` 结构矛盾）+ 5 个 P1（摘要文档示例与 Schema 不符、改进总结无证据 ✅）+ P2/P3
- 当前等级：**PENDING_REVIEW**
  - 说明：v2.2 已关闭 `684a012` 的全部 P0/P1，但新一轮复审在权威基准 PRD 内部发现核心 Context 契约不自洽，且两份摘要文档的示例/状态标记与 Schema/事实不符；L1 DOC-ALIGNED 待 P0/P1 关闭后再行定级。
- 本轮修订：PRD **v2.2**（含 `docs/schemas/`、`docs/README.md` 新增）

## 针对 684a012 三份评审的处理状态

| 来源 | 编号 | 发现 | 状态 | 处理位置 |
|------|------|------|------|---------|
| claude | F1 (P0) | E4 即达 DONE 与 Merge Policy 的 CI gate 时序矛盾 | 已修订 | PRD §3.3 新增 `MERGING` 中间态（E4/E4a/E4b）；§14.5 重写为合并流水线；§3.4 推演同步 |
| claude | F2 (P0) | Reviewer 执行权限边界未定义 | 已修订 | PRD §12.2 `execution_mode` 强制规则、§12.3 准入矩阵补列、§5.3 worktree 注入、§15.3 风险表 |
| codex | P1-1 | repository 路径两种写法并存 | 已修订 | 统一为 `review_context.repository`（PRD §2.4 注 / §5.2 注） |
| codex | P1-2 | Task 缺 Schema/branch 字段；merge 配置段未定义 | 已修订 | PRD §14.2 Task 最小 Schema、Type A 增 task_id/source/target_branch、§13 merge 段 |
| codex | P1-3 | 双写缺恢复算法 | 已修订 | PRD §11.4 DDL + §11.5 写入顺序与三场景 Reconcile 规则 |
| codex | P1-4 | 缺版本化 Schema 与 fixtures | 已修订 | 新增 `docs/schemas/`（5 个 Schema + 正反 fixtures，已通过 jsonschema 校验） |
| codex | P1-5 | STATUS 同时声明"未达 L1"与"当前 PG-0" | 已修订 | 本文件改为 PENDING_REVIEW 单一表述 |
| codex | P2/P3 | checkin 未定义 / v2.0 叙事标题 / min_effective_votes 推导 | 已修订 | 命令更名 `macao checkpoint create` 并入命令表；标题类留待下轮整理；Loader 推导规则见 PRD §13 |
| claude | F3 (P1) | 无合并前人工签字开关 | 已修订 | `merge.require_human_signoff: true` 默认保守值（PRD §13/§14.5 第 4 步） |
| claude | F4 (P1) | 与 GitHub/GitLab 分支保护关系空白 | 已修订 | PRD §14.5 尾注：MVP 假设未启用分支保护的本地仓库，共享仓库集成 v1.1+ |
| claude | F5 (P1) | .review.yml 格式错误无同轮重试 | 已修订 | PRD §12.5 两级输出自愈（Extractor + 局部 Re-prompt，限 1 次） |
| claude | F6 (P1) | 崩溃恢复算法缺失 | 已修订 | 同 codex P1-3（§11.4/11.5） |
| claude | F7 (P1) | 缺非确定性 E2E 测试策略 | 已修订 | PRD §12.4 fixture 回放 + §15.5 评测计划；完整 E2E 策略随 PoC 报告补充 |
| gemini | 环节1 (P1) | PTY 权限弹窗/ANSI/孤儿进程 | 已修订 | PRD §12.6 PTY 运行规范 |
| gemini | 环节2 (P1) | 多 Reviewer 工作区并发冲突 | 已修订 | PRD §5.3 worktree 注入机制 + §12.3 强制列 |
| gemini | 环节3 (P1) | SQLite DDL 与 Reconcile 缺失 | 已修订 | 同 codex P1-3 |
| gemini | 环节4 (P2) | YAML 输出自愈 | 已修订 | 同 claude F5（§12.5） |
| gemini | 环节5 (P2) | Pre-merge rebase 策略缺失 | 已修订 | PRD §14.5 第 1 步（rebase 不触发复审的边界已写明） |
| gemini | 环节6 (P2) | agmsg 物理形态与 DLQ | 已修订 | PRD §11.6 |
| gemini | 环节7 (P3) | usage 估算兜底；docs/README 为空 | 已修订 | PRD §15.4 estimated 标记；新增 `docs/README.md` 索引 |

## 针对 8ab9be7 评审的处理状态

| 来源 | 编号 | 发现 | 状态 | 处理位置 |
|------|------|------|------|---------|
| kimi | P0-1 | PRD 内部 `review_context` 结构矛盾：§2.4 Type B 与 §5.2 字段命名/嵌套结构/缺省块不一致 | **待修订** | 需统一 `review_context` 权威结构，全文同步并新增/更新 Schema |
| kimi | P1-1 | `EXECUTIVE_SUMMARY.md` `.dev.yml` 示例字段名与 Schema 不符（`coverage` vs `test_coverage`）且缺 `review_round` | **待修订** | `docs/EXECUTIVE_SUMMARY.md` 第 124–151 行 |
| kimi | P1-2 | `EXECUTIVE_SUMMARY.md` `vote_result.json` 示例缺必需字段且 `next_step` 类型不符 | **待修订** | `docs/EXECUTIVE_SUMMARY.md` 第 180–190 行 |
| kimi | P1-3 | `EXECUTIVE_SUMMARY.md` `.review.yml` 示例缺必需字段且 `feedback` 结构不符 | **待修订** | `docs/EXECUTIVE_SUMMARY.md` 第 157–174 行 |
| kimi | P1-4 | `IMPROVEMENT_SUMMARY.md` 多处用 ✅ 标记未完成的未来目标 | **待修订** | `docs/IMPROVEMENT_SUMMARY.md` 第 334–339、399–404、479–483 行 |
| kimi | P1-5 | `IMPROVEMENT_SUMMARY.md` `quality_snapshot.tests.passed` 为含 emoji 字符串而非整数 | **待修订** | `docs/IMPROVEMENT_SUMMARY.md` 第 188–193 行 |
| kimi | P2-1 | 缺少 `review_context` 与 AEP payload 级 Schema | 可延期 | 待新增 `docs/schemas/` 文件 |
| kimi | P2-2 | 部分 Schema 对嵌套结构约束不足（`next_step`/`summary`/`artifacts`/`feedback`） | 可延期 | 待细化对应 Schema |
| kimi | P2-3 | `EXECUTIVE_SUMMARY.md` 对 `.review.yml` 路径表述笼统 | 可延期 | 第 25 行附近补充路径说明 |
| kimi | P3-1 | `IMPROVEMENT_SUMMARY.md` 标题仍以 v2.0 为叙事 | 可延期 | 文件名/标题可注明 "截至 v2.2" |

## 下一步

1. 关闭 P0-1：在 PRD 内选定 `review_context` 唯一权威结构，统一 §2.4 Type B 与 §5.2 的字段命名、嵌套路径与缺省块；
2. 关闭 P1-1/1-2/1-3：重写 `EXECUTIVE_SUMMARY.md` 三处示例，使其通过对应 Schema（`dev_manifest`/`review_manifest`/`vote_result`）；
3. 关闭 P1-4/1-5：修正 `IMPROVEMENT_SUMMARY.md` 的 ✅ 状态标记与 `quality_snapshot` 字段类型；
4. 对修复后的 PRD v2.2 申请下一轮独立复审（重点复核 `review_context` 一致性、摘要文档示例、schemas 完整性）；
5. 四场景 SIM 复核扩展为五场景（增加"CI gate 失败 → E4b 返工"场景）；
6. 复审通过后定级 L1 DOC-ALIGNED / PG-0。
