# LDKpark  
A small and fun package.

## Installation  

```bash
pip install LDKpark
```

## Usage  

```python
from LDKpark import add
print(add(1,2)) #3

from LDKpark.games100 import minesweeper
minesweeper.run() #开始游戏：扫雷
minesweeper.close() #结束游戏
```

### Google Dinosaur 小游戏

```python
from LDKpark.games100 import dinosaur
python -m LDKpark.games100.dinosaur  # 在命令行运行小游戏
```

**依赖**:
- `pygame`：用于运行 `Google Dinosaur` 小游戏（已在 `pyproject.toml` 中声明）。
- 在代码中以函数调用运行游戏，避免在导入包时加载 GUI 库：

```python
from LDKpark.games100 import dinosaur, minesweeper
dinosaur.run()  # 运行恐龙小游戏

minesweeper.run()  # 开始游戏：扫雷
minesweeper.close()  # 结束游戏
```

**PR 提交要求（简单规范）**:
- 基于 `GoogleDinosaur` 分支创建功能分支，例如 `feat/dinosaur`。
- 在提交信息中使用前缀（如 `feat(game):`、`fix:`）。
- 在 PR 描述中写明变更要点、依赖变动（如新增 `pygame`）、如何运行与验证步骤。
- 若引入新的系统依赖（例如 `tkinter` 在 Linux 上），在 PR 中注明并给出安装命令。
- 在将改动 push 到远程前，确保本地 `pytest`（若有）通过，或说明为何不适用。



