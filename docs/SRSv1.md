# 产品方案：Multi-and-Autonomous CLI Agent Orchestrator（暂称 A）

## 1. 产品定位

### 产品名称（暂定）

**A — Agent Workflow Orchestrator**

定位：

> 一个面向 AI 软件开发团队的多 Agent 编排平台，通过统一管理不同厂商 CLI Coding Agent，实现跨机器、多角色、多阶段的软件研发协作。

核心理念：

不是替代 Claude Code、Codex、Kimi Code 等 CLI，而是：

> 把各种 CLI Agent 当作“软件工程团队成员”，进行调度、协作、通信和状态管理。

---

# 2. 产品目标

## 解决的问题

目前：

```
开发者
 |
Claude Code
Codex
Kimi
OpenCode
```

每个 CLI：

* 能力强
* 有自己的 Coding Plan
* 有自己的上下文管理
* 有自己的工具链
* 所使用模型的训练数据和关注角度与其他模型不同

但是：

* 无法组成团队
* 无法统一调度
* 无法自动 Review
* 无法跨机器协作
* 无法知道其它 Agent 当前状态

A 提供：

```
                A

       Project / Team Manager

              |
       Agent Controller

              |
 +------------+-------------+
 |            |             |

Claude     Codex        Kimi
Executor   Reviewer     Reviewer

              |
            agmsg

```

---

# 3. 核心能力

## 3.1 多 CLI Agent 管理

支持：

第一阶段(角色可配置，以下是范例)：

| CLI             | 角色       |
| --------------- | -------- |
| Claude Code CLI | Executor |
| Codex CLI       | Reviewer |
| Kimi Code       | Reviewer |
| OpenCode        | Reviewer |

未来：

* Antigravity CLI
* Cursor Agent
* Grok CLI
* 其它 coding agent

---

# 4. 总体架构

```
                        User
                         |
                   Chat Interface
                         |
                         |
                 +---------------+
                 |       A       |
                 | Orchestrator |
                 +---------------+

                         |
        +----------------+----------------+
        |                                 |
 Project Manager                 Agent Manager
        |                                 |
        |                                 |
 Workflow Engine                Agent Registry
        |                                 |
        |                                 |
        +----------------+----------------+
                         |
                  Agent Adapter Layer
                         |
     +-------------------+-------------------+
     |                   |                   |
Claude Adapter    Codex Adapter       Kimi Adapter

     |                   |                   |

Claude CLI          Codex CLI          Kimi CLI


                         |
                    Agent Event Layer

                         |
                    agmsg Protocol

                         |

                 Other Machines

```

---

# 5. 核心模块设计

# 5.1 Project / Team Manager

负责：

* 项目定义
* 团队定义
* Agent角色绑定

例如：

项目：

```yaml
project:
  name: washdb

team:
  name: washdb

```

读取 agmsg team：

```
washdb

members:

cc-ds4
cc-glm
qwen
kimi
```

绑定：

```yaml
roles:

 executor:

   member:
      cc-ds4


 reviewers:

   - cc-glm
   - qwen
   - kimi

```

---

# 5.2 Agent Registry

维护：

```
Agent

=
identity
+
role
+
location
+
adapter
+
state
```

例如：

```yaml
agent:

 id:
   cc-ds4


 role:
   executor


 runtime:

   cli:
     claude-code


 location:

   host:
     localhost


 adapter:

   type:
     claude-hook

```

远程：

```yaml
agent:

 id:
   qwen


location:

 ssh:
   user1@10.0.0.5


runtime:

 cli:
   codex

```

---

# 5.3 Agent Adapter Interface

这是整个系统最重要的抽象。

统一接口：

```typescript
interface AgentAdapter {


 start(agent)


 stop(agent)


 sendMessage(message)


 getState()


 subscribeEvent(callback)


 getLogs()


}
```

---

## Adapter实现优先级

```
        Agent Adapter


             |
             |

 +-----------+------------+


 Official Hook Adapter

             |

 MCP Adapter

             |

 Wrapper Adapter

             |

 Terminal Observation Adapter

```

---

## 例：

Claude Code：

```
ClaudeAdapter

source:

Claude Hook


event:

TaskCompleted
Stop
PostToolUse

```

Codex：

```
CodexAdapter

source:

plugin
+
stdout
```

Kimi：

```
KimiAdapter

source:

PTY

```

---

# 6. Agent State Detection

## 设计目标

统一：

不同CLI内部状态：

```
Claude:

thinking

tool execution


Codex:

planning

coding


Kimi:

analysis

```

转换为：

```
A Business State

```

---

# 三层 State Detection 架构

```
              State Engine


                  |

       +----------+-----------+

       |                      |

Explicit              Inference

State                  Engine


       |                      |

Hook/API             Behavior Analysis


                  |

             LLM Judge


```

---

# 6.1 第一层：Explicit State

最高优先级。

来源：

* CLI Hook
* Event API
* MCP

例如：

Claude：

```
TaskCompleted

```

转换：

```
IMPLEMENT_FINISHED

```

---

# 6.2 第二层：Behavior Inference

主要方案。

输入：

```
Process

stdout

filesystem

git

command execution

agmsg

```

例如：

发现：

```
git diff增加

+
pytest成功

+
停止输出

```

推断：

```
READY_FOR_REVIEW

```

规则：

```yaml
rules:


- condition:

    git_changed:true

    tests_pass:true

    no_activity:300s


  state:

    WAITING_REVIEW

```

---

# 6.3 第三层：LLM State Judge

用于复杂情况。

输入：

```
last 200 logs

git status

recent events

messages

```

输出：

```json
{
 state:

 "BLOCKED",

 confidence:

 0.86
}

```

---

# 7. Agent Communication Protocol

## 设计目标

解决：

* 跨机器
* 跨CLI
* 跨厂商

采用：

agmsg 作为底层 Message Bus。

---

## 上层定义 AEP

Agent Event Protocol

类似：

```
HTTP
  |
TCP

```

关系：

```
AEP
 |
agmsg
 |
Agent

```

---

## Message 类型

### Command

A → Agent

例如：

```json
{
 type:

 "TASK_ASSIGN",


from:

 "A",


to:

 "cc-ds4",


payload:

{

 task:

 "implement feature X"

}

}

```

---

### Review Request

Executor：

```
cc-ds4

```

发送：

```json
{
type:

"REVIEW_REQUEST",


artifact:

"architecture.md",


reviewers:

[
"cc-glm",
"qwen"
]

}

```

---

### Review Response

Reviewer：

```json
{
type:

"REVIEW_RESULT",


status:

"APPROVED",


comments:

[]

}

```

---

### State Event

Agent：

```json
{
type:

"STATE_CHANGED",

agent:

"cc-ds4",

state:

"CODING"

}

```

---

# 8. Workflow Engine

建议：

采用：

## LangGraph

原因：

你的流程天然是：

```
State Machine

```

例如：

```
Requirement

    |

Design

    |

Implementation

    |

Review

    |

Fix

    |

Merge

```

状态：

```python
WAIT_REVIEW

WAIT_FIX

DONE

```

---

# 9. 第一阶段 MVP

目标：

实现：

> Claude Code Executor + 多 Reviewer 自动评审

---

## 支持环境

单机：

```
A

Claude

Codex

Kimi

```

---

## 功能

### 1

创建项目：

```
create team washdb

```

### 2

绑定：

```
executor:

cc-ds4


reviewers:

cc-glm
qwen

```

### 3

启动开发：

```
A:

implement feature xxx

```

### 4

Claude执行

状态：

```
CODING

```

### 5

完成：

```
WAITING_REVIEW

```

### 6

A发送：

agmsg:

```
review request

```

### 7

Reviewer工作

返回：

```
APPROVED

```

### 8

Executor继续

---

# 10. 技术选型

| 模块                  | 技术                      |
| ------------------- | ----------------------- |
| Workflow            | LangGraph               |
| Agent Communication | agmsg + AEP             |
| CLI Adapter         | Python/Go               |
| Process管理           | PTY / tmux / subprocess |
| Remote Agent        | SSH + Agent Gateway     |
| Event Storage       | SQLite/PostgreSQL       |
| Message Queue       | agmsg                   |
| UI                  | Web Chat + Dashboard    |
| State Engine        | 规则引擎 + LLM Judge        |

---

# 11. 后续高级能力

## Agent Scheduler

类似 Kubernetes scheduler：

根据：

* 当前负载
* 专业能力
* 成功率

选择 reviewer。

---

## Agent Capability Registry

例如：

```
cc-glm

skills:

architecture review

security

database


qwen:

frontend

test


```

---

## Multi Reviewer Consensus

例如：

```
3 reviewers

2/3 approve

continue

```

---

## Human Override

任何时候：

```
A:

unknown state

please decide

```

人工确认。

---

# 12. 产品核心壁垒

我认为不是 workflow。

Workflow：

* LangGraph
* CrewAI
* AutoGen

都可以解决。

真正壁垒：

## 1. CLI Adapter Ecosystem

统一：

```
Claude
Codex
Kimi
OpenCode

```

## 2. Agent State Intelligence

把：

```
terminal activity

+
hooks

+
logs

+
git

+
LLM

```

变成：

```
可靠状态

```

## 3. Agent Communication Protocol

形成：

```
AI coding team communication standard

```

---

# 最终定位

这个产品可以定义为：

> **Kubernetes + Slack + CI/CD for AI Coding Agents**

其中：

| 传统软件              | A               |
| ----------------- | --------------- |
| Container         | CLI Agent       |
| Pod               | Agent Session   |
| Controller        | Orchestrator    |
| Service Discovery | Agent Registry  |
| Network           | agmsg           |
| Health Check      | State Detection |
| RBAC              | Agent Role      |
| CI Pipeline       | Workflow        |

