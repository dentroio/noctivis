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
        description="Static ELF classification, function inventory, and one decompilation. Samples are not executed.",
        tools=("binary.inspect", "binary.list_functions", "binary.decompile"),
    )
}
