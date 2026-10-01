import asyncio
from evaluation.integration.real_runner import RealIntegrationRunner, real_scenario_store

async def main():
    runner = RealIntegrationRunner()
    await runner.setup_test_data()
    
    scenario = None
    for s in real_scenario_store.get_all():
        if s.id == 'tool_001':
            scenario = s
            break
    
    if not scenario:
        print('Scenario not found')
        return
    
    result = await RealIntegrationRunner().run_scenario(scenario)
    
    print(f'Status: {result.status.value}')
    print(f'Duration: {result.duration_ms}ms')
    print(f'Checks passed: {result.checks_passed}')
    print(f'Checks failed: {result.checks_failed}')
    print(f'Failure reason: {result.failure_reason}')

asyncio.run(main())