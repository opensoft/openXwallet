"""Record and independently check every new credential helper generation."""
import json
from pathlib import Path
import subprocess
import pytest

@pytest.fixture(autouse=True)
def child_generations(tmp_path,monkeypatch):
    original=subprocess.Popen;records=[]
    class Tracked(original):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            command=self.args
            if isinstance(command,(list,tuple)) and any(str(x).endswith(("/hosted/_credential_io.py","/credential_worker.py","/readback_worker.py","/fixture_role.py","/hosted/_launch_exec.py","/stage_crash_role.py")) for x in command):
                fields=(Path("/proc")/str(self.pid)/"stat").read_text().rsplit(")",1)[1].split()
                records.append({"pid":self.pid,"start_time":fields[19]})
    monkeypatch.setattr(subprocess,"Popen",Tracked)
    try:yield
    finally:
        alive=[]
        for item in records:
            try:matches=(Path("/proc")/str(item["pid"])/"stat").read_text().rsplit(")",1)[1].split()[19]==item["start_time"]
            except FileNotFoundError:matches=False
            if matches:alive.append(item)
        (tmp_path/"credential-generations.json").write_text(json.dumps({"generations":records,"matching_alive":alive}))
        assert not alive,"credential helper generation survived fixture teardown"
