import re

with open(r'E:\ResolveAI\backend\evaluation\integration\scenarios.py', 'r', encoding='utf-8') as f:
    content = f.read()

matches = re.findall(r'request_id="eval_[^"]+"', content)
print(f'Remaining eval_ patterns: {len(matches)}')
for m in matches[:10]:
    print(f'  {m}')
if len(matches) > 10:
    print(f'  ... and {len(matches)-10} more')