# 后端评审指南 (Backend Review Guide)

> 目的:为下一轮代码评审划清**待评审范围**与**评审重点**。
> 配套:`review/CODE_REVIEW.md` / `review/CODE_REVIEW_2026-07-28.md` 记录上一轮已发现并修复的缺陷;本文档面向"尚未评审/需复核"的部分。
> 基线日期:2026-08-18 (评审修复后) · 123 tests · FastAPI + SQLAlchemy 2.x + MySQL 8 (测试用内存 SQLite)
>
> 复核说明 (2026-08-17):`review/CODE_REVIEW_2026-07-28.md` 复审遗留的 3 条
> (P1 掌握层级越界 / P2 兑奖并发 / P2 PK 公开结算) **均已修复**,下文相应条目已标注。
> 新发现缺口:PK 结算 job 是占位 stub,结算目前不会执行 (见 §2 P2)。
>
> 变更记录:
> - 2026-08-19: P4 NPC 人设条目更新 —— `assert_persona_safe` 改站外联系/线下接触类黑名单;词数分档截断;9 条行为红线 (EMAIL_AI_ASSISTANT 评审裁决)。笔友 AI 助手本轮变更见 `reviews/2026-08-19-review-request-*.md`(待提交)。
> - 2026-08-17 (二): 基线更新至 118 tests;笔友模块本轮大改 (信箱式 UI/主题题库/60s 延迟回信/广场隐私),
>   本轮变更的评审申请见 `reviews/2026-08-17-review-request-1f26a97.md`;
>   `reviews/2026-08-17-srs-alignment-review.md` 的处理结论已追加于该文末尾。

---

## 0. 评审原则 (Principles)

1. **证据先行**:每条发现必须给出 `file:line` 定位与可复现的反例输入或调用序列;没有证据的"闻起来不对"写入疑问清单,不占缺陷条目。
2. **分级看影响,不看观感**:
   - **P0** = 越权/跨用户数据泄露、应用无法启动、儿童隐私外泄;
   - **P1** = 数据完整性破坏 (重复发奖、状态机错乱)、注入面、API 契约破坏;
   - **P2** = 并发竞态、边界/算法正确性、仅在特定条件下触发的问题。
   与 §2 的优先级排序一致;拿不准时降一级并注明理由。
3. **区分缺陷与决策**:§1.2 的已知简化是**已接受的 MVP 边界**,不记为缺陷;认为不可接受时单列为"决策项",说明业务代价,不与缺陷混淆。
4. **验证修复,而不是重复发现旧缺陷**:文中标注"已修复"的条目,评审动作是**构造反例去击穿修复** (如并发双扣、越界层级),而不是把原缺陷再报一遍。修复声明必须附带回归测试才算数。
5. **儿童安全语境加权**:用户是儿童。提示注入、NPC 人设约束、PII 最小化、内容适当性在本项目权重高于一般应用;凡涉及儿童内容出库到外部 LLM 的路径,授权必须先于调用。
6. **可复现性**:发现须附验证方式 (pytest 用例或 curl 序列);"测试通过"的声明要能在干净环境重跑 (注意共享 venv 可能缺 `pytest-cov`,历史教训见 `review/CODE_REVIEW_2026-07-28.md`)。
7. **范围纪律**:只评 §1.1 范围内的后端;STT、`.apkg`、浏览器推送、即时评分延迟等客户端职责不判后端缺陷。
8. **Required action 要可落地**:每条发现给出最小可行修复方向;若接受权宜之计 (如单进程下可容忍的竞态),必须写明"生产化前需补什么",而不是一句"可接受"。

---

## 1. 待评审范围 (Scope)

### 1.1 在评审范围内 (In scope)

整个 `backend/` 后端,约 20 个路由分组、54 张表、21 个功能子模块 (FR-1~21):

- `app/api/v1/endpoints/` — 所有 HTTP 端点(鉴权、入参、响应一致性)
- `app/services/` — 业务逻辑(正确性、副作用、事务)
- `app/models/` — 7 组数据模型(字段、约束、外键、JSON 列)
- `app/seed/` — 词库 ETL (`vocabd.py` / `words.py`) 与种子装入
- `app/core/` — 枚举、安全原语 (`security.py`)、时间
- `tests/` — 测试充分性与 e2e

### 1.2 不在本次范围 / 已知简化 (Out of scope / known simplifications)

评审时请将这些视为**已接受的 MVP 边界**,而非缺陷(如认为不可接受,请单列):

| 项 | 现状 | 备注 |
|---|---|---|
| 前端 | 未实现(API-only) | 原生 JS 前端为后续独立工作 |
| LLM 真实路径 | 未配置 `LLM_API_KEY` 时回退确定性模板 | provider 可配 (`LLM_PROVIDER=anthropic\|openai`);LLM 分支**未被活测试**(OpenAI 兼容路径有 mock 单测);模板分支已测 |
| CEFR 覆盖 | 仅 ~28% 词有真实 CEFR (EVP),其余默认 A2 | 数据缺口,非逻辑缺陷 |
| 家长身份 | 无独立家长登录 | 孩子可确认**自己家庭**的兑奖(家庭级校验已防跨家庭);真正家长身份留 v1.1 |
| 融合课三步 | 统一进一个 submit(写 `user_input` + 可选说 `speak_text`),非 3 个独立子步 | 客户端编排三步 |
| 口语即时反馈 | 客户端本地评分(P95<1s 由前端保证) | 后端做权威评分用于证据 |
| 写作/复述评分 | 复述=关键词覆盖率;写作=产出量启发式 | 真实质量由 LLM 反馈体现 |
| 迁移证据 | 复述/写作 `MasteryEvidence.word_id` 为空(不绑单词) | `MasteryEvidence.word_id` 已改 nullable |
| 连击 (streak) | `User.streak` 未自动更新 | 无 last_active 字段 |
| 数据库迁移 | `create_all` 无 Alembic | 改模型需 `init_db --drop` 重建;现有库不会自动 ALTER |
| STT / `.apkg` / 浏览器推送 | 均为客户端职责 | 后端仅提供 TTS 文本 / Anki TSV / 角标数据源 |
| RemediationTask | 自动生成(pending),但无"完成"流转 | 完成即重新做对应听写/跟读会话 |
| 运行平台 | 开发/生产 MySQL 8 (`mysql+pymysql`);测试固定内存 SQLite | 2026-08-17 已在 MySQL 8.0.33 实测:建库/54 表/23k 词种子/健康检查通过;测试套件仍跑 SQLite |
| 限流 / 认证节流 | 无 | APIKey 已发放但 **scopes 未在任何路由强制** |

---

## 2. 评审重点 (Focus Areas) — 按优先级

### P0 — 授权与数据隔离 (IDOR / 越权)

最高优先级(上一轮 CODE_REVIEW 的主题)。**每一个接受资源 id 的端点都必须绑定 `current_user`。** 请逐条复核 §3 清单,重点关注:

- 跨用户读取:`emails` 线程、`/errors`、`/game/chests`、`/scenario-weeks` 的 week 归属。
- 越权写:`rewards/{id}/confirm|reject`(家庭授权 `_assert_family_access`)、`/parents/{parent_id}/*`(`_assert_parent_access`)。
- 子资源归属链:`session-items/{id}` → `Session.user_id`;`shadow/retelling/writing/{item_id}` → 会话归属。

### P1 — 输入校验与注入

- **LIKE 注入 / 通配符**:`words` 列表的 `theme` 过滤、`scenario` 的场景词匹配用 `cast(JSON, String).like(f'%"{x}"%')` —— 用户输入未转义 `%`/`_`/`\`,可能影响匹配范围(非 SQL 注入,因参数化绑定)。
- **JSON 列写入**:`prompt_json`、`payload_json`、`mastered_dates_json` 等的可信度(均由服务端构造,非用户直传)。
- **Pydantic 边界**:各 schema 的 `min_length/max_length/ge/le` 是否充分(邮件/作文内容上限)。

### P2 — 并发与一致性

- ~~**XP 扣减竞态**~~ **已修复 (2026-08-17 复核确认)**:`xp.spend` 改为原子条件更新 `UPDATE ... WHERE xp >= amount` (`services/xp.py:41-62`);`confirm_redemption` 先做原子状态转换 `PENDING→CONFIRMED` (只有一个并发调用成功),再原子扣 XP、原子减库存 `WHERE stock > 0` (`services/parent.py:72-124`)。下轮评审请**验证修复**而非重新找旧缺陷。
- ~~**奖品库存超卖**~~ 同上,已随 `confirm_redemption` 的原子库存递减修复。
- **PK 结算幂等**:`PKRecord` 已加 `(user_id, week_start)` 唯一约束 (`models/game.py:123`);公开 `/pk/settle` 端点已删除。⚠️ **新缺口**:结算移入 worker 后,`workers/jobs.py:42-46` 的 `pk_settlement` 仍是占位 stub (只打日志,未调用 `pk.settle_last_week`),且调度器默认关闭 —— **结算目前不会执行**,需接线或明确由谁触发。
- **ErrorBook/ReviewLog upsert**:按 `(user,word)` 查询后 insert/update,并发可能产生重复行。`ReviewLog` 有唯一约束兜底 (`uq_review_user_word`);**ErrorBook 仍无唯一约束** (仍未修复)。

### P3 — 算法正确性

- **SM-2**(`services/srs.py`):对照 `SRS_SCHEDULER §4` —— EF∈[1.3,2.5]、失败重置、interval 1/3/n·EF。边界:quality=3 是否算通过、`round(prev_interval*prev_ef)`。
- **掌握推进**(`mastery.py`):相邻层级规则 —— **复审 P1 已修复**:`next_idx = min(cur + 1, tgt)` (`services/mastery.py:226`),每次最多推进一层且不超本次练习目标;回归测试 `tests/test_core.py:87`。下轮复核边界:识别不能直接跳 transfer、重复低目标练习不越界。
- **ERROR-3 跨 3 自然日**:`_mark_good_day` 同日不计、3 个不同日 mastered(目前仅 helper 级单测,未端到端)。
- **ERROR-4 假掌握**:启发式 = `state.layer≥apply 且 combined<60`;是否合理、是否漏报。
- **跟读评分** 60/40(内容+时长)、复述覆盖率、写作产出量 —— 启发式阈值是否合理。

### P4 — 隐私与儿童安全

- **提示注入**:用户文本(邮件/作文/复述/跟读转录)直接进 `llm.chat` 的 `messages`(`feedback.generate`、`penpal.generate_reply`)—— 恶意/意外内容可能影响 LLM 输出。NPC 系统提示是否足够约束。
- **儿童友好反馈**:`feedback.py` 系统提示禁止成人语法术语;LLM 输出经 `_parse`(只取 praises/tip)兜底,但仍信任 LLM 文本。
- **NPC 人设**:`assert_persona_safe` 关键词黑名单(2026-08-19 起改为站外联系/线下接触类;沉浸人设已获评审裁决允许);回复按学习者级别分档硬截断 (原 ≤60 词);system prompt 含 9 条行为红线 (EMAIL_AI_ASSISTANT §5.1)。
- **PII / 儿童隐私**:无生物特征采集;`ParentProfile.notify_email`、用户名等 PII 存储与日志。

### P5 — 测试覆盖缺口

当前 ~87%,但以下几乎未覆盖(评审时判断是否需补):

- `app/workers/jobs.py` / `scheduler.py`(0%)—— 后台 job 仅注册未运行。
- `app/services/llm.py` 真实调用分支(无 key 无法测)。
- `app/seed/loader.py` / `words.py`(xlsx 回退路径)。
- e2e 广度:已有 听写 / 家长兑奖 / 场景周;**缺 融合课三步、PK 结算、NPC 回复(活 LLM) 的端到端**。
- ERROR-3 跨日 mastered 仅 helper 级。

### P6 — 运维与工程

- **无 Alembic**:生产部署的 schema 演进风险。
- **`create_all` 不会 ALTER 已有表**:已有 dev 库改字段需 `--drop` 重建(易踩坑,见记忆)。
- **调度器默认关闭**(`scheduler_enabled=false`):NPC/复盘/PK 结算 job 生产环境需显式开启。公开 `/pk/settle` 端点已删除,但 worker 的 `pk_settlement` job 仍是占位 stub (未调用 `pk.settle_last_week`) —— PK 结算链路当前未接通 (见 §2 P2)。
- **错误处理**:服务层 `ValueError`/`PermissionError` → 端点映射是否一致(403/400/404 语义)。
- **日志**:是否记录足够排错信息(令牌、用户 id);是否泄露敏感信息。

---

## 3. IDOR / 越权复核清单 (Concrete checklist)

逐一确认"接受 id 的端点"都做了归属校验:

| 端点 | 资源 | 应有校验 | 位置 |
|---|---|---|---|
| `POST /session-items/{id}/submit` | SessionItem→Session | `sess.user_id == current_user` | `sessions.py` |
| `POST /sessions/{id}/finish` | Session | `sess.user_id == current_user` | `mastery.finish_session` |
| `POST /shadow/{id}/score` `retelling/writing/{id}/submit` | SessionItem | 会话归属 | 各 endpoint |
| `POST /scenario-weeks/{id}/start-day` `/review` | ScenarioWeek | `week.user_id == current_user` | `scenario.py` |
| `POST /emails/{id}/reply` | Email | `email.sender_user_id == current_user` (用户发给 NPC 的邮件;须**先于** LLM 调用) | `emails.py` |
| `POST /emails/{id}/correction` `/polish` | Email | `email.sender_user_id == current_user` (只能纠错/润色自己发的信) | `emails.py` |
| `POST /emails/{id}/tips` | Email | `email.receiver_user_id == current_user` (**只能基于发给自己的信**取回信建议) | `emails.py` |
| `GET /emails?pen_pal_id&thread_root_id` | PenPal / Email | 带 pal: `_resolve_penpal` owner 校验;**无 pal (R9, 2026-08-22)**: 线程首信参与者授权 (`sender/receiver` 须含 current_user,否则 403) | `penpal.get_thread` |
| `DELETE /pen-pals/{id}` | PenPal | owner 校验 | `penpal.unbind_penpal` |
| `GET /npcs/{id}/profile` | NPC | 属主或已绑定该 NPC 的活跃笔友,否则 403 | `npcs.py` |
| `GET /users/{id}/profile` | User | 本人或活跃笔友,否则 403 (儿童隐私: ID 枚举不可见) | `users.py` |
| `POST /rewards/{id}/confirm|reject` | Redemption→RewardItem | 家庭授权 `_assert_family_access` | `parent.py` |
| `/parents/{parent_id}/*` (5 个) | ParentProfile | `_assert_parent_access` | `parents.py` |
| `POST /game/chests/{id}/open` | ChestDrop | `chest.user_id == current_user` | `game.open_chest` |
| `DELETE /api-keys/{id}` | APIKey | `row.user_id == current_user` | `api_keys.revoke` |
| `GET /errors` `/errors/stats` | ErrorBook | 按 `user_id` 过滤 | `mastery.list_errors` |
| `GET /reviews/due` `/notifications/due` | ReviewLog | 按 `user_id` | `srs`/`notifications` |

> ⚠️ 任何"只校验认证、未校验资源归属"的端点都是 P0 缺陷。
> **工程约定 (2026-08-30 评审裁定新增)**:
> 1. **禁止裸 SQL 写 `pen_pals`** —— 好友关系的创建/变更/复活必须走
>    `bind_penpal`/`unbind_penpal` (全部业务守卫) 或受审计的管理脚本
>    (`scripts/add_friend.py`);旁路写入是儿童保护的绕过面
>    (产品裁决后无运行时兜底,见 backend/README (二十三) §1.4)。
>    已知合法旁路仅一处: 信箱惰性补齐 (`penpal.mailbox`,历史信件对,
>    `admin_authorized=False`)。
> 2. **枚举列裸 SQL 比较须用成员名** —— `SQLEnum` 存枚举**名**
>    (`ADULT`/`PRIMARY`),不是值 (`adult`/`8-11`);(二十一) 迁移的
>    `age_band='adult'` 永假缺陷即由此而来 (已移除,前车之鉴)。

---

## 4. 复现与运行

```bash
cd backend
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements-dev.txt
cp .env.example .env
# 启动本机 MySQL 8: C:\mysoft\mysql-8.0.33-winx64\start_server.bat (默认 root 无密码)
# 词库:需自备 data/dist/vocabd.business.db (已 gitignore;来自 english_job 发行库)
.venv/Scripts/python -m scripts.init_db --drop --seed   # 自动建库 (utf8mb4) + 建表 + 导入 23k 词
.venv/Scripts/python -m pytest                           # 104 tests (内存 SQLite,无需 MySQL)
.venv/Scripts/python -m uvicorn app.main:app --reload    # http://127.0.0.1:8000/docs
```

- 未配置 `LLM_API_KEY` 时,NPC 回复与写作反馈走模板 (LLM 分支未活测)。
- 改模型后必须 `init_db --drop` 重建(`create_all` 不 ALTER 已有表)。

---

## 5. 建议的评审产出

- 新发现按 `review/CODE_REVIEW.md` 的格式记录(P0/P1/P2 + Location + Required action)。
- 对 §1.2 中"已知简化"若认为不可接受,单列为决策项而非缺陷。
- 优先级:P0(授权/数据隔离)> P3(算法)> P2(并发)> P1(注入)> P4(安全)> P5(测试)> P6(运维)。
