with open('app/workflows/engine.py', 'rb') as f:
    content = f.read()
idx = content.find(b'async def _step_policy_check')
start = max(0, idx - 100)
end = min(len(content), idx + 200)
for i, ch in enumerate(content[start:end]):
    print(f'{i}: {ch} ({chr(ch) if 32 <= ch < 127 else ""})')