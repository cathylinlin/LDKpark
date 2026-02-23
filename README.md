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




