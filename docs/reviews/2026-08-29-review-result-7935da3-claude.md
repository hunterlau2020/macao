# MACAO L3 / PG-2 终局整改全量闭环独立复审结论 — claude

- **评审日期**：2026-08-29
- **评审对象**：`docs/reviews/2026-08-29-review-request-L3-Final-Closed.md`
- **评审范围（commit）**：`ea536ab..7935da3`（HEAD）
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md`（§2.1 L3 判据、§3.3 证据最低要求、§4 声明验证矩阵、§6 反例场景库、§9 自审 Checklist）、`docs/MACAO_PRD_v2.md` v2.3.1、`docs/schemas/*.schema.json`
- **评审方式**：全部结论由本人从一手代码、SQLite 实库与实机复现独立推导；不采信申请文档自述，亦不采信 codex / grok / zcode / kimi / qwen 既有结论
- **结论**：**不予授予 L3 SCENARIO-VERIFIED / PG-2；维持 L2 / PG-1 待定**
  - 申请清单 3 项：**P1-2 完全属实闭环（VERIFIED）**、**P1-1 部分闭环（PARTIALLY_VERIFIED）**、**P3-1 声明被证伪（CONTRADICTED）**；
  - 独立发现 **2 项新 P1**（均由本轮 commit 新引入，且均有确定性实机复现），另有 2 项 P3。

---

## 〇、reviewer 自审登记（GUIDELINES §9）

- 本轮激活 checklist **B**（"已完成 ≠ 已有完成证据"）与 **A**（"声明位置 vs 实际读取位置不一致"）。上轮我提 P1-NEW-1 时只核到"`detect_*` 是否被生产调用"这一层，**未核对超时判定所用的配置项与 PRD §1.2 超时列语义是否一致**；本轮该盲点直接命中新发现 P1-NEW-3。
- 本轮所有 P1 结论均附可复现脚本与实测输出（GUIDELINES §9 强制自检第 5 条）。

---

## 一、申请清单逐项独立复核

| 编号 | 申请声明 | 独立复核结论 | 证据 |
|---|---|---|---|
| **P1-1** | 超时 ABSTAIN 落盘终局票面 + 基于时钟的自动检测 | **PARTIALLY_VERIFIED** | 见下表分解 |
| **P1-2** | `review_manifest` 消费 key 修正 + `artifacts.sha256` 补齐 | **VERIFIED** | 见 §二 |
| **P3-1** | `git diff --check 4df059e..HEAD` 100% 洁净、返回码 0 | **CONTRADICTED** | 见 §三 P3-NEW-1 |

### P1-1 分解复核

| 子项 | 结论 | 证据 |
|---|---|---|
| deadline 记录与随消息发布 | ✅ VERIFIED | `orchestrator.py:300-313` 计算并落 `REVIEW_REQUESTS_DISPATCHED` 审计（含 `deadline`/`timeout_seconds`）；`:337`/`:345` 将 deadline 写入 payload 与 `message_queue.deadline`。补齐了我上轮"deadline 恒为 NULL"的证据缺口 |
| 自动检测已接入生产链路 | ✅ VERIFIED | `orchestrator.py:429-431`：`if timed_out_reviewers is None: timed_out_reviewers = self.detect_timed_out_reviewers(task_id)`。我上轮"该参数零生产调用方"的阻断点确已闭环 |
| ABSTAIN 写入终局 `vote_result.json` | ✅ VERIFIED（正常路径） | `vote.py:117-126` 注入 ABSTAIN 票；`:161` `reviewers_responded = len(votes_list)`，与 PRD §2.2 第 318 行"计入 `reviewers_responded`"一致；`orchestrator.py:671-676` 于 `resolve_override` 从审计回填。实测终局 JSON 含 `opencode: ABSTAIN`、`abstain: 1` |
| 测试强度 | ✅ 实质断言 | `test_reviewer_timeout_degradation_scenario` 已由"手工传超时列表"升级为"推进时钟 → `detect_timed_out_reviewers` 自动检出"，并强断言落盘 JSON 的 `votes` / `reviewers_responded` / `vote_breakdown`，非浅断言 |
| **降级触发口径与人工确认** | ❌ **CONTRADICTED** | 见 §三 **P1-NEW-3** |
| **审计窗口鲁棒性** | ❌ **CONTRADICTED** | 见 §三 **P1-NEW-4** |

### 机验清单复核（申请文档 §二）

| # | 声明 | 实测 | 状态 |
|---|---|---|---|
| 1 | 49 ran / 49 PASS | `Ran 49 tests ... OK` | ✅ 属实 |
| 2 | 5 轮连续回归 0 flake | run1..run5 全部 `OK` | ✅ 属实 |
| 3 | `macao test-clis` 4/4 PASS | 4 款 CLI 全 PASS，0 orphan | ✅ 属实 |
| 4 | `e2e-run` 产物 100% 匹配、5 份全 `consumed=1` / `archived_path` 非空 / `sha256` 64 位 | 实测逐行核对全部成立 | ✅ 属实 |
| 5 | `git diff --check 4df059e..HEAD` 返回码 0 | 实测返回码 **2**，5 处尾随空白 | ❌ **证伪** |

---

## 二、已确认的正向闭环（P1-2 完全属实）

`fsm.py:105` 由 `rev_file.stem` 改为 `rev_file.name.replace(".review.yml", "")`；`store.py:83-97` 在 `content is None` 时按 `project_root` 拼接相对路径读盘计算 sha256。实机 `e2e-run` 后直查 SQLite，5 份产物**全部**闭环（对比我上轮实测的 3/5 `consumed=0`、5/5 `sha256=''`）：

```text
status PASS  tracked 5  archived 5
{'kind':'dev_manifest',    'reviewer_id':'',            'sha256':'d40d248a38e0...(64)', 'consumed':1, 'archived_path':'.macao/archive/<ref>/r1/.dev.yml'}
{'kind':'review_manifest', 'reviewer_id':'antigravity', 'sha256':'00f804900d6b...(64)', 'consumed':1, 'archived_path':'.macao/archive/<ref>/r1/antigravity.review.yml'}
{'kind':'review_manifest', 'reviewer_id':'codex',       'sha256':'cb47a3bf19c5...(64)', 'consumed':1, 'archived_path':'.macao/archive/<ref>/r1/codex.review.yml'}
{'kind':'review_manifest', 'reviewer_id':'opencode',    'sha256':'386c0e51e681...(64)', 'consumed':1, 'archived_path':'.macao/archive/<ref>/r1/opencode.review.yml'}
{'kind':'vote_result',     'reviewer_id':'',            'sha256':'9332b4d97197...(64)', 'consumed':1, 'archived_path':'.macao/archive/<ref>/r1/vote_result.json'}
```

配套测试 `test_artifacts_registered_and_tracked_in_database` 已按我上轮建议补齐 `consumed == 1`、`archived_path.startswith(".macao/archive/")`、`len(sha256) == 64` 三类强断言，覆盖盲点已封堵。`store.py:152-162` 同时修正了 `list_audit_events` 的 `detail` JSON 反序列化，使下游 `a["detail"]["review_round"]` 不再 `AttributeError`——该修正是必要且正确的。

---

## 三、本轮独立新发现

### P1-NEW-3（阻断）：自动超时降级绕过 PRD 强制的 ping 与 §6.1 人工确认，Reviewer 仅慢 10 分钟即被弃权并触发自动批准合并

- **口径错配（证据 1）**：PRD §1.2 第 128 行 `WAITING_REVIEW` 行的"超时"列为 **`30m（10m/reviewer 触发 ping）`** —— `per_reviewer`(10m) 是 **ping 触发点**，整轮评审窗口是 `review_request`(30m)。实现 `orchestrator.py:301-302` 与 `:385-386` **直接把 `per_reviewer` 当作弃权判定线**，且 `review_request` 配置项零消费方；`grep -rn "ping" src/macao/**/*.py` 无任何 ping/自愈实现（仅匹配到 `typing`）。降级提前 3 倍触发；PRD 第 1436 行亦把 `per_reviewer` 描述为"自愈仍在其窗口内"的**恢复窗口**，而非弃权判定线。
- **人工确认缺失（证据 2）**：PRD §2.2 第 318 行"Reviewer 超时经 **§6.1 人工确认**标记弃权后……写入 `ABSTAIN` 票据"；PRD §3.3 第 834 行"弃权标记由 Orchestrator 记入本轮票面，**随 E7 终局 `vote_result.json` 一并落盘**（不提前写决策未定的文件）"。实现在 `orchestrator.py:429-431` 无条件自动检测，`:467-481` 直接合成 ABSTAIN，随后在有效票达标时于 `:541` 生成 **`resolution: automatic`** 的 `vote_result.json` 并经 E4 转入 `MERGING`——**没有任何 §6.1 人工确认，也没有走 E7**。
- **实机复现（3 Reviewer，2 赞成 + 1 仅慢 11 分钟）**：

  ```text
  auto-detected timeouts: ['antigravity']
  state after: MERGING
  decision= APPROVED  resolution= automatic  responded= 3  breakdown= {'approve': 2, 'reject': 0, 'abstain': 1}
  votes= [('codex','YES_APPROVE'), ('opencode','YES_APPROVE'), ('antigravity','ABSTAIN')]
  ```

  在 `require_human_signoff: false`（E2E 沙箱配置 `e2e_runner.py:82` 即采用该值，亦为合法生产配置）下继续执行：

  ```text
  merge ok= True | msg= Merge pipeline completed successfully | final state= DONE
  ```

  即：第三位 Reviewer 只是慢了 10 分钟，其尚未提交的意见被系统自动作废，代码自动合并到 `main` 并进入 `DONE`。
- **回归性质**：本 commit 之前超时不可检测，该路径**不存在**；本轮新增的自动检测把"慢 10 分钟"变成"意见被丢弃 + 自动合并"。这是**本轮新引入的安全性回退**，且与 GUIDELINES §6 反例库"人工接管超时后系统的默认动作（是否静默按高置信度状态继续）"直接相关。
- **建议修复**：(1) `per_reviewer` 到期只发 ping / 触发一次自愈，不得据此弃权；(2) 以 `timeouts.review_request`(30m) 作为整轮降级窗口；(3) 超时降级的结果一律进入 `DEADLOCK` → `HUMAN_OVERRIDE_REQUEST` → E7 人工裁定，禁止在 `resolution: automatic` 的票面中出现超时 ABSTAIN；(4) 补一条断言"存在超时 ABSTAIN 时决策不得为 automatic"的回归测试。

### P1-NEW-4（阻断）：审计窗口硬编码 `limit=50`，轮询到一定次数后超时检测静默失效，终局票面丢失 ABSTAIN（P1-1 需求自行回退）

- **根因**：`orchestrator.py:370` `audits = self.store.list_audit_events(task_id, limit=50)`（超时检测）与 `:672` 同样 `limit=50`（`resolve_override` 回填 ABSTAIN）。`list_audit_events` 为 `ORDER BY sequence_id DESC LIMIT ?`，只返回最新 50 条。
- **放大因素**：`collect_and_evaluate_consensus` 是可重复调用的轮询式 API；`orchestrator.py:467-481` 的 `REVIEWER_TIMEOUT_ABSTAIN` 写入**只按内存 `votes_list` 去重、不查历史审计**，故每次轮询都追加一条，叠加 `DEADLOCK_DETECTED`，每轮询净增 2 条审计——自我加速把 `REVIEW_REQUESTS_DISPATCHED` 挤出窗口。
- **实机复现 1（检测静默失效）**：2 Reviewer，1 赞成 + 1 超时，重复调用共识评估：

  ```text
  poll  1 | total audit events=  7 | detect_timed_out=['opencode']
  poll  5 | total audit events= 15 | detect_timed_out=['opencode']
  poll 20 | total audit events= 45 | detect_timed_out=['opencode']
  poll 25 | total audit events= 55 | detect_timed_out=[]        <-- 派发事件被挤出 50 条窗口
  poll 40 | total audit events= 70 | detect_timed_out=[]
  ```

- **实机复现 2（终局票面丢失 ABSTAIN）**：同场景轮询 80 次（累计 110 条审计）后执行 `resolve_override('APPROVED')`：

  ```text
  FINAL vote_result: responded= 1  breakdown= {'approve': 1, 'reject': 0, 'abstain': 0}  votes= [('codex','YES_APPROVE')]
  ```

  与本轮刚"闭环"的 P1-1 目标态（`responded=2 / abstain=1 / opencode: ABSTAIN`）完全相反——**本轮修复的正确性取决于轮询次数**，属不可接受的隐式失效。
- **判据冲突**：GUIDELINES §4"所有状态转换可审计"与 §7-5"崩溃恢复类测试必须验证重启后是否重复投票/重复生成产物"——此处正是重复写审计导致的审计链自噬。
- **建议修复**：(1) 用按 `type` + `task_id` + `review_round` 的定向 SQL 查询取代 `limit` 窗口扫描（新增 `StateStore.find_audit_events(task_id, type, review_round)`）；(2) `REVIEWER_TIMEOUT_ABSTAIN` 按 `(task, round, reviewer)` 幂等写入；(3) 补一条"轮询 N 次后检测结果与终局票面保持不变"的回归测试。

### P3-NEW-1：`git diff --check` 声明被证伪

申请文档 §一 P3-1 与 §二 第 5 条均声明 `git diff --check 4df059e..HEAD` "100% 洁净，返回码 0"。实测返回码 **2**：

```text
docs/reviews/2026-08-29-review-result-ea536ab-codex.md:36: trailing whitespace.
docs/reviews/2026-08-29-review-result-ea536ab-codex.md:52: trailing whitespace.
docs/reviews/2026-08-29-review-result-ea536ab-codex.md:63: trailing whitespace.
docs/reviews/2026-08-29-review-result-ea536ab-codex.md:76: trailing whitespace.
docs/reviews/2026-08-29-review-result-ea536ab-codex.md:85: trailing whitespace.
```

`docs/POC_VERIFICATION_REPORT.md` 的旧问题确已清理（属实），但**本 commit 自身新增的 codex 复审报告引入了 5 处新的尾随空白**，`ea536ab..HEAD` 区间同样返回 2。属 GUIDELINES §9-B 典型模式：以"已清理某文件"替代"命令实际返回 0"。

### P3-NEW-2：`vote_breakdown` 收窄后 E2E 报告 `effective_votes` 走死 fallback

`vote.py:165-169` 将 `vote_breakdown` 由引擎输出的 7 键收窄为 `approve/reject/abstain` 三键。该收窄**与 PRD §2.3 第 363 行示例及 `vote_result.schema.json` 完全一致，属对齐改进**；但 `e2e_runner.py:238` 的 `breakdown.get("effective_votes", approve_count)` 自此恒走 fallback，E2E 报告中的 `effective_votes` 在混合票型下会误报为赞成票数（全同意场景两值巧合相等，故未被 49 项测试发现）。建议改为由 `approve + reject` 直接计算。

### 遗留未闭环项（跨轮，非本轮虚假声明）

- `adapter/integ_harness.py:109` `ansi_stripped_ok = True` 仍为无条件常量：第 108 行取到 `clean_logs` 后从未检查内容，`test-clis` 的 `ansi_stripped` 列仍是橡皮图章。该文件本轮未修改，建议在 L4 / OPS 前闭环。

---

## 四、定级建议

| 判据 | 结论 |
|---|---|
| L2 SPEC-CODE-ALIGNED | 满足 |
| **PG-1**（L2 + P0/P1 归零） | **暂不满足**：存在 P1-NEW-3、P1-NEW-4 |
| **L3 SCENARIO-VERIFIED** | **不满足**：超时场景的实现与 PRD §1.2/§2.2/§3.3 口径冲突（P1-NEW-3），且其正确性依赖调用次数（P1-NEW-4），TEST 证据判为 `PARTIALLY_VERIFIED` |
| **PG-2** | **不予授予** |

**授予条件**：

1. 闭环 **P1-NEW-3**：`per_reviewer` 仅触发 ping/自愈；以 `review_request` 为降级窗口；超时降级一律经 E7 人工裁定落盘，`resolution: automatic` 的票面中不得出现超时 ABSTAIN；
2. 闭环 **P1-NEW-4**：审计查询改为定向 SQL，`REVIEWER_TIMEOUT_ABSTAIN` 幂等写入，并补轮询稳定性回归测试；
3. （建议同轮）修正 P3-NEW-1 尾随空白并以命令返回码而非"某文件已清理"作为声明依据；修正 P3-NEW-2 的 `effective_votes` 计算。

上述 1、2 闭环并经实机复验后，本人支持授予 **L3 SCENARIO-VERIFIED / PG-2**。

**须特别记录**：本轮 P1-2 是我方连续三轮跟踪项中**首个完全无保留闭环**的条目（key 匹配、consumed、archived_path、sha256、测试断言五项齐备），整改质量显著提升；P1-1 的"自动检测接入生产链路"部分亦真实闭环。本轮两项 P1 均属"修复引入的新语义偏差"而非"虚假声明"。

---

## 五、附：本轮复现命令

```bash
# 机验清单 1-3
PYTHONPATH=src python3 -m unittest discover tests -v
for i in 1 2 3 4 5; do PYTHONPATH=src python3 -m unittest discover tests | tail -1; done
PYTHONPATH=src python3 -m macao.cli.main test-clis

# P1-2 闭环核验：E2E 后直查 artifacts 表
PYTHONPATH=src python3 -c "
import sqlite3
from macao.workflow.e2e_runner import ControlledE2ERunner
r=ControlledE2ERunner(); r.run_e2e_cycle()
c=sqlite3.connect(str(r.repo_dir/'.macao'/'state.db')); c.row_factory=sqlite3.Row
for row in c.execute('SELECT kind,reviewer_id,sha256,consumed,archived_path FROM artifacts'): print(dict(row))
r.cleanup()"

# P1-NEW-3：3 Reviewer，2 赞成 + 1 慢 11 分钟 -> 自动 APPROVED -> MERGING -> (signoff 关闭时) DONE
#   在临时 repo 中 dispatch 后将 REVIEW_REQUESTS_DISPATCHED / STATE_TRANSITION_E2 的 ts 回拨 11 分钟，
#   再调用 collect_and_evaluate_consensus(configured_reviewers=3) 与 execute_merge，见 §三 实测输出

# P1-NEW-4：2 Reviewer，1 赞成 + 1 超时，重复调用 collect_and_evaluate_consensus
#   第 25 次起 detect_timed_out_reviewers 返回 []；第 80 次后 resolve_override 的终局票面 abstain=0

# P3-NEW-1
git diff --check 4df059e..HEAD; echo "rc=$?"
```
