import json
from pathlib import Path

cfg = Path("config/settings.json")
cfg.parent.mkdir(parents=True, exist_ok=True)

data = {}
if cfg.exists():
    try:
        data = json.loads(cfg.read_text())
    except Exception:
        data = {}

data.setdefault("company_name", data.get("company_name", ""))
data["auto_open_results"] = True

cfg.write_text(json.dumps(data, indent=2))
print("auto_open_results set to True in", cfg)

