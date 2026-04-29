import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from models.evaluation import DocumentQAEvalCaseResult, DocumentQAEvalSummary


@dataclass(frozen=True)
class StoredEvaluationCaseResult:
    run_id: str
    name: str
    passed: bool
    answer: str
    citation_count: int
    checks: list[str]
    failures: list[str]
    latency_ms: float
    document_id: str | None


@dataclass(frozen=True)
class StoredEvaluationRun:
    run_id: str
    total_cases: int
    passed: int
    failed: int
    average_latency_ms: float
    created_at: str


class SQLiteEvaluationResultStore:
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self._initialize()

    def _initialize(self) -> None:
        Path(self.db_path).touch(exist_ok=True)

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluation_runs (
                    run_id TEXT PRIMARY KEY,
                    total_cases INTEGER NOT NULL,
                    passed INTEGER NOT NULL,
                    failed INTEGER NOT NULL,
                    average_latency_ms REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluation_case_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    answer TEXT NOT NULL,
                    citation_count INTEGER NOT NULL,
                    checks_json TEXT NOT NULL,
                    failures_json TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    document_id TEXT,
                    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id)
                )
                """
            )

            connection.commit()

    def save_summary(self, summary: DocumentQAEvalSummary) -> StoredEvaluationRun:
        run_id = f"eval-{uuid4().hex[:12]}"
        created_at = self._now()

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO evaluation_runs (
                    run_id,
                    total_cases,
                    passed,
                    failed,
                    average_latency_ms,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    summary.total_cases,
                    summary.passed,
                    summary.failed,
                    summary.average_latency_ms,
                    created_at,
                ),
            )

            for result in summary.results:
                self._insert_case_result(
                    cursor=cursor,
                    run_id=run_id,
                    result=result,
                )

            connection.commit()

        return StoredEvaluationRun(
            run_id=run_id,
            total_cases=summary.total_cases,
            passed=summary.passed,
            failed=summary.failed,
            average_latency_ms=summary.average_latency_ms,
            created_at=created_at,
        )

    def get_latest_run(self) -> StoredEvaluationRun | None:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    run_id,
                    total_cases,
                    passed,
                    failed,
                    average_latency_ms,
                    created_at
                FROM evaluation_runs
                ORDER BY created_at DESC
                LIMIT 1
                """
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_run(row)

    def get_case_results(self, run_id: str) -> list[StoredEvaluationCaseResult]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    run_id,
                    name,
                    passed,
                    answer,
                    citation_count,
                    checks_json,
                    failures_json,
                    latency_ms,
                    document_id
                FROM evaluation_case_results
                WHERE run_id = ?
                ORDER BY id ASC
                """,
                (run_id,),
            )

            rows = cursor.fetchall()

        return [
            self._row_to_case_result(row)
            for row in rows
        ]

    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM evaluation_case_results")
            cursor.execute("DELETE FROM evaluation_runs")
            connection.commit()

    def _insert_case_result(
        self,
        cursor: sqlite3.Cursor,
        run_id: str,
        result: DocumentQAEvalCaseResult,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO evaluation_case_results (
                run_id,
                name,
                passed,
                answer,
                citation_count,
                checks_json,
                failures_json,
                latency_ms,
                document_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                result.name,
                1 if result.passed else 0,
                result.answer,
                result.citation_count,
                json.dumps(result.checks),
                json.dumps(result.failures),
                result.latency_ms,
                result.document_id,
            ),
        )

    def _row_to_run(self, row: tuple[object, ...]) -> StoredEvaluationRun:
        return StoredEvaluationRun(
            run_id=str(row[0]),
            total_cases=int(row[1]),
            passed=int(row[2]),
            failed=int(row[3]),
            average_latency_ms=float(row[4]),
            created_at=str(row[5]),
        )

    def _row_to_case_result(
        self,
        row: tuple[object, ...],
    ) -> StoredEvaluationCaseResult:
        return StoredEvaluationCaseResult(
            run_id=str(row[0]),
            name=str(row[1]),
            passed=bool(row[2]),
            answer=str(row[3]),
            citation_count=int(row[4]),
            checks=json.loads(str(row[5])),
            failures=json.loads(str(row[6])),
            latency_ms=float(row[7]),
            document_id=None if row[8] is None else str(row[8]),
        )

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


sqlite_evaluation_result_store = SQLiteEvaluationResultStore(
    db_path=os.getenv("APP_DB_PATH", "app.db")
)