"""Opt-in performance benchmarks (informational only).

These are NOT part of the default test suite and are NEVER a hard pass/fail gate:
timings are machine-dependent. They exist to (a) establish a baseline and (b) let a
developer measure the effect of the performance changes proposed in
`.agents/plans/pending/2026-07-04-assess-performance.md` (PERF-1, PERF-3).

Run explicitly with:

    OCMAN_BENCHMARK=1 PYTHONPATH=. pytest tests/test_perf.py -s

They print timings to stdout and always assert-pass (unless the operation errors),
so they cannot destabilize CI even if accidentally collected.
"""

import os
import time
import json
import sqlite3
import contextlib
from pathlib import Path

import pytest

import ocman
from ocman import bundle_session_data, extract_and_import_session, db_rebase_paths

pytestmark = pytest.mark.skipif(
    os.environ.get("OCMAN_BENCHMARK") != "1",
    reason="informational benchmark; set OCMAN_BENCHMARK=1 to run",
)


@contextlib.contextmanager
def _timed(label):
    start = time.perf_counter()
    yield
    dur = time.perf_counter() - start
    print(f"[benchmark] {label}: {dur*1000:.1f} ms")


def _make_db(tmp_path):
    db_path = tmp_path / "opencode.db"
    ocman.OPENCODE_DB_PATH = db_path
    ocman.OPENCODE_HISTORY_PATH = tmp_path / "hist.json"
    ocman.OPENCODE_STORAGE_DIR = tmp_path / "storage"
    ocman.OPENCODE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("CREATE TABLE project (id TEXT PRIMARY KEY, worktree TEXT, name TEXT)")
    cur.execute(
        "CREATE TABLE session (id TEXT PRIMARY KEY, project_id TEXT, title TEXT, "
        "time_created INTEGER, time_updated INTEGER, directory TEXT, parent_id TEXT)"
    )
    for table, col in ocman.SESSION_RELATIONAL_TABLES:
        if table == "session":
            continue
        cur.execute(f"CREATE TABLE {table} (id TEXT, {col} TEXT)")
    conn.commit()
    conn.close()
    return db_path


def test_benchmark_import_collision_remap(tmp_path):
    """PERF-1: time an import-with-collision over a wide subtree of diffs."""
    _make_db(tmp_path)
    n = 300
    conn = sqlite3.connect(str(ocman.OPENCODE_DB_PATH))
    cur = conn.cursor()
    cur.execute("INSERT INTO project VALUES ('proj-1', '/old/path', 'P')")
    cur.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('root', 'proj-1', 'Root', '/old/path/root')")
    for i in range(n):
        sid = f"child{i}"
        cur.execute(
            "INSERT INTO session (id, project_id, title, directory, parent_id) VALUES (?,?,?,?,?)",
            (sid, "proj-1", f"C{i}", f"/old/path/root/{sid}", "root"),
        )
        (ocman.OPENCODE_STORAGE_DIR / f"{sid}.json").write_text(
            json.dumps({"session_id": sid, "parent": "root", "blob": "x" * 500}), encoding="utf-8"
        )
    (ocman.OPENCODE_STORAGE_DIR / "root.json").write_text(
        json.dumps({"session_id": "root", "blob": "y" * 500}), encoding="utf-8"
    )
    conn.commit()
    conn.close()

    bundle = tmp_path / "b.ocbox"
    bundle_session_data("root", bundle)

    # Do not delete originals -> collision -> remap path exercised.
    with _timed(f"import-collision remap ({n} children)"):
        imported = extract_and_import_session(bundle, target_project_id="proj-1")
    assert imported != "root"


def test_benchmark_rebase_many_sessions(tmp_path):
    """PERF-3: time a rebase over many sessions."""
    _make_db(tmp_path)
    n = 2000
    conn = sqlite3.connect(str(ocman.OPENCODE_DB_PATH))
    cur = conn.cursor()
    cur.execute("INSERT INTO project VALUES ('proj-1', '/old/prefix/p', 'P')")
    cur.executemany(
        "INSERT INTO session (id, project_id, title, directory) VALUES (?,?,?,?)",
        [(f"s{i}", "proj-1", f"S{i}", f"/old/prefix/p/s{i}") for i in range(n)],
    )
    conn.commit()
    conn.close()

    with _timed(f"db_rebase_paths ({n} sessions)"):
        stats = db_rebase_paths("/old/prefix", "/new/prefix")
    assert stats["sessions_updated"] == n
