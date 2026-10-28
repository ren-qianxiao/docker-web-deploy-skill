#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deploy.py — 通用 Docker 网站部署助手（仅依赖 Python 标准库）

适用于任何包含 docker-compose.yml / Dockerfile 的网站项目。

子命令：
    check                  体检：系统、Docker、Compose、WSL、虚拟化、端口、磁盘
    extract <zip>          安全解压 zip，并定位项目根目录
    find-project <dir>     查找项目根（优先 docker-compose.yml）
    inspect [project]      解析 compose：服务名、宿主机端口、镜像/构建目录
    verify --url URL       轮询网站首页与指定路径是否就绪

所有命令输出 JSON（UTF-8）。
"""

import argparse
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------- 基础工具

def _decode(raw: bytes) -> str:
    """Windows 的 wsl.exe 常输出 UTF-16，这里做自适应解码。"""
    if not raw:
        return ""
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    if raw.count(b"\x00") > len(raw) // 4:
        return raw.decode("utf-16-le", errors="replace")
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", errors="replace")


def run(cmd, timeout=20, cwd=None):
    try:
        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
        proc = subprocess.run(
            cmd, capture_output=True, timeout=timeout, cwd=cwd, **kwargs
        )
        return {
            "ok": proc.returncode == 0,
            "code": proc.returncode,
            "out": _decode(proc.stdout).strip(),
            "err": _decode(proc.stderr).strip(),
        }
    except FileNotFoundError:
        return {"ok": False, "code": None, "out": "", "err": "command not found"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "code": None, "out": "", "err": "timeout"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "code": None, "out": "", "err": str(exc)}


def find_docker():
    path = shutil.which("docker")
    if path:
        return path
    if os.name == "nt":
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/DockerDesktop/resources/bin/docker.exe",
            Path(r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"),
        ]
        for item in candidates:
            if item.is_file():
                return str(item)
    return None


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def port_owner(port):
    system = platform.system()
    if system == "Windows":
        res = run(["netstat", "-ano"], timeout=15)
        for line in res["out"].splitlines():
            if (":%d " % port) in line and "LISTENING" in line.upper():
                return line.strip()
    else:
        if shutil.which("lsof"):
            res = run(["lsof", "-nP", "-iTCP:%d" % port, "-sTCP:LISTEN"], timeout=10)
            if res["out"]:
                return res["out"].splitlines()[-1].strip()
    return ""


def is_admin():
    if os.name == "nt":
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:  # noqa: BLE001
            return None
    try:
        return os.geteuid() == 0
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------- check

def cmd_check(_args):
    system = platform.system()
    info = {
        "os": system,
        "os_release": platform.release(),
        "os_version": platform.version(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "is_admin": is_admin(),
    }

    docker = find_docker()
    info["docker_cli"] = docker
    if docker:
        ver = run([docker, "--version"], timeout=15)
        info["docker_version"] = ver["out"] or ver["err"]

        comp = run([docker, "compose", "version"], timeout=15)
        info["compose"] = {"ok": comp["ok"], "version": comp["out"] or comp["err"]}

        daemon = run([docker, "info", "--format", "{{.ServerVersion}}"], timeout=25)
        info["daemon"] = {
            "running": daemon["ok"],
            "server_version": daemon["out"] if daemon["ok"] else "",
            "error": "" if daemon["ok"] else (daemon["err"] or daemon["out"])[:400],
        }
        if daemon["ok"]:
            ps = run([docker, "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"], timeout=15)
            info["containers"] = ps["out"]
    else:
        info["docker_version"] = ""
        info["compose"] = {"ok": False, "version": ""}
        info["daemon"] = {"running": False, "server_version": "", "error": "docker CLI not found"}

    if system == "Windows":
        status = run(["wsl", "--status"], timeout=20)
        text = (status["out"] + " " + status["err"]).strip()
        listed = run(["wsl", "-l", "-v"], timeout=20)
        low = text.lower()
        info["wsl"] = {
            "available": not ("未安装" in text or "not installed" in low),
            "status": text[:500],
            "distros": (listed["out"] or listed["err"])[:800],
        }
        virt = run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Processor).VirtualizationFirmwareEnabled"],
            timeout=25,
        )
        info["virtualization"] = virt["out"].strip() or "unknown"
    elif system == "Linux":
        try:
            cpuinfo = Path("/proc/cpuinfo").read_text(errors="ignore")
            info["virtualization"] = ("vmx" in cpuinfo) or ("svm" in cpuinfo)
        except Exception:  # noqa: BLE001
            info["virtualization"] = "unknown"
    else:
        info["virtualization"] = "n/a"

    in_use = port_in_use(8080)
    info["port_8080"] = {"in_use": in_use, "owner": port_owner(8080) if in_use else ""}

    try:
        usage = shutil.disk_usage(str(Path.home()))
        info["disk_free_gb"] = round(usage.free / 1_000_000_000, 1)
    except Exception:  # noqa: BLE001
        info["disk_free_gb"] = None

    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0


# ---------------------------------------------------------------- 项目定位

def find_project(root: Path):
    """优先 docker-compose.yml；没有则退回 Dockerfile。"""
    for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        hits = [p.parent for p in root.rglob(name) if len(p.relative_to(root).parts) <= 4]
        if hits:
            hits.sort(key=lambda d: (d.name not in ("gpr-map-system",), len(d.parts), str(d)))
            return hits[0]
    hits = [p.parent for p in root.rglob("Dockerfile") if len(p.relative_to(root).parts) <= 3]
    if hits:
        hits.sort(key=lambda d: (len(d.parts), str(d)))
        return hits[0]
    return None


def unique_dir(path: Path) -> Path:
    if not path.exists():
        return path
    index = 2
    while True:
        alt = path.with_name("%s-%d" % (path.name, index))
        if not alt.exists():
            return alt
        index += 1


def cmd_extract(args):
    zpath = Path(args.zip).expanduser().resolve()
    if not zpath.is_file():
        print(json.dumps({"ok": False, "error": "zip not found: %s" % zpath}, ensure_ascii=False))
        return 2

    dest = Path(args.dest).expanduser().resolve() if args.dest else zpath.parent / (zpath.stem + "-extracted")
    dest = unique_dir(dest)
    dest.mkdir(parents=True, exist_ok=False)

    count = 0
    skipped = []
    try:
        with zipfile.ZipFile(zpath) as zf:
            for item in zf.infolist():
                name = item.filename.replace("\\", "/")
                if item.is_dir() or name.endswith("/"):
                    continue
                parts = [p for p in name.split("/") if p not in ("", ".", "..")]
                if not parts:
                    continue
                target = dest.joinpath(*parts)
                try:
                    target.resolve().relative_to(dest.resolve())
                except ValueError:
                    skipped.append(item.filename)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(item) as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)
                count += 1
    except zipfile.BadZipFile:
        print(json.dumps({"ok": False, "error": "not a valid zip file: %s" % zpath}, ensure_ascii=False))
        return 2

    project = find_project(dest)
    result = {
        "ok": project is not None,
        "zip": str(zpath),
        "extracted_to": str(dest),
        "files": count,
        "skipped_unsafe": skipped,
        "project_root": str(project) if project else None,
        "has_compose": bool(project and any((project / n).is_file() for n in
                                           ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"))),
        "has_dockerfile": bool(project and (project / "Dockerfile").is_file()),
    }
    if not project:
        result["error"] = "解压成功，但没有找到 docker-compose.yml 或 Dockerfile"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if project else 1


def cmd_find_project(args):
    root = Path(args.path).expanduser().resolve()
    project = find_project(root) if root.is_dir() else None
    print(json.dumps({"ok": bool(project), "project_root": str(project) if project else None},
                     ensure_ascii=False, indent=2))
    return 0 if project else 1


# ---------------------------------------------------------------- inspect

def _parse_ports_regex(text):
    """兜底解析 compose 文本中的端口映射。"""
    pairs = []
    for match in re.finditer(r"-\s*[\"']?(\d{2,5}):(\d{2,5})[\"']?", text):
        host, container = match.group(1), match.group(2)
        pairs.append({"published": int(host), "target": int(container), "protocol": "tcp"})
    return pairs


def cmd_inspect(args):
    project = Path(args.project).expanduser().resolve() if args.project else Path.cwd()
    compose_files = [p for p in project.glob("docker-compose.y*ml")] + \
                    [p for p in project.glob("compose.y*ml")]
    compose = compose_files[0] if compose_files else None

    result = {
        "ok": compose is not None,
        "project_root": str(project),
        "compose_file": str(compose) if compose else None,
        "services": [],
        "host_port": None,
        "source": None,
    }

    if not compose:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    docker = find_docker()
    if docker:
        cfg = run([docker, "compose", "config", "--format", "json"], cwd=project, timeout=40)
        if cfg["ok"] and cfg["out"]:
            try:
                data = json.loads(cfg["out"])
                for name, svc in (data.get("services") or {}).items():
                    ports = []
                    for item in svc.get("ports") or []:
                        if isinstance(item, dict):
                            ports.append({
                                "published": item.get("published"),
                                "target": item.get("target"),
                                "protocol": item.get("protocol", "tcp"),
                            })
                    result["services"].append({
                        "name": name,
                        "image": svc.get("image"),
                        "build": bool(svc.get("build")),
                        "ports": ports,
                    })
                result["source"] = "docker compose config"
            except Exception:  # noqa: BLE001
                pass

    if not result["services"]:
        text = compose.read_text(encoding="utf-8", errors="replace")
        ports = _parse_ports_regex(text)
        names = re.findall(r"^  ([A-Za-z0-9_.-]+):\s*$", text, re.M)
        result["services"] = [{"name": n, "image": None, "build": None, "ports": ports}
                              for n in names[:10]] or [{"name": "app", "image": None, "build": None, "ports": ports}]
        result["source"] = "regex"

    for svc in result["services"]:
        for item in svc.get("ports") or []:
            if item.get("published"):
                result["host_port"] = int(item["published"])
                break
        if result["host_port"]:
            break

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


# ---------------------------------------------------------------- verify

def fetch(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read(300000)
            return {
                "ok": 200 <= resp.status < 400,
                "status": resp.status,
                "content_type": resp.headers.get("Content-Type", ""),
                "bytes": len(body),
                "body": body,
            }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "status": None, "error": str(exc), "body": b""}


def cmd_verify(args):
    base = args.url.rstrip("/")
    deadline = time.time() + args.timeout
    index = None
    while time.time() < deadline:
        index = fetch(base + "/")
        if index["ok"] and index["bytes"] > 0:
            break
        time.sleep(2)

    endpoints = {}
    if index and index["ok"]:
        for path in args.path or []:
            if not path.startswith("/"):
                path = "/" + path
            res = fetch(base + path, timeout=10)
            item = {
                "ok": res["ok"],
                "status": res["status"],
                "bytes": res.get("bytes", 0),
                "content_type": res.get("content_type", ""),
            }
            if res["ok"] and (path.endswith(".json") or "json" in item["content_type"]):
                try:
                    payload = json.loads(res["body"].decode("utf-8"))
                    if isinstance(payload, dict):
                        item["json_keys"] = list(payload.keys())[:10]
                except Exception as exc:  # noqa: BLE001
                    item["parse_error"] = str(exc)
            endpoints[path] = item

    ok = bool(index and index["ok"] and all(v["ok"] for v in endpoints.values()))
    print(json.dumps({
        "ok": ok,
        "url": base,
        "index": {
            "ok": bool(index and index["ok"]),
            "status": index.get("status") if index else None,
            "bytes": index.get("bytes", 0) if index else 0,
            "error": index.get("error", "") if index else "timeout",
        },
        "endpoints": endpoints,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description="Generic Docker website deployment helper")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="环境体检")

    p_extract = sub.add_parser("extract", help="安全解压 zip 并定位项目根目录")
    p_extract.add_argument("zip")
    p_extract.add_argument("--dest", default=None)

    p_find = sub.add_parser("find-project", help="查找项目根目录")
    p_find.add_argument("path")

    p_inspect = sub.add_parser("inspect", help="解析 compose 的服务与端口")
    p_inspect.add_argument("project", nargs="?", default=None)

    p_verify = sub.add_parser("verify", help="验证网站是否就绪")
    p_verify.add_argument("--url", default="http://localhost:8080")
    p_verify.add_argument("--timeout", type=int, default=90)
    p_verify.add_argument("--path", action="append", default=[],
                          help="额外验证路径，可重复，如 --path /api/health --path /data/x.json")

    args = parser.parse_args()
    handlers = {
        "check": cmd_check,
        "extract": cmd_extract,
        "find-project": cmd_find_project,
        "inspect": cmd_inspect,
        "verify": cmd_verify,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
