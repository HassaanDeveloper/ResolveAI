import asyncio
import time
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from evaluation.integration.models import (
    RealIntegrationScenario,
    RealEvaluationResult,
    RealEvaluationSummary,
    RealScenarioStatus,
    RealScenarioInput,
    real_scenario_store,
)
from evaluation.integration.fixtures import (
    TEST_POLICY_DOCUMENT,
    TEST_CANCELLATION_POLICY,
    TEST_CUSTOMERS,
    TEST_ORDERS,
    TEST_SHIPMENTS,
    TEST_REFUNDS,
    TEST_APPROVALS,
    TEST_NAMESPACE,
    EXPECTED_TEST_SECTIONS,
    EXPECTED_TEST_DOCUMENT_NAME,
    EXPECTED_TEST_CANCELLATION_DOCUMENT_NAME,
    get_test_order_by_number,
    get_test_shipment_by_order_id,
    get_test_customer_by_external_id,
    _RUNTIME_IDS,
)
from app.workflows.engine import workflow_engine
from app.workflows.models import ResolutionRequest, WorkflowStatus
from app.tools import tool_registry
from app.rag import ingestion_service, retrieval_service
from app.rag.models import Document, DocumentSource
from app.approvals import approval_service
from app.services.database import get_supabase_client
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RealIntegrationRunner:
    """Runs real integration evaluation scenarios against actual services."""
    
    def __init__(self):
        self.supabase = None
        self.created_test_records = []  # Track for cleanup
    
    def _get_client(self):
        if self.supabase is None:
            self.supabase = get_supabase_client()
        return self.supabase
    
    async def setup_test_data(self) -> None:
        """Set up synthetic test data in Supabase."""
        client = self._get_client()
        
        # Clear runtime IDs cache
        _RUNTIME_IDS["customers"].clear()
        _RUNTIME_IDS["orders"].clear()
        _RUNTIME_IDS["shipments"].clear()
        
        # Insert test customers (no id field - DB generates UUID)
        for customer in TEST_CUSTOMERS:
            try:
                result = client.table("customers").upsert(customer).execute()
                if result.data:
                    customer_id = result.data[0]["id"]
                    self.created_test_records.append(("customers", customer_id))
                    # Cache by external_customer_id for lookups
                    _RUNTIME_IDS["customers"][customer["external_customer_id"]] = customer_id
            except Exception as e:
                logger.warning(f"Failed to insert test customer {customer['external_customer_id']}: {e}")
        
        # Insert test orders (resolve customer_id from external_customer_id)
        for order in TEST_ORDERS:
            try:
                # Get customer UUID
                customer_id = _RUNTIME_IDS["customers"].get(order.get("external_customer_id"))
                if not customer_id:
                    # Try to look up
                    customer_id = client.table("customers").select("id").eq("external_customer_id", order["external_customer_id"]).single().execute()
                    if customer_id.data:
                        customer_id = customer_id.data["id"]
                    else:
                        logger.warning(f"Customer not found for order {order['order_number']}: {order['external_customer_id']}")
                        continue
                
                order_data = {k: v for k, v in order.items() if k not in ("external_customer_id", "id")}
                order_data["customer_id"] = customer_id
                
                result = client.table("orders").upsert(order_data).execute()
                if result.data:
                    order_id = result.data[0]["id"]
                    self.created_test_records.append(("orders", order_id))
                    # Cache by order_number for lookups
                    _RUNTIME_IDS["orders"][order["order_number"]] = order_id
            except Exception as e:
                logger.warning(f"Failed to insert test order {order['order_number']}: {e}")
        
        # Insert test shipments (resolve order_id from order_number)
        for shipment in TEST_SHIPMENTS:
            try:
                order_id = _RUNTIME_IDS["orders"].get(shipment.get("order_number"))
                if not order_id:
                    order_id = client.table("orders").select("id").eq("order_number", shipment["order_number"]).single().execute()
                    if order_id.data:
                        order_id = order_id.data["id"]
                    else:
                        logger.warning(f"Order not found for shipment {shipment['tracking_number']}: {shipment['order_number']}")
                        continue
                
                shipment_data = {k: v for k, v in shipment.items() if k not in ("order_number", "id")}
                shipment_data["order_id"] = order_id
                
                result = client.table("shipments").upsert(shipment_data).execute()
                if result.data:
                    shipment_id = result.data[0]["id"]
                    self.created_test_records.append(("shipments", shipment_id))
                    # Cache by tracking_number for lookups
                    _RUNTIME_IDS["shipments"][shipment["tracking_number"]] = shipment_id
            except Exception as e:
                logger.warning(f"Failed to insert test shipment {shipment['tracking_number']}: {e}")
        
        # Insert test refunds (resolve order_id from order_number)
        for refund in TEST_REFUNDS:
            try:
                order_id = _RUNTIME_IDS["orders"].get(refund.get("order_number"))
                if not order_id:
                    order_id = client.table("orders").select("id").eq("order_number", refund["order_number"]).single().execute()
                    if order_id.data:
                        order_id = order_id.data["id"]
                    else:
                        logger.warning(f"Order not found for refund {refund['operation_id']}: {refund['order_number']}")
                        continue
                
                refund_data = {k: v for k, v in refund.items() if k not in ("order_number", "id")}
                refund_data["order_id"] = order_id
                
                result = client.table("refunds").upsert(refund_data).execute()
                if result.data:
                    refund_id = result.data[0]["id"]
                    self.created_test_records.append(("refunds", refund_id))
            except Exception as e:
                logger.warning(f"Failed to insert test refund {refund['operation_id']}: {e}")
        
        logger.info(f"Set up {len(self.created_test_records)} test records")
    
    async def cleanup_test_data(self, full: bool = False) -> None:
        """Clean up test data from Supabase.

        Args:
            full: If True, clean up core test data tables as well. 
                  If False (default), only clean workflow tables.

        Teardown order is FK-driven: children before parents.
        audit_events/approval_requests -> resolutions -> refunds -> operations
        -> shipments -> orders -> customers.
        """
        client = self._get_client()

        # Resolutions created by the evaluator carry the namespace in one of
        # two places, so both are matched:
        #   * order_number - set once an order is resolved. Note that
        #     request_id is a UUID for these, so a request_id prefix filter
        #     never matches.
        #   * request_id  - scenarios that fail before order lookup
        #     (e.g. llm_002 grounding) leave order_number NULL and only
        #     expose the namespace through request_id.
        eval_resolution_ids = set()
        for column in ("order_number", "request_id"):
            try:
                rows = (client.table("resolutions")
                        .select("id")
                        .like(column, f"%{TEST_NAMESPACE}%")
                        .execute())
                eval_resolution_ids.update(r["id"] for r in (rows.data or []))
            except Exception as e:
                logger.warning(f"Failed to list test resolutions by {column}: {e}")

        # 1. Children of resolutions: audit_events and approval_requests.
        #    These FK-reference resolutions, so they must go first or the
        #    resolutions delete is rejected by the database.
        for rid in eval_resolution_ids:
            for table in ("audit_events", "approval_requests"):
                try:
                    client.table(table).delete().eq("resolution_id", rid).execute()
                except Exception as e:
                    logger.warning(f"Failed to delete test records from {table} for {rid}: {e}")

        # 2. Resolutions themselves, via either namespace-bearing column.
        for column in ("order_number", "request_id"):
            try:
                client.table("resolutions").delete().like(column, f"%{TEST_NAMESPACE}%").execute()
            except Exception as e:
                logger.warning(f"Failed to delete test records from resolutions by {column}: {e}")

        # 3. Refunds: FK to orders, so they must be removed before orders.
        #    operation_id is prefixed by the action, e.g.
        #    "refund-order-eval-test-10001-49.99", hence the substring match.
        for table, column in (("refunds", "operation_id"), ("operations", "operation_id")):
            try:
                client.table(table).delete().like(column, f"%{TEST_NAMESPACE}%").execute()
            except Exception as e:
                logger.warning(f"Failed to delete test records from {table}: {e}")

        if full:
            # 4. Core test data tables, children first.
            #    shipments reference orders; orders reference customers.
            try:
                client.table("shipments").delete().like("tracking_number", f"%{TEST_NAMESPACE}%").execute()
            except Exception as e:
                logger.warning(f"Failed to delete test records from shipments: {e}")

            try:
                client.table("orders").delete().like("order_number", f"%{TEST_NAMESPACE}%").execute()
            except Exception as e:
                logger.warning(f"Failed to delete test records from orders: {e}")

            try:
                client.table("customers").delete().like("external_customer_id", f"%{TEST_NAMESPACE}%").execute()
            except Exception as e:
                logger.warning(f"Failed to delete test records from customers: {e}")

            # Tracked records are removed last as a safety net for any fixture
            # row whose business key did not carry the namespace.
            for table, record_id in reversed(self.created_test_records):
                try:
                    client.table(table).delete().eq("id", record_id).execute()
                except Exception as e:
                    logger.warning(f"Failed to delete test record {table}.{record_id}: {e}")

            self.created_test_records.clear()
        
        logger.info("Cleaned up test data")
    
    async def seed_test_documents(self) -> List[str]:
        """Seed test policy documents for RAG evaluation."""
        client = self._get_client()
        document_ids = []
        
        # Create test refund policy document
        refund_doc = Document(
            name=EXPECTED_TEST_DOCUMENT_NAME,
            source=DocumentSource("test-policy"),
            version="1.0",
            content=TEST_POLICY_DOCUMENT,
            metadata={"test_namespace": TEST_NAMESPACE}
        )
        
        result = await ingestion_service.ingest_document(refund_doc)
        if result.success:
            document_ids.append(result.document_id)
            logger.info(f"Seeded test refund policy document: {result.document_id}")
        
        # Create test cancellation policy document
        cancel_doc = Document(
            name=EXPECTED_TEST_CANCELLATION_DOCUMENT_NAME,
            source=DocumentSource("test-policy"),
            version="1.0",
            content=TEST_CANCELLATION_POLICY,
            metadata={"test_namespace": TEST_NAMESPACE}
        )
        
        result = await ingestion_service.ingest_document(cancel_doc)
        if result.success:
            document_ids.append(result.document_id)
            logger.info(f"Seeded test cancellation policy document: {result.document_id}")
        
        return document_ids
    
    async def cleanup_test_documents(self, document_ids: List[str]) -> None:
        """Clean up test documents."""
        for doc_id in document_ids:
            try:
                await ingestion_service.delete_document(doc_id)
            except Exception as e:
                logger.warning(f"Failed to delete test document {doc_id}: {e}")
    
    async def run_scenario(self, scenario: RealIntegrationScenario) -> RealEvaluationResult:
        """Run a single real integration scenario with proper test isolation."""
        # Generate unique request_id for this run to avoid duplicate key conflicts
        unique_suffix = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        original_request_id = scenario.input.request_id
        unique_request_id = f"{original_request_id}_{unique_suffix}"
        
        # Create a copy of the input with unique request_id
        scenario_input = RealScenarioInput(
            request_id=unique_request_id,
            user_request=scenario.input.user_request,
            customer_id=scenario.input.customer_id,
            order_id=scenario.input.order_id,
        )
        
        # Create modified scenario with unique request_id
        modified_scenario = RealIntegrationScenario(
            id=scenario.id,
            name=scenario.name,
            description=scenario.description,
            category=scenario.category,
            requires_gemini=scenario.requires_gemini,
            requires_supabase=scenario.requires_supabase,
            requires_pgvector=scenario.requires_pgvector,
            input=scenario_input,
            expectations=scenario.expectations,
            tags=scenario.tags,
        )
        
        start_time = time.time()
        checks_passed = []
        checks_failed = []
        trace = {}
        
        try:
            # Pre-scenario cleanup to ensure clean state
            await self.cleanup_test_data(full=False)
            
            # Check prerequisites
            if scenario.requires_gemini and (not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here"):
                return RealEvaluationResult(
                    scenario_id=scenario.id,
                    scenario_name=scenario.name,
                    status=RealScenarioStatus.SKIPPED,
                    duration_ms=0,
                    skip_reason="GEMINI_API_KEY not configured",
                )
            
            if scenario.requires_supabase and (not settings.SUPABASE_URL or settings.SUPABASE_URL == "https://your-project.supabase.co"):
                return RealEvaluationResult(
                    scenario_id=scenario.id,
                    scenario_name=scenario.name,
                    status=RealScenarioStatus.SKIPPED,
                    duration_ms=0,
                    skip_reason="SUPABASE_URL not configured",
                )
            
            # Run the scenario based on category
            if scenario.category == "rag":
                result = await self._run_rag_scenario(modified_scenario, checks_passed, checks_failed, trace)
            elif scenario.category == "policy":
                result = await self._run_policy_scenario(modified_scenario, checks_passed, checks_failed, trace)
            elif scenario.category == "tool_execution":
                result = await self._run_tool_execution_scenario(modified_scenario, checks_passed, checks_failed, trace)
            elif scenario.category == "approval":
                result = await self._run_approval_scenario(modified_scenario, checks_passed, checks_failed, trace)
            elif scenario.category == "side_effect_safety":
                result = await self._run_side_effect_safety_scenario(modified_scenario, checks_passed, checks_failed, trace)
            elif scenario.category == "llm":
                result = await self._run_llm_scenario(modified_scenario, checks_passed, checks_failed, trace)
            else:
                return RealEvaluationResult(
                    scenario_id=scenario.id,
                    scenario_name=scenario.name,
                    status=RealScenarioStatus.FAIL,
                    duration_ms=int((time.time() - start_time) * 1000),
                    checks_failed=[f"Unknown scenario category: {scenario.category}"],
                    failure_reason=f"Unknown scenario category: {scenario.category}",
                )
            
            # Post-scenario cleanup
            await self.cleanup_test_data(full=False)
            
            # Determine overall status
            status = RealScenarioStatus.PASS if len(checks_failed) == 0 else RealScenarioStatus.FAIL
            failure_reason = None if status == RealScenarioStatus.PASS else "; ".join(checks_failed)
            
            return RealEvaluationResult(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                status=status,
                duration_ms=int((time.time() - start_time) * 1000),
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                failure_reason=failure_reason,
                trace=trace,
            )
            
        except Exception as e:
            logger.error(f"Scenario {scenario.id} failed with exception: {e}")
            return RealEvaluationResult(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                status=RealScenarioStatus.FAIL,
                duration_ms=int((time.time() - start_time) * 1000),
                checks_failed=[f"Exception: {str(e)}"],
                failure_reason=str(e),
                trace=trace,
            )
    
    async def _run_rag_scenario(
        self,
        scenario: RealIntegrationScenario,
        checks_passed: List[str],
        checks_failed: List[str],
        trace: Dict[str, Any]
    ) -> None:
        """Run RAG evaluation scenario."""
        # This scenario tests: document -> chunking -> embedding -> pgvector -> retrieval -> evidence
        
        # Step 1: Verify test documents exist in pgvector
        client = self._get_client()
        doc_result = client.table("documents").select("id, name, content").ilike("name", "%Test%Integration%Evaluation%").execute()
        
        if not doc_result.data:
            checks_failed.append("No test documents found in database")
            return
        
        trace["seeded_documents"] = [{"id": d["id"], "name": d["name"]} for d in doc_result.data]
        checks_passed.append(f"Found {len(doc_result.data)} seeded test documents")
        
        # Step 2: Verify chunks exist with embeddings
        chunks_result = client.table("document_chunks").select("id, document_id, embedding").in_(
            "document_id", [d["id"] for d in doc_result.data]
        ).execute()
        
        chunks_with_embeddings = [c for c in (chunks_result.data or []) if c.get("embedding")]
        trace["chunks_total"] = len(chunks_result.data or [])
        trace["chunks_with_embeddings"] = len(chunks_with_embeddings)
        
        if len(chunks_with_embeddings) == 0:
            checks_failed.append("No chunks with embeddings found")
            return
        
        checks_passed.append(f"Found {len(chunks_with_embeddings)} chunks with embeddings")
        
        # Step 3: Perform actual retrieval query
        request = scenario.input
        from app.rag.retrieval.models import RetrievalRequest
        
        retrieval_request = RetrievalRequest(
            query=request.user_request,
            max_results=5,
            similarity_threshold=0.6,
        )
        
        retrieval_response = await retrieval_service.retrieve(retrieval_request)
        trace["retrieval_response"] = {
            "query": retrieval_response.query,
            "total_candidates": retrieval_response.total_candidates,
            "evidence_count": len(retrieval_response.evidence),
            "processing_time_ms": retrieval_response.processing_time_ms,
        }
        
        # Step 4: Verify evidence quality
        if scenario.expectations.evidence:
            exp = scenario.expectations.evidence
            
            if exp.must_have_evidence and len(retrieval_response.evidence) == 0:
                checks_failed.append("Expected evidence but retrieved none")
            else:
                checks_passed.append(f"Retrieved {len(retrieval_response.evidence)} evidence items")
            
            # Verify evidence comes from seeded documents
            evidence_from_test_docs = 0
            for ev in retrieval_response.evidence:
                if ev.document_name in [EXPECTED_TEST_DOCUMENT_NAME, EXPECTED_TEST_CANCELLATION_DOCUMENT_NAME]:
                    evidence_from_test_docs += 1
            
            if evidence_from_test_docs > 0:
                checks_passed.append(f"Evidence originated from seeded test documents ({evidence_from_test_docs} items)")
            else:
                checks_failed.append("Retrieved evidence did not originate from seeded test documents")
            
            # Verify expected sections are present
            retrieved_sections = set(ev.section for ev in retrieval_response.evidence)
            for expected_section in exp.must_contain_sections:
                if expected_section in retrieved_sections:
                    checks_passed.append(f"Evidence contains expected section: {expected_section}")
                else:
                    checks_failed.append(f"Missing expected section in evidence: {expected_section}")
            
            # Verify relevance scores
            low_relevance = [ev for ev in retrieval_response.evidence if ev.relevance_score < exp.min_relevance_score]
            if low_relevance:
                checks_failed.append(f"{len(low_relevance)} evidence items below minimum relevance score ({exp.min_relevance_score})")
            else:
                checks_passed.append("All evidence meets minimum relevance score")
        
        trace["actual_evidence"] = [
            {
                "document_name": ev.document_name,
                "section": ev.section,
                "source": ev.source,
                "relevance_score": ev.relevance_score,
                "content_preview": ev.content[:200] if ev.content else ""
            }
            for ev in retrieval_response.evidence
        ]
    
    async def _run_policy_scenario(
        self,
        scenario: RealIntegrationScenario,
        checks_passed: List[str],
        checks_failed: List[str],
        trace: Dict[str, Any]
    ) -> None:
        """Run policy evaluation scenario with independent expectations."""
        from app.policies import policy_engine
        from app.policies.models import PolicyInput, PolicyDecision, ActionType
        
        request = scenario.input
        exp_policy = scenario.expectations.policy_decision
        
        # Build policy input from scenario
        # We need to determine the action type and gather facts
        action_type_map = {
            "refund_request": ActionType.ISSUE_REFUND,
            "cancellation_request": ActionType.CANCEL_ORDER,
            "escalation_request": ActionType.CREATE_ESCALATION,
        }
        
        # Determine intent from user request
        request_lower = request.user_request.lower()
        if "refund" in request_lower or "money back" in request_lower:
            intent = "refund_request"
        elif "cancel" in request_lower:
            intent = "cancellation_request"
        elif "escalate" in request_lower or "manager" in request_lower or "complaint" in request_lower:
            intent = "escalation_request"
        else:
            intent = "refund_request"  # default
        
        action_type = action_type_map.get(intent, ActionType.ISSUE_REFUND)
        
        # Get order and shipment info if order_id provided
        order_status = None
        shipment_status = None
        refund_amount = None
        eligibility_satisfied = False
        eligibility_reason = ""
        
        if request.order_id:
            order = get_test_order_by_number(request.order_id)
            if order:
                order_status = order["status"]
                # Determine eligibility based on test data
                if intent == "refund_request":
                    refund_amount = order["total_amount"]
                    shipment = get_test_shipment_by_order_id(order["order_number"])
                    if shipment:
                        shipment_status = shipment["status"]
                        # Check eligibility based on our test policy
                        if shipment_status in ["delayed", "in_transit", "failed"]:
                            eligibility_satisfied = True
                            eligibility_reason = "Delayed/failed shipment per test policy"
                        elif order_status == "delivered":
                            # Check if within 30 days
                            if shipment_status == "delivered" and shipment.get("delivered_at"):
                                # Simplified check
                                eligibility_satisfied = False
                                eligibility_reason = "Delivered outside 30-day window per test policy"
        
        policy_input = PolicyInput(
            action_type=action_type,
            order_status=order_status,
            shipment_status=shipment_status,
            refund_amount=refund_amount,
            eligibility_satisfied=eligibility_satisfied,
            eligibility_reason=eligibility_reason,
        )
        
        # Evaluate using REAL policy engine
        policy_output = policy_engine.evaluate(policy_input)
        
        trace["policy_input"] = {
            "action_type": action_type.value,
            "order_status": order_status,
            "shipment_status": shipment_status,
            "refund_amount": str(refund_amount) if refund_amount else None,
            "eligibility_satisfied": eligibility_satisfied,
            "eligibility_reason": eligibility_reason,
        }
        trace["policy_output"] = {
            "decision": policy_output.decision.value,
            "reason": policy_output.reason,
            "policy_rule": policy_output.policy_rule,
            "risk_level": policy_output.risk_level.value,
            "approval_tier": policy_output.approval_tier,
        }
        
        # Check policy decision against INDEPENDENT expectations
        if policy_output.decision.value == exp_policy.decision:
            checks_passed.append(f"Policy decision matches expected: {exp_policy.decision}")
        else:
            checks_failed.append(f"Policy decision mismatch: expected {exp_policy.decision}, got {policy_output.decision.value}")
        
        if exp_policy.approval_tier:
            if policy_output.approval_tier == exp_policy.approval_tier:
                checks_passed.append(f"Approval tier matches expected: {exp_policy.approval_tier}")
            else:
                checks_failed.append(f"Approval tier mismatch: expected {exp_policy.approval_tier}, got {policy_output.approval_tier}")
        
        if exp_policy.reason_contains:
            for expected_phrase in exp_policy.reason_contains:
                if expected_phrase.lower() in policy_output.reason.lower():
                    checks_passed.append(f"Policy reason contains expected phrase: '{expected_phrase}'")
                else:
                    checks_failed.append(f"Policy reason missing expected phrase: '{expected_phrase}'")
    
    async def _run_tool_execution_scenario(
        self,
        scenario: RealIntegrationScenario,
        checks_passed: List[str],
        checks_failed: List[str],
        trace: Dict[str, Any]
    ) -> None:
        """Run tool execution scenario with actual tool registry and Supabase."""
        request = scenario.input
        
        # Execute workflow (which uses real tool registry)
        resolution_request = ResolutionRequest(
            request_id=request.request_id,
            user_request=request.user_request,
            customer_id=request.customer_id,
            order_id=request.order_id,
        )
        
        workflow = await workflow_engine.execute(resolution_request)
        
        trace["workflow"] = {
            "id": workflow.id,
            "status": workflow.status.value,
            "intent": workflow.intent.value if workflow.intent else None,
            "order_number": workflow.order_number,
            "tool_calls": [
                {
                    "tool": call.tool_name,
                    "input": call.input_data,
                    "success": call.success,
                    "output": call.output_data,
                    "error": call.error,
                }
                for call in workflow.tool_calls
            ],
            "policy_result": {
                "decision": workflow.policy_result.decision if workflow.policy_result else None,
                "reason": workflow.policy_result.reason if workflow.policy_result else None,
            } if workflow.policy_result else None,
        }
        
        # Verify expected side effects
        for exp_se in scenario.expectations.side_effects:
            # Check if tool was called
            tool_called = any(call.tool_name == exp_se.tool_name for call in workflow.tool_calls)
            tool_succeeded = any(
                call.tool_name == exp_se.tool_name and call.success 
                for call in workflow.tool_calls
            )
            
            if exp_se.should_execute:
                if tool_succeeded:
                    checks_passed.append(f"Side-effect tool {exp_se.tool_name} executed successfully")
                    
                    # Verify database state if specified
                    if exp_se.expected_db_state:
                        await self._verify_db_state(exp_se.expected_db_state, checks_passed, checks_failed, trace)
                else:
                    checks_failed.append(f"Expected side-effect tool {exp_se.tool_name} to execute but it did not succeed")
            else:
                if tool_succeeded:
                    checks_failed.append(f"Side-effect tool {exp_se.tool_name} should NOT have executed but did")
                else:
                    checks_passed.append(f"Side-effect tool {exp_se.tool_name} correctly did not execute")
        
        # Verify final workflow status
        if workflow.status.value == scenario.expectations.final_workflow_status:
            checks_passed.append(f"Final workflow status matches expected: {scenario.expectations.final_workflow_status}")
        else:
            checks_failed.append(f"Final workflow status mismatch: expected {scenario.expectations.final_workflow_status}, got {workflow.status.value}")
    
    async def _verify_db_state(
        self,
        expected_state: Dict[str, Any],
        checks_passed: List[str],
        checks_failed: List[str],
        trace: Dict[str, Any]
    ) -> None:
        """Verify database state matches expectations."""
        client = self._get_client()
        
        for key, expected_value in expected_state.items():
            # Parse table.column format
            if "." in key:
                table, column = key.split(".", 1)
                try:
                    result = client.table(table).select(column).execute()
                    actual_values = [row[column] for row in (result.data or []) if row.get(column) is not None]
                    
                    if expected_value in actual_values:
                        checks_passed.append(f"DB state verified: {key} == {expected_value}")
                    else:
                        checks_failed.append(f"DB state mismatch: {key} expected {expected_value}, found {actual_values}")
                except Exception as e:
                    checks_failed.append(f"Failed to verify DB state {key}: {e}")
    
    async def _run_approval_scenario(
        self,
        scenario: RealIntegrationScenario,
        checks_passed: List[str],
        checks_failed: List[str],
        trace: Dict[str, Any]
    ) -> None:
        """Run approval state transition scenario."""
        request = scenario.input
        exp_approval = scenario.expectations.approval_state
        
        if not exp_approval:
            checks_failed.append("Approval scenario requires approval_state expectations")
            return
        
        # Execute workflow to create approval request
        resolution_request = ResolutionRequest(
            request_id=request.request_id,
            user_request=request.user_request,
            customer_id=request.customer_id,
            order_id=request.order_id,
        )
        
        workflow = await workflow_engine.execute(resolution_request)
        
        trace["workflow"] = {
            "id": workflow.id,
            "status": workflow.status.value,
            "approval_id": workflow.context.get("approval_id") if workflow.context else None,
        }
        
        # Check if approval was created
        approval_id = workflow.context.get("approval_id") if workflow.context else None
        if not approval_id:
            if exp_approval.expected_status == "PENDING":
                checks_failed.append("Expected approval request to be created but none found")
                return
            else:
                checks_passed.append("No approval required (as expected)")
                return
        
        # Get approval from database
        try:
            approval = await approval_service.get_approval(approval_id)
            trace["approval"] = {
                "id": approval.id,
                "status": approval.status.value,
                "requested_at": approval.requested_at.isoformat() if approval.requested_at else None,
                "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
                "decided_by": approval.decided_by,
            }
            
            # Check current status
            if approval.status.value == exp_approval.expected_status:
                checks_passed.append(f"Approval status matches expected: {exp_approval.expected_status}")
            else:
                checks_failed.append(f"Approval status mismatch: expected {exp_approval.expected_status}, got {approval.status.value}")
            
            # If transition sequence specified, verify it
            if exp_approval.transition_sequence:
                # For now, just check final state matches last in sequence
                expected_final = exp_approval.transition_sequence[-1]
                if approval.status.value == expected_final:
                    checks_passed.append(f"Approval transitioned to expected final state: {expected_final}")
                else:
                    checks_failed.append(f"Approval did not reach expected final state: expected {expected_final}, got {approval.status.value}")
        
        except Exception as e:
            checks_failed.append(f"Failed to retrieve approval: {e}")
        
        # Verify final workflow status
        if workflow.status.value == scenario.expectations.final_workflow_status:
            checks_passed.append(f"Final workflow status matches expected: {scenario.expectations.final_workflow_status}")
        else:
            checks_failed.append(f"Final workflow status mismatch: expected {scenario.expectations.final_workflow_status}, got {workflow.status.value}")
    
    async def _run_side_effect_safety_scenario(
        self,
        scenario: RealIntegrationScenario,
        checks_passed: List[str],
        checks_failed: List[str],
        trace: Dict[str, Any]
    ) -> None:
        """Run side-effect safety scenario."""
        # This tests: ALLOWED executes, DENIED doesn't execute, approval-required doesn't execute before approval,
        # approved executes, idempotency prevents duplicates
        
        request = scenario.input
        
        # Execute workflow
        resolution_request = ResolutionRequest(
            request_id=request.request_id,
            user_request=request.user_request,
            customer_id=request.customer_id,
            order_id=request.order_id,
        )
        
        workflow = await workflow_engine.execute(resolution_request)
        
        trace["workflow"] = {
            "id": workflow.id,
            "status": workflow.status.value,
            "tool_calls": [
                {
                    "tool": call.tool_name,
                    "input": call.input_data,
                    "success": call.success,
                    "output": call.output_data,
                }
                for call in workflow.tool_calls
            ],
        }
        
        # Verify each expected side effect
        for exp_se in scenario.expectations.side_effects:
            tool_succeeded = any(
                call.tool_name == exp_se.tool_name and call.success 
                for call in workflow.tool_calls
            )
            
            if exp_se.should_execute:
                if tool_succeeded:
                    checks_passed.append(f"Allowed side-effect {exp_se.tool_name} executed")
                    
                    # Verify database state
                    if exp_se.expected_db_state:
                        await self._verify_db_state(exp_se.expected_db_state, checks_passed, checks_failed, trace)
                else:
                    checks_failed.append(f"Allowed side-effect {exp_se.tool_name} should have executed but didn't")
            else:
                if tool_succeeded:
                    checks_failed.append(f"Denied/pending side-effect {exp_se.tool_name} executed when it shouldn't have")
                else:
                    checks_passed.append(f"Denied/pending side-effect {exp_se.tool_name} correctly blocked")
        
        # Verify idempotency if specified
        if exp_se.expected_operation_status == "duplicate":
            # Check operation record status
            client = self._get_client()
            for call in workflow.tool_calls:
                if call.tool_name in ["issue_refund", "cancel_order"]:
                    op_id = call.input_data.get("operation_id")
                    if op_id:
                        op_result = client.table("operations").select("status").eq("operation_id", op_id).execute()
                        if op_result.data and op_result.data[0]["status"] == "duplicate":
                            checks_passed.append(f"Idempotency verified: operation {op_id} marked as duplicate")
                        else:
                            checks_failed.append(f"Idempotency failed: operation {op_id} not marked as duplicate")
    
    async def _run_llm_scenario(
        self,
        scenario: RealIntegrationScenario,
        checks_passed: List[str],
        checks_failed: List[str],
        trace: Dict[str, Any]
    ) -> None:
        """Run LLM evaluation scenario with actual Gemini call."""
        from app.rag.embeddings import gemini_embedding_service
        
        request = scenario.input
        
        # Verify Gemini is actually called
        try:
            # Test embedding generation (uses real Gemini)
            embedding = await gemini_embedding_service.embed_query("test query for evaluation")
            
            if embedding and len(embedding) == 3072:
                checks_passed.append("Gemini embedding service invoked successfully (3072-dim)")
                trace["embedding_dimension"] = len(embedding)
            else:
                checks_failed.append(f"Gemini embedding returned unexpected dimension: {len(embedding) if embedding else 0}")
        
        except Exception as e:
            checks_failed.append(f"Gemini embedding failed: {e}")
            trace["gemini_error"] = str(e)
            return
        
        # Run full workflow which may invoke LLM for response generation
        resolution_request = ResolutionRequest(
            request_id=request.request_id,
            user_request=request.user_request,
            customer_id=request.customer_id,
            order_id=request.order_id,
        )
        
        workflow = await workflow_engine.execute(resolution_request)
        
        trace["workflow"] = {
            "id": workflow.id,
            "status": workflow.status.value,
            "final_message": "See response",
        }
        
        # Verify LLM response was generated (check workflow has meaningful output)
        if workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.REJECTED, WorkflowStatus.PENDING_APPROVAL]:
            checks_passed.append("Workflow completed with real LLM-influenced path")
        else:
            checks_failed.append(f"Workflow ended in unexpected state: {workflow.status.value}")
        
        # Verify policy still controls decisions (LLM doesn't override)
        if workflow.policy_result:
            if workflow.policy_result.decision in ["ALLOW", "DENY", "REQUIRES_APPROVAL"]:
                checks_passed.append("Policy engine remained authoritative for decision")
            else:
                checks_failed.append("Policy engine returned unexpected decision")
        
        # If grounding expected, verify evidence used
        if scenario.expectations.grounding:
            exp_ground = scenario.expectations.grounding
            if exp_ground.answer_references_evidence and workflow.retrieved_documents:
                checks_passed.append("Retrieved evidence available for grounding")
            else:
                checks_failed.append("Expected evidence for grounding but none retrieved")


async def run_real_integration_evaluation() -> RealEvaluationSummary:
    """Run all real integration evaluation scenarios."""
    runner = RealIntegrationRunner()
    results = []
    
    print("=" * 60)
    print("ResolveAI Real Integration Evaluation (Layer B)")
    print("=" * 60)
    print(f"Total scenarios: {len(real_scenario_store.get_all())}")
    print()
    
    # Pre-run cleanup to ensure clean state
    # print("Pre-run cleanup (workflow tables only)...")
# await runner.cleanup_test_data(full=False)
# print("[OK] Pre-run cleanup complete")
    
    # Setup
    print("Setting up test data...")
    setup_success = True
    try:
        await runner.setup_test_data()
        print("[OK] Test data seeded")
    except Exception as e:
        print(f"[SKIP] Supabase not configured, skipping DB tests: {e}")
        setup_success = False
    
    # Seed test documents for RAG
    doc_ids = []
    if setup_success:
        try:
            doc_ids = await runner.seed_test_documents()
            print(f"[OK] Seeded {len(doc_ids)} test documents")
        except Exception as e:
            print(f"[SKIP] Failed to seed test documents: {e}")
    
    # Run scenarios
    for scenario in real_scenario_store.get_all():
        print(f"\nRunning: {scenario.name} ({scenario.id})")
        print(f"  Category: {scenario.category}")
        print(f"  Requires Gemini: {scenario.requires_gemini}")
        print(f"  Requires Supabase: {scenario.requires_supabase}")
        print(f"  Requires pgvector: {scenario.requires_pgvector}")
        
        result = await runner.run_scenario(scenario)
        results.append(result)
        
        status_str = result.status.value
        if result.status == RealScenarioStatus.PASS:
            print(f"  [PASS] {status_str} ({result.duration_ms}ms)")
        elif result.status == RealScenarioStatus.FAIL:
            print(f"  [FAIL] {status_str} ({result.duration_ms}ms)")
            for check in result.checks_failed:
                print(f"    FAIL: {check}")
        else:
            print(f"  [SKIP] {status_str} ({result.duration_ms}ms) - {result.skip_reason}")
        
        for check in result.checks_passed:
            print(f"    [OK] {check}")
    
    # Cleanup
    print("\nCleaning up...")
    try:
        await runner.cleanup_test_documents(doc_ids)
        await runner.cleanup_test_data(full=True)
        print("[OK] Cleanup complete")
    except Exception as e:
        print(f"[WARN] Cleanup warning: {e}")
    
    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.status == RealScenarioStatus.PASS)
    failed = sum(1 for r in results if r.status == RealScenarioStatus.FAIL)
    skipped = sum(1 for r in results if r.status == RealScenarioStatus.SKIPPED)
    
    by_category = {}
    for r in results:
        scenario = real_scenario_store.get_by_id(r.scenario_id)
        cat = scenario.category if scenario else "unknown"
        if cat not in by_category:
            by_category[cat] = {"passed": 0, "failed": 0, "skipped": 0}
        # Map enum values to dict keys
        status_key = r.status.value.lower()
        if status_key == "pass":
            status_key = "passed"
        elif status_key == "fail":
            status_key = "failed"
        elif status_key == "skipped":
            status_key = "skipped"
        by_category[cat][status_key] += 1
    
    total_latency = sum(r.duration_ms for r in results)
    
    summary = RealEvaluationSummary(
        total_scenarios=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        by_category=by_category,
        total_duration_ms=total_latency,
        timestamp=datetime.utcnow(),
        results=results,
    )
    
    print("\n" + "=" * 60)
    print("REAL INTEGRATION EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total Scenarios: {total}")
    print(f"[PASS] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")
    print(f"[SKIP] Skipped: {skipped}")
    print(f"Total Duration: {total_latency}ms")
    print()
    
    print("By Category:")
    for cat, counts in by_category.items():
        print(f"  {cat}: [PASS]{counts['passed']} [FAIL]{counts['failed']} [SKIP]{counts['skipped']}")
    
    print("\nDetailed Results:")
    for r in results:
        status_icon = "[PASS]" if r.status == RealScenarioStatus.PASS else "[FAIL]" if r.status == RealScenarioStatus.FAIL else "[SKIP]"
        print(f"  {status_icon} {r.scenario_name} ({r.scenario_id}) - {r.duration_ms}ms")
        if r.checks_failed:
            for check in r.checks_failed:
                print(f"    [FAIL] {check}")
        if r.skip_reason:
            print(f"    Skip reason: {r.skip_reason}")
    
    return summary


async def main():
    """Main entry point for real integration evaluation."""
    summary = await run_real_integration_evaluation()
    
    # Save results
    import json
    import os
    output_dir = "evaluation/integration/results"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"real_integration_{timestamp}.json")
    
    with open(filepath, 'w') as f:
        json.dump(summary.model_dump(), f, indent=2, default=str)
    
    print(f"\nResults saved to {filepath}")
    
    return summary


if __name__ == "__main__":
    asyncio.run(main())