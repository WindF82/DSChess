# 双步象棋 - 主程序 (tkinter GUI)

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import sys
import os

from constants import *
from game_engine import Piece, GameState
from network import NetworkManager


class DoubleChessApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("双步象棋")
        self.root.resizable(False, False)

        self.game = GameState()
        self.network = None
        self.my_side = None
        self.opponent_confirmed = False
        self.i_confirmed = False
        self.selected_piece = None
        self.selected_hand_piece = None
        self.valid_moves = []
        self.pending_upgrade = None
        self.game_over = False

        # 拖放状态
        self.drag_active = False
        self.drag_window = None
        self.drag_piece = None

        # 计时器
        self.move_timer = 60       # 每手棋60秒
        self.timer_id = None

        self.setup_menu_ui()

    def setup_menu_ui(self):
        """主菜单界面"""
        for w in self.root.winfo_children():
            w.destroy()

        self.root.geometry("400x600")
        self.root.configure(bg="#f0e6d3")

        frame = tk.Frame(self.root, bg="#f0e6d3")
        frame.pack(expand=True)

        tk.Label(frame, text="双步象棋", font=("楷体", 32, "bold"),
                 bg="#f0e6d3", fg="#8b0000").pack(pady=10)

        tk.Label(frame, text="局域网双人对战", font=("宋体", 12),
                 bg="#f0e6d3", fg="#333").pack(pady=3)

        tk.Label(frame, text="房间码:", font=("宋体", 12),
                 bg="#f0e6d3", fg="#555").pack(pady=(10, 0))

        self.room_code_var = tk.StringVar(value="")
        self.room_code_entry = tk.Entry(frame, textvariable=self.room_code_var,
                                         font=("宋体", 16), width=15, justify="center",
                                         bg="white", relief="solid")
        self.room_code_entry.pack(pady=5)

        btn_frame = tk.Frame(frame, bg="#f0e6d3")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="创建房间", font=("宋体", 13),
                  bg="#8b0000", fg="white", width=12, height=2,
                  command=self.host_game).pack(side=tk.LEFT, padx=10)

        tk.Button(btn_frame, text="加入房间", font=("宋体", 13),
                  bg="#1a1a1a", fg="white", width=12, height=2,
                  command=self.join_game).pack(side=tk.LEFT, padx=10)

        tk.Label(frame, text="双方输入相同房间码即可联机", font=("宋体", 9),
                 bg="#f0e6d3", fg="#999").pack(pady=3)

        # 规则说明
        rules_frame = tk.LabelFrame(frame, text=" 下棋说明 ", font=("宋体", 11, "bold"),
                                     bg="#faf5eb", fg="#8b0000", padx=8, pady=5)
        rules_frame.pack(pady=10, padx=15, fill=tk.BOTH)

        rules_text = (
            "【布置阶段】黑方先放1子，之后轮流各放2子。\n"
            "  将/士限九宫格内，兵仅限第3行/第6行。\n"
            "  从右侧手牌拖放至棋盘即可布置。\n\n"
            "【行棋阶段】黑方先走1步，之后轮流各走2步。\n"
            "  按住己方棋子拖至目标位置松手即可走子。\n\n"
            "【走法】\n"
            "  将/帅 — 九宫内横竖1格\n"
            "  士/仕 — 九宫内斜向1格\n"
            "  相/象 — 本界内斜45°任意格(不跨子)\n"
            "  马     — 全局日字形(无别脚)\n"
            "  车     — 全局纵横任意格(不跨子)\n"
            "  炮     — 走法同车，隔1子吃子\n"
            "  兵/卒 — 过河前只能向前1格\n"
            "          过河后可横向或向前1格\n"
            "          到达底线可升变为B类马/炮/车\n\n"
            "【时限】每手棋限1分钟，超时跳过该手。\n\n"
            "【胜负】吃掉对方2个将获胜；\n"
            "60回合无吃将则算分（将5/车4/士相马炮3/兵2）"
        )
        rules_label = tk.Label(rules_frame, text=rules_text, font=("宋体", 8),
                                bg="#faf5eb", fg="#333", justify=tk.LEFT, anchor="w")
        rules_label.pack(fill=tk.BOTH)

        # 开发者信息
        tk.Label(rules_frame, text="", bg="#faf5eb").pack()
        dev_frame = tk.Frame(rules_frame, bg="#faf5eb")
        dev_frame.pack(fill=tk.X)
        tk.Label(dev_frame, text="作者：一建高工崔雷", font=("宋体", 8),
                 bg="#faf5eb", fg="#666").pack(side=tk.LEFT)
        tk.Label(dev_frame, text="cuilei@alumni.sjtu.edu.cn", font=("宋体", 8),
                 bg="#faf5eb", fg="#666").pack(side=tk.RIGHT)

    def host_game(self):
        """创建主机"""
        code = self.room_code_var.get().strip()
        if not code:
            messagebox.showwarning("提示", "请先输入房间码")
            return
        self.network = NetworkManager(self.on_network_message)
        if not self.network.start_host(code):
            messagebox.showerror("错误", "无法启动服务器")
            return
        self.my_side = SIDE_BLACK
        self.show_waiting_ui(code)

    def join_game(self):
        """加入房间"""
        code = self.room_code_var.get().strip()
        if not code:
            messagebox.showwarning("提示", "请先输入房间码")
            return
        self.network = NetworkManager(self.on_network_message)
        self.my_side = SIDE_RED
        self.show_searching_ui(code)
        success = self.network.join_room(code)
        if not success:
            self.setup_menu_ui()
            return

    def show_waiting_ui(self, code):
        """等待连接界面"""
        for w in self.root.winfo_children():
            w.destroy()
        self.root.geometry("400x260")
        self.root.configure(bg="#f0e6d3")

        frame = tk.Frame(self.root, bg="#f0e6d3")
        frame.pack(expand=True)

        tk.Label(frame, text="等待对手加入...", font=("宋体", 20, "bold"),
                 bg="#f0e6d3", fg="#8b0000").pack(pady=20)
        tk.Label(frame, text=f"房间码: {code}", font=("宋体", 18, "bold"),
                 bg="#f0e6d3", fg="#1a1a1a").pack(pady=5)
        tk.Label(frame, text="请让对手输入相同的房间码并点击'加入房间'",
                 font=("宋体", 10), bg="#f0e6d3", fg="#999").pack(pady=5)

        self.status_label = tk.Label(frame, text="等待中...", font=("宋体", 10),
                                      bg="#f0e6d3", fg="#999")
        self.status_label.pack(pady=15)

        tk.Button(frame, text="取消", font=("宋体", 10),
                  command=self.cancel_waiting).pack(pady=5)

    def show_searching_ui(self, code):
        """搜索房间界面"""
        for w in self.root.winfo_children():
            w.destroy()
        self.root.geometry("400x260")
        self.root.configure(bg="#f0e6d3")
        frame = tk.Frame(self.root, bg="#f0e6d3")
        frame.pack(expand=True)
        tk.Label(frame, text=f"正在搜索房间 '{code}' ...", font=("宋体", 14),
                 bg="#f0e6d3", fg="#333").pack(pady=40)
        tk.Label(frame, text="请确保与主机在同一局域网内", font=("宋体", 10),
                 bg="#f0e6d3", fg="#999").pack()
        self.root.update()

    def cancel_waiting(self):
        """取消等待"""
        if self.network:
            self.network.stop()
            self.network = None
        self.setup_menu_ui()

    def on_network_message(self, msg_type, data):
        """处理网络消息"""
        if msg_type == "connected":
            self.root.after(0, self.on_connected)
        elif msg_type == "disconnected":
            self.root.after(0, self.on_disconnected)
        elif msg_type == "error":
            self.root.after(0, lambda: messagebox.showerror("错误", data.get("message", "")))
        elif msg_type == "confirm_room_request":
            self.root.after(0, self.show_confirm_room)
        elif msg_type == "confirm_room_response":
            self.opponent_confirmed = data.get("agree", False)
            self.root.after(0, self.check_room_confirm)
        elif msg_type == "start_game":
            self.root.after(0, self.start_game_ui)
        elif msg_type == "place_piece":
            self.root.after(0, lambda: self.handle_remote_place(data))
        elif msg_type == "move_piece":
            self.root.after(0, lambda: self.handle_remote_move(data))
        elif msg_type == "upgrade_soldier":
            self.root.after(0, lambda: self.handle_remote_upgrade(data))
        elif msg_type == "game_over":
            self.root.after(0, lambda: self.handle_game_over(data))

    def on_connected(self):
        """连接成功"""
        if self.my_side == SIDE_BLACK:
            self.status_label.config(text="对手已连接!")
            self.network.send("confirm_room_request")
            self.root.after(300, self._show_self_confirm)
        else:
            self.status_label = tk.Label(self.root, text="已连接! 等待双方确认...",
                                          font=("宋体", 12), bg="#f0e6d3", fg="#333")
            self.status_label.pack(pady=10)

    def _show_self_confirm(self):
        """主机自身的确认对话框"""
        result = messagebox.askyesno("进入房间", "对手已连接, 是否同意进入房间开始对局?")
        self.i_confirmed = result
        self.network.send("confirm_room_response", {"agree": result})
        self.check_room_confirm()

    def on_disconnected(self):
        """连接断开"""
        messagebox.showwarning("断开", "与对手的连接已断开!")
        if self.network:
            self.network.stop()
            self.network = None
        self.setup_menu_ui()

    def show_confirm_room(self):
        """显示确认进入房间对话框"""
        result = messagebox.askyesno("进入房间", "对手邀请你进入房间, 是否同意?")
        self.i_confirmed = result
        self.network.send("confirm_room_response", {"agree": result})
        self.check_room_confirm()

    def check_room_confirm(self):
        """检查双方是否都确认"""
        if self.i_confirmed and self.opponent_confirmed:
            if self.my_side == SIDE_BLACK:
                self.network.send("start_game")
            self.start_game_ui()

    def start_game_ui(self):
        """启动游戏界面"""
        self._stop_timer()
        for w in self.root.winfo_children():
            w.destroy()

        self.root.geometry(f"{CANVAS_WIDTH + 280}x{CANVAS_HEIGHT + 60}")
        self.root.configure(bg="#f0e6d3")

        # 状态栏
        self.status_bar = tk.Label(self.root, text="", font=("宋体", 12),
                                    bg="#8b0000", fg="white", height=2)
        self.status_bar.pack(fill=tk.X, side=tk.TOP)

        # 主容器
        main_frame = tk.Frame(self.root, bg="#f0e6d3")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 棋盘画布
        self.canvas = tk.Canvas(main_frame, width=CANVAS_WIDTH, height=CANVAS_HEIGHT,
                                 bg=COLOR_BOARD, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # 右侧信息面板
        info_frame = tk.Frame(main_frame, bg="#f0e6d3", width=250)
        info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        info_frame.pack_propagate(False)

        tk.Label(info_frame, text="手中棋子", font=("宋体", 14, "bold"),
                 bg="#f0e6d3").pack(pady=5)

        self.hand_listbox = tk.Listbox(info_frame, font=("宋体", 11), height=12,
                                        selectmode=tk.SINGLE)
        self.hand_listbox.pack(fill=tk.X, padx=5)
        self.hand_listbox.bind("<ButtonPress-1>", self.on_hand_press)
        self.hand_listbox.bind("<B1-Motion>", self.on_hand_drag)
        self.hand_listbox.bind("<ButtonRelease-1>", self.on_hand_release)

        tk.Label(info_frame, text="", bg="#f0e6d3").pack()

        tk.Label(info_frame, text="被吃棋子", font=("宋体", 14, "bold"),
                 bg="#f0e6d3").pack(pady=5)

        self.captured_listbox = tk.Listbox(info_frame, font=("宋体", 11), height=8)
        self.captured_listbox.pack(fill=tk.X, padx=5)

        tk.Label(info_frame, text="", bg="#f0e6d3").pack()

        self.score_label = tk.Label(info_frame, text="黑方: 0 | 红方: 0",
                                     font=("宋体", 11), bg="#f0e6d3", fg="#333")
        self.score_label.pack(pady=10)

        self.round_label = tk.Label(info_frame, text="回合: 0/60",
                                     font=("宋体", 11), bg="#f0e6d3", fg="#333")
        self.round_label.pack()

        # 初始化游戏
        self.game = GameState()
        self.game.phase = PHASE_PLACEMENT
        self.game.current_player = SIDE_BLACK
        self.selected_piece = None
        self.selected_hand_piece = None
        self.valid_moves = []
        self.drag_active = False
        self.drag_window = None
        self.drag_piece = None
        self.movement_drag_active = False
        self.movement_drag_piece = None
        self.drag_from_row = -1
        self.drag_from_col = -1
        self.drag_x = -1
        self.drag_y = -1
        self.move_timer = 60
        self.game_over = False
        self.update_ui()
        self._start_timer()

    # ==================== 计时器 ====================

    def _start_timer(self):
        self._stop_timer()
        if self.game_over:
            return
        if self.game.current_player != self.my_side:
            return
        self.move_timer = 60
        self._update_timer_display()
        self.timer_id = self.root.after(1000, self._tick_timer)

    def _stop_timer(self):
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def _tick_timer(self):
        if self.game_over:
            return
        if self.game.current_player != self.my_side:
            return
        self.move_timer -= 1
        self._update_timer_display()
        if self.move_timer <= 0:
            self._timer_expired()
        else:
            self.timer_id = self.root.after(1000, self._tick_timer)

    def _timer_expired(self):
        if self.game_over:
            return
        self._stop_timer()
        if self.game.phase == PHASE_PLACEMENT:
            messagebox.showwarning("超时", "布置超时，跳过该手!")
            self.game.move_count += 1
            self.selected_hand_piece = None
            self._destroy_drag_overlay()
            self._check_placement_done()
        elif self.game.phase == PHASE_PLAYING:
            if self.pending_upgrade:
                return
            messagebox.showwarning("超时", "走子超时，跳过该手!")
            self.game.move_count += 1
            self.selected_piece = None
            self.valid_moves = []
            self._check_movement_done()

    def _update_timer_display(self):
        sec = max(0, self.move_timer)
        if sec <= 10:
            self.status_bar.config(fg="#ff4444")
        else:
            self.status_bar.config(fg="white")

    # ==================== 绘制棋盘 ====================

    def draw_board(self):
        """绘制棋盘"""
        self.canvas.delete("all")

        # 绘制横线
        for r in range(BOARD_ROWS):
            y = MARGIN_Y + r * CELL_SIZE
            x1 = MARGIN_X
            x2 = MARGIN_X + BOARD_WIDTH
            self.canvas.create_line(x1, y, x2, y, fill=COLOR_LINE, width=1)

        # 绘制竖线 (河界处断开)
        for c in range(BOARD_COLS):
            x = MARGIN_X + c * CELL_SIZE
            self.canvas.create_line(x, MARGIN_Y, x, MARGIN_Y + 4 * CELL_SIZE,
                                     fill=COLOR_LINE, width=1)
            self.canvas.create_line(x, MARGIN_Y + 5 * CELL_SIZE, x,
                                     MARGIN_Y + BOARD_HEIGHT, fill=COLOR_LINE, width=1)

        for c in [0, BOARD_COLS - 1]:
            x = MARGIN_X + c * CELL_SIZE
            self.canvas.create_line(x, MARGIN_Y, x, MARGIN_Y + BOARD_HEIGHT,
                                     fill=COLOR_LINE, width=2)

        x1, y1 = MARGIN_X, MARGIN_Y
        x2, y2 = MARGIN_X + BOARD_WIDTH, MARGIN_Y + BOARD_HEIGHT
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=COLOR_LINE, width=2)

        self._draw_palace_diagonals(0, 2)
        self._draw_palace_diagonals(7, 9)

        ry = MARGIN_Y + 4.5 * CELL_SIZE
        self.canvas.create_text(CANVAS_WIDTH // 2, ry, text="楚 河          汉 界",
                                 font=("楷体", 16), fill=COLOR_RIVER)

        if self.selected_piece:
            for r, c in self.valid_moves:
                cx = MARGIN_X + c * CELL_SIZE
                cy = MARGIN_Y + r * CELL_SIZE
                self.canvas.create_oval(cx - 10, cy - 10, cx + 10, cy + 10,
                                         fill=COLOR_VALID_MOVE, outline="")

        if self.selected_piece and self.selected_piece.is_placed:
            r, c = self.selected_piece.row, self.selected_piece.col
            cx = MARGIN_X + c * CELL_SIZE
            cy = MARGIN_Y + r * CELL_SIZE
            self.canvas.create_oval(cx - PIECE_RADIUS - 3, cy - PIECE_RADIUS - 3,
                                     cx + PIECE_RADIUS + 3, cy + PIECE_RADIUS + 3,
                                     outline=COLOR_SELECTED, width=3)

        if self.game.last_move:
            for pos in [(self.game.last_move[0], self.game.last_move[1]),
                         (self.game.last_move[2], self.game.last_move[3])]:
                r, c = pos
                cx = MARGIN_X + c * CELL_SIZE
                cy = MARGIN_Y + r * CELL_SIZE
                self.canvas.create_rectangle(cx - PIECE_RADIUS - 2, cy - PIECE_RADIUS - 2,
                                              cx + PIECE_RADIUS + 2, cy + PIECE_RADIUS + 2,
                                              outline=COLOR_LAST_MOVE, width=2)

        for piece in self.game.pieces:
            if self.movement_drag_active and piece is self.movement_drag_piece:
                self._draw_piece_faded(piece)
            else:
                self._draw_piece(piece)

        if self.drag_active and self.drag_piece:
            self._draw_drag_preview()

        if self.movement_drag_active and self.movement_drag_piece:
            self._draw_movement_ghost()

    def _draw_palace_diagonals(self, row_start, row_end):
        for r in [row_start, row_end]:
            for side_col, opposite_col in [(3, 5)]:
                x1 = MARGIN_X + side_col * CELL_SIZE
                y1 = MARGIN_Y + r * CELL_SIZE
                x2 = MARGIN_X + opposite_col * CELL_SIZE
                y2 = MARGIN_Y + (row_end if r == row_start else row_start) * CELL_SIZE
                self.canvas.create_line(x1, y1, x2, y2, fill=COLOR_LINE, width=1)

    def _draw_piece(self, piece):
        cx = MARGIN_X + piece.col * CELL_SIZE
        cy = MARGIN_Y + piece.row * CELL_SIZE
        r = PIECE_RADIUS

        if piece.side == SIDE_BLACK:
            fill_color = COLOR_BLACK_PIECE
            text_color = COLOR_BLACK_TEXT
        else:
            fill_color = COLOR_RED_PIECE
            text_color = COLOR_RED_TEXT

        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                 fill=fill_color, outline="#555", width=2)
        self.canvas.create_text(cx, cy, text=piece.name, font=("楷体", 16, "bold"),
                                 fill=text_color)

        if piece.piece_class == "B" or piece.is_upgraded:
            self.canvas.create_text(cx + r - 6, cy - r + 6, text="B",
                                     font=("Arial", 7, "bold"), fill="#ffcc00")

    def _draw_drag_preview(self):
        piece = self.drag_piece
        x = self.root.winfo_pointerx() - self.canvas.winfo_rootx()
        y = self.root.winfo_pointery() - self.canvas.winfo_rooty()
        row = round((y - MARGIN_Y) / CELL_SIZE)
        col = round((x - MARGIN_X) / CELL_SIZE)

        if not (0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS):
            return
        if self.game.phase != PHASE_PLACEMENT:
            return

        valid = self.game.is_valid_placement(piece, row, col)
        cx = MARGIN_X + col * CELL_SIZE
        cy = MARGIN_Y + row * CELL_SIZE
        r = PIECE_RADIUS

        if piece.side == SIDE_BLACK:
            fill = "#3a3a3a"
            text_color = "#aaaaaa"
        else:
            fill = "#dd5555"
            text_color = "#ffaaaa"
        outline = "#00aa00" if valid else "#aa0000"

        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                 fill=fill, outline=outline, width=2, dash=(5, 3))
        self.canvas.create_text(cx, cy, text=piece.name,
                                 font=("楷体", 16, "bold"), fill=text_color)

    def _draw_piece_faded(self, piece):
        cx = MARGIN_X + piece.col * CELL_SIZE
        cy = MARGIN_Y + piece.row * CELL_SIZE
        r = PIECE_RADIUS
        if piece.side == SIDE_BLACK:
            fill = "#444444"
            text_color = "#888888"
        else:
            fill = "#cc6666"
            text_color = "#ffaaaa"
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                 fill=fill, outline="#888", width=1, dash=(3, 3))
        self.canvas.create_text(cx, cy, text=piece.name, font=("楷体", 16, "bold"),
                                 fill=text_color)

    def _draw_movement_ghost(self):
        piece = self.movement_drag_piece
        col = round((self.drag_x - MARGIN_X) / CELL_SIZE)
        row = round((self.drag_y - MARGIN_Y) / CELL_SIZE)
        if not (0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS):
            return
        valid = (row, col) in self.valid_moves
        cx = MARGIN_X + col * CELL_SIZE
        cy = MARGIN_Y + row * CELL_SIZE
        r = PIECE_RADIUS
        if piece.side == SIDE_BLACK:
            fill = COLOR_BLACK_PIECE
            text_color = COLOR_BLACK_TEXT
        else:
            fill = COLOR_RED_PIECE
            text_color = COLOR_RED_TEXT
        outline = "#00aa00" if valid else "#aa0000"
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                 fill=fill, outline=outline, width=3)
        self.canvas.create_text(cx, cy, text=piece.name,
                                 font=("楷体", 16, "bold"), fill=text_color)
        if piece.piece_class == "B" or piece.is_upgraded:
            self.canvas.create_text(cx + r - 6, cy - r + 6, text="B",
                                     font=("Arial", 7, "bold"), fill="#ffcc00")

    # ==================== 拖放交互 ====================

    def on_hand_press(self, event):
        if self.game.phase != PHASE_PLACEMENT:
            return
        if self.game.current_player != self.my_side:
            return

        idx = self.hand_listbox.nearest(event.y)
        my_hand = self.game.black_hand if self.my_side == SIDE_BLACK else self.game.red_hand
        if idx < 0 or idx >= len(my_hand):
            return

        self.drag_piece = my_hand[idx]
        self.selected_hand_piece = self.drag_piece
        self.selected_piece = None
        self.valid_moves = []
        self.drag_active = True

        self._create_drag_overlay()

    def on_hand_drag(self, event):
        if not self.drag_active or not self.drag_window:
            return
        x = event.x_root + 15
        y = event.y_root + 15
        self.drag_window.geometry(f"+{x}+{y}")

        canvas_x = event.x_root - self.canvas.winfo_rootx()
        canvas_y = event.y_root - self.canvas.winfo_rooty()
        if (0 <= canvas_x < self.canvas.winfo_width() and
                0 <= canvas_y < self.canvas.winfo_height()):
            self.draw_board()

    def on_hand_release(self, event):
        if not self.drag_active:
            return
        self.drag_active = False
        self._destroy_drag_overlay()

        canvas_x = event.x_root - self.canvas.winfo_rootx()
        canvas_y = event.y_root - self.canvas.winfo_rooty()

        if (canvas_x < 0 or canvas_x >= self.canvas.winfo_width() or
                canvas_y < 0 or canvas_y >= self.canvas.winfo_height()):
            self.selected_hand_piece = None
            self.drag_piece = None
            self.draw_board()
            return

        col = round((canvas_x - MARGIN_X) / CELL_SIZE)
        row = round((canvas_y - MARGIN_Y) / CELL_SIZE)

        if 0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS:
            if self.drag_piece and self.game.is_valid_placement(self.drag_piece, row, col):
                piece = self.drag_piece
                self.game.place_piece(piece, row, col)
                if self.network:
                    self.network.send("place_piece", {
                        "piece_name": piece.name,
                        "piece_class": piece.piece_class,
                        "row": row,
                        "col": col,
                    })
                self.selected_hand_piece = None
                self.drag_piece = None
                self._check_placement_done()
                return

        self.selected_hand_piece = None
        self.drag_piece = None
        self.draw_board()

    def _create_drag_overlay(self):
        self._destroy_drag_overlay()
        piece = self.drag_piece
        if piece is None:
            return
        self.drag_window = tk.Toplevel(self.root)
        self.drag_window.overrideredirect(True)
        self.drag_window.attributes("-topmost", True)

        if piece.side == SIDE_BLACK:
            bg = "#1a1a1a"
            fg = "white"
        else:
            bg = "#cc0000"
            fg = "white"

        frame = tk.Frame(self.drag_window, bg=bg, bd=2, relief="solid")
        frame.pack()
        label = tk.Label(frame, text=piece.name, font=("楷体", 20, "bold"),
                          bg=bg, fg=fg, padx=10, pady=5)
        label.pack()
        if piece.piece_class == "B":
            tk.Label(frame, text="B类", font=("Arial", 8), bg=bg, fg="#ffcc00").pack()

        x = self.root.winfo_pointerx() + 15
        y = self.root.winfo_pointery() + 15
        self.drag_window.geometry(f"+{x}+{y}")

    def _destroy_drag_overlay(self):
        if self.drag_window:
            try:
                self.drag_window.destroy()
            except tk.TclError:
                pass
            self.drag_window = None

    # ==================== 棋盘交互 (拖放式走子) ====================

    def on_canvas_press(self, event):
        if self.game_over:
            return
        if self.game.current_player != self.my_side:
            return

        col = round((event.x - MARGIN_X) / CELL_SIZE)
        row = round((event.y - MARGIN_Y) / CELL_SIZE)

        if not (0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS):
            return

        if self.game.phase == PHASE_PLACEMENT:
            if self.selected_hand_piece and self.game.is_valid_placement(self.selected_hand_piece, row, col):
                piece = self.selected_hand_piece
                self.game.place_piece(piece, row, col)
                if self.network:
                    self.network.send("place_piece", {
                        "piece_name": piece.name,
                        "piece_class": piece.piece_class,
                        "row": row,
                        "col": col,
                    })
                self.selected_hand_piece = None
                self._check_placement_done()
            return

        if self.game.phase == PHASE_PLAYING and not self.pending_upgrade:
            piece = self.game.get_piece_at(row, col)
            if piece and piece.side == self.my_side:
                self.movement_drag_active = True
                self.movement_drag_piece = piece
                self.drag_from_row = row
                self.drag_from_col = col
                self.drag_x = event.x
                self.drag_y = event.y
                self.selected_piece = piece
                self.selected_hand_piece = None
                self.valid_moves = self.game.get_valid_moves(piece)
                self.draw_board()

    def on_canvas_drag(self, event):
        if not self.movement_drag_active:
            return
        self.drag_x = event.x
        self.drag_y = event.y
        self.draw_board()

    def on_canvas_release(self, event):
        if not self.movement_drag_active:
            return
        self.movement_drag_active = False
        piece = self.movement_drag_piece
        self.movement_drag_piece = None

        col = round((event.x - MARGIN_X) / CELL_SIZE)
        row = round((event.y - MARGIN_Y) / CELL_SIZE)

        if (0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS and
                (row, col) in self.valid_moves and
                (row, col) != (self.drag_from_row, self.drag_from_col)):
            self._execute_move(self.drag_from_row, self.drag_from_col, row, col)
        else:
            self.selected_piece = None
            self.valid_moves = []
            self.draw_board()

    def handle_remote_place(self, data):
        piece_name = data["piece_name"]
        piece_class = data["piece_class"]
        row = data["row"]
        col = data["col"]
        hand = self.game.get_hand_for_current_player()
        target = None
        for p in hand:
            if p.name == piece_name and p.piece_class == piece_class:
                target = p
                break
        if target is None:
            return
        self.game.place_piece(target, row, col)
        self._check_placement_done()

    def _check_placement_done(self):
        target = self.game.pieces_to_place_this_turn
        if self.game.move_count >= target:
            self.game.advance_placement_turn()
            self.selected_hand_piece = None
            self.drag_piece = None
            self._destroy_drag_overlay()
        self.update_ui()
        self.draw_board()
        if self.game.phase == PHASE_PLACEMENT:
            self._start_timer()

    def _execute_move(self, from_row, from_col, to_row, to_col):
        piece, captured = self.game.move_piece(from_row, from_col, to_row, to_col)
        if piece is None:
            return

        if self.network:
            self.network.send("move_piece", {
                "from_row": from_row,
                "from_col": from_col,
                "to_row": to_row,
                "to_col": to_col,
            })

        self.selected_piece = None
        self.valid_moves = []

        if piece and piece.is_soldier and not piece.is_upgraded:
            if (piece.side == SIDE_BLACK and to_row == 9) or \
               (piece.side == SIDE_RED and to_row == 0):
                self.pending_upgrade = piece
                self._stop_timer()
                self._show_upgrade_dialog()
                return

        self._check_movement_done()

    def _show_upgrade_dialog(self):
        piece = self.pending_upgrade
        if piece.side != self.my_side:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("兵升级")
        dialog.geometry("250x180")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"兵已到达敌方底线!\n请选择升级为:", font=("宋体", 12)).pack(pady=10)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack()

        if piece.side == SIDE_BLACK:
            options = ["馬", "砲", "車"]
        else:
            options = ["馬", "炮", "車"]

        for name in options:
            btn = tk.Button(btn_frame, text=name, font=("宋体", 12),
                            width=8, height=2,
                            command=lambda n=name: self._do_upgrade(n, dialog))
            btn.pack(side=tk.LEFT, padx=5, pady=10)

    def _do_upgrade(self, new_name, dialog):
        dialog.destroy()
        piece = self.pending_upgrade
        self.game.upgrade_soldier(piece, new_name)
        if self.network:
            self.network.send("upgrade_soldier", {
                "row": piece.row,
                "col": piece.col,
                "upgrade_to": new_name,
            })
        self.pending_upgrade = None
        self._check_movement_done()

    def handle_remote_move(self, data):
        from_row = data["from_row"]
        from_col = data["from_col"]
        to_row = data["to_row"]
        to_col = data["to_col"]
        self.game.move_piece(from_row, from_col, to_row, to_col)
        piece = self.game.get_piece_at(to_row, to_col)
        if piece and piece.is_soldier and not piece.is_upgraded:
            if (piece.side == SIDE_BLACK and to_row == 9) or \
               (piece.side == SIDE_RED and to_row == 0):
                self.pending_upgrade = piece
        if not self.pending_upgrade:
            self._check_movement_done()

    def handle_remote_upgrade(self, data):
        row, col = data["row"], data["col"]
        upgrade_to = data["upgrade_to"]
        piece = self.game.get_piece_at(row, col)
        if piece:
            self.game.upgrade_soldier(piece, upgrade_to)
        self.pending_upgrade = None
        self._check_movement_done()

    def _check_movement_done(self):
        if self.pending_upgrade:
            return

        self.game.history.append(self.game._board_key())
        if len(self.game.history) >= 4:
            recent = self.game.history[-4:]
            if recent[0] == recent[2] and recent[1] == recent[3]:
                if self.game.current_player == SIDE_BLACK:
                    self.game.penalties_black += 10
                else:
                    self.game.penalties_red += 10

        if self.game.move_count >= self.game.moves_this_turn:
            self.game.advance_movement_turn()

        winner, reason = self.game.check_game_over()
        if winner is not None or reason is not None:
            self._end_game(winner, reason)
            return

        self.update_ui()
        self.draw_board()
        self._start_timer()

    def _end_game(self, winner, reason):
        self.game_over = True
        self._stop_timer()
        self.game.phase = PHASE_GAME_OVER
        if winner:
            msg = f"{reason}"
        else:
            msg = reason or "游戏结束"
        if self.network:
            self.network.send("game_over", {"winner": winner, "reason": reason})
        self.update_ui()
        self.draw_board()
        self.root.after(500, lambda: messagebox.showinfo("游戏结束", msg))
        self.root.after(1000, self.setup_menu_ui)

    def handle_game_over(self, data):
        self.game_over = True
        self._stop_timer()
        self.game.phase = PHASE_GAME_OVER
        winner = data.get("winner")
        reason = data.get("reason", "对方判定游戏结束")
        self.update_ui()
        self.draw_board()
        self.root.after(500, lambda: messagebox.showinfo("游戏结束", reason))
        self.root.after(1000, self.setup_menu_ui)

    # ==================== UI更新 ====================

    def update_ui(self):
        self._update_status()
        self._update_hand_list()
        self._update_captured()
        self._update_score()
        self.draw_board()

    def _update_status(self):
        timer_text = f" | 倒计时: {max(0, self.move_timer)}秒" if (self.game.current_player == self.my_side and not self.game_over) else ""

        if self.game.phase == PHASE_PLACEMENT:
            player_name = "黑方(你)" if self.my_side == SIDE_BLACK else "红方(你)"
            opp_name = "红方" if self.my_side == SIDE_BLACK else "黑方"
            current = "你" if self.game.current_player == self.my_side else "对手"
            count = self.game.pieces_to_place_this_turn
            self.status_bar.config(text=f"布置阶段 | {player_name} vs {opp_name} | 当前: {current} ({count}枚){timer_text}")
        elif self.game.phase == PHASE_PLAYING:
            current = "你" if self.game.current_player == self.my_side else "对手"
            moves = self.game.moves_this_turn
            remaining = moves - self.game.move_count
            self.status_bar.config(text=f"行棋阶段 | 当前: {current} | 剩余步数: {remaining}/{moves}{timer_text}")
        elif self.game.phase == PHASE_GAME_OVER:
            self.status_bar.config(text="游戏结束")

    def _update_hand_list(self):
        self.hand_listbox.delete(0, tk.END)
        if self.game.phase == PHASE_PLACEMENT:
            my_hand = self.game.black_hand if self.my_side == SIDE_BLACK else self.game.red_hand
            if self.game.current_player == self.my_side:
                for p in my_hand:
                    cls = f"[{p.piece_class}类]" if p.piece_class == "B" else ""
                    self.hand_listbox.insert(tk.END, f"{p.name} {cls}")
                if not my_hand:
                    self.hand_listbox.insert(tk.END, "(布置完毕)")
            else:
                opp = "黑方" if self.game.current_player == SIDE_BLACK else "红方"
                self.hand_listbox.insert(tk.END, f"(等待{opp}布置...)")
        else:
            self.hand_listbox.insert(tk.END, "(布置完毕)")

    def _update_captured(self):
        self.captured_listbox.delete(0, tk.END)
        my_captured = self.game.black_captured if self.my_side == SIDE_BLACK else self.game.red_captured
        opp_captured = self.game.red_captured if self.my_side == SIDE_BLACK else self.game.black_captured
        self.captured_listbox.insert(tk.END, "--- 我方损失 ---")
        for p in my_captured:
            self.captured_listbox.insert(tk.END, f"  {p.name} ({p.score}分)")
        self.captured_listbox.insert(tk.END, "--- 敌方损失 ---")
        for p in opp_captured:
            self.captured_listbox.insert(tk.END, f"  {p.name} ({p.score}分)")

    def _update_score(self):
        bs = self.game._calculate_score(SIDE_BLACK)
        rs = self.game._calculate_score(SIDE_RED)
        bp = self.game.penalties_black
        rp = self.game.penalties_red
        self.score_label.config(text=f"黑: {bs-bp} (扣{bp}) | 红: {rs-rp} (扣{rp})")
        self.round_label.config(text=f"回合: {self.game.round_count}/{MAX_ROUNDS}")

    # ==================== 主循环 ====================

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_close(self):
        self._stop_timer()
        self._destroy_drag_overlay()
        if self.network:
            self.network.stop()
        self.root.destroy()


def main():
    app = DoubleChessApp()
    app.run()


if __name__ == "__main__":
    main()
