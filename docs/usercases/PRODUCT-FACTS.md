# 产品裁决原文：fact + 锚点

来源：管理员在完善 UC-1 / FAQ 时的原话（2026-08-31～2026-09-01）。
约定：每条 **fact** 是已裁定的产品结论（陈述句）；**锚点 `quote`** 取原话中的陈述片段，供回写 FAQ / PRD / Schema 时防转义走样。
已吸收进 [FAQ Q5、Q9–Q16](../FAQ.md) 与本目录各 UC；本文件只钉结论，不替代 FAQ 解释。

---

## 一、调度与状态探测

| id | fact | quote（锚点） |
|---|---|---|
| F-1 | 角色状态探测判定的是各席位对应的**任务 FSM 态**（`IDLE`、`CODING`、`READY_FOR_REVIEW`、`WAITING_REVIEW` 等十态之一），不是 CLI 是否安装或空闲。 | 当前状态是IDLE、CODING、READY_FOR_REVIEW、WAITING_REVIEW |
| F-2 | 调度罗盘是任务级 FSM：据此决定通知 reviewer 评审，或等待 executor 继续 coding。各 CLI 自报运行态不能代替该判定。 | 通知reviewer进行review；等待executor继续coding |
| F-3 | UC-1 的 2.h / 2.i 按探测任务 FSM 的口径编写。 | 按探测FSM的口径改 2.h / 2.i |
| F-4 | 项目态是唯一 FSM；各角色「状态」是该任务态上的投影。`READING_MSG` 不单列为角色态；`REVIEWING` 不是第十一任务态；`CONSENSUS_CHECK` 时专家未完成任务；`MERGING` 合入的是 git，不是「合并评审意见」。管理员原表见第三节，以本条为准。 | 执行者写好评审申请，agmsg发给评审专家，等待评审结果 |
| F-5 | 一份评审结论含总体是否通过，以及若干修改意见或问题点；不同模型给出的问题点可以不同。这些意见以**标题清单 + 正文索引**进入 `vote_result.json`（见 F-8b），全文仍在 `docs/reviews/`。 | 一个评审结论中，除了是否采纳，还有若干条修改意见，不同模型评审结果中的修改意见（或者说发现的问题点）可能不一样 |

---

## 二、编排器边界、产物分层与计票

| id | fact | quote（锚点） |
|---|---|---|
| F-6 | `macao init` 无法唯一判定任务态时，向管理员确认，禁止猜测。 | 如果编排器无法判断的时候，可以问用户（管理员） |
| F-7 | 评审方法以 `docs/MACAO_REVIEW_GUIDELINES.md` 为准，`docs/reference/*.md` 为方法来源；过程留痕只写入 `docs/reviews/*.md`。 | 评审流程参考 docs/MACAO_REVIEW_GUIDELINES.md 及 docs/reference/*.md，评审过程要留痕（docs/reviews/*.md） |
| F-8 | agmsg 的主用途是通知其他 team agents，不是全文库，不是 FSM 事实源。 | agmsg主要用来通知团队其他agents |
| F-9 | 编排器不承担项目规划与任务分解；由编排器「负责 task create」并理解整体规划属于过度介入。 | 需要了解整体项目规划及任务分解，这会过度介入到项目开发流程中 |
| F-10 | 编排器不撰写评审申请摘要；`REVIEW_REQUEST` 只投递执行者已写好的信封。 | 编排器负责"发 REVIEW_REQUEST"，也需要编排器了解项目评审申请摘要，相当于编排器要了解项目内容 |
| F-11 | 编排器不裁决哪些意见采纳。计票是规则函数；采纳是执行者的内容工作。 | 编排器"写vote_result" ：需要编排器了解评审内容，并能合理裁决哪些意见采纳哪些不采纳 |
| F-12 | 编排器是不接入模型的规则响应系统，不介入项目开发内容；即使以后接入模型，也不过分介入开发。 | 编排器在早期被设计为不接入AI模型的基于规则的响应系统，是无法完成介入项目开发内容的，即使接入了AI模型，也不建议过分介入开发 |
| F-13 | 执行者撰写评审申请。评审者按 GUIDELINES 撰写评审结论：结论为是否通过，证据为问题列表或建议列表。执行者汇总各份结论：摘录各份「是否通过」供加权计票；把问题或建议的标题清单、正文索引、发现该问题的专家、严重性、是否采纳写入 `vote_result`。执行者不写 `decision`，只做汇总。 | 是由执行者负责撰写评审申请；评审者写评审结论，结论根据评审原则分为结论（是否通过）和证据（具体问题列表或建议列表）；执行者汇总所有评审结论；执行者不写decision，只是汇总 |
| F-14 | agmsg 正文有体积上限，只存放摘要；评审申请与评审结论的全文放在 `docs/reviews/`。 | agmsg的消息正文有大小限制，只适合存放摘要信息，这也是为什么 docs/reviews/ 存在的原因（下面有评审申请和评审结论的全文） |
| F-15 | `*.dev.yml`（评审申请信封）和 `*.review.yml` 只存放摘要；全文保存在 `docs/reviews`。 | *.dev.yml(评审申请)和 *.review.yml 只存放摘要，全文仍然保存在 docs/reviews 里 |
| F-16 | 不同模型的评审细致程度不同，不能仅按票数决定总体是否通过；在 `macao.yaml` 为席位配置 `vote_weight`，某些模型可以获得更大权重。权重只作用于总票；单条意见是否采纳仍由执行者在汇总段标明。 | 不同模型的评审细致程度不同，简单按票数来决定是否采纳不够科学，需要增加一个权重，某些模型可以获得更大的权重 |

---

## 三、状态对照：管理员原表与裁定

管理员给出的项目态 / 角色态对照如下（陈述摘录自原表）。

| 项目状态 | 执行者 | 评审专家 | 原表备注 |
|---|---|---|---|
| IDLE/DONE | IDLE/DONE | IDLE/DONE | 无任务、上一个任务完成了；执行者等待任务；评审专家等待评审 |
| CODING | CODING | IDLE | 执行者进入编码状态；评审专家等待评审 |
| READY_FOR_REVIEW | READY_FOR_REVIEW | IDLE | 执行者写好评审申请，agmsg发给评审专家，等待评审结果 |
| WAITING_REVIEW | WAITING_REVIEW | READING_MSG | 执行者等待评审结果；评审专家读取agmsg信息 |
| REVIEWING | WAITING_REVIEW | REVIEWING | 执行者等待评审结果；评审专家评审中 |
| CONSENSUS_CHECK | WAITING_REVIEW | DONE | 撰写完评审结论，并用agmsg通知执行者 |
| MERGING | READING_MSG | IDLE | 合并评审意见；执行者读取agmsg信息及对应的评审文档，总结评审结论 |
| 评审未通过后的 CODING | — | — | 评审不通过，继续coding（订正问题） |
| 评审通过后的 DONE | — | — | 评审通过，则前一个任务完成 |

**裁定（覆盖上表中与 F-4 冲突的格子）：**

- 库内只有一个 `tasks.state`；上表「角色状态」一律视为投影，不另存第二套 FSM。
- 读 agmsg 是通知送达的一瞬，不把 `READING_MSG` 列成角色态。
- `REVIEWING` 只表示专家在 `WAITING_REVIEW` 下尚未交票，不是独立项目态。
- `CONSENSUS_CHECK` 时双方等待计票结果；专家交票不等于任务 `DONE`。
- `MERGING` 执行 Fast-Forward 合入 git；筛选意见、总结采纳发生在 `REWORK`，由执行者写入 `vote_result` 汇总段。
- 评审未通过进入 `REWORK`（须新 commit），再回到编码；评审通过且合并完成进入 `DONE`。

---

## 四、落地指针

| fact id | 主要落点 |
|---|---|
| F-1～F-4、F-6 | `docs/usercases/UC1-init-glm.md` 2.h / 2.i；FAQ Q9、Q12、Q16 |
| 第三节对照与裁定 | FAQ Q12 |
| F-7、F-8、F-14、F-15 | FAQ Q11、Q14、Q16；UC-3 / UC-4 |
| F-9～F-13 | FAQ Q5、Q10、Q13、Q15；UC-2 / UC-5 / UC-6 |
| F-5、F-16 | FAQ Q15；UC-5 `issues_index` + `vote_weight`；UC-6 `issues_summary` |
