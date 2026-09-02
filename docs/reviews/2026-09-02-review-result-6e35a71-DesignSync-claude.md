# PRD v2.5 产品方案与技术设计同步 独立评审结论（Round 2，`6e35a71`）

- **评审日期**：2026-09-02
- **评审人**：claude
- **评审对象**：[`docs/reviews/2026-09-02-review-request-PRD-v2.5-Design-Sync-r2.md`](2026-09-02-review-request-PRD-v2.5-Design-Sync-r2.md)
- **申请声称基线**：`6e35a71`；**工作区 HEAD**：`12a05e2`（差量 = 两份 r2 申请文件 + `STATUS.md`，被审正文与 `6e35a71` 同）
- **本人前序票**：`0bc6247`（NO_APPROVE，P0×2+P1×8）→ `2766c69`（NO_APPROVE，P1×2）→ `2da1bc2`（NO_APPROVE，P1×3）→ `caf3473`（NO_APPROVE，P1×5，用例轨）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §2/§3/§5/§6/§8/§9；`docs/PRD_CHANGE_PROPOSAL_v2.5.md` §2（D-1～D-9）；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **申请定级**：L1 DOC-ALIGNED / PG-0

## 结论

**`NO_APPROVE`。** 机器票不得为「有条件通过」（PRODUCT-FACTS F-17）。

前四轮的全部阻断项在本基线上**确已闭环**，且本轮无回退：PRD §2.1/§2.2/§2.3/§2.5/§5.2/§13 六处规范示例全部通过其自称的机器契约（历史 P0-2 → N-6 → M-1 那条「权威文档与其自称契约互斥」的复发链，本轮**首次断开**）。这是四轮以来最实质的进展。

但本轮我在**此前未被任何一方检查过的三个面**上取得了新的阻断级证据：

1. `macao.yaml` 的 `policy` 配置面**不是** D-6 五重门禁的那套参数——机器契约允许把两道反支配门禁双双关掉（P1-1，附可复算反例）；
2. PRD 自身对合并流水线的**关卡顺序**给出了两个互斥版本（P1-2）；
3. 返工检查点的拓扑守卫在 PRD / 变更清单 / 用例 / 现有代码之间有**四种强度**（P1-3）；
4. 交付物 #9（`STATUS.md`）自身的计数三处互斥、双向对账不平（P1-4）；
5. `review_disposition` 契约未实现提案明文规定的枚举联动，`DEFERRED` / `REJECTED` 可翻转 E4/E5a（P1-5，与 Codex 独立收敛）。

P1-1、P1-2、P1-5 属于「按权威文档实现会得到错误安全语义」，不是文字瑕疵；建议在颁发 PG-0 前闭环。

**票型说明**：同基线四份报告为 **2 YES（grok、qwen）: 2 NO（Codex `REJECT` P1×8、本报告）**。Codex 与我在五条上独立收敛（详见 §七）。按 GUIDELINES §8「真理不等于投票」，建议以可复跑反例逐条裁定。

用例轨另文出具：[`2026-09-02-review-result-6e35a71-UseCases-claude.md`](2026-09-02-review-result-6e35a71-UseCases-claude.md)。

---

## 0. Reviewer 自审记录（GUIDELINES §9）

### 0.1 本轮被我自己证伪、因而**未**上报的三条假设

诚实登记，因为它们本可以变成三条错误的 P1：

1. **`review_status_vote_conflict.yml` 只因缺 `items` 被拒（负例通过错原因）** ——
   我先看到首条错误是 `'items' is a required property`，怀疑 status/vote 互锁根本没生效。隔离复验：把合法 `items` 补齐后单独跑，仍报 `'YES_APPROVE' was expected`；再跑控制组（`APPROVED`+`YES_APPROVE`+ 无 BLOCKING）→ 0 error。**互锁真实存在，假设撤回。**
2. **`EXEMPTED_BY_ADMIN` 未绑定 `override_id`（`schemas/README.md:24` 声称已约束）** ——
   构造 `disposition_type: EXEMPTED_BY_ADMIN` 且删除 `override_id` 的实例 → **REJECTED**，原因正是 `dispositions/0 -> 'override_id' is a required property`；补回 `override_id` → 接受。**约束真实存在，假设撤回。**
3. **UC-1-gemini 的 `seat_quorum_required: 2 / weight_quorum_required: 2` 违反 $\lceil 2N/3 \rceil$ / $\lceil 2W/3 \rceil$** ——
   实算该文件的团队：$N=3$、权重 $1{+}1{+}1$ 故 $W=3$，$\lceil 6/3 \rceil = 2$、$\lceil 6/3 \rceil = 2$，**两值都对**。PRD §13 示例（$N=3, W=4$）同样自洽。**假设撤回。**

### 0.2 一条只能给出「无数值分歧」而非「无分歧」的结论

对 UC-5 §2.b 残留的浮点「加权占比」（见用例轨 P2-1），我尝试构造与纯整数门禁判定不同的数值反例：穷举 $E_W \in [1,5000]$、$W_{win} \in [0,E_W]$ 共约 1.25×10⁷ 组，`(W_win/E_W) >= 2/3` 与 `3*W_win >= 2*E_W` **零分歧**。所以我只能断言它是**规范歧义**（与 D-6「严禁浮点运算」直接抵触），**不能**断言它会算错票。这条据此定为 P2 而非 P1。

### 0.3 强制自检 5 项

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段声明位置 vs 实际读取位置 | §2.5 / Schema / Layer 1c / UC-6 四方同构 ✓；**但 `policy.*` 声明面与五重门禁读取面不一致（P1-1）** |
| 2 | 「已完成 / 100%」是否等同证据 | 申请 §3 五项机验我逐条重放：4 项 VERIFIED，第 1 项份数 CONTRADICTED（P3-2） |
| 3 | 确定性语言是否标注 | 本报告中「未被拦截 / 被接受」均附实例与运行输出 |
| 4 | 代码块可执行性 | 本报告全部脚本原样贴出，均已实跑 |
| 5 | 每条 P1 是否附路径行号 | 是 |

### 0.4a 本轮漏审登记（由同行报告触发后本机复核确认）

Codex 在同基线出具的报告（`NO_APPROVE`/REJECT，P1×8）里有三条我该查而没查到的：

1. **`macao_config` 根级 `required` 不含 `policy`**（codex P1-3）——我查了 `consensus_rule` 的枚举取值域（并确认它已封闭），却没查**这个键是否一定存在**。检查取值域而不检查必填集，是我上轮「能解析 ≠ 合契约」之后的同一类惯性，登记为**第三条常备检查项：枚举封闭性必须与 `required` 一起看**。已并入 P1-1。
2. **`DEFERRED` / `REJECTED` 的 `requires_new_checkpoint` 联动缺失**（codex P1-4）——我在读申请 §3 的 D-4 行时确实注意到「`requires_new_checkpoint=false`」这句不在 D-4 的权威定义里，但我只往 D-4（提案 `:37`）找，没往提案 §L180-184 的枚举细则找，于是停在「申请多写了一句」，没走到「提案写了、契约没实现」。已作为 P1-5 独立成条。
3. **`dev_manifest` 必填集缺 `checkpoint_ref` / `full_document`**（codex P1-2）——我把该 Schema 的 `required` 打印出来看过，但当时的注意力在 `full_document` 的**子字段**是否齐全，没回头问「这个对象本身必填吗」。已作为 P2-6 登记。

三条我都本机复现后才写入本报告，不是转述。

### 0.5 证据类型适用性（GUIDELINES §3.1）

本轮为 **DOC + SPEC**；`src/` 仅在 P1-3 作为**反证**引用（现有代码比 PRD 更严），不作为定级证据。TEST/OPS **NOT_APPLICABLE**：86/86 绿灯只覆盖 v2.3.1 引擎，v2.5 计票、E5a、`admin_override` 命令路径在变更清单中仍标「待实施」，与 L1 无关。

---

## 一、申请 §3 自动化结论：独立重放

全部**不采信自述**，本机重跑：

| 申请声明 | 本机结果 | 判定 |
|---|---|---|
| 179 份 Markdown、0 控制字符 | **0 控制字符**（按字节扫 `0x09/0x0b/0x0c/0x0d`）；**份数复现不出 179**：`git ls-tree -r 6e35a71 \| grep .md` = **167**，`find docs` = 172，`find -L docs`（跟随 `usecases` 软链）= 185 | 结论 **VERIFIED**；份数 **CONTRADICTED**（P3-2） |
| UC-6 / UC-3 / UC-1-gemini 示例 Draft-07 PASS | 抽出三处围栏 → `review_disposition` / `dev_manifest` / `macao_config` 各 0 error | **VERIFIED** |
| 正例 8/8、反例 7/7 FAIL-CLOSED | 8/8 通过；7/7 被拒，且**逐条打印拒绝原因**确认拒的是名义约束 | **VERIFIED** |
| `docs/schemas/` vs `src/macao/schemas/` 逐字节一致 | 8 份同名契约 `cmp` 全 SAME | **VERIFIED** |
| 86/86 OK；`compileall` 0 Errors | `Ran 86 tests ... OK`；compile 退出 0 | **VERIFIED** |

**额外补跑（申请未做）——PRD 正文规范示例 vs 其自称契约**：

```bash
python3 - <<'PY'
import re,json,yaml,jsonschema,glob,os
S={os.path.basename(p).replace('.schema.json',''):json.load(open(p)) for p in glob.glob('docs/schemas/*.schema.json')}
lines=open('docs/MACAO_PRD_v2.md').read().split('\n')
def sect(a_re,b_re):
    a=b=None
    for i,l in enumerate(lines):
        if a is None and re.match(a_re,l): a=i
        elif a is not None and re.match(b_re,l): b=i; break
    return '\n'.join(lines[a:b])
for s_re,e_re,sch in [(r'^### 2\.1 ',r'^### 2\.2 ','dev_manifest'),
                      (r'^### 2\.2 ',r'^### 2\.3 ','review_manifest'),
                      (r'^### 2\.3 ',r'^### 2\.4 ','vote_result'),
                      (r'^### 2\.5 ',r'^## 第三部分','review_disposition'),
                      (r'^### 5\.2 ',r'^### 5\.3 ','review_context'),
                      (r'^## 第十三部分',r'^## 第十四部分','macao_config')]:
    for lang,f in re.findall(r'^```(yaml|json)\n(.*?)^```', sect(s_re,e_re), re.M|re.S):
        o=yaml.safe_load(f); k=list(o)
        cand=[o]+([o[k[0]]] if len(k)==1 and isinstance(o[k[0]],dict) else [])
        n=min(len(list(jsonschema.Draft7Validator(S[sch]).iter_errors(c))) for c in cand)
        print(f"{s_re:22s} -> {sch:20s} errors={n}")
PY
```

输出：**六处全部 `errors=0`**。这是本轮最重要的正面结论——历史上 `0bc6247` P0-2、`2766c69` N-6、`2da1bc2` M-1 是同一类复发缺陷（权威正文的示例通不过自己指定的契约），**本轮首次全部成立**。

---

## 二、本人前序阻断项闭环核验

| 轮次 | 项 | 本轮判定 | 证据 |
|---|---|---|---|
| `0bc6247` | P0-1 §5.2 实例 FAIL(7) | **闭环** | 上表 `review_context` errors=0；`required` 十键与 §5.2 `required_blocks` 十项同名同序 |
| `0bc6247` | P0-2 §2.3 vote_result FAIL(10) | **闭环** | 上表 errors=0 |
| `2766c69` | N-x 五重门禁公式控制字符污染 | **闭环** | 全库 0 控制字节；L332–335 恢复 `\forall` / `\times` / `\lceil` |
| `2da1bc2` | M-1 §5.2 与 `additionalProperties:false` 互斥 | **闭环** | `required_blocks` 已进 `properties`；实例通过 |
| `2da1bc2` | M-2 `consensus_rule` 枚举双值 | **闭环** | 枚举仅 `["weighted_2/3_v1"]`；探针 `'2/3_majority' is not one of [...]` |
| `2da1bc2` | M-3 §2.5 缺 `override_id` | **闭环** | §2.5 含 `override_id`；契约侧 `EXEMPTED_BY_ADMIN ⟹ required override_id` 实测生效（见 §0.1-2） |

**六项全部 VERIFIED 闭环，无回退。**

---

## 三、P1：必须先解决（5 项）

### P1-1　`macao.yaml` 的 `policy` 配置面不是 D-6 的那套参数：整块 policy 可缺席，两道反支配门禁可被关闭

**证据**

D-6（`docs/PRD_CHANGE_PROPOSAL_v2.5.md:39`）与提案 §L410/L414 把两道反支配门禁定为**硬边界**：

- `docs/PRD_CHANGE_PROPOSAL_v2.5.md:410`：「**配置期独裁帽**：$\forall i, 3 w_i < 2W$（**不满足则拒绝启动**）」
- `docs/PRD_CHANGE_PROPOSAL_v2.5.md:414`：「胜方最少席位门禁：$\ge minimum\_winning\_seats$（默认 2，**且 $2 \le minimum\_winning\_seats \le N$**）」
- `docs/FAQ.md:310`：「胜方最少席位：胜方席位数 $\ge 2$（**禁止单席位独裁裁决**）」

机器契约却两条都不编码：

- `docs/schemas/macao_config.schema.json:69`：`"minimum_winning_seats": { "type": "integer", "minimum": 1 }` ——**下界 1**，与提案的 $\ge 2$ 直接冲突，也没有与 $N$ 的耦合上界；`docs/schemas/vote_result.schema.json:70` 同。
- `docs/schemas/macao_config.schema.json:68`：`"dictator_cap_enabled": { "type": "boolean" }` ——独裁帽是一个**可置 false 的开关**。全库无任何一处定义 `false` 时的行为；`docs/v2.5_CODE_CHANGE_INVENTORY.md:65` 把它写成「独裁帽**选项**」，而同文件 `:74` 又写成无条件校验。
- `docs/schemas/macao_config.schema.json:6`：根级 `required` 只有 `["project","team"]`——**`policy` 整块可以缺席**。补测（构造合法 `project.repository` 后）：一份带两名 reviewer、完全没有 `policy`、也没有任何 `vote_weight` 的配置 → **ACCEPTED，0 error**。也就是说申请 §2 第 2 行「`macao_config` v2.5（**封闭为 `weighted_2/3_v1`**）」只在 `policy` 出现时成立；缺 `policy` 时 `consensus_rule` 的枚举封闭是空转的。（此点由 Codex `6e35a71` 报告 P1-3 提出，我本机独立复现——我此前只查了枚举取值域，没查根级必填集，属本轮漏审，登记于 §0.5a）
- `docs/schemas/macao_config.schema.json:67`：`"min_effective_votes"` 仍在契约里，`docs/usercases/UC1-init-gemini.md:167` 的 v2.5 示例仍在写它，`docs/usercases/UC1-init-glm.md:253` 还指引管理员用它调「法定人数风险」——但五重门禁**不读这个键**，`policy_snapshot` 的 required 里也没有它。同一个「席位法定人数」于是有 `min_effective_votes` 与 `seat_quorum_required` 两个名字（GUIDELINES §5 唯一权威表）。

**这不是文字问题——`minimum_winning_seats` 是判定改变量。** 可复算反例：

```python
import math
def tally(weights, votes, minwin):
    N=len(weights); W=sum(weights)
    assert all(3*w < 2*W for w in weights), "dictator cap violated"     # 配置合法
    eff=[(w,v) for w,v in zip(weights,votes) if v!='ABSTAIN']
    EN=len(eff); EW=sum(w for w,_ in eff)
    if EN < math.ceil(2*N/3): return "DEADLOCK seat_quorum"
    if EW < math.ceil(2*W/3): return "DEADLOCK weight_quorum"
    aw=sum(w for w,v in eff if v=='YES'); asz=sum(1 for w,v in eff if v=='YES')
    rw=sum(w for w,v in eff if v=='NO');  rsz=sum(1 for w,v in eff if v=='NO')
    if 3*aw>=2*EW and asz>=minwin: return f"APPROVED (胜方席位数={asz})"
    if 3*rw>=2*EW and rsz>=minwin: return "REWORK_REQUIRED"
    return "DEADLOCK threshold"

w=[5,2,1,1]; v=['YES','ABSTAIN','NO','NO']        # W=9，max 3*w_i=15 < 2W=18 → 独裁帽合法
for mw in (1,2):
    print("minimum_winning_seats=%d -> %s" % (mw, tally(w,v,mw)))
```

实跑输出：

```
minimum_winning_seats=1 -> APPROVED (胜方席位数=1)
minimum_winning_seats=2 -> DEADLOCK threshold
```

即：**一份完全通过 `macao_config.schema.json` 校验、且满足独裁帽的配置，在 `minimum_winning_seats: 1` 下由单一席位批准合并**——正是 FAQ:310 明文说这道门禁存在就是为了禁止的情形。契约库是 L1 的机器仪器；仪器放行了权威裁定禁止的配置。

**影响**：D-6 的两道反支配保证在 L1 层不成立；`docs/schemas/README.md:28` 的兜底句「跨项业务规则由运行时模块保证」在这里不适用，因为 `minimum_winning_seats >= 2` 与 `dictator_cap_enabled` 恒真**都是单键约束，Draft-07 完全表达得了**（`"minimum": 2` / `"const": true`）。

**最小闭环**
1. `macao_config.schema.json` 与 `vote_result.schema.json`：`minimum_winning_seats` 的 `"minimum"` 由 `1` 改 `2`；
2. `dictator_cap_enabled` 改 `{"type":"boolean","const":true}`，或从契约中删除该键并在 PRD §13 示例中同步删除（推荐后者：D-6 说它不可选）；
3. `min_effective_votes` 从契约与 UC-1-gemini/UC-1-glm 中删除，或在 PRD §13 明确写「v2.5 已废止，Loader 忽略」；
4. `minimum_winning_seats <= N` 的上界写进 PRD §13 与 Loader 校验（Draft-07 表达不了，属运行时）。
5. 根级 `required` 增补 `"policy"`，`team.reviewers[].required` 增补 `"vote_weight"`（或在 PRD §13 明写 Loader 注入默认 1 并写进 `policy_snapshot`）。

---

### P1-2　PRD 自身给出两个互斥的合并流水线顺序，且互斥点正好是 Pre-merge fail-closed 关卡

**证据**

- `docs/MACAO_PRD_v2.md:1478` §14.5 的编号步骤：**1. Pre-merge Evidence Push 校验（`ls-remote`）→ 2. 检出与校验 → 3. CI Gate → 4. 人工签字 → 5. 推送与 Post-merge Seal → 6. 通告完成**。
- `docs/MACAO_PRD_v2.md:853` §3.3 **E4 行的伴随动作**：「Merge Controller 启动合并流水线（**§14.5：检出 → pre-merge evidence push 校验 → merge → CI gate → 人工签字 → push**）」

同一文件、同一被引小节，顺序**倒置**：E4 行把「检出」排在 Pre-merge 校验之前，并且漏掉第 6 步。

`docs/usercases/UC8-merge-signoff.md:21` 关卡 1..6 与 §14.5 编号一致（这一点 grok 与 qwen 都核对过，也确实对）；**没有人核对 E4 行**。而 E4 行是状态机的规范来源——`docs/MACAO_PRD_v2.md:867` 明文：「除本表所列来源外，任何实现不得引入其他状态转移路径」。

**影响**：D-8 与 UC-8 关卡 1 的全部意义是「证据未落地就绝不碰源码分支」。照 E4 行实现，Merge Controller 会先检出 target 再校验 evidence ref——`ls-remote` 失败时工作区已经切走，这恰好是 UC-8 §2 开头「杜绝『源码已合入、证据未落地』的审计断裂」要防的顺序。Phase 1 实现者读 §3.3 转移表（这是 FSM 的规范入口）比读 §14.5 更可能。

**最小闭环**：把 `docs/MACAO_PRD_v2.md:853` 括号内改为「§14.5：pre-merge evidence 校验 → 检出 → merge → CI gate → 人工签字 → push → 通告」，或直接改为「见 §14.5 第 1–6 步」不再复述顺序（推荐后者：复述本身就是这条缺陷的成因）。

---

### P1-3　返工检查点的拓扑守卫在四个位置有四种强度，最弱的那个在权威 PRD 与变更清单里

**证据**

| 位置 | 守卫强度 |
|---|---|
| `docs/MACAO_PRD_v2.md:858`（§3.3 **E6**） | 「新 source commit **`!=` 上一轮**」 |
| `docs/MACAO_PRD_v2.md:849`（§3.3 `CODING`/`REWORK` → `READY_FOR_REVIEW`） | 「**新 commit** + round 匹配」 |
| `docs/v2.5_CODE_CHANGE_INVENTORY.md:85`（E6 守卫，交付物 #4） | 「当前提交了新 commit（**`!= 上轮 checkpoint_ref`**）」 |
| `docs/usercases/UC3-dev-checkpoint.md:16` P2 / `:53` d3 | 「**严格为上轮 `checkpoint_ref` 之子孙**且未被消费」 |
| `src/macao/workflow/orchestrator.py:257`（现有实现） | `if not self.git.is_ancestor(prev_ref, latest_commit): return None` |

`!=` 与「子孙」不是同一条守卫：`!=` 放行**上轮 checkpoint 的祖先**、放行**另一条分支上的无关 commit**。用例与现有代码要求拓扑单调前进；权威 PRD 与技术变更清单只要求不相等。

**影响**：这是本轮唯一一处「现有代码比权威文档更严」的地方。交付物 #4 是 Phase 1 重构 `orchestrator.py` 的施工图，它把 E6 守卫写成 `!=`；按图施工会把 `orchestrator.py:257` 已有的 `is_ancestor` 检查**弱化掉**，而 UC-3 §6 验收标准里又没有针对该守卫的用例（`:92` 第 1 条只写「新 commit」），弱化不会被测试发现。

**最小闭环**：`docs/MACAO_PRD_v2.md:858` E6 触发条件与 `:849` 行改为「新 source commit 为上一轮 `checkpoint_ref` 的拓扑子孙（`is_ancestor(prev, new)`）且未被消费」；`docs/v2.5_CODE_CHANGE_INVENTORY.md:85` 同步；UC-3 §6 增一条反例断言（提交上轮 checkpoint 的祖先 → 拒绝）。

---

### P1-4　交付物 #9 `STATUS.md` 计数三处互斥，双向对账不平；申请据其自述宣告「完整如实记录」

**证据**（对账脚本与 `STATUS.md` 自身宣告的治理规则同构）

| 位置 | 数字 |
|---|---|
| `docs/reviews/STATUS.md:6`（头部） | 报告 **108**、申请 **23** |
| `docs/reviews/STATUS.md:105`（登记表标题） | 报告 **107**、申请 **21** |
| `docs/reviews/STATUS.md:107`（对账正文） | 「计数由 103 更正为 **107**……申请由 20 更正为 **21**」 |
| 本机实测（`docs/reviews/` 目录） | `review-result-*` **112** + `review-2.5-*` **2** = **114**；`review-request-*` **23** |

双向对账（**登记但文件不存在 / 存在但未登记**）：

```bash
python3 - <<'PY'
import re,os,glob
st=open('docs/reviews/STATUS.md').read()
files={os.path.basename(p) for p in glob.glob('docs/reviews/*.md')}
res=sorted(f for f in files if 'review-result' in f or f.startswith('review-2.5'))
linked={os.path.basename(x) for x in
        set(re.findall(r'\(([^)]*\.md)\)',st))|set(re.findall(r'`([^`]*\.md)`',st))}
print("存在但未登记:", [f for f in res if f not in linked])
print("登记但文件不存在:", [f for f in linked if f.startswith('20') and f not in files])
PY
```

输出：**登记但文件不存在 0；存在但未登记 7**——

```
2026-09-01-review-result-5583bdd-grok.md                 （已提交于 6e35a71，属被审基线内积压）
2026-09-01-review-result-caf3473-DesignSync-r2-qwen.md   （已提交于 9492436，属被审基线内积压）
2026-09-01-review-result-caf3473-qwen.md                 （已提交于 9492436，属被审基线内积压）
2026-09-02-review-result-6e35a71-DesignSync-grok.md      （本轮同期产出，不计入基线欠账）
2026-09-02-review-result-6e35a71-DesignSync-r2-qwen.md   （同上）
2026-09-02-review-result-6e35a71-UseCases-grok.md        （同上）
2026-09-02-review-result-6e35a71-qwen.md                 （同上）
```

**公平地说，基线 `6e35a71` 上的真实欠账是 3 份，不是 7 份**——另 4 份是本轮同期报告。但 3 份欠账里包含 `5583bdd-grok`，而这**正是本申请 §1 用来论证「全部阻断项已闭环」的那份评审**：登记表里没有它。

**影响**：申请 §2 第 9 行称 `STATUS.md`「完整如实记录全量 **108** 份专家评审报告结论与闭环履历」。三个互斥数字里没有一个等于实测值，而这份文件是**门禁状态注册表**——它是 PG-0 判定的登记依据，不是普通文档。GUIDELINES §8 要求审计相关的结构性事实需多 reviewer 共识；一个自身对不上账的注册表不能作为定级依据。grok 在其报告 §三 第 9 行也持相同立场（「实时登记表，不是对齐证据；本轮不按其『已闭环』句定级」），但未做对账。

**最小闭环**：以 `git ls-files docs/reviews/` 为唯一源重算三处计数使之相等；补登 3 份基线内欠账 + 本轮 4 份；把上述对账脚本落到 `tests/` 或 CI，使这条不再靠人复核（这已是自 `2766c69` Codex P2-1 起**连续四轮**未固化的同一项）。

---

### P1-5　`review_disposition` 契约未实现提案明文规定的 `disposition_type` 联动，`DEFERRED` / `REJECTED` 可置 `requires_new_checkpoint=true` 并翻转 E4/E5a

**证据**

`docs/PRD_CHANGE_PROPOSAL_v2.5.md:180-184` 对五个枚举逐条给出硬约束：

> - `ADOPTED`：`requires_new_checkpoint` 可为 `true` 或 `false`；
> - `DEFERRED`：延期，必须有理由，**`requires_new_checkpoint=false`**；
> - `REJECTED`：不采纳，必须有理由，**`requires_new_checkpoint=false`**；
> - `EXEMPTED_BY_ADMIN`：……必须有 `override_id`，**`requires_new_checkpoint=false`**。

`docs/schemas/review_disposition.schema.json` 只为 `EXEMPTED_BY_ADMIN` 建了条件约束（`override_id` 必填，见 §0.1-2 我的复验），**`DEFERRED` 与 `REJECTED` 的布尔值完全自由**：

```
DEFERRED + requires_new_checkpoint=true -> ACCEPTED
REJECTED + requires_new_checkpoint=true -> ACCEPTED
```

（从 `fixtures/valid/disposition.yml` 出发，仅替换 `dispositions[]`，其余不动。）

**影响**：D-5 的守卫语义是「任一 `requires_new_checkpoint=true` ⟹ E5a 进 `REWORK`」（`MACAO_PRD_v2.md:857`）。一个「延期，不改码」的 `DEFERRED` 项带上 `true` 后**合法通过契约**，并把本该 E4 合并的任务推回返工轮——这是判定翻转，不是格式问题。同理 `REJECTED`（不采纳，按定义就不会产生新代码）。

同段 `:193` 强制规则 6 还要求「disposition 必须**反向引用冻结的 vote result 和 `issues_index` 哈希**」；契约里 `issues_index_sha256` 是**可选**属性，且完全没有 vote_result 的引用字段。

**最小闭环**：在 `review_disposition.schema.json` 的 `allOf` 中为 `DEFERRED` / `REJECTED` 补 `requires_new_checkpoint: {"const": false}` 条件分支；`issues_index_sha256` 移入 `required`；补一个指向冻结 vote result 的引用对象。每个枚举补一正一反 fixture。

**来源**：本条与 Codex `6e35a71` 报告 P1-4 独立收敛；上述反例为我本机复跑结果。

---

## 四、P2：登记，Phase 1 前处理（7 项）

| ID | 问题 | 证据 |
|---|---|---|
| **P2-1** | 权威提案两处把 `review_context` 写成「**9 大**必需块 / 9 大 context 语义块」，与 PRD、Schema、`schemas/README` 的 **10** 冲突 | `PRD_CHANGE_PROPOSAL_v2.5.md:458` 与 `:489` vs `MACAO_PRD_v2.md:977`（「10 大必需块」，自称唯一权威完整模型）、`review_context.schema.json` `required` **实测 10 键**、`schemas/README.md:26`、`UC4-review-dispatch.md:6/28`。GUIDELINES §5 唯一权威表；`:489` 更直接描述错了它要修的那个契约 |
| **P2-2** | `schemas/README.md:26` 宣称 `review_context.schema.json`「**禁止 base64 内联**」，契约实际不拦 | 反证实例（从 `fixtures/valid/review_context_full.json` 出发）：置 `code_changes.diff_policy = "inline_base64"`，`code_changes.diff_command` = 一段 base64 大块 → **ACCEPTED，0 error**。`diff_policy` 是无枚举的 `{"type":"string"}`；`additionalProperties:false` 只拦未知键，不拦载体语义。这正是 GUIDELINES §6 第 11 号场景（`review_context` 载体不一致）在契约层的缺口 |
| **P2-3** | `aep_envelope.schema.json` 的 `payload` 为任意 `object`，16 KiB 预算与 Type A–H 八种载荷结构零约束；`protocol` 仍接受 `AEP/1.0` | 实测 `properties.payload = {"type":"object"}`。**与 grok DS-P2-3 / qwen P2-6 收敛**。附带后果：`REVIEW_REQUEST` 与 `review_context.schema.json` 在契约层**没有绑定**，P2-2 因此无法靠信封侧兜住 |
| **P2-4** | PRD §14.2 `role_view` 表缺「override APPROVED 且待 FINAL」行 | `MACAO_PRD_v2.md:1454-1466` 十一行 vs `UC1-init-glm.md:145-146` 十二行。语义无冲突（两行都投影 `SHOULD_DISPOSE`），方向是 PRD 补齐。**与 grok DS-P2-2 / qwen P2-2 收敛** |
| **P2-6** | `dev_manifest.schema.json` 未把状态转移所依赖的引用设为必填 | `required` 实测为 `[version, executor, development, status, signal, review_round]`——`task_id`、`checkpoint_ref`、`full_document` **全是可选**。而 `MACAO_PRD_v2.md:876` 要求 `.dev.yml` 按 `checkpoint_ref + review_round` 双匹配受理，`UC3:53` d5 把 `full_document.path` + 字节级 sha256 列为 fail-closed 条件。契约放行一份没有 `checkpoint_ref`、没有 `full_document` 的 `.dev.yml`。**与 Codex P1-2 收敛**，我判 P2 而非 P1：这两项校验在 PRD 与用例中均有明文归属（运行时 Layer 1a），`schemas/README.md:28` 的兜底句在此适用 |
| **P2-7** | 交付物 #5 `SRSv1.md` 与 PRD 的 AEP 类数冲突 | `docs/SRSv1.md:613`：「统一为 **7 类** AEP 消息（`DEVELOPMENT_STARTED` / `REVIEW_RESPONSE` 等），以 `MACAO_PRD_v2.md` §2.4 为准」vs `MACAO_PRD_v2.md:346`「共定义 **8 种**消息类型（Type A 到 Type H）」。申请 §2 第 5 行称该文件本轮「更新头部映射表」，正文这一句未随 D-7 更新。**与 Codex P1-8 收敛**，我判 P2：该句自带「以 PRD §2.4 为准」的兜底，不产生实现歧义 |
| **P2-5** | 提案 §4.2 的迁移记录锚定的 PRD 行号已**全部失效** | `PRD_CHANGE_PROPOSAL_v2.5.md:453` 声称在「L416、L833、L859、L1355、L1510、**L1632、L1658**」删除了「评审产物提交到 source branch」。PRD 现共 **1615 行**，L1632/L1658 **越界**；其余五行逐行核对与该表述无关（L859 是 E7 行、L1510 是凭据脱敏行）。**实质迁移本身我已独立确认为真**（全库仅剩 `MACAO_PRD_v2.md:246` 的禁令句与 `:123` 的「不污染 source branch」），所以这是记账失效而非回退；但它使该条闭环声明不可复核（GUIDELINES §9 A/B 型） |

---

## 五、P3：可延期（2 项）

| ID | 问题 |
|---|---|
| **P3-1** | 悬空章节引用：`PRD_CHANGE_PROPOSAL_v2.5.md:453` 的 **§16.4**（PRD 第十六部分只有 16.1–16.3）。`schemas/README.md:14` 的「§13」、`UC9:6` 的「§18」、`UC10:6` 的「§20」属「第 N 部分」简写，可读，建议统一写法 |
| **P3-2** | 「179 份 Markdown」不可复现，且**三名 reviewer 得到三个不同数**：本人 167（`git ls-tree 6e35a71`）/ 172（`find docs`）/ 185（`find -L docs`，跟随 `docs/usecases` 软链），grok 报 181，qwen 报 181。0 控制字符的结论各方一致为真。建议申请改为写明口径与命令，而不是写一个数 |

---

## 六、GUIDELINES §6 反例库：11/11 可唯一推导

| # | 场景 | 唯一推导来源 | 结果 |
|---|---|---|---|
| 1 | 2-reviewer 全部弃权 | $E_N=0 < \lceil 4/3 \rceil=2$ | `DEADLOCK`（UC-9 §2.d 明写「全体弃权 ⟹ 必然 DEADLOCK」） |
| 2 | 1 超时 + 1 批准 | $E_N=1 < 2$ | `DEADLOCK` |
| 3 | 1:1 僵局 | 门禁 4：$3\cdot1 < 2\cdot2$ 两侧皆不过 | `DEADLOCK` |
| 4 | 3-reviewer 1:1:1 | YES/NO/ABSTAIN → 阈值不过；YES/NO/NO → $3\cdot2 \ge 2\cdot3$ 且 $rsz=2$ | 前者 `DEADLOCK`，后者 `REWORK_REQUIRED`，均唯一 |
| 5 | 崩溃重启重复投票 | `UC4:68` E5 + `UC9:69` E3 幂等 | 去重不双计 |
| 6 | 同 reviewer 两份票 | `UC4:44` f4 + `:58` A5，审计 `REVIEW_DEDUP` | 保留有效票 |
| 7 | `.dev.yml` 缺字段但 `signal=EXPLICIT` | `UC3:53` d1 Schema 先于 d2；`dev_manifest` required 六键 | fail-closed 拒绝 |
| 8 | 第二轮 `.review.yml` 是否覆盖第一轮 | `PRD:876` ref+round 双匹配；`UC1-glm:152` `STALE` 语义 | 不覆盖，按轮隔离 |
| 9 | 人工接管超时默认动作 | `PRD:1160` 接管超时总则 + `UC7:51` §2.f | HOLD + 升级告警，**不得静默推进** |
| 10 | Git 冲突致 checkpoint 与工作区不一致 | `UC8:63` E2 `CHECKPOINT_DRIFT` + `:78` 验收 3 | 不合并 → E4b |
| 11 | `review_context` diff 载体不一致 | `PRD:1031` `diff_policy: generate_locally` + §2.4 禁 base64 | 正文唯一；**但契约层不拦，见 P2-2** |

11/11 可从文档体系唯一推出。第 11 项的**正文**唯一，**契约**不唯一。

---

## 七、与其他 Reviewer 的交叉核对（GUIDELINES §8）

同基线共四份报告：grok（`YES_APPROVE`，无 P0/P1，P2×8/P3×1）、qwen（`YES_APPROVE`，ADVISORY×2）、**Codex（`REJECT`，P1×8，两轨合并出具）**、本报告（`NO_APPROVE`）。票型 **2:2**。

**与 Codex 的收敛（5 项）**

Codex 与我独立到达同一批结论，且证据路径不同（他走「构造未覆盖反例打契约」，我走「用文档自称的约束反查契约」）：

| 我的项 | Codex 的项 | 状态 |
|---|---|---|
| P1-1（配置面与 D-6 冲突） | P1-3（`macao_config` 并未封闭） | **互补**：他找到根级不要求 `policy`，我找到 `minimum_winning_seats` 下界与独裁帽开关。三个洞在同一个契约上，已合并为 P1-1 |
| P1-5（`DEFERRED`/`REJECTED` 联动缺失） | P1-4 | **独立收敛**，反例一致 |
| P1-2（E4 行流水线顺序倒置） | P2-2（「合并关卡顺序有一处摘要漂移」） | **独立收敛**，我判 P1 他判 P2。分歧点在后果评估：我认为 §3.3 转移表是 FSM 的规范入口且带「不得引入其他路径」的硬约束，照它实现会把 fail-closed 关卡排到检出之后 |
| P2-3（AEP payload 无约束） | P1-1 | **收敛**，我判 P2 他判 P1。我采纳他的加权：他构造了 ~50 KiB 内联正文被接受的实例，比我「payload 是任意 object」的静态观察更强；但 `schemas/README.md:28` 明写跨项规则归运行时，故我维持 P2 |
| P2-6 / P2-7（`.dev.yml` 必填集、SRS 7 vs 8 类） | P1-2 / P1-8 | **收敛**，见 §0.4a |

**与 grok / qwen 的收敛（3 项）**

| 项 | 三方一致 |
|---|---|
| 前四轮全部 P0/P1 已闭环、无回退 | 是。我另加了六处 PRD 示例 × 契约的全量复跑作为证据 |
| AEP 信封 16 KiB / payload 无约束 | 我 P2-3 = grok DS-P2-3 = qwen P2-6 = codex P1-1（四方一致） |
| §14.2 缺 override 后 `SHOULD_DISPOSE` 行 | 我 P2-4 = grok DS-P2-2 = qwen P2-2 |

**我认可对方、本轮自己未查到的**

- grok DS-P2-8：`docs/EXECUTIVE_SUMMARY.md` 仍自称权威基准 v2.3。复核属实，采纳登记（不在申请交付物清单内，不改我的票）。
- grok 与 qwen 都独立确认「UC-8 六关卡与 §14.5 编号一致」——**这一点他们对，我复核为真**；我的 P1-2 指向的是没有人查的 §3.3 E4 行，与之不矛盾。
- Codex 的三条见 §0.4a。

**我提出、四方中只有我给出证据的（2 项）**

| 我的项 | 其余三方 | 我坚持的依据 |
|---|---|---|
| P1-3 拓扑守卫四种强度 | 均未涉及 | 六处原文并列可比；`orchestrator.py:257` 是反向证据（现有实现比权威文档严），照交付物 #4 施工会弱化它 |
| P1-4 STATUS 对账 | grok 表态「不按其自述定级」（立场一致，未对账）；qwen 记为「已入库并对账」；codex 未涉及 | 对账脚本可复跑：三处计数互斥（108/107/107），实测 114，基线内 3 份未登记——其中包括申请 §1 用来论证闭环的 `5583bdd-grok` |

**关于定级差异**：grok 与 qwen 的 YES 均基于「D-1～D-9 与九项交付物的**正文**主边对齐」，这一点我独立复现且同意（见 §一 §二）。分歧全部落在正文之外：机器契约的取值域与必填集（P1-1、P1-5）、转移表伴随动作句（P1-2）、施工图与实现的守卫强度（P1-3）、登记表自身（P1-4）。按 GUIDELINES §2.1，L1 的判据是「设计文档之间、与权威基准之间一致；所有 YAML/JSON 示例是合法可解析格式」——前半句正是这些项所在的域。Codex 独立到达同样的立场（REJECT），并在其中三条上与我逐条收敛。

按 GUIDELINES §8「真理不等于投票」，票型 2:2 不构成裁决；建议以本报告与 Codex 报告中**可复跑的反例**为准逐条裁定，而不是计票。

## 八、建议闭环顺序与验收标准

1. **P1-1**：改两份 Schema 的 `minimum_winning_seats.minimum: 2`；`dictator_cap_enabled` 收 `const: true` 或删键；清理 `min_effective_votes`。
   *验收*：以 `{"minimum_winning_seats": 1}` 和 `{"dictator_cap_enabled": false}` 两个反例过 `macao_config.schema.json`，**均须被拒并打印拒绝原因**。
2. **P1-2**：`MACAO_PRD_v2.md:853` 改为「见 §14.5 第 1–6 步」。
   *验收*：全库 grep「检出 → pre-merge」零命中；§14.5、§3.3 E4、UC-8 关卡表三处顺序脚本比对一致。
3. **P1-3**：PRD `:849`/`:858` 与变更清单 `:85` 补拓扑子孙守卫；UC-3 §6 增反例断言。
   *验收*：fixture「提交上轮 checkpoint 的祖先」→ E6 拒绝、任务态不变。
4. **P1-4**：重算 STATUS 三处计数并补登；对账脚本入 `tests/`。
   *验收*：脚本双向输出均为 0，且三处计数相等。
5. **P1-5**：`review_disposition.schema.json` 补 `DEFERRED` / `REJECTED` ⟹ `requires_new_checkpoint: false` 的条件分支；`issues_index_sha256` 移入 `required`。
   *验收*：`DEFERRED + true`、`REJECTED + true` 两个反例**均须被拒并打印拒绝原因**；五个枚举各补一正一反 fixture。
6. **P2-1/P2-2/P2-5/P2-6/P2-7**：提案 9→10；`diff_policy` 收敛为枚举 `["generate_locally"]`（或 `schemas/README.md:26` 改成「禁令在正文，契约不校验」）；提案 §4.2 迁移记录改为引小节名而非行号；`dev_manifest` 必填集补 `checkpoint_ref` / `full_document`；`SRSv1.md:613` 改 8 类。
7. **回归门禁固化**（连续四轮未做，第 5 次登记）：把本报告 §一 的六处示例×契约复跑、§六 的 11 场景推导、P1-4 对账脚本合为一个交付前门禁；否则「每轮闭上一轮、同类再开一处」的模式会继续。

---

## 附：机器票与结构化 issue 索引

`vote`: **`NO_APPROVE`**　`opinion.status`: `CHANGES_REQUESTED`

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/DS-P1-1` | critical | `BLOCKING` | `policy` 配置面与 D-6 冲突：`minimum_winning_seats` 契约下界 1（提案要求 ≥2）、`dictator_cap_enabled` 可关、`min_effective_votes` 孤儿键；单席位可批准合并（附反例） |
| `claude/DS-P1-2` | major | `BLOCKING` | `MACAO_PRD_v2.md:853` E4 行的流水线顺序与 §14.5 倒置，Pre-merge fail-closed 关卡被排到检出之后 |
| `claude/DS-P1-3` | major | `BLOCKING` | 返工拓扑守卫四种强度；PRD `:858` 与变更清单 `:85` 的 `!=` 弱于 UC-3 与 `orchestrator.py:257` 现有实现 |
| `claude/DS-P1-4` | major | `BLOCKING` | 交付物 #9 `STATUS.md` 计数三处互斥（108/107/107），实测 114；7 份未登记（基线内 3 份） |
| `claude/DS-P2-1` | major | `ADVISORY` | 提案 `:458`/`:489` 「9 大 context 语义块」vs PRD/Schema/README 的 10 |
| `claude/DS-P2-2` | major | `ADVISORY` | `schemas/README.md:26` 宣称禁 base64，契约实际接受 `diff_policy: inline_base64` + base64 载荷 |
| `claude/DS-P2-3` | minor | `ADVISORY` | `aep_envelope` payload 无约束；16 KiB / 八类载荷 / `REVIEW_REQUEST`↔`review_context` 绑定均未编码 |
| `claude/DS-P2-4` | minor | `ADVISORY` | PRD §14.2 role_view 缺 override 后 `SHOULD_DISPOSE` 行 |
| `claude/DS-P1-5` | major | `BLOCKING` | `review_disposition` 契约未实现提案 §L180-184 的枚举联动：`DEFERRED`/`REJECTED` 可置 `requires_new_checkpoint=true` 并把 E4 翻成 E5a；`issues_index_sha256` 仍可选，无冻结 vote_result 引用 |
| `claude/DS-P2-5` | minor | `ADVISORY` | 提案 §4.2 迁移记录行号全部失效（L1632/L1658 越界）；实质迁移已独立确认为真 |
| `claude/DS-P2-6` | minor | `ADVISORY` | `dev_manifest.schema.json` 的 `required` 不含 `task_id`/`checkpoint_ref`/`full_document` |
| `claude/DS-P2-7` | minor | `ADVISORY` | `SRSv1.md:613` 写「7 类 AEP 消息」，PRD §2.4 为 8 类 |
| `claude/DS-P3-1` | minor | `ADVISORY` | 提案 §16.4 悬空；「第 N 部分」简写口径不统一 |
| `claude/DS-P3-2` | minor | `ADVISORY` | 「179 份 md」不可复现，三名 reviewer 三个数（167/172/185 vs 181 vs 181） |
