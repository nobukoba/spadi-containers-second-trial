#!/usr/bin/env python3
"""Exercise runtime orchestration with mock hardware, Valkey, and tmux.

Run on Linux/WSL2: python3 scripts/tests/test-nestdaq-recipes.py
This checks helper contracts and lifecycle order; it is not a hardware test.
"""
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile


def mock(tool, args):
    path = Path(os.environ["MOCK_STATE"])
    state = json.loads(path.read_text())
    state["calls"].append([tool, *args])
    result, code = "", 0
    if tool == "tmux":
        args = args[2:]  # -L socket
        op = args[0]
        if op == "has-session":
            code = 0 if state["session"] else 1
        elif op == "new-session":
            state["session"] = True
        elif op == "kill-session":
            state["session"] = False
        elif op == "new-window" and "start-device.sh" in args[-1]:
            tokens = shlex.split(args[-1])
            service = tokens[tokens.index("start-device.sh") + 1]
            # Real NestDAQ allocates the index automatically per service.
            index = sum(k.startswith(service + ":") for k in state["states"])
            state["states"][f"{service}:{service}-{index}"] = "IDLE"
    elif tool == "write_register":
        if os.environ.get("MOCK_MASK_ERROR"):
            result = "#E: RBCP timeout"
    elif tool == "read_register":
        result = "#D: Read register: 0 (0x" + ("ffffffbf" if args[1] == "10300000" else "ffffffff") + ")"
    elif tool == "valkey-cli":
        commands = {"get", "set", "hset", "keys", "del", "flushdb", "ping", "COMMAND", "publish"}
        offset = next(i for i, arg in enumerate(args) if arg in commands)
        op, *values = args[offset:]
        if op == "ping":
            result = "PONG"
        elif op == "COMMAND":
            result = "ts.add"
        elif op == "get":
            key = values[0]
            if key.endswith(":fair-mq-state"):
                result = state["states"].get(key.removeprefix("daq_service:").removesuffix(":fair-mq-state"), "")
            else:
                result = str(state["values"].get(key, ""))
        elif op == "set":
            state["values"][values[0]] = values[1]
        elif op == "hset":
            state["parameters"][values[0]] = dict(zip(values[1::2], values[2::2]))
        elif op == "keys" and values[0].endswith("fair-mq-state"):
            result = "\n".join("daq_service:" + k + ":fair-mq-state" for k in state["states"])
        elif op == "publish":
            assert values[0] == "daqctl"
            message = json.loads(values[1])
            assert message["command"] == "change_state"
            assert message["instances"] == ["all"]
            transition = message["value"]
            target = {"CONNECT": "DEVICE READY", "INIT TASK": "READY", "RUN": "RUNNING", "STOP": "READY", "quit": "EXITING"}[transition]
            # Match the names in pinned FairMQ 1.4.55 States.cxx.
            for service in message["services"]:
                key = f"{service}:{service}-0"
                state["states"][key] = "ERROR" if service == os.environ.get("MOCK_DEVICE_ERROR") else target
                if service == "FileSink" and transition == "RUN":
                    prefix = state["parameters"]["parameters:FileSink-0"]["prefix"]
                    run = int(state["values"]["run_info:run_number"])
                    state["output"] = str(Path(prefix) / f"run{run:06d}.dat")
                    Path(state["output"]).write_text("mock FileSink header\n")
                elif service == "FileSink" and transition == "STOP" and state.get("output"):
                    with open(state["output"], "a") as f:
                        f.write("mock FileSink trailer\n")
    path.write_text(json.dumps(state))
    if result:
        print(result)
    return code


def main():
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="spadi recipes ") as temporary:
        tmp = Path(temporary)
        base = tmp / "image"
        (base / "scripts").mkdir(parents=True)
        for component in ("fee", "nestdaq"):
            shutil.copytree(root / "scripts" / component, base / "scripts" / component)
        # Container COPY/chmod makes the deployed shell scripts executable.
        for script in base.rglob("*.sh"):
            script.chmod(0o755)
            subprocess.run(["bash", "-n", str(script)], check=True)
        local = tmp / "workspace" / "spadi"
        commands = tmp / "bin"
        commands.mkdir()
        env = dict(os.environ, SPADI_ROOT=str(base), SPADI_LOCAL=str(local), MOCK_STATE=str(tmp / "state.json"))
        env["PATH"] = str(commands) + ":" + str(local / "scripts/nestdaq/common") + ":" + env["PATH"]
        for tool in ("tmux", "valkey-cli", "write_register", "read_register", "AmQStrTdcSampler", "STFBuilder", "TimeFrameBuilder", "FileSink", "daq-webctl"):
            command = commands / tool
            command.write_text("#!/bin/bash\nexec python3 " + shlex.quote(str(Path(__file__).resolve())) + " --mock " + shlex.quote(tool) + ' "$@"\n')
            command.chmod(0o755)
        def reset():
            Path(env["MOCK_STATE"]).write_text(json.dumps({"calls": [], "states": {}, "values": {}, "parameters": {}, "session": False}))
        def read():
            return json.loads(Path(env["MOCK_STATE"]).read_text())
        def run(script, *args, expected=0, extra=None):
            p = subprocess.run(["bash", str(script), *map(str, args)], env=env | (extra or {}), text=True, capture_output=True, timeout=45)
            assert (p.returncode == 0) == (expected == 0), p.stdout + p.stderr
            return p
        prepare = root / "scripts/runtime/spadi-prepare-runtime.sh"
        reset()
        run(prepare)
        recipe = local / "scripts/nestdaq/amaneq-lrtdc-1ch"
        config = recipe / "config.sh"
        # An IP override must reach the FEE tools and hardware sampler together.
        config.write_text(config.read_text().replace("192.168.10.16", "192.168.10.17").replace("CONTROL_TIMEOUT=30", "CONTROL_TIMEOUT=1"))
        before = config.read_bytes()
        run(prepare)
        assert config.read_bytes() == before
        assert not (local / "src").exists()
        run(recipe / "run-start.sh")
        s = read()
        assert s["parameters"]["parameters:AmQStrTdcSampler-0"] == {"msiTcpIp": "192.168.10.17", "TdcType": "1", "enable-uds": "false"}
        assert s["parameters"]["parameters:FileSink-0"]["openmode"] == "create"
        writes = [c[1:] for c in s["calls"] if c[0] == "write_register"]
        assert len(writes) == 4 and all(c[0] == "192.168.10.17" for c in writes)
        publications = [json.loads(c[-1]) for c in s["calls"] if "publish" in c]
        starts = [p["services"][0] for p in publications if p["value"] == "RUN"]
        assert starts == ["FileSink", "TimeFrameBuilder", "STFBuilder", "AmQStrTdcSampler"]
        assert all(v == "RUNNING" for v in s["states"].values())
        assert s["parameters"]["daq_service:topology:endpoint:FileSink:dqm"]["type"] == "pub"
        assert "RUNNING" in run(recipe / "run-status.sh").stdout
        run(recipe / "fee-setup.sh", expected=1)
        run(recipe / "run-stop.sh")
        s = read()
        stops = [json.loads(c[-1])["services"][0] for c in s["calls"] if "publish" in c and json.loads(c[-1])["value"] == "STOP"]
        assert stops == ["AmQStrTdcSampler", "STFBuilder", "TimeFrameBuilder", "FileSink"]
        assert not s["session"] and "trailer" in Path(s["output"]).read_text()
        reset()
        run(recipe / "run-start.sh", expected=1)  # existing file refused
        assert not any(c[0] in ("valkey-cli", "write_register", "read_register") for c in read()["calls"])
        Path(s["output"]).unlink()
        reset()
        run(recipe / "run-start.sh", expected=1, extra={"MOCK_MASK_ERROR": "1"})
        assert not any(c[0] == "valkey-cli" for c in read()["calls"])
        reset()
        run(recipe / "run-start.sh", expected=1, extra={"MOCK_DEVICE_ERROR": "STFBuilder"})
        assert read()["session"]  # error retains logs instead of claiming acquisition
        reset()
        replay = local / "scripts/nestdaq/raris-ac-lgad/config.sh"
        common = local / "scripts/nestdaq/common"
        run(common / "apply-parameters.sh", replay)
        run(common / "apply-topology.sh", replay)
        run(common / "tmux-start.sh", replay)
        s = read()
        assert all(f"parameters:STFBFilePlayer-{i}" in s["parameters"] for i in range(3))
        assert "parameters:AmQStrTdcSampler-0" not in s["parameters"]
        assert "daq_service:topology:link:STFBFilePlayer:out,TimeFrameBuilder:in" in s["values"]
        assert not any("FileSink" in key for key in s["states"])
        # Verify moved documentation links, including all four language pages.
        for page in [root / "README.md", root / "README.ja.md", *list((root / "docs").glob("*-guide*.md"))]:
            for target in re.findall(r"\]\(([^)]+)\)", page.read_text()):
                if not target.startswith(("http", "#")):
                    assert (page.parent / target.split("#")[0]).exists(), (page, target)
        print("PASS: live topology, parameter names, IP override, start/stop ordering, output protection, error retention, non-overwriting preparation, replay compatibility, guide links")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--mock":
        sys.exit(mock(sys.argv[2], sys.argv[3:]))
    main()
