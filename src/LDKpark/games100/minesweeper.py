import tkinter as tk
from tkinter import messagebox
import random

# 全局变量，存储窗口实例，用于控制关闭
_root = None

class MinesweeperGUI:
    def __init__(self, master, rows=10, cols=10, mines=15):
        self.master = master
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.buttons = {}  # 存储按钮控件
        self.mine_coords = set() # 地雷坐标
        self.game_over = False
        self.revealed_count = 0
        
        # 初始化游戏逻辑数据 (0: 空白, -1: 地雷, 1-8: 周围地雷数)
        self.board = [[0 for _ in range(cols)] for _ in range(rows)]
        
        self.setup_ui()
        self.setup_game()

    def setup_ui(self):
        """构建界面网格"""
        self.master.title("扫雷 - Minesweeper")
        
        # 顶部信息栏
        top_frame = tk.Frame(self.master)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        self.mine_label = tk.Label(top_frame, text=f"剩余地雷: {self.mines}", font=("Arial", 12))
        self.mine_label.pack(side=tk.LEFT)
        
        # 重新开始按钮
        restart_btn = tk.Button(top_frame, text="重新开始", command=self.restart_game)
        restart_btn.pack(side=tk.RIGHT)

        # 游戏区域网格
        grid_frame = tk.Frame(self.master)
        grid_frame.pack(padx=10, pady=10)

        for r in range(self.rows):
            for c in range(self.cols):
                btn = tk.Button(
                    grid_frame, 
                    width=3, 
                    height=1, 
                    font=("Arial", 10, "bold"),
                    bg="#dddddd"
                )
                btn.grid(row=r, column=c)
                
                # 绑定事件
                btn.bind('<Button-1>', lambda event, r=r, c=c: self.on_left_click(r, c))
                btn.bind('<Button-3>', lambda event, r=r, c=c: self.on_right_click(r, c))
                
                self.buttons[(r, c)] = btn

    def setup_game(self):
        """初始化地雷布局"""
        self.mine_coords.clear()
        self.revealed_count = 0
        self.game_over = False
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        
        # 重置按钮显示
        for r in range(self.rows):
            for c in range(self.cols):
                self.buttons[(r, c)].config(text="", state=tk.NORMAL, bg="#dddddd", relief=tk.RAISED)

        # 随机放置地雷
        while len(self.mine_coords) < self.mines:
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            if (r, c) not in self.mine_coords:
                self.mine_coords.add((r, c))
                self.board[r][c] = -1 # -1 代表地雷

        # 计算每个格子周围的地雷数
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == -1:
                    continue
                count = 0
                for i in range(r-1, r+2):
                    for j in range(c-1, c+2):
                        if 0 <= i < self.rows and 0 <= j < self.cols:
                            if self.board[i][j] == -1:
                                count += 1
                self.board[r][c] = count

    def restart_game(self):
        """重置游戏状态"""
        self.setup_game()
        self.mine_label.config(text=f"剩余地雷: {self.mines}")

    def on_left_click(self, r, c):
        """左键点击：揭开格子"""
        if self.game_over:
            return
        
        btn = self.buttons[(r, c)]
        # 如果已经被揭开或标记了旗帜，则忽略
        if btn['state'] == tk.DISABLED or btn['text'] == '🚩':
            return

        # 踩雷
        if self.board[r][c] == -1:
            self.show_all_mines()
            btn.config(bg='red')
            messagebox.showinfo("游戏结束", "踩到地雷了！游戏结束。")
            self.game_over = True
            return

        # 安全区域：递归揭开
        self.reveal_cell(r, c)
        
        # 检查胜利条件：揭开的格子数 = 总数 - 地雷数
        if self.revealed_count == self.rows * self.cols - self.mines:
            messagebox.showinfo("胜利", "恭喜你，扫雷成功！")
            self.game_over = True

    def reveal_cell(self, r, c):
        """递归揭开空白区域"""
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return
        
        btn = self.buttons[(r, c)]
        # 如果已经揭开，跳过
        if btn['state'] == tk.DISABLED:
            return

        btn.config(state=tk.DISABLED, relief=tk.SUNKEN, bg="#ffffff")
        self.revealed_count += 1
        
        val = self.board[r][c]
        
        # 如果周围有地雷，显示数字
        if val > 0:
            colors = {1: 'blue', 2: 'green', 3: 'red', 4: 'darkblue', 
                      5: 'brown', 6: 'cyan', 7: 'black', 8: 'gray'}
            btn.config(text=str(val), disabledforeground=colors.get(val, 'black'))
            return
        
        # 如果是空白格 (0)，递归揭开周围的格子
        if val == 0:
            for i in range(r-1, r+2):
                for j in range(c-1, c+2):
                    if i != r or j != c:
                        self.reveal_cell(i, j)

    def on_right_click(self, r, c):
        """右键点击：标记/取消标记旗帜"""
        if self.game_over:
            return
            
        btn = self.buttons[(r, c)]
        current_text = btn['text']
        
        if btn['state'] == tk.DISABLED:
            return
            
        if current_text == '':
            btn.config(text='🚩', fg='red')
        elif current_text == '🚩':
            btn.config(text='', fg='black')

    def show_all_mines(self):
        """游戏结束时显示所有地雷"""
        for r, c in self.mine_coords:
            self.buttons[(r, c)].config(text='💣', bg='#ffcccc')

def run():
    """
    启动扫雷游戏。
    这是一个阻塞函数，会启动 Tkinter 主循环。
    关闭窗口后，函数才会返回。
    """
    global _root
    # 如果窗口已存在且未被销毁，尝试将其置于前台
    if _root is not None:
        try:
            _root.lift()
            return
        except tk.TclError:
            pass # 窗口已被销毁，重新创建

    _root = tk.Tk()
    game = MinesweeperGUI(_root)
    _root.mainloop()

def close():
    """
    关闭扫雷游戏窗口。
    可以在程序其他地方调用以强制关闭游戏。
    """
    global _root
    if _root is not None:
        try:
            _root.destroy()
        except tk.TclError:
            pass # 窗口可能已经关闭
        _root = None
