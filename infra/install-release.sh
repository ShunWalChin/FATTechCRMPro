#!/usr/bin/env bash
# Install a packaged release into /opt/fattechcrmpro and hand over to deploy.sh.
#
# Extraction alone is not installation. `tar -x` adds and overwrites but never removes, so a file
# deleted in a release used to linger in production forever. That stayed invisible until a release
# first removed routes and the leftovers collided with their replacements at build time. This prunes
# what the new inventory no longer lists, so the running tree is the released tree and nothing else.
#
# Usage: install-release.sh <archive> <sha256> <release-tag> <commit>
set -euo pipefail
archive=$1; digest=$2; tag=$3; commit=$4
root=${FATTECH_ROOT:-/opt/fattechcrmpro}
env_file=${FATTECH_ENV_FILE:-/etc/fattechcrmpro.env}

printf '%s  %s\n' "$digest" "$archive" | sha256sum --check
bash "$root/infra/backup.sh"
tar -xzf "$archive" -C "$root"

python3 - "$root" <<'PY'
import csv, hashlib, pathlib, sys
root = pathlib.Path(sys.argv[1])
rows = list(csv.DictReader((root / "docs/FILE_INVENTORY.csv").open()))
released = {row["path"] for row in rows}
# Files the release legitimately does not track: the inventory cannot list itself, the marker this
# script writes, and build caches the image produces.
keep = {"docs/FILE_INVENTORY.csv", "RELEASE", "apps/web/tsconfig.tsbuildinfo"}
removed = []
for path in sorted(root.rglob("*")):
    if not path.is_file():
        continue
    relative = path.relative_to(root).as_posix()
    if relative in released or relative in keep or relative.startswith((".git/", "node_modules/")):
        continue
    path.unlink()
    removed.append(relative)
print(f"Removidos {len(removed)} arquivos que esta versao nao contem mais: {removed or 'nenhum'}")

bad = []
for row in rows:
    data = (root / row["path"]).read_bytes()
    if len(data) != int(row["bytes"]) or hashlib.sha256(data).hexdigest() != row["sha256"]:
        bad.append(row["path"])
print(f"Conferidos {len(rows)} arquivos versionados; divergentes: {bad or 'nenhum'}")
assert not bad
PY

python3 - "$env_file" "$tag" <<'PY'
import pathlib, sys
path, tag = pathlib.Path(sys.argv[1]), sys.argv[2]
lines = path.read_text().splitlines()
assert sum(line.startswith("RELEASE_TAG=") for line in lines) == 1, "RELEASE_TAG ausente ou duplicado"
path.write_text("\n".join(f"RELEASE_TAG={tag}" if line.startswith("RELEASE_TAG=") else line
                          for line in lines) + "\n")
print(f"RELEASE_TAG={tag}")
PY

bash "$root/infra/deploy.sh"
printf '%s\n' "$commit" > "$root/RELEASE"
docker compose --env-file "$env_file" -f "$root/infra/compose.yml" ps \
  --format '{{.Name}} {{.Image}} {{.Status}}'
