import os
import json
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_PATH = DB_DIR / "codesense.db"


class Database:
    def __init__(self):
        self.use_supabase = bool(SUPABASE_URL and SUPABASE_KEY)
        self.supabase = None
        if self.use_supabase:
            try:
                from supabase import create_client
                self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            except Exception as e:
                print(f"[DB] Supabase initialization failed ({e}), falling back to SQLite.")
                self.use_supabase = False

        if not self.use_supabase:
            self._init_sqlite()

    def _get_sqlite_conn(self):
        conn = sqlite3.connect(str(SQLITE_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self):
        with self._get_sqlite_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT NOT NULL,
                description TEXT,
                repo_url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                status TEXT NOT NULL,
                overall_score REAL,
                total_loc INTEGER DEFAULT 0,
                total_complexity REAL DEFAULT 0,
                bug_probability REAL DEFAULT 0,
                tech_debt_minutes INTEGER DEFAULT 0,
                error_message TEXT,
                summary TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_metrics (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                language TEXT NOT NULL,
                loc INTEGER NOT NULL,
                cyclomatic_complexity REAL NOT NULL,
                maintainability_index REAL NOT NULL,
                duplication_pct REAL NOT NULL DEFAULT 0,
                cbo INTEGER NOT NULL DEFAULT 0,
                lcom INTEGER NOT NULL DEFAULT 0,
                dit INTEGER NOT NULL DEFAULT 0,
                noc INTEGER NOT NULL DEFAULT 0,
                comment_density REAL NOT NULL DEFAULT 0,
                bug_probability REAL NOT NULL DEFAULT 0,
                smells_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS defects (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER,
                rule_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                tool TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                priority INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                suggested_fix TEXT,
                file_path TEXT,
                impact TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
            );
            """)
            conn.commit()

    # Projects
    def create_project(self, name: str, description: str = "", repo_url: str = "", user_id: str = "default-user") -> Dict[str, Any]:
        proj_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        if self.use_supabase:
            res = self.supabase.table("projects").insert({
                "id": proj_id,
                "user_id": user_id,
                "name": name,
                "description": description,
                "repo_url": repo_url,
                "created_at": now,
                "updated_at": now,
            }).execute()
            return res.data[0] if res.data else {}
        else:
            with self._get_sqlite_conn() as conn:
                conn.execute(
                    "INSERT INTO projects (id, user_id, name, description, repo_url, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (proj_id, user_id, name, description, repo_url, now, now)
                )
                conn.commit()
            return {"id": proj_id, "user_id": user_id, "name": name, "description": description, "repo_url": repo_url, "created_at": now, "updated_at": now}

    def list_projects(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.use_supabase:
            query = self.supabase.table("projects").select("*").order("created_at", desc=True)
            if user_id:
                query = query.eq("user_id", user_id)
            res = query.execute()
            return res.data or []
        else:
            with self._get_sqlite_conn() as conn:
                if user_id:
                    rows = conn.execute("SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
                else:
                    rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
                return [dict(r) for r in rows]

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        if self.use_supabase:
            res = self.supabase.table("projects").select("*").eq("id", project_id).execute()
            return res.data[0] if res.data else None
        else:
            with self._get_sqlite_conn() as conn:
                row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
                return dict(row) if row else None

    def delete_project(self, project_id: str) -> bool:
        if self.use_supabase:
            self.supabase.table("projects").delete().eq("id", project_id).execute()
            return True
        else:
            with self._get_sqlite_conn() as conn:
                conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                conn.commit()
            return True

    # Analysis Runs
    def create_run(self, project_id: str) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        if self.use_supabase:
            res = self.supabase.table("analysis_runs").insert({
                "id": run_id,
                "project_id": project_id,
                "status": "queued",
                "created_at": now,
                "summary": {},
            }).execute()
            return res.data[0] if res.data else {}
        else:
            with self._get_sqlite_conn() as conn:
                conn.execute(
                    "INSERT INTO analysis_runs (id, project_id, status, created_at, summary) VALUES (?, ?, ?, ?, ?)",
                    (run_id, project_id, "queued", now, "{}")
                )
                conn.commit()
            return {"id": run_id, "project_id": project_id, "status": "queued", "created_at": now, "summary": {}}

    def update_run_status(self, run_id: str, status: str, error_message: Optional[str] = None):
        if self.use_supabase:
            data = {"status": status}
            if error_message:
                data["error_message"] = error_message
            if status in ["done", "failed"]:
                data["completed_at"] = datetime.utcnow().isoformat()
            self.supabase.table("analysis_runs").update(data).eq("id", run_id).execute()
        else:
            with self._get_sqlite_conn() as conn:
                if status in ["done", "failed"]:
                    completed_at = datetime.utcnow().isoformat()
                    conn.execute(
                        "UPDATE analysis_runs SET status = ?, error_message = ?, completed_at = ? WHERE id = ?",
                        (status, error_message, completed_at, run_id)
                    )
                else:
                    conn.execute(
                        "UPDATE analysis_runs SET status = ?, error_message = ? WHERE id = ?",
                        (status, error_message, run_id)
                    )
                conn.commit()

    def update_run_results(self, run_id: str, overall_score: float, total_loc: int, total_complexity: float,
                           bug_probability: float, tech_debt_minutes: int, summary: Dict[str, Any]):
        completed_at = datetime.utcnow().isoformat()
        if self.use_supabase:
            self.supabase.table("analysis_runs").update({
                "status": "done",
                "overall_score": overall_score,
                "total_loc": total_loc,
                "total_complexity": total_complexity,
                "bug_probability": bug_probability,
                "tech_debt_minutes": tech_debt_minutes,
                "summary": summary,
                "completed_at": completed_at,
            }).eq("id", run_id).execute()
        else:
            with self._get_sqlite_conn() as conn:
                conn.execute(
                    """UPDATE analysis_runs 
                       SET status = 'done', overall_score = ?, total_loc = ?, total_complexity = ?,
                           bug_probability = ?, tech_debt_minutes = ?, summary = ?, completed_at = ?
                       WHERE id = ?""",
                    (overall_score, total_loc, total_complexity, bug_probability, tech_debt_minutes, json.dumps(summary), completed_at, run_id)
                )
                conn.commit()

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        if self.use_supabase:
            res = self.supabase.table("analysis_runs").select("*").eq("id", run_id).execute()
            return res.data[0] if res.data else None
        else:
            with self._get_sqlite_conn() as conn:
                row = conn.execute("SELECT * FROM analysis_runs WHERE id = ?", (run_id,)).fetchone()
                if not row:
                    return None
                data = dict(row)
                if isinstance(data.get("summary"), str):
                    try:
                        data["summary"] = json.loads(data["summary"])
                    except Exception:
                        data["summary"] = {}
                return data

    def list_runs_for_project(self, project_id: str) -> List[Dict[str, Any]]:
        if self.use_supabase:
            res = self.supabase.table("analysis_runs").select("*").eq("project_id", project_id).order("created_at", desc=True).execute()
            return res.data or []
        else:
            with self._get_sqlite_conn() as conn:
                rows = conn.execute("SELECT * FROM analysis_runs WHERE project_id = ? ORDER BY created_at DESC", (project_id,)).fetchall()
                results = []
                for r in rows:
                    d = dict(r)
                    if isinstance(d.get("summary"), str):
                        try:
                            d["summary"] = json.loads(d["summary"])
                        except Exception:
                            d["summary"] = {}
                    results.append(d)
                return results

    # File Metrics
    def save_file_metrics(self, run_id: str, metrics_list: List[Dict[str, Any]]):
        if not metrics_list:
            return
        now = datetime.utcnow().isoformat()
        records = []
        for m in metrics_list:
            records.append({
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "file_path": m["file_path"],
                "language": m.get("language", "python"),
                "loc": m.get("loc", 0),
                "cyclomatic_complexity": m.get("cyclomatic_complexity", 0.0),
                "maintainability_index": m.get("maintainability_index", 100.0),
                "duplication_pct": m.get("duplication_pct", 0.0),
                "cbo": m.get("cbo", 0),
                "lcom": m.get("lcom", 0),
                "dit": m.get("dit", 0),
                "noc": m.get("noc", 0),
                "comment_density": m.get("comment_density", 0.0),
                "bug_probability": m.get("bug_probability", 0.0),
                "smells_count": m.get("smells_count", 0),
                "created_at": now,
            })
        if self.use_supabase:
            self.supabase.table("file_metrics").insert(records).execute()
        else:
            with self._get_sqlite_conn() as conn:
                conn.executemany(
                    """INSERT INTO file_metrics 
                       (id, run_id, file_path, language, loc, cyclomatic_complexity, maintainability_index, 
                        duplication_pct, cbo, lcom, dit, noc, comment_density, bug_probability, smells_count, created_at)
                       VALUES (:id, :run_id, :file_path, :language, :loc, :cyclomatic_complexity, :maintainability_index,
                               :duplication_pct, :cbo, :lcom, :dit, :noc, :comment_density, :bug_probability, :smells_count, :created_at)""",
                    records
                )
                conn.commit()

    def get_file_metrics(self, run_id: str) -> List[Dict[str, Any]]:
        if self.use_supabase:
            res = self.supabase.table("file_metrics").select("*").eq("run_id", run_id).execute()
            return res.data or []
        else:
            with self._get_sqlite_conn() as conn:
                rows = conn.execute("SELECT * FROM file_metrics WHERE run_id = ?", (run_id,)).fetchall()
                return [dict(r) for r in rows]

    # Defects
    def save_defects(self, run_id: str, defects_list: List[Dict[str, Any]]):
        if not defects_list:
            return
        now = datetime.utcnow().isoformat()
        records = []
        for d in defects_list:
            records.append({
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "file_path": d.get("file_path", ""),
                "line_number": d.get("line_number", 1),
                "rule_id": d.get("rule_id", "UNKNOWN"),
                "severity": d.get("severity", "info"),
                "tool": d.get("tool", "static"),
                "description": d.get("description", ""),
                "created_at": now,
            })
        if self.use_supabase:
            self.supabase.table("defects").insert(records).execute()
        else:
            with self._get_sqlite_conn() as conn:
                conn.executemany(
                    """INSERT INTO defects 
                       (id, run_id, file_path, line_number, rule_id, severity, tool, description, created_at)
                       VALUES (:id, :run_id, :file_path, :line_number, :rule_id, :severity, :tool, :description, :created_at)""",
                    records
                )
                conn.commit()

    def get_defects(self, run_id: str) -> List[Dict[str, Any]]:
        if self.use_supabase:
            res = self.supabase.table("defects").select("*").eq("run_id", run_id).execute()
            return res.data or []
        else:
            with self._get_sqlite_conn() as conn:
                rows = conn.execute("SELECT * FROM defects WHERE run_id = ?", (run_id,)).fetchall()
                return [dict(r) for r in rows]

    # Recommendations
    def save_recommendations(self, run_id: str, recs_list: List[Dict[str, Any]]):
        if not recs_list:
            return
        now = datetime.utcnow().isoformat()
        records = []
        for r in recs_list:
            records.append({
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "priority": r.get("priority", 1),
                "title": r.get("title", ""),
                "category": r.get("category", "General"),
                "description": r.get("description", ""),
                "suggested_fix": r.get("suggested_fix", ""),
                "file_path": r.get("file_path", ""),
                "impact": r.get("impact", "Medium"),
                "created_at": now,
            })
        if self.use_supabase:
            self.supabase.table("recommendations").insert(records).execute()
        else:
            with self._get_sqlite_conn() as conn:
                conn.executemany(
                    """INSERT INTO recommendations 
                       (id, run_id, priority, title, category, description, suggested_fix, file_path, impact, created_at)
                       VALUES (:id, :run_id, :priority, :title, :category, :description, :suggested_fix, :file_path, :impact, :created_at)""",
                    records
                )
                conn.commit()

    def get_recommendations(self, run_id: str) -> List[Dict[str, Any]]:
        if self.use_supabase:
            res = self.supabase.table("recommendations").select("*").eq("run_id", run_id).order("priority", desc=False).execute()
            return res.data or []
        else:
            with self._get_sqlite_conn() as conn:
                rows = conn.execute("SELECT * FROM recommendations WHERE run_id = ? ORDER BY priority ASC", (run_id,)).fetchall()
                return [dict(r) for r in rows]


db = Database()
