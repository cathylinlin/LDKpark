资源说明 — dinosaur 素材目录

目的：统一素材命名/尺寸/格式，便于用作帧动画与状态切换（跑、跳、失败等）。

目录结构建议：
- assets/dinosaur/
  - README.md                # 本说明
  - manifest.json            # 示例映射（见下）
  - sheets/                  # 精灵表（可选）
    - hero_walk.png
    - hero_idle.png
  - frames/                  # 切好的逐帧图片（可选）
    - run_000.png
    - run_001.png
  - face/                    # 独立表情层（可选）
    - face_happy.png
    - face_hurt.png
  - sfx/                     # 音效（jump.wav, die.wav）

格式与通用规则：
- 使用 PNG（带透明通道），尽量不要使用 JPG。
- 所有行为的帧（同一动作）必须保持相同的帧尺寸（width × height）。
- 统一锚点（anchor/offset）：建议以帧中心或双脚为锚点，便于位置对齐与碰撞。
- 命名规范：`action_frameIndex.png` 或 `action_sheet.png`（横向或纵向帧排列）。例：`run_000.png`, `jump_00.png`，或 `hero_run.png`。
- 帧速率建议：奔跑 10–16 fps，走路 6–12 fps，跳跃（较短）8–12 fps，失败/死亡动画可用 6–10 fps。

需要的动作/表情素材（最小集合）：
1. idle（待机）
   - `idle_sheet.png` 或 `idle_000.png ... idle_N.png`
2. run（奔跑）
   - `run_sheet.png` 或 `run_000.png ... run_N.png`
3. jump_up（起跳上升）
   - `jump_up_00.png` 或 2–4 帧
4. jump_fall（下落/落地前）
   - `jump_fall_00.png` 或 1–2 帧
5. land（着地）
   - `land_00.png`（1帧或短动画）
6. die/fail（失败）
   - `die_sheet.png` 或 `die_000.png ... die_N.png`
7. face 表情层（可选，推荐）
   - `face_normal.png`, `face_happy.png`, `face_hurt.png`, `face_surprised.png`
   - 表情做成独立图层可以在运行时与身体动画叠加（比如跳跃时切换到 `face_surprised`）
8. 额外：发光、尘土、粒子等特效贴图（可做独立帧或精灵表）
9. 音效：`jump.wav`, `land.wav`, `die.wav`, `score.wav`

关于“动作+表情变化”的素材策略（三种可选方案）：
- 方案 A（简单）：在每个动作帧里直接把表情画进该帧（每个动作完整帧集含表情变化）。优点：实现简单；缺点：重复素材大、修改麻烦。
- 方案 B（分层）：身体动作与脸部表情分层（推荐）。即主体帧只包含身体，脸部为单独小图贴在头部位置。运行时根据状态替换脸部图层（跳跃时切换 `face_surprised.png`，失败时 `face_hurt.png`）。优点：节省素材、灵活。缺点：需要在代码中处理层对齐。
- 方案 C（混合）：常用动作使用分层，关键帧（例如死亡）使用独立合成帧。

表情切换时的素材需求举例（采用分层方案 B）：
- 每个动作只提供身体帧（`run_000.png`...），并提供若干表情贴图（尺寸小且带透明）：`face_normal.png`, `face_jump.png`, `face_fail.png`。
- 代码在状态机中指定：`state == jumping -> face = face_jump`，`state == running -> face = face_normal`，`state == dead -> face = face_fail`。

manifest.json 示例（放在本目录，可被脚本读取）：
- 包含动作到文件映射、单帧尺寸、锚点与推荐 fps，便于自动切片与加载。

如果你愿意，把图片素材（或一个 zip）放到 `assets/dinosaur/`，我可以：
- 帮你切帧并生成 `frames/`，
- 生成示例 `scripts/run_game.py`，直接演示跑/跳/失败时表情变化。

需要我现在为你生成 `manifest.json` 示例文件并把文件写入？我可以一并创建示例 manifest。