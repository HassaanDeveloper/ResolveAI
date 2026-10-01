import asyncio
import traceback
import uuid

from app.workflows.engine import WorkflowEngine
from app.workflows.models import ResolutionRequest


async def main():
    req = ResolutionRequest(
        request_id=str(uuid.uuid4()),
        user_request="order 10482 hasn't arrived",
        customer_id="CUST-001",
        order_id="10482",
    )
    engine = WorkflowEngine()
    wf = await engine.execute(req)
    print("STATUS:", wf.status)
    print("FINAL:", wf.final_status)
    print("ERRORS:", wf.errors)
    print("INTENT:", wf.intent)
    print("ORDER_NUMBER:", wf.order_number)
    print("TOOL_CALLS:", [(c.tool_name, c.success) for c in wf.tool_calls])

    from app.api.routes.resolutions import _build_trace_response
    resp = _build_trace_response(wf)
    print("TRACE_RESP_OK status:", resp.status, "errors:", resp.errors)


try:
    asyncio.run(main())
except Exception:
    traceback.print_exc()
