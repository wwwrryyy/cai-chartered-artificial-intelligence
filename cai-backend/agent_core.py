"""Tool-based agent loop for CAI."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from gemma_client import call_gemma_with_tools, synthesize_tool_response
from tools import TAX_TOOLS, execute_tool


class CAIAgent:
    """Agent loop: plan → execute → verify/respond."""

    def __init__(self) -> None:
        self.tools = TAX_TOOLS
        self.trace: List[Dict[str, Any]] = []

    def run(self, user_input: str, financial_profile: Dict[str, Any]) -> Dict[str, Any]:
        self.trace = []
        plan = self._plan(user_input=user_input, financial_profile=financial_profile)
        tool_calls = plan.get("tool_calls", [])
        tool_results = self._execute(tool_calls)
        response = self._respond(user_input=user_input, tool_results=tool_results)

        return {
            "plan": plan,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "response": response,
            "trace": self.get_trace(),
        }

    def _plan(self, user_input: str, financial_profile: Dict[str, Any]) -> Dict[str, Any]:
        planning_payload = {
            "user_input": user_input,
            "financial_profile": financial_profile,
            "task": "Decide tool calls required for tax analysis and verification",
        }
        prompt = json.dumps(planning_payload, ensure_ascii=False, indent=2)

        plan = call_gemma_with_tools(prompt=prompt, tools=self.tools)

        self.trace.append(
            {
                "step": "plan",
                "details": {
                    "planning_note": plan.get("planning_note", ""),
                    "tool_calls": plan.get("tool_calls", []),
                    "planner_ok": plan.get("ok", False),
                },
            }
        )

        if not plan.get("tool_calls"):
            # Deterministic fallback so demo always has traceable tool usage.
            income = float(financial_profile.get("annual_income", 0) or 0)
            deductions = financial_profile.get("deduction_map", {}) or {}
            fallback_calls = [
                {"name": "lookup_tax_slab", "arguments": {"income": income, "regime": "old"}},
                {"name": "lookup_tax_slab", "arguments": {"income": income, "regime": "new"}},
                {
                    "name": "compute_tax",
                    "arguments": {"income": income, "deductions": deductions, "regime": "old"},
                },
            ]
            plan["tool_calls"] = fallback_calls
            self.trace.append(
                {
                    "step": "plan_fallback",
                    "details": {
                        "message": "No tool calls returned by planner; fallback tool calls generated.",
                        "tool_calls": fallback_calls,
                    },
                }
            )

        return plan

    def _execute(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for index, call in enumerate(tool_calls, start=1):
            tool_name = str(call.get("name", "")).strip()
            arguments = call.get("arguments", {}) or {}
            result = execute_tool(tool_name, arguments)
            wrapped = {
                "index": index,
                "tool": tool_name,
                "arguments": arguments,
                "result": result,
            }
            results.append(wrapped)
            self.trace.append({"step": f"execute_{index}", "details": wrapped})

        if not tool_calls:
            self.trace.append(
                {
                    "step": "execute",
                    "details": {"message": "No tool calls were executed."},
                }
            )

        return results

    def _respond(self, user_input: str, tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        synthesis = synthesize_tool_response(user_input=user_input, tool_results=tool_results)
        self.trace.append({"step": "respond", "details": synthesis})
        return synthesis

    def get_trace(self) -> List[Dict[str, Any]]:
        return list(self.trace)