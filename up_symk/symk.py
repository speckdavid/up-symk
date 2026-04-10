from .symk_base import *

import unified_planning as up
from typing import Callable, IO, List, Optional, Tuple, Union
from unified_planning.model import ProblemKind
from unified_planning.engines import OptimalityGuarantee
from unified_planning.engines import PlanGenerationResultStatus as ResultStatus
from unified_planning.engines import PDDLAnytimePlanner
from unified_planning.engines import Credits
from unified_planning.engines.pddl_planner import *
from unified_planning.model.problem_kind import FEATURES


class SymKOptimalPDDLPlanner(SymKMixin, PDDLAnytimePlanner):
    def __init__(
        self,
        symk_search_config: Optional[str] = None,
        symk_anytime_search_config: Optional[str] = None,
        symk_driver_options: Optional[str] = None,
        symk_translate_options: Optional[List[str]] = None,
        symk_preprocess_options: Optional[List[str]] = None,
        symk_search_time_limit: Optional[str] = None,
        number_of_plans: Optional[int] = 1,
        loopless: Optional[bool] = False,
        plan_cost_bound: Optional[int] = None,
        log_level: str = "info",
    ):
        PDDLAnytimePlanner.__init__(self)

        input_number_of_plans = format_input_value(number_of_plans, min_value=1)
        input_plan_cost_bound = format_input_value(plan_cost_bound, min_value=0)

        if symk_search_config is None:
            symk_search_config = f"sym_bd(bound={input_plan_cost_bound})"

        if symk_anytime_search_config is None:
            symk_anytime_search_config = f"symq_bd(simple={loopless},plan_selection=top_k(num_plans={input_number_of_plans},dump_plans=true),bound={input_plan_cost_bound},quality=1.0)"

        SymKMixin.__init__(
            self,
            symk_search_config=symk_search_config,
            symk_anytime_search_config=symk_anytime_search_config,
            symk_driver_options=symk_driver_options,
            symk_translate_options=symk_translate_options,
            symk_preprocess_options=symk_preprocess_options,
            symk_search_time_limit=symk_search_time_limit,
            log_level=log_level,
        )

    @property
    def name(self) -> str:
        return "SymK (with optimality guarantee)"

    @staticmethod
    def get_credits(**kwargs) -> Optional["Credits"]:
        c = Credits(**credits)
        details = [
            c.long_description,
            "The optimal engine uses symbolic search by David Speck.",
        ]
        c.long_description = " ".join(details)
        return c

    def _starting_plan_str(self) -> str:
        return "New plan"

    def _ending_plan_str(self) -> str:
        return "step(s)"

    def _parse_plan_line(self, plan_line: str) -> str:
        if plan_line.startswith("[t="):
            return ""
        return "(%s)" % plan_line.split("(")[0].strip()

    @staticmethod
    def satisfies(optimality_guarantee: "OptimalityGuarantee") -> bool:
        return True

    @staticmethod
    def supported_kind() -> "ProblemKind":
        supported_kind = ProblemKind(version=2)
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
        supported_kind.set_effects_kind("FORALL_EFFECTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")

        # Attempt to set the supported kinds (depends on UP version)
        if (
            "ACTIONS_COST_KIND" in FEATURES
            and "INT_NUMBERS_IN_ACTIONS_COST" in FEATURES["ACTIONS_COST_KIND"]
        ):
            supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")

        if "FLUENTS_TYPE" in FEATURES and "DERIVED_FLUENTS" in FEATURES["FLUENTS_TYPE"]:
            supported_kind.set_fluents_type("DERIVED_FLUENTS")
        return supported_kind

    @staticmethod
    def supports(problem_kind: "ProblemKind") -> bool:
        return problem_kind <= SymKOptimalPDDLPlanner.supported_kind()

    @staticmethod
    def ensures(anytime_guarantee: up.engines.AnytimeGuarantee) -> bool:
        if anytime_guarantee == up.engines.AnytimeGuarantee.OPTIMAL_PLANS:
            return True
        return False

    def _solve(
        self,
        problem: "up.model.AbstractProblem",
        heuristic: Optional[
            Callable[["up.model.state.ROState"], Optional[float]]
        ] = None,
        timeout: Optional[float] = None,
        output_stream: Optional[Union[Tuple[IO[str], IO[str]], IO[str]]] = None,
        anytime: bool = False,
    ):
        return super()._solve(
            problem, heuristic, timeout, output_stream, anytime=anytime
        )


class SymKPDDLPlanner(SymKOptimalPDDLPlanner):
    def __init__(
        self,
        symk_search_config: Optional[str] = None,
        symk_anytime_search_config: Optional[str] = None,
        symk_driver_options: Optional[str] = None,
        symk_translate_options: Optional[List[str]] = None,
        symk_preprocess_options: Optional[List[str]] = None,
        symk_search_time_limit: Optional[str] = None,
        number_of_plans: Optional[int] = 1,
        loopless: Optional[bool] = False,
        plan_cost_bound: Optional[int] = None,
        log_level: str = "info",
    ):
        input_number_of_plans = format_input_value(number_of_plans, min_value=1)
        input_plan_cost_bound = format_input_value(plan_cost_bound, min_value=0)

        if symk_anytime_search_config is None:
            symk_anytime_search_config = f"symk_bd(simple={loopless},plan_selection=top_k(num_plans={input_number_of_plans},dump_plans=true),bound={input_plan_cost_bound})"

        super().__init__(
            symk_search_config=symk_search_config,
            symk_anytime_search_config=symk_anytime_search_config,
            symk_driver_options=symk_driver_options,
            symk_translate_options=symk_translate_options,
            symk_preprocess_options=symk_preprocess_options,
            symk_search_time_limit=symk_search_time_limit,
            number_of_plans=number_of_plans,
            plan_cost_bound=plan_cost_bound,
            log_level=log_level,
        )

    @property
    def name(self) -> str:
        return "SymK"

    # Oneshot planner is optimal
    @staticmethod
    def satisfies(optimality_guarantee: "OptimalityGuarantee") -> bool:
        return False

    # Plans are reported with increasing costs thus potentially also non-optimal ones
    @staticmethod
    def ensures(anytime_guarantee: up.engines.AnytimeGuarantee) -> bool:
        return False

    def _solve(
        self,
        problem: "up.model.AbstractProblem",
        heuristic: Optional[
            Callable[["up.model.state.ROState"], Optional[float]]
        ] = None,
        timeout: Optional[float] = None,
        output_stream: Optional[Union[Tuple[IO[str], IO[str]], IO[str]]] = None,
        anytime: bool = False,
    ):
        self._guarantee_metrics_task = ResultStatus.SOLVED_OPTIMALLY

        return super()._solve(
            problem, heuristic, timeout, output_stream, anytime=anytime
        )
