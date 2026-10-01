import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from evaluation.models import (
    EvaluationScenario,
    EvaluationResult,
    EvaluationSummary,
    EvaluationMetric,
    scenario_store,
)
from app.workflows.engine import workflow_engine
from app.workflows.models import ResolutionRequest
from app.tools import tool_registry


@dataclass
class MetricEvaluator:
    """Evaluates a single scenario against expected results."""
    
    scenario: 'EvaluationScenario'
    workflow: any  # ResolutionWorkflow
    
    def evaluate(self) -> 'EvaluationResult':
        """Run all metric evaluations."""
        errors = []
        metrics = {}
        
        # 1. Task Success
        task_success = self._eval_task_success()
        metrics[EvaluationMetric.TASK_SUCCESS] = task_success
        if not task_success:
            errors.append(f"Task failed: expected {self.scenario.expected.final_state}, got {self.workflow.status.value}")
        
        # 2. Tool Selection Accuracy
        tool_acc = self._eval_tool_selection()
        metrics[EvaluationMetric.TOOL_SELECTION_ACCURACY] = tool_acc
        if tool_acc < 1.0:
            errors.append(f"Tool selection accuracy: {tool_acc:.2f}")
        
        # 3. Argument Accuracy
        arg_acc = self._eval_argument_accuracy()
        metrics[EvaluationMetric.ARGUMENT_ACCURACY] = arg_acc
        if arg_acc < 1.0:
            errors.append(f"Argument accuracy: {arg_acc:.2f}")
        
        # 4. Policy Compliance
        policy_compliance = self._eval_policy_compliance()
        metrics[EvaluationMetric.POLICY_COMPLIANCE] = policy_compliance
        if not policy_compliance:
            errors.append("Policy compliance failed")
        
        # 5. Grounding
        grounding = self._eval_grounding()
        metrics[EvaluationMetric.GROUNDING] = grounding
        if not grounding:
            errors.append("Grounding failed")
        
        # 6. Citation Correctness
        citation = self._eval_citation()
        metrics[EvaluationMetric.CITATION_CORRECTNESS] = citation
        if not citation:
            errors.append("Citation correctness failed")
        
        # 7. Human Escalation Accuracy
        esc_acc = self._eval_escalation_accuracy()
        metrics[EvaluationMetric.HUMAN_ESCALATION_ACCURACY] = esc_acc
        if not esc_acc:
            errors.append("Human escalation accuracy failed")
        
        # 8. Side-effect Safety
        safety = self._eval_side_effect_safety()
        metrics[EvaluationMetric.SIDE_EFFECT_SAFETY] = safety
        if not safety:
            errors.append("Side-effect safety failed")
        
        return EvaluationResult(
            scenario_id=self.scenario.id,
            scenario_name=self.scenario.name,
            passed=len(errors) == 0,
            metrics=metrics,
            latency_ms=0,  # Will be set by runner
            errors=errors,
            trace=self._extract_trace(),
        )
    
    def _eval_task_success(self) -> bool:
        """Check if final state matches expected."""
        expected = self.scenario.expected.final_state
        actual = self.workflow.status.value
        return actual == expected
    
    def _eval_tool_selection(self) -> float:
        """Check if correct tools were called in order."""
        expected_tools = [t.tool_name for t in self.scenario.expected.tools]
        actual_tools = [call.tool_name for call in self.workflow.tool_calls]
        
        if not expected_tools:
            return 1.0  # No tools expected
        
        matches = 0
        for exp_tool in expected_tools:
            if exp_tool in actual_tools:
                matches += 1
        
        return matches / len(expected_tools)
    
    def _eval_argument_accuracy(self) -> float:
        """Check if tool arguments match expected."""
        expected_tools = {t.tool_name: t.arguments for t in self.scenario.expected.tools}
        actual_tools = {call.tool_name: call.input_data for call in self.workflow.tool_calls}
        
        if not expected_tools:
            return 1.0
        
        total_args = 0
        correct_args = 0
        
        for tool_name, exp_args in expected_tools.items():
            if tool_name not in actual_tools:
                continue
            
            actual_args = actual_tools[tool_name]
            for key, exp_val in exp_args.items():
                total_args += 1
                if key in actual_args and actual_args[key] == exp_val:
                    correct_args += 1
        
        return correct_args / total_args if total_args > 0 else 1.0
    
    def _eval_policy_compliance(self) -> bool:
        """Check if policy decision matches expected."""
        expected = self.scenario.expected.policy_result
        if not expected:
            return True  # No policy expectation
        
        actual = self.workflow.policy_result.decision if self.workflow.policy_result else None
        return actual == expected
    
    def _eval_grounding(self) -> bool:
        """Check if decision is grounded in expected policies."""
        if not self.scenario.expected.grounding:
            return True
        
        # Check if retrieved documents contain expected policy sections
        retrieved_text = " ".join([
            str(doc.get("data", "")) for doc in self.workflow.retrieved_documents
        ])
        
        for expected_ground in self.scenario.expected.grounding:
            if expected_ground.lower() not in retrieved_text.lower():
                return False
        
        return True
    
    def _eval_citation(self) -> bool:
        """Check if citations in response match retrieved documents."""
        # Simplified: check if policy_result references exist in retrieved docs
        if not self.workflow.policy_result or not self.workflow.policy_result.policy_references:
            return True
        
        # Check if each cited document exists in retrieved documents
        retrieved_sections = set()
        for doc in self.workflow.retrieved_documents:
            if doc.get("type") == "policy" and doc.get("data", {}).get("section"):
                retrieved_sections.add(doc["data"]["section"])
        
        for ref in self.workflow.policy_result.policy_references:
            if ref.section not in retrieved_sections:
                return False
        
        return True
    
    def _eval_escalation_accuracy(self) -> bool:
        """Check if approval was requested when needed."""
        expected_approval = self.scenario.expected.policy_result == "REQUIRES_APPROVAL"
        
        if self.workflow.policy_result is None:
            return True
        
        actual_approval = self.workflow.policy_result.decision == "REQUIRES_APPROVAL"
        
        # If approval required but workflow didn't reach approval stage
        if self.scenario.expected.policy_result == "REQUIRES_APPROVAL":
            return self.workflow.status.value == "PENDING_APPROVAL"
        
        return actual_approval == expected_approval
    
    def _eval_side_effect_safety(self) -> bool:
        """Check that no side-effect tools were called without approval."""
        # Check if any side-effect tools were called when they shouldn't have been
        if self.scenario.expected.policy_result in ["DENY", "REQUIRES_APPROVAL"]:
            # Should not have executed side-effect tools
            for call in self.workflow.tool_calls:
                if call.tool_name in ["issue_refund", "cancel_order", "create_escalation"]:
                    # Check if it was actually executed (not just checked)
                    if call.success and call.tool_name in ["issue_refund", "cancel_order"]:
                        return False
        
        # Check that no unauthorized side effects occurred
        if self.scenario.expected.policy_result == "DENY":
            for call in self.workflow.tool_calls:
                if call.tool_name in ["issue_refund", "cancel_order"] and call.success:
                    return False
        
        return True
    
    def _extract_trace(self) -> Dict[str, Any]:
        """Extract workflow trace for debugging."""
        return {
            "workflow_id": self.workflow.id,
            "request_id": self.workflow.request_id,
            "status": self.workflow.status.value,
            "intent": self.workflow.intent.value if self.workflow.intent else None,
            "order_id": self.workflow.order_id,
            "order_number": self.workflow.order_number,
            "tool_calls": [
                {
                    "tool": call.tool_name,
                    "input": call.input_data,
                    "success": call.success,
                    "output": call.output_data,
                    "error": call.error,
                }
                for call in self.workflow.tool_calls
            ],
            "policy_result": {
                "decision": self.workflow.policy_result.decision if self.workflow.policy_result else None,
                "reason": self.workflow.policy_result.reason if self.workflow.policy_result else None,
                "policy_rule": self.workflow.policy_result.policy_rule if self.workflow.policy_result else None,
            } if self.workflow.policy_result else None,
            "approval": {
                "status": self.workflow.approval.status if self.workflow.approval else None,
                "approval_id": self.workflow.context.get("approval_id") if self.workflow.context else None,
            } if self.workflow.approval else None,
            "verification": {
                "success": self.workflow.verification.success if self.workflow.verification else None,
                "details": self.workflow.verification.details if self.workflow.verification else None,
            } if self.workflow.verification else None,
            "errors": self.workflow.errors,
        }


async def run_evaluation(scenario: 'EvaluationScenario') -> 'EvaluationResult':
    """Run a single evaluation scenario."""
    start_time = time.time()
    
    # Create resolution request
    request = ResolutionRequest(
        request_id=scenario.input.request_id,
        user_request=scenario.input.user_request,
        customer_id=scenario.input.customer_id,
        order_id=scenario.input.order_id,
    )
    
    # Run workflow
    workflow = await workflow_engine.execute(scenario.input)
    
    # Evaluate
    evaluator = MetricEvaluator(scenario=scenario, workflow=workflow)
    result = evaluator.evaluate()
    result.latency_ms = int((time.time() - start_time) * 1000)
    
    return result


async def run_all_evaluations() -> 'EvaluationSummary':
    """Run all evaluation scenarios."""
    results = []
    
    for scenario in scenario_store.get_all():
        print(f"Running scenario: {scenario.name} ({scenario.id})")
        try:
            result = await run_evaluation(scenario)
            results.append(result)
            status = "PASS" if result.passed else "FAIL"
            print(f"  {status} - {result.latency_ms}ms")
            if result.errors:
                for err in result.errors:
                    print(f"  ERROR: {err}")
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append(EvaluationResult(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                passed=False,
                metrics={},
                latency_ms=0,
                errors=[f"Execution failed: {str(e)}"],
            ))
    
    # Calculate summary metrics
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    
    # Aggregate metrics
    metric_sums: Dict[str, List[float]] = {}
    for r in results:
        for metric, value in r.metrics.items():
            if metric not in metric_sums:
                metric_sums[metric] = []
            metric_sums[metric].append(value)
    
    aggregated = {}
    for metric, values in metric_sums.items():
        aggregated[metric.value] = sum(values) / len(values) if values else 0.0
    
    total_latency = sum(r.latency_ms for r in results)
    
    return EvaluationSummary(
        total_scenarios=total,
        passed=passed,
        failed=failed,
        metrics=aggregated,
        total_latency_ms=total_latency,
        timestamp=datetime.utcnow(),
        results=results,
    )


def save_results(summary: 'EvaluationSummary', output_dir: str = "evaluation/results") -> None:
    """Save evaluation results to JSON."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"evaluation_{timestamp}.json")
    
    with open(filepath, 'w') as f:
        json.dump(summary.model_dump(), f, indent=2, default=str)
    
    print(f"\nResults saved to {filepath}")
    
    # Also save human-readable summary
    summary_path = os.path.join(output_dir, f"summary_{timestamp}.md")
    with open(summary_path, 'w') as f:
        f.write(f"# Evaluation Summary - {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Scenarios**: {summary.total_scenarios}\n")
        f.write(f"**Passed**: {summary.passed}\n")
        f.write(f"**Failed**: {summary.failed}\n")
        f.write(f"**Pass Rate**: {summary.passed/summary.total_scenarios*100:.1f}%\n")
        f.write(f"**Total Latency**: {summary.total_latency_ms}ms\n")
        f.write(f"**Avg Latency**: {summary.total_latency_ms/summary.total_scenarios:.0f}ms\n\n")
        
        f.write("## Metrics\n\n")
        for metric, value in summary.metrics.items():
            f.write(f"- **{metric}**: {value:.2f}\n")
        
        f.write("\n## Results\n\n")
        for r in summary.results:
            status = "✅ PASS" if r.passed else "❌ FAIL"
            f.write(f"- {status} **{r.scenario_name}** ({r.scenario_id}) - {r.latency_ms}ms\n")
            if r.errors:
                for err in r.errors:
                    f.write(f"  - {err}\n")
    
    print(f"Summary saved to {summary_path}")


async def main():
    """Main entry point for evaluation runner."""
    print("Starting ResolveAI Evaluation Suite")
    print(f"Total scenarios: {len(scenario_store.get_all())}")
    
    # Load scenarios from scenario files
    import evaluation.scenarios.refund_scenarios
    import evaluation.scenarios.cancellation_scenarios
    import evaluation.scenarios.escalation_shipping_scenarios
    
    print(f"Loaded {len(scenario_store.get_all())} scenarios")
    
    summary = await run_all_evaluations()
    save_results(summary)
    
    print("\n=== Evaluation Complete ===")
    print(f"Passed: {summary.passed}/{summary.total_scenarios}")
    print(f"Failed: {summary.failed}/{summary.total_scenarios}")
    for metric, value in summary.metrics.items():
        print(f"  {metric}: {value:.2f}")


if __name__ == "__main__":
    asyncio.run(main())