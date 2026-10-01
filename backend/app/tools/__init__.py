from app.tools.registry import tool_registry
from app.tools.get_order import get_order_tool
from app.tools.get_customer import get_customer_tool
from app.tools.get_shipping_status import get_shipping_status_tool
from app.tools.search_company_policy import search_company_policy_tool
from app.tools.calculate_refund import calculate_refund_tool
from app.tools.issue_refund import issue_refund_tool
from app.tools.cancel_order import cancel_order_tool
from app.tools.create_escalation import create_escalation_tool

# Register all tools
tool_registry.register(get_order_tool)
tool_registry.register(get_customer_tool)
tool_registry.register(get_shipping_status_tool)
tool_registry.register(search_company_policy_tool)
tool_registry.register(calculate_refund_tool)
tool_registry.register(issue_refund_tool)
tool_registry.register(cancel_order_tool)
tool_registry.register(create_escalation_tool)

__all__ = [
    "tool_registry",
    "get_order_tool",
    "get_customer_tool",
    "get_shipping_status_tool",
    "search_company_policy_tool",
    "calculate_refund_tool",
    "issue_refund_tool",
    "cancel_order_tool",
    "create_escalation_tool",
]