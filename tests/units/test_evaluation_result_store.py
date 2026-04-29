from models.evaluation import DocumentQAEvalCaseResult, DocumentQAEvalSummary
from services.evaluation_result_store import SQLiteEvaluationResultStore


def _build_summary() -> DocumentQAEvalSummary:
    return DocumentQAEvalSummary(
        total_cases=2,
        passed=1,
        failed=1,
        average_latency_ms=12.5,
        results=[
            DocumentQAEvalCaseResult(
                name="passing_case",
                passed=True,
                answer="FastAPI is the backend framework.",
                citation_count=1,
                checks=["Answer contains 'FastAPI'."],
                failures=[],
                latency_ms=10.0,
                document_id="doc-123",
            ),
            DocumentQAEvalCaseResult(
                name="failing_case",
                passed=False,
                answer="I could not find the answer.",
                citation_count=0,
                checks=[],
                failures=["Answer does not contain 'Django'."],
                latency_ms=15.0,
                document_id=None,
            ),
        ],
    )


def test_save_summary_stores_evaluation_run(tmp_path):
    store = SQLiteEvaluationResultStore(str(tmp_path / "test_eval.db"))
    summary = _build_summary()

    stored_run = store.save_summary(summary)

    assert stored_run.run_id.startswith("eval-")
    assert stored_run.total_cases == 2
    assert stored_run.passed == 1
    assert stored_run.failed == 1
    assert stored_run.average_latency_ms == 12.5
    assert stored_run.created_at


def test_get_latest_run_returns_most_recent_run(tmp_path):
    store = SQLiteEvaluationResultStore(str(tmp_path / "test_eval.db"))

    first_run = store.save_summary(_build_summary())
    second_run = store.save_summary(_build_summary())

    latest_run = store.get_latest_run()

    assert latest_run == second_run
    assert latest_run != first_run


def test_get_latest_run_returns_none_when_no_runs_exist(tmp_path):
    store = SQLiteEvaluationResultStore(str(tmp_path / "test_eval.db"))

    latest_run = store.get_latest_run()

    assert latest_run is None


def test_get_case_results_returns_results_for_run(tmp_path):
    store = SQLiteEvaluationResultStore(str(tmp_path / "test_eval.db"))
    summary = _build_summary()

    stored_run = store.save_summary(summary)
    case_results = store.get_case_results(stored_run.run_id)

    assert len(case_results) == 2

    passing_case = case_results[0]
    assert passing_case.run_id == stored_run.run_id
    assert passing_case.name == "passing_case"
    assert passing_case.passed is True
    assert passing_case.answer == "FastAPI is the backend framework."
    assert passing_case.citation_count == 1
    assert passing_case.checks == ["Answer contains 'FastAPI'."]
    assert passing_case.failures == []
    assert passing_case.latency_ms == 10.0
    assert passing_case.document_id == "doc-123"

    failing_case = case_results[1]
    assert failing_case.run_id == stored_run.run_id
    assert failing_case.name == "failing_case"
    assert failing_case.passed is False
    assert failing_case.answer == "I could not find the answer."
    assert failing_case.citation_count == 0
    assert failing_case.checks == []
    assert failing_case.failures == ["Answer does not contain 'Django'."]
    assert failing_case.latency_ms == 15.0
    assert failing_case.document_id is None


def test_get_case_results_returns_empty_list_for_unknown_run(tmp_path):
    store = SQLiteEvaluationResultStore(str(tmp_path / "test_eval.db"))

    case_results = store.get_case_results("eval-missing")

    assert case_results == []


def test_clear_removes_runs_and_case_results(tmp_path):
    store = SQLiteEvaluationResultStore(str(tmp_path / "test_eval.db"))

    stored_run = store.save_summary(_build_summary())

    store.clear()

    assert store.get_latest_run() is None
    assert store.get_case_results(stored_run.run_id) == []