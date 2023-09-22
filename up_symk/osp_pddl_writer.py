import unified_planning as up
from unified_planning.io import PDDLWriter
from unified_planning.exceptions import UPUnsupportedProblemTypeError

from typing import IO


class OspPDDLWriter(PDDLWriter):
    def __init__(
        self,
        problem: "up.model.Problem",
        needs_requirements: bool = True,
        rewrite_bool_assignments: bool = False,
    ):
        self.original_problem = problem
        assert len(problem.quality_metrics) <= 2

        self.osp_qm = next(
            (qm for qm in problem.quality_metrics if isinstance(qm, up.model.metrics.Oversubscription)),
            None,
        )

        self.plan_cost_qm = next(
            (qm for qm in problem.quality_metrics if isinstance(qm, up.model.metrics.MinimizeActionCosts)),
            None,
        )

        self.plan_len_qm = next(
            (qm for qm in problem.quality_metrics if isinstance(qm, up.model.metrics.MinimizeSequentialPlanLength)),
            None,
        )

        assert self.osp_qm, "OspPDDLWriter called on a problem that is not an oversubscription task!"

        self.goals = list(self.osp_qm.goals.items())

        new_problem = problem.clone()
        new_problem.clear_quality_metrics()

        for qm in self.original_problem.quality_metrics:
            if not isinstance(qm, up.model.metrics.Oversubscription):
                new_problem.add_quality_metric(qm)

        assert len(new_problem.quality_metrics) <= 1

        super().__init__(
            new_problem,
            needs_requirements=needs_requirements,
            rewrite_bool_assignments=rewrite_bool_assignments,
        )

    def _write_domain(self, out: IO[str]):
        super()._write_domain(out)
        out.flush()

    # We replace the goal section with utilities and the dummy plan cost bound
    def _write_problem(self, out: IO[str]):
        super()._write_problem(out)
        out.flush()

        def get_util_pddl(goal):
            assert len(goal) == 2
            fact = goal[0]
            try:
                fact_pddl = f"{fact.fluent().name} {fact.get_nary_expression_string(' ', fact.args)[1:-1]}"
            except:
                raise UPUnsupportedProblemTypeError(
                    "Symk currently only supports fluents in the oversubscribed goal description. Please use another oversubscription engine or define the oversubscribed goal definition via derived predicates that can capture complex conditions."
                )
            return f"(= ({fact_pddl}) {goal[1]})"

        util_str = "(:utility"
        for goal in self.goals:
            util_str += " " + get_util_pddl(goal)
        util_str += ")\n"

        # Max int - 1 as max plan cost
        # Bound is set via the search engine
        bound_str = " (:bound 2147483646)\n"

        replace_line_with_string(out.name, ":goal", util_str + bound_str)


def replace_line_with_string(file_path: str, target_string: str, new_string: str):
    with open(file_path, "r") as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        if target_string in line:
            lines[i] = new_string

    with open(file_path, "w") as file:
        file.writelines(lines)
