# 双步象棋 - 游戏引擎

from constants import *


class Piece:
    def __init__(self, name, piece_class, side, row=-1, col=-1):
        self.name = name          # 棋子名称 (将/帅/士/仕/相/象/馬/車/砲/炮/卒/兵)
        self.piece_class = piece_class  # "A" or "B"
        self.side = side          # "black" or "red"
        self.row = row            # 棋盘行 (0-9)
        self.col = col            # 棋盘列 (0-8)
        self.is_upgraded = False  # 兵是否已升级

    @property
    def is_general(self):
        return self.name in ("将", "帅")

    @property
    def is_advisor(self):
        return self.name in ("士", "仕")

    @property
    def is_elephant(self):
        return self.name in ("相", "象")

    @property
    def is_horse(self):
        return self.name == "馬"

    @property
    def is_chariot(self):
        return self.name == "車"

    @property
    def is_cannon(self):
        return self.name in ("砲", "炮")

    @property
    def is_soldier(self):
        return self.name in ("卒", "兵")

    @property
    def is_placed(self):
        return self.row >= 0 and self.col >= 0

    @property
    def score(self):
        return PIECE_SCORES.get(self.name, 0)

    def clone(self):
        p = Piece(self.name, self.piece_class, self.side, self.row, self.col)
        p.is_upgraded = self.is_upgraded
        return p

    def __repr__(self):
        return f"{self.name}({self.piece_class},{self.side[:1]})@{self.row},{self.col}"


class GameState:
    def __init__(self):
        self.phase = PHASE_WAITING
        self.current_player = SIDE_BLACK  # 黑先
        self.pieces = []      # 所有在棋盘上的棋子
        self.black_hand = []  # 黑方手中待布置棋子
        self.red_hand = []    # 红方手中待布置棋子
        self.black_captured = []  # 黑方被吃棋子
        self.red_captured = []    # 红方被吃棋子
        self.move_count = 0       # 当前回合移动计数 (布置时是放置计数)
        self.is_first_turn = True # 是否第一回合 (黑1步)
        self.round_count = 0      # 回合数
        self.history = []         # 历史棋盘快照 (用于检测循环)
        self.last_move = None     # 最后一步走子信息
        self.penalties_black = 0  # 黑方扣分
        self.penalties_red = 0    # 红方扣分
        self.placed_count_black = 0
        self.placed_count_red = 0
        self.init_hands()

    def init_hands(self):
        self.black_hand = []
        self.red_hand = []
        for name, cls in ALL_BLACK_PIECES:
            self.black_hand.append(Piece(name, cls, SIDE_BLACK))
        for name, cls in ALL_RED_PIECES:
            self.red_hand.append(Piece(name, cls, SIDE_RED))

    @property
    def pieces_to_place_this_turn(self):
        """当前玩家本轮可布置的棋子数"""
        if self.current_player == SIDE_BLACK:
            remaining = len(self.black_hand)
        else:
            remaining = len(self.red_hand)
        if remaining <= 0:
            return 0
        if self.is_first_turn and self.current_player == SIDE_BLACK:
            return 1
        return min(2, remaining)

    @property
    def moves_this_turn(self):
        """当前玩家本轮可行走的步数"""
        if self.is_first_turn and self.current_player == SIDE_BLACK:
            return 1
        return 2

    @property
    def is_placement_phase(self):
        return self.phase == PHASE_PLACEMENT

    @property
    def is_playing_phase(self):
        return self.phase == PHASE_PLAYING

    def get_piece_at(self, row, col):
        for p in self.pieces:
            if p.row == row and p.col == col:
                return p
        return None

    def get_hand_for_current_player(self):
        if self.current_player == SIDE_BLACK:
            return self.black_hand
        return self.red_hand

    def get_pieces_for_player(self, side):
        return [p for p in self.pieces if p.side == side]

    def is_valid_placement(self, piece, row, col):
        """检查布置位置是否合法"""
        if row < 0 or row >= BOARD_ROWS or col < 0 or col >= BOARD_COLS:
            return False
        if self.get_piece_at(row, col) is not None:
            return False
        # 将/士 只能放置在九宫格内
        if piece.is_general or piece.is_advisor:
            pc_start, pc_end = PALACE_COLS
            if not (pc_start <= col <= pc_end):
                return False
            if piece.side == SIDE_BLACK:
                pr_start, pr_end = PALACE_ROWS_BLACK
            else:
                pr_start, pr_end = PALACE_ROWS_RED
            if not (pr_start <= row <= pr_end):
                return False
        if piece.is_soldier:
            if piece.side == SIDE_BLACK and row != SOLDIER_ROW_BLACK:
                return False
            if piece.side == SIDE_RED and row != SOLDIER_ROW_RED:
                return False
        else:
            if piece.side == SIDE_BLACK and row >= 5:
                return False
            if piece.side == SIDE_RED and row <= 4:
                return False
        return True

    def place_piece(self, piece, row, col):
        """布置棋子"""
        piece.row = row
        piece.col = col
        self.pieces.append(piece)
        hand = self.get_hand_for_current_player()
        if piece in hand:
            hand.remove(piece)
        if self.current_player == SIDE_BLACK:
            self.placed_count_black += 1
        else:
            self.placed_count_red += 1
        self.move_count += 1
        return True

    def advance_placement_turn(self):
        """布置阶段切换到下一轮"""
        self.move_count = 0
        if self.current_player == SIDE_BLACK:
            self.current_player = SIDE_RED
        else:
            self.current_player = SIDE_BLACK
        if self.is_first_turn and self.current_player == SIDE_BLACK:
            pass  # 黑方第一轮已过
        if self.is_first_turn and self.current_player == SIDE_RED:
            self.is_first_turn = False
        # 检查布置是否完毕
        if len(self.black_hand) == 0 and len(self.red_hand) == 0:
            self.phase = PHASE_PLAYING
            self.current_player = SIDE_BLACK
            self.move_count = 0
            self.is_first_turn = True
            self.round_count = 0

    def get_valid_moves(self, piece):
        """获取棋子的所有合法走法"""
        if piece.is_general:
            return self._get_general_moves(piece)
        elif piece.is_advisor:
            return self._get_advisor_moves(piece)
        elif piece.is_elephant:
            return self._get_elephant_moves(piece)
        elif piece.is_horse:
            return self._get_horse_moves(piece)
        elif piece.is_chariot:
            return self._get_chariot_moves(piece)
        elif piece.is_cannon:
            return self._get_cannon_moves(piece)
        elif piece.is_soldier:
            return self._get_soldier_moves(piece)
        return []

    def _get_general_moves(self, piece):
        """将/帅: 九宫内横走1格或竖走1格"""
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        if piece.side == SIDE_BLACK:
            pr, pr_end = PALACE_ROWS_BLACK
        else:
            pr, pr_end = PALACE_ROWS_RED
        pc, pc_end = PALACE_COLS
        for dr, dc in directions:
            nr, nc = piece.row + dr, piece.col + dc
            if pr <= nr <= pr_end and pc <= nc <= pc_end:
                target = self.get_piece_at(nr, nc)
                if target is None or target.side != piece.side:
                    moves.append((nr, nc))
        return moves

    def _get_advisor_moves(self, piece):
        """士/仕: 九宫内斜向1格"""
        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        if piece.side == SIDE_BLACK:
            pr, pr_end = PALACE_ROWS_BLACK
        else:
            pr, pr_end = PALACE_ROWS_RED
        pc, pc_end = PALACE_COLS
        for dr, dc in directions:
            nr, nc = piece.row + dr, piece.col + dc
            if pr <= nr <= pr_end and pc <= nc <= pc_end:
                target = self.get_piece_at(nr, nc)
                if target is None or target.side != piece.side:
                    moves.append((nr, nc))
        return moves

    def _get_elephant_moves(self, piece):
        """相/象: 本界内斜45度不跨子走任意格"""
        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        if piece.side == SIDE_BLACK:
            territory = BLACK_TERRITORY
        else:
            territory = RED_TERRITORY
        for dr, dc in directions:
            nr, nc = piece.row + dr, piece.col + dc
            while 0 <= nr < BOARD_ROWS and 0 <= nc < BOARD_COLS:
                if nr not in territory or nc < 0 or nc >= BOARD_COLS:
                    break
                target = self.get_piece_at(nr, nc)
                if target is None:
                    moves.append((nr, nc))
                elif target.side != piece.side:
                    moves.append((nr, nc))
                    break  # 吃掉对方棋子后停止
                else:
                    break  # 遇到己方棋子停止
                nr += dr
                nc += dc
        return moves

    def _get_horse_moves(self, piece):
        """馬: 全局走日字形(无别脚)"""
        moves = []
        # 日字形的8个方向
        horse_offsets = [
            (-2, -1), (-2, 1),
            (-1, -2), (-1, 2),
            (1, -2), (1, 2),
            (2, -1), (2, 1),
        ]
        for dr, dc in horse_offsets:
            nr, nc = piece.row + dr, piece.col + dc
            if 0 <= nr < BOARD_ROWS and 0 <= nc < BOARD_COLS:
                target = self.get_piece_at(nr, nc)
                if target is None or target.side != piece.side:
                    moves.append((nr, nc))
        return moves

    def _get_chariot_moves(self, piece):
        """車: 全局纵横线不跨子走任意格"""
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in directions:
            nr, nc = piece.row + dr, piece.col + dc
            while 0 <= nr < BOARD_ROWS and 0 <= nc < BOARD_COLS:
                target = self.get_piece_at(nr, nc)
                if target is None:
                    moves.append((nr, nc))
                elif target.side != piece.side:
                    moves.append((nr, nc))
                    break
                else:
                    break
                nr += dr
                nc += dc
        return moves

    def _get_cannon_moves(self, piece):
        """炮: 不跨子走任意格, 隔1子吃子"""
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in directions:
            nr, nc = piece.row + dr, piece.col + dc
            # 非吃子移动
            while 0 <= nr < BOARD_ROWS and 0 <= nc < BOARD_COLS:
                target = self.get_piece_at(nr, nc)
                if target is None:
                    moves.append((nr, nc))
                else:
                    break  # 遇到棋子停止
                nr += dr
                nc += dc
            # 吃子移动: 跳过第一个棋子后的目标
            nr, nc = piece.row + dr, piece.col + dc
            screen_found = False
            while 0 <= nr < BOARD_ROWS and 0 <= nc < BOARD_COLS:
                target = self.get_piece_at(nr, nc)
                if not screen_found:
                    if target is not None:
                        screen_found = True  # 找到炮架
                else:
                    if target is not None:
                        if target.side != piece.side:
                            moves.append((nr, nc))
                        break  # 无论是否可吃都停止
                nr += dr
                nc += dc
        return moves

    def _get_soldier_moves(self, piece):
        """兵/卒: 本界只能向前1格, 过河可横/前1格"""
        moves = []
        if piece.is_upgraded:
            # 已升级, 按B类棋子规则
            return self._get_b_class_moves(piece)
        # 确定前进方向
        if piece.side == SIDE_BLACK:
            forward = 1  # 黑方向下走
            crossed = piece.row >= 5  # 是否已过河
            back_row = 9  # 敌方底线
        else:
            forward = -1  # 红方向上走
            crossed = piece.row <= 4
            back_row = 0
        # 前方1格
        nr = piece.row + forward
        nc = piece.col
        if 0 <= nr < BOARD_ROWS:
            target = self.get_piece_at(nr, nc)
            if target is None or target.side != piece.side:
                moves.append((nr, nc))
        # 过河后可横向走
        if crossed:
            for dc in (-1, 1):
                nc = piece.col + dc
                if 0 <= nc < BOARD_COLS:
                    target = self.get_piece_at(piece.row, nc)
                    if target is None or target.side != piece.side:
                        moves.append((piece.row, nc))
        return moves

    def _get_b_class_moves(self, piece):
        """已升级兵按B类走法"""
        if piece.is_horse:
            return self._get_horse_moves(piece)
        elif piece.is_cannon:
            return self._get_cannon_moves(piece)
        elif piece.is_chariot:
            return self._get_chariot_moves(piece)
        return []

    def move_piece(self, from_row, from_col, to_row, to_col):
        """移动棋子并返回是否吃子"""
        piece = self.get_piece_at(from_row, from_col)
        if piece is None:
            return None, None
        captured = self.get_piece_at(to_row, to_col)
        if captured:
            self.pieces.remove(captured)
            if captured.side == SIDE_BLACK:
                self.black_captured.append(captured)
            else:
                self.red_captured.append(captured)
        piece.row = to_row
        piece.col = to_col
        self.move_count += 1
        self.last_move = (from_row, from_col, to_row, to_col)
        # 检查兵是否到达敌方底线
        if piece.is_soldier and not piece.is_upgraded:
            if piece.side == SIDE_BLACK and to_row == 9:
                return piece, captured
            if piece.side == SIDE_RED and to_row == 0:
                return piece, captured
        return piece, captured

    def upgrade_soldier(self, piece, new_name):
        """将兵升级为B类棋子"""
        piece.name = new_name
        piece.piece_class = "B"
        piece.is_upgraded = True

    def get_upgrade_options(self):
        """获取可升级的B类棋子选项"""
        cannon_name = "砲" if self.current_player == SIDE_BLACK else "炮"
        return [("馬", "B"), (cannon_name, "B"), ("車", "B")]

    def advance_movement_turn(self):
        """切换到下一轮行棋"""
        self.move_count = 0
        if self.current_player == SIDE_BLACK:
            self.current_player = SIDE_RED
        else:
            self.current_player = SIDE_BLACK
            self.round_count += 1
        if self.is_first_turn:
            self.is_first_turn = False

    def check_game_over(self):
        """检查游戏是否结束"""
        # 检查是否被吃掉两个将
        black_generals_lost = sum(1 for p in self.black_captured if p.is_general)
        red_generals_lost = sum(1 for p in self.red_captured if p.is_general)
        if black_generals_lost >= 2:
            return SIDE_RED, "红方胜利! (吃掉黑方两将)"
        if red_generals_lost >= 2:
            return SIDE_BLACK, "黑方胜利! (吃掉红方两将)"
        # 检查60回合判分
        if self.round_count >= MAX_ROUNDS:
            return self._score_judgement()
        return None, None

    def _score_judgement(self):
        """按分数判胜负"""
        black_score = self._calculate_score(SIDE_BLACK) - self.penalties_black
        red_score = self._calculate_score(SIDE_RED) - self.penalties_red
        if black_score > red_score:
            return SIDE_BLACK, f"黑方分数胜利! ({black_score} : {red_score})"
        elif red_score > black_score:
            return SIDE_RED, f"红方分数胜利! ({red_score} : {black_score})"
        else:
            return None, f"平局! ({black_score} : {red_score})"

    def _calculate_score(self, side):
        """计算一方总分"""
        total = 0
        for p in self.pieces:
            if p.side == side:
                total += p.score
        return total

    def check_cycle(self):
        """检测循环, 返回主动循环方"""
        current_key = self._board_key()
        self.history.append(current_key)
        if len(self.history) >= 4:
            # 检查最近4个状态是否有重复
            recent = self.history[-4:]
            if recent[0] == recent[2] and recent[1] == recent[3]:
                # 双方走成循环, 主动方扣分
                return self.current_player
        return None

    def _board_key(self):
        """生成棋盘状态快照"""
        key = []
        for p in sorted(self.pieces, key=lambda x: (x.row, x.col)):
            key.append((p.name, p.piece_class, p.side, p.row, p.col, p.is_upgraded))
        return tuple(key)

    def clone(self):
        """深拷贝游戏状态"""
        import copy
        return copy.deepcopy(self)
