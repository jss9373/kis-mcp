#!/bin/bash
python3 - << 'PYEOF'
import json
path = '/mnt/c/Users/cappy/AppData/Roaming/Claude/claude_desktop_config.json'
with open(path) as f:
    cfg = json.load(f)
cfg['mcpServers'].pop('kis', None)
with open(path, 'w') as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
print('KIS MCP 비활성화 완료 — Claude Desktop 재시작하세요')
PYEOF
