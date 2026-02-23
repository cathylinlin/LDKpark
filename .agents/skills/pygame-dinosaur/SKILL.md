---
name: pygame-dinosaur
description: Skill for developing a 2D Google‑Dinosaur style game using pygame. Provides templates, asset guidance, and step-by-step workflows to build playable demos, sprite animations, input handling, and packaging instructions.
---

# Pygame Dinosaur Skill

目的：提供可复用的工作流、示例脚本和资源建议，以快速构建和迭代 2D "Dinosaur" 风格的小游戏（基于 `pygame`）。

何时使用：当需要从头或基于模板构建一个轻量的 2D 平台/跑酷类小游戏、实现精灵动画、碰撞、分数系统或导出可运行 demo 时。

提供内容（按优先级）
- **scripts/**: 可运行的模板脚本（`run_game.py`、`sprite_loader.py`、`build_assets.py`）。
- **assets/**: 精灵表（sprite sheets）、单帧 PNG、背景图、音效（短 SFX）样例与命名建议。
- **references/**: 小游戏架构说明、控制器映射、性能注意事项与打包说明。

文件结构建议

```
pygame-dinosaur/
├── SKILL.md
├── scripts/
│   ├── run_game.py         # 最小可运行示例
│   ├── sprite_loader.py    # 精灵表切片工具
│   └── demo_input.py       # 键盘/触摸输入示例
├── assets/
│   ├── hero_walk.png       # 精灵表（横向帧）
│   ├── hero_idle.png
│   ├── bg.png
│   └── sfx/               # 音效
└── references/
    └── architecture.md
```

开发工作流（步骤式）
1. 准备素材：收集或生成 `assets/hero_walk.png`（带透明通道）或一组逐帧图片，保证每帧同尺寸。
2. 使用 `scripts/sprite_loader.py` 将精灵表切片为独立帧并输出到 `assets/frames/`（按命名约定 `walk_000.png`）。
3. 在 `scripts/run_game.py` 中创建 `AnimatedSprite` 类：
   - 使用 `pygame.image.load(...).convert_alpha()` 加载帧。
   - 用 `pygame.time.get_ticks()` 或 `dt` 控制帧切换速率。
   - 使用 `pygame.sprite.Sprite` 与 `pygame.sprite.Group` 管理绘制与碰撞。
4. 实现输入与物理：简易跳跃、重力、地面检测、最大跳跃次数。
5. 添加关卡与障碍生成功能，使用随机数或预设帧序列。
6. 添加分数、UI 文本与暂停逻辑。
7. 优化与打包：对图片调用 `convert_alpha()`、按需缩放，生成 `pyproject.toml` 或 `setup.cfg` 的可选说明，并提供 `pip` 安装或 `pyinstaller` 打包指南。

精灵与素材建议
- 使用 PNG（带透明通道）或精灵表（sprite sheet）。
- 保持帧统一尺寸，有利于碰撞盒统一管理。
- 命名规范：`action_frameIndex.png`（例如 `walk_000.png`）或单文件精灵表 `hero_walk.png`。
- 资源授权：注明素材来源与许可（CC0、CC-BY 等）。

示例：最小可运行 `run_game.py` 要点
- 初始化 `pygame`、创建窗口并设定 `clock`。
- 加载帧序列到 `frames` 列表。
- 定义 `AnimatedSprite.update()` 用时间间隔切换帧。
- 在主循环中调用 `group.update()`、`group.draw(screen)`、`pygame.display.flip()`。

性能与调试
- 在游戏循环中限制帧率（例如 60 FPS）。
- 对静态背景使用单独 `Surface` 缓存，避免每帧重绘复杂背景。
- 在开发阶段打印 `dt` 与当前帧索引，帮助调试动画定时。

测试与验证
- 本地运行 `python -m scripts.run_game` 验证帧动画、输入、碰撞。 
- 使用不同分辨率与 DPI 测试素材缩放。

打包与分发
- 建议提供 `requirements.txt`（包含 `pygame` 的具体版本）。
- 提供 `pyinstaller` 示例命令以生成独立可执行文件：
  ```
  pyinstaller --onefile --add-data "assets:assets" scripts/run_game.py
  ```

如何让 Claude 使用此技能（指示）
- 当用户请求“创建 pygame Dinosaur 游戏原型”或“把这些贴图做成帧动画”，触发此技能。
- 优先加载 `SKILL.md` 元信息，再在需要时读取 `references/architecture.md` 或 `scripts/` 以生成或修改代码。
- 若用户提供素材，调用 `scripts/sprite_loader.py` 示例或生成新的 `run_game.py`，并返回可以直接运行的代码与运行命令。

示例触发句
- "生成一个最小可运行的 pygame Dinosaur 示例，帧率 12fps，使用提供的 hero_walk.png（帧宽 64，高 64）"。
- "把这个 hero_walk.png 切成 8 帧并生成 demo 脚本，主角持续行走并能跳跃。"

附录：快速模板代码片段（供 Claude 输出）
- 提供 `AnimatedSprite` 与加载帧的简短模板，便于快速插入到用户工程中。
