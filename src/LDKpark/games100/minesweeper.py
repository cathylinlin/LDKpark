import tkinter as tk
from tkinter import messagebox
import random

# 全局变量，存储窗口实例，用于控制关闭
_root = None

# 难度配置
DIFFICULTY = {
    "简单": {"rows": 9, "cols": 9, "mines": 10},
    "中级": {"rows": 16, "cols": 16, "mines": 40},
    "困难": {"rows": 16, "cols": 30, "mines": 99},
}


class MinesweeperGUI:
    def __init__(self, master, difficulty="简单"):
        self.master = master
        self.difficulty = difficulty
        self.rows = DIFFICULTY[difficulty]["rows"]
        self.cols = DIFFICULTY[difficulty]["cols"]
        self.mines = DIFFICULTY[difficulty]["mines"]
        self.buttons = {}
        self.mine_coords = set()
        self.game_over = False
        self.revealed_count = 0
        self.flagged_count = 0
        self.first_click = True
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

        self.setup_ui()
        self.setup_game()

    def setup_ui(self):
        """构建界面"""
        self.master.title("扫雷 - Minesweeper")

        # 顶部信息栏
        top_frame = tk.Frame(self.master)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # 难度选择
        self.difficulty_var = tk.StringVar(value=self.difficulty)
        difficulty_menu = tk.OptionMenu(
            top_frame, self.difficulty_var, *DIFFICULTY.keys(), command=self.change_difficulty
        )
        difficulty_menu.pack(side=tk.LEFT, padx=5)

        # 地雷计数
        self.mine_label = tk.Label(
            top_frame, text=f"剩余地雷: {self.mines}", font=("Arial", 12)
        )
        self.mine_label.pack(side=tk.LEFT, padx=10)

        # 重新开始按钮
        restart_btn = tk.Button(top_frame, text="重新开始", command=self.restart_game)
        restart_btn.pack(side=tk.RIGHT, padx=5)

        # 游戏区域
        self.grid_frame = tk.Frame(self.master)
        self.grid_frame.pack(padx=10, pady=10)

        self.create_grid()

    def create_grid(self):
        """创建游戏网格"""
        # 清除旧网格
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.buttons.clear()

        for r in range(self.rows):
            for c in range(self.cols):
                btn = tk.Button(
                    self.grid_frame,
                    width=2,
                    height=1,
                    font=("Arial", 10, "bold"),
                    bg="#dddddd",
                )
                btn.grid(row=r, column=c)

                btn.bind(
                    "<Button-1>", lambda event, r=r, c=c: self.on_left_click(r, c)
                )
                btn.bind(
                    "<Button-3>", lambda event, r=r, c=c: self.on_right_click(r, c)
                )

                self.buttons[(r, c)] = btn

    def setup_game(self):
        """初始化游戏状态（不放置地雷）"""
        self.mine_coords.clear()
        self.revealed_count = 0
        self.flagged_count = 0
        self.game_over = False
        self.first_click = True
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

        # 重置按钮显示
        for r in range(self.rows):
            for c in range(self.cols):
                self.buttons[(r, c)].config(
                    text="", state=tk.NORMAL, bg="#dddddd", relief=tk.RAISED
                )

        self.update_mine_label()

    def place_mines(self, safe_r, safe_c):
        """放置地雷，确保指定位置及其周围是安全的"""
        # 安全区域（第一次点击的格子及其周围）
        safe_zone = set()
        for i in range(safe_r - 1, safe_r + 2):
            for j in range(safe_c - 1, safe_c + 2):
                if 0 <= i < self.rows and 0 <= j < self.cols:
                    safe_zone.add((i, j))

        # 随机放置地雷
        all_cells = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) not in safe_zone
        ]

        self.mine_coords = set(random.sample(all_cells, min(self.mines, len(all_cells))))

        # 标记地雷
        for r, c in self.mine_coords:
            self.board[r][c] = -1

        # 计算每个格子周围的地雷数
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == -1:
                    continue
                count = 0
                for i in range(r - 1, r + 2):
                    for j in range(c - 1, c + 2):
                        if 0 <= i < self.rows and 0 <= j < self.cols:
                            if self.board[i][j] == -1:
                                count += 1
                self.board[r][c] = count

    def change_difficulty(self, new_difficulty):
        """切换难度"""
        if new_difficulty == self.difficulty:
            return

        self.difficulty = new_difficulty
        self.rows = DIFFICULTY[new_difficulty]["rows"]
        self.cols = DIFFICULTY[new_difficulty]["cols"]
        self.mines = DIFFICULTY[new_difficulty]["mines"]

        # 重新创建网格
        self.create_grid()
        self.setup_game()

    def restart_game(self):
        """重新开始游戏"""
        self.setup_game()

    def update_mine_label(self):
        """更新地雷计数显示"""
        remaining = self.mines - self.flagged_count
        self.mine_label.config(text=f"剩余地雷: {remaining}")

    def on_left_click(self, r, c):
        """左键点击：揭开格子"""
        if self.game_over:
            return

        btn = self.buttons[(r, c)]
        if btn["state"] == tk.DISABLED or btn["text"] == "🚩":
            return

        # 第一次点击时放置地雷
        if self.first_click:
            self.place_mines(r, c)
            self.first_click = False

        # 踩雷
        if self.board[r][c] == -1:
            self.show_all_mines()
            btn.config(bg="red")
            messagebox.showinfo("游戏结束", "踩到地雷了！游戏结束。")
            self.game_over = True
            return

        # 安全区域：递归揭开
        self.reveal_cell(r, c)

        # 检查胜利条件
        if self.revealed_count == self.rows * self.cols - self.mines:
            messagebox.showinfo("胜利", "恭喜你，扫雷成功！")
            self.game_over = True

    def reveal_cell(self, r, c):
        """递归揭开空白区域"""
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return

        btn = self.buttons[(r, c)]
        if btn["state"] == tk.DISABLED:
            return

        btn.config(state=tk.DISABLED, relief=tk.SUNKEN, bg="#ffffff")
        self.revealed_count += 1

        val = self.board[r][c]

        # 如果周围有地雷，显示数字
        if val > 0:
            colors = {
                1: "blue",
                2: "green",
                3: "red",
                4: "darkblue",
                5: "brown",
                6: "cyan",
                7: "black",
                8: "gray",
            }
            btn.config(text=str(val), disabledforeground=colors.get(val, "black"))
            return

        # 如果是空白格 (0)，递归揭开周围的格子
        if val == 0:
            for i in range(r - 1, r + 2):
                for j in range(c - 1, c + 2):
                    if i != r or j != c:
                        self.reveal_cell(i, j)

    def on_right_click(self, r, c):
        """右键点击：标记/取消标记旗帜"""
        if self.game_over:
            return

        btn = self.buttons[(r, c)]
        current_text = btn["text"]

        if btn["state"] == tk.DISABLED:
            return

        if current_text == "":
            btn.config(text="🚩", fg="red")
            self.flagged_count += 1
        elif current_text == "🚩":
            btn.config(text="", fg="black")
            self.flagged_count -= 1

        self.update_mine_label()

    def show_all_mines(self):
        """游戏结束时显示所有地雷"""
        for r, c in self.mine_coords:
            self.buttons[(r, c)].config(text="💣", bg="#ffcccc")


def run(difficulty="简单"):
    """
    启动扫雷游戏。
    这是一个阻塞函数，会启动 Tkinter 主循环。
    关闭窗口后，函数才会返回。

    参数:
        difficulty: 难度级别，可选 "简单"、"中级"、"困难"
    """
    global _root

    if difficulty not in DIFFICULTY:
        difficulty = "简单"

    # 如果窗口已存在且未被销毁，尝试将其置于前台
    if _root is not None:
        try:
            _root.lift()
            return
        except tk.TclError:
            pass

    _root = tk.Tk()
    game = MinesweeperGUI(_root, difficulty)
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
            pass
        _root = None


