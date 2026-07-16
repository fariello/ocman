#!/usr/bin/env python3
"""
bench_env.py - capture the machine/environment for a performance benchmark run, diagnose
known good/bad configurations, detect HPC schedulers, and optionally warm caches.

Performance numbers are meaningless without the context they were measured in. This tool
gathers that context DEEPLY and HONESTLY before any benchmark runs: hostname, OS/kernel,
CPU model/cores/flags, RAM breakdown (total/free/available/cached/used), swap, load
average, GPU(s), container/VM hints, Python version, and the filesystem/storage the work
will run on. It then DIAGNOSES the environment against a set of known performance
pitfalls (working set on NFS, CPU governor set to powersave, heavy swap pressure, thermal
throttling, an over-loaded host, tmpfs vs. spinning disk) and prints copy-pasteable
suggested remedies. It also DETECTS HPC schedulers (Slurm/PBS/SGE/LSF) and reports how to
submit, and can run a bounded disk-speed probe and a cache warm-up over given paths.

It is dependency-free (Python stdlib only), matching scan_secrets.py and run_checks.py,
and portable: capture is rich on Linux (via /proc, /sys, and common CLIs) and degrades
gracefully elsewhere. It NEVER fabricates a value it could not read - unknown fields are
reported as null / "unknown" with a note.

SAFETY:
  - This tool is READ-ONLY with respect to system state. It reads /proc, /sys, and runs
    read-only informational commands (uname, lsblk, nvidia-smi, sysctl -n, getconf). It
    NEVER changes governors, mounts, swap, or any system setting; it only SUGGESTS such
    changes as text for the user to run.
  - The optional --disk-probe and --warm steps write/read ONLY inside a caller-named
    scratch directory (default: the OS temp dir) or read the caller-named input paths.
    They are bounded in size and are skipped unless explicitly requested.
  - No network calls are made by this tool.

Usage:
    python3 bench_env.py [--repo PATH] [--format json|csv|text] [--out FILE]
                         [--paths P[,P...]] [--disk-probe] [--probe-mb N]
                         [--warm P[,P...]] [--scrub] [--version]

Exit codes: 0 = capture completed (diagnostics may still WARN; a warning is not an error);
            2 = usage/environment error.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

PROBE_DEFAULT_MB = 64
LOG_NOTE_LIMIT = 2000


# ---- small helpers ---------------------------------------------------------


def _run(argv: list[str], timeout: int = 15) -> str:
    """Run a read-only informational command; return stdout stripped, or "" on any failure.

    Never raises: a missing tool or a non-zero exit yields "" so capture is best-effort.
    """

    try:
        p = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return (p.stdout or "").strip()


def _read(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _which(name: str) -> bool:
    return shutil.which(name) is not None


def _int_or_none(text: str):
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


# ---- data model ------------------------------------------------------------


@dataclass
class Diagnostic:
    """A flagged environment condition with a severity and a suggested remedy."""

    id: str
    severity: str  # info | warn | high
    area: str  # storage | cpu | memory | thermal | load | gpu | general
    finding: str
    remedy: str


@dataclass
class DiskProbe:
    path: str
    write_mb_s: float | None = None
    read_mb_s: float | None = None
    note: str = ""


@dataclass
class EnvReport:
    schema: str = "bench-env/1"
    captured_at_utc: str = ""
    tool_version: str = ""
    # identity
    hostname: str = ""
    fqdn: str = ""
    user: str = ""
    # os / runtime
    os: str = ""
    os_release: str = ""
    kernel: str = ""
    arch: str = ""
    python_version: str = ""
    container_hint: str = ""
    virtualization_hint: str = ""
    # cpu
    cpu_model: str = ""
    cpu_logical: int | None = None
    cpu_physical: int | None = None
    cpu_governor: str = ""
    cpu_max_mhz: float | None = None
    cpu_flags_sample: list[str] = field(default_factory=list)
    numa_nodes: int | None = None
    # memory (kB where from /proc/meminfo, else best-effort)
    mem_total_kb: int | None = None
    mem_free_kb: int | None = None
    mem_available_kb: int | None = None
    mem_cached_kb: int | None = None
    mem_used_kb: int | None = None
    swap_total_kb: int | None = None
    swap_free_kb: int | None = None
    # load
    load_avg: list[float] = field(default_factory=list)
    uptime_s: int | None = None
    # gpu
    gpus: list[dict] = field(default_factory=list)
    # storage: filesystem type for each path of interest
    paths: list[dict] = field(default_factory=list)
    disk_probe: DiskProbe | None = None
    # hpc
    hpc: dict = field(default_factory=dict)
    # honesty
    unread: list[str] = field(default_factory=list)  # fields we could not read
    diagnostics: list[Diagnostic] = field(default_factory=list)


# ---- capture ---------------------------------------------------------------


def _framework_version() -> str:
    """Return the agent-workflows framework version this tool ships with.

    The VERSION file lives at the framework root (.agents/workflows/VERSION); this script
    is at .agents/workflows/benchmark/tools/bench_env.py, so it is three directories up.
    Returns "unknown" if the file is absent (e.g. run standalone outside the framework).
    """

    version_path = Path(__file__).resolve().parent.parent.parent / "VERSION"
    try:
        value = version_path.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"
    return value or "unknown"


def capture_identity(rep: EnvReport) -> None:
    rep.hostname = socket.gethostname() or "unknown"
    try:
        rep.fqdn = socket.getfqdn() or ""
    except OSError:
        rep.fqdn = ""
    try:
        rep.user = getpass.getuser()
    except Exception:  # getuser can raise if no known user; best-effort
        rep.user = ""


def capture_os(rep: EnvReport) -> None:
    rep.os = platform.system() or "unknown"
    rep.kernel = platform.release() or ""
    rep.arch = platform.machine() or ""
    rep.python_version = platform.python_version()
    # Distro / product name
    if rep.os == "Linux":
        osr = _read("/etc/os-release")
        m = re.search(r'^PRETTY_NAME="?(.*?)"?$', osr, re.MULTILINE)
        rep.os_release = m.group(1) if m else ""
        # container hints
        if Path("/.dockerenv").exists():
            rep.container_hint = "docker"
        elif "docker" in _read("/proc/1/cgroup") or "containerd" in _read(
            "/proc/1/cgroup"
        ):
            rep.container_hint = "container"
        elif os.environ.get("SINGULARITY_NAME") or os.environ.get("APPTAINER_NAME"):
            rep.container_hint = "singularity/apptainer"
        # virtualization hint (read-only)
        vt = _run(["systemd-detect-virt"]) if _which("systemd-detect-virt") else ""
        rep.virtualization_hint = vt if vt and vt != "none" else ""
    elif rep.os == "Darwin":
        rep.os_release = _run(["sw_vers", "-productVersion"])
    else:
        rep.os_release = platform.platform()


def capture_cpu(rep: EnvReport) -> None:
    rep.cpu_logical = os.cpu_count()
    if rep.os == "Linux":
        cpuinfo = _read("/proc/cpuinfo")
        m = re.search(r"^model name\s*:\s*(.+)$", cpuinfo, re.MULTILINE)
        rep.cpu_model = m.group(1).strip() if m else ""
        # physical cores: distinct (physical id, core id) pairs
        phys = set(re.findall(r"^physical id\s*:\s*(\d+)", cpuinfo, re.MULTILINE))
        cores = re.findall(r"^cpu cores\s*:\s*(\d+)", cpuinfo, re.MULTILINE)
        cores_per = _int_or_none(cores[0]) if cores else None
        if phys and cores_per:
            rep.cpu_physical = len(phys) * cores_per
        fm = re.search(r"^flags\s*:\s*(.+)$", cpuinfo, re.MULTILINE)
        if fm:
            interesting = {"avx", "avx2", "avx512f", "sse4_2", "fma", "aes", "sve"}
            rep.cpu_flags_sample = sorted(set(fm.group(1).split()) & interesting)
        gov = _read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
        rep.cpu_governor = gov
        mhz = _read("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
        v = _int_or_none(mhz)
        rep.cpu_max_mhz = round(v / 1000.0, 1) if v else None
        nodes = (
            [p for p in Path("/sys/devices/system/node").glob("node*")]
            if Path("/sys/devices/system/node").exists()
            else []
        )
        rep.numa_nodes = len(nodes) or None
    elif rep.os == "Darwin":
        rep.cpu_model = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
        rep.cpu_physical = _int_or_none(_run(["sysctl", "-n", "hw.physicalcpu"]))
    if not rep.cpu_model:
        rep.cpu_model = platform.processor() or "unknown"
        rep.unread.append("cpu_model")


def capture_memory(rep: EnvReport) -> None:
    if rep.os == "Linux":
        mi = _read("/proc/meminfo")

        def kb(key: str):
            m = re.search(rf"^{re.escape(key)}:\s*(\d+)\s*kB", mi, re.MULTILINE)
            return _int_or_none(m.group(1)) if m else None

        rep.mem_total_kb = kb("MemTotal")
        rep.mem_free_kb = kb("MemFree")
        rep.mem_available_kb = kb("MemAvailable")
        rep.mem_cached_kb = kb("Cached")
        rep.swap_total_kb = kb("SwapTotal")
        rep.swap_free_kb = kb("SwapFree")
        if rep.mem_total_kb is not None and rep.mem_available_kb is not None:
            rep.mem_used_kb = rep.mem_total_kb - rep.mem_available_kb
    elif rep.os == "Darwin":
        total = _int_or_none(_run(["sysctl", "-n", "hw.memsize"]))
        rep.mem_total_kb = total // 1024 if total else None
        rep.unread.append("mem_free/available/cached (macOS: use vm_stat manually)")
    else:
        rep.unread.append("memory (unsupported OS for /proc/meminfo)")


def capture_load(rep: EnvReport) -> None:
    try:
        rep.load_avg = [round(x, 2) for x in os.getloadavg()]
    except (OSError, AttributeError):
        rep.unread.append("load_avg")
    if rep.os == "Linux":
        up = _read("/proc/uptime").split()
        if up:
            rep.uptime_s = _int_or_none(up[0].split(".")[0])


def capture_gpu(rep: EnvReport) -> None:
    if _which("nvidia-smi"):
        out = _run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version",
                "--format=csv,noheader,nounits",
            ]
        )
        for line in out.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                rep.gpus.append(
                    {
                        "vendor": "nvidia",
                        "name": parts[0],
                        "mem_total_mb": _int_or_none(parts[1]),
                        "mem_used_mb": _int_or_none(parts[2]),
                        "util_pct": _int_or_none(parts[3]),
                        "driver": parts[4],
                    }
                )
    elif _which("rocm-smi"):
        rep.gpus.append(
            {
                "vendor": "amd",
                "name": "rocm device(s) present",
                "note": "parse rocm-smi manually for detail",
            }
        )
    # No GPU tool present => empty list (honest: absence is not "no GPU", it is "not detected")


def _fs_type_for(path: Path) -> tuple[str, str]:
    """Return (fs_type, source_device) for the filesystem containing path (Linux best-effort)."""

    try:
        resolved = str(path.resolve())
    except OSError:
        resolved = str(path)
    # Prefer findmnt (accurate, handles bind/overlay); fall back to /proc/mounts longest-prefix.
    if _which("findmnt"):
        out = _run(["findmnt", "-n", "-o", "FSTYPE,SOURCE", "--target", resolved])
        if out:
            parts = out.split()
            fstype = parts[0] if parts else ""
            source = parts[1] if len(parts) > 1 else ""
            return fstype, source
    mounts = _read("/proc/mounts")
    best = ("", "", -1)
    for line in mounts.splitlines():
        cols = line.split()
        if len(cols) >= 3:
            dev, mnt, fstype = cols[0], cols[1], cols[2]
            if resolved == mnt or resolved.startswith(mnt.rstrip("/") + "/"):
                if len(mnt) > best[2]:
                    best = (fstype, dev, len(mnt))
    return (best[0], best[1])


# Filesystem types considered network / slow for a working set.
NETWORK_FS = {
    "nfs",
    "nfs4",
    "cifs",
    "smb",
    "smbfs",
    "fuse.sshfs",
    "lustre",
    "gpfs",
    "beegfs",
    "glusterfs",
    "ceph",
    "afs",
    "9p",
}
FAST_FS = {"tmpfs", "ramfs"}


def capture_paths(rep: EnvReport, paths: list[Path]) -> None:
    for p in paths:
        fstype, source = _fs_type_for(p)
        entry = {
            "path": str(p),
            "exists": p.exists(),
            "fs_type": fstype or "unknown",
            "source": source,
        }
        # free space
        try:
            usage = shutil.disk_usage(p if p.exists() else p.anchor or ".")
            entry["free_gb"] = round(usage.free / 1e9, 1)
            entry["total_gb"] = round(usage.total / 1e9, 1)
        except OSError:
            entry["free_gb"] = None
        rep.paths.append(entry)


def capture_hpc(rep: EnvReport) -> None:
    schedulers = []
    detected = {}
    checks = [
        ("slurm", "sbatch", ["squeue", "sinfo", "scontrol"]),
        ("pbs/torque", "qsub", ["qstat"]),
        (
            "sge",
            "qsub",
            ["qstat", "qconf"],
        ),  # note: qsub shared with pbs; disambiguate below
        ("lsf", "bsub", ["bjobs", "bqueues"]),
    ]
    for name, submit, _friends in checks:
        if _which(submit):
            schedulers.append(name)
            detected[name] = shutil.which(submit)
    # Slurm env vars are the strongest signal we are ON a compute/login node of a cluster
    inside_alloc = bool(
        os.environ.get("SLURM_JOB_ID")
        or os.environ.get("PBS_JOBID")
        or os.environ.get("LSB_JOBID")
    )
    # Disambiguate slurm as the primary if present
    primary = (
        "slurm" if "slurm" in schedulers else (schedulers[0] if schedulers else "")
    )
    rep.hpc = {
        "scheduler_detected": bool(schedulers),
        "schedulers": sorted(set(schedulers)),
        "primary": primary,
        "submit_paths": detected,
        "inside_allocation": inside_alloc,
        "slurm_partitions_hint": _run(["sinfo", "-h", "-o", "%P"]).split()
        if _which("sinfo")
        else [],
    }


# ---- disk probe / warm-up --------------------------------------------------


def disk_probe(scratch: Path, size_mb: int) -> DiskProbe:
    """Bounded sequential write-then-read probe inside `scratch`. Read-only w.r.t. system."""

    dp = DiskProbe(path=str(scratch))
    try:
        scratch.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        dp.note = f"could not create scratch dir: {e}"
        return dp
    payload = os.urandom(1024 * 1024)  # 1 MiB block
    fd_path = scratch / f".bench_probe_{os.getpid()}.tmp"
    try:
        # write
        t0 = time.perf_counter()
        with open(fd_path, "wb") as f:
            for _ in range(size_mb):
                f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        wt = time.perf_counter() - t0
        dp.write_mb_s = round(size_mb / wt, 1) if wt > 0 else None
        # drop this file from page cache best-effort not attempted (needs root); read anyway
        t0 = time.perf_counter()
        with open(fd_path, "rb") as f:
            while f.read(1024 * 1024):
                pass
        rt = time.perf_counter() - t0
        dp.read_mb_s = round(size_mb / rt, 1) if rt > 0 else None
        dp.note = "sequential; read may be cache-warm (no root to drop caches)"
    except OSError as e:
        dp.note = f"probe failed: {e}"
    finally:
        try:
            fd_path.unlink()
        except OSError:
            pass
    return dp


def warm_paths(paths: list[Path]) -> list[str]:
    """Best-effort cache warm-up: sequentially read the given files/dirs so a subsequent
    benchmark does not pay the first-touch / NFS-fetch cost. Read-only."""

    notes = []
    for p in paths:
        if not p.exists():
            notes.append(f"{p}: does not exist, skipped")
            continue
        files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()]
        n, total = 0, 0
        for f in files:
            try:
                with open(f, "rb") as fh:
                    while True:
                        chunk = fh.read(1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                n += 1
            except OSError:
                continue
        notes.append(f"{p}: warmed {n} file(s), {round(total/1e6, 1)} MB read")
    return notes


# ---- diagnosis -------------------------------------------------------------


def diagnose(rep: EnvReport) -> None:
    d = rep.diagnostics
    # Storage: working set on a network / slow filesystem
    for entry in rep.paths:
        ft = (entry.get("fs_type") or "").lower()
        base = ft.split(".")[0]
        if ft in NETWORK_FS or base in {"nfs", "cifs", "lustre", "gpfs", "beegfs"}:
            d.append(
                Diagnostic(
                    id="storage.network_fs",
                    severity="high",
                    area="storage",
                    finding=f"{entry['path']} is on a network filesystem ({ft}). Benchmark I/O "
                    f"will include network latency and can vary run to run.",
                    remedy="Copy the working set to node-local storage before timing, e.g. "
                    '`cp -a <data> "$TMPDIR"/` (or /dev/shm for small sets), then point '
                    "the benchmark at the local copy. On HPC use the node's local scratch.",
                )
            )
        elif ft in FAST_FS:
            d.append(
                Diagnostic(
                    id="storage.tmpfs",
                    severity="info",
                    area="storage",
                    finding=f"{entry['path']} is on {ft} (RAM-backed). Fast, but it consumes RAM "
                    f"and results will not reflect real disk I/O.",
                    remedy="Fine for CPU-bound benchmarks; for I/O-representative numbers use the "
                    "real target storage.",
                )
            )
        if entry.get("free_gb") is not None and entry["free_gb"] < 2:
            d.append(
                Diagnostic(
                    id="storage.low_space",
                    severity="warn",
                    area="storage",
                    finding=f"{entry['path']} has only {entry['free_gb']} GB free.",
                    remedy="Free space or choose another scratch dir; a full disk can stall or fail runs.",
                )
            )
    # CPU governor
    if rep.cpu_governor and rep.cpu_governor not in ("performance", ""):
        d.append(
            Diagnostic(
                id="cpu.governor",
                severity="warn",
                area="cpu",
                finding=f"CPU frequency governor is '{rep.cpu_governor}', which can down-clock "
                f"during bursts and add variance.",
                remedy="For stable numbers set the performance governor (needs privilege): "
                "`sudo cpupower frequency-set -g performance` (or via your cluster's docs). "
                "Revert afterwards if this is a shared machine.",
            )
        )
    # Memory pressure / swap
    if rep.swap_total_kb and rep.swap_free_kb is not None:
        used = rep.swap_total_kb - rep.swap_free_kb
        if used > 0.1 * rep.swap_total_kb and used > 256 * 1024:
            d.append(
                Diagnostic(
                    id="memory.swapping",
                    severity="high",
                    area="memory",
                    finding=f"The host is using swap ({round(used/1024)} MB). Swapping during a "
                    f"benchmark badly distorts timings.",
                    remedy="Reduce memory use or run on a host with more RAM; confirm no other job "
                    "is consuming memory before timing.",
                )
            )
    if rep.mem_total_kb and rep.mem_available_kb is not None:
        avail_frac = rep.mem_available_kb / rep.mem_total_kb
        if avail_frac < 0.1:
            d.append(
                Diagnostic(
                    id="memory.low_available",
                    severity="warn",
                    area="memory",
                    finding=f"Only {round(avail_frac*100)}% of RAM is available; the box is under "
                    f"memory pressure.",
                    remedy="Free memory or pick a less-loaded host before benchmarking.",
                )
            )
    # Load relative to cores
    if rep.load_avg and rep.cpu_logical:
        one_min = rep.load_avg[0]
        if one_min > rep.cpu_logical * 0.7:
            d.append(
                Diagnostic(
                    id="load.busy",
                    severity="high",
                    area="load",
                    finding=f"1-minute load average is {one_min} on {rep.cpu_logical} logical CPUs; "
                    f"the host is busy with other work.",
                    remedy="Benchmark on an idle host, or reserve dedicated cores (e.g. taskset / "
                    "cgroups / an exclusive HPC allocation) so competing work does not skew results.",
                )
            )
    # Virtualization / container note (informational)
    if rep.container_hint:
        d.append(
            Diagnostic(
                id="general.container",
                severity="info",
                area="general",
                finding=f"Running inside {rep.container_hint}; cgroup CPU/memory limits may cap "
                f"resources below the host totals reported here.",
                remedy="Record the container's CPU/memory limits alongside results; host totals may "
                "overstate what the benchmark can actually use.",
            )
        )
    if rep.virtualization_hint:
        d.append(
            Diagnostic(
                id="general.virtualized",
                severity="info",
                area="general",
                finding=f"Virtualization detected ({rep.virtualization_hint}); neighbours on the "
                f"hypervisor can add variance ('noisy neighbour').",
                remedy="Prefer bare metal or a dedicated instance for the most stable numbers; "
                "otherwise run more iterations and report variance.",
            )
        )
    # HPC: available but not inside an allocation
    if rep.hpc.get("scheduler_detected") and not rep.hpc.get("inside_allocation"):
        d.append(
            Diagnostic(
                id="hpc.on_login_node",
                severity="warn",
                area="general",
                finding=f"An HPC scheduler ({rep.hpc.get('primary')}) is available but this process "
                f"is not inside a job allocation - you may be on a shared login node.",
                remedy="Do not benchmark on the login node. Submit to a compute node "
                "(the benchmark workflow can generate and submit the job script for you).",
            )
        )


# ---- scrubbing (anonymization for sharing) ---------------------------------


def scrub(rep: EnvReport) -> None:
    """Replace identifying fields with stable placeholders so a report can be shared."""

    rep.hostname = "host-redacted"
    rep.fqdn = ""
    rep.user = "user-redacted"
    for entry in rep.paths:
        # keep the fs_type and free space (the useful part), redact the actual path/device
        entry["path"] = "path-redacted"
        entry["source"] = "redacted" if entry.get("source") else ""
    if rep.disk_probe:
        rep.disk_probe.path = "scratch-redacted"
    rep.hpc["submit_paths"] = {k: "redacted" for k in rep.hpc.get("submit_paths", {})}


# ---- output ----------------------------------------------------------------


def emit(rep: EnvReport, fmt: str, out) -> None:
    if fmt == "json":
        json.dump(asdict(rep), out, indent=2, default=str)
        out.write("\n")
    elif fmt == "csv":
        import csv

        w = csv.writer(out)
        w.writerow(["field", "value"])
        flat = asdict(rep)
        for k, v in flat.items():
            if k == "diagnostics":
                continue
            w.writerow([k, json.dumps(v) if isinstance(v, (list, dict)) else v])
        w.writerow([])
        w.writerow(["diag_id", "severity", "area", "finding", "remedy"])
        for d in rep.diagnostics:
            w.writerow([d.id, d.severity, d.area, d.finding, d.remedy])
    else:
        L = out.write
        L(f"Benchmark environment capture ({rep.schema})\n")
        L(f"  captured: {rep.captured_at_utc}  tool: {rep.tool_version}\n")
        L(f"  host: {rep.hostname}  user: {rep.user}\n")
        L(
            f"  os: {rep.os_release or rep.os} ({rep.arch})  kernel: {rep.kernel}  python: {rep.python_version}\n"
        )
        if rep.container_hint:
            L(f"  container: {rep.container_hint}\n")
        if rep.virtualization_hint:
            L(f"  virtualization: {rep.virtualization_hint}\n")
        L(f"  cpu: {rep.cpu_model}\n")
        L(
            f"       logical={rep.cpu_logical} physical={rep.cpu_physical} governor={rep.cpu_governor or 'n/a'} "
            f"max_mhz={rep.cpu_max_mhz} numa={rep.numa_nodes} flags={','.join(rep.cpu_flags_sample) or 'n/a'}\n"
        )

        def gb(kb):
            return f"{round(kb/1024/1024, 1)}GB" if kb else "n/a"

        L(
            f"  mem: total={gb(rep.mem_total_kb)} avail={gb(rep.mem_available_kb)} "
            f"free={gb(rep.mem_free_kb)} cached={gb(rep.mem_cached_kb)} used={gb(rep.mem_used_kb)} "
            f"swap_total={gb(rep.swap_total_kb)} swap_free={gb(rep.swap_free_kb)}\n"
        )
        L(f"  load: {rep.load_avg or 'n/a'}  uptime_s: {rep.uptime_s}\n")
        if rep.gpus:
            for g in rep.gpus:
                L(
                    f"  gpu: {g.get('vendor')} {g.get('name')} mem_total_mb={g.get('mem_total_mb')} "
                    f"util_pct={g.get('util_pct')} driver={g.get('driver')}\n"
                )
        else:
            L("  gpu: none detected (no nvidia-smi/rocm-smi, or none present)\n")
        for entry in rep.paths:
            L(
                f"  path: {entry['path']}  fs={entry['fs_type']}  free_gb={entry.get('free_gb')}\n"
            )
        if rep.disk_probe:
            dp = rep.disk_probe
            L(
                f"  disk probe @ {dp.path}: write={dp.write_mb_s} MB/s read={dp.read_mb_s} MB/s ({dp.note})\n"
            )
        if rep.hpc.get("scheduler_detected"):
            L(
                f"  hpc: {rep.hpc.get('primary')} detected; inside_allocation={rep.hpc.get('inside_allocation')} "
                f"partitions={rep.hpc.get('slurm_partitions_hint')}\n"
            )
        else:
            L("  hpc: no scheduler detected\n")
        if rep.unread:
            L(f"  NOT READ (honest): {', '.join(rep.unread)}\n")
        L("\nDiagnostics (flagged conditions and suggested remedies):\n")
        if not rep.diagnostics:
            L("  none - environment looks reasonable for benchmarking\n")
        order = {"high": 0, "warn": 1, "info": 2}
        for d in sorted(rep.diagnostics, key=lambda x: order.get(x.severity, 3)):
            L(
                f"  [{d.severity:4}] {d.area}: {d.finding}\n         remedy: {d.remedy}\n"
            )


# ---- main ------------------------------------------------------------------


def build_report(
    repo: Path,
    paths: list[Path],
    want_probe: bool,
    probe_mb: int,
    warm: list[Path],
    want_scrub: bool,
) -> EnvReport:
    rep = EnvReport()
    rep.captured_at_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rep.tool_version = _framework_version()
    capture_identity(rep)
    capture_os(rep)
    capture_cpu(rep)
    capture_memory(rep)
    capture_load(rep)
    capture_gpu(rep)
    # Always include the repo path plus any caller-named paths.
    all_paths = [repo] + [p for p in paths if str(p) != str(repo)]
    capture_paths(rep, all_paths)
    capture_hpc(rep)
    if warm:
        rep.diagnostics.append(
            Diagnostic(
                id="warm.done",
                severity="info",
                area="storage",
                finding="cache warm-up requested",
                remedy="; ".join(warm_paths(warm)),
            )
        )
    if want_probe:
        scratch = Path(tempfile.gettempdir()) / "bench_env_probe"
        rep.disk_probe = disk_probe(scratch, probe_mb)
    diagnose(rep)
    if want_scrub:
        scrub(rep)
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Capture and diagnose the benchmark environment."
    )
    ap.add_argument(
        "--version",
        action="store_true",
        help="Print the agent-workflows framework version and exit.",
    )
    ap.add_argument(
        "--repo", default=".", help="Repository / working directory to inspect."
    )
    ap.add_argument("--format", choices=["json", "csv", "text"], default="text")
    ap.add_argument("--out", help="Write output to FILE instead of stdout.")
    ap.add_argument(
        "--paths",
        default="",
        help="Comma-separated extra paths to inspect (e.g. data dirs, scratch).",
    )
    ap.add_argument(
        "--disk-probe",
        action="store_true",
        help="Run a bounded write/read probe in the OS temp dir (writes only there).",
    )
    ap.add_argument(
        "--probe-mb",
        type=int,
        default=PROBE_DEFAULT_MB,
        help=f"Size of the disk probe in MB (default {PROBE_DEFAULT_MB}).",
    )
    ap.add_argument(
        "--warm",
        default="",
        help="Comma-separated paths to read into cache before benchmarking (read-only).",
    )
    ap.add_argument(
        "--scrub",
        action="store_true",
        help="Redact hostname/user/paths so the report can be shared.",
    )
    args = ap.parse_args(argv)

    if args.version:
        print(_framework_version())
        return 0

    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"error: --repo path does not exist: {repo}", file=sys.stderr)
        return 2
    paths = [Path(p.strip()).resolve() for p in args.paths.split(",") if p.strip()]
    warm = [Path(p.strip()).resolve() for p in args.warm.split(",") if p.strip()]

    rep = build_report(repo, paths, args.disk_probe, args.probe_mb, warm, args.scrub)

    # newline="" so the csv module controls line endings (no double-blank rows on Windows).
    out = open(args.out, "w", encoding="utf-8", newline="") if args.out else sys.stdout
    try:
        emit(rep, args.format, out)
    finally:
        if args.out:
            out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
