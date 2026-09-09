# MACAO 检查点防伪加固、执行者接线闭环与全适配器验收准则透传（`bdc177e` / Round 5）独立复审结论

- **评审日期**：2026-09-09
- **评审人**：claude（独立评审；不采信申请自述、不采信 `STATUS.md` 定级句；无同轮既有 codex/grok/pi-qwen 报告可交叉核对——本报告为本轮独立复现的第一手结论）
- **评审对象**：[`docs/reviews/2026-09-09-review-request-bdc177e.md`](2026-09-09-review-request-bdc177e.md)
- **受审提交**：`bdc177eaaff577e119093e686f2164bcc133f781`（申请文档自称的完整 SHA 与 `git rev-parse bdc177e` 结果**逐字符一致**，见 §一）
- **合并审计范围**：`e06d44c..bdc177e`
- **工作区 HEAD**：`3cb887b`，相对 `bdc177e` 仅追加申请文件与 `STATUS.md` 更新
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.1 §3.4、§3.5、§5.2、§8、§9
- **前序基线**：`e06d44c`（四方评审：grok YES_APPROVE / codex REJECT / claude NO_APPROVE / pi-qwen NO_APPROVE，仲裁为 REWORK）
- **目标定级**：L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3
- **机器票**：**`YES_APPROVE`**（限本轮申报范围：检查点防伪、UC-11 E1 守卫延续、执行者接线、验收准则透传；L4/PG-3 仍拒绝，见 §四）
- **证据**：`BLOCKING` × 0；`ADVISORY` × 1（P2，新发现，非阻断）；**无 P0**

**结论：授予本轮 L3 SCENARIO-VERIFIED / PG-2（限本轮申报范围）；不授予 L4 RELEASE-READY / PG-3。既有编排引擎 L3/PG-2（`4e38ed6` 轮）维持不变。**

这是我在本项目连续五轮评审中第一次投出 `YES_APPROVE`。原因很直接：我针对 Round 4 (`e06d44c`) 自己提出的三项 P1（检查点字符串前缀路径穿越、CLI 组合根从未装配执行者适配器且五个适配器字段名与编排器不一致、申请文档自身机器信封自相矛盾），本轮逐一用全新构造的独立反例重新攻击，**三项全部真实闭环**，且申请文档本身这次是自洽的（完整 SHA 真实存在、信封 sha256 与实际文件内容一致、evidence_commit 所指的文件确实存在于该提交中）。我在验证"blob 逐字节比对"这一新增硬化机制时，独立发现了一处未被申请提及、也未被官方回归覆盖的边界情形（详见 §三），但其可达面显著窄于此前四轮的历次阻断项，且申请正文对该机制的描述本身并未夸大（明确写了"当文件在对应 commit 存在时"这一前置条件），故定为非阻断的 P2。

---

## 0. Reviewer 自审

### 0.1 强制自检

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段/路径 vs 实际读取 | `orchestrator.py` 检查点路径判断已改为 `doc_path.relative_to(self.root.resolve())`（`ValueError` 捕获）与 `is_relative_to()` 双重判断，非字符串前缀比较；5 个执行者适配器统一为 `task_payload.get("acceptance_criteria") or task_payload.get("success_criteria") or []` |
| 2 | 「已完成 / 100% / 全绿」 | 170/170、`git show --check` rc=0、8 份 Schema 逐字节一致均 **VERIFIED**；Round 4 三项 P1 **均 VERIFIED 闭环**；本轮申请文档自身机器信封 **VERIFIED 自洽**（这在此前四轮中是第一次） |
| 3 | 确定性用语未标目标 | 申请对 Git blob 校验的描述明确限定"当文件在对应 commit 存在时"，未夸大为无条件保证——这是本轮相对此前几轮措辞更谨慎的一处改进 |
| 4 | YAML/JSON Schema | 8 份契约逐字节一致 **VERIFIED** |
| 5 | P1 均附路径与复放 | 无 P1；P2 已附路径与复放，见 §三 |

### 0.2 复现证据归档（按 v1.1 §3.5）

复现脚本：[`docs/reviews/evidence/2026-09-09-bdc177e-claude/probe_bdc177e_claude.py`](evidence/2026-09-09-bdc177e-claude/probe_bdc177e_claude.py)。四个探针均使用独立 `tempfile.mkdtemp()` 沙箱，对宿主仓库零写入。最后执行：2026-09-09。环境：Linux、Python 3.10+、系统 git，无网络、无真实厂商 CLI。

---

## 一、申请 §2/§3 机验独立复跑

| 声明 | 本机 | 判定 |
|---|---|---|
| 完整 SHA `bdc177eaaff577e119093e686f2164bcc133f781` | `git rev-parse bdc177e` 结果逐字符一致 | **VERIFIED**（Round 4 P1-3 同类问题本轮未重犯） |
| `PYTHONPATH=src python3 -m unittest discover tests` 170/170 | `Ran 170 tests in 58.5s … OK` | **VERIFIED** |
| `python3 -m compileall -q src tests` rc=0 | rc=0 | **VERIFIED** |
| `git show --check bdc177e...` rc=0 | rc=0，命令按申请字面文本可直接执行成功（Round 4 同类命令曾因 SHA 虚构而 fatal，本轮未重犯） | **VERIFIED** |
| 双 Schema 8 份逐字节一致 | `docs/schemas/*.schema.json` ↔ `src/macao/schemas/` 8/8 SAME | **VERIFIED** |
| 伴随机器信封 `evidence_commit: "bdc177e"` 且信封 sha256 与实际文件一致 | `git ls-tree -r bdc177e` 含该文件；`git show bdc177e:<path> \| sha256sum` 与信封声明值逐字符相同 | **VERIFIED**（Round 4 P1-3 同类自证矛盾本轮未重犯） |

---

## 二、Round 4 遗留 P1 闭环核验（本人独立复放，全新构造，非沿用旧脚本）

### 2.1 检查点路径穿越（我 Round 4 P1-1）—— CLOSED

**独立复现**（构造与上轮完全相同的"同名前缀兄弟目录"场景，针对 `bdc177e` 纯净树重新执行）：

```text
sibling_escape -> advanced=False   # 上轮为 True，本轮已拒绝
```

**根因确认**：`orchestrator.py` 现使用 `doc_path.relative_to(self.root.resolve())`（越界时抛 `ValueError` 并被捕获返回 `None`）加 `is_relative_to()` 双重判断，替换了原先的 `str(doc_path).startswith(str(self.root.resolve()))`。两种判断方式均基于真实路径层级组件比较，不再受字符串前缀巧合影响。

### 2.2 CLI 组合根未装配执行者、字段名不一致（我 Round 4 P1-2）—— CLOSED

**独立复现**：

```text
get_orchestrator(...).executor is None -> False (type=ClaudeCodeAdapter)
acceptance criterion reaches prompt sent to executor -> True
```

**根因确认**：`cli/main.py:get_orchestrator()` 现读取 `config_dict["team"]["executor"]` 并调用新增的 `LiveAgentDispatcher.get_adapter_for_executor()` 装配真实适配器实例后再传入 `Orchestrator(...)`；`Orchestrator.__init__` 亦增加了同一逻辑的自愈兜底（仅在调用方未显式传入 `executor_adapter` 且能从 `macao.yaml` 读到 `team.executor` 时触发，未引入新的静默降级）。5 个执行者适配器（`claude.py`/`codex.py`/`opencode.py`/`antigravity.py`/`kimi.py`）统一改为 `task_payload.get("acceptance_criteria") or task_payload.get("success_criteria") or []`，字段名不一致问题消除。`get_adapter_for_executor` 对未识别的 `cli_type` 返回 `None`（fail-closed，未引入新的模糊匹配后门，与 round 3 修复的未知 CLI 处置原则一致）。

### 2.3 申请文档自身机器信封自相矛盾（我 Round 4 P1-3）—— CLOSED

见 §一：完整 SHA、evidence_commit 归属、信封 sha256 三项本轮均自洽，独立验证通过。

---

## 三、P2（新发现，非阻断）：Git blob 反篡改校验对"从未提交"的证据文件静默失效

**独立复现**（在项目根目录内放一份真实存在、SHA 与信封声明完全一致，但从未 `git add`/`git commit` 过的文件）：

```text
untracked_evidence_bypass -> advanced=True
（文件真实存在于项目根目录内，磁盘 SHA 与信封一致，但从未被提交到 git；
  新增的 blob 比对逻辑因“找不到该文件在该 commit 下的 git 对象”而被整段跳过，
  仅剩磁盘哈希校验生效）
```

**对照组**（验证 blob 检查在文件确实被追踪时能正确捕获篡改，证明该机制本身逻辑正确）：

```text
tampered_tracked_file (control) -> advanced=False
（文件已提交到 git，但提交后又在磁盘上被本地修改而未重新提交；
  磁盘哈希与信封声明的哈希"一致"——因为两者都是攻击者/执行者可控的同一份被篡改内容——
  但 git 记录的原始 blob 内容不同，新增校验正确拒绝）
```

**根因**（`orchestrator.py`）：

```python
if self.git and self.git.is_git_repository():
    rel_posix = rel_doc_path.as_posix()
    code, _, _ = self.git._run("cat-file", "-e", f"{latest_commit}:{rel_posix}")
    if code == 0:
        blob_bytes = self.git.get_file_bytes_at_commit(latest_commit, rel_posix)
        if blob_bytes is not None:
            calc_blob_sha = hashlib.sha256(blob_bytes).hexdigest()
            if calc_blob_sha.lower() != str(doc_sha).lower():
                return None
```

只有 `git cat-file -e <commit>:<path>` 返回 0（即该文件在该 commit 下确实被 git 追踪）时才会进入 blob 比对分支；文件若从未被 `git add`/提交，这段代码整体被跳过，检查点退化为仅验证"磁盘文件内容的 SHA-256 与信封声明值一致"——而磁盘内容与信封声明值通常本就出自同一个执行者/同一次操作，二者一致并不能证明该内容未被篡改或伪造，只能证明"信封没有算错自己刚生成的文件的哈希"。

**定性**：这不是一处"声明与实现不符"的诚信问题——申请正文明确写"**当文件在对应 commit 存在时**，通过 `git cat-file -p` 获取提交时的树对象字节"，这个限定条件本身就是如实的。我把它定为 P2 而非 P1，理由有三：(1) 可达面比 Round 4 的字符串前缀漏洞窄得多——攻击面仅限于"项目根目录内、从未提交过的文件"，不再能引用项目外任意路径；(2) 申请描述本身没有夸大成"无条件严防篡改"；(3) 这更接近一处应当被登记为"已知简化"的设计边界，而非被违反的安全承诺。但既然本轮申请把这项能力的价值主张定位为"严防篡改"，而实际达成的只是"部分场景下的严防篡改"，仍值得在 `STATUS.md`／PRD 按 v1.1 §5.2 正式登记，避免被后续申请无意中外推为"篡改检测已 100% 覆盖"。

**建议（不阻断本轮）**：若坚持"证据文档必须可被 git 溯源验证"的设计意图，应在 blob 检查分支缺失（`code != 0`）时同样 `return None`（即要求 `full_document` 引用的文件必须已被提交，而不是允许其退化为纯磁盘校验）；或者在 `docs/reviews/STATUS.md` 的 §5.2 已知简化表中登记本项边界及其 owner/expiry。补一条"从未提交的证据文件"的官方回归测试（当前 `tests/test_p1_closures_and_regressions.py:833` 的 `test_checkpoint_git_blob_verification` 只覆盖了"已提交后被篡改"这一种情形，未覆盖"从未提交"这一种）。

---

## 四、L4 / PG-3（单独否决，沿用未闭）

本轮 diff 范围（`e06d44c..bdc177e`）未触及 `live_runner.py`。该文件仍硬编码三名 `cli: "mock-cli"` reviewer，`auto_signoff: bool = True` 默认自动签收。GUIDELINES v1.1 §7.2 的 10 行 OPS 必测矩阵本轮申请仍未提供任何一行独立证据。**L4 仍需一次真实 CLI + 真实人工接管的留档演练才可申请，与此前各轮判定一致。**

---

## 五、建议闭环顺序

1. **P2**（可延期，不阻断本轮）：blob 检查覆盖"从未提交的证据文件"这一分支，或在 `STATUS.md` §5.2 登记为已知简化并设定 expiry；补充对应回归测试。
2. **L4**：真实 CLI 至少一轮非全同意评审 + 人工 `override resolve` 实机留痕；按 v1.1 §7.2 十行矩阵逐格提供证据。

验收 P2 时请重放本报告归档脚本 [`evidence/2026-09-09-bdc177e-claude/probe_bdc177e_claude.py`](evidence/2026-09-09-bdc177e-claude/probe_bdc177e_claude.py) 的 `probe_untracked_evidence_bypass()`：期望结果从 `advanced=True` 翻转为 `advanced=False`；其余三个探针（`sibling_escape`、`tampered_tracked_file`、执行者接线两项）结果不得回归。

---

## 附：机器票与结构化 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/P2-1` | minor | `ADVISORY` | 检查点新增的 Git blob 反篡改校验对"项目根目录内但从未提交"的证据文件静默退化为仅磁盘哈希校验；申请描述本身未夸大，故非阻断 |

`vote`: `YES_APPROVE`（限本轮申报范围：检查点防伪、执行者接线、验收准则透传；L4/PG-3 另行拒绝，见 §四）
