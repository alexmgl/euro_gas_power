import time
import numpy as np
from matplotlib import pyplot as plt
import statsmodels.api as sm

# A simple timer decorator to track solve time.
def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} took {execution_time:.6f} seconds.")
        return result
    return wrapper

# Node for Dancing Links structure.
class Node:
    def __init__(self, c=None, s=None, llink=None, rlink=None, ulink=None, dlink=None):
        self.is_header = False
        self.name = None
        self.c = c            # reference to the column header
        self.s = s            # used for storing the row index (for option rows) or count (in column headers)
        # Initialize circular pointers if not provided.
        self.llink = llink if llink is not None else self
        self.rlink = rlink if rlink is not None else self
        self.ulink = ulink if ulink is not None else self
        self.dlink = dlink if dlink is not None else self

    # Remove self from horizontal list.
    def cover_h(self):
        self.rlink.llink = self.llink
        self.llink.rlink = self.rlink

    # Restore self in horizontal list.
    def uncover_h(self):
        self.rlink.llink = self
        self.llink.rlink = self

    # Remove self from vertical list.
    def cover_v(self):
        self.ulink.dlink = self.dlink
        self.dlink.ulink = self.ulink

    # Restore self in vertical list.
    def uncover_v(self):
        self.dlink.ulink = self
        self.ulink.dlink = self

# DLX-based Sudoku solver using Dancing Links.
class DLXSudoku:
    def __init__(self, board):
        self.board = board
        self.size = 9
        self.numbers = set(range(1, 10))
        # Build the list of valid options from blank cells.
        self.options = self.get_all_options()
        # Create the universe of constraints from these options.
        self.constraints = self.get_constraint_universe()
        # Build the DLX matrix.
        self.header = Node()  # master header
        self.header.is_header = True
        self.column_list = []    # list of column header nodes
        self.column_index = {}   # mapping from constraint name to its column node
        self.create_column_headers()
        self.create_rows()
        self.solution = []       # will store chosen nodes representing a solution

    # For each blank cell, check all candidate numbers and include only valid moves.
    def valid_moves(self):
        moves = []
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == 0:
                    for k in self.numbers:
                        if self.is_valid_move(i, j, k):
                            moves.append((i, j, k))
        return moves

    # Standard sudoku move validation.
    def is_valid_move(self, i, j, k):
        # Row check.
        if k in self.board[i]:
            return False
        # Column check.
        for r in range(self.size):
            if self.board[r][j] == k:
                return False
        # 3x3 sub-grid check.
        box_row, box_col = 3 * (i // 3), 3 * (j // 3)
        for r in range(box_row, box_row + 3):
            for c in range(box_col, box_col + 3):
                if self.board[r][c] == k:
                    return False
        return True

    # Build the list of options.
    # Each option is a tuple of four constraint labels:
    #   - Cell constraint: "pij" (cell at row i, col j is filled)
    #   - Row constraint: "r{i}{k}" (row i gets value k)
    #   - Column constraint: "c{j}{k}" (col j gets value k)
    #   - Box constraint: "b{x}{k}" (box x gets value k, with x = 3*(i//3)+(j//3))
    def get_all_options(self):
        options = []
        for (i, j, k) in self.valid_moves():
            box = 3 * (i // 3) + (j // 3)
            option = (f"p{i}{j}", f"r{i}{k}", f"c{j}{k}", f"b{box}{k}")
            options.append(option)
        return options

    # Get the sorted list of all constraints.
    def get_constraint_universe(self):
        cons = set()
        for option in self.options:
            for c in option:
                cons.add(c)
        return sorted(list(cons))  # sorting fixes the order

    # Create column header nodes and link them in a circular doubly linked list.
    def create_column_headers(self):
        # Initialize header's pointers to itself.
        self.header.rlink = self.header
        self.header.llink = self.header
        # For each constraint, create a header node.
        for cons in self.constraints:
            col = Node(s=0)
            col.name = cons
            col.is_header = True
            # Insert col to the right of the current last node.
            col.llink = self.header.llink
            col.rlink = self.header
            self.header.llink.rlink = col
            self.header.llink = col
            self.column_list.append(col)
            self.column_index[cons] = col

    # Create the DLX matrix rows from the options.
    def create_rows(self):
        self.row_nodes = []  # list of lists; each inner list holds nodes for one option row
        for option_index, option in enumerate(self.options):
            first_node = None
            row_nodes = []
            for cons in option:
                col = self.column_index[cons]
                new_node = Node(c=col, s=option_index)
                # Insert new_node into the bottom of column col.
                new_node.dlink = col
                new_node.ulink = col.ulink
                col.ulink.dlink = new_node
                col.ulink = new_node
                col.s += 1
                # Link new_node horizontally into this row.
                if first_node is None:
                    first_node = new_node
                    new_node.rlink = new_node
                    new_node.llink = new_node
                else:
                    last = first_node.llink
                    last.rlink = new_node
                    new_node.llink = last
                    new_node.rlink = first_node
                    first_node.llink = new_node
                row_nodes.append(new_node)
            self.row_nodes.append(row_nodes)

    # Cover a column: remove the column header and all rows in that column.
    def cover(self, col):
        col.cover_h()  # remove col header from horizontal list
        r = col.dlink
        while r != col:
            j = r.rlink
            while j != r:
                j.cover_v()
                j.c.s -= 1
                j = j.rlink
            r = r.dlink

    # Uncover a column: restore the column header and rows.
    def uncover(self, col):
        r = col.ulink
        while r != col:
            j = r.llink
            while j != r:
                j.c.s += 1
                j.uncover_v()
                j = j.llink
            r = r.ulink
        col.uncover_h()

    # Choose the column with the fewest nodes.
    def choose_column(self):
        min_count = float('inf')
        chosen = None
        col = self.header.rlink
        while col != self.header:
            if col.s < min_count:
                min_count = col.s
                chosen = col
            col = col.rlink
        return chosen

    # Recursive search for a solution.
    def search(self):
        # If header links to itself, all constraints are satisfied.
        if self.header.rlink == self.header:
            return True
        col = self.choose_column()
        if col.s == 0:
            return False  # dead end: no option for this constraint
        self.cover(col)
        r = col.dlink
        while r != col:
            self.solution.append(r)
            # Cover all columns for nodes in row r.
            j = r.rlink
            while j != r:
                self.cover(j.c)
                j = j.rlink
            next_r = r.dlink  # store pointer to next row before recursing
            if self.search():
                return True
            # Backtrack: remove r from solution and uncover columns.
            r = self.solution.pop()
            j = r.llink
            while j != r:
                self.uncover(j.c)
                j = j.llink
            r = next_r
        self.uncover(col)
        return False

    # Fill the board with the values from the solution.
    def fill_board(self):
        for node in self.solution:
            option_index = node.s
            option = self.options[option_index]
            # option is a tuple like ("pij", "rik", "cjk", "bxk")
            # Extract row and column from the cell constraint "pij"
            cell = option[0]
            i = int(cell[1])
            j = int(cell[2])
            # Extract the value from the row constraint "rik"
            val = int(option[1][2])
            self.board[i][j] = val
        return self.board

    # Solve the sudoku: return the filled board or None if no solution.
    def solve(self):
        if self.search():
            return self.fill_board()
        else:
            return None

# A wrapper class that uses DLXSudoku to solve a board.
class SudokuSolver:
    def __init__(self, board):
        self.board = board

    @timer_decorator
    def solve(self):
        solver = DLXSudoku(self.board)
        solved_board = solver.solve()
        return solved_board

# Testing the solver.
if __name__ == '__main__':
    # Example board with some zeros.
    board = [
        [1, 0, 4, 3, 8, 2, 9, 5, 6],
        [2, 0, 5, 4, 6, 7, 1, 3, 8],
        [3, 8, 6, 9, 5, 1, 4, 0, 2],
        [4, 6, 1, 5, 2, 3, 8, 9, 7],
        [7, 3, 8, 1, 4, 9, 6, 2, 5],
        [9, 5, 2, 8, 7, 6, 3, 1, 4],
        [5, 2, 9, 6, 3, 4, 7, 8, 1],
        [6, 0, 7, 2, 9, 8, 5, 4, 3],
        [8, 4, 3, 0, 1, 5, 2, 6, 9]
    ]

    solver = SudokuSolver(board)
    solved = solver.solve()
    if solved is not None:
        print("Solved Board:")
        for row in solved:
            print(row)
    else:
        print("No solution found.")

    # (Optional) Running multiple simulations and plotting runtime statistics.
    time_run = []
    filled_cells = []
    time_mean = []
    for i in range(35, 64):
        errors = 0
        sims = 100
        # Assume generate_board.generate_sudoku_board(difficulty=i) is defined elsewhere.
        for _ in range(sims):
            try:
                # Replace this with your board generator.
                from misc import generate_board
                board_gen = generate_board.generate_sudoku_board(difficulty=i)
                solver = SudokuSolver(board_gen)
                solver.solve()
            except Exception as e:
                errors += 1
                continue
        if time_run:
            my_array = np.array(time_run)
            time_mean.append(my_array.mean())
            filled_cells.append(i)
            print(f'{i} Mean: {my_array.mean():.5f} seconds, StdEv: {my_array.std():.5f}')
            plt.scatter(i, my_array.mean())
    plt.grid(axis='y')
    plt.show()

    # Fit a linear regression model (if desired).
    if time_mean and filled_cells:
        model = sm.OLS(time_mean, filled_cells).fit()
        print(model.summary())
