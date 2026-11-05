# Legal Story Image Video｜法律故事生图视频

**独立的 AI 生图 / 图生视频创作项目。** 用「透明背景极简抽象小人 + 写实电影感背景」讲述法律故事。人物、背景分层生成，最后通过常规剪辑软件或图生视频服务合成，**不是代码动画项目**。

## 视觉路线

- **人物**：白色圆头、黑点眼睛、极简嘴巴、粗描边、简单服饰；优先无头发的抽象风格，避免日系精致动漫和真人五官。
- **环境**：真实中国城市、售楼部、医院、工厂、家庭、律所等写实背景，电影感光影和真实空间透视。
- **情绪**：用镜头、天气、光色、动作传达希望、危机与释然，治愈感不等于弱化事实。
- **素材**：人物与背景独立生成，人物始终使用透明通道（PNG RGBA / SVG 透明），在合成阶段叠加。

## 一次视频的完整流程

选题与法律事实核验 → 故事文案 → 角色定妆/透明资产 → 纯背景生图 → 分镜表 → 静态镜头与少量图生视频 → 旁白与字幕 → 多轨剪辑 → 人工/自动审核 → 输出成片。

每期先完成 **3 张关键帧 + 20–30 秒试片**，通过角色一致性、写实背景、法律准确性及声音审核后再扩展整片。

## AI Agent 入口

- **运行规范**：[AGENTS.md](AGENTS.md)
- **独立 Skill**：[.agents/skills/legal-story-image-video/SKILL.md](.agents/skills/legal-story-image-video/SKILL.md)
- **人物模板（透明 SVG）**：[assets/characters/vector/](assets/characters/vector/)
- **角色清单**：[references/character-manifest.example.json](references/character-manifest.example.json)
- **双层生成提示词**：[references/prompts.md](references/prompts.md)
- **分镜表模板**：[references/shot-list-template.csv](references/shot-list-template.csv)
- **交付标准**：[docs/delivery-checklist.md](docs/delivery-checklist.md)

在 Codex、Claude Code 或其他支持 Skills 的 Agent 中，直接打开本仓库作为项目工作区，提出例如：

> 使用本仓库的 legal-story-image-video Skill，制作《一个买到烂尾楼的普通人会经历什么》。先核验事实，生成分镜和角色/写实背景，先完成30秒试片，不修改其他视频项目。

Skill 也可复制到执行器支持的项目级 Skills 目录。具体技能自动发现机制由执行器决定；只把文件放在仓库里不代表第三方 Agent 已完成安装。

## 资产目录

```text
legal-story-image-video/
├─ README.md
├─ AGENTS.md
├─ .agents/skills/legal-story-image-video/SKILL.md
├─ references/
│  ├─ prompts.md
│  ├─ character-manifest.example.json
│  └─ shot-list-template.csv
├─ assets/characters/vector/      # 透明 SVG：可编辑的抽象角色母版
└─ docs/delivery-checklist.md
```

SVG 母版可导出成透明 PNG。前期另行生成的 8 张 PNG 为**概念初版**，部分带头发，未达到最终参考片的抽象程度；正式批量生成前以本仓库的极简人物风格规范重新定妆。每期视频的旁白、商用素材和成片放在独立的视频工程目录，不直接塞进本仓库。

## 项目边界

此仓库只管理**生图叙事视频**的制作规范、角色母版、提示词和交付模板。不引用、导入或改写其他代码动效项目；两套工作流保持独立。真实案例必须核验事实，非真实情节标注「情景演绎」，不得把生成的聊天记录、证据或人物画面冒充真实取证资料。

## 当前版本

v0.1：独立 Skill、README、角色清单、透明 SVG 母版、分镜和交付验收规范。**这是一套可复用的制作规范与素材模板，不意味着已经部署可一键执行的自动生图/剪辑服务。**
