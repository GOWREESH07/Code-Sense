import os
import json
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ROOT_DIR = _BACKEND_DIR.parent
for env_path in [_BACKEND_DIR / ".env", _ROOT_DIR / ".env"]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

DB_DIR = _BACKEND_DIR / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_PATH = DB_DIR / "codesense.db"



class Database:
    def __init__(self):
        self.use_supabase = bool(SUPABASE_URL and SUPABASE_KEY)
        self.supabase = None
        if self.use_supabase:
            try:
                from supabase import create_client, ClientOptions
                import httpx
                # Disable HTTP/2 to prevent connection drops/resets from Supabase Edge/Cloudflare
                custom_httpx = httpx.Client(http2=False, timeout=30.0)
                options = ClientOptions(httpx_client=custom_httpx)
                self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY, options=options)
                print(f"[DB] Successfully initialized Supabase client at: {SUPABASE_URL} (HTTP/1.1 pool)")
            except Exception as e:
                print(f"[DB] Supabase initialization failed ({e}), falling back to SQLite.")
                self.use_supabase = False

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
                ai_generated_score REAL NOT NULL DEFAULT 0.0,
                ai_confidence TEXT NOT NULL DEFAULT 'low',
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
            );
            """)
            # Safe schema evolution for existing SQLite tables
            try:
                cursor.execute("ALTER TABLE file_metrics ADD COLUMN ai_generated_score REAL DEFAULT 0.0")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE file_metrics ADD COLUMN ai_confidence TEXT DEFAULT 'low'")
            except Exception:
                pass

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

    def _ensure_project_in_supabase(self, project_id: str):
        if not self.use_supabase:
            return
        try:
            parent = self.supabase.table("projects").select("id").eq("id", project_id).execute()
            if not parent.data:
                with self._get_sqlite_conn() as conn:
                    p_row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
                    if p_row:
                        p_data = dict(p_row)
                        supabase_uid = None
                        if p_data.get("user_id") and p_data["user_id"] != "default-user":
                            try:
                                uuid.UUID(str(p_data["user_id"]))
                                supabase_uid = str(p_data["user_id"])
                            except ValueError:
                                supabase_uid = None
                        self.supabase.table("projects").insert({
                            "id": p_data["id"],
                            "user_id": supabase_uid,
                            "name": p_data["name"],
                            "description": p_data.get("description", ""),
                            "repo_url": p_data.get("repo_url", ""),
                            "created_at": p_data["created_at"],
                            "updated_at": p_data["updated_at"],
                        }).execute()
        except Exception as e:
            print(f"[DB] _ensure_project_in_supabase notice: {e}")

    def _ensure_run_in_supabase(self, run_id: str):
        if not self.use_supabase:
            return
        try:
            r = self.supabase.table("analysis_runs").select("id, project_id").eq("id", run_id).execute()
            if not r.data:
                with self._get_sqlite_conn() as conn:
                    row = conn.execute("SELECT * FROM analysis_runs WHERE id = ?", (run_id,)).fetchone()
                    if row:
                        rd = dict(row)
                        self._ensure_project_in_supabase(rd["project_id"])
                        summary_val = rd.get("summary") or {}
                        if isinstance(summary_val, str):
                            try:
                                summary_val = json.loads(summary_val)
                            except Exception:
                                summary_val = {}
                        self.supabase.table("analysis_runs").insert({
                            "id": rd["id"],
                            "project_id": rd["project_id"],
                            "status": rd.get("status", "queued"),
                            "overall_score": rd.get("overall_score"),
                            "total_loc": rd.get("total_loc", 0),
                            "total_complexity": rd.get("total_complexity", 0.0),
                            "bug_probability": rd.get("bug_probability", 0.0),
                            "tech_debt_minutes": rd.get("tech_debt_minutes", 0),
                            "summary": summary_val,
                            "created_at": rd.get("created_at"),
                            "completed_at": rd.get("completed_at"),
                        }).execute()
        except Exception as e:
            print(f"[DB] _ensure_run_in_supabase notice: {e}")

    # Projects
    def create_project(self, name: str, description: str = "", repo_url: str = "", user_id: str = "default-user") -> Dict[str, Any]:
        proj_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        
        # 1. Always persist to local SQLite first
        with self._get_sqlite_conn() as conn:
            conn.execute(
                "INSERT INTO projects (id, user_id, name, description, repo_url, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (proj_id, user_id, name, description, repo_url, now, now)
            )
            conn.commit()

        # 2. Replicate to Supabase if connected
        if self.use_supabase:
            supabase_uid = None
            if user_id and user_id != "default-user":
                try:
                    uuid.UUID(str(user_id))
                    supabase_uid = str(user_id)
                except ValueError:
                    supabase_uid = None
            try:
                self.supabase.table("projects").insert({
                    "id": proj_id,
                    "user_id": supabase_uid,
                    "name": name,
                    "description": description,
                    "repo_url": repo_url,
                    "created_at": now,
                    "updated_at": now,
                }).execute()
            except Exception as e:
                print(f"[DB] Supabase create_project warning: {e}")

        return {"id": proj_id, "user_id": user_id, "name": name, "description": description, "repo_url": repo_url, "created_at": now, "updated_at": now}


    def list_projects(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        remote_projs = []
        if self.use_supabase:
            try:
                query = self.supabase.table("projects").select("*").order("created_at", desc=True)
                if user_id:
                    query = query.eq("user_id", user_id)
                res = query.execute()
                remote_projs = res.data or []
            except Exception as e:
                print(f"[DB] Supabase list_projects warning: {e}")

        with self._get_sqlite_conn() as conn:
            if user_id:
                rows = conn.execute("SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
            local_projs = [dict(r) for r in rows]

        # Merge projects from both sources
        seen_ids = set()
        merged = []
        for p in remote_projs + local_projs:
            if p["id"] not in seen_ids:
                seen_ids.add(p["id"])
                merged.append(p)
        return merged

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        if self.use_supabase:
            try:
                res = self.supabase.table("projects").select("*").eq("id", project_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                print(f"[DB] Supabase get_project warning: {e}")

        with self._get_sqlite_conn() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            return dict(row) if row else None

    def delete_project(self, project_id: str) -> bool:
        with self._get_sqlite_conn() as conn:
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()

        if self.use_supabase:
            try:
                self.supabase.table("projects").delete().eq("id", project_id).execute()
            except Exception as e:
                print(f"[DB] Supabase delete_project warning: {e}")

        return True

    # Analysis Runs
    def create_run(self, project_id: str) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        # 1. Local SQLite first
        with self._get_sqlite_conn() as conn:
            conn.execute(
                "INSERT INTO analysis_runs (id, project_id, status, created_at, summary) VALUES (?, ?, ?, ?, ?)",
                (run_id, project_id, "queued", now, "{}")
            )
            conn.commit()

        # 2. Replicate to Supabase
        if self.use_supabase:
            try:
                # Ensure parent project exists in Supabase first to satisfy foreign key
                parent = self.supabase.table("projects").select("id").eq("id", project_id).execute()
                if not parent.data:
                    with self._get_sqlite_conn() as conn:
                        p_row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
                        if p_row:
                            p_data = dict(p_row)
                            supabase_uid = None
                            if p_data.get("user_id") and p_data["user_id"] != "default-user":
                                try:
                                    uuid.UUID(str(p_data["user_id"]))
                                    supabase_uid = str(p_data["user_id"])
                                except ValueError:
                                    supabase_uid = None
                            self.supabase.table("projects").insert({
                                "id": p_data["id"],
                                "user_id": supabase_uid,
                                "name": p_data["name"],
                                "description": p_data.get("description", ""),
                                "repo_url": p_data.get("repo_url", ""),
                                "created_at": p_data["created_at"],
                                "updated_at": p_data["updated_at"],
                            }).execute()

                self.supabase.table("analysis_runs").insert({
                    "id": run_id,
                    "project_id": project_id,
                    "status": "queued",
                    "created_at": now,
                    "summary": {},
                }).execute()
            except Exception as e:
                print(f"[DB] Supabase create_run warning: {e}")

        return {"id": run_id, "project_id": project_id, "status": "queued", "created_at": now, "summary": {}}


    def update_run_status(self, run_id: str, status: str, error_message: Optional[str] = None):
        now = datetime.utcnow().isoformat()
        with self._get_sqlite_conn() as conn:
            if status in ["done", "failed"]:
                conn.execute(
                    "UPDATE analysis_runs SET status = ?, error_message = ?, completed_at = ? WHERE id = ?",
                    (status, error_message, now, run_id)
                )
            else:
                conn.execute(
                    "UPDATE analysis_runs SET status = ?, error_message = ? WHERE id = ?",
                    (status, error_message, run_id)
                )
            conn.commit()

        if self.use_supabase:
            try:
                data = {"status": status}
                if error_message:
                    data["error_message"] = error_message
                if status in ["done", "failed"]:
                    data["completed_at"] = now
                self.supabase.table("analysis_runs").update(data).eq("id", run_id).execute()
            except Exception as e:
                print(f"[DB] Supabase update_run_status warning: {e}")

    def update_run_results(self, run_id: str, overall_score: float, total_loc: int, total_complexity: float,
                           bug_probability: float, tech_debt_minutes: int, summary: Dict[str, Any]):
        completed_at = datetime.utcnow().isoformat()
        with self._get_sqlite_conn() as conn:
            conn.execute(
                """UPDATE analysis_runs 
                   SET status = 'done', overall_score = ?, total_loc = ?, total_complexity = ?,
                       bug_probability = ?, tech_debt_minutes = ?, summary = ?, completed_at = ?
                   WHERE id = ?""",
                (overall_score, total_loc, total_complexity, bug_probability, tech_debt_minutes, json.dumps(summary), completed_at, run_id)
            )
            conn.commit()

        if self.use_supabase:
            try:
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
            except Exception as e:
                print(f"[DB] Supabase update_run_results warning: {e}")

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        if self.use_supabase:
            try:
                res = self.supabase.table("analysis_runs").select("*").eq("id", run_id).execute()
                if res.data:
                    data = res.data[0]
                    if isinstance(data.get("summary"), str):
                        try:
                            data["summary"] = json.loads(data["summary"])
                        except Exception:
                            data["summary"] = {}
                    return data
            except Exception as e:
                print(f"[DB] Supabase get_run warning: {e}")

        # Fallback to local SQLite
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
        runs = []
        if self.use_supabase:
            try:
                res = self.supabase.table("analysis_runs").select("*").eq("project_id", project_id).order("created_at", desc=True).execute()
                runs = res.data or []
                for r in runs:
                    if isinstance(r.get("summary"), str):
                        try:
                            r["summary"] = json.loads(r["summary"])
                        except Exception:
                            r["summary"] = {}
            except Exception as e:
                print(f"[DB] Supabase list_runs_for_project warning: {e}")

        with self._get_sqlite_conn() as conn:
            rows = conn.execute("SELECT * FROM analysis_runs WHERE project_id = ? ORDER BY created_at DESC", (project_id,)).fetchall()
            for r in rows:
                d = dict(r)
                if isinstance(d.get("summary"), str):
                    try:
                        d["summary"] = json.loads(d["summary"])
                    except Exception:
                        d["summary"] = {}
                if not any(existing["id"] == d["id"] for existing in runs):
                    runs.append(d)

        return runs

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
                "ai_generated_score": float(m.get("ai_generated_score", 0.0) or 0.0),
                "ai_confidence": str(m.get("ai_confidence", "low") or "low"),
                "created_at": now,
            })

        with self._get_sqlite_conn() as conn:
            conn.executemany(
                """INSERT INTO file_metrics 
                   (id, run_id, file_path, language, loc, cyclomatic_complexity, maintainability_index, 
                    duplication_pct, cbo, lcom, dit, noc, comment_density, bug_probability, smells_count, 
                    ai_generated_score, ai_confidence, created_at)
                   VALUES (:id, :run_id, :file_path, :language, :loc, :cyclomatic_complexity, :maintainability_index,
                           :duplication_pct, :cbo, :lcom, :dit, :noc, :comment_density, :bug_probability, :smells_count, 
                           :ai_generated_score, :ai_confidence, :created_at)""",
                records
            )
            conn.commit()

        if self.use_supabase:
            try:
                self._ensure_run_in_supabase(run_id)
                self.supabase.table("file_metrics").insert(records).execute()
            except Exception as e:
                # If remote table doesn't have the new columns yet, retry without them so base metrics still sync
                if "ai_generated_score" in str(e) or "ai_confidence" in str(e):
                    try:
                        stripped_records = [{k: v for k, v in r.items() if k not in ("ai_generated_score", "ai_confidence")} for r in records]
                        self.supabase.table("file_metrics").insert(stripped_records).execute()
                    except Exception as e2:
                        print(f"[DB] Supabase save_file_metrics fallback warning: {e2}")
                print(f"[DB] Supabase save_file_metrics warning: {e}")

    def get_file_metrics(self, run_id: str) -> List[Dict[str, Any]]:
        if self.use_supabase:
            try:
                res = self.supabase.table("file_metrics").select("*").eq("run_id", run_id).execute()
                if res.data:
                    return res.data
            except Exception as e:
                print(f"[DB] Supabase get_file_metrics warning: {e}")

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

        with self._get_sqlite_conn() as conn:
            conn.executemany(
                """INSERT INTO defects 
                   (id, run_id, file_path, line_number, rule_id, severity, tool, description, created_at)
                   VALUES (:id, :run_id, :file_path, :line_number, :rule_id, :severity, :tool, :description, :created_at)""",
                records
            )
            conn.commit()

        if self.use_supabase:
            try:
                self._ensure_run_in_supabase(run_id)
                self.supabase.table("defects").insert(records).execute()
            except Exception as e:
                print(f"[DB] Supabase save_defects warning: {e}")


    def get_defects(self, run_id: str) -> List[Dict[str, Any]]:
        if self.use_supabase:
            try:
                res = self.supabase.table("defects").select("*").eq("run_id", run_id).execute()
                if res.data:
                    return res.data
            except Exception as e:
                print(f"[DB] Supabase get_defects warning: {e}")

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

        with self._get_sqlite_conn() as conn:
            conn.executemany(
                """INSERT INTO recommendations 
                   (id, run_id, priority, title, category, description, suggested_fix, file_path, impact, created_at)
                   VALUES (:id, :run_id, :priority, :title, :category, :description, :suggested_fix, :file_path, :impact, :created_at)""",
                records
            )
            conn.commit()

        if self.use_supabase:
            try:
                self._ensure_run_in_supabase(run_id)
                self.supabase.table("recommendations").insert(records).execute()
            except Exception as e:
                print(f"[DB] Supabase save_recommendations warning: {e}")


    def get_recommendations(self, run_id: str) -> List[Dict[str, Any]]:
        if self.use_supabase:
            try:
                res = self.supabase.table("recommendations").select("*").eq("run_id", run_id).order("priority", desc=False).execute()
                if res.data:
                    return res.data
            except Exception as e:
                print(f"[DB] Supabase get_recommendations warning: {e}")

        with self._get_sqlite_conn() as conn:
            rows = conn.execute("SELECT * FROM recommendations WHERE run_id = ? ORDER BY priority ASC", (run_id,)).fetchall()
            return [dict(r) for r in rows]

    def sync_sqlite_to_supabase(self):
        """One-time utility to sync existing SQLite data into Supabase."""
        if not self.use_supabase:
            return
        try:
            with self._get_sqlite_conn() as conn:
                projects = [dict(r) for r in conn.execute("SELECT * FROM projects").fetchall()]
                runs = [dict(r) for r in conn.execute("SELECT * FROM analysis_runs").fetchall()]
                metrics = [dict(r) for r in conn.execute("SELECT * FROM file_metrics").fetchall()]
                defects = [dict(r) for r in conn.execute("SELECT * FROM defects").fetchall()]
                recs = [dict(r) for r in conn.execute("SELECT * FROM recommendations").fetchall()]

            if projects:
                self.supabase.table("projects").upsert(projects).execute()
            for r in runs:
                if isinstance(r.get("summary"), str):
                    try:
                        r["summary"] = json.loads(r["summary"])
                    except Exception:
                        r["summary"] = {}
            if runs:
                self.supabase.table("analysis_runs").upsert(runs).execute()
            if metrics:
                self.supabase.table("file_metrics").upsert(metrics).execute()
            if defects:
                self.supabase.table("defects").upsert(defects).execute()
            if recs:
                self.supabase.table("recommendations").upsert(recs).execute()
            print(f"[DB Sync] Successfully synced {len(projects)} projects and {len(runs)} runs to Supabase!")
        except Exception as e:
            print(f"[DB Sync] Supabase sync notice: {e}")


db = Database()

