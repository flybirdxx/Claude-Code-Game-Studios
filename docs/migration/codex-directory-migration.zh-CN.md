# Claude Code Game Studios → Codex：逐目录迁移设计

状态：**Step 2 设计完成；迁移尚未实现、尚未通过 Codex 运行验收。**

本轮交付为这份设计、全量文件清单和可复现清单的审计脚本。设计里的目标目录、配置示例及验收项是后续实现合同，不代表已经安装的能力。

## 0. 基线与范围

| 项目 | 已核实内容 |
|---|---|
| 上游 | https://github.com/Donchitos/Claude-Code-Game-Studios |
| 迁移目标 | https://github.com/flybirdxx/Claude-Code-Game-Studios |
| 检查日期 | 2026-10-12（北京时间） |
| 两仓库检查时的 main | `be8993bbc5a1f016bc770b2846ce06272d284526`，一致 |
| 框架版本 | `project.yaml`：1.1.3 |
| 已跟踪文件 | 585 |
| Agent | 49 个 Markdown 定义 |
| Skill | 74 个 `SKILL.md`；整个技能目录 191 个文件 |
| 路径规则 | 13 个 |
| hooks 目录 | 14 个文件；settings 实际注册 9 类事件、12 个 handler |
| 公共辅助脚本 | `.claude/scripts/` 中 10 个 |
| 框架参考资料 | `.claude/docs/` 中 105 个文件 |
| 技能／Agent 测试框架 | 128 个文件 |
| 入口说明 | 5 个实际 `CLAUDE.md`；另有 1 个个人配置模板 |

检查方式：完整 Git 树枚举、全部文本文件的耦合标记扫描，以及入口、配置、技能元数据、规则、Hook 和关键技能的细读。清单中的词法命中也可能来自历史记录、注释或示例，不等于缺陷，更不是全局替换指令。

本设计的运行目标是**本地 Codex CLI，随后验证同一主机上的 IDE／桌面 Codex**。Windows 使用 Git Bash 执行现有 Bash 资产；同时保留 Linux／WSL 验证路径。仅向普通 ChatGPT 对话上传仓库，不会自动获得本地配置、命令 Hook 和引擎执行环境。[O1][O3][O7]

迁移继续使用现有工作室职责、技能阶段、审核门、项目配置和状态文件。不引入 FastAPI、数据库、独立调度器或自建 Agent Runtime；本项目与 VibeX 无关。

## 1. 需要纠正的前置假设

1. 使用 Codex 已公开的入口：`AGENTS.md`、`.agents/skills/`、`.codex/agents/`、`.codex/config.toml`。`.gpt/` 不是本方案的运行入口。[O1][O2][O4]
2. 当前 Codex 有原生子 Agent 和 Hook。应适配其已有接口，并按客户端验证，不先重建这些系统。[O2][O3]
3. `allowed-tools` 改名为 `required_tools` 不会自动产生权限约束；不存在靠自定义字段完成转换的捷径。
4. Skill 继续使用 Markdown 和随附文件，不转成一套新 Workflow YAML。原 `workflow-catalog.yaml` 本来就是流程资产，应保留。
5. `production/session-state/active.md` 保持原格式与 CHECKPOINT 标记；不改成 `session.json`。
6. 49 个角色是可选角色库。实际调用集合仍受 `team.size`、`modes.rigor` 和原技能规则约束，不启动 49 个并发进程。

## 2. 目标目录与迁移策略

迁移期间采用增量兼容方式：保留 `.claude/` 和 `CLAUDE.md`，添加 Codex 对应文件。业务文件共享，禁止同时维护两份 GDD、故事或项目配置。通过验收后，再单独决定是否停止维护 Claude 入口。

| 编号 | 源目录／文件 | Codex 目标 | 处理方式 |
|---|---|---|---|
| D01 | 根及 4 个子目录的 `CLAUDE.md` | 同级 `AGENTS.md` | 增加入口；改写引用和工具语义 |
| D02 | `.claude/agents/*.md` | `.codex/agents/*.toml` | 49 个角色逐一转换 |
| D03 | `.claude/skills/<name>/` | `.agents/skills/<name>/` | 74 个完整技能包迁移，含全部随附文件 |
| D04 | `.claude/rules/*.md` | `docs/studio/rules/` + 入口中的路径路由 | 保留 13 条规则的内容和适用范围 |
| D05 | `.claude/hooks/` | `.codex/hooks/` + `.codex/hooks.json` | 适配实际事件输入／输出；区别未支持项 |
| D06 | `.claude/settings.json` | `.codex/config.toml`、`hooks.json`、`rules/studio.rules` | 按配置、事件、命令策略拆分 |
| D06 | `.claude/statusline.sh` | `scripts/studio/status.sh`（按需调用） | 保留阶段与任务摘要，放弃复用 Claude stdin UI 协议 |
| D07 | `.claude/scripts/*` | `scripts/studio/*` | 保留确定性检查算法，更新路径 |
| D07 | `.claude/hooks/yaml-helper.sh` | `scripts/studio/yaml-helper.sh` | 保留配置解析逻辑，抽离宿主环境依赖 |
| D08 | `.claude/docs/` | `docs/studio/` | 保留知识、模板、审核门，重写宿主说明 |
| D09 | `project.yaml`、本地项目配置 | 原位置 | 保持 schema、优先级和配置来源标注 |
| D09 | `design/`、`docs/`、`src/`、`production/` | 原位置 | 保持项目产物与状态路径 |
| D10 | `CCGS Skill Testing Framework/` | 原位置 | 保留行为规格；改宿主格式断言 |
| D11 | `.github/`、根文档、Git 配置 | 原位置 | 更新维护入口、路径、忽略项；保留许可与历史 |

原快照没有独立 `.claude/commands/` 目录，也没有已跟踪的 MCP server 配置文件。不得把它们列为已存在的迁移资产。Unity、Blender 等 MCP 接入只在具体工作流确有需求时另行配置。

目标目录中的 `docs/studio/`、`scripts/studio/`、`.codex/agent-memory/` 是**本项目自定的组织约定**，没有 Codex 自动加载魔法。只有明确的入口说明、脚本调用或配置引用才会使用它们。

## D01. 入口文件：保留层级，改掉自动导入假设

| 源入口 | 新入口 |
|---|---|
| `CLAUDE.md` | `AGENTS.md` |
| `design/CLAUDE.md` | `design/AGENTS.md` |
| `docs/CLAUDE.md` | `docs/AGENTS.md` |
| `src/CLAUDE.md` | `src/AGENTS.md` |
| `CCGS Skill Testing Framework/CLAUDE.md` | `CCGS Skill Testing Framework/AGENTS.md` |

保留职责边界、产物标准、用户已授权范围、审核门、配置解析入口，以及压缩后先读 `active.md` 的恢复规则。将原 `@.claude/docs/...` 导入改为明确阅读指令；关键短规则放进根入口，长参考资料按任务读取。不能假设 `AGENTS.md` 会按 Claude 的 `@path` 语法自动展开文件。[O4]

Codex 启动时按项目根到当前工作目录建立说明链。为覆盖从根目录跨文件夹工作的情况，根入口还要明确要求：修改目标前检查该目录的 `AGENTS.md` 与路径规则。验收分别从根目录、`src/`、`design/` 和包含空格的测试框架目录启动。

`setup-engine` 的转换必须同步处理其 `references/`：原来改 `CLAUDE.md` 技术栈和 `ENGINE-REFERENCE-IMPORT` 的步骤，改为更新 Codex 入口对应的技术栈／版本引用区块；按 `project.yaml` 选择引擎参考，不保留默认 Godot 导入。兼容期如需同步两个宿主入口，由同一更新步骤生成，避免一方继续读错引擎版本。

个人偏好模板 `.claude/docs/CLAUDE-local-template.md` 改写为 `docs/studio/codex-local-preferences.md`。个人通用说明使用官方用户级入口；项目数据偏好仍走 `project.local.yaml` 白名单。不要虚构会自动合并的 `AGENTS.local.md`；`AGENTS.override.md` 也不能当作同目录 `AGENTS.md` 的追加文件。[O4]

## D02. Agent：保留职责，转换可执行定义

实际字段分布：49 个 Agent 都有 `name`、`description`、`tools`、`model`、`maxTurns`；15 个有 `disallowedTools`，17 个有 `memory: project`，5 个声明预加载 `skills`，`prototyper` 另有 `isolation: worktree`。

| Claude 字段／内容 | Codex 设计 | 等价性说明 |
|---|---|---|
| `name`、`description` | 同名 TOML 字段 | 保留角色 ID，避免破坏 `specialists.*` 路由 |
| Markdown 正文 | `developer_instructions` | 职责、禁区、审核输出原样保留语义 |
| `model: inherit` | 省略模型覆盖 | 继承运行会话配置 |
| `opus/sonnet/haiku` | 移除 Claude 别名，登记原模型意图 | 首轮继承可用模型；以后单独做成本／质量映射，不声称一对一 |
| `tools`、`disallowedTools` | 能力对照、原生配置和已验证 Hook 约束 | 不原样写入不受支持的字段，不靠提示词宣称硬隔离 |
| `maxTurns` | 保留为任务预算说明及待验证约束 | 当前采用的公开 Agent schema 未建立同等字段 |
| `skills` | 委派说明要求先读指定技能 | 不假定 Codex 自动执行 Claude 的预加载声明 |
| `memory: project` | 显式读写 `.codex/agent-memory/<role>/` | 自定文件约定，gitignore；不是原生 memory 字段 |
| `isolation: worktree` | 原型流程显式创建与回收 Git worktree | 不依靠未验证的同名字段；保留更改供审查 |

Codex 当前支持每个 `.codex/agents/*.toml` 定义一个角色，关键字段为 `name`、`description`、`developer_instructions`。[O2] 例如以下只是结构示意，正式转换应写入完整迁移后的原角色正文：

```toml
name = "gameplay-programmer"
description = "根据已确认的玩法设计实现游戏逻辑，并报告实际测试结果。"
developer_instructions = """
遵循项目 AGENTS.md 与适用路径规则。
先读取任务指定的设计、实现范围和验收标准。
遵守 gameplay-programmer 的完整职责与禁止事项。
"""
```

权限要单独验收：`sandbox_mode = "read-only"` 并不等于禁止 Bash，且父会话的运行策略会影响子 Agent。对于原 `disallowedTools: Bash` 的角色，必须证明目标限制真正生效；未证明前标为不等价，不能仅删字段后宣布迁移成功。

协作沿用原技能的任务划分。保留 `team.size` 的 active set 公告、阶段依赖和审核职责；一项需要独立审核的任务，在子 Agent 不可用时必须报告未评估，不能让同一个角色自评后伪装成独立审核通过。原实验性 Agent Teams 文档保留为来源说明，Codex 版本改写成主 Agent 委派与汇总规则，不搬运 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 环境变量。

## D03. Skill：迁移 191 个文件，不只复制 74 个入口

`references/` 等随附文件承载后续阶段。v1.1.3 的核心变化正涉及长技能的后半流程，因此验收必须核对阶段、引用和内容，不以 `SKILL.md` 文件存在作为完成标准。

| 源字段／语法 | 处理方式 |
|---|---|
| `name`、`description` | 保留并修正宿主命令描述；同名冲突明确提示 |
| `argument-hint` | 转为正文“输入与用法”，由自然语言参数解析 |
| `user-invocable` | 转为客户端调用说明，不宣称沿用该开关 |
| `disable-model-invocation: true` | 对应技能新增 `agents/openai.yaml`，设 `policy.allow_implicit_invocation: false` |
| `allowed-tools` | 从运行 frontmatter 中移除；能力／权限在迁移矩阵中逐项处理 |
| `model` | 移除 Claude 别名；不把 Skill 当成模型切换器 |
| `$ARGUMENTS` | 明确读取用户这次调用的输入，保留缺参行为 |
| `!` 加反引号的 shell 预处理 | 改为技能开始时明确调用脚本并读取输出 |
| `CLAUDE_SKILL_DIR`、`CLAUDE_PROJECT_DIR` | 解析技能文件位置和项目根，再调用稳定目标路径 |
| `Read/Glob/Grep/Write/Edit` | 改写为当前客户端文件／shell／patch 能力，保持动作含义 |
| `AskUserQuestion` | 使用当前客户端可用的问答界面；缺少界面时明确提问并保留待决状态 |
| `Agent`、`subagent_type` | 使用真实注册的 Codex 角色委派，验收实际派发结果 |
| `TaskCreate/Get/List/Update` | 会话计划使用可用计划工具；持久状态仍由原故事文件及 checkpoint 表达 |

4 个禁止隐式调用的技能是 `day-one-patch`、`dev-story`、`hotfix`、`story-done`。其映射采用官方 skill metadata 结构。[O1]

配置读取是最重要的语义修改。原技能在模型读到正文前由 Claude 展开命令；Codex 版本应把“先执行配置解析、确认输出及来源、再进入 Phase 1”写成实际步骤。把原文命令直接留在 Markdown 中不算实现。

路径处理不能简单替换 `.claude` 为 `.agents`：例如 `${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh` 在新布局会落到错误目录。所有这类调用均改为先确定项目根，调用 `<root>/scripts/studio/yaml-helper.sh resolve_config ...`。从子目录和独立 worktree 启动也必须读到本项目配置。

调用示例面向 Codex CLI／IDE使用 `$setup-engine`、`$team-combat` 或 `/skills` 选择；ChatGPT 安装式技能的选择方式不同，单独说明。`/help`、`/settings` 等源命令更不能假设与客户端内建 slash command 一一对应。[O1]

业务决策规则与宿主权限分开。原 `collaborative/guided/autonomous`、`automation_always_ask` 与已有授权的范围继续适用；迁移不会将自主模式默认开启，也不会把阶段批准偷换成后续所有动作的永久授权。

## D04. 13 条路径规则：规则正文与命令权限分开

源 `.claude/rules/` 是带 `paths` 的内容规范；Codex `.rules` 是命令执行策略。两者用途不同，禁止直接改后缀混用。[O5]

| 规则文件 | 必须保留的适用范围 |
|---|---|
| `agent-memory.md` | Codex 迁移后的 Agent 记忆目录 |
| `ai-code.md` | Godot `src/ai`、Unity AI C#、Unreal AI C++ |
| `data-files.md` | 三引擎资产数据 JSON |
| `design-docs.md` | `design/gdd/**` |
| `engine-code.md` | 各引擎 Core 代码 |
| `gameplay-code.md` | 各引擎 Gameplay 代码 |
| `narrative.md` | `design/narrative/**` |
| `network-code.md` | 各引擎 Networking／Network 代码 |
| `prototype-code.md` | `prototypes/**` |
| `shader-code.md` | `.gdshader`、Unity shader 族、Unreal shader 族，包括目录外扩展名命中 |
| `skill-authoring.md` | `.agents/skills/**`、`.codex/agents/**` |
| `test-standards.md` | `tests/**`、Unity／Unreal 测试路径 |
| `ui-code.md` | 各引擎 UI 代码 |

迁移方式：正文放 `docs/studio/rules/`，根入口保存规则索引并要求在读取／创建／修改目标前加载适用规则；自然目录边界可补充嵌套 `AGENTS.md`。路径 glob 是项目路由数据，不声称 Codex 自动解释原 frontmatter。

分布式 shader 扩展名、大小写变体和 brace pattern 需要专门的匹配夹具。若补充路径选择脚本，应使用定义清楚的匹配语义，不能把 Python 普通 `fnmatch` 当作自动支持 brace expansion。要同时测已有文件与新文件创建；不能只测“读取已存在文件时规则会加载”。

## D05. Hooks：逐项迁移事件合同

当前 Codex 的官方 Hook 事件与部分 Claude 名称相同，但工具 payload、上下文输出、信任和覆盖范围必须按目标宿主验证。项目配置放 `.codex/hooks.json`；脚本放 `.codex/hooks/`。本地 Hook 启用需要项目与定义的信任，本步骤不要求用户先确认不存在的代码。[O3]

| 源文件 | 源注册事件 | Codex 处理与关键验收 |
|---|---|---|
| `session-start.sh` | `SessionStart` | 保留分支／配置／checkpoint 摘要；改入口与版本检查，验证内容实际进入上下文 |
| `detect-gaps.sh` | `SessionStart` | 保留缺失产物检测；不依赖另一并发 Hook 先写结果 |
| `validate-commit.sh` | `PreToolUse: Bash/PowerShell` | 适配目标 shell payload，保留原检查及 advisory／blocking 级别 |
| `validate-push.sh` | 同上 | 保留推送前检查；不同参数顺序与 shell wrapper 作为测试样本 |
| `validate-assets.sh` | `PostToolUse: Write/Edit` | 解析 `apply_patch` 的多文件操作，不能只读取 `tool_input.file_path` |
| `validate-skill-change.sh` | 同上 | 识别 `.agents/skills/` 与被改动的 references；保留来源项目判定 |
| `pre-compact.sh` | `PreCompact` | 保留落盘 checkpoint／日志目的；重新验证输出处理 |
| `post-compact.sh` | `PostCompact` | 验证压缩后恢复，避免与 SessionStart 重复大量注入 |
| `session-stop.sh` | `Stop` | 仍按回合结束处理，保留内容 hash 去重，不擅改成 SessionEnd |
| `log-agent.sh` | `SubagentStart` | 适配 role／agent／session ID，记录真实子 Agent |
| `log-agent-stop.sh` | `SubagentStop` | 关联启动记录，重复事件不重复计数 |
| `notify.sh` | `Notification` | 当前引用的 Codex 事件表没有同名事件；原脚本留在 Claude 路径，Codex 采用客户端通知，差异公开 |
| `log-instructions.sh` | **settings 中未注册** | 不把注释所称 InstructionsLoaded 当作已启用能力；Codex 未建立对应事件，保留来源诊断文件并用规则加载验收代替 |
| `yaml-helper.sh` | 非事件 handler | 作为公共配置函数迁到 `scripts/studio/`，不要再注册一个 Hook |

两个必须明确的差异：

- 目标 `apply_patch` 的变更来自命令／patch 内容，不是原来的单一 `file_path`。新增、删除、改名、多文件、空格和中文路径都需要覆盖。通过 Bash 或 MCP 改文件还需各自验证；必要时在工作流阶段结束补跑文件检查。不能因 matcher 写成 `Write|Edit` 就声称覆盖所有写入。
- PostToolUse 在写入之后运行。无效 JSON 检测只能返回失败反馈并要求修复，不能报告为“写入已被阻止”。PreToolUse 的拒绝、异常、超时和不支持动作需分别记录；不把 Hook 当作全部执行路径的安全隔离。[O3]

原脚本大多可以保留业务算法；新增薄适配函数处理项目根、工具参数、变更路径列表及输出。先使用捕获的目标事件测试，再决定哪些旧脚本需要改语言，避免为迁移重写所有 Bash。

## D06. settings、权限和状态显示

| 原设置 | 新位置／行为 |
|---|---|
| 模型／运行配置 | `.codex/config.toml`；只使用验证过的 schema 字段 |
| `hooks` | `.codex/hooks.json`；同层只保留一种定义形式，避免重复注册 |
| Bash allow／deny | `.codex/rules/studio.rules` + 实际可覆盖的 Hook 检查 |
| `Read(**/.env*)` 等路径拒绝 | 对照目标文件权限能力单独验收；命令前缀规则不能替代路径读取控制 |
| `permissions.defaultMode` | 依据 Codex 实际授权／沙箱设置选择，不能仅改字符串 |
| `statusLine` | Codex 客户端原生状态 + `$sprint-status`；项目阶段摘要可用迁移后的 `status.sh` |

原 100 多条 shell pattern 不应按字符替换成 `prefix_rule`。需按危险动作归组，分别验证 `git -C`、选项换序、复合 shell、PowerShell 和重定向。规则文件只表达目标支持的控制；不能声称它等价于 Claude 的全工具 ACL。迁移不能新增宽泛 allow、关闭审批、启用无沙箱或绕过 Hook 信任。

原 `.claude/docs/settings-local-template.md` 改为 `docs/studio/codex-settings-guide.md`，指导用户级 Codex 配置；不创建未证实会自动读取的 `.codex/settings.local.json` 或 `config.local.toml`。[O6]

## D07. 脚本与配置解析：算法优先复用

| 脚本 | 保留的功能 | 迁移重点 |
|---|---|---|
| `adr-dep-graph.sh` | ADR 依赖与环检测 | 引用路径；缺依赖章节不伪装为无环 |
| `artifact-check.sh` | workflow catalog 产物存在性 | catalog 新位置；仍只给观察，不擅判 gate |
| `gdd-structure-check.sh` | GDD 章节存在性 | 保留 Detailed Design／Detailed Rules 同义处理 |
| `godot-parse-check.gd` | Godot 实际加载解析 | `res://scripts/studio/` 路径及 class cache 前置步骤 |
| `migrate-v1-config.sh` | v1.0 到 v1.1 配置迁移 | legacy 路径和 dry-run；不要混成 GPT 转换器 |
| `project-coherence.sh` | 配置与引擎项目实际状态比对 | 根目录与引擎命令定位 |
| `review-receipts.sh` | 内容 hash 审核收据 | 保持 hash／失效规则 |
| `review-scope.sh` | 增量 GDD 审核范围 | 保持依赖纳入规则 |
| `rotate-session-state.sh` | checkpoint 与历史轮转 | 保持不丢历史；模板引用改路径 |
| `story-status.sh` | 故事状态排序 | 从 shell 预注入改为技能显式调用 |
| `yaml-helper.sh`（原 hooks 中） | 配置解析及共享函数 | 根目录、legacy 路径、输出来源与 CLI 调用入口 |

保留真实优先级：本地允许覆盖的 key → `project.yaml` → 适用 legacy 镜像 → `modes.rigor` 展开 → 文档默认值。`--review` 与 per-system override 仍按各技能原有规则应用。

特别保留：

- 空模板不预填 rigor 派生的六个 knob，否则会遮蔽 rigor 展开。
- 未配置时默认 `modes.rigor: minimal`、`modes.automation: collaborative`。
- `testing.strict.*` 未设置仍由调用技能决定策略，不新增统一默认值。
- 引擎、禁止模式和允许库的 legacy fallback 不应因移目录消失。
- `project.local.yaml` 白名单、BOM／CRLF、错误 enum、缺 Python 时的 notes 行保持可诊断。
- 项目根解析区别嵌套项目与父项目；不能仅向上取最近 Git 根后无条件读取父配置。

## D08. 框架知识资料

`.claude/docs/` 的 105 个文件迁到 `docs/studio/`。其中 workflow catalog、director gates、产物模板和编码标准主要更新链接；宿主执行说明必须重写。

| 文件组 | 必须处理的内容 |
|---|---|
| `coordination-rules.md`、`agent-roster.md`、`agent-teams.md` | 原生角色名、派发与 active set，区分团队会话和子 Agent |
| `skills-reference.md`、`quick-start.md`、`setup-requirements.md` | `$skill` 入口、所需 Codex 能力、Windows Git Bash |
| `config-resolution.md`、`effects-map.md`、`settings-guidance.md` | 显式配置调用；保持配置值语义 |
| `model-tiers.md` | 删除 Claude 别名／强制模型环境变量的运行指令，保留原成本策略意图 |
| `hooks-reference.md` 及其子文件 | 换成经过测试的目标事件合同 |
| `context-management.md`、`error-recovery-protocol.md` | Codex 恢复流程、同一份 active.md、真实失败状态 |
| `workflow-catalog.yaml` | 保留阶段、路径、artifact 判定；核对每个 Skill 名及命令说明 |
| `templates/`、`director-gates/` | 保留产物结构和 verdict 字典，不用统一 PASS 擦掉细节 |

更新链接时排除历史、许可、来源归属和引擎代码标识符。比如 Unity 的 `SendMessage()` 是游戏 API，不是应替换的 Agent 通信工具。

## D09. 项目资产和状态

保持 `design/`、`docs/engine-reference/`、`docs/architecture/`、两处 registry、`src/` 和 `project.yaml` 原位。路径也是现有审核门的输入，不应随框架重命名。例如 `design/accessibility-requirements.md` 不迁到 `design/ux/`。

`production/session-state/active.md`、日志、Agent memory 是运行时文件；当前 Git 树只跟踪 session-state 的 `.gitkeep`。迁移既要照顾已有项目中的本地文件，也不能把它们作为模板数据发布。

保持以下恢复语义：checkpoint 有边界、摘要有上限、完整文件可以按需读、Stop 按内容去重归档、恢复后重新验证事实。不要把“模板今天还没有代码”记录成长期项目属性。

阶段推进继续由 `gate-check` 管理，更新项目阶段和 legacy 镜像；迁移脚本不能直接将阶段设为完成。业务任务状态继续用故事文件和既有产物，不因为失去 Claude Task ID 而再建数据库。

## D10. 测试框架：规格保留，宿主断言更新

保留 `CCGS Skill Testing Framework/` 的原位置及 catalog 中的 `spec` 路径。本快照有 **73 个 Skill 行为规格、49 个 Agent 行为规格**；`settings` 尚缺独立 Skill spec，是原有缺口，不应报告为 74/74 已有规格。

必须同步更新 `$skill-test`／`$skill-improve`：

- 源静态检查要求 `argument-hint/user-invocable/allowed-tools`，Codex 版本要检查目标 schema 和正文输入合同，否则所有正确迁移都会被误判。
- Agent 枚举改为 `.codex/agents/*.toml`；Skill 枚举改为 `.agents/skills/*/SKILL.md`。
- 入口上下文检查改为 AGENTS 说明链与显式引用，不再模拟 Claude `@` 导入。
- 继续读完整 `references/`，保留原“未提供输入”和“实际缺少产物”的区别，以及各 gate 自己的 verdict 集合。
- 原测试结果只保留为 Claude 基线；Codex 结果单独记宿主与版本，初始为未运行，不能继承原 PASS。
- 模型别名、frontmatter 字段等宿主断言允许转换；质量指标与业务行为断言不能为了通过而降低。

建议新增的迁移测试只覆盖真实风险：

| 验收 ID | 场景 | 通过条件 |
|---|---|---|
| M01 | 文件与引用覆盖 | 49 个角色、74 个完整 Skill 包、13 条规则全部有处理记录；191 个 Skill 文件均在清单中 |
| M02 | 客户端能力 | 记录 `codex --version`、系统、shell；角色、技能、Hook 配置能实际被加载 |
| M03 | 多入口与新文件 | 根目录／子目录启动；新增 shader、Unity／Unreal 代码触发对应规则 |
| M04 | 配置等价 | local 优先级、rigor 展开、legacy、非法 key、CRLF／BOM、嵌套项目与 worktree |
| M05 | bootstrap 与参数 | 显式脚本真实执行；空参数、`--review`、四个禁止隐式调用的技能保持行为 |
| M06 | 角色与任务流 | 使用真实自定义角色；individual／small／studio 活跃集合、等待与审核边界正确 |
| M07 | Hook payload | patch 多文件／改名／删除、非 patch 写入、错误／超时、Windows 路径、重复事件 |
| M08 | 权限 | 原禁止动作仍受限制；无凭据泄露；未覆盖能力公开，不默默放宽 |
| M09 | 会话恢复 | compact／resume 后恢复 active.md；日志不重复膨胀；不读取其他 worktree 状态 |
| M10 | 工作流回归 | setup-engine → design-system → create-architecture → create-stories → dev-story → story-done；以及 team-combat、skill-test |

M10 在临时 fixture 游戏中验证；Godot、Unity、Unreal 的模型路由／路径都要检查。引擎构建与运行只对实际安装并运行过的环境标为通过，缺失引擎标为未测试。

本轮没有运行上述迁移验收，也没有调用付费模型或执行游戏引擎。

## D11. 仓库元数据、维护与回滚

- README 增加 Codex 安装、启动、平台能力和已知差异；UPGRADING 给出已有项目的本地状态迁移步骤。
- CHANGELOG 追加迁移记录，历史 Claude 内容保持原样；LICENSE 和作者归属保留。
- `.gitignore` 增加自定 Codex memory／临时产物；保留 `project.local.yaml`、session logs 与 checkpoint 的既有忽略规则。
- `.gitattributes` 为新 Markdown／TOML 目录补充适当 LF 规则，保持现有 `*.sh text eol=lf`。
- `.github/CODEOWNERS` 当前指向上游作者。后续改为 fork 的实际维护者并更新新目录，避免迁移 PR 自动请求上游审核。本轮没有改 CODEOWNERS 或通知上游。
- `.github/` 当前有 5 个元数据文件，没有已跟踪的 Actions workflow；验证 workflow 如新增，明确标为新增资产。
- 上游同步以固定 commit + 每个源文件 blob/hash 为依据。保留 Claude 源与 Codex 目标的映射，源变动触发重新审查，不能长期靠手工维护无来源的双份正文。
- 回滚只撤销本次增加／适配的宿主文件；保留用户产生的 GDD、代码、配置和 session state。迁移工具实施时必须有 dry-run、冲突报告及可审查 diff。

## 3. 后续实现的提交顺序

| 批次 | 改动范围 | 完成判据 |
|---|---|---|
| P0 | 锁定基线、客户端版本和能力矩阵 | 本设计与 585 文件清单；目标客户端能力探测有记录 |
| P1 | 公共资料／脚本路径、5 层入口、规则索引 | 从不同目录正确读取配置、规则与引擎资料 |
| P2 | Skill bootstrap 与输入语法、74 个完整包 | 所有 references 保留；配置脚本可执行；Skill 静态检查改好 |
| P3 | 49 个 Agent 定义、委派和权限差异 | 实际 role 路由、active set、预加载与隔离语义验证 |
| P4 | 11 个候选运行 Hook、配置绑定与命令规则 | 事件 payload 夹具和本地真实事件均通过；2 项无对应事件能力明确说明 |
| P5 | 测试规格、端到端流程、README／升级说明 | M01–M10 有真实结果，未测试项逐项列明 |

P1–P5 实现属于下一步。每批在 fork 分支上形成可审查提交，不批量覆盖 main，不自动删除 Claude 支持。只在明确的迁移切换决定之后处理源目录退役。

## 4. 文件清单的复现方式

在仓库根运行（Python 3.10+ 和 Git，无第三方 Python 包）：

```bash
python tools/migration/audit_codex_migration.py --output docs/migration/codex-migration-inventory.json
```

默认扫描固定基线 `be8993bbc5a1f016bc770b2846ce06272d284526`，不把本轮新建的迁移文档算入源文件总数。工具只读取 Git 对象并写指定清单，不执行 Hook、不生成或安装 Skill、不修改原文件。

清单为每个已跟踪文件记录来源 Git blob、SHA-256、拟处理动作、目标位置、设计编号、词法标记行号。所有状态初始是 `planned_not_implemented`。它只包含源文件映射；本设计提出的新入口、metadata、适配帮助函数和测试 fixture 还应在实现提交中明确列出。

## 5. 来源与核验边界

源仓库结论基于上述固定 commit 的本地快照及两仓库当次 HEAD 对照。官方文档于 2026-10-12 读取，描述当前公开能力；本方案没有把云端聊天中可用的工具等同于用户本地 CLI 的版本与环境。

- [源仓库固定版本](https://github.com/Donchitos/Claude-Code-Game-Studios/tree/be8993bbc5a1f016bc770b2846ce06272d284526)
- [源 settings](https://github.com/Donchitos/Claude-Code-Game-Studios/blob/be8993bbc5a1f016bc770b2846ce06272d284526/.claude/settings.json)
- [源配置解析合同](https://github.com/Donchitos/Claude-Code-Game-Studios/blob/be8993bbc5a1f016bc770b2846ce06272d284526/.claude/docs/config-resolution.md)
- [源测试框架](https://github.com/Donchitos/Claude-Code-Game-Studios/tree/be8993bbc5a1f016bc770b2846ce06272d284526/CCGS%20Skill%20Testing%20Framework)

[O1]: https://learn.chatgpt.com/docs/build-skills "OpenAI：Build skills"
[O2]: https://learn.chatgpt.com/docs/agent-configuration/subagents "OpenAI：Subagents"
[O3]: https://learn.chatgpt.com/docs/hooks "OpenAI：Hooks"
[O4]: https://learn.chatgpt.com/docs/agent-configuration/agents-md "OpenAI：AGENTS.md"
[O5]: https://learn.chatgpt.com/docs/agent-configuration/rules "OpenAI：Rules"
[O6]: https://developers.openai.com/codex/config-basic "OpenAI：Config basics"
[O7]: https://learn.chatgpt.com/docs/extend/mcp?surface=cli "OpenAI：MCP 与宿主差异"
