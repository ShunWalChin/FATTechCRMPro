"""Reproduce the explicitly requested engineering tools without mixing runtime deps."""
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
is_windows = __import__("os").name == "nt"
npm = "npm.cmd" if is_windows else "npm"
commands = [
    [npm, "install", "--prefix", ".local/tooling", "--save-exact", "ruflo@3.41.2"],
    ["uv", "tool", "install", "graphifyy==0.9.57", "--python", "3.12"],
    ["graphify", "install", "--project", "--platform", "codex"],
    ["node", "scripts/ruflo.mjs", "init", "--codex", "--full", "--all-agents", "--no-global", "--no-signup", "--no-skills-sh"],
]
for command in commands:
    subprocess.run(command, cwd=root, check=True)
print("Ponytail: codex plugin marketplace add DietrichGebert/ponytail; codex plugin add ponytail@ponytail")
