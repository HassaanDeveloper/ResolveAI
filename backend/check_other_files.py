import re

for fname in ['escalation_shipping_scenarios.py', 'cancellation_scenarios.py', 'refund_scenarios.py']:
    with open(f'E:\\ResolveAI\\backend\\evaluation\\integration\\scenarios\\{fname}', 'r', encoding='utf-8') as f:
        content = f.read()
    matches = re.findall(r'request_id="eval_[^"]+"', content)
    print(f'{fname}: {len(matches)} remaining eval_ patterns')
    for m in matches[:5]:
        print(f'  {m}')
    if len(matches) > 5:
        print(f'  ... and {len(matches)-5} more')