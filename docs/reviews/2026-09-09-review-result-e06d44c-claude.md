# MACAO 检查点防伪闭环、UC-11 E1 守卫与 Provider 参数扩展（`e06d44c` / Round 4）独立复审结论

- **评审日期**：2026-09-09
- **评审人**：claude（独立评审；不采信申请自述、不采信 `STATUS.md` 定级句、不采信同轮已存在的 codex/pi-qwen 复现脚本作为结论——本报告 §一~§四写完、独立复现全部落盘后，才对照 `docs/reviews/evidence/` 下已有的两份同轮证据目录做交叉核对，见 §五）
- **评审对象**：[`docs/reviews/2026-09-09-review-request-e06d44c.md`](2026-09-09-review-request-e06d44c.md)
- **受审提交**：短 SHA `e06d44c`，实际解析为 `e06d44cb31a0dbcbe199e6bb124430e9701e087f`（申请文档自称的完整 SHA `e06d44c77c688bb715bb997a3cf556bc91f6920f` 经核实**不是本仓库中的任何 git 对象**，见 P1-3）
- **合并审计范围**：`7bc8d70..e06d44c`（含 `972e0d0`、`080720c`、`e06d44c`）
- **工作区 HEAD**：`b8d8e9e`，相对 `e06d44c` 仅追加申请文件与 `STATUS.md` 更新
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.1 §3.4、§3.5、§8、§9；`docs/usercases/UC3-dev-checkpoint.md`；`docs/usercases/UC11-scenarioc-inflight-adoption.md`
- **前序基线**：`7bc8d70`（五方评审：codex REJECT / grok NO_APPROVE / claude NO_APPROVE / qwen 不予认证 / pi-qwen NO_APPROVE，全票否决待返工）
- **目标定级**：L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3
- **机器票**：**`NO_APPROVE`**
- **证据**：`BLOCKING` × 3（P1）；L4 OPS 缺口维持；`ADVISORY` × 若干；**无 P0**

**结论：不授予本轮 L3 SCENARIO-VERIFIED / PG-2 全量认证；不授予 L4 RELEASE-READY / PG-3。既有编排引擎 L3/PG-2（`4e38ed6` 轮）维持不变。**

Round 3 我自己提出的两项 P1（检查点全零/空/缺失哈希 fail-open、`task adopt` 接受不存在 commit 且绕过 FSM）本轮**均已独立复放确认为真实闭环**——`orchestrator.py` 的检查点校验现已拒绝全部四类历史反例，`Orchestrator.adopt_task()` 现在会先执行 `git.commit_exists()` 并经 `WorkflowFSM.transition()` 正式推进。方法论 v1.1 的"参照系纪律""复现证据归档"两条新规也被认真执行（`.macao/.dev.yml` 生成、SHA 计算脚本均可复跑）。

但本轮在"堵旧洞"的同时留下三处新的、可独立复现的阻断：(1) 检查点新增的"路径必须位于项目根目录内"防护用了一个经典的字符串前缀比较漏洞，同目录名前缀的兄弟目录即可绕过；(2) CLI 唯一的组合根 `get_orchestrator()` 从未真正装配过执行者适配器，`Orchestrator.start_task()` 里"把任务派发给执行者"这整段代码在生产路径上是死码，且即便日后装配了，全部 5 个执行者适配器读取的字段名 `success_criteria` 与编排器实际发送的 `acceptance_criteria` 对不上，验收标准仍会丢失；(3) 本申请文档自身的机器信封与"完整 SHA"引用存在自相矛盾——声称的完整 SHA 不是本仓库任何 git 对象、`.dev.yml` 里 `evidence_commit: "e06d44c"` 所指的正是这份文档自己，但这份文档在 `e06d44c` 提交时根本不存在（首次出现于其后的 `b8d8e9e`），信封 sha256 也对不上文件真实内容。

---

## 0. Reviewer 自审

### 0.1 强制自检

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段/路径 vs 实际读取 | `orchestrator.py` 的路径包含检查用 `str(doc_path).startswith(str(self.root.resolve()))`——字符串前缀比较非路径层级比较；`Orchestrator.start_task()` 依赖 `self.executor`，而 `cli/main.py:get_orchestrator()` 从未传入 `executor_adapter=`；5 个执行者适配器读 `success_criteria`，编排器发送 `acceptance_criteria` |
| 2 | 「已完成 / 100% / 全绿」 | 165/165、`git show --check`（短 SHA）rc=0、8 份 Schema 逐字节一致、round 3 两项 P1 均 **VERIFIED 闭环**；申请「路径穿越防护」「验收标准全量透传」**CONTRADICTED** |
| 3 | 确定性用语未标目标 | 申请 §3.3 给出的 `git show --check <完整 SHA>` 命令若照抄执行会因该 SHA 不存在而 `fatal`，申请写的"预期结果：返回码 0"未标注前提 |
| 4 | YAML/JSON Schema | 8 份契约逐字节一致 **VERIFIED**；`macao_config.schema.json` 新增 `provider` 字段结构正确 |
| 5 | P1 均附路径与复放 | 是，均针对 `e06d44c` 纯净树独立复现，脚本归档于 [`docs/reviews/evidence/2026-09-09-e06d44c-claude/`](evidence/2026-09-09-e06d44c-claude/) |

### 0.2 复现证据归档（按 v1.1 §3.5）

复现脚本：[`docs/reviews/evidence/2026-09-09-e06d44c-claude/probe_e06d44c_claude.py`](evidence/2026-09-09-e06d44c-claude/probe_e06d44c_claude.py)。前两个探针使用独立 `tempfile.mkdtemp()` 沙箱，对宿主仓库零写入；第三个探针（应用文档自证性核查）为对已提交历史的只读 git 内省，不修改任何文件。最后执行：2026-09-09。环境：Linux、Python 3.10+、系统 git，无网络、无真实厂商 CLI。

---

## 一、申请 §3 机验独立复跑

| 声明 | 本机 | 判定 |
|---|---|---|
| `PYTHONPATH=src python3 -m unittest discover tests` 165/165 | `Ran 165 tests in 58.7s … OK` | **VERIFIED** |
| `python3 -m unittest tests/test_schema.py` 8/8 | 未单跑此文件，但全量测试已含其用例且通过；双 Schema 目录人工比对逐字节一致 | **VERIFIED** |
| `python3 -m compileall -q src tests` rc=0 | rc=0 | **VERIFIED** |
| `git show --check e06d44c77c688bb715bb997a3cf556bc91f6920f` rc=0 | 该 SHA **不是本仓库任何 git 对象**（`git cat-file -t` 报错，非 rc=0）；改用短 SHA `e06d44c` 或真实完整 SHA `e06d44cb31a0dbcbe199e6bb124430e9701e087f` 执行则 rc=0 | **CONTRADICTED**（P1-3，申请自身的命令按其字面文本无法复现声称的结果） |
| §3.4 Grok/Claude/Qwen 三方 round 3 复现脚本反向回归 | 未逐字节重放三份脚本，但本报告 §二 P1-1 已用本人独立构造的等价反例证实 round 3 两项 P1 均已真实闭环 | **PARTIALLY_VERIFIED**（本人独立复现覆盖同一结论） |
| 检查点 8 步 fail-closed（全零/空/缺失/`executor.cli` 错配） | 见 §二对照组 | **VERIFIED**（round 3 遗留项真实闭环） |
| `task adopt` UC-11 E1 守卫 | 见 §二对照组 | **VERIFIED**（round 3 遗留项真实闭环） |
| 「审查员 PTY 载荷验收标准全量透传」 | 该声明限定于 `LiveAgentDispatcher`（审查员侧），本机核实其 payload 确实新增了 `acceptance_criteria` 字段 | **VERIFIED**（仅限声明范围内）；但见 P1-2，**执行者侧**的对应链路完全断裂，申请未提及此范围差异 |
| Provider 参数扩展（`macao_config.schema.json`、`pi.py --provider`、`opencode.py -m provider/model`） | 三处均读码确认，逻辑与声明一致 | **VERIFIED** |
| Claude 会话 `cwd` 强制过滤 | `session_locator.py` 无 `cwd` 的会话记录现被 `continue` 跳过 | **VERIFIED** |

---

## 二、Round 3 遗留 P1 闭环核验（本人独立复放，非采信申请自述）

**独立复现**（每个反例使用独立 `tempfile.mkdtemp()` 项目 + 独立任务）：

```text
zero_hash             -> advanced=False  final_state=CODING   # round 3 曾 fail-open，本轮已拒绝
missing_file          -> advanced=False  final_state=CODING   # 同上
empty_sha             -> advanced=False  final_state=CODING   # 同上
wrong_cli             -> advanced=False  final_state=CODING   # 同上（executor.cli 现已参与比对）
wrong_id (control)    -> advanced=False  final_state=CODING   # 对照组：round 3 已生效，本轮维持
tampered_sha (control)-> advanced=False  final_state=CODING   # 对照组：同上
good (control)        -> advanced=True   final_state=READY_FOR_REVIEW  # happy path 未被误伤
```

```text
$ git cat-file -e deadbeef^{commit}
fatal: Not a valid object name deadbeef^{commit}

$ macao task adopt --no-review
UC-11 E1 Error: Declared review baseline commit 'deadbeef' does not exist in git
repository. Refusing to adopt in-flight state.
exit=1
```

**根因确认**：`orchestrator.py` 的 `check_development_checkpoint` 现要求 `full_document.sha256` 匹配 `^[0-9a-fA-F]{64}$` 且显式排除全零常量，文件必须 `.exists() and .is_file()` 后才计算真实 SHA-256 并比对；`executor.cli` 现与 `raw_config` 中的执行者配置精确比较。`task adopt` 已下沉为 `Orchestrator.adopt_task()`，入口处对 `checkpoint_ref` 执行 `self.git.commit_exists(...)`，不存在则在创建任何任务记录前 `raise ValueError`；状态写入已改为 `self.fsm.transition(..., trigger_id="E1_ADOPT"/"E2_ADOPT")`，`transitions.py:30/33` 已正式注册两条转移边。

**Round 3 P1-1、P1-2 均 CLOSED。**

---

## 三、P1：本轮新引入的阻断

### P1-1　检查点"路径必须位于项目根目录内"防护可被同名前缀的兄弟目录绕过

**独立复现**：

```text
computed relative path (../ escape): ../proj-evil-secrets/secret.txt
sibling_escape -> advanced=True   final_state=READY_FOR_REVIEW
(root=/tmp/xxx/proj, sibling=/tmp/xxx/proj-evil-secrets, path traversal target=/tmp/xxx/proj-evil-secrets/secret.txt)
```

**根因**（`orchestrator.py`，`e06d44c` 纯净树）：

```python
doc_path = (self.root / doc_path_str).resolve()
if not str(doc_path).startswith(str(self.root.resolve())):
    return None
```

这是经典的字符串前缀比较漏洞：`self.root` 若为 `/tmp/xxx/proj`，而 `doc_path` 解析到 `/tmp/xxx/proj-evil-secrets/secret.txt`，则 `"/tmp/xxx/proj-evil-secrets/secret.txt".startswith("/tmp/xxx/proj")` 为 **True**（因为 `"proj-evil-secrets"` 这个字符串本身以 `"proj"` 开头），但该文件物理上位于项目根目录**之外**的同级兄弟目录中，不在 `self.root` 之下。申请 §1.1 第 6 条明确写"物理文件必须真实存在、为 regular file、且**位于项目根目录内（防止路径穿越）**"——本反例构造的 `full_document.path` 为 `"../proj-evil-secrets/secret.txt"`，经此漏洞放行后，其真实 SHA-256 被正确计算并与信封声明值吻合，任务顺利推进到 `READY_FOR_REVIEW`。

**影响**：检查点的 `full_document` 是整条审查链的证据锚点（"评审对象=合并对象"不变量的起点）。这个防护本是本轮新增的第 6 项硬化措施，实际上比完全不做路径检查更危险——它给了一种"已做路径穿越防护"的虚假保证，掩盖了执行者可以引用仓库外任意可读文件作为审查依据的事实。

**验收**：改用真正的路径包含判断（如 `Path.is_relative_to()`，Python 3.9+；或 `os.path.commonpath([doc_path, self.root.resolve()]) == str(self.root.resolve())`，并额外拒绝 `doc_path == self.root.resolve()` 这种根目录本身的边界情形）。补一条"同名前缀兄弟目录"反例作为永久回归。

### P1-2　CLI 唯一组合根从未装配执行者适配器；即便装配，5 个执行者适配器的字段名与编排器不一致，验收标准仍会丢失

**独立复现（两部分）**：

```text
get_orchestrator(...).executor is None -> True
```

```text
acceptance criterion reaches prompt sent to executor -> False
(prompt: 'TASK: do the thing\nAcceptance Criteria: {}\nWhen finished, create .macao/.dev.yml manifest.')
```

**根因（第一部分）**：`cli/main.py` 的 `get_orchestrator()`——被 `task create`、`task checkpoint`、`task adopt`、`merge`、`override resolve` 等**全部** CLI 子命令共用的唯一组合根——只构造 `Orchestrator(project_root=project_root, config=config_dict)`，从不传 `executor_adapter=`。`Orchestrator.__init__` 中 `self.executor = executor_adapter` 因此在生产路径上恒为 `None`。`start_task()`：

```python
if self.executor:
    self.executor.start()
    self.executor.inject_task({...})
```

这段代码是生产环境下的**死码**——不是"验收标准透传给执行者的方式不对"，而是"执行者从未被启动、任务描述与验收标准从未被发送给任何执行者进程"。这与本轮申请 §1 第 3 条"审查员 PTY 载荷验收标准全量透传"字面不矛盾（那条声明限定于 `LiveAgentDispatcher`，即**审查员**侧，且经我核实确实成立），但申请通篇未提及**执行者**侧这条更基础的链路完全未接线——多轮以来反复被讨论的"验收标准是否送达"问题，实际上上游还有一个从未被任何一轮申请提及的更严重缺口。

**根因（第二部分，即便第一部分被修复后仍会独立成立）**：`orchestrator.py:start_task()` 发送的 payload 键名是 `"acceptance_criteria"`；`src/macao/adapter/{claude,codex,opencode,antigravity,kimi}.py` 的 `inject_task()` 全部读取 `task_payload.get("success_criteria", {})`——五个文件统一使用了与发送方不一致的字段名，读取结果恒为默认空字典 `{}`，用户显式传入的验收标准字符串永远不会出现在发给执行者的 prompt 中。

**验收**：`get_orchestrator()`（或其调用方）需要根据 `macao.yaml` 的 `team.executor` 配置真正构造并传入对应的执行者适配器实例；补一条"CLI 组合根产出的 Orchestrator 实例 `.executor is not None`"的集成测试。同时统一 `acceptance_criteria`/`success_criteria` 两侧字段名（建议五个 adapter 侧改为读 `acceptance_criteria`，与 schema/`vote_result.json` 等其余产物的既有命名一致）；补一条"验收标准字符串出现在实际发送给执行者的 prompt 文本中"的回归测试，覆盖全部 5 个执行者适配器。

### P1-3　申请文档自身的机器信封与"完整 SHA"引用自相矛盾

**独立复现**（对已提交历史的只读 git 内省，无写入）：

```text
short SHA e06d44c resolves to -> e06d44cb31a0dbcbe199e6bb124430e9701e087f
application-claimed full SHA  -> e06d44c77c688bb715bb997a3cf556bc91f6920f (exists_as_git_object=False)
'docs/reviews/2026-09-09-review-request-e06d44c.md' present inside commit e06d44c -> False
document first added in commit -> b8d8e9e7769e62cf0e25a4b29510e4399f25ccf9
envelope-claimed sha256 -> d599dca03ec19592bb519b8a7b3f4a7bf6fb5f48d39e9163435f4d40fd246222
actual on-disk sha256   -> e13b9bdf0741e354b9e3ac2eeb2c7dadddf05ef8827c24972cd5d2d6e4a2b695 (match=False)
```

三处独立矛盾：
1. 申请标题行「完整 SHA：`e06d44c77c688bb715bb997a3cf556bc91f6920f`」——这个 40 位十六进制字符串**不是本仓库中的任何 git 对象**（`git cat-file -t` 报错）。真实完整 SHA 是 `e06d44cb31a0dbcbe199e6bb124430e9701e087f`（第 8 位后分叉：`c77c68` vs `cb31a0`）。申请 §3.3 给出的验收命令 `git show --check e06d44c77c688bb715bb997a3cf556bc91f6920f` 若按字面执行会 `fatal`，而非申请所写的"预期结果：返回码 0"。
2. 附带机器信封 `full_document.evidence_commit: "e06d44c"`——即声称"这份文档本身在提交 `e06d44c` 时就已存在并可被引用为证据"。但 `git ls-tree -r e06d44c` 中不含这份文件；它实际首次出现于**其后**的 `b8d8e9e`。一份文档不可能是早于自己被创建的提交的"证据"。
3. 信封 `sha256: "d599dca0…"` 与文件当前真实内容的 SHA-256（`e13b9bdf…`）不符。

**定性**：这不是代码缺陷，是本轮申请文档自身违反了 GUIDELINES v1.1 §9"确定性表述纪律"与本项目历经四轮才建立起来的"检查点必须逐字节对账证据"这条核心原则——而这条原则恰恰是本轮申请正文声称已经在代码层"彻底闭环"的能力（P1-1 所述的 8 步 fail-closed 检查）。申请文档本应是最先落实该纪律的地方。

**验收**：申请文档的机器信封只应引用其自身已提交、可被 `git cat-file` 验证存在的版本；若信封在正文提交时尚未产生真实 commit（先写文档、后提交），应显式标注为 `EXAMPLE`/`DRAFT`（GUIDELINES v1.1 §9 已允许此类占位符标注方式），不得以确定性语气声称"已由主执行席位签署并逐字节对账"。

---

## 四、L4 / PG-3（单独否决，沿用未闭）

`live_runner.py` 本轮未被触及（`git diff --stat 7bc8d70 e06d44c` 无此文件）：三名 reviewer 仍硬编码 `cli: "mock-cli"`，`auto_signoff: bool = True` 默认自动签收。GUIDELINES v1.1 §7.2 的 10 行 OPS 必测矩阵本轮申请仍未提供任何一行独立证据。**即使 P1-1～P1-3 全部修复，L4 仍需一次真实 CLI + 真实人工接管的留档演练才可申请。**

---

## 五、交叉核对（codex / pi-qwen 已归档的证据脚本）

写完 §一~§四并落盘本人复现脚本后，我查看了 `docs/reviews/evidence/2026-09-09-e06d44c-{codex,pi-qwen}/` 目录下已经存在的复现脚本（尚无对应的 `review-result-*.md` 报告文件可供交叉核对结论文字，仅脚本本身）：

- **与 codex**：其 `reproduce_checkpoint_sibling_escape.py` 采用与我几乎相同的构造手法（`repo.with_name(repo.name + "-sibling")`）复现同一个字符串前缀路径穿越漏洞——**独立同结论**，非转述。其 `reproduce_executor_acceptance_loss.py` 同样验证了 `get_orchestrator(...).executor is None` 与全部 5 个执行者适配器的字段名不匹配问题，与我的 P1-2 **独立同结论**。
- **与 pi-qwen**：其 `README.md`（G05）记录了与我 P1-3 完全一致的三项发现（完整 SHA 不存在、文档不在其自称的 evidence_commit 内、信封 sha256 不匹配），且额外指出首版曾误用 `git rev-parse --verify`（只验证语法不验证存在性）而漏报，后自行更正——这是一次值得记录的方法论自我修正案例。其 G03 对执行者适配器字段名问题的措辞（"5/7 执行器适配器丢弃 acceptance_criteria"）比我更精确地统计了 pi/cursor 两个适配器本轮已经修复，与我 P1-2 的结论方向一致。
- 三方各自独立、使用不同技术路径收敛到同一组事实，未见任何一方转述另一方，这是本轮定级判断的有力支撑。

---

## 六、建议闭环顺序与验收标准

1. **P1-1**：`orchestrator.py` 的路径包含判断改为 `Path.is_relative_to()` 或等价的层级比较，补同名前缀兄弟目录反例回归。
2. **P1-2**：`get_orchestrator()` 装配真实执行者适配器；统一 `acceptance_criteria`/`success_criteria` 字段名；补"组合根产出的 Orchestrator 已装配执行者"与"验收标准出现在执行者 prompt 中"两类回归，覆盖全部 5 个适配器。
3. **P1-3**：下一份申请文档的机器信封只引用真实存在的已提交版本，或显式标注 `EXAMPLE`。
4. **L4**：真实 CLI 至少一轮非全同意评审 + 人工 `override resolve` 实机留痕；按 v1.1 §7.2 十行矩阵逐格提供证据。

验收时请重放本报告归档脚本 [`evidence/2026-09-09-e06d44c-claude/probe_e06d44c_claude.py`](evidence/2026-09-09-e06d44c-claude/probe_e06d44c_claude.py)：`sibling_escape` 需翻转为 `advanced=False`；`get_orchestrator(...).executor is None` 需翻转为 `False`；执行者 prompt 需包含验收标准字符串；应用文档自证性核查三项需全部一致。

---

## 附：机器票与结构化 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/P1-1` | critical | `BLOCKING` | 检查点"项目根目录内"路径防护为字符串前缀比较，可被同名前缀兄弟目录绕过 |
| `claude/P1-2` | critical | `BLOCKING` | CLI 唯一组合根从未装配执行者适配器（生产路径死码）；5 个执行者适配器字段名与编排器不一致，验收标准永久丢失 |
| `claude/P1-3` | major | `BLOCKING` | 申请文档自身机器信封与"完整 SHA"引用自相矛盾：声称的完整 SHA 非本仓库对象、文档不在其自称的 evidence_commit 内、信封 sha256 与实际内容不符 |

`vote`: `NO_APPROVE`
