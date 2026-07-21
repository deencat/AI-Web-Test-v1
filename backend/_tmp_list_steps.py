import json
from pathlib import Path

ex = json.loads(Path("../gan-harness/_eval_artifacts/ex1154.json").read_text(encoding="utf-8"))
for s in ex.get("steps") or []:
    desc = (s.get("step_description") or "")[:100]
    actual = (s.get("actual_result") or "")[:100]
    print(f"{s.get('step_number')}: {s.get('result')} | {desc}")
    if actual:
        print(f"   actual: {actual}")
