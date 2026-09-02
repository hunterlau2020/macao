# 全量用例体系（UseCases）PRD v2.5 对齐复审（基线 `a0123e8`）评审结论

- **评审日期**：2026-09-02
- **评审人**：qwen（独立评审）
- **评审对象**：`2026-09-02-review-request-a0123e8-UseCases-v2.5-Alignment.md`，钉死 `a0123e8`
- **结论**：**授予用例文档体系 L1 DOC-ALIGNED / PG-0（轨 B）。** 本人 4027cce 轮 2 项 BLOCKING：B-1（UC-8 纯本地模式三真源）完全闭环，B-2（D-6 门禁）表面锁闭环、权重算术本体受设计同步轨阻断项牵连（P2 登记）；用例正文与 PRD v2.5 权威表、契约、事实源逐项一致，无新 P0/P1。
- **结构化 issue**：`BLOCKING` × 0、`ADVISORY` × 4（P2×2 / P3×2）

## 1. 前序轮本人阻断闭环核验

| 项 | 独立复验 | 判定 |
|---|---|---|
| B-1 UC-8 纯本地模式不可表达 + 根配置非法 + §14.5 无本地分支 | ①`remote_name: null` 契约 **ACCEPTED**（探针）；②`macao_config_local_only.yaml` 正例合法；③根 `macao.yaml` 校验 **VALID**；④PRD §14.5 Gate 1 远端 `ls-remote` fail-closed / 纯本地显式 `null` 双分支在位（:1505-1507）；⑤UC-8 六关卡与 §14.5 语义同序——三真源写成同一条边 | ✅ CLOSED |
| B-2 D-6 两门禁契约可关 | `dictator_cap_enabled: false` → REJECT；`minimum_winning_seats: 1` → REJECT；invalid fixtures `macao_config_dictator_cap_false` / `minimum_seats_one` 16/16 拦截套件内。**权重算术 ∀i 3w_i<2W 仍无校验**——设计同步轨 B-1'（P1），本轨按牵连登记 P2（A-1） | ⚠️ 表面锁闭环 |

## 2. 申请 §1 四项修复独立核验

| 声明 | 独立复验 | 判定 |
|---|---|---|
| 1. UC-8 `remote_name: null` 全链路 | 见 §1 B-1（五步全验） | ✅ |
| 2. UC-1 移除 `min_effective_votes`，统一 `seat_quorum_required` | 两份 UC-1 文档 grep 0 命中；`macao_config.schema.json` 无该字段（探针）；单一事实源成立 | ✅ |
| 3. UC-5/UC-10 反支配硬约束 | Schema 层两把锁实测拒绝（§1 B-2）；UC-5 :76/87 与 UC-10 体检项表述与契约同文 | ✅（算术本体见 A-1） |
| 4. 13 份用例 0 控制字符 + 内嵌示例过契约 | 字节级扫描 13/13 clean；UC-6 处置示例/UC-3 dev 示例/UC-1-gemini 配置示例经仓库验证器复跑通过；92/92 含 `test_prd_snippets_schema` 2/2 | ✅ |

## 3. 用例 ↔ 权威基准逐册抽验

- **UC-2/3/4**：E1/E2/E6 触发与产物单写者表述与 §3.3/§3.4 同文；UC-3 返工"拓扑单调前进新 commit"与清单 E6 `merge-base --is-ancestor` 一致 ✓
- **UC-5**：五重纯整数门禁公式与 §2.3 逐项一致；DEADLOCK 即时落盘 + HOLD 与 §3.3/场景三一致 ✓
- **UC-6**：五类处置枚举、`requires_new_checkpoint` 布尔、FINAL 穷尽覆盖、E5a/E6 分流与 §2.5/§3.3 一致；**示例缺 `vote_result_ref`**（见 A-2）
- **UC-7**：五选项闭合、E7 源态 `CONSENSUS_CHECK` 系、`admin_override.json` 不可变语义与 §3.3 :881 一致（无"或 REWORK"残留）✓
- **UC-9/10**：timeout `source:"timeout"` 计入 accounted 且排除 E_N/E_W、迟到票隔离；doctor 只读体检——与 §6.2/§14 一致 ✓
- **符号链接**：`docs/usecases -> usercases` 在位 ✓

## 4. ADVISORY（P2/P3）

- **A-1（P2，跨轨牵连）**：UC-5/UC-10"违反独裁帽 → `validate_config` 期拒绝"的承诺，在权重算术校验落地前仅半可执行（依赖设计同步轨 B-1' 修复）；用例文本本身正确表达 v2.5 规格，不阻断本轨
- **A-2（P2）**：UC-6 规范示例缺 `vote_result_ref`，与 PRD §2.5 :676 示例及提案 :186 不一致（与契约 required 修复同批补齐，见设计同步轨 B-2'）
- **A-3（P3）**：UC-8 六关卡与 §14.5 五步编号映射注记（连续三轮登记，语义无歧义）
- **A-4（P3）**：申请"92/92"为 L1 文档轮机验，不得外推为 L2 代码证明（与 grok 同口径备注）

## 5. 定级意见

**授予轨 B L1 DOC-ALIGNED / PG-0。** 判据核对：13 份用例与 PRD v2.5/契约/事实源字段级可对照且无矛盾（A-1/A-2 为跨轨牵连与示例级残留，不构成用例体系内部矛盾）；全部内嵌示例可解析过契约；P0/P1 为零。与面板关系：claude/grok 同授（本轨第 3 张授予票）；codex REJECT 的三项证据均指向契约/配置/信封等**设计同步轨交付物**，除 UC-6 示例（已列 A-2）外不涉用例正文——分歧如实登记，不以票数代替证据。注意：设计同步轨未授予，Phase 1 实施准入仍以该轨闭环为前提，本轨授予仅认证用例文档体系。

## Reviewer 自审记录

- 上轮 B-2 探针止于表面锁，本轮补权重反例后发现算术本体未校验——按"锁的覆盖范围穷举"纪律牵连登记（同设计同步轨报告自审）
- UC-6 示例缺字段为本人逐块比对 PRD §2.5 示例时发现，非转引
- 92/92、16/16、0 diff 均本机复跑，未采信申请粘贴值；未覆盖：win32、Phase 1 实现
