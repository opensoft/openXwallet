"""Isolated controlled worker: load the selected config, report ready, await exit."""
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    json.load(stream)
print("ready", flush=True)
for line in sys.stdin:
    if line.strip() == "exit":
        break
