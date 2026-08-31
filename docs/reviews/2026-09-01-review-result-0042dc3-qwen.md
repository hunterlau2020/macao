# PRD v2.5 修改提案（DRAFT v0.2）L1 复审结论

- **评审日期**：2026-09-01
- **评审人**：qwen（独立评审）
- **评审对象**：`docs/PRD_CHANGE_PROPOSAL_v2.5.md` **DRAFT v0.2 工作区修订稿**（基于已提交版本 `0042dc3`，工作区差异 485+/258-；命名沿用 `0042dc3` 与本轮同行一致，修订稿未提交状态见 §四注记）
- **评审级别**：L1 DOC-ALIGNED（设计文档对齐评审，适用 GUIDELINES §1–§6、§9、§11；CODE/TEST 为 NOT_APPLICABLE）
- **对齐基准**：`docs/MACAO_PRD_v2.md`（现行 v2.3.1 标题）、`docs/usercases/PRODUCT-FACTS.md` F-1~F-22、`docs/usercases/UC1~UC10`、`docs/FAQ.md`、三份输入评审 `2026-09-01-review-result-0042dc3-{gemini,glm,grok}.md`
- **结论**：**授予 L1 DOC-ALIGNED。** 三份输入评审的全部 P0×3 / P1×12 逐项核验**实质闭环**，闭环证据在 v0.2 中逐条可定位；提案内部算术、转移守卫、引用行号、示例可解析性独立复核全部通过；0 项新 P0/P1，仅 4 项 P3 登记（§三）。不构成 `ACCEPTED/IMPLEMENTED`（提案 §13 自我约束有效）。

---

## 一、三份输入评审闭环逐项核验（§12 声明 → v0.2 实证）

| 输入项 | v0.2 闭环落点 | 独立核验 |
|---|---|---|
| **glm P0-1** 未显式推翻 F-13/F-16 方案 | D-2"正式替代"+§9.2 废止清单+§11"不再列为开放项" | ✅ 推翻已显式声明；F-13/F-16 原文核读（F-13"Executor 负责语义处置不写 decision"、F-16"权重管理员预定、禁自动调整"）与 v0.2 §7.1"不得自动调整权重"、P-3 写者边界**同向而非冲突**；冲突对象实为 UC 层 issues_summary 回写方案，已列迁移 |
| **glm P1-1** 显式 ABSTAIN 与实现冲突 | D-3 + §4.1 + §10.1 + 验收场景 8 | ✅ 显式弃权保留、`abstain_reason` 必填、`source: manifest/timeout` 区分、responded/accounted 双统计定义完整 |
| **glm P1-2** git 提交语义迁移遗漏 | §9.1 行号清单 | ✅ 逐条命中现行 PRD：L416（.review.yml 纳入 git 提交）、L833（E3 伴随）、L859（生命周期）、L1355（写入顺序③）、L1510（§14.1 第 7 步）、L1632、L1658-1669（C2 content_base64 内嵌/C3 git 留证）——**7 处引用全部属实** |
| **glm P2-1~4** | §4.3 穷尽覆盖 / §6.3 唯一 `role_view` / §7.1+§7.2"三者叠加不互相替代" / §4.2+§4.4 `EXEMPTED_BY_ADMIN` | ✅ 四项分别落位；role_view 表与 `docs/usercases/UC1-init-glm.md:143` 投影表值域一致 |
| **grok P0-1** E4c 语义判断违反 P-1 | D-5 + §4.3 规则 3 | ✅ `requires_new_checkpoint` 必填布尔、缺失失败关闭、"Orchestrator 不得从自然语言/文件类型/枚举推断"——E4c 不复存在，改由 E5a 显式守卫 |
| **grok P0-2** BACKLOG 与单任务 FSM 互斥 | D-4 | ✅ 更名 `DEFERRED`、`followup_task_id` 可选且**不查库**、后续任务 DONE 后创建——与验收场景 19 自洽 |
| **grok P1-1** disposition 与 F-13/F-16 冲突 | D-2（同 glm P0-1 并案） | ✅ |
| **grok P1-2** 2:1 示例与独裁帽冲突 | §7.1 示例改 N=3 `2:1:1` + 配置期帽 | ✅ 帽公式复核：`3*2=6 < 2*4=8` 通过；N=2 权重 2:1 `6<6` 不通过→拒启动（与 grok §V SIM 一致）；`3*w_i < 2*W` 严格不等号形式化（gemini P2-2 同闭） |
| **grok P1-3/P1-4** HOLD 无协议边、豁免未接转移表 | §4.4 `DISPOSITION_REQUIRED` + deadline/ping + §4.5 E7 行 + `NEEDS_ADMIN`→HOLD | ✅ 现行 AEP 枚举实测 **7 类**（`core/types.py:22-30`），"新增第八种"算术成立；超时"不自动创建/忽略/合并"fail-closed 明文化 |
| **grok P1-5** context 语义块不完整 | §5.2 九块逐项迁移表（首轮/后续轮分列） | ✅ 与现行 §5.2 语义块全集对照无遗漏，且"缺少引用/不可达/hash 不符/路径越界/round 不一致失败关闭" |
| **grok P1-6** evidence ref 生命周期未闭合 | §5.4（5.4.1~5.4.3） | ✅ canonical/inbox/staging 三层 + refspec + 串行 promotion + 双阶段 push/verify + pre-merge seal + post-merge 失败保持 MERGING（不假回滚）+ show/export 可见性；自引用禁令（blob 不嵌自身 commit）逻辑自洽 |
| **grok P1-7/P1-8** 路径无 round、覆盖不一致 | §4.3 `r<round>` 路径 + 规则 1"精确覆盖、一项不多不少恰好一次" | ✅ REWORK 与 APPROVED 两路均要求全量覆盖，口径统一 |
| **grok P1-9** 三个 2/3 歧义、权重 quorum 分母 | §7.2 五门禁命名 + 整数公式 | ✅ 权重 quorum 分母明确为**配置总权重 W**；§7.3 六行决策表逐行复算通过（含"高权 ABSTAIN+两低权 YES → DEADLOCK，`E_W=2<ceil(8/3)=3`"）；该行为在 §7.3 尾注显式公示为接受的安全行为 |
| **grok P2-1~P2-6 / P3-2** | §6.1 命令边界 / §4.3 枚举统一 / §4.3 规则 2 冻结拼接序 / §4.6 完整示例 / P-4 sidecar / §5.3 预算入配置 / §9.1 文首升版 | ✅ 逐项落位；P3-1（F-5 悬空"见 F-8b"）在现行 PRODUCT-FACTS **已不复现**（F-5 文本干净、全文无 F-8b），自然清账 |
| **gemini**（0 P0/P1；3 P2 + 1 P3 + §V 六项裁定建议） | §4.1 Schema 条件互锁 / §7.1 帽形式化 / D-4 消解 BACKLOG 校验 / §6.1 交互分流 / D-9 adopt 别名 | ✅ 全映射；§V 六项（ADVISORY 必处置、独立产物、16KiB、默认全 1、adopt 别名、BACKLOG 不自动建任务）在 v0.2 均有对应规范文本 |

## 二、独立内部一致性复核（不依赖 §12 自述）

1. **§4.6 示例算术复算**：N=3、W=4、票面 2:1:1（YES w2 + YES w1 + NO w1）→ 席位 quorum `3≥2`✓、权重 quorum `4≥ceil(8/3)=3`✓、胜方 `3*3=9≥2*4=8`✓、胜方席位 `2≥2`✓ → `APPROVED` 与示例一致；NO 方 `BLOCKING` issue 与"少数方 BLOCKING 不否决加权结果"（§4.1 尾段）自洽
2. **转移守卫闭环**：§4.2 四场景 ↔ §4.5 E3~E7 守卫逐一对应；E5a 独立编号不复用 E4a/E4b（审计语义隔离）✓
3. **写者边界**：D-1（Orchestrator 单写 vote_result）/ D-2（Executor 单写 disposition）/ P-3 交叉引用 `path+evidence_commit+sha256`——无双写者残留；与 PRODUCT-FACTS F-20 待定项解析方向一致
4. **引用真实性**：`docs/usercases/` UC-1~UC-10 + PRODUCT-FACTS + README 存在；`issues_summary` 旧方案实存于 `FAQ.md`（Q15/§执行者汇总段）与 `UC1/UC5/UC6`——§9.2 废止对象全部可定位
5. **示例可解析性**：全文 5 个代码块（4 YAML + 1 JSON）`safe_load/json.loads` **5/5 通过**（L1 硬性判据）
6. **确定性用语**：无"100%/99%"式既成事实表述；§5.3/§11 将未实测参数显式标注为"PoC 后可调"——符合 L1 目标/事实分离要求

## 三、P3 登记（不阻塞，回写时批处理）

1. **提案正文未提交**：v0.2 修订稿仅存在于工作区（`M docs/PRD_CHANGE_PROPOSAL_v2.5.md`）——标记 `ACCEPTED` 前必须先落盘为可追溯 commit（本报告以工作区内容为评审对象，已钉死声明）
2. **生效条件清单遗漏**：文首"生效条件"列举"PRD、SRS、Schema、代码、fixture、测试、FAQ 和 UC"，**漏 `PRODUCT-FACTS`**（§9.2/§13 实际覆盖，仅清单措辞不全）
3. **PRD 版本标题滞后**：现行权威文件标题仍为 **v2.3.1**（v2.4 增补已入正文未升标题，grok P3-2 复现）——§9.1 已计划"一次升级 v2.5"，回写时须含文首版本行
4. **目录命名分裂**：`docs/usercases/`（UC 套件/FACTS 所在）与 `docs/usecases/`（另一份 UC-1）并存——拼写不一致的孪生目录，建议合并并统一引用

## 四、定级判定

**授予 L1 DOC-ALIGNED。**

- 判据核对：四份文档体系字段/术语可对照核验（§5 唯一权威表方向：`DEFERRED` 统一、`role_view` 唯一、issues 拼接序冻结）✓；全部示例合法可解析 ✓；确定性用语标注合规 ✓；P0/P1 为零 ✓
- **不构成** `ACCEPTED/IMPLEMENTED`：按提案自身 §13 与文首生效条件，须先完成 PRD/SRS/Schema/代码/测试全链同步并经 §10.3 二十项验收——本评审仅认证设计文档层一致性
- 与同行关系：gemini（0042dc3 轮即授予 L1）、glm（NOT-ACCEPTED→本轮其 P0/P1 已闭环）、grok（"不能作为编码基线"→本轮其 P0×2/P1×9 已闭环）；本报告为 v0.2 修订稿的首份复评结论
- 建议决议：管理员可据三份评审的闭环核验结果批准提案进入 §10.2 实施序列；批准前落实 §三-1（提案落盘提交）

## 五、全量对账与自审记录

- 输入评审三份全部通读（99+67+170 行），§12 闭环表与三份原文**无漏项**（含 grok P2-5/P2-6/P3-1/P3-2 与 gemini §V 六项，超出 §12 表面的四行摘要）
- 算术核验为本人按 §7.2 公式手算（§4.6 示例 + §7.3 六行 + 配置帽三例），未复用提案结论；行号引用 7 处逐一读取现行 PRD 原文
- glm 报告披露其为 UC-1/5/6 F-13 对齐修复（`2cd45ed`）执行者——本报告对其 P0-1 闭环的核验独立于该披露，仅以 F-13/F-16 原文与 v0.2 文本对照为准
- 利益相关声明：本人对加权计票与 disposition 方案无路径依赖（历史轮次未参与 UC-5/6 编写）；未跑现有测试套件（对象为 DRAFT 提案，CODE/TEST NOT_APPLICABLE，与 grok 同口径）
- 未覆盖：v2.5 实施后的 CODE/TEST/OPS 验证（属后续轮次）；win32 平台
