import asyncio
from evaluation.integration.real_runner import RealIntegrationRunner, real_scenario_store
from app.workflows.engine import workflow_engine
from evaluation.integration.models import RealScenarioInput

async def main():
    runner = RealIntegrationRunner()
    await runner.setup_test_data()
    
    scenario = None
    for s in real_scenario_store.get_all():
        if s.id == 'safe_001':
            scenario = s
            break
    
    if not scenario:
        print('Scenario not found')
        return
    
    print('Running workflow engine directly...')
    
    workflow = await workflow_engine.execute(scenario.input)
    print(f'Workflow status: {workflow.status.value}')
    print(f'Workflow errors: {workflow.errors}')
    print(f'Tool calls: {len(workflow.tool_calls)}')
    for tc in workflow.tool_calls:
        print(f'  - {tc.tool_name}: success={tc.success}, error={tc.error}')
    print(f'Policy result: {workflow.policy_result}')
    if workflow.policy_result:
        print(f'  Decision: {workflow.policy_result.decision}')
        print(f'  Approval tier: {workflow.policy_result.approval_tier}')
    print(f'Action result: {workflow.action_result}')
    print(f'Verification: {workflow.verification}')
    print(f'Errors: {workflow.errors}')

asyncio.run(main())