import re

# Read the scenarios.py file
with open(r'E:\ResolveAI\backend\evaluation\integration\scenarios.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all eval_<prefix>_<number> patterns with eval-test-<prefix>-<number>
# Pattern: request_id="eval_<prefix>_<number>" -> request_id=f"{TEST_NAMESPACE}<prefix>-<number>"

replacements = {
    # RAG scenarios
    'request_id="eval_rag_001"': 'request_id=f"{TEST_NAMESPACE}rag-001"',
    'request_id="eval_rag_002"': 'request_id=f"{TEST_NAMESPACE}rag-002"',
    
    # Policy scenarios
    'request_id="eval_pol_001"': 'request_id=f"{TEST_NAMESPACE}pol-001"',
    'request_id="eval_pol_002"': 'request_id=f"{TEST_NAMESPACE}pol-002"',
    'request_id="eval_pol_003"': 'request_id=f"{TEST_NAMESPACE}pol-003"',
    'request_id="eval_pol_004"': 'request_id=f"{TEST_NAMESPACE}pol-004"',
    'request_id="eval_pol_005"': 'request_id=f"{TEST_NAMESPACE}pol-005"',
    'request_id="eval_pol_006"': 'request_id=f"{TEST_NAMESPACE}pol-006"',
    
    # Tool scenarios
    'request_id="eval_tool_001"': 'request_id=f"{TEST_NAMESPACE}tool-001"',
    'request_id="eval_tool_002"': 'request_id=f"{TEST_NAMESPACE}tool-002"',
    
    # Approval scenarios
    'request_id="eval_app_001"': 'request_id=f"{TEST_NAMESPACE}app-001"',
    'request_id="eval_app_002"': 'request_id=f"{TEST_NAMESPACE}app-002"',
    
    # LLM scenarios
    'request_id="eval_llm_001"': 'request_id=f"{TEST_NAMESPACE}llm-001"',
    'request_id="eval_llm_002"': 'request_id=f"{TEST_NAMESPACE}llm-002"',
    
    # Escalation scenarios
    'request_id="eval_escalation_001"': 'request_id=f"{TEST_NAMESPACE}escalation-001"',
    'request_id="eval_escalation_002"': 'request_id=f"{TEST_NAMESPACE}escalation-002"',
    
    # Shipping scenarios
    'request_id="eval_shipping_001"': 'request_id=f"{TEST_NAMESPACE}shipping-001"',
    'request_id="eval_shipping_002"': 'request_id=f"{TEST_NAMESPACE}shipping-002"',
    
    # Cancellation scenarios
    'request_id="eval_cancel_001"': 'request_id=f"{TEST_NAMESPACE}cancel-001"',
    'request_id="eval_cancel_002"': 'request_id=f"{TEST_NAMESPACE}cancel-002"',
    'request_id="eval_cancel_003"': 'request_id=f"{TEST_NAMESPACE}cancel-003"',
    
    # Refund scenarios
    'request_id="eval_refund_001"': 'request_id=f"{TEST_NAMESPACE}refund-001"',
    'request_id="eval_refund_002"': 'request_id=f"{TEST_NAMESPACE}refund-002"',
    'request_id="eval_refund_003"': 'request_id=f"{TEST_NAMESPACE}refund-003"',
    'request_id="eval_refund_004"': 'request_id=f"{TEST_NAMESPACE}refund-004"',
    'request_id="eval_refund_005"': 'request_id=f"{TEST_NAMESPACE}refund-005"',
    
    # Safe scenarios
    'request_id="eval_safe_001"': 'request_id=f"{TEST_NAMESPACE}safe-001"',
    'request_id="eval_safe_002"': 'request_id=f"{TEST_NAMESPACE}safe-002"',
    'request_id="eval_safe_003"': 'request_id=f"{TEST_NAMESPACE}safe-003"',
    'request_id="eval_safe_004"': 'request_id=f"{TEST_NAMESPACE}safe-004"',
    'request_id="eval_safe_005"': 'request_id=f"{TEST_NAMESPACE}safe-005"',
    
    # Escalation scenarios
    'request_id="eval_escalation_001"': 'request_id=f"{TEST_NAMESPACE}escalation-001"',
    'request_id="eval_escalation_002"': 'request_id=f"{TEST_NAMESPACE}escalation-002"',
    
    # Shipping scenarios
    'request_id="eval_shipping_001"': 'request_id=f"{TEST_NAMESPACE}shipping-001"',
    'request_id="eval_shipping_002"': 'request_id=f"{TEST_NAMESPACE}shipping-002"',
    
    # Cancellation scenarios
    'request_id="eval_cancel_001"': 'request_id=f"{TEST_NAMESPACE}cancel-001"',
    'request_id="eval_cancel_002"': 'request_id=f"{TEST_NAMESPACE}cancel-002"',
    'request_id="eval_cancel_003"': 'request_id=f"{TEST_NAMESPACE}cancel-003"',
    
    # Refund scenarios
    'request_id="eval_refund_001"': 'request_id=f"{TEST_NAMESPACE}refund-001"',
    'request_id="eval_refund_002"': 'request_id=f"{TEST_NAMESPACE}refund-002"',
    'request_id="eval_refund_003"': 'request_id=f"{TEST_NAMESPACE}refund-003"',
    'request_id="eval_refund_004"': 'request_id=f"{TEST_NAMESPACE}refund-004"',
    'request_id="eval_refund_005"': 'request_id=f"{TEST_NAMESPACE}refund-005"',
}

# Read the file
with open(r'E:\ResolveAI\backend\evaluation\integration\scenarios.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Apply all replacements
for old, new in replacements.items():
    content = content.replace(old, new)

# Write the modified content back
with open(r'E:\ResolveAI\backend\evaluation\integration\scenarios.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all request_id prefixes in scenarios.py")