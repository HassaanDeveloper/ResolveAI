from evaluation.integration.fixtures import get_test_order_by_number, get_test_shipment_by_order_id, TEST_NAMESPACE
from app.policies import policy_engine
from app.policies.models import PolicyInput, PolicyDecision, ActionType

# Mimic the _run_policy_scenario logic for pol_001
request_order_id = 'eval-test-10001'
request_user_request = 'I want a refund for order eval-test-10001 - it has been delayed for 2 weeks'

# Determine intent
request_lower = request_user_request.lower()
if 'refund' in request_lower or 'money back' in request_lower:
    intent = 'refund_request'
elif 'cancel' in request_lower:
    intent = 'cancellation_request'
else:
    intent = 'refund_request'

action_type_map = {
    'refund_request': ActionType.ISSUE_REFUND,
    'cancellation_request': ActionType.CANCEL_ORDER,
    'escalation_request': ActionType.CREATE_ESCALATION,
}
action_type = action_type_map.get(intent, ActionType.ISSUE_REFUND)

# Get order and shipment info
order = get_test_order_by_number(request_order_id)
print('Order:', order)

if order:
    order_status = order['status']
    refund_amount = order['total_amount']
    shipment = get_test_shipment_by_order_id(order['id'])
    print('Shipment:', shipment)
    if shipment:
        shipment_status = shipment['status']
        if shipment_status in ['delayed', 'in_transit', 'failed']:
            eligibility_satisfied = True
            eligibility_reason = 'Delayed/failed shipment per test policy'
        elif order_status == 'delivered':
            eligibility_satisfied = False
            eligibility_reason = 'Delivered outside 30-day window per test policy'
        else:
            eligibility_satisfied = False
            eligibility_reason = 'Unknown'
    else:
        shipment_status = None
        eligibility_satisfied = False
        eligibility_reason = ''
else:
    order_status = None
    shipment_status = None
    refund_amount = None
    eligibility_satisfied = False
    eligibility_reason = ''

print(f'order_status={order_status}, shipment_status={shipment_status}, refund_amount={refund_amount}')
print(f'eligibility_satisfied={eligibility_satisfied}, eligibility_reason={eligibility_reason}')

policy_input = PolicyInput(
    action_type=action_type,
    order_status=order_status,
    shipment_status=shipment_status,
    refund_amount=refund_amount,
    eligibility_satisfied=eligibility_satisfied,
    eligibility_reason=eligibility_reason,
)

policy_output = policy_engine.evaluate(policy_input)
print(f'Decision: {policy_output.decision.value}')
print(f'Reason: {policy_output.reason}')
print(f'Policy Rule: {policy_output.policy_rule}')