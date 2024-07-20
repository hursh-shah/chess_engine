import chess
import random
from math import sqrt, log
from qiskit import QuantumCircuit, Aer, transpile, assemble, execute
from qiskit.visualization import plot_histogram

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
        s = sorted(self.childNodes, key=lambda c: c.wins / c.visits + sqrt(2 * log(self.visits) / c.visits))[-1]
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

def grover_search(moves):
    n = len(moves)
    num_qubits = int(sqrt(n).bit_length())

    qc = QuantumCircuit(num_qubits)
    qc.h(range(num_qubits))

    # Placeholder for a real oracle function
    qc.cz(0, 1)

    # Diffusion operator
    qc.h(range(num_qubits))
    qc.x(range(num_qubits))
    qc.h(num_qubits - 1)
    qc.mct(list(range(num_qubits - 1)), num_qubits - 1)
    qc.h(num_qubits - 1)
    qc.x(range(num_qubits))
    qc.h(range(num_qubits))

    qc.measure_all()

    backend = Aer.get_backend('qasm_simulator')
    qobj = assemble(transpile(qc, backend))
    result = execute(qc, backend).result()
    counts = result.get_counts()
    plot_histogram(counts)

    most_likely_state = max(counts, key=counts.get)
    selected_move_index = int(most_likely_state, 2) % n

    return moves[selected_move_index]

def quantum_selection(node):
    if node.untriedMoves:
        return random.choice(node.untriedMoves)
    else:
        return grover_search([child.move for child in node.childNodes])

def rollout_policy(board):
    weights = {move: 1 for move in board.legal_moves}

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

    moves = list(weights.keys())
    probabilities = [weights[move] for move in moves]
    total_weight = sum(probabilities)
    if total_weight == 0:
        return random.choice(moves)
    probabilities = [p / total_weight for p in probabilities]
    move = random.choices(moves, probabilities)[0]

    return move

def UCT(rootstate, itermax):
    rootnode = Node(state=rootstate)

    for _ in range(itermax):
        node = rootnode
        state = rootstate.copy()

        while node.untriedMoves == [] and node.childNodes != []:
            node = node.UCTSelectChild()
            state.push(node.move)

        if node.untriedMoves != []:
            m = quantum_selection(node)
            state.push(m)
            node = node.AddChild(m, state)

        while not state.is_game_over():
            move = rollout_policy(state)
            state.push(move)

        while node is not None:
            node.Update(state.result())
            node = node.parentNode

    return sorted(rootnode.childNodes, key=lambda c: c.visits)[-1].move

OPENINGS = {
    "e4 e5": "Nf3",
    "e4 e5 Nf3 Nc6": "Bb5",
    "e4 e5 Nf3 Nc6 Bb5 Nf6": "O-O",
    "e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4": "d4",
    "e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 d4 Nd6": "Bxc6",
    "e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 d4 Nd6 Bxc6 dxc6": "dxe5",
    "e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 d4 Nd6 Bxc6 dxc6 dxe5 Nf5": "Qxd8+",
    "e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 d4 Nd6 Bxc6 dxc6 dxe5 Nf5 Qxd8+ Kxd8": "Nc3",
    "e4 c5": "Nf3",
    "e4 c5 Nf3 Nc6": "d4",
    "e4 c5 Nf3 Nc6 d4 cxd4": "Nxd4",
    "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 g6": "Nc3",
    "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 g6 Nc3 Bg7": "Be3",
    "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 g6 Nc3 Bg7 Be3 Nf6": "Bc4",
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
