# MACAO L3/PG-2 终局定级复审 独立复审结论（qwen）

- **评审日期**：2026-08-30
- **评审人**：qwen（独立评审）
- **被评审范围**：`3e1a991..7973853`（申请 `2026-08-30-review-request-L3-PG2-Final.md` 以移动引用 `HEAD` 界定范围，本报告钉死为 `7973853`，与 claude P3-NEW-10 同判）
- **评审方法**：独立复放——64 测试两轮、`test-clis`/`e2e-run`/`compileall`/`git diff --check` 实机、**17 项自研反例**（E9 全生命周期 11 项：反对票+超时→HOLD→迟到隔离→RETRY→Gen2 全票自动合并→Gen1 证据不可变→g2 另存→审计留痕；20 次轮询幂等；checkpoint 三分支拒绝+两分支探针；codex 作废旧票反例重组）、PRD 权威对照、注册表对账
- **结论**：**支持授予 L3 SCENARIO-VERIFIED / PG-2**（附登记性勘误要求，见 §六）。申请 4 项中 3 项完全闭环、1 项（P1-2）部分闭环且其"Fail-closed"表述被证伪；本人两轮追踪的 P1-Q3（E9 代际毒化活锁）在 HEAD **回归验证真实闭环**；按本报告独立定级尺度，当前**无存续 P0/P1**。与 claude（REJECT，P1-NEW-11）、codex（REJECT，7 项 P1）存在定级分歧，逐项举证于 §五。

---

## 一、申请清单 4 项逐条独立复验

| 编号 | 申请声明 | 独立复验结果 | 判定 |
|---|---|---|---|
| **P1-NEW-9** | E9 代际归档防覆写：哈希异动以 `g{gen}_{name}` 另存 + `ARTIFACT_ARCHIVED` 审计 | **动态属实**：Gen1 反对票（`GEN1-DISSENT`）经 E9 归档后，Gen2 共识归档不覆盖——Gen1 文件逐字留存、Gen2 差异票另存为 `g2_codex.review.yml`、`ARTIFACT_ARCHIVED` 7 条含代际/路径/SHA256；`_get_generation` 以本轮派发审计计数，代际锚点时序正确（派发审计晚于 E2/E9 转移，归档计到当前代） | ✅ VERIFIED |
| **P2-NEW-4** | RETRY_REVIEW 后清理活跃 `vote_result.json` | **动态属实**：E9 归档+重派发后活跃目录无 `vote_result.json`——崩溃重建不再被残留 E9 裁定误导回退 `WAITING_REVIEW` | ✅ VERIFIED |
| **P3-NEW-7** | `LATE_REVIEW_ISOLATED` 代际内幂等 | **动态属实**：超时+迟到票后连续轮询 20 次，审计严格 1 条（`already_logged` 以 `sequence_id >= latest_dispatch_seq` 代际门槛） | ✅ VERIFIED |
| **P1-2** | `check_development_checkpoint` "强校验"+"不合规清单 Fail-closed 拒绝转移" | **部分属实**：显式非法值三分支（`tests_passed: false` / 伪造 commit / `signal: IMPLICIT`）均正确拒绝（本报告 C1-C3 独立复现）；但**字段缺失走宽容默认**：`data.get("signal", "EXPLICIT")`、`quality.get("tests_passed", True)`——缺 `signal`、缺 `quality_metrics` 乃至仅 4 行的最小清单**均被接受**并驱动 FSM 进入 `READY_FOR_REVIEW`（本报告 C5 探针独立命中，与 claude §3.1 一致）；`version` 未校验、未调用 schema 校验（STATUS"严格 Schema"表述不实）。**"Fail-closed"声明在"字段缺失"维度被证伪** | ⚠️ PARTIALLY_VERIFIED（附声明证伪登记） |

## 二、跨轮追踪项闭环验证（本人 提出/追踪）

| 项 | 验证 | 结果 |
|---|---|---|
| **P1-Q3**（E9 重试代际毒化活锁，bf5ae2d 轮本人提出，3e1a991 声称闭环） | **HEAD 生产路径全周期回归**：1 反对+1 超时 → HOLD → 迟到票隔离不越界 → `RETRY_REVIEW`（重派发 disp=2）→ **Gen2 全员按时全票赞成 → `resolution=automatic` 自动 APPROVED → MERGING** | ✅ 真实闭环（`latest_dispatch_seq` 代际解绑生效，无活锁） |
| **P1-Q2**（迟到票越界，f41b9da 轮） | A2 复验：HOLD 后迟到票仍无法自动合并 | ✅ 保持闭环 |
| GOV-1（注册表冒名，7935da3 轮提出） | 注册表无冒名残留；本轮 3 份同行报告命名正确 | ✅ 保持闭环 |
| R1 Schema 寻址（六轮追踪） | bf5ae2d 轮闭环，本轮保持 | ✅ |
| P2-CARRY-1（ANSI 硬编码，claude 四轮追踪） | `integ_harness.py:110` 现为正则真实检测（`ANSI_ESCAPE_RE` 逐行断言），test-clis 4/4 ANSI=YES 为实测值 | ✅ 3e1a991 已闭环 |

## 三、机验独立复放

| 项目 | 结果 |
|---|---|
| 64 项测试 ×2 | Ran 64 / OK ×2（15.56s / 15.65s） |
| `compileall -q src` | exit 0 |
| `git diff --check 3e1a991..7973853` | exit 0 ✓ |
| `test-clis` | 4/4 PASS（claude 2.1.251 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22），ANSI 列为真实检测值，0 僵尸 |
| `e2e-run` | 7/7 OK、终态 DONE、产物归档一致 |
| 自研反例 17 检查 | 产品侧 17/17 通过（其中 C5 为宽松默认观察项，非缺陷断言；另 2 处初次 FAIL 系本人脚本 yaml/补丁构造错误，单独复跑排除，见 §八） |

## 四、codex"作废旧票参与新共识"反例独立重组

复现构造：Gen1 codex 反对 + opencode 超时 → HOLD → E9 重试 → **codex 端重写其 Gen1 反对票**（无新评审）+ opencode 新赞成 → collect 结果：**1:1 → Deadlock → HOLD（fail-safe，不自动合并）**。YES 侧组合（stale YES + fresh YES → 自动合并）与"评审者重投相同票"在信息论上不可区分——manifest 协议不携带派发代标识（无 dispatch_id 字段），系统无法也不应猜测写入门意。且 E9 保持同 checkpoint_ref/round，旧票评的是同一对象。**本报告定级：P2（协议设计登记），不构成自动推进至 MERGING 的现实缺陷**——与 codex 定级分歧见 §五。

## 五、定级分歧登记（独立举证，不随票）

| 项 | 他方定级 | 本报告定级 | 举证 |
|---|---|---|---|
| 缺字段宽容默认（claude **P1-NEW-11**） | claude：P1 阻断 | **P2** | (1) 不产生不安全终态：缺字段清单进入评审后，Reviewer 共识与人工接管仍是安全边界，`tests_passed` 本身为执行者**自报**字段（谎报 `true` 与缺失同效），硬安全增益有限；(2) 属输入门质量/规范卫生，非状态机安全违约——与本人 bf5ae2d 轮对同类项（kimi P1-2）的 P2 定级一致，无新证据支持升级；(3) 全体仓库测试与 e2e 夹具均依赖最小清单，宽容默认是有意的向后兼容，正确修法是 schema 必填校验+夹具合法化（kimi 3e1a991 轮验收标准），随下轮补齐 |
| 同上（kimi **P3-1**） | kimi：P3 | **P2** | 声明方向性错误（"Fail-closed"实为缺字段维度 Fail-open）+ 第四轮遗留 + STATUS"严格 Schema"失实——严重于普通 P3，须勘误+补修 |
| codex P1-1（manifest 无代际绑定） | codex：P1 | **P2** | §四：reject 侧 fail-safe；YES 侧不可区分于合法重投；协议增强（dispatch_id 入 schema）登记为设计项 |
| codex P1-3/4/5/6/7 及 timeout 生产驱动（连续多轮） | codex：P1 | **P2** | 维持本人历轮定级与理由（本地 SQLite 故障窗、远端不确定态可人工恢复、物理消费语义历史登记、真实 Adapter 属 PG-3 联调、扫描器属 OPS），记录于 bf5ae2d 轮 §五，本轮无新证据 |
| kimi P2-1（PRD §6.1 ping 流程与实现不一致） | kimi：P2（建议改 PRD） | **同意 P2**，倾向 PRD 勘误（现行为"超时→HOLD+人工接管"更保守且已有全场景证据；ping/30m 窗口列 PG-3） |

## 六、P2/P3 登记（不阻断定级）

1. **P2**：`check_development_checkpoint` 缺字段宽容默认 + `version` 未校验 + 未调 schema（§一 P1-2 行）——修复方向：required 字段严格化 + `version` 校验 + 测试夹具 schema 合法化；
2. **P2**：manifest 协议无派发代标识（§四）——设计增强项；
3. **P2**：codex 历史系（publish 事务边界、push 后远端不确定态、产物物理消费语义/git 提交、真实 Adapter 消费链）；
4. **P3**：申请/STATUS 两处表述勘误（**登记性前置，见下**）；申请范围用移动引用 `HEAD`（P3-NEW-10，本报告已钉死）；`audit_events` 无索引（claude P3-NEW-5）；Schema 环境变量单测未断言可加载（claude P3-NEW-9）。

**登记性前置（不阻塞定级，但须随下次文档提交完成，逾期按治理项升级）**：STATUS.md 将 P1-2 行"严格 Schema 与 commit 校验"更正为"显式值强校验 + commit 物理存在性校验；缺字段默认放行（P2 登记待补）"，申请文档勘误"Fail-closed 拒绝转移"的适用范围。

## 七、定级判定

**支持授予 L3 SCENARIO-VERIFIED / PG-2。**

- GUIDELINES §2.1 L3 判据逐项：全同意（e2e+测试）、1:1 僵局（本人重组复现）、超时/弃权（A1-A2 生产路径）、崩溃恢复（P2-NEW-4 修复后 reconcile 不再误回退）、返工循环（max-round HOLD 跨轮闭环）、**E9 重试两代际**（本人 11 项全周期复现：HOLD→隔离→重派→Gen2 自动共识→Gen1 证据不可变）——均有可复现 TEST/独立复放证据；
- 本报告独立定级尺度下 P0/P1 为零（§五逐项举证的分歧均维持 P2 并附理由）；PG-1/PG-2 条件满足；
- 过程事实：本人连续五轮提出/追踪的 P1（P1-Q2/P1-Q3）与 R1/P2-CARRY-1 等项均真实闭环，本轮申请无治理虚报（P1-2 表述失实已按证据登记并要求勘误，非主观造假模式）；
- 提请委员会注意：本支持票与 claude/codex 的 REJECT 构成分歧，分歧焦点（§五前两行）均已给出可复现证据与定级理由，供终局裁定参考。

## 八、全量对账声明

`reviews/` 目录现有 **61 份结果在盘**（58 份已提交 + 本轮 3 份同行未入库报告：claude/codex/kimi）+ **12 份申请**；申请所称"58+12"与提交态一致 ✓；STATUS:39 本轮行"待专家评审"待补 4 份（含本报告）。3e1a991 轮 3 份（claude 219 行 REJECT / codex 190 REJECT / kimi 112 授予）已入库。本报告为本轮（7973853）第 4 份。

## Reviewer 自审记录

- 独立性：本轮先完成全部 17 项自研复放与机验后，才读取 3 份同行报告的结论段用于共识登记；C5 宽松探针在读取 claude 报告前已命中
- 本人脚本两次假 FAIL（Mock issue 对象 schema 字段不符、字符串补丁未命中致 C1 误带 dispatch）均已单独复跑定位排除，未进入任何结论；教训：对 setup 复用函数的参数变更应逐调用点核对
- P1-Q3 回归采用生产自动检测路径（真实 1s 时钟 + 无参 collect），不复用仓库测试的显式传参路径（claude 3e1a991 轮指出的同一盲区）
- 分歧逐项举证（§五），含对本轮同行 REJECT 结论的不采信理由；未以票数代替证据
- 利益相关声明：P1-2 残留与本人在 bf5ae2d 轮"随下轮补齐"的登记相关，定级维持 P2 与历史一致，非为新护短
- 未覆盖：真实远端 push、真实 LLM 评审质量、Windows、多任务并发同一 checkpoint
