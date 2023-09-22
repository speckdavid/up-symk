import pkg_resources
import sys

import unified_planning as up

from fractions import Fraction
from typing import List, Optional, Union
from unified_planning.engines import PlanGenerationResultStatus as ResultStatus
from unified_planning.engines import PDDLPlanner
from unified_planning.engines.results import LogMessage
from unified_planning.utils import powerset


credits = {
    "name": "SymK",
    "author": "David Speck (cf. https://github.com/speckdavid/symk/blob/master/README.md )",
    "contact": "david.speck@liu.se (for UP integration)",
    "website": "https://github.com/speckdavid/symk",
    "license": "GPLv3",
    "short_description": "SymK is a state-of-the-art domain-independent optimal and top-k planner.",
    "long_description": "SymK is a state-of-the-art domain-independent optimal and top-k planner.",
}


class SymKMixin(PDDLPlanner):
    def __init__(
        self,
        symk_search_config: Optional[str] = None,
        symk_anytime_search_config: Optional[str] = None,
        symk_driver_options: Optional[str] = None,
        symk_translate_options: Optional[List[str]] = None,
        symk_preprocess_options: Optional[List[str]] = None,
        symk_search_time_limit: Optional[str] = None,
        log_level: str = "info",
    ):
        super().__init__(rewrite_bool_assignments=True)
        self._symk_search_config = symk_search_config
        self._symk_anytime_search_config = symk_anytime_search_config
        self._symk_driver_options = symk_driver_options
        self._symk_translate_options = symk_translate_options
        self._symk_preprocess_options = symk_preprocess_options
        self._symk_search_time_limit = symk_search_time_limit
        self._log_level = log_level
        self._guarantee_no_plan_found = ResultStatus.UNSOLVABLE_PROVEN
        self._guarantee_metrics_task = ResultStatus.SOLVED_OPTIMALLY

    def _base_cmd(self, plan_filename: str) -> List[str]:
        downward = pkg_resources.resource_filename(__name__, "symk/fast-downward.py")
        assert sys.executable, "Path to interpreter could not be found"
        cmd = [sys.executable, downward, "--plan-file", plan_filename]
        if self._symk_driver_options is not None:
            cmd += self._symk_driver_options
        if self._symk_search_time_limit is not None:
            cmd += ["--search-time-limit", self._symk_search_time_limit]
        cmd += ["--log-level", self._log_level]
        return cmd

    def _get_cmd(
        self, domain_filename: str, problem_filename: str, plan_filename: str
    ) -> List[str]:
        cmd = self._base_cmd(plan_filename)
        cmd += [domain_filename, problem_filename]
        if self._symk_translate_options:
            cmd += ["--translate-options"] + self._symk_translate_options
        if self._symk_preprocess_options:
            cmd += ["--preprocess-options"] + self._symk_preprocess_options
        if self._symk_search_config:
            cmd += ["--search-options", "--search"] + self._symk_search_config.split()
        return cmd

    def _get_anytime_cmd(
        self, domain_filename: str, problem_filename: str, plan_filename: str
    ) -> List[str]:
        cmd = self._base_cmd(plan_filename)
        cmd += [domain_filename, problem_filename]
        if self._symk_translate_options:
            cmd += ["--translate-options"] + self._symk_translate_options
        if self._symk_preprocess_options:
            cmd += ["--preprocess-options"] + self._symk_preprocess_options
        if self._symk_anytime_search_config:
            cmd += [
                "--search-options",
                "--search",
            ] + self._symk_anytime_search_config.split()
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


def replace_search_engine_in_config(search_config: str, new_engine: str) -> str:
    # Find the index of the first "(" in the search engine configuration
    search_config_last_id = search_config.find("(")

    # Make sure that "(" is found in the search engine configuration
    assert (
        search_config_last_id != -1
    ), "Opening parenthesis not found in search engine configuration."

    # Replace the search engine substring with the new engine
    updated_config = f"{new_engine}{search_config[search_config_last_id:]}"

    return updated_config


def format_input_value(value, min_value=0):
    if value is None:
        return "infinity"
    assert value >= min_value if value is not None else True
    return value
