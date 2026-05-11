# 双步象棋 - 常量定义

# 棋盘尺寸
BOARD_COLS = 9      # 纵向9线
BOARD_ROWS = 10     # 横向10线

# 棋盘像素参数
CELL_SIZE = 60
MARGIN_X = 50
MARGIN_Y = 50
BOARD_WIDTH = (BOARD_COLS - 1) * CELL_SIZE
BOARD_HEIGHT = (BOARD_ROWS - 1) * CELL_SIZE
CANVAS_WIDTH = MARGIN_X * 2 + BOARD_WIDTH
CANVAS_HEIGHT = MARGIN_Y * 2 + BOARD_HEIGHT

# 棋子半径
PIECE_RADIUS = 25

# 颜色
COLOR_BOARD = "#DEB887"
COLOR_LINE = "#000000"
COLOR_BLACK_PIECE = "#1a1a1a"
COLOR_BLACK_TEXT = "#ffffff"
COLOR_RED_PIECE = "#cc0000"
COLOR_RED_TEXT = "#ffffff"
COLOR_SELECTED = "#00ff00"
COLOR_VALID_MOVE = "#88cc88"
COLOR_LAST_MOVE = "#ffff88"
COLOR_RIVER = "#0000cc"

# 阵营
SIDE_BLACK = "black"
SIDE_RED = "red"

# A类棋子定义 (每方)
# 将(2) 士(1) 相(2) 马(2) 车(2) 炮(2) 兵(5) = 16
CLASS_A_BLACK = [
    ("将", "A"), ("将", "A"),
    ("士", "A"),
    ("相", "A"), ("相", "A"),
    ("馬", "A"), ("馬", "A"),
    ("車", "A"), ("車", "A"),
    ("砲", "A"), ("砲", "A"),
    ("卒", "A"), ("卒", "A"), ("卒", "A"), ("卒", "A"), ("卒", "A"),
]
CLASS_A_RED = [
    ("帅", "A"), ("帅", "A"),
    ("仕", "A"),
    ("象", "A"), ("象", "A"),
    ("馬", "A"), ("馬", "A"),
    ("車", "A"), ("車", "A"),
    ("炮", "A"), ("炮", "A"),
    ("兵", "A"), ("兵", "A"), ("兵", "A"), ("兵", "A"), ("兵", "A"),
]

# B类棋子定义 (每方3个)
CLASS_B_BLACK = [("馬", "B"), ("砲", "B"), ("車", "B")]
CLASS_B_RED = [("馬", "B"), ("炮", "B"), ("車", "B")]

# 所有待布置棋子 (仅A类, 16枚/方)
# B类棋子(马/炮/车)仅通过兵升变获得，不直接布置
ALL_BLACK_PIECES = CLASS_A_BLACK
ALL_RED_PIECES = CLASS_A_RED

# 九宫范围 (行列索引)
PALACE_ROWS_BLACK = (0, 2)
PALACE_ROWS_RED = (7, 9)
PALACE_COLS = (3, 5)

# 楚河汉界 (河界在第4行和第5行之间)
RIVER_ROW_BLACK = 4  # 黑方河界行 (己方最后一行)
RIVER_ROW_RED = 5    # 红方河界行 (己方第一行)

# 兵卒布置限制行
SOLDIER_ROW_BLACK = 3  # 黑卒只能放在第3行
SOLDIER_ROW_RED = 6    # 红兵只能放在第6行

# 黑方领土行 (0-4), 红方领土行 (5-9)
BLACK_TERRITORY = range(0, 5)
RED_TERRITORY = range(5, 10)

# 棋子分值
SCORE_GENERAL = 5      # 将/帅
SCORE_CHARIOT = 4      # 车
SCORE_ADVISOR = 3      # 士/仕
SCORE_ELEPHANT = 3     # 相/象
SCORE_HORSE = 3        # 马
SCORE_CANNON = 3       # 炮
SCORE_SOLDIER = 2      # 兵/卒

PIECE_SCORES = {
    "将": SCORE_GENERAL, "帅": SCORE_GENERAL,
    "士": SCORE_ADVISOR, "仕": SCORE_ADVISOR,
    "相": SCORE_ELEPHANT, "象": SCORE_ELEPHANT,
    "馬": SCORE_HORSE,
    "車": SCORE_CHARIOT,
    "砲": SCORE_CANNON, "炮": SCORE_CANNON,
    "卒": SCORE_SOLDIER, "兵": SCORE_SOLDIER,
}

# 游戏阶段
PHASE_WAITING = "waiting"       # 等待连接
PHASE_CONFIRM = "confirm"       # 确认进入房间
PHASE_PLACEMENT = "placement"   # 布置阶段
PHASE_PLAYING = "playing"       # 行棋阶段
PHASE_GAME_OVER = "game_over"   # 结束

# 网络
DEFAULT_PORT = 55555
BUFFER_SIZE = 4096

# 计时器 (秒)
PLACEMENT_TIMER = 30  # 布置阶段每手棋30秒
PLAYING_TIMER = 60    # 行棋阶段每手棋60秒

# 回合限制
MAX_ROUNDS = 60  # 60回合未吃将则判分

# 移动计数模式
# 黑方先走: 第1回合黑1步、红2步，之后都是2步交替
# 布置: 黑1个、红2个，之后都是2个交替
