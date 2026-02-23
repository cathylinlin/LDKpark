import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import threading
import time
import os

# 尝试导入音频播放库
# 为了兼容性，我们尝试导入 pygame (需要安装)，如果没有则尝试使用系统命令播放
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

class TetrisApp:
    # 标准俄罗斯方块颜色
    COLORS = {
        'I': '#00f0f0',  # 青色
        'O': '#f0f000',  # 黄色
        'T': '#a000f0',  # 紫色
        'S': '#00f000',  # 绿色
        'Z': '#f00000',  # 红色
        'J': '#0000f0',  # 蓝色
        'L': '#f0a000',  # 橙色
    }
    
    # 7种标准形状
    SHAPES = {
        'I': [(0, 0), (0, 1), (0, 2), (0, 3)],
        'O': [(0, 0), (0, 1), (1, 0), (1, 1)],
        'T': [(0, 1), (1, 0), (1, 1), (1, 2)],
        'S': [(0, 1), (0, 2), (1, 0), (1, 1)],
        'Z': [(0, 0), (0, 1), (1, 1), (1, 2)],
        'J': [(0, 0), (1, 0), (1, 1), (1, 2)],
        'L': [(0, 2), (1, 0), (1, 1), (1, 2)],
    }

    def __init__(self, root):
        self.root = root
        self.root.title("俄罗斯方块 - Tetris")
        
        # 游戏常量
        self.rows = 20
        self.cols = 10
        self.cell_size = 30
        
        # 游戏状态
        self.board = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self.current_shape = None
        self.current_pos = None
        self.current_type = None
        self.next_type = None
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.paused = False
        self.is_running = False
        
        # 键位设置 (默认键位)
        self.keys = {
            'left': 'a',
            'right': 'd',
            'rotate': 'w',
            'drop': 's',
            'hard_drop': 'space',
            'pause': 'p'
        }
        
        # BGM 相关
        self.bgm_path = None
        self.bgm_thread = None
        self.stop_bgm_event = threading.Event()
        
        self.setup_ui()
        self.bind_keys()
        
    def setup_ui(self):
        """构建界面"""
        # 主框架
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(padx=10, pady=10)
        
        # 左侧：游戏画布
        self.canvas = tk.Canvas(
            main_frame, 
            width=self.cols * self.cell_size, 
            height=self.rows * self.cell_size,
            bg='black', 
            highlightthickness=2,
            highlightbackground="white"
        )
        self.canvas.pack(side=tk.LEFT)
        
        # 右侧：信息面板
        info_frame = tk.Frame(main_frame, bg='#2b2b2b', width=150)
        info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # 分数
        tk.Label(info_frame, text="分数:", fg='white', bg='#2b2b2b', font=('Arial', 12)).pack(anchor='w')
        self.score_label = tk.Label(info_frame, text="0", fg='yellow', bg='#2b2b2b', font=('Arial', 16, 'bold'))
        self.score_label.pack(anchor='w')
        
        # 等级
        tk.Label(info_frame, text="等级:", fg='white', bg='#2b2b2b', font=('Arial', 12)).pack(anchor='w', pady=(10,0))
        self.level_label = tk.Label(info_frame, text="1", fg='cyan', bg='#2b2b2b', font=('Arial', 16, 'bold'))
        self.level_label.pack(anchor='w')
        
        # 下一个方块预览
        tk.Label(info_frame, text="下一个:", fg='white', bg='#2b2b2b', font=('Arial', 12)).pack(anchor='w', pady=(20,0))
        self.next_canvas = tk.Canvas(info_frame, width=100, height=100, bg='black', highlightthickness=1, highlightbackground="gray")
        self.next_canvas.pack(anchor='w')
        
        # 按钮
        btn_frame = tk.Frame(info_frame, bg='#2b2b2b')
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="开始游戏", command=self.start_game, width=12).pack(pady=2)
        tk.Button(btn_frame, text="设置键位", command=self.open_settings, width=12).pack(pady=2)
        tk.Button(btn_frame, text="加载BGM", command=self.load_bgm, width=12).pack(pady=2)
        
    def bind_keys(self):
        """绑定键盘事件"""
        # 先解绑旧事件（防止重复绑定）
        try:
            self.root.unbind('<KeyPress>')
        except:
            pass
            
        self.root.bind('<KeyPress>', self.handle_keypress)
        self.root.focus_set()

    def handle_keypress(self, event):
        """处理按键"""
        if not self.is_running or self.game_over:
            return

        key = event.keysym.lower()
        
        if key == self.keys['left']:
            self.move(0, -1)
        elif key == self.keys['right']:
            self.move(0, 1)
        elif key == self.keys['rotate']:
            self.rotate()
        elif key == self.keys['drop']:
            self.move(1, 0)
        elif key == self.keys['hard_drop']:
            self.hard_drop()
        elif key == self.keys['pause']:
            self.toggle_pause()

    def start_game(self):
        """开始/重新开始游戏"""
        self.board = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.paused = False
        self.is_running = True
        
        self.update_info()
        self.spawn_shape()
        self.run_game_loop()
        
        # 启动 BGM
        if self.bgm_path:
            self.play_bgm()

    def run_game_loop(self):
        """游戏主循环"""
        if not self.is_running or self.game_over:
            return
            
        if not self.paused:
            if not self.move(1, 0): # 如果无法下移
                self.lock_shape()
                lines = self.clear_lines()
                if lines > 0:
                    self.update_score(lines)
                
                if not self.spawn_shape():
                    self.game_over = True
                    self.canvas.create_text(
                        self.cols * self.cell_size / 2, 
                        self.rows * self.cell_size / 2,
                        text="GAME OVER", fill="red", font=('Arial', 24, 'bold')
                    )
                    self.stop_bgm()
                    return
        
        speed = max(50, 500 - (self.level - 1) * 50)
        self.root.after(speed, self.run_game_loop)

    def spawn_shape(self):
        """生成新方块"""
        if self.next_type is None:
            self.next_type = random.choice(list(self.SHAPES.keys()))
            
        self.current_type = self.next_type
        self.next_type = random.choice(list(self.SHAPES.keys()))
        self.current_shape = [list(coord) for coord in self.SHAPES[self.current_type]]
        self.current_pos = [0, self.cols // 2 - 1] # 初始位置
        
        self.draw_next_shape()
        
        if not self.is_valid_position(self.current_shape, self.current_pos):
            return False
        self.draw_board()
        return True

    def is_valid_position(self, shape, pos):
        """检查位置是否有效"""
        for r, c in shape:
            new_r = pos[0] + r
            new_c = pos[1] + c
            
            if new_r < 0 or new_r >= self.rows:
                return False
            if new_c < 0 or new_c >= self.cols:
                return False
            if self.board[new_r][new_c] is not None:
                return False
        return True

    def move(self, dr, dc):
        """移动方块"""
        new_pos = [self.current_pos[0] + dr, self.current_pos[1] + dc]
        if self.is_valid_position(self.current_shape, new_pos):
            self.current_pos = new_pos
            self.draw_board()
            return True
        return False

    def rotate(self):
        """旋转方块"""
        # 计算边界框
        rows = [coord[0] for coord in self.current_shape]
        cols = [coord[1] for coord in self.current_shape]
        min_r, max_r = min(rows), max(rows)
        min_c, max_c = min(cols), max(cols)
        
        shape_height = max_r - min_r + 1
        
        rotated = []
        for r, c in self.current_shape:
            # 1. 平移到原点
            pr = r - min_r
            pc = c - min_c
            # 2. 旋转 (row, col) -> (col, height - 1 - row)
            nr = pc
            nc = shape_height - 1 - pr
            # 3. 平移回去
            rotated.append([nr + min_r, nc + min_c])
            
        if self.is_valid_position(rotated, self.current_pos):
            self.current_shape = rotated
            self.draw_board()

    def hard_drop(self):
        """硬降"""
        while self.move(1, 0):
            pass

    def lock_shape(self):
        """锁定当前方块到面板"""
        for r, c in self.current_shape:
            board_r = self.current_pos[0] + r
            board_c = self.current_pos[1] + c
            if 0 <= board_r < self.rows and 0 <= board_c < self.cols:
                self.board[board_r][board_c] = self.COLORS[self.current_type]

    def clear_lines(self):
        """消除满行"""
        lines_to_clear = []
        for r in range(self.rows):
            if None not in self.board[r]:
                lines_to_clear.append(r)
        
        for r in lines_to_clear:
            del self.board[r]
            self.board.insert(0, [None for _ in range(self.cols)])
            
        return len(lines_to_clear)

    def update_score(self, lines):
        """更新分数和等级"""
        points = [0, 100, 300, 500, 800]
        self.score += points[lines] * self.level
        self.lines_cleared += lines
        
        # 每10行升一级
        new_level = self.lines_cleared // 10 + 1
        if new_level > self.level:
            self.level = new_level
        
        self.update_info()

    def update_info(self):
        """更新界面信息"""
        self.score_label.config(text=str(self.score))
        self.level_label.config(text=str(self.level))

    def draw_board(self):
        """绘制整个游戏界面"""
        self.canvas.delete("all")
        
        # 绘制已锁定的方块
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c]:
                    self.draw_cell(r, c, self.board[r][c])
        
        # 绘制当前方块
        if self.current_shape and self.current_pos:
            for r, c in self.current_shape:
                br = self.current_pos[0] + r
                bc = self.current_pos[1] + c
                if br >= 0: # 防止在顶部之上绘制
                    self.draw_cell(br, bc, self.COLORS[self.current_type])

    def draw_cell(self, r, c, color):
        """绘制单个格子"""
        x1 = c * self.cell_size
        y1 = r * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='white', width=1)

    def draw_next_shape(self):
        """绘制下一个方块预览"""
        self.next_canvas.delete("all")
        if not self.next_type:
            return
            
        shape = self.SHAPES[self.next_type]
        color = self.COLORS[self.next_type]
        
        # 计算居中偏移
        rows = [coord[0] for coord in shape]
        cols = [coord[1] for coord in shape]
        min_r = min(rows)
        min_c = min(cols)
        
        # 预览窗口大小是100x100，格子大小设为20
        offset_x = 20 
        offset_y = 20
        
        for r, c in shape:
            # 居中显示
            draw_x = (c - min_c) * 20 + offset_x
            draw_y = (r - min_r) * 20 + offset_y
            self.next_canvas.create_rectangle(
                draw_x, draw_y, draw_x + 20, draw_y + 20, 
                fill=color, outline='white'
            )

    def toggle_pause(self):
        """切换暂停"""
        self.paused = not self.paused
        if self.paused:
            self.canvas.create_text(
                self.cols * self.cell_size / 2, 
                self.rows * self.cell_size / 2,
                text="PAUSED", fill="yellow", font=('Arial', 24, 'bold')
            )

    # --- 音频部分 ---
    def load_bgm(self):
        """加载BGM文件"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg")])
        if file_path:
            self.bgm_path = file_path
            messagebox.showinfo("BGM", f"已选择BGM:\n{os.path.basename(file_path)}")

    def play_bgm(self):
        """播放BGM"""
        if not self.bgm_path:
            return
            
        self.stop_bgm_event.clear()
        
        def play_loop():
            if HAS_PYGAME:
                try:
                    pygame.mixer.music.load(self.bgm_path)
                    pygame.mixer.music.play(-1) # -1 表示循环播放
                    while not self.stop_bgm_event.is_set() and pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                except Exception as e:
                    print(f"音频播放错误: {e}")
            else:
                # 如果没有 pygame，提示用户
                print("未安装 pygame 库，无法播放音频。请运行: pip install pygame")
        
        if HAS_PYGAME:
            self.bgm_thread = threading.Thread(target=play_loop, daemon=True)
            self.bgm_thread.start()

    def stop_bgm(self):
        """停止BGM"""
        if HAS_PYGAME:
            try:
                pygame.mixer.music.stop()
            except:
                pass
        self.stop_bgm_event.set()

    # --- 设置部分 ---
    def open_settings(self):
        """打开键位设置窗口"""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("键位设置")
        
        tk.Label(settings_win, text="点击按钮后按下新键位进行绑定").pack(pady=5)
        
        row = 0
        new_keys = self.keys.copy()
        
        def rebind(key_name):
            def on_key_press(event):
                btn_text = f"{key_name}: {event.keysym}"
                buttons[key_name].config(text=btn_text)
                new_keys[key_name] = event.keysym.lower()
            
            # 创建一个临时顶层窗口捕获按键
            grabber = tk.Toplevel(settings_win)
            grabber.overrideredirect(True)
            grabber.geometry(f"+{settings_win.winfo_rootx()}+{settings_win.winfo_rooty()}")
            grabber.bind("<KeyPress>", lambda e: (on_key_press(e), grabber.destroy()))
            grabber.focus_set()
            grabber.grab_set()

        buttons = {}
        for name, key in self.keys.items():
            frame = tk.Frame(settings_win)
            frame.pack(pady=2, padx=10, fill='x')
            
            btn = tk.Button(frame, text=f"{name}: {key}", width=20, command=lambda n=name: rebind(n))
            btn.pack(side=tk.RIGHT)
            buttons[name] = btn
            
        def save_settings():
            self.keys = new_keys
            self.bind_keys() # 重新绑定
            settings_win.destroy()
            messagebox.showinfo("设置", "键位已更新！")
            
        tk.Button(settings_win, text="保存并关闭", command=save_settings).pack(pady=10)

# --- 模块接口函数 ---
_root = None
_app = None

def run():
    """启动游戏"""
    global _root, _app
    if _root is not None:
        try:
            _root.lift()
            return
        except tk.TclError:
            pass
            
    _root = tk.Tk()
    _app = TetrisApp(_root)
    _root.mainloop()

def close():
    """关闭游戏"""
    global _root
    if _root:
        try:
            if _app:
                _app.stop_bgm()
            _root.destroy()
        except:
            pass
        _root = None
