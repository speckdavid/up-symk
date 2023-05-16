import pkg_resources
import sys
import unified_planning as up
from typing import List, Optional
from unified_planning.model import ProblemKind
from unified_planning.engines import OptimalityGuarantee
from unified_planning.engines import PlanGenerationResultStatus as ResultStatus
from unified_planning.engines import PDDLPlanner, OperationMode, Credits
from unified_planning.engines.results import LogMessage


credits = {
    "name": "SymK",
    "author": "David Speck (cf. https://github.com/speckdavid/symk/blob/master/README.md)",
    "contact": "david.speck@liu.se (for UP integration)",
    "website": "https://github.com/speckdavid/symk",
    "license": "GPLv3",
    "short_description": "SymK is a state-of-the-art domain-independent classical optimal and top-k planner.",
    "long_description": "SymK is a state-of-the-art domain-independent classical optimal and top-k planner.",
}


class SymKPDDLPlannerBase(PDDLPlanner):
    def __init__(
        self,
        fast_downward_alias: Optional[str] = None,
        fast_downward_search_config: Optional[str] = None,
        fast_downward_anytime_alias: Optional[str] = None,
        fast_downward_anytime_search_config: Optional[str] = None,
        fast_downward_translate_options: Optional[List[str]] = None,
        fast_downward_search_time_limit: Optional[str] = None,
        log_level: str = "info",
    ):
        super().__init__(rewrite_bool_assignments=True)
        self._fd_alias = fast_downward_alias
        self._fd_search_config = fast_downward_search_config
        self._fd_anytime_alias = fast_downward_anytime_alias
        self._fd_anytime_search_config = fast_downward_anytime_search_config
        self._fd_translate_options = fast_downward_translate_options
        self._fd_search_time_limit = fast_downward_search_time_limit
        self._log_level = log_level
        assert not (self._fd_alias and self._fd_search_config)
        assert not (self._fd_anytime_alias and self._fd_anytime_search_config)
        self._guarantee_no_plan_found = ResultStatus.UNSOLVABLE_INCOMPLETELY
        self._guarantee_metrics_task = ResultStatus.SOLVED_SATISFICING
        self._mode_running = OperationMode.ONESHOT_PLANNER

    def _get_cmd(
        self, domain_filename: str, problem_filename: str, plan_filename: str
    ) -> List[str]:
        downward = pkg_resources.resource_filename(
            __name__, "symk/fast-downward.py"
        )
        assert sys.executable, "Path to interpreter could not be found"
        cmd = [sys.executable, downward, "--plan-file", plan_filename]
        if self._fd_search_time_limit is not None:
            cmd += ["--search-time-limit", self._fd_search_time_limit]
        cmd += ["--log-level", self._log_level]
        if self._mode_running is OperationMode.ONESHOT_PLANNER:
            if self._fd_alias:
                cmd += ["--alias", self._fd_alias]
            cmd += [domain_filename, problem_filename]
            if self._fd_translate_options:
                cmd += ["--translate-options"] + self._fd_translate_options
            if self._fd_search_config:
                cmd += ["--search-options", "--search"] + \
                    self._fd_search_config.split()
        elif self._mode_running is OperationMode.ANYTIME_PLANNER:
            if self._fd_anytime_alias:
                cmd += ["--alias", self._fd_anytime_alias]
            cmd += [domain_filename, problem_filename]
            if self._fd_translate_options:
                cmd += ["--translate-options"] + self._fd_translate_options
            if self._fd_anytime_search_config:
                cmd += [
                    "--search-options",
                    "--search",
                ] + self._fd_anytime_search_config.split()
        return cmd

    def _result_status(
        self,
        problem: "up.model.Problem",
        plan: Optional["up.plans.Plan"],
        retval: int = None,  # Default value for legacy support
        log_messages: Optional[List[LogMessage]] = None,
    ) -> "up.engines.results.PlanGenerationResultStatus":
        def solved(metrics):
            if metrics:
                return self._guarantee_metrics_task
            else:
                return ResultStatus.SOLVED_SATISFICING

        # https://www.fast-downward.org/ExitCodes
        metrics = problem.quality_metrics
        if retval is None:  # legacy support
            if plan is None:
                return self._guarantee_no_plan_found
            else:
                return solved(metrics)
        if retval in (0, 1, 2, 3):
            if plan is None:
                return self._guarantee_no_plan_found
            else:
                return solved(metrics)
        if retval in (10, 11):
            return ResultStatus.UNSOLVABLE_PROVEN
        if retval == 12:
            return ResultStatus.UNSOLVABLE_INCOMPLETELY
        else:
            return ResultStatus.INTERNAL_ERROR


class SymKOptimalPDDLPlanner(SymKPDDLPlannerBase):
    def __init__(self, log_level: str = "info"):
        super().__init__(
            fast_downward_search_config="sym-bd()", log_level=log_level
        )
        self._guarantee_no_plan_found = ResultStatus.UNSOLVABLE_PROVEN
        self._guarantee_metrics_task = ResultStatus.SOLVED_OPTIMALLY

    @property
    def name(self) -> str:
        return "SymK (with optimality guarantee)"

    @staticmethod
    def get_credits(**kwargs) -> Optional["Credits"]:
        c = Credits(**credits)
        details = [
            c.long_description,
            "The optimal engine uses symbolic bidirectional search by",
            "David Speck.",
        ]
        c.long_description = " ".join(details)
        return c

    @staticmethod
    def supported_kind() -> "ProblemKind":
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        return supported_kind

    @staticmethod
    def supports(problem_kind: "ProblemKind") -> bool:
        return problem_kind <= SymKOptimalPDDLPlanner.supported_kind()

    @staticmethod
    def satisfies(optimality_guarantee: OptimalityGuarantee) -> bool:
        return True
