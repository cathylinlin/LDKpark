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

### Git 开发规则（针对本仓库）

- 分支：新的功能请基于 `GoogleDinosaur` 分支开发（或创建以 `GoogleDinosaur` 为基准的新分支）。
- 提交信息：使用简洁前缀，如 `feat(game): 添加 dinosaur 小游戏`、`fix: 修复 bug`。
- 提交前：运行 `git status`、`pytest`（如果适用）并确保无破坏性更改。

示例：
```bash
# 切换到基准分支
git checkout GoogleDinosaur

# 创建功能分支并切换
git checkout -b feat/dinosaur

# 添加修改
git add .
git commit -m "feat(game): add google dinosaur minimal game (pygame)"
git push --set-upstream origin feat/dinosaur
```

