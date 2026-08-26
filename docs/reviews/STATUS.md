# MACAO 文档门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。

- 更新时间：2026-08-26（v2.2 修订后）
- 最近复审对象：commit `684a012`（PRD v2.1），三份独立评审：
  - `reviews/2026-08-26-review-result-684a012-codex.md`：上轮 P0 全关，核心实质对齐；余下 5 个 P1
  - `reviews/2026-08-26-review-result-684a012-claude.md`：新发现 2 个 P0（F1 CI Gate 状态矛盾、F2 Reviewer 执行权限边界）+ F3~F9
  - `reviews/2026-08-26-review-result-684a012-gemini.md`：7 大工程环节增量
- 当前等级：**PENDING_REVIEW**
  - 说明：此前本文件曾依据 gemini 单方结论标记"已达成 L1 DOC-ALIGNED"，但 claude 复审发现的 2 个 P0 与 codex 的 P1 清单表明该结论过早，现予撤回；
    待下方各项经下一次独立复审确认后再行定级。
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

## 下一步

1. 对 PRD v2.2 申请下一轮独立复审（重点复核 MERGING 转移边、execution_mode 约束、schemas 一致性）；
2. 四场景 SIM 复核扩展为五场景（增加"CI gate 失败 → E4b 返工"场景）；
3. 复审通过后定级 L1 DOC-ALIGNED / PG-0。
