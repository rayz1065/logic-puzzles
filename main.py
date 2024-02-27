import sys
import argparse
import json
import kakuro.puzzle, kakuro.solver
import communicating_vessels.puzzle, communicating_vessels.solver
import einstein.puzzle, einstein.solver
import magical_maze.puzzle, magical_maze.solver


PUZZLES = {
    "kakuro": (kakuro.puzzle.KakuroPuzzle, kakuro.solver.KakuroSolver),
    "communicating_vessels": (
        communicating_vessels.puzzle.CommunicatingVesselsPuzzle,
        communicating_vessels.solver.CommunicatingVesselsSolver,
    ),
    "einstein": (einstein.puzzle.EinsteinPuzzle, einstein.solver.EinsteinSolver),
    "magical_maze": (
        magical_maze.puzzle.MagicalMazePuzzle,
        magical_maze.solver.MagicalMazeSolver,
    ),
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("puzzle", choices=PUZZLES.keys(), help="Puzzle type")
    parser.add_argument("--input", type=argparse.FileType("r"), default=sys.stdin)
    parser.add_argument("--output", type=argparse.FileType("w"), default=sys.stdout)
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    puzzle_type = args.puzzle
    puzzle_cls, solver_cls = PUZZLES[puzzle_type]
    puzzle = puzzle_cls.from_file(args.input)
    solver = solver_cls(puzzle)

    solutions = solver.solve()

    if not args.json:
        print(f"Found {len(solutions)} solutions", file=args.output)
        for state in solutions:
            print("-----------------", file=args.output)
            puzzle.set_state(state)
            print(puzzle, file=args.output)
    else:
        json.dump([x.__dict__ for x in solutions], args.output)


if __name__ == "__main__":
    main()
