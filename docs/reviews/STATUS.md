# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-08-28（四方独立专家针对 906b17e 集成申请出具评审报告，全量对账完成）
- **当前申请对象**：自 `2026-08-27-review-request-Phase0-Phase1-Code.md` 与技术框架横向评审（`aa173d8`）以来的架构装配、4 款真实 AI CLI 适配器矩阵、第一阶段 PTY 联调 Harness、第二阶段端到端协同闭环与全套自动化测试
- **当前定级状态**：**维持 L2 SPEC-CODE-ALIGNED / PG-1（未达 L3 SCENARIO-VERIFIED / PG-2）**；四方专家一致指出：配置注入键路径断裂致 signoff 绕过、E2E Runner 伪造产物未注入真实 Adapter、展示字段与底层断裂、Worktree 降级与沙箱边界需系统性整改
- **历史文档定级**：PRD **v2.3.1**（§3.2 Layer 1c 四值终局分支已单点闭环修复，达到 L1 DOC-ALIGNED / PG-0）
- **当前代码机验**：`PYTHONPATH=src python3 -m unittest discover tests -v` **34 ran / 34 PASS (100%)**；`test-clis` / `doctor` / `preflight` / `git diff --check` **全部 clean PASS**。

---

## 评审申请记录全量对账表 (Review Registry - 31 份历史与当前评审报告 + 4 份申请全量对账)

| 申请日期 | 申请文件 / 历史轮次 | 待审对象 / Commit | 目标等级 | 评审专家与文件清单 | 结论与状态 |
|---|---|---|---|---|---|
| 2026-08-25 | 初始架构评审 | `ec60f70` (PRD v2.1) | L1 | `2026-08-25-review-result-ec60f70-claude.md`<br>`2026-08-25-review-result-ec60f70-codex.md`<br>`2026-08-25-review-result-ec60f70-gemini.md` (3 份) | 未通过（发现状态机与共识分歧） |
| 2026-08-26 | 历史迭代轮 1 | `47f54f2` (PRD v2.2) | L1 | `2026-08-26-review-result-47f54f2-codex.md` (1 份) | 历史追踪（指出沙箱与存储边界） |
| 2026-08-26 | 历史迭代轮 2 | `684a012` (PRD v2.2.1) | L1 | `2026-08-26-review-result-684a012-claude.md`<br>`2026-08-26-review-result-684a012-codex.md`<br>`2026-08-26-review-result-684a012-gemini.md` (3 份) | 历史追踪（收敛 AEP 信封与 Schema） |
| 2026-08-26 | 历史迭代轮 3 | `8ab9be7` (PRD v2.2.2) | L1 | `2026-08-26-review-result-8ab9be7-claude.md`<br>`2026-08-26-review-result-8ab9be7-codex.md`<br>`2026-08-26-review-result-8ab9be7-gemini.md`<br>`2026-08-26-review-result-8ab9be7-kimi.md`<br>`2026-08-26-review-result-8ab9be7-opencode.md` (5 份) | 历史追踪（确立并集方案 B 与死锁 HOLD） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.md` | `cc77a94` (PRD v2.3) | L1 | `2026-08-26-review-result-cc77a94-claude.md`<br>`2026-08-26-review-result-cc77a94-codex.md`<br>`2026-08-26-review-result-cc77a94-gemini.md`<br>`2026-08-26-review-result-cc77a94-kimi.md`<br>`2026-08-26-review-result-PRD-v2.3-opencode.md` (5 份) | 未通过（提出 2 P0 + 3 P1 修订项） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.1.md` | `403ddc7` (PRD v2.3.1) | L1 / PG-0 | `2026-08-26-review-result-403ddc7-claude.md`<br>`2026-08-27-review-result-403ddc7-codex.md`<br>`2026-08-27-review-result-403ddc7-zcode.md` (3 份) | 上轮 2 P0 + 3 P1 全部 VERIFIED；新增 P1（§3.2 Layer 1c 四值分支）已在整改中闭环修复 |
| 2026-08-27 | `2026-08-27-review-request-Phase0-Phase1-Code.md` | `d137a05` .. `435eeea` | L2 / PG-1 | `2026-08-27-review-result-435eeea-claude.md`<br>`2026-08-27-review-result-435eeea-codex.md`<br>`2026-08-27-review-result-435eeea-zcode.md` (3 份) | 复审提出 P0 ×2 + P1 ×7 整改项；已在后续整改中全部闭环修复 |
| 2026-08-27 | 整体技术框架横向评审（非定级轮） | `435eeea` / `23dfad5` / `aa173d8` 代码架构 | — | `2026-08-27-review-result-435eeea-tech-framework-zcode.md`<br>`2026-08-27-review-result-23dfad5-tech-framework-claude.md`<br>`2026-08-27-review-result-23dfad5-codex-framework.md`<br>`2026-08-27-review-result-aa173d8-tech-framework-qwen.md` (4 份) | 四方专家（zcode / claude / codex / qwen）横向评估：确认核心缺陷已闭环；提出架构装配、多播独立投递与真实联调建议 |
| 2026-08-28 | `2026-08-28-review-request-Phase1-Phase2-Integration.md` | `aa173d8` .. `906b17e` | **L3 / PG-2** | `2026-08-28-review-result-906b17e-zcode.md`<br>`2026-08-28-review-result-906b17e-claude.md`<br>`2026-08-28-review-result-906b17e-codex.md`<br>`2026-08-28-review-result-906b17e-integration-qwen.md` (4 份) | **四方专家一致评审：未达 L3 SCENARIO-VERIFIED / PG-2，维持 L2/PG-1**<br>核心问题：<br>1. P0-1: E2E Runner 伪造产物未注入真实/Mock Adapter，展示字段与底层断裂（votes_yes=0）；<br>2. P0-2: 配置注入键路径断裂（`require_human_signoff` 静默失效，从未推送 remote）；<br>3. P0-3: 所谓 sandboxed 仅为临时 cwd，未达成 OS 级沙箱隔离承诺；<br>4. 归档目录假阳性与 Windows 跨平台测试失败（3 FAIL）。待全面整改。 |

---

## 本轮待整改核心问题清单 (From 4 Experts on 906b17e)

| 编号 | 严重度 | 问题描述与整改要求 | 涉及专家 |
|---|---|---|---|
| **P0-1** | 阻断 | **E2E 真实/仿真隔离与 Adapter 注入**：Runner 必须通过 Adapter 驱动产物生成，杜绝直接写 YAML 伪造；修复 `vote_breakdown` 键不匹配与归档目录检查（`<checkpoint_ref>` 而非 `<task_id>`）。 | zcode, claude, codex, qwen |
| **P0-2** | 阻断 | **配置解析与合并安全硬校验**：修复 `Orchestrator` 与 `MergeController` 对 `require_human_signoff`、`remote_name` 的直接读取，禁止异常时回退到危险缺省值；打通真实/仿真 Git Remote push 校验。 | zcode, claude, codex, qwen |
| **P0-3** | 阻断 | **沙箱边界定性与安全分级**：在代码与文档中严格区分 `CWD/Worktree 隔离` 与 `OS 容器级沙箱`，在未实装 Bubblewrap/Docker 时明确标注，禁止虚假安全承诺。 | codex, zcode, qwen |
| **P1-1** | 严重 | **PTY 跨平台与真实子进程生命周期测试**：在 Windows 上优雅降级或跳过 PTY 测试；在 Linux 上补充长进程/信号强杀真实测试。 | zcode, claude, codex |
| **P1-2** | 严重 | **归档物理目录路径修正**：对齐 PRD 规范，归档路径统一为 `.macao/archive/<checkpoint_ref>/r<round>/`，严禁 0 归档假阳性。 | zcode, claude, codex, qwen |

---

## 下一步行动

1. 提交全部评审报告与 STATUS 全量对账；
2. 开展针对上述 P0/P1 的系统性代码与测试整改。
