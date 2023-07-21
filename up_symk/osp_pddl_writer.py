import unified_planning as up
from unified_planning.io import PDDLWriter

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
            (
                qm
                for qm in problem.quality_metrics
                if isinstance(qm, up.model.metrics.Oversubscription)
            ),
            None,
        )

        self.plan_cost_qm = next(
            (
                qm
                for qm in problem.quality_metrics
                if isinstance(qm, up.model.metrics.MinimizeActionCosts)
            ),
            None,
        )

        self.plan_len_qm = next(
            (
                qm
                for qm in problem.quality_metrics
                if isinstance(qm, up.model.metrics.MinimizeSequentialPlanLength)
            ),
            None,
        )

        assert (
            self.osp_qm
        ), "OspPDDLWritter called on a problem that is Oversubscription task!"

        self.goals = list(self.osp_qm.goals.items())

        new_problem = problem.clone()
        new_problem.clear_quality_metrics()

        # for g in self.goals:
        #     if g[0] not in new_problem.goals:
        #         new_problem.add_goal(g[0])

        for qm in self.original_problem.quality_metrics:
            if not isinstance(qm, up.model.metrics.Oversubscription):
                new_problem.add_quality_metric(qm)

        assert len(new_problem.quality_metrics) <= 1

        print(new_problem.quality_metrics)

        super().__init__(
            new_problem,
            needs_requirements=needs_requirements,
            rewrite_bool_assignments=rewrite_bool_assignments,
        )

    def _write_domain(self, out: IO[str]):
        super()._write_domain(out)
        out.flush()
        with open(out.name, "r") as file:
            print(file.read())

    # We replace the goal section with utilities and the cost bound
    def _write_problem(self, out: IO[str]):
        super()._write_problem(out)
        out.flush()

        def get_util_pddl(goal):
            assert len(goal) == 2
            fact = goal[0]
            fact_pddl = f"{fact.fluent().name} {fact.get_nary_expression_string(' ', self.goals[0][0].args)[1:-1]}"
            return f"(= ({fact_pddl}) {goal[1]})"

        util_str = "(:utility"
        for goal in self.goals:
            util_str += " " + get_util_pddl(goal)
        util_str += ")\n"

        # TODO: set correct bound via an parameter
        bound_str = " (:bound 3)\n"

        replace_string_in_file(out.name, "(:goal (and ))", util_str + bound_str)


def replace_string_in_file(file_path: IO[str], old_string: str, new_string: str):
    with open(file_path, "r") as file:
        file_contents = file.read()

    print(file_contents)
    assert old_string in file_contents
    modified_contents = file_contents.replace(old_string, new_string)

    print(modified_contents)

    with open(file_path, "w") as file:
        file.write(modified_contents)
