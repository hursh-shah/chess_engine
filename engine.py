import chess
import random
from math import sqrt, log

class Node:
    def __init__(self, move=None, parent=None, state=None):
        self.move = move
        self.parentNode = parent
        self.childNodes = []
        self.wins = 0
        self.visits = 0
        self.untriedMoves = list(state.legal_moves) 
        self.playerJustMoved = state.turn

    def UCTSelectChild(self):
        s = sorted(self.childNodes, key=lambda c: c.wins/c.visits + sqrt(2*log(self.visits)/c.visits))[-1]
        return s
    
    def AddChild(self, m, s):
        n = Node(move=m, parent=self, state=s)
        self.untriedMoves.remove(m)
        self.childNodes.append(n)
        return n
    
    def Update(self, result):
        self.visits += 1
        if result == '1-0':
            self.wins += 1
        elif result == '0-1':
            self.wins -= 1
        elif result == '1/2-1/2':
            self.wins += 0.5


def rollout_policy(board):
    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    piece_development_squares = [chess.C3, chess.G3, chess.C6, chess.G6,
                                 chess.F3, chess.F6]

    weights = {move: 1 for move in board.legal_moves}
    piece_moves = {}

    for move in board.legal_moves:
        if board.is_capture(move):
            weights[move] += 10  
        if board.is_check():
            weights[move] += 5  
        if board.gives_check(move):
            weights[move] += 5  
        if board.is_into_check(move):
            weights[move] -= 20  
        if board.is_pinned(board.turn, move.from_square):
            weights[move] -= 5
        if board.is_castling(move):
            weights[move] += 5  
        if move.to_square in piece_development_squares:
            weights[move] += 3

    moves = list(weights.keys())
    probabilities = [weights[move] for move in moves]
    total_weight = sum(probabilities)
    if total_weight == 0:
        return random.choice(moves)
    probabilities = [p / total_weight for p in probabilities]
    move = random.choices(moves, probabilities)[0]

    return move


def UCT(rootstate, itermax):
    """
    Conduct an MCTS search
    """
    rootnode = Node(state=rootstate)

    for _ in range(itermax):
        node = rootnode
        state = rootstate.copy()

        while node.untriedMoves == [] and node.childNodes != []:
            node = node.UCTSelectChild()
            state.push(node.move)

        if node.untriedMoves != []:  
            m = random.choice(node.untriedMoves) 
            state.push(m)
            node = node.AddChild(m, state) 

        while not state.is_game_over():
            move = rollout_policy(state)
            state.push(move)

        while node != None:
            node.Update(state.result()) 
            node = node.parentNode

    return sorted(rootnode.childNodes, key=lambda c: c.visits)[-1].move

OPENINGS = {
    # Ruy Lopez, Berlin Defense
    "e4 e5": "Nf3",
    "e4 e5 Nf3 Nc6": "Bb5",
    "e4 e5 Nf3 Nc6 Bb5 Nf6": "O-O",
    "e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4": "d4",
    "e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 d4 Nd6": "Bxc6",
    "e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 d4 Nd6 Bxc6 dxc6": "dxe5",
    "e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 d4 Nd6 Bxc6 dxc6 dxe5 Nf5": "Qxd8+",
    "e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 d4 Nd6 Bxc6 dxc6 dxe5 Nf5 Qxd8+ Kxd8": "Nc3",

    # Sicilian Defense, Accelerated Dragon
    "e4 c5": "Nf3",
    "e4 c5 Nf3 Nc6": "d4",
    "e4 c5 Nf3 Nc6 d4 cxd4": "Nxd4",
    "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 g6": "Nc3",
    "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 g6 Nc3 Bg7": "Be3",
    "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 g6 Nc3 Bg7 Be3 Nf6": "Bc4",

    # Accelerated Dragon as Black
    "e4 c5": "Nf3",
    "e4 c5 Nf3 Nc6": "d4",
    "e4 c5 Nf3 Nc6 d4 cxd4": "Nxd4",
    "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 g6": "Nc3",
    "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 Bg7": "Be3",
    "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 Bg7 Be3 Nf6": "f3",
}

def get_opening_move(board):
    board_str = " ".join(str(board.move_stack[i]) for i in range(len(board.move_stack)))

    if board_str in OPENINGS:
        return chess.Move.from_uci(OPENINGS[board_str])

    return None


def play_game():
    board = chess.Board()
    move_number = 1
    while not board.is_game_over():
        print(f"Move number: {move_number}")
        print(board, "\n")
        opening_move = get_opening_move(board)
        if opening_move is not None:
            move = opening_move
        else:
            move = UCT(board, 50)  
        board.push(move)
        print(f"Move made: {move}\n")
        print("------")
        move_number += 1
    print(board, "\n")

play_game()
