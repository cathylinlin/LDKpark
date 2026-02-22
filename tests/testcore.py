from LDKpark import add

def test_add():
    assert add(1,2)==3

from LDKpark.games100 import minesweeper
minesweeper.run()
minesweeper.close()
