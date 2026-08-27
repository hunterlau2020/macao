# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-08-27（Phase 0 / Phase 1 核心代码开发完成，全套 22 项自动化测试全绿，提交代码级独立评审申请）
- **当前申请对象**：自 `2026-08-26-review-request-PRD-v2.3.1.md` 后的技术架构设计、核心代码实现与测试套件（commit `d137a05` .. `435eeea`）
- **当前目标等级**：**L2 SPEC-CODE-ALIGNED / PG-1 预准入**（待专家评审定级）
- **历史文档定级**：PRD **v2.3.1**（6 Schema + 11 fixtures，机验 18/18 PASS）
- **当前代码机验**：`PYTHONPATH=src python3 -m unittest discover tests -v` **22/22 PASS**（含 S1~S6 场景仿真、崩溃 Reconcile、FSM、仲裁算法与 Context 构建）

---

## 评审申请记录全量对账表 (Review Registry)

| 申请日期 | 申请文件 | 待审对象 / 范围 | 目标等级 | 评审状态 / 结论 |
|---|---|---|---|---|
| 2026-08-25 | `2026-08-25-review-result-ec60f70-*.md` | commit `ec60f70` (PRD v2.1) | L1 | 未通过（3 份评审：claude/codex/gemini） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.md` | commit `cc77a94` (PRD v2.3) | L1 | 未通过（5 份评审：claude/codex/gemini/kimi/opencode） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.1.md` | commit `403ddc7` (PRD v2.3.1) | L1 / PG-0 | 修订闭环完成（机验 18/18 PASS） |
| 2026-08-27 | `2026-08-27-review-request-Phase0-Phase1-Code.md` | commit `d137a05` .. `435eeea`<br>(Phase 0/1 架构/代码/22 项测试) | L2 / PG-1 | **PENDING_REVIEW**（待专家独立复审） |

---

## v2.3.1 修订闭环清单（对应 cc77a94 五份评审全部交付项）

| 编号 | 级别 | 修订内容 | 落点 | 代码实现落点 (commit 435eeea) |
|------|------|---------|------|------------------------------|
| P0-1 | P0 | "评审对象=合并对象"硬绑定：rebase 豁免**废除**；E4a push 对象==checkpoint_ref 硬校验 | PRD §14.5 步 1、§13、§3.3 E4a | `src/macao/merge/controller.py` |
| P0-2 | P0 | worktree **强制化**：独立 worktree 路径注入；准入硬条件 | PRD §16.3/§12.2/§2.4/§5.2 | `src/macao/utils/git_utils.py` |
| P1-1 | P1 | 弃权口径裁决：`.review.yml` 移出 ABSTAIN；弃权仅 Orchestrator 终局落盘 | review_manifest.schema.json、PRD §2.2 | `src/macao/consensus/engine.py`<br>`src/macao/workflow/orchestrator.py` |
| P1-2 | P1 | artifacts 改 `artifact_id` 自增主键 + 五元组唯一约束 + 追加归档语义 | PRD §11.4 DDL、§11.5 | `src/macao/storage/db.py`<br>`src/macao/storage/store.py` |
| P1-3 | P1 | 治理对账：STATUS 与 reviews/ 全量对账完成 | STATUS.md（本文件） | 已在每次申请前完成全量对账 |
| 分歧项 | — | Deadlock 入口边按并集方案 B 落文（E3 伴随动作内联判定 + 场景三） | PRD §3.3 E3 行、§3.4 | `src/macao/workflow/orchestrator.py`<br>`tests/test_orchestrator_sim.py` |
| P2-9 | P2 | vote_result 终局四值决策模型 + human_override 强制校验 | PRD §3.4、vote_result.schema.json | `src/macao/consensus/vote.py` |

---

## 评审专家分工与排班（依据 docs/EXPERT_QUALITY.md）

- **本轮代码评审阵容**：
  - **claude**（语义/业务流转轴）：主审 10 态 FSM、Orchestrator 多 Agent 事件循环与多轮返工；
  - **codex**（安全/沙箱/存储轴）：主审 Git Worktree 物理隔离、PTY 进程组强杀回收、SQLite WAL 存储与 Reconcile 恢复；
  - **opencode**（治理/Schema 契约轴）：主审 Schema 强校验落点、AEP 消息规范与评审治理闭环。

---

## 下一步行动

1. 组织专家对 `docs/reviews/2026-08-27-review-request-Phase0-Phase1-Code.md` 开展独立代码复审；
2. 若复审通过，宣告达成 **L2 SPEC-CODE-ALIGNED / PG-1 准入**；
3. 申请用户介入监督，开展真实三方 CLI（`claude-code`, `codex`, `kimi`）环境探针与实机连通性测试。
