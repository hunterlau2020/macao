# UC-10 既有项目接入与诊断（`macao doctor` / `preflight`）

- **设计日期**：2026-09-01
- **设计人**：glm
- **状态**：用例设计稿（待实现；实现前须过 Schema/测试对账）
- **关联**：PRD v2.4 §14.1 第 1–2 步、§14.2、§20（Wizard 与运行时隔离）；FAQ Q8/Q9/Q11；UC-1（init 吸收 setup）；`preflight`/`doctor`（cli/main.py）、`ensure_gitignore_isolation`。
- **边界声明**：**零侵入**：不自动改既有任务 FSM、不迁移既有分支策略、不动用户代码；一切修复动作显式列出并经确认。诊断是**只读报告 + 建议命令**，不是自动修复器（FAQ Q9：配置文件不记运行态，运行态在 State Store）。

---

## 1. 前置条件

| # | 条件 | 不满足时的行为 |
|---|---|---|
| P1 | 处于已存在 Git 项目目录（非 MACAO 沙箱） | E1 |
| P2 | `macao.yaml` 存在（接入完成态）或走接入流（§2a） | A1 |

## 2. 主成功场景

### a. 接入既有项目（FAQ Q8 路径）

a1 `macao init`（UC-1 全流程：CLI 探测 → 团队绑定 → `macao.yaml` + `.gitignore` 隔离）；a2 g/h 步按 UC-1 做进展判定：已有 `.macao/` 或 agmsg 痕迹 → **可疑已开始**，FSM 推不出唯一 10 态则**问管理员**（UC-1 h5，禁止猜态、禁止伪造历史任务）；a3 纯净目录 → 全员 `IDLE`，正常起步。

### b. 诊断总检（`macao doctor`）

分组只读检查，逐项 ✅/⚠️/❌ + 建议命令：

| 组 | 检查项 |
|---|---|
| 配置 | `macao.yaml` Schema、`vote_weight` 独裁帽、`min_effective_votes` 与席位数匹配、timeout 合法 |
| 环境 | Git 仓库/分支拓扑（source/target 存在、ff 可行）、`state.db` 可写、表结构版本 |
| 隔离 | `.gitignore` 9 条规则齐备（差量列出缺失项）、无泄漏的 `.macao/worktrees/*`、无残留锁文件 |
| 席位 | `agent_registry` 与 macao.yaml 双向零差集、agmsg 入队状态（`identities.sh`） |
| 适配器 | 各席位 `dispatchable`（preflight + capabilities + §12.2 矩阵） |
| 产物 | 未归档 `.review.yml`/`.dev.yml` 的 STALE/孤儿标记；归档目录 sha256 抽查 |

### c. 探活预检（`macao preflight`）

各 CLI 安装/版本/登录态/权限模式矩阵（Preflight Report）；版本超出支持矩阵 → 告警并要求显式确认（PRD §14.4）；通信组件（agmsg 脚本可用性）就绪检查。

### d. 对账提示

发现"DB 有活跃任务但产物/席位不一致" → 提示 `macao daemon --once` 触发一次扫描对账（产物型触发是正规路径），**doctor 不自行转移状态**。

### e. 修复动作（全部显式）

| 问题 | 建议（用户确认后执行） |
|---|---|
| `.gitignore` 缺规则 | `macao init --force` 或直接 `ensure_gitignore_isolation` 幂等注入 |
| 孤儿 worktree | 列出路径 + `prune` 建议命令；**不自动删**（先展示内含未归档产物则强制人工） |
| 席位未入队 | `join.sh <team> <name> <type> "$(pwd)"` |
| CLI 版本越界 | 指示支持矩阵与降级选项（临时标记弃权走 UC-9，PRD §14.4） |
| state.db 表版本旧 | 迁移预览（dry-run diff）→ 确认后 `CREATE TABLE IF NOT EXISTS` 增量迁移；失败回滚 |

### f. 报告落盘

诊断报告写 `docs/reviews/<yyyy-MM-dd>-doctor-<slug>.md`（留痕目录同评审件，FAQ Q16）；终端只打印摘要 + 报告路径。

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | 未 init 直接 `doctor` | 走 §2a 接入建议；不产出半配置 |
| A2 | 沙箱/演练目录（`macao_live_run_*`） | 识别并标注"演练现场"，跳过席位入队检查 |
| A3 | 既有项目已有 CI/分支保护 | 提示共享仓库边界（PRD §14.5：MVP 面向本地/个人仓库），建议 v1.1 门禁方案 |
| A4 | `--fix` 非交互模式 | 仅执行**幂等且无破坏**类修复（gitignore 注入、DB 增量迁移 dry-run 落盘）；删除类动作必须交互确认 |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 非 Git 仓库 | 接入中止（UC-1 E1 同源）；诊断仅报配置组 |
| E2 | `state.db` 损坏/版本不可迁 | 报告 ❌ + 备份指引（`.bak` 后重建）；**不自动删库** |
| E3 | agmsg 缺失 | 席位组降级为 ⚠️（单机模式可运行，通知能力受限）；给出安装指引 |
| E4 | 诊断中途异常 | 已完成分组照常输出（分段容错）；异常组标 ❌ + stderr；退出码非 0 |

## 5. 后置条件

- **成功**：用户得到分组诊断报告 + 逐项建议命令；确认执行的修复全部幂等可重入；零 FSM 副作用（除非用户在 UC-1 h5 显式确认写态）。
- **失败**：报告仍落盘（含失败分组）；不留下半修复状态（迁移事务回滚）。

## 6. 验收标准（可测）

1. fixture 矩阵：缺 gitignore 规则、席位差集、CLI 越界、孤儿 worktree、STALE 产物 → 各自 ⚠️/❌ + 正确建议命令
2. 幂等：连续两次 doctor + 修复 → 第二次全 ✅；gitignore 注入与 UC-1/P2-R-1 逐行差量语义一致
3. 零侵入断言：doctor 路径无 `update_task_state`、无 worktree 删除、无 AEP 投递（单测 + 代码审计）
4. 可疑已开始项目：构造 tasks 态与产物矛盾 → 走 UC-1 h5 问管理员，不猜态（A6 场景复用）
5. 报告命名落 `docs/reviews/`；`--fix` 不执行删除类动作（A4）

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/cli/main.py` | `doctor` 命令（分组检查器）、preflight 增席位/通信组 |
| `src/macao/cli/wizard.py` | 复用 `ensure_gitignore_isolation`；新增 `check_state_db_consistency()` |
| `tests/` | 第 6 节 |

## 8. 设计自审

- 零侵入是硬边界：诊断可以"建议一切"，执行只限幂等无破坏类（A4 白名单）
- 与 UC-1 的分工：init 负责"接入 + 首次观测"，doctor 负责"持续体检"；两者共用 g/h 判定与 h5 问管理员路径，不实现第二套 FSM 猜测逻辑
- 遗留决策点：①孤儿 worktree 内未归档产物的保全流程；②doctor 报告保留策略（是否入 90 天滚动，建议长期保留）
