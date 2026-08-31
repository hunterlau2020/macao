# UC-1 初始化 MACAO 项目配置（`macao init --agteam <team>`）

- **设计日期**：2026-08-31
- **设计人**：glm
- **状态**：用例设计稿（待实现；实现前须过 Schema/测试对账）
- **关联**：吸收并统一现行 `macao init`（模板写入）与 `macao setup`（探测向导）；对齐 PRD v2.4 §17 agmsg 映射、`macao_config.schema.json` 既有字段（`team.name`、`agmsg_member_id`）；回应 codex 3c5ed32 轮 P1-5（无条件覆盖配置）验收标准。
- **agmsg 集成约束**：对 agmsg 的一切读取**只经官方脚本**（`~/.agents/skills/agmsg/scripts/` 下的 `team.sh` / `history.sh` / `identities.sh` / `whoami.sh` / `join.sh`），**禁止直读 `db/`（messages.db）与 `teams/` 目录**。

---

## 1. 前置条件

| # | 条件 | 不满足时的行为 |
|---|---|---|
| P1 | 当前目录为 Git 仓库（或用户确认 `--no-git` 裸模式） | E1 |
| P2 | agmsg 已安装且 `~/.agents/skills/agmsg/scripts/` 可用 | E2 |
| P3 | `--agteam <team>` 指名的团队存在于 agmsg（`team.sh <team>` 非空） | E3 |
| P4 | 本机至少安装 1 款受支持 CLI（`probe_available_clis` 非空） | E4 |
| P5 | `macao.yaml` 不存在，或用户显式 `--force` | E5（防覆盖） |

## 2. 主成功场景（细化 a–g）

### a. 用户进入 `~/projectX`

记录 `project_root = $(pwd)`；读取 Git 上下文（分支/remote，复用 `detect_git_context`）。

### b. 用户输入 `macao init --agteam stockdb`

### c. 系统读取 agmsg 团队画像（只经脚本）

- **c1** `team.sh stockdb` → 名册 `[{name, type, project}]`（成员数 N、名称、CLI 类型）
- **c2** 对每名成员 `history.sh stockdb <name>` → 通信语料（条数、时间跨度、消息样本）
- **c3 角色启发式推断**（输出必须带置信度，仅供 d 步建议，绝不直接落盘）：

| 信号 | 推断 | 置信度 |
|---|---|---|
| 消息中高频出现 diff/commit/修复类内容；或该成员 == `whoami.sh` 当前身份（发起者本人） | Executor 候选 | 高 |
| 常收到"请审查/REVIEW/意见"类消息、回复中含评审语义 | Reviewer 候选 | 高 |
| 仅偶发闲聊/通知 | 未定 → 交用户指定 | 低 |
| 历史为空（N 条 ≈ 0） | 全部未定 → 走 d 步纯交互 | — |

### d. 系统生成交互式配置建议（名册 ∩ 本机 CLI 探测 = 可用矩阵）

- **d1 CLI↔成员绑定建议**：成员 `type` 映射 CLI（`codex→codex`、`claude-code→claude`…）；本机未装的成员标 `MISSING`，装了但不在团队的 CLI 标 `EXTRA`（可选纳入）
- **d2 角色建议**：1 名 Executor（默认 c3 最高置信者）+ ≥2 名 Reviewer（其余成员）
- **d3 模型建议**：按 CLI 给默认模型表（opencode→`Qwen3.8 max`、claude-code→`claude-3-7-sonnet`、agy→`gemini-2.0-pro`…），允许逐项改写
- **d4 输出建议表**：`成员 | agmsg_member_id | cli | adapter | 角色 | model | 置信度`，逐行 `[Y/n/编辑]`

### e. 用户逐项确认/修改

空回车 = 接受建议；支持 `--yes` 全默认跳过交互。

### f. 落盘静态配置

- **f1** 组装 `macao.yaml`：`team.name=stockdb`；executor/reviewers 各含 `agmsg_member_id`（schema 已支持；`generate_smart_config` 扩展）
- **f2** 写前 Schema 校验（`validate_config`），失败即中止不落盘
- **f3** 存在旧配置且 `--force`：先 `macao.yaml.bak.<ts>` 原子备份再写；无 `--force` → E5
- **f4** 注入 `.gitignore` 隔离（幂等，复用 `ensure_gitignore_isolation` 8 规则）
- **f5** 非交互修正：若本会话 agent 尚未加入该 agmsg 团队（`identities.sh` 无此项目记录），提示执行 `join.sh stockdb <macao> <type> "$(pwd)"`（MACAO 自身作为编排者入队，PRD §11.6 agmsg 网桥前置条件）

### g. 项目进展判定（信号按优先级）

| 判定 | 信号（任一命中即为"已开始"） | 后续动作 |
|---|---|---|
| **已开始运行** | ① `.macao/state.db` 存在且含活跃任务；② agmsg 历史含 workflow 形态消息（REVIEW_REQUEST / vote / 任务派发样本文本）；③ `.macao/archive/` 非空 | 提示运行 `macao doctor` + `macao daemon --once` 对账，**不自动改状态库** |
| **新项目** | 以上全无 | 提示下一步 `macao task create`；建议首个微任务走 `live-run` 演练 |

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | 无 `--agteam` 参数 | 退化为现行 setup 流程（本机 CLI 探测 → 默认 3 Reviewer 建议），并提示"检测到 agmsg 团队 `<available_teams>`，可用 `--agteam` 绑定"——两条入口合一 |
| A2 | 团队成员数 < 3 | 角色建议降级为"1 Executor + 全部其余为 Reviewer"，警告法定人数风险（`policy.min_effective_votes`） |
| A3 | 同一 CLI 多个成员 | 允许（靠 `agmsg_member_id` / `id` 区分席位），模型可各异（29ef7bc 起支持 per-agent model） |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 非 Git 仓库 | 询问是否裸模式；默认中止（E6 拓扑门禁 `is_ancestor` 依赖 Git） |
| E2 | agmsg 未安装 | 明示"`--agteam` 需要 agmsg"，转 A1 纯本机流程 |
| E3 | 团队不存在 | 列出 `available_teams`，允许现场 `join.sh` 新建或改选 |
| E4 | 无任何受支持 CLI | 中止并给出安装指引（不允许产出不可运行的 macao.yaml） |
| E5 | macao.yaml 已存在且无 `--force` | 拒绝覆盖（对齐现行 `init` 保护语义），提示 `--force` 备份路径 |

## 5. 后置条件

- **成功**：`macao.yaml` 通过 Schema 校验且每个成员可追溯（`agmsg_member_id` ↔ roster 名册一一对应）；`.gitignore` 含隔离规则；进展判定结果已告知用户；**零副作用于 `.macao/` 状态库**（init 只做静态配置）
- **失败**：不留半成品文件（写前校验 + 临时文件原子改名）

## 6. 验收标准（可测）

1. `--force` 备份语义 + 默认拒覆盖（正反例）
2. 建议表与 roster / CLI 探测交集一致；`MISSING` / `EXTRA` 正确标注
3. 角色启发式：构造"评审语义"历史语料 → Reviewer 建议命中；空历史 → 全交互
4. 产出 `macao.yaml` 过 `validate_config`，且 `agmsg_member_id` 与 `team.sh` 名册**双向零差集**
5. 进展判定：含 `state.db` 活跃任务 → "已开始"+doctor 提示；纯净目录 → "新项目"
6. 全程对 agmsg 仅脚本调用（代码审计断言：无 `sqlite3.connect(messages.db)`、无直读 `teams/`）

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/cli/main.py:init` | 重写，吸收 `setup`（`setup` 保留为别名一个版本期） |
| `src/macao/cli/wizard.py` | 新增三个纯函数：`load_agmsg_roster()` / `infer_roles_from_history()` / `detect_project_progress()`；history 样本 fixture 化可单测（不依赖真实 agmsg） |
| `docs/MACAO_PRD_v2.md` §17 | 补本 UC 交互序列（v2.4） |
| `tests/` | 按第 6 节验收标准逐条建测（含 E1–E5 异常分支） |

## 8. 设计自审

- c3 角色启发式为**建议器**而非决策器：所有推断须经 e 步用户确认——与本项目 fail-closed 纪律一致（拒绝把启发式结果当事实落盘）
- g 步"不自动改状态库"：init 与运行态严格分离，进展判定仅产生提示动作
- 本 UC 吸收 setup 后，codex P1-5 的两条验收标准（拒覆盖/探测驱动候选）成为 P5/E4 与 d1 的内在属性
- 遗留决策点（实现前需拍板）：①模型默认表是否独立配置文件化；②`--no-git` 裸模式是否真正支持（E6 依赖 Git，建议 v1 拒绝裸模式）
