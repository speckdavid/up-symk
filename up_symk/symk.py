from .symk_base import *
from .osp_pddl_writer import *

import subprocess
import sys
import tempfile
import os

import asyncio
from asyncio.subprocess import PIPE

import unified_planning as up
from typing import Callable, IO, List, Optional, Tuple, Union
from unified_planning.model import ProblemKind
from unified_planning.engines import OptimalityGuarantee
from unified_planning.engines import PlanGenerationResultStatus as ResultStatus
from unified_planning.engines import PDDLAnytimePlanner
from unified_planning.engines import Credits
from unified_planning.engines.pddl_planner import *
from unified_planning.engines.results import (
    LogLevel,
    PlanGenerationResult,
    PlanGenerationResultStatus,
)

# By default, on non-Windows OSs we use the first method and on Windows we
# always use the second. It is possible to use asyncio under unix by setting
# the environment variable UP_USE_ASYNCIO_PDDL_PLANNER to true.
USE_ASYNCIO_ON_UNIX = False
ENV_USE_ASYNCIO = os.environ.get("UP_USE_ASYNCIO_PDDL_PLANNER")
if ENV_USE_ASYNCIO is not None:
    USE_ASYNCIO_ON_UNIX = ENV_USE_ASYNCIO.lower() in ["true", "1"]


class SymKOptimalPDDLPlanner(SymKMixin, PDDLAnytimePlanner):
    def __init__(
        self,
        symk_search_config: Optional[str] = None,
        symk_anytime_search_config: Optional[str] = None,
        symk_driver_options: Optional[str] = None,
        symk_translate_options: Optional[List[str]] = None,
        symk_preprocess_options: Optional[List[str]] = None,
        symk_search_time_limit: Optional[str] = None,
        number_of_plans: Optional[int] = None,
        plan_cost_bound: Optional[int] = None,
        log_level: str = "info",
    ):
        PDDLAnytimePlanner.__init__(self)

        input_number_of_plans = format_input_value(number_of_plans, min_value=1)
        input_plan_cost_bound = format_input_value(plan_cost_bound, min_value=0)

        if symk_search_config is None:
            symk_search_config = f"sym-bd(bound={input_plan_cost_bound})"

        if symk_anytime_search_config is None:
            symk_anytime_search_config = f"symq-bd(plan_selection=top_k(num_plans={input_number_of_plans},dump_plans=true),bound={input_plan_cost_bound},quality=1.0)"

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
        supported_kind.set_effects_kind("FORALL_EFFECTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        # supported_kind.set_fluents_type("DERIVED_FLUENTS")
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
        osp_metric = any(
            isinstance(qm, up.model.metrics.Oversubscription)
            for qm in problem.quality_metrics
        )

        # Call OSP engine
        if osp_metric:
            assert (
                len(problem.goals) == 0
            ), "The oversubscription engine of Symk does not support hard goals! To simulate hard goals, please assign a very high utility to the hard goals (and set the plan cost bound accordingly)."

            # Only translate and preprocess
            self._symk_driver_options = ["--translate", "--search"]

            # Replace search engine
            self._symk_search_config = replace_search_engine_in_config(
                self._symk_search_config, "sym-osp-fw"
            )
            if self.ensures(up.engines.AnytimeGuarantee.OPTIMAL_PLANS):
                assert "symq" in self._symk_anytime_search_config
                self._symk_anytime_search_config = replace_search_engine_in_config(
                    self._symk_anytime_search_config, "symq-osp-fw"
                )
            else:
                assert "symk" in self._symk_anytime_search_config
                self._symk_anytime_search_config = replace_search_engine_in_config(
                    self._symk_anytime_search_config, "symk-osp-fw"
                )

            return self._solve_osp_task(
                problem, timeout, output_stream, anytime=anytime
            )

        return super()._solve(
            problem, heuristic, timeout, output_stream, anytime=anytime
        )

    # SOLVE OSP TASK => We use the PDDL writter and then change the file
    # This is definetly not ideal but the best we can do
    def _solve_osp_task(
        self,
        problem: "up.model.AbstractProblem",
        timeout: Optional[float] = None,
        output_stream: Optional[Union[Tuple[IO[str], IO[str]], IO[str]]] = None,
        anytime: bool = False,
    ) -> "up.engines.results.PlanGenerationResult":
        assert isinstance(problem, up.model.Problem)
        self._writer = OspPDDLWriter(
            problem, self._needs_requirements, self._rewrite_bool_assignments
        )
        plan = None
        logs: List["up.engines.results.LogMessage"] = []

        with tempfile.TemporaryDirectory() as tempdir:
            domain_filename = os.path.join(tempdir, "domain.pddl")
            problem_filename = os.path.join(tempdir, "problem.pddl")
            plan_filename = os.path.join(tempdir, "plan.txt")
            self._writer.write_domain(domain_filename)
            self._writer.write_problem(problem_filename)

            if anytime:
                assert isinstance(
                    self, up.engines.pddl_anytime_planner.PDDLAnytimePlanner
                )
                cmd = self._get_anytime_cmd(
                    domain_filename, problem_filename, plan_filename
                )
            else:
                assert self._mode_running == OperationMode.ONESHOT_PLANNER
                cmd = self._get_cmd(domain_filename, problem_filename, plan_filename)

            if output_stream is None:
                # If we do not have an output stream to write to, we simply call
                # a subprocess and retrieve the final output and error with communicate
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                timeout_occurred: bool = False
                proc_out: List[str] = []
                proc_err: List[str] = []
                try:
                    out_err_bytes = process.communicate(timeout=timeout)
                    proc_out, proc_err = [[x.decode()] for x in out_err_bytes]
                except subprocess.TimeoutExpired:
                    timeout_occurred = True
                retval = process.returncode
            else:
                if sys.platform == "win32":
                    # On windows we have to use asyncio (does not work inside notebooks)
                    try:
                        loop = asyncio.ProactorEventLoop()
                        exec_res = loop.run_until_complete(
                            run_command_asyncio(
                                self, cmd, output_stream=output_stream, timeout=timeout
                            )
                        )
                    finally:
                        loop.close()
                else:
                    # On non-windows OSs, we can choose between asyncio and posix
                    # select (see comment on USE_ASYNCIO_ON_UNIX variable for details)
                    if USE_ASYNCIO_ON_UNIX:
                        exec_res = asyncio.run(
                            run_command_asyncio(
                                self, cmd, output_stream=output_stream, timeout=timeout
                            )
                        )
                    else:
                        exec_res = run_command_posix_select(
                            self, cmd, output_stream=output_stream, timeout=timeout
                        )
                timeout_occurred, (proc_out, proc_err), retval = exec_res

            logs.append(up.engines.results.LogMessage(LogLevel.INFO, "".join(proc_out)))
            logs.append(
                up.engines.results.LogMessage(LogLevel.ERROR, "".join(proc_err))
            )
            if os.path.isfile(plan_filename):
                plan = self._plan_from_file(
                    problem, plan_filename, self._writer.get_item_named
                )
            if timeout_occurred and retval != 0:
                return PlanGenerationResult(
                    PlanGenerationResultStatus.TIMEOUT,
                    plan=plan,
                    log_messages=logs,
                    engine_name=self.name,
                )
        status: PlanGenerationResultStatus = self._result_status(
            problem, plan, retval, logs
        )
        res = PlanGenerationResult(
            status, plan, log_messages=logs, engine_name=self.name
        )
        return res


class SymKPDDLPlanner(SymKOptimalPDDLPlanner):
    def __init__(
        self,
        symk_search_config: Optional[str] = None,
        symk_anytime_search_config: Optional[str] = None,
        symk_driver_options: Optional[str] = None,
        symk_translate_options: Optional[List[str]] = None,
        symk_preprocess_options: Optional[List[str]] = None,
        symk_search_time_limit: Optional[str] = None,
        number_of_plans: Optional[int] = None,
        plan_cost_bound: Optional[int] = None,
        log_level: str = "info",
    ):
        input_number_of_plans = format_input_value(number_of_plans, min_value=1)
        input_plan_cost_bound = format_input_value(plan_cost_bound, min_value=0)

        if symk_anytime_search_config is None:
            symk_anytime_search_config = f"symk-bd(plan_selection=top_k(num_plans={input_number_of_plans},dump_plans=true),bound={input_plan_cost_bound})"

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
        return True

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
        if anytime:
            self._guarantee_metrics_task = ResultStatus.SOLVED_SATISFICING
        else:
            self._guarantee_metrics_task = ResultStatus.SOLVED_OPTIMALLY

        return super()._solve(
            problem, heuristic, timeout, output_stream, anytime=anytime
        )
