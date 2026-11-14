from dataclasses import dataclass

@dataclass(frozen=True)
class Capability:
    id: str
    description: str
    tools: tuple[str, ...]
    allows_execution: bool = False

CAPABILITIES = {
    "binary-intelligence": Capability(
        id="binary-intelligence",
        description="Static binary classification and investigation",
        tools=("binary.inspect", "binary.list_functions", "binary.decompile"),
    )
}
