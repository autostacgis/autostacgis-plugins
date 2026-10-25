"""Backward chaining with explicit goal and search-parameter contracts."""

import json
from pathlib import Path

from autostacgis.goals import compile_goal, select_outputs

from ._backward_chain_planner import Planner


class BackwardChainSolver:
    contract = json.loads(Path(__file__).with_name("backward_chain_contract.json").read_text())

    def __init__(self, app, request, settings):
        self.app = app
        self.request = request
        self.planner = Planner(app, request, settings)

    def plan(self, records):
        plan = self.planner.plan(records)
        plan.module_contracts = self.planner.modules
        plan.parameter_templates = self.planner.parameter_templates
        return plan

    def validate_outputs(self, plan, records):
        goals = compile_goal(self.request["goal"], list(plan.initial.values()), self.app)
        return select_outputs(records, goals) is not None


ID = "backward_chain"
CAPABILITY = "solver"
IMPLEMENTATION = BackwardChainSolver
REQUIRES = ()
DEFAULTS = BackwardChainSolver.contract["settings"]

VERSION = "0.0.1"
DEPENDENCIES = []
