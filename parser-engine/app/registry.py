import json
from pathlib import Path
from .models import ParserSpec

class ParserRegistry:
    def __init__(self, root: str = "/app/parsers"):
        self.root = Path(root)

    def get(self, fingerprint: str) -> ParserSpec | None:
        path = self.root / f"{fingerprint}.json"
        if not path.exists():
            return None
        return ParserSpec.model_validate(json.loads(path.read_text()))

    def put(self, spec: ParserSpec) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / f"{spec.fingerprint}.json").write_text(
            json.dumps(spec.model_dump(), indent=2)
        )
