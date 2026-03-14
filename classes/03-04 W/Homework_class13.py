"""
Homework: Reading Code with State / Transitions / Invariants (Tic-Tac-Toe)

This program brute-forces tic-tac-toe WITHOUT recursion.

What it actually counts:
- It explores all possible games where X starts and players alternate.
- The search STOPS as soon as someone wins (a terminal state).
- It also records full boards that end in a tie.
- It tracks UNIQUE *terminal* boards “up to symmetry” (rotations + reflections),
  meaning rotated/flipped versions are treated as the same terminal board.

YOUR TASKS:

RULE:  Do not change any executable code (no reformatting logic, no renaming variables, no moving lines). 
       Only add/replace comments and docstrings.
       
1) Define STATE for this program.
- State is the collection of values that change while the search runs.
What variables change as the program runs?
   - The main changing state is the current board, stored in board.
   - The running totals also belong to state: unique_seen, full_boards,
     x_wins_on_full_board, draws_on_full_board, x_wins, o_wins, and ties.
   - move_number is also part of the current search state because it tells how
     deep into a game we are.
2) Explain where TRANSITIONS happen.
   - Where does the state change? (where in the code, which functions)
- Transitions happen whenever the state changes.
   - The biggest transitions are in the nested loops where a square changes
     from ' ' to 'X' or 'O'.
   - More transitions happen when moves are undone by setting a square back to ' '.
   - State also changes inside record_unique_board() and record_full_board()
     when the counters and unique_seen list are updated.
3) Identify 4 INVARIANTS.
   - What properties remain true as the program runs (and what checks enforce them).
 - Invariant 1: Players alternate correctly, with X moving on odd-numbered moves
     and O moving on even-numbered moves. This is enforced by the loop structure.
   - Invariant 2: No move is placed on an occupied square. This is enforced by
     checks like if board[o1] == ' ' before placing a mark.
   - Invariant 3: Once a win appears, the search does not continue deeper from
     that board. This is enforced by should_continue() calling has_winner().
   - Invariant 4: unique_seen stores only one representative for each terminal
     board up to symmetry. This is enforced by converting a board to its
     standard_form() and checking rep not in unique_seen before appending.
   - For instance: has_winner() is a check; the invariant is “we do not continue exploring after a win.”
4) For every function that says ''' TODO ''', replace that docstring with a real explanation
   of what the function does (1-4 sentences).
5) Add inline comments anywhere you see "# TODO" explaining what that code block is doing.
6) DO NOT USE AI. Write 5-8 sentences explaining one non-obvious part (choose one):  
   (a) symmetry logic (what makes a board unique), 
   (b) why we undo moves,  
The program must remove the move to return the board to its previous state once it has explored every possible outcome of that decision.
Undoing restores the exact state the parent loop left behind because the old X is still on the board. 
Old moves would remain on the board and taint the search if they were not reversed. 
It ensures that every path is investigated from the appropriate board state. 
This is significant because the program uses a single shared board list rather than creating new copies each time.



   (c) why standard_form() produces uniqueness

7) The output from the program is two print statements:
       127872
       138 81792 46080 91 44 3

    explain what each number represents.
 The first number is the total number of full 9-move boards reached by the search.
    The second line means:
    - 138 = number of unique terminal boards up to symmetry
    - 81792 = full boards where X wins on move 9
    - 46080 = full boards that are draws
    - 91 = unique terminal boards where X is the winner
    - 44 = unique terminal boards where O is the winner
    - 3 = unique terminal boards that are ties

Submission:
- Update this file with your answers. Commit and sync

"""

# ----------------------------
# Global running totals (STATE)
# ----------------------------

unique_seen = []             # TODO: What does this list store? Why do we store "standard forms"? 
# Stores standard-form representations of terminal boards already counted, so rotated/flipped versions of the same ending board are only counted once.
board = [' '] * 9            # TODO: What does this represent? Why do we undo moves?
# Represents the current board state during the search. 
# We undo moves so one shared board list can be reused while exploring different game paths.

full_boards = 0              # TODO: What does this count? 
# Counts all terminal boards reached only because all 9 squares were filled.
x_wins_on_full_board = 0     # TODO: What does this count?
# Counts full 9-move boards where X wins on the last move.
draws_on_full_board = 0      # TODO: What does this count? 
# Counts full 9-move boards with no winner.

x_wins = 0                   # TODO: What does this count?
# Counts unique terminal board shapes (up to symmetry) where X has won.
o_wins = 0                   # TODO: What does this count? 
# Counts unique terminal board shapes (up to symmetry) where O has won.
ties = 0                     # TODO: What does this count? 
#Counts unique terminal board shapes (up to symmetry) that are ties


# ----------------------------
# Board representation helpers
# ----------------------------

def to_grid(flat_board: list[str]) -> list[list[str]]:
    '''Convert a 1-dimensional board list of length 9 into a 3x3 grid. This makes rotations,
    flips, and symmetry comparisons easier to write and understand.'''
    grid = []
    for row in range(3):
        row_vals = []
        for col in range(3):
            row_vals.append(flat_board[row * 3 + col])
        grid.append(row_vals)
    return grid


def rotate_clockwise(grid: list[list[str]]) -> list[list[str]]:
    '''Return a new 3x3 grid rotated 90 degrees clockwise. This is used to generate
    equivalent board layouts under symmetry.'''
    rotated = [[' '] * 3 for _ in range(3)]
    for r in range(3):
        for c in range(3):
            rotated[c][2 - r] = grid[r][c]
    return rotated


def flip_vertical(grid: list[list[str]]) -> list[list[str]]:
    '''Return a vertically flipped version of the 3x3 grid by swapping the top and bottom rows.
    This gives the reflection half of the board symmetries.'''
    return [grid[2], grid[1], grid[0]]

def standard_form(flat_board: list[str]) -> list[list[str]]:
    '''Compute one canonical representative for a board among all its symmetric versions.
    The function generates the 4 rotations of the board and the 4 rotations of its vertical flip,
    then returns the minimum one in Python's list ordering. This makes equivalent boards share
    the same representation.

    A non-obvious part is why this creates uniqueness. Many different-looking boards are really
    the same position if one can be rotated or reflected into the other. By generating every such
    version and always picking the same "smallest" one, the program gives every symmetry class one
    stable label. That means two boards that are equivalent under symmetry will always reduce to
    the exact same standard form. Boards that are not equivalent will not end up with the same set
    of variants, so they will not collapse to the same representative. This is why standard_form()
    lets unique_seen treat symmetric terminal boards as one unique outcome.'''
    grid = to_grid(flat_board)
    flipped = flip_vertical(grid)

    variants = []
    for _ in range(4):
        variants.append(grid)
        variants.append(flipped)
        grid = rotate_clockwise(grid)
        flipped = rotate_clockwise(flipped)

    return min(variants)

def record_unique_board(flat_board: list[str]) -> None:
    '''Record a terminal board only if its symmetry class has not already been seen.
    After converting the board to standard form, this function updates the correct
    unique-terminal counter for X wins, O wins, or ties.'''
    global x_wins, o_wins, ties

    rep = standard_form(flat_board)

    # TODO: Why do we check "rep not in unique_seen" before appending?
    # Guard against double-counting: if we've already seen this canonical board
    # (perhaps reached via a different move order or a symmetric position),
    # we skip it. Only new canonical boards update the counters.
    if rep not in unique_seen:
        unique_seen.append(rep)

        # TODO: This updates counts for unique *terminal* boards. What are the categories?
        winner = who_won(flat_board) 
        if winner == 'X':
            x_wins += 1 # This unique terminal board is an X win
        elif winner == 'O':
            o_wins += 1 # This unique terminal board is an O win
        else:
            ties += 1 # This unique terminal board is a draw


# ----------------------------
# Game logic
# ----------------------------

def has_winner(flat_board: list[str]) -> bool:
    ''' TODO '''
    winning_lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # cols
        [0, 4, 8], [6, 4, 2],             # diagonals
    ]

    for line in winning_lines:
        score = 0
        for idx in line:
            if flat_board[idx] == 'X':
                score += 10
            elif flat_board[idx] == 'O':
                score -= 10
        if abs(score) == 30:
            return True

    return False


def who_won(flat_board: list[str]) -> str:
    ''' TODO '''
    winning_lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # cols
        [0, 4, 8], [6, 4, 2],             # diagonals
    ]

    for line in winning_lines:
        score = 0
        for idx in line:
            if flat_board[idx] == 'X':
                score += 10
            elif flat_board[idx] == 'O':
                score -= 10

        if score == 30:
            return 'X'
        elif score == -30:
            return 'O'

    return 'TIE'


def should_continue(flat_board: list[str], move_number: int) -> bool:
    ''' TODO '''
    # TODO: What condition makes us STOP exploring deeper moves?
    # In should_continue:
    if has_winner(flat_board):
        record_unique_board(flat_board)
        return False
    # STOP condition: once a winner exists, there's no point exploring further moves.
    # We record the board and signal the calling loop to skip its inner loops.
    return True


def record_full_board(flat_board: list[str]) -> None:
    ''' TODO '''
    global full_boards, x_wins_on_full_board, draws_on_full_board

    # TODO: This is a terminal state because the board is full (9 moves). 
    # Every 9-move sequence is a terminal state; count it regardless of symmetry.
    record_unique_board(flat_board)
    full_boards += 1

    # TODO: On a full board, either X has won (last move) or it is a draw.
    # X made the last move, so if there's a winner it must be X.
    if has_winner(flat_board):
        x_wins_on_full_board += 1
    else:
        draws_on_full_board += 1
    # No winner on a full board → draw.



# ----------------------------
# Brute force search (9 nested loops)
# ----------------------------

# TODO: In these loops, where are transitions taking place?
# Transitions happen in these loops whenever a square changes from ' ' to 'X' or 'O'.
# More transitions happen when each move is undone, returning the board to its earlier state.
# TODO: Where else do transitions happen?
# Other transitions also happen inside record_unique_board() and record_full_board() when counters update.


# Move 1: X
for x1 in range(9):
    board[x1] = 'X'
    if should_continue(board, 1):

        # Move 2: O
        for o1 in range(9):
            if board[o1] == ' ':
                board[o1] = 'O'
                if should_continue(board, 2):

                    # Move 3: X
                    for x2 in range(9):
                        if board[x2] == ' ':
                            board[x2] = 'X'
                            if should_continue(board, 3):

                                # Move 4: O
                                for o2 in range(9):
                                    if board[o2] == ' ':
                                        board[o2] = 'O'
                                        if should_continue(board, 4):

                                            # Move 5: X
                                            for x3 in range(9):
                                                if board[x3] == ' ':
                                                    board[x3] = 'X'
                                                    if should_continue(board, 5):

                                                        # Move 6: O
                                                        for o3 in range(9):
                                                            if board[o3] == ' ':
                                                                board[o3] = 'O'
                                                                if should_continue(board, 6):

                                                                    # Move 7: X
                                                                    for x4 in range(9):
                                                                        if board[x4] == ' ':
                                                                            board[x4] = 'X'
                                                                            if should_continue(board, 7):

                                                                                # Move 8: O
                                                                                for o4 in range(9):
                                                                                    if board[o4] == ' ':
                                                                                        board[o4] = 'O'
                                                                                        if should_continue(board, 8):

                                                                                            # Move 9: X
                                                                                            for x5 in range(9):
                                                                                                if board[x5] == ' ':
                                                                                                    board[x5] = 'X'

                                                                                                    # Full board reached (terminal)
                                                                                                    record_full_board(board)

                                                                                                    # undo move 9
                                                                                                    board[x5] = ' '

                                                                                        # undo move 8
                                                                                        board[o4] = ' '

                                                                            # undo move 7
                                                                            board[x4] = ' '

                                                                # undo move 6
                                                                board[o3] = ' '

                                                    # undo move 5
                                                    board[x3] = ' '

                                        # undo move 4
                                        board[o2] = ' '

                            # undo move 3
                            board[x2] = ' '

                # undo move 2
                board[o1] = ' '

    # undo move 1
    board[x1] = ' '


print(full_boards)
print(len(unique_seen), x_wins_on_full_board, draws_on_full_board, x_wins, o_wins, ties)
