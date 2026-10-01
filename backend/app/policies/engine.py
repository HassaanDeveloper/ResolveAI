from decimal import Decimal
from typing import List, Optional
from app.policies.models import (
    PolicyInput,
    PolicyOutput,
    PolicyDecision,
    RiskLevel,
    ActionType,
    PolicyRule,
)


class PolicyEngine:
    """
    Deterministic policy engine for business rule enforcement.
    
    The LLM may recommend actions, but this engine makes the final
    ALLOW/DENY/REQUIRES_APPROVAL decision based on deterministic rules.
    The LLM must NEVER override policy decisions.
    """

    # Approval thresholds (USD)
    AUTO_APPROVE_THRESHOLD = Decimal("100.00")
    MANAGER_APPROVE_THRESHOLD = Decimal("500.00")
    DIRECTOR_APPROVE_THRESHOLD = Decimal("1000.00")

    def __init__(self):
        self.rules = self._initialize_rules()

    def _initialize_rules(self) -> List[PolicyRule]:
        """Initialize the ordered list of policy rules."""
        return [
            PolicyRule(
                name="refund_eligibility_denied",
                description="Refund violating eligibility requirements",
                condition="action_type == issue_refund and not eligibility_satisfied",
                decision=PolicyDecision.DENY,
                priority=100,  # Highest priority - deny first
            ),
            PolicyRule(
                name="refund_high_value_customer_escalation",
                description="High-value customer or previous escalations require approval regardless of amount",
                condition="action_type == issue_refund and eligibility_satisfied and (is_high_value_customer or previous_escalations > 0)",
                decision=PolicyDecision.REQUIRES_APPROVAL,
                priority=95,
            ),
            PolicyRule(
                name="refund_carrier_loss_requires_approval",
                description="Carrier loss or damage refunds require approval regardless of amount",
                condition="action_type == issue_refund and eligibility_satisfied and (shipment_status == 'failed' or 'carrier' in (eligibility_reason or '').lower())",
                decision=PolicyDecision.REQUIRES_APPROVAL,
                priority=93,
            ),
            PolicyRule(
                name="refund_auto_approve",
                description="Refund <= $100 AND eligibility satisfied",
                condition="action_type == issue_refund and eligibility_satisfied and refund_amount <= 100",
                decision=PolicyDecision.ALLOW,
                priority=90,
            ),
            PolicyRule(
                name="refund_manager_approval",
                description="Refund > $100 and <= $500",
                condition="action_type == issue_refund and eligibility_satisfied and refund_amount > 100 and refund_amount <= 500",
                decision=PolicyDecision.REQUIRES_APPROVAL,
                priority=80,
            ),
            PolicyRule(
                name="refund_director_approval",
                description="Refund > $500 and <= $1000",
                condition="action_type == issue_refund and eligibility_satisfied and refund_amount > 500 and refund_amount <= 1000",
                decision=PolicyDecision.REQUIRES_APPROVAL,
                priority=70,
            ),
            PolicyRule(
                name="refund_legal_review",
                description="Refund > $1000 requires legal review",
                condition="action_type == issue_refund and eligibility_satisfied and refund_amount > 1000",
                decision=PolicyDecision.REQUIRES_APPROVAL,
                priority=60,
            ),
            PolicyRule(
                name="cancellation_after_shipment",
                description="Cancellation after shipment requires approval",
                condition="action_type == cancel_order and order_status in [shipped, in_transit, delivered]",
                decision=PolicyDecision.REQUIRES_APPROVAL,
                priority=90,
            ),
            PolicyRule(
                name="cancellation_before_shipment",
                description="Cancellation before shipment allowed",
                condition="action_type == cancel_order and order_status in [pending, processing]",
                decision=PolicyDecision.ALLOW,
                priority=80,
            ),
            PolicyRule(
                name="escalation_always_allowed",
                description="Creating escalations is always allowed",
                condition="action_type == create_escalation",
                decision=PolicyDecision.ALLOW,
                priority=100,
            ),
            PolicyRule(
                name="unknown_action_requires_approval",
                description="Unknown or high-risk actions require approval",
                condition="true",  # Catch-all
                decision=PolicyDecision.REQUIRES_APPROVAL,
                priority=0,  # Lowest priority
            ),
        ]

    def evaluate(self, input_data: PolicyInput) -> PolicyOutput:
        """
        Evaluate the policy input against all rules.
        
        Rules are evaluated in priority order (highest first).
        First matching rule determines the decision.
        """
        # Sort rules by priority (descending)
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            if self._evaluate_condition(rule.condition, input_data):
                return self._build_output(rule, input_data)

        # Should never reach here due to catch-all rule
        return PolicyOutput(
            decision=PolicyDecision.REQUIRES_APPROVAL,
            reason="No matching policy rule found",
            policy_rule="unknown_action_requires_approval",
            risk_level=RiskLevel.HIGH,
            requires_human_review=True,
        )

    def _evaluate_condition(self, condition: str, input_data: PolicyInput) -> bool:
        """Evaluate a rule condition against the input data."""
        # Create a safe evaluation context
        context = {
            "action_type": input_data.action_type,
            "order_status": input_data.order_status,
            "shipment_status": input_data.shipment_status,
            "refund_amount": input_data.refund_amount,
            "currency": input_data.currency,
            "eligibility_satisfied": input_data.eligibility_satisfied,
            "eligibility_reason": input_data.eligibility_reason,
            "policy_evidence": input_data.policy_evidence,
            "customer_tier": input_data.customer_tier,
            "is_high_value_customer": input_data.is_high_value_customer,
            "previous_escalations": input_data.previous_escalations,
            # Constants
            "AUTO_APPROVE_THRESHOLD": self.AUTO_APPROVE_THRESHOLD,
            "MANAGER_APPROVE_THRESHOLD": self.MANAGER_APPROVE_THRESHOLD,
            "DIRECTOR_APPROVE_THRESHOLD": self.DIRECTOR_APPROVE_THRESHOLD,
            "PolicyDecision": PolicyDecision,
            "RiskLevel": RiskLevel,
            "ActionType": ActionType,
        }

        try:
            # Replace enum references with values for evaluation
            eval_condition = condition
            for enum_val in ActionType:
                eval_condition = eval_condition.replace(f"ActionType.{enum_val.name}", f"'{enum_val.value}'")
            
            # Handle 'in' expressions for order_status
            eval_condition = eval_condition.replace("order_status in [shipped, in_transit, delivered]", 
                f"order_status in ['shipped', 'in_transit', 'delivered']")
            eval_condition = eval_condition.replace("order_status in [pending, processing]", 
                f"order_status in ['pending', 'processing']")
            
            # Handle enum comparisons
            eval_condition = eval_condition.replace("action_type == issue_refund", 
                f"action_type == '{ActionType.ISSUE_REFUND.value}'")
            eval_condition = eval_condition.replace("action_type == cancel_order", 
                f"action_type == '{ActionType.CANCEL_ORDER.value}'")
            eval_condition = eval_condition.replace("action_type == create_escalation", 
                f"action_type == '{ActionType.CREATE_ESCALATION.value}'")

            # Evaluate
            return eval(eval_condition, {"__builtins__": {}}, context)
        except Exception:
            return False

    def _build_output(self, rule: PolicyRule, input_data: PolicyInput) -> PolicyOutput:
        """Build the policy output based on the matched rule."""
        risk_level = self._determine_risk_level(rule, input_data)
        requires_review = rule.decision == PolicyDecision.REQUIRES_APPROVAL
        approval_tier = self._determine_approval_tier(rule, input_data)
        conditions = self._determine_conditions(rule, input_data)

        return PolicyOutput(
            decision=rule.decision,
            reason=self._format_reason(rule, input_data),
            policy_rule=rule.name,
            risk_level=risk_level,
            requires_human_review=requires_review,
            approval_tier=approval_tier,
            conditions=conditions,
        )

    def _determine_risk_level(self, rule: PolicyRule, input_data: PolicyInput) -> RiskLevel:
        """Determine risk level based on rule and input."""
        if rule.decision == PolicyDecision.DENY:
            return RiskLevel.HIGH
        if rule.decision == PolicyDecision.REQUIRES_APPROVAL:
            if input_data.action_type == ActionType.ISSUE_REFUND and input_data.refund_amount:
                if input_data.refund_amount > self.DIRECTOR_APPROVE_THRESHOLD:
                    return RiskLevel.HIGH
                elif input_data.refund_amount > self.MANAGER_APPROVE_THRESHOLD:
                    return RiskLevel.HIGH
                elif input_data.refund_amount > self.AUTO_APPROVE_THRESHOLD:
                    return RiskLevel.MEDIUM
            if input_data.action_type == ActionType.CANCEL_ORDER:
                if input_data.order_status == "delivered":
                    return RiskLevel.HIGH
                return RiskLevel.MEDIUM
            if input_data.is_high_value_customer or input_data.previous_escalations > 0:
                return RiskLevel.HIGH
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _determine_approval_tier(self, rule: PolicyRule, input_data: PolicyInput) -> Optional[str]:
        """Determine which approval tier is required."""
        if rule.decision != PolicyDecision.REQUIRES_APPROVAL:
            return None

        if input_data.action_type == ActionType.ISSUE_REFUND and input_data.refund_amount:
            if input_data.refund_amount > self.DIRECTOR_APPROVE_THRESHOLD:
                return "director"
            elif input_data.refund_amount > self.MANAGER_APPROVE_THRESHOLD:
                return "director"
            elif input_data.refund_amount > self.AUTO_APPROVE_THRESHOLD:
                return "manager"
        if input_data.action_type == ActionType.CANCEL_ORDER:
            if input_data.order_status == "delivered":
                return "director"
            return "manager"
        if input_data.is_high_value_customer or input_data.previous_escalations > 0:
            return "director"
        return "manager"

    def _determine_conditions(self, rule: PolicyRule, input_data: PolicyInput) -> List[str]:
        """Determine any conditions that must be met."""
        conditions = []
        if rule.decision == PolicyDecision.ALLOW:
            if input_data.action_type == ActionType.ISSUE_REFUND:
                conditions.append("Refund amount must not exceed order total")
                conditions.append("No prior completed refund for same order")
        elif rule.decision == PolicyDecision.REQUIRES_APPROVAL:
            if input_data.action_type == ActionType.ISSUE_REFUND:
                conditions.append(f"Requires {self._determine_approval_tier(rule, input_data)} approval")
                conditions.append("Refund amount must not exceed order total")
            if input_data.action_type == ActionType.CANCEL_ORDER:
                conditions.append(f"Requires {self._determine_approval_tier(rule, input_data)} approval")
                if input_data.order_status == "shipped":
                    conditions.append("Carrier intercept may be required")
        return conditions

    def _format_reason(self, rule: PolicyRule, input_data: PolicyInput) -> str:
        """Format a human-readable reason for the decision."""
        if rule.name == "refund_eligibility_denied":
            return f"Refund denied: {input_data.eligibility_reason or 'Policy eligibility not satisfied'}"
        elif rule.name == "refund_carrier_loss_requires_approval":
            return f"Refund of ${input_data.refund_amount} requires approval: carrier loss/damage detected"
        elif rule.name == "refund_auto_approve":
            return f"Refund of ${input_data.refund_amount} auto-approved: eligible amount within auto-approve threshold (<=${self.AUTO_APPROVE_THRESHOLD})"
        elif rule.name == "refund_manager_approval":
            return f"Refund of ${input_data.refund_amount} requires manager approval: exceeds auto-approve threshold (${self.AUTO_APPROVE_THRESHOLD})"
        elif rule.name == "refund_director_approval":
            return f"Refund of ${input_data.refund_amount} requires director approval: exceeds manager threshold (${self.MANAGER_APPROVE_THRESHOLD})"
        elif rule.name == "refund_legal_review":
            return f"Refund of ${input_data.refund_amount} requires legal review: exceeds director threshold (${self.DIRECTOR_APPROVE_THRESHOLD})"
        elif rule.name == "cancellation_after_shipment":
            return f"Cancellation requires approval: order status is '{input_data.order_status}' (already shipped)"
        elif rule.name == "cancellation_before_shipment":
            return f"Cancellation auto-approved: order status is '{input_data.order_status}' (not yet shipped)"
        elif rule.name == "escalation_always_allowed":
            return "Escalation creation is always permitted"
        else:
            return f"Policy rule '{rule.name}' matched: {rule.description}"


# Singleton instance
policy_engine = PolicyEngine()