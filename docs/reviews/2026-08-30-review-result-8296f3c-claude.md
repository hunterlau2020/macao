# MACAO 独立评审结果 — `8296f3c`（claude）

- **评审人**：claude
- **评审日期**：2026-08-30
- **评审对象**：`docs/reviews/2026-08-30-review-request-L3-PG2-Unanimous-Seal.md`
- **实际评审范围**：`3ea5256..8296f3c`（申请书写作 `3ea5256..HEAD`；`HEAD` 是移动引用，本报告钉死为 `8296f3c`，见 P3-NEW-10）
- **依据基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0、`docs/schemas/*.schema.json`
- **申请定级**：L3 SCENARIO-VERIFIED / PG-2

## 结论

> **授予 L3 SCENARIO-VERIFIED；授予 Process Gate 1；授予 Process Gate 2。**
> **不授予 L4 / PG-3**（不在本次申请范围，且缺 §3.3 要求的 OPS 证据与用户手册）。

这是我评审本项目八轮以来第一次给出授予结论，理由如下：

1. **申请清单 2 项全部 VERIFIED**。我上一轮提出的唯一阻断项 P1-NEW-12（E6 返工回路不校验「新 commit」）已彻底闭环，我用四分支、跨三轮的独立场景验证，包括仓库单测未覆盖的「回退到已消费 commit」分支。
2. **P0/P1 存量为零**。我把八轮以来自己提出的全部阻断项逐一回归，无一复发；本轮新发现的问题（P2-NEW-6）与遗留项均为 P2/P3。按 §2.2，PG-1 的「P0/P1 为零」条件成立。
3. **§2.1 列举的六类 L3 场景全部具备可复现证据**，且其中五类是我用生产路径（而非仓库单测路径）自行重放的（§2）。
4. **PG-2 的两项附加条件成立**：六份 Schema 自 `403ddc7`（2026-08-27）起 **42 个 commit、8 轮评审未变更**，`core/types.py` 自 `4df059e` 起 5 轮未变更，接口稳定；消费方场景测试由 `macao test-clis`（4 款真实 CLI 的 PTY 生命周期）与 `macao e2e-run`（全链路 + 5 份产物与 SQLite 账本双向核对）共同承担。
5. **5 项机验声明加注册表对账全部由我独立重跑，全部属实**；注册表 66/66 + 14/14 双向零差集。

同时我必须明确指出：**P2-NEW-6 应在任何下游团队实际接入之前修复。** PG-2 的语义是「允许下游模块/团队依赖该规范」，而 MACAO 目前会把自身运行态（含 `state.db` 与三个嵌套 git worktree）暴露在被评审仓库里且不做 `.gitignore` 处理，接入方按常规 `git add -A` 就会把这些东西提交进被评审的 commit。它不满足 P1 的判定标准（不产生错误的状态转移、不导致未评审对象被合并），我按 P2 处置；但读者若把 PG-2 的「可被依赖」理解为包含开箱可用性，主张 P1 也是有依据的。我把判断依据完整写在 §3.1，供委员会自行取舍。

---

## §0 本次评审的自查与方法声明

1. 全部结论由我在 `3ea5256..8296f3c` 上独立重新推导；不采信申请书表述，也不采信目录中其他 reviewer 的结论。
2. **本轮我特别防范了一种属于我自己的偏差**：连续七轮给出「不予授予」之后，继续挑出一个理由维持否决，比如实给出授予更省事、也更不容易被追责。为避免这种锚定，我这轮反过来做：先把授予 L3/PG-2 所需的每一项条件列成清单，逐条找**反证**；找不到反证才算通过。§2 的六类场景、§1.3 的接口稳定性、§1.2 的机验，都是按这个方式核的。
3. 对 P1-NEW-12 我**不复用**仓库新增的 2 分支单测，自建 4 分支场景（无改动重交 / 新 commit / 回退到已消费 commit / 再次新 commit），并让流程真实跑满三轮返工。
4. 我另做了三项**未发现问题**的反向核查，如实记录以免读者误以为未查：
   - **弃权是否会被静默计票**（PRD §2.2:318 / §6.1:1152）：2 赞成 + 1 超时、30 次轮询，`vote_result.json` 始终未落盘、`HUMAN_OVERRIDE` 事件为 0、状态稳定 HOLD；人工裁定后 ABSTAIN 票据才随终局票面落盘。**符合规范**。
   - **合并流水线是否仍然 fail-closed**：`merge/controller.py:48-61`（签字绑定 `checkpoint_ref`）、`:82`（`merge --ff-only`）、`:87-101`（CI gate 失败原子回滚）、`:107-113`（push 前 `HEAD == full_checkpoint_ref` 硬校验）、`:129-140`（push 后远端 SHA 复核）五道闸全部在位。**符合 §14.5**。
   - **新增的「已消费」校验是否误伤正常路径**：`register_artifact` 落 `consumed=0`，`fsm.py` 只在 `trigger_id == "E2"` 时归档 `.dev.yml` 并置 `consumed=1`，与 PRD §3.4:858「E2 触发时标记 consumed」一致；因此首次检查点与崩溃后重入均不会被误拒，`e2e-run` 与 65/65 单测亦全绿。**无误伤**。

---

## §1 申请清单逐项核验

### 1.1 整改项

| 编号 | 申请书主张 | 我的独立核验 | 状态 |
|---|---|---|---|
| **P1-NEW-12**（Claude）/ **P1-1**（Codex） | `REWORK` 下强校验 `latest_commit != checkpoint_ref`；并拒绝已作为 `consumed=1` 的 `dev_manifest` 出现过的 commit | 落点属实：`orchestrator.py:238-241`（返工新鲜度闸）与 `:243-249`（已消费闸）。四分支实测全部正确（§2.1），且返工回路在连续三轮、三个真实 commit 上仍然畅通，未出现过度收紧。两条 PRD 规则（§3.3 E6:839「新 commit」、§2.1:216「未被消费过」）现已分别落地。 | **VERIFIED** |
| **P2-1**（Codex） | `E9` 源状态收敛为 `CONSENSUS_CHECK` | 落点属实：`transitions.py:48-51`。八状态矩阵实测仅 `CONSENSUS_CHECK` 为 `True`。**但该收敛引入了一处表内不一致**，见 P3-NEW-13——不影响当前运行时行为，故不阻断。 | **VERIFIED（附 P3-NEW-13）** |

### 1.2 机验声明（全部由我独立重跑）

| 申请书声明 | 我的实测 | 状态 |
|---|---|---|
| 全量单测 65 项 | `Ran 65 tests in 16.276s / OK`，RC=0 | **VERIFIED** |
| 5 轮连续回归 325 次，0 flake | `Run 1..5 PASS`（5 × 65 = 325） | **VERIFIED** |
| `macao test-clis` 4/4，0 僵尸 | claude 2.1.251 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22 全 `PASS`、全 `✓ DEAD (0 Zombie)`，RC=0。ANSI 列的证据强度见 P2-CARRY-1 | **VERIFIED（ANSI 列除外）** |
| `macao e2e-run` 7/7、DONE、5 份产物哈希一致 | `final_state=DONE`、`decision=APPROVED`、`merge_exact_match=True`。另以固定工作目录重跑并直查 SQLite：`artifacts` 恰 5 行，**违反 `consumed=1` / `sha256` 64 位 / 归档文件物理存在 三不变式的行数 = 0**；`ARTIFACT_ARCHIVED` 审计 6 行 | **VERIFIED** |
| `compileall -q src && git diff --check` → RC 0 | `compileall` RC=0；`git diff --check 3ea5256..8296f3c` RC=0；工作区 RC=0 | **VERIFIED** |
| 注册表 66 份结果 + 14 份申请，与目录 100% 对账 | `git ls-tree -r HEAD docs/reviews` 计得 **66** / **14**；STATUS 注册表引用的文件名与 HEAD 受控文件**双向零差集**；`git status --short docs/reviews` 为空 | **VERIFIED** |

### 1.3 PG-2 附加条件（申请书未主张，由我主动核验）

| 条件 | 证据 | 状态 |
|---|---|---|
| **接口稳定** | `docs/schemas/` 下六份 Schema 中，五份（`dev_manifest` / `review_manifest` / `vote_result` / `aep_envelope` / `macao_config`）最后一次变更为 `403ddc7`（2026-08-27），`review_context` 更早（`ec9d841`，2026-08-26）；即**最近一次任何 Schema 变更就是 `403ddc7`**，此后历经 42 个 commit、8 轮评审零变更；`src/macao/core/types.py` 最后一次变更为 `4df059e`，此后 5 轮零变更 | **VERIFIED** |
| **消费方场景测试** | `macao test-clis`：4 款真实 Agent CLI 的 PTY 拉起 / 日志清洗 / 强杀回收全链路，0 孤儿 0 僵尸；`macao e2e-run`：Adapter 契约驱动的全流程，5 份物理产物与 SQLite 账本双向核对，`merge_exact_match=True` | **VERIFIED** |

---

## §2 L3 六类场景的证据核对

§2.1 要求 L3 达成「全同意 / 1:1 僵局 / 超时 / 弃权 / 崩溃恢复 / 返工循环等场景均有可复现推演或测试证据」。逐条列出我**亲自重放**的证据（非引用仓库单测）：

| 场景 | 我的验证方式与结果 | 状态 |
|---|---|---|
| 全同意 | `e2e-run` 全链路 `DONE`；另在自建 3-Reviewer 环境中全票赞成 → `MERGING` → `APPROVED / automatic / approve=3` | **VERIFIED** |
| 1:1 僵局 | 2-Reviewer 一赞成一反对 → `decision=None`、**不写** `vote_result.json`、稳定 HOLD 于 `CONSENSUS_CHECK` | **VERIFIED** |
| 超时 | `per_reviewer` 真实过期触发生产侧 `detect_timed_out_reviewers()`；超时处置按派发代际绑定，E9 重试后如期票正常计入（`LATE_REVIEW_ISOLATED=0`），重试再超时则稳定 HOLD | **VERIFIED** |
| 弃权 | 30 次轮询无人工裁定 → 无票面落盘、`HUMAN_OVERRIDE=0`；人工裁定后 ABSTAIN 票据才随终局 `vote_result.json` 落盘（`approve=2 / abstain=1`），符合 §2.2:318 与 §6.1:1152 | **VERIFIED** |
| 崩溃恢复 | E9 重试后活跃目录无残留 `vote_result.json`；第二代际僵局 HOLD 经崩溃重建后状态保持 `CONSENSUS_CHECK`，`CRASH_RECONCILE` 无动作 | **VERIFIED** |
| 返工循环 | §2.1 四分支 + 连续三轮三个真实 commit（见下） | **VERIFIED** |

### 2.1 返工回路四分支实测（P1-NEW-12 闭环证据）

```text
round1: REWORK_REQUIRED | state: REWORK | round: 2 | ref: 31937b2b
A. REWORK + IDENTICAL commit            -> accepted: False | state: REWORK             (期望拒绝)
B. REWORK + NEW commit                  -> accepted: True  | state: READY_FOR_REVIEW   (期望接受)
round2: REWORK_REQUIRED | state: REWORK | round: 3
C. REWORK + revert to consumed commit A -> accepted: False | state: REWORK             (期望拒绝)
D. REWORK + third NEW commit            -> accepted: True  | state: READY_FOR_REVIEW   (期望接受)
commits in repo: 3
```

A 分支即我上一轮的原始复现（当时 `accepted: True` 并一路走到 `MERGING`），现已正确拦截；C 分支是仓库单测未覆盖的「回退到已消费 commit」路径，`:243-249` 的已消费闸正确生效；B/D 证明收紧没有误伤正常返工。

---

## §3 本轮发现

### P2-NEW-6（新增，非本轮引入）：MACAO 把自身运行态留在被评审仓库内且不做 `.gitignore` 处理

`GitManager.create_isolated_worktree` 把 Reviewer 隔离工作区建在 `<repo>/.macao/worktrees/<reviewer>/<task>/r<n>`（与 PRD:499 的示例一致），`StateStore` 的 `state.db`、`.dev.yml`、`.reviews/`、`vote_result.json`、`archive/` 也都在 `<repo>/.macao/` 之下。而 `macao init`（`cli/main.py:175`）只生成 `macao.yaml`，**全仓库除 `e2e_runner.py:46-47` 为自己的沙箱写过一次之外，没有任何代码写入或维护 `.gitignore`**。

实测（`macao init` → 建任务 → 正常派发 → 模拟 Executor 的常规提交动作）：

```text
macao init rc: 0
files after init: ['a.txt', 'macao.yaml']
.gitignore exists after init: False

git status --porcelain after a normal dispatch:
    ?? .macao/
    ?? macao.yaml

`git add -A` stderr:
    warning: adding embedded git repository: .macao/worktrees/antigravity/task-.../r1
    hint: You've added another git repository inside your current repository.

staged paths that are MACAO's own runtime state:
    .macao/.dev.yml
    .macao/archive/58c45d9f.../r1/.dev.yml
    .macao/state.db
    .macao/worktrees/antigravity/task-.../r1
    .macao/worktrees/codex/task-.../r1
    .macao/worktrees/opencode/task-.../r1
```

**危害**：Executor 是一个自主 CLI Agent，`git add -A && git commit` 是它最常见的收尾动作。一旦发生：

1. MACAO 的审计数据库 `state.db`、本轮 `.dev.yml` 与归档目录被提交进**正是要被评审和合并的那个 commit**；
2. 三个 Reviewer worktree 被以 gitlink（mode 160000）方式登记，等价于三个指向不存在仓库的伪 submodule，一旦合并到 `main`，任何克隆者都会拿到坏引用；
3. Reviewer 拿到的 diff 被 MACAO 自身噪声污染，评审信噪比下降。

**为何定 P2 而非 P1**：它不产生错误的状态转移，不导致未评审对象被合并，`checkpoint_ref` 与合并对象仍然逐位一致（§14.5-1:1537 的哈希链不变式未被破坏）——被污染的是内容，不是链路。**但它确实会让首个下游接入方踩坑**，而 PG-2 的语义正是「允许下游模块/团队依赖」，因此我把它列为**授予 PG-2 之后、实际接入之前的第一优先修复项**。

**建议修复**：`macao init` 幂等地把 `.macao/` 追加进项目 `.gitignore`（已存在则跳过）；`Orchestrator` 初始化时若检测到 `.macao/` 未被忽略则告警；或更彻底地把 worktree 与 `state.db` 移出仓库（如 `~/.macao/<repo-hash>/`），仅在仓库内保留协议产物。

### P2-CARRY-1（连续第七轮）：`test-clis` 的 ANSI 校验仍非独立证据

`integ_harness.py:110` 本轮未改动。被扫描的 `clean_logs` 来自 `pty_session.py:115-119`，其内容早在 `:89`、`:96` 处被**同一个** `ANSI_ESCAPE_RE`（`strip_ansi`）清洗过，该断言检验的是正则幂等性而非清洗有效性，对任何常规 ANSI 输入结构性地不可能失败；`if clean_logs else True` 使空捕获真空通过。申请书与 STATUS.md 仍写「ANSI Strip True / ANSI 真实检测」。

该项不阻断定级（`test-clis` 的另外三列——PTY 拉起、进程强杀、0 僵尸——是真实证据，消费方场景测试的成立不依赖 ANSI 这一列），但**「ANSI 真实检测通过」这句话连续七轮超出证据范围，应在申请书与 STATUS 中降级表述或按建议改为双向断言**（保留未清洗原始缓冲，断言「原始含 ANSI ∧ 清洗后不含」）。

### P3-NEW-13（新增）：E9 收敛后转换表出现表内不一致；`UNKNOWN` 与 E8 目前是死状态/死触发

`transitions.py:48-51` 把 E9 收敛为仅 `CONSENSUS_CHECK`，但 `:43-46` 的 E7 仍允许 `UNKNOWN → {MERGING, REWORK, WAITING_REVIEW, CANCELLED}`。而 `resolve_override` 的 `choice_map` 中，`WAITING_REVIEW` 这一目标**只由 `RETRY_REVIEW`/E9 产生**：

```text
UNKNOWN -> WAITING_REVIEW via E7: True     <- 表声明合法，但无任何代码路径会发出
UNKNOWN -> WAITING_REVIEW via E9: False    <- 真实路径，现已被拦截
UNKNOWN -> MERGING / REWORK  via E7: True
UNKNOWN -> CANCELLED         via E10: True
```

即：`UNKNOWN` 态下管理员保留了最激进的选项（强制合并），却失去了最保守的选项（要求重新评审）。

**但这不构成当前的运行时缺陷**：我核查了全部源码，`AgentState.UNKNOWN` 只出现在 `transitions.py:17/38/44` 三处声明中，**没有任何代码把任务转入 `UNKNOWN`**，E8（`60min 无进展 + Layer 3 置信度 <0.7`，PRD §3.3:843）整体未实现。因此 `UNKNOWN` 是死状态、E8 是死触发，上述不一致是潜伏的，不影响本次定级。

**建议**：实现 E8 之前先统一口径——要么 E7 与 E9 同时去掉 `UNKNOWN`（严格照 PRD §3.3:840-841 的源状态列，并以 §3.3:850「除本表所列来源外，任何实现不得引入其他状态转移路径」为准），要么两者同时保留 `UNKNOWN`；不宜只收敛其中一个。

### 跨轮遗留（P3，不阻断）

- **P3-NEW-11**：`store.py:104-105` 的 `ON CONFLICT … DO UPDATE` 未变，`artifacts` 仍只保留最新代际的 `archived_path`/`sha256`；跨代际追溯依赖 `ARTIFACT_ARCHIVED` 审计表。建议在文档中明确两者口径差异。
- **P3-NEW-4**：`per_reviewer` 仍是唯一弃权判定线，PRD §1.2:128 的 `30m（10m/reviewer 触发 ping）` 两级语义仍未实现，`orchestrator.py` 全文无 `ping`。
- **P3-NEW-5**：`db.py` 仍无任何 `CREATE INDEX`。本轮 `:243-249` 又新增了一次每检查点的 `list_artifacts(task_id)` 全表扫描；当前规模无影响，长任务下建议加索引。
- **P3-NEW-9**：`tests/test_config.py` 的 `MACAO_SCHEMAS_DIR` 单测仍只断言路径解析；`SchemaValidator` 的类级单例缓存（`schema.py:36-42`）会使进程内改环境变量不再生效，扩展该单测时需一并处理。
- **P3-NEW-10**：申请书**第四次**使用移动引用（`3ea5256..HEAD`，应钉死为 `3ea5256..8296f3c`）；行号继续漂移：`orchestrator.py:237-251` 实为 `:237-249`（基本准确）；`tests:1510-1620` 实为 `:1511-1625`。`transitions.py:48-51` 准确。

---

## §4 治理观察

1. **P1-3 全量对账连续第四轮机验通过**：66/66、14/14 双向零差集，工作区无未受控评审残留。该规则自确立以来已稳定运行四轮，可视为固化成功。
2. **本轮闭环质量**：P1-NEW-12 的修法正确且完整——不只按我指出的「比较 `checkpoint_ref`」打补丁，还一并落地了我在建议中附带提到的 PRD §2.1:216「未被消费过」，并且把已消费闸放在所有入口状态（而非仅 `REWORK`）上，覆盖面超出我的建议。新增单测虽只覆盖 2 分支，但我自建的 4 分支全部通过，结论不依赖仓库单测。
3. **申请书的框架问题（第二次指出）**：本轮仍以「Qwen 支持授予、Kimi 授予、Claude 提 P1-NEW-12、Codex 提 P1-1/P2-1」的票型组织叙述。按 §8「真理不等于投票」，定级不由票数决定。本报告的授予结论与其他四方是否授予无关，只基于 §1–§2 的证据。
4. **委员会出席**：`3ea5256` 一轮 Claude / Codex / Kimi / Qwen 四方出席，Grok 缺席；zcode 最近一份真实署名报告仍停留在 `2026-08-29-review-result-4df059e-zcode.md`，此后连续七轮缺席。按 §8「沉默 ≠ 同意」，缺席方不得计入任何多数——**本次授予结论亦不得被表述为「全员一致」，除非五方各自独立出具了授予结论。**
5. **STATUS 待更新**：STATUS.md 尚未登记本轮（`8296f3c`）的任何结果报告，需按 P1-3 补齐。

---

## §5 定级判定

| 门禁 | 判定 | 依据 |
|---|---|---|
| L1 DOC-ALIGNED / PG-0 | **维持** | PRD v2.3.1 无回归 |
| L2 SPEC-CODE-ALIGNED | **维持** | 65/65 单测、5 轮 325 次零 flake、`test-clis` 4/4、`e2e-run` 7/7 与账本零违规、`compileall` 与 `git diff --check` 皆 RC=0，均经我独立复现 |
| **PG-1** | **授予** | L2 成立 + P0/P1 存量为零（八轮以来我提出的全部阻断项逐一回归无复发；本轮新发现与遗留项均为 P2/P3） |
| **L3 SCENARIO-VERIFIED** | **授予** | §2 六类场景全部具备可复现证据，其中五类由我用生产路径独立重放 |
| **PG-2** | **授予** | PG-1 + 接口稳定（六份 Schema 8 轮 42 commit 零变更）+ 消费方场景测试（`test-clis` 4/4 真实 CLI、`e2e-run` 全链路与账本双向核对） |
| L4 / PG-3 | **不授予** | 不在本次申请范围；§3.3 要求的 OPS 证据（人工接管路径实机演练）与用户手册均未提交 |

### 授予后的待办（不阻断本次定级，按优先级）

1. **P2-NEW-6**：`macao init` 幂等写入 `.gitignore`（`.macao/`），或把 worktree 与 `state.db` 移出被评审仓库。**建议在任何下游团队实际接入之前完成**——这是 PG-2「可被依赖」在工程实践上的直接前提。
2. **P2-CARRY-1**：ANSI 校验改为原始流/清洗流双向断言，或在申请书与 STATUS 中如实降级表述。
3. **P3-NEW-13**：实现 E8 之前先统一 E7/E9 对 `UNKNOWN` 的口径。
4. **其余 P3**：审计索引、台账代际口径说明、ping/30m 两级窗口、Schema 单例缓存与单测、申请书钉死 commit 与行号勘误。
5. **面向 L4/PG-3**：补人工接管路径的实机演练记录（OPS 证据）与用户手册。

---

## §6 复现命令

```bash
cd /home/debian/macao

# 机验（申请书 5 项 + 注册表，全部可复现）
PYTHONPATH=src python3 -m unittest discover tests -v                    # Ran 65 tests OK
for i in 1 2 3 4 5; do PYTHONPATH=src python3 -m unittest discover tests >/dev/null 2>&1 && echo "Run $i PASS"; done
PYTHONPATH=src python3 -m macao.cli.main test-clis
PYTHONPATH=src python3 -m macao.cli.main e2e-run
python3 -m compileall -q src && echo OK; git diff --check 3ea5256..8296f3c; echo "RC=$?"
git ls-tree -r --name-only HEAD docs/reviews | grep -c review-result    # 66
git ls-tree -r --name-only HEAD docs/reviews | grep -c review-request   # 14

# 本轮修复落点
sed -n '236,254p' src/macao/workflow/orchestrator.py    # P1-NEW-12：返工新鲜度闸 + 已消费闸
sed -n '42,51p'   src/macao/workflow/transitions.py     # Codex P2-1：E9 收敛（附 P3-NEW-13）

# PG-2 附加条件核验
for f in docs/schemas/*.schema.json; do git log -1 --format="%h %ad" --date=short -- $f; done   # 最新者为 403ddc7 / 2026-08-27
git rev-list --count 403ddc7..HEAD                                                              # 42
git log -1 --format="%h %ad" --date=short -- src/macao/core/types.py                            # 4df059e

# 反向核查（均未发现问题）
sed -n '48,61p;82p;87,101p;107,113p;129,140p' src/macao/merge/controller.py   # 合并五道闸
sed -n '69,80p' src/macao/workflow/fsm.py                                     # E2 时才置 consumed，与 PRD §3.4:858 一致

# P2-NEW-6
grep -rn "gitignore" src/                              # 仅 e2e_runner.py:46-47（其自身沙箱）
sed -n '173,185p' src/macao/cli/main.py                # macao init 只写 macao.yaml
sed -n '91,112p' src/macao/utils/git_utils.py          # worktree 建在 <repo>/.macao/worktrees/

# 基准锚点
sed -n '128p;216p;318p;839p;840,841p;843p;850p;858p;1152p;1537p' docs/MACAO_PRD_v2.md
```

四分支返工脚本、弃权 30 轮询脚本、`.gitignore` 污染脚本与 `UNKNOWN` 转换矩阵脚本保存于本次评审的临时目录；核心配置为 `reviewer_ids=["codex","opencode","antigravity"]`、`min_effective_votes=3`、`max_rework_rounds=3~5`、`timeouts.per_reviewer="2s"`、`require_signoff=False`，完整输出已在 §0、§2、§3 中逐条给出，可按上述参数重放。
