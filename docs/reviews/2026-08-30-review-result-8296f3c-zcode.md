# MACAO L3/PG-2 全员一致终局封板申请 独立评审结论

- **评审日期**：2026-08-30
- **评审人**：zcode（独立评审，GLM；应仓库所有者指令参与本轮，非申请 §头所列五人 panel 之列，登记为附加独立评审）
- **评审对象**：commit `3ea5256` .. `8296f3c`（P1-NEW-12/Codex P1-1 E6 新 commit 硬校验 + Codex P2-1 E9 源状态收敛；65 项全量测试）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.0（注：任务指令所称 `docs/REVIEW_GUIDE.md` 不存在，以仓库唯一评审方法论文档为基准）+ `docs/MACAO_PRD_v2.md` v2.3.1 + `docs/schemas/`
- **申请文件**：`docs/reviews/2026-08-30-review-request-L3-PG2-Unanimous-Seal.md`
- **结论**：**本轮不予 L3 SCENARIO-VERIFIED / PG-2——阻断项仅剩 1 项 P1，且为一行修复**。本轮两项声明修复属实；本人全部历史阻断条件与遗留项经逐项核验**实质清账**（超时场景已真实实现并有 5 项专项测试）；L3 六场景判据首次全部具备测试证据。唯一阻断：**"全绿声明平台条件性"第 4 次复发**——申请"65/65 PASS、5 轮 0 flake"在 win32 实测为 **64/65（3/3 次一致复现 1 项失败）**，根因为测试断言硬编码 POSIX 路径分隔符。生产代码无影响、修复代价一行；修复后本人**支持授予 L3 / PG-2**（明确：这是本人视角的最后一项）。

---

## 一、本轮声明修复独立复验

| 项 | 申请声明 | 独立复验 | 判定 |
|---|---|---|---|
| P1-NEW-12 / Codex P1-1 | E6 返工回路新 commit 硬校验 | `orchestrator.py:237-251`：REWORK 下 `latest_commit == prev_ref` 直接 `return None`；已消费 `dev_manifest`（`consumed=1` 同 commit）拒绝；且新增 `commit_exists` 物理存在校验——**同时落实了本人首轮代码评审（435eeea 轮）P2-6"Layer 1a 不校验 commit_exists/未消费"**，为历轮首次；`test_rework_unchanged_commit_fails_closed_and_requires_fresh_commit` Case A/B 双向覆盖 | **✅ 属实** |
| Codex P2-1 | E9 源状态收敛 | `transitions.py:48-51`：E9 仅 `CONSENSUS_CHECK → WAITING_REVIEW`，对齐 PRD §3.3:841 | **✅ 属实** |

## 二、本人历史阻断条件与遗留项清账（跨 `4df059e`..`8296f3c` 六轮追验）

| 历史项 | 来源轮 | 现状与证据 |
|---|---|---|
| **超时场景证据**（L3 授予条件） | 4df059e 轮（本人唯一阻断） | **✅ 已实质满足**：`orchestrator.py` 实现完整超时链路——`per_reviewer` 时长经 `parse_duration` 自配置读取、REVIEW_REQUEST 携带 deadline、`detect_timed_out_reviewers` 以**可注入 `current_time`**（fake-clock 友好）按"expected − submitted"差集检测；超时弃权以 `REVIEWER_TIMEOUT_ABSTAIN` 审计事件落账并**按 E9 重试分发代际隔离**（历史超时被 RETRY_REVIEW 作废，杜绝跨代际毒化）；迟到票据隔离不参与自动仲裁；TIMEOUT ABSTAIN 路径 HOLD 不写盘、触发 E7。测试 5 项：降级场景、3 人全超时 HOLD+人工接管、审计轮询 >50 不丢失、超时后迟到维持 HOLD、E9 重试后重复超时维持 HOLD |
| vote.py 校验移至写盘后（顺序回归） | 4df059e 轮 P2-1 | **✅ 已复原**：`vote.py:199` 校验先于 `:203` 写盘 |
| qwen R1：非法 `human_resolution` 静默落 APPROVED | e7ba2d2 轮起追踪三轮 | **✅ 已修**：`vote.py:149-152` 改为归一化（大小写/同义词）+ 非法值 `raise ValueError` fail-fast |
| ls-remote 空结果静默跳过远端校验 | 4df059e 轮 P3-1 | **✅ 已修**：`merge/controller.py:130-134` `code_ls != 0 or empty` → 回滚 + Fail-closed 拒绝 |
| 死依赖 pytest/prompt_toolkit | 435eeea 轮起 | **未修**（`pyproject.toml:31-32`），P3 继续携带 |
| schema.py 向上遍历寻址（qwen R2，pip 分发后失效） | aa173d8 轮起 | **未修**（`core/schema.py:24` 仍 parents 遍历），P2 携带——PoC 阶段可接受，正式分发前必须改 `importlib.resources` |

## 三、阻断项（新 P1 ×1）

### P1-1 "全绿声明平台条件性"第 4 次复发：65/65 在 win32 实测 64/65

- **实测**：`PYTHONPATH=src python -m unittest discover tests` 于本机（win32 / Python 3.11.9）**3 次运行均 1 failure**：
  `test_p0_p1_rectification.py:471` 断言 `a["archived_path"].startswith(".macao/archive/")`——硬编码 POSIX 分隔符；win32 下 `str(Path)` 产出 `.macao\archive\<sha>\r1\.dev.yml`，断言恒 False。
- **定性**：生产代码无同类硬编码（grep 证实，仅注释提及），归档物理行为在两平台均正确——**缺陷限于测试断言可移植性**；但申请 §2"65 项 100% 通过 / 5 轮 325 次 0 flake"未注明平台限定，与"22/22（6 ERROR@win32）→24/24→34/34（3 FAIL@win32）"构成**同模式第 4 次复发**。前两次（34/34 轮）经五人 panel 定为 P1 并整改（HAS_PTY 优雅跳过），本轮在测试断言层复发。
- **修复**（一行）：断言改用 `Path(...).as_posix().startswith(".macao/archive/")` 或比较 `os.sep`；同时建议申请模板固定附加"平台 + 依赖安装步骤"字段，从流程上终结该模式。
- **定级依据**：与本人在 `906b17e` 轮 P1-5（同类同因）保持一致；PG-1/PG-2 要求 P0/P1 为零，故本轮阻断。

## 四、L3 判据终局对账（GUIDELINES §2.1 六场景）

| 场景 | 证据 | 状态 |
|---|---|---|
| 全同意 | S1 / e2e-run（本机实测 votes_yes=3、7/7 步、5 份归档、终态 DONE） | ✓ |
| 1:1 僵局 | S3 + deadlock 专项（HOLD 不写盘） | ✓ |
| **超时** | 本轮起 5 项专项测试 + 可注入时钟实现 | **✓（本人条件已满足）** |
| 弃权 | consensus 弃权算术 + 超时弃权落账/E7 持久化断言 | ✓ |
| 崩溃恢复 | reconcile ×2 | ✓ |
| 返工循环 | S2 + E6 新 commit 双向用例 | ✓ |

**首次六项全齐。** PG-2 的"接口稳定"维度：协议枚举经 P0-NEW-2 修复后与 Schema/PRD 一致并有枚举一致性守卫；"消费方场景测试"：Adapter 契约全生命周期驱动 + 事务性分发。

## 五、其他登记（P3 ×3）

1. `transitions.py:46` E7 允许自 `UNKNOWN` 转移——PRD E7 行字面仅 `CONSENSUS_CHECK`；自 UNKNOWN 人工复位有 §3.2 Layer 3 依据（"等待用户确认后人工设定状态"），设计可辩护，但建议在代码注释或 PRD 显式登记该依据，避免后续评审再次对表。
2. **治理账目异常**：commit `0c8bf11` message 声称"同步 claude, codex, grok, **zcode** 对 ea536ab 独立复审报告"，但 `docs/reviews/` 中**不存在 zcode 对 ea536ab 的评审文件**（本人名下最后一份为 `4df059e`）。按"STATUS 与 reviews/ 全量对账"规则应核实：报告是否曾以 zcode 名义提交后被替换/删除，或有提交信息笔误。
3. 死依赖 pytest/prompt_toolkit（历轮已列，随批处理）。

## 六、评审人机验记录（win32 / Python 3.11.9）

| 项目 | 结果 |
|---|---|
| 全量套件 ×3 | **65 ran / 1 failure ×3**（`test_artifacts_registered_and_tracked_in_database` 路径分隔符断言；其余 64 项含超时 5 项、E6 双向用例全绿） |
| `macao e2e-run` | 7/7 步 OK、votes_yes=3、Archived 5 files、终态 DONE |
| `compileall src` / `git diff --check` | OK / clean |
| 登记表对账 | results=66、requests=14，与申请 §3 声明一致 |

## 七、定级判定与闭环路径

1. **本轮不予 L3 / PG-2**：P1-1（一行修复）未清零前，PG-1"P0/P1 为零"不满足。
2. **对整体状态的评价**：本人自 `4df059e` 轮设下的全部授予条件（message_id、超时场景）及历史 P2/P3 已实质清账；六场景判据首次全齐；本轮两项修复质量高（E6 三重校验含物理存在性检查）。与 L3 的距离已收敛为**一个测试断言 + 一句平台限定声明**。
3. **闭环路径**：修 `test_p0_p1_rectification.py:471`（`as_posix()`）→ win32/posix 各跑一轮全量（或声明 POSIX-only 并使该断言平台无关）→ 任一 panel 成员书面确认 → **本人支持授予 L3 SCENARIO-VERIFIED / PG-2，无进一步条件**。

## 八、Reviewer 自审记录

- 基准勘误：任务指令指定 `docs/REVIEW_GUIDE.md` 不存在，实际使用 `MACAO_REVIEW_GUIDELINES.md`，已在报告头注明。
- 本轮执行了"整改 diff 全量重读"固定动作（`4df059e`..`8296f3c` 的 orchestrator/transitions/vote/store/schema 变更逐段审读），未发现新的生产级回归；唯一的测试层问题即 P1-1。
- 全部判定附行号或本机实测；3×65 的失败为确定性复现（非概率性），与本轮 message_id 类概率缺陷无关。
