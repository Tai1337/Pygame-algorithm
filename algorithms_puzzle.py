
import heapq

GRID_SIZE = 3

SOLVED_BOARD_TUPLE = ((1, 2, 3), (4, 5, 6), (7, 8, 0))

_GOAL_POSITIONS = {}

def _precompute_goal_positions():
    
    global _GOAL_POSITIONS
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            tile_value = SOLVED_BOARD_TUPLE[r][c]
            if tile_value != 0:
                _GOAL_POSITIONS[tile_value] = (r, c)

_precompute_goal_positions() # Call precomputation when module is loaded

def _list_to_tuple(board_list):
    """Converts a board represented as a list of lists to a tuple of tuples."""
    return tuple(map(tuple, board_list))

def _get_empty_pos(board_tuple):
    """Finds the (row, col) of the empty tile (0) in a board_tuple."""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board_tuple[r][c] == 0:
                return r, c
    return None # Should not happen in a valid 8-puzzle board

def _calculate_manhattan_distance(board_tuple):
    """
    Calculates the sum of Manhattan distances for all numbered tiles
    from their current position to their goal position.
    """
    distance = 0
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            tile_value = board_tuple[r][c]
            if tile_value != 0: # Skip the empty tile
                goal_r, goal_c = _GOAL_POSITIONS[tile_value]
                distance += abs(r - goal_r) + abs(c - goal_c)
    return distance

def _get_successor_states(board_tuple):
    """
    Generates all valid successor states from the current board_tuple.
    Returns a list of tuples: (new_board_tuple, move_rc).
    move_rc is the (row, col) of the tile that was moved into the empty space.
    """
    successors = []
    er, ec = _get_empty_pos(board_tuple) # Empty tile's current row and column

    # Define potential moves: (dr, dc) for change in row and column
    # These correspond to moving a tile from (nr, nc) into (er, ec)
    # dr, dc are relative to the empty space to find the tile to move
    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # Tile to the Right, Left, Down, Up of empty
        nr, nc = er + dr, ec + dc # Position of the tile to be potentially moved

        if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE: # Check if (nr, nc) is within grid bounds
            # Create a mutable copy of the board to perform the swap
            temp_list_of_lists = [list(row) for row in board_tuple]

            # Swap the tile at (nr, nc) with the empty tile at (er, ec)
            moved_tile_value = temp_list_of_lists[nr][nc]
            temp_list_of_lists[er][ec] = moved_tile_value
            temp_list_of_lists[nr][nc] = 0 # The tile's original spot becomes empty

            new_board_tuple = tuple(map(tuple, temp_list_of_lists))
            # The "move" is the coordinate of the tile that was effectively "clicked" or moved
            successors.append((new_board_tuple, (nr, nc)))
    return successors

def solve_puzzle_a_star(initial_board_list):
    """
    Solves the 8-Puzzle using the A* search algorithm with Manhattan distance heuristic.

    Args:
        initial_board_list (list of lists): The starting configuration of the puzzle.

    Returns:
        list: A list of (row, col) tuples representing the sequence of tile coordinates
              to move to solve the puzzle. Returns an empty list if the puzzle is
              already solved. Returns None if the puzzle is unsolvable (though this
              function assumes solvable puzzles from the game).
    """
    initial_board_tuple = _list_to_tuple(initial_board_list)

    if initial_board_tuple == SOLVED_BOARD_TUPLE:
        return [] # Puzzle is already solved

    # Priority queue stores: (f_score, g_score, current_board_tuple, path_of_moves)
    # path_of_moves is a list of (r,c) of the tile that was moved.
    open_set = []
    g_initial = 0
    h_initial = _calculate_manhattan_distance(initial_board_tuple)
    f_initial = g_initial + h_initial
    heapq.heappush(open_set, (f_initial, g_initial, initial_board_tuple, []))

    # closed_set stores board_tuples that have been expanded (popped and processed).
    # This prevents re-processing states for which the optimal path is already found.
    closed_set = set()

    while open_set:
        f_score, g_score, current_board, path = heapq.heappop(open_set)

        if current_board in closed_set:
            continue # Already found a better or equal path to this state
        closed_set.add(current_board)

        if current_board == SOLVED_BOARD_TUPLE:
            return path # Solution found

        for next_board_tuple, move_coord in _get_successor_states(current_board):
            if next_board_tuple in closed_set:
                continue

            tentative_g_score = g_score + 1 # Cost of each move is 1
            h_score_next = _calculate_manhattan_distance(next_board_tuple)
            f_score_next = tentative_g_score + h_score_next

            new_path = path + [move_coord]
            heapq.heappush(open_set, (f_score_next, tentative_g_score, next_board_tuple, new_path))

    return None # Should only be reached if the puzzle is unsolvable

# --- Algorithm Definitions for Integration ---

PUZZLE_ALGORITHMS_MAP = {
    "A* Solver (Manhattan)": solve_puzzle_a_star,
    # You can add other solving algorithms here if you develop them
    # "IDA* Solver": solve_puzzle_ida_star, # Example
}

PUZZLE_ALGORITHMS_COSTS = {
    "A* Solver (Manhattan)": 50,  # Example cost: 50 in-game money
    # "IDA* Solver": 70,
}

PUZZLE_ALGORITHMS_INFO = {
    "A* Solver (Manhattan)": "Automatically solves the puzzle using A* search with the Manhattan distance heuristic. Finds an optimal (shortest) solution.",
    # "IDA* Solver": "Uses Iterative Deepening A* to find a solution. Memory efficient.",
}

# --- Example Usage (for testing this file directly) ---
if __name__ == '__main__':
    print("Testing 8-Puzzle Solver...")

    # Example solvable puzzle (0 is the empty space)
    # Easy one:
    # 1 2 3
    # 4 5 0
    # 7 8 6
    # solvable_board = [
    #     [1, 2, 3],
    #     [4, 5, 0],
    #     [7, 8, 6]
    # ]
    # Expected moves (approx): move (1,2) (tile 6) -> (1,1), then (2,2) (tile 6) -> (1,2)
    # My function expects move (r,c) of the tile to move.
    # If empty is at (1,2) [value 0]
    # move tile 6 (at (2,2)) -> (1,2) means clicking (2,2). Board becomes:
    # 1 2 3
    # 4 5 6
    # 7 8 0  -- Solved!
    # Path: [(2,2)]

    solvable_board = [
        [1, 2, 3],
        [4, 0, 5], # Empty in middle
        [7, 8, 6]
    ]
    # Target:
    # 1 2 3
    # 4 5 6
    # 7 8 0
    # Moves:
    # 1. Click (1,2) (tile 5):
    #    1 2 3
    #    4 5 0
    #    7 8 6
    # 2. Click (2,2) (tile 6):
    #    1 2 3
    #    4 5 6
    #    7 8 0  -- Solved
    # Path: [(1,2), (2,2)]


    print(f"Initial board: {solvable_board}")
    solution_path = solve_puzzle_a_star(solvable_board)

    if solution_path is not None:
        print(f"Solution found! Path of moves (tile r,c to click): {solution_path}")
        print(f"Number of moves: {len(solution_path)}")
    else:
        print("No solution found (or puzzle is unsolvable).")

    already_solved_board = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 0]
    ]
    print(f"\nInitial board (already solved): {already_solved_board}")
    solution_path_solved = solve_puzzle_a_star(already_solved_board)
    if solution_path_solved is not None:
        print(f"Solution found! Path: {solution_path_solved}")
        print(f"Number of moves: {len(solution_path_solved)}")
    else:
        print("Error with already solved board.")


    
    complex_board = [
        [7, 2, 4],
        [5, 0, 6],
        [8, 3, 1]
    ]
    print(f"\nInitial board (complex): {complex_board}")
    solution_path_complex = solve_puzzle_a_star(complex_board)
    if solution_path_complex is not None:
        print(f"Solution found! Path: {solution_path_complex}")
        print(f"Number of moves: {len(solution_path_complex)}")
    else:
        print("No solution found for complex board.")