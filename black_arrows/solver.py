from logic_puzzles.solver import SimpleBranchingSolver


class BlackArrowsSolver(SimpleBranchingSolver):
    def get_branching_score(self, location):
        return 1

    def _compute_dirty(self, location):
        return set()
