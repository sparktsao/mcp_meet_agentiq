import sys
import os
import json
import asyncio
import re
from pathlib import Path
from typing import List
from aiofiles import open as aio_open
from aiofiles.os import stat as aio_stat
from aiofiles.os import listdir as aio_listdir

# Maximum number of search results to return
SEARCH_LIMIT = 200

# Command-line argument parsing
if len(sys.argv) < 2:
    print("Usage: python mcp_server.py <vault-directory>", file=sys.stderr)
    sys.exit(1)


def normalize_path(p: str) -> str:
    return str(Path(p).resolve().as_posix()).lower()


def expand_home(filepath: str) -> str:
    return str(Path(filepath).expanduser().resolve())

vault_directories = [normalize_path(expand_home(sys.argv[1]))]

async def validate_path(requested_path: str) -> str:
    path_obj = Path(expand_home(requested_path)).resolve()
    normalized_requested = normalize_path(str(path_obj))

    if any(part.startswith(".") for part in path_obj.parts):
        raise ValueError("Access denied - hidden files/directories not allowed")

    is_allowed = any(normalized_requested.startswith(dir) for dir in vault_directories)
    if not is_allowed:
        raise ValueError(f"Access denied - path outside allowed directories: {path_obj}")

    try:
        real_path = normalize_path(await asyncio.to_thread(path_obj.resolve))
        if not any(real_path.startswith(dir) for dir in vault_directories):
            raise ValueError("Access denied - symlink target outside allowed directories")
        return str(path_obj)
    except:
        parent_dir = path_obj.parent
        real_parent_path = normalize_path(await asyncio.to_thread(parent_dir.resolve))
        if not any(real_parent_path.startswith(dir) for dir in vault_directories):
            raise ValueError("Access denied - parent directory outside allowed directories")
        return str(path_obj)


async def search_notes(query: str) -> List[str]:
    results = []

    async def search(base_path: str, current_path: str):
        try:
            entries = await aio_listdir(current_path)
            for entry in entries:
                full_path = Path(current_path) / entry
                try:
                    await validate_path(str(full_path))
                    matches = query.lower() in entry.lower()
                    try:
                        matches = matches or re.search(query.replace("*", ".*"), entry, re.IGNORECASE)
                    except:
                        pass
                    if full_path.suffix == ".md" and matches:
                        results.append(str(full_path.relative_to(base_path)))
                    if full_path.is_dir():
                        await search(base_path, str(full_path))
                except:
                    continue
        except:
            pass

    await asyncio.gather(*[search(dir, dir) for dir in vault_directories])
    return results[:SEARCH_LIMIT]


async def read_notes(paths: List[str]) -> str:
    results = []
    for file_path in paths:
        try:
            valid_path = await validate_path(os.path.join(vault_directories[0], file_path))
            async with aio_open(valid_path, "r", encoding="utf-8") as file:
                content = await file.read()
                results.append(f"{file_path}:\n{content}\n")
        except Exception as error:
            results.append(f"{file_path}: Error - {error}")
    return "\n---\n".join(results)


async def handle_request(request: str):
    try:
        data = json.loads(request)
        name = data.get("name")
        args = data.get("arguments", {})

        if name == "read_notes":
            return json.dumps({"content": [{"type": "text", "text": await read_notes(args.get("paths", []))}]})
        elif name == "search_notes":
            results = await search_notes(args.get("query", ""))
            return json.dumps({"content": [{"type": "text", "text": "\n".join(results) or "No matches found"}]})
        else:
            return json.dumps({"content": [{"type": "text", "text": f"Error: Unknown tool {name}"}], "isError": True})
    except Exception as e:
        return json.dumps({"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True})


async def run_server():
    print("MCP Python Server running on stdin/stdout", file=sys.stderr)
    print(f"Allowed directories: {vault_directories}", file=sys.stderr)
    while True:
        try:
            request = sys.stdin.readline().strip()
            if not request:
                await asyncio.sleep(0.1)
                continue
            response = await handle_request(request)
            sys.stdout.write(response + "\n")
            sys.stdout.flush()
        except Exception as e:
            print(f"Fatal error: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(run_server())
