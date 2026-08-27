# MACAO 整体技术框架评审（技术选型 / 代码组织 / 代码质量）

- 评审日期：2026-08-27
- 被评审 commit：`23dfad5`（含 PRD v2.3.1 与 Phase 0/1 专家复审 P0/P1 整改后的最新状态）
- 性质：不是 PRD 对齐/门禁定级评审，是一次独立的工程质量审查，覆盖用户提出的三个问题。评审方式：通读 `src/macao/` 全部 24 个模块 + `pyproject.toml` + `tests/`，并对可疑处编写独立复现脚本实测（不满足于读代码猜测行为）。
- **结论**：技术选型本身基本合理，代码组织的分层设计是清楚的，但存在一个贯穿全局的模式——**测试覆盖的路径是干净的，测试没有覆盖的路径（CLI 命令的真实调用链、Adapter 的 `preflight()`、`macao.yaml` 的加载与消费）几乎全部是坏的**。其中最严重的一组问题是配置系统事实上完全不生效：`macao init` 生成的文件连自己的 Schema 都过不了，`ConfigManager` 里两个安全关键属性读的是不存在的路径，`Orchestrator` 从不加载 `macao.yaml`，且默认配置把 PRD 明确要求的安全默认值反过来了。这些都是可复现的、不是风格问题。

---

## 一、技术选型

### 1.1 基本判断：选型整体合理，符合"单机 PoC"定位

| 选型 | 评价 |
|---|---|
| SQLite（WAL 模式）作为 State Store | 合适。单进程、单机场景下 WAL 提供足够的并发读写安全性，`storage/db.py` 正确设置了 `PRAGMA journal_mode=WAL` 与 `foreign_keys=ON`，比自制文件锁方案更可靠。 |
| PTY（`pty.openpty` + `os.killpg`）包装第三方 CLI | 合适，是目前"以最小侵入方式接管无头/交互式 CLI 输出"的标准手段；`pty_session.py` 的 SIGTERM→等待→SIGKILL 两段式回收进程组符合 PRD §12.6，实现规范。 |
| Click + Rich 作为 CLI 框架 | 合适，Python CLI 生态的标准组合，`prompt_toolkit` 留作可选依赖也是合理的克制（当前用不到交互式补全）。 |
| JSON Schema (Draft-07) + jsonschema 库做产物契约校验 | 合适，与 `docs/schemas/` 的既有设计一脉相承，`core/schema.py` 用单例缓存全部 Schema 避免重复加载，思路正确。 |
| YAML 作为 `.dev.yml`/`.review.yml`/`macao.yaml` 格式 | 合适，符合可读性优先的 PoC 定位；全部读取都用 `yaml.safe_load`（未见 `yaml.load` 不安全用法），这一点做得对。 |

### 1.2 值得指出的选型/依赖问题（非阻断，但应清理）

- **`pyproject.toml` 把 `pytest` 声明为 `dev` 依赖，但全部 9 个测试文件都是标准库 `unittest`**（`grep "import pytest\|@pytest"` 在 `tests/` 下零命中）。要么是选型决策未落地（原计划用 pytest 后来改用 unittest 忘记改依赖），要么是预留了未来的迁移但目前是死依赖。建议要么迁移测试到 pytest 定义清楚，要么直接删掉这个依赖声明。
- **`orchestrator.py` 顶部 `import logging`，但全文件没有任何 `logging.getLogger(...)` 或 `logger.xxx(...)` 调用**——是唯一 import 了 `logging` 模块的文件，却完全没有使用；同时全项目也没有统一的日志基础设施（错误处理普遍用 `console.print` 直接输出到终端，或者静默 `except Exception: pass`）。对于一个定位为"审计友好、可追溯"的编排系统而言，缺少结构化日志（而不是只有 SQLite 里的 `audit_events` 表）是一个选型空白，值得在后续阶段补上（哪怕只是标准库 `logging` 配合文件 handler）。
- **`subprocess.run(ci_gate_command, shell=True, ...)` 已在本轮修复为 `shlex.split` + 非 shell 调用**（`merge/controller.py`），这是好的选型修正，避免了 CI gate 命令注入风险，值得肯定。

---

## 二、代码组织结构

### 2.1 基本判断：分层清楚，模块边界总体合理

```
core/      纯类型与配置/Schema 校验（无状态、无 I/O 副作用为主）
storage/   SQLite 持久化（db 连接、CRUD、崩溃恢复）
msg/       AEP 信封与消息总线
adapter/   三方 CLI 适配器 + PTY 会话 + Mock 适配器
consensus/ 仲裁算法与 vote_result 生成
workflow/  状态识别、转移表、FSM 驱动、Orchestrator 编排
merge/     合并流水线
utils/     Git 操作、ANSI 清洗、Context 构建
cli/       Click 命令入口 + Rich 渲染
```

这是一个合理的六边形/分层结构，`workflow.orchestrator.Orchestrator` 作为唯一的"中央装配点"依赖注入其余各层（`store`/`msg_bus`/`fsm`/`vote_aggregator`/`merge_controller`/`git`），依赖方向没有反转，符合 PRD §11.1 的单进程事件循环设想。这一点是做对的。

### 2.2 结构性问题一：`ConfigManager` 是一座孤岛，从未被 `Orchestrator`/CLI 真正接入

`core/config.py` 定义了 `ConfigManager`，`docs/MACAO_PRD_v2.md` §13 也明确称 `macao.yaml` 是"单一事实源"。但实测：

- `cli/main.py` 的 `task_create`、`override_resolve`、`merge_approve` 等命令构造 `Orchestrator(project_root=".")` 时**从不传入配置**，也从不调用 `ConfigManager.load()`；
- `Orchestrator.__init__` 因此总是落到硬编码的默认字典：`{"max_rework_rounds": 3, "min_effective_votes": 2, "ci_gate_command": None, "require_signoff": False}`；
- 也就是说，无论 `macao.yaml` 里怎么配置 `merge.require_human_signoff`、`merge.ci_gate_command`、`policy.max_rework_rounds`，实际运行时**统统不生效**，`ConfigManager` 目前只在 `cli doctor` 命令里被调用来"验证一下能不能解析"，验证完之后数据就被丢弃，不会被用来驱动任何行为。

这是一个组织结构问题而不是简单的 bug：`ConfigManager` 和 `Orchestrator` 之间缺一条依赖注入的路径，导致一整层（配置层）名存实亡。建议：`cli/main.py` 的每个命令在构造 `Orchestrator` 前先 `ConfigManager.load_config()`，把得到的字典转换成 `Orchestrator(config=...)`。

### 2.3 结构性问题二：同名类型在两个模块里各定义一份，字段还不一样

`core/types.py` 定义了一个 `CapabilityManifest`（字段：`agent_id, cli_name, version, execution_mode, can_execute, can_review, supports_worktree, supports_hook, allowed_flags`），`adapter/base.py` **又独立定义了一个同名的 `CapabilityManifest`**（字段：`can_execute, can_review, supports_hook, supports_noninteractive, supports_worktree, execution_mode, supported_os, cli_version_range`）——两者字段集合不同、构造方式不兼容。当前所有四个 Adapter（`claude.py`/`codex.py`/`kimi.py`/`mock.py`）统一从 `adapter.base` 导入使用，`core.types` 里那份目前是未被任何人使用的"孤儿定义"，但只要有新代码不小心 `from macao.core.types import CapabilityManifest`，就会拿到一个字段完全不同、无法与现有 Adapter 互操作的类。

同理，`core/types.py` 用 `MessageType = AEPType` 保留了一个"向后兼容别名"——但这是一个尚未发布、没有外部消费者的内部项目，不存在需要兼容的历史调用方，这类别名只会增加以后"两个名字该用哪个"的认知负担，建议直接统一成 `AEPType` 并删除别名（`msg/envelope.py`、`msg/bus.py` 两处的 import 已经在 `MessageType`/`AEPType` 之间不统一使用，见下节）。

### 2.4 结构性问题三：core/types 里的类型改了字段，但四个 Adapter 与它的老定义仍在用旧字段名（见下节代码质量 3.1，是本轮最严重的具体 bug，根因是组织问题——类型定义与消费方分属不同模块，缺少集中的编译期/类型检查兜底）

---

## 三、代码实现质量

### 3.1（严重）`PreflightCheckResult` 字段已改名，但四个 Adapter 的 `preflight()` 全部还在用旧字段名——一调用就崩

`core/types.py` 当前定义：

```python
@dataclass
class PreflightCheckResult:
    agent_id: str
    installed: bool
    version: Optional[str] = None
    execution_mode: Optional[ExecutionMode] = None
    error: Optional[str] = None
```

但 `adapter/claude.py`、`adapter/codex.py`、`adapter/kimi.py`、`adapter/mock.py` 的 `preflight()` 无一例外仍在用旧字段构造它：`cli_name=...`、`auth_valid=...`、`in_matrix=...`、`details=...`、`remediation=...`——这些字段在当前 dataclass 里根本不存在。**独立复现**：

```python
>>> MockAgentAdapter('cc-glm', 'codex', role='reviewer').preflight()
TypeError: PreflightCheckResult.__init__() got an unexpected keyword argument 'cli_name'
```

四个 Adapter 无一例外全部会在调用 `.preflight()` 时崩溃。这是 Adapter Contract（PRD §12.1）7 个抽象方法之一，且是"部署上线前第一步必须调的方法"，但完全没有测试覆盖（`grep preflight tests/` 零命中），所以在 22/24 测试全绿的情况下完全没有暴露。

### 3.2（严重）`macao preflight` CLI 命令是完全硬编码的假数据，不调用任何 Adapter

`cli/main.py` 的 `preflight` 命令：

```python
probes = [
    {"agent": "Environment: Git", "installed": True, "version": "2.43.0", ...},
    {"agent": "Claude Code CLI", "installed": True, "version": "0.2.29 (Hook/PTY capable)", ...},
    ...
]
render_preflight_table(probes)
console.print("✓ Preflight checks passed successfully...")
```

无论机器上是否真的装了这些 CLI，`macao preflight` 永远打印"全部安装成功"。这不只是"没接线"，而是直接返回了看起来权威、实际上完全虚构的诊断信息——PRD §14.1 把 `preflight` 列为"从零到第一次合并"的第一步，用户会依赖它的输出判断环境是否就绪，当前实现会系统性地给出假阳性。

### 3.3（严重）`macao init` 生成的配置文件通不过自己的 Schema 校验——用户的第一条命令就是坏的

`cli/main.py` 的 `init` 命令生成的模板使用顶层键 `agents` / `consensus` / `orchestration`；而 `docs/schemas/macao_config.schema.json`（`ConfigManager.load()` 据此校验）要求的顶层键是 `project` / `team` / `policy` / `merge`。**独立复现**（用 Click 的 `CliRunner` 实测 `macao init` → `macao doctor` 真实调用链）：

```
$ macao init                     # exit_code 0，看起来成功
$ macao doctor  ->  ConfigManager.load_config("macao.yaml")
ValueError: Invalid macao.yaml schema: 'team' is a required property
```

PRD §14.1 描述的用户旅程第一步是 `preflight → init → doctor`；照做的用户在第二步就会看到自己的配置文件被判定非法，而这份文件正是上一步命令自己生成的。这是当前实现里最直接影响"能不能跑通最基本流程"的 bug。

### 3.4（严重）`ConfigManager` 里两个安全关键属性读的是不存在的路径，永远返回硬编码默认值

```python
@property
def require_human_signoff(self) -> bool:
    policy = self.data.get("policy", {})
    merge_policy = policy.get("merge_policy", {})          # 实际路径是顶层 merge.*，不是 policy.merge_policy.*
    return merge_policy.get("require_human_signoff", True)  # 永远拿不到真实值，只会返回这个 True

@property
def auto_rebase_disabled(self) -> bool:
    policy = self.data.get("policy", {})
    rebase_policy = policy.get("rebase_policy", {})         # 同样路径不存在
    return not rebase_policy.get("allow_clean_rebase", False)
```

而仓库根目录实际的 `macao.yaml`（符合 Schema 的那份）把这两个值放在顶层 `merge.require_human_signoff` / `merge.rebase_before_merge`。**独立复现**：无论 `macao.yaml` 里这两个值写成什么，这两个属性读到的永远是各自 `.get(..., 默认值)` 里写死的那个默认值——当前测出来"恰好"是 `True`/`True`，纯属默认值与文件真实值巧合相同，并不是真的读到了文件内容（可以把 `macao.yaml` 里的 `require_human_signoff` 改成 `false` 验证：这两个属性依然会返回 `True`/`disabled=True`，不会变化）。

这两个属性恰好对应 PRD 里被四轮评审反复强调、明确写为"刻意的保守安全默认值"的两个开关，是整个系统里"防止自动化误合并"的关键防线,但当前实现让它们形同虚设：不是因为默认值选错了，而是因为读配置这件事本身没有真正发生。

### 3.5（中）`Orchestrator` 的默认 `require_signoff` 是 `False`，与 PRD 的安全默认值方向相反

```python
self.config = config or {
    "max_rework_rounds": 3,
    "min_effective_votes": 2,
    "ci_gate_command": None,
    "require_signoff": False    # PRD 明确要求默认 true
}
```

结合 3.4：因为 `ConfigManager` 从未被接入（2.2），且这里的默认值本身就设反了，`cli/main.py` 里任何不显式传 config 构造 `Orchestrator` 的命令（目前全部命令都是这样调用的），实际生效的行为是"默认不需要人工签字就能合并"——正好是 PRD 三轮评审、五份独立报告反复确认要防止的那个结果。这不是某个属性读错路径的孤立问题，是 3.2/3.3/3.4/3.5 一整条链路共同造成的：`macao.yaml` 里怎么配置这个开关，从文件到 `ConfigManager` 到 `Orchestrator` 的每一环都断开了，最终生效的是一个方向相反的硬编码默认值。

### 3.6（低，代码卫生）值得顺手清理的点

- `core/schema.py` 的 `_load_all_schemas()` 用 `except Exception: pass` 静默吞掉 Schema 加载失败——如果某个 Schema 文件损坏，不会有任何报错，只会在后续每次 `validate()` 调用时收到"Schema not found"这个误导性信息，建议至少 log 一条 warning。
- `storage/db.py` 的 `connection()` 每次调用都新开一条 SQLite 连接、用完即关，而不是复用一条长连接或连接池——对当前单机单进程 PoC 规模没有实际影响，但如果后续任务量上升会有可观的连接建立开销，值得留意但不阻断。
- `git_utils.py` 的 `get_changed_files()` 在 `git diff` 无输出或失败时返回硬编码的兜底 `[{"path": "src/main.py", "status": "modified"}]`——这是一个容易误导排查的"假数据兜底"，与 3.2 是同一类反模式（用看起来合理的假数据代替明确的失败信号），建议改成返回空列表并让调用方感知"未取到 diff"这一事实。

---

## 四、优先级汇总

| 编号 | 级别 | 发现 | 影响 |
|---|---|---|---|
| 3.3 | **P0** | `macao init` 生成的配置文件无法通过自身 Schema 校验 | 用户第一条命令即失败，PRD 用户旅程第一步不可用 |
| 3.1 | **P0** | 四个 Adapter 的 `preflight()` 因字段名不匹配必然抛 `TypeError` | Adapter Contract 核心方法完全不可用，且无测试覆盖 |
| 3.4 + 3.5 | **P0**（合并计） | `require_human_signoff`/`rebase` 配置读取路径错误 + `Orchestrator` 默认值方向与 PRD 相反 + `ConfigManager` 从未接入 | 安全关键开关整体失效，实际运行时默认"无需人工签字即可合并" |
| 3.2 | **P1** | `macao preflight` 命令完全是硬编码假数据 | 用户会依据虚假的"环境就绪"提示做出错误判断 |
| 2.2 | **P1** | `ConfigManager` 未与 `Orchestrator`/CLI 打通 | 配置系统整体名存实亡（是 3.4/3.5 的根因） |
| 2.3 | **P2** | `CapabilityManifest` 在两个模块重复定义且字段不兼容 | 当前无实际影响，是未来误用的隐患 |
| 1.2/3.6 | **P3** | pytest 死依赖、orchestrator.py 未用的 logging import、静默吞异常、假兜底数据 | 代码卫生问题，不影响功能 |

## 五、建议的处理顺序

1. 先修 3.1（四个 Adapter 的 `PreflightCheckResult` 构造）——最小改动，逐个把旧字段名换成 `agent_id/installed/version/execution_mode/error`；
2. 修 3.3（统一 `macao init` 模板与 `macao_config.schema.json`，建议让 `init` 直接从 Schema/示例文件生成，避免模板与 Schema 各写一份而失步）；
3. 打通 2.2（`ConfigManager` → `Orchestrator` 的依赖注入路径），随后顺带修 3.4（改正两个属性的真实路径）与 3.5（默认值改回 PRD 要求的方向）——这三者是同一条链路，建议一次性解决并补一条"从 macao.yaml 加载后 `require_human_signoff` 确实生效"的回归测试，这类测试目前完全空白；
4. 修 3.2，把 `preflight` 命令接回真实 Adapter 调用；
5. 2.3/1.2/3.6 可在下一轮顺手清理，不阻断功能。

## Reviewer 自审记录

方法：不满足于"22/24 测试全绿"这一表面信号，专门去读测试覆盖没有触达的路径（CLI 命令的真实调用链、`preflight()`、配置加载）——这正是前几轮 P0/P1 集中出现的区域，提示这个项目当前的风险分布规律是"被测试覆盖的核心状态机路径质量很高，被测试忽略的边缘路径（尤其是 CLI 入口与配置系统）系统性地存在断裂"。对每一个怀疑点都编写了独立最小复现脚本实际执行，而不是仅凭读代码下结论。未覆盖 `msg/bus.py`/`cli/ui.py` 之外的极小工具文件的逐行审查，但已抽样确认无同类问题。
