import logging
import re
from typing import Annotated
import time
from uuid import uuid4

from auth import require_api_key
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from models.health import HealthResponse
from services.exceptions import AppServiceError, NotFoundError

from models.routing import RouteRequest, RouteResponse
from services.routing_service import RoutingService
from services.rule_based_router import RuleBasedRouter

from models.extraction import ExtractRequest, ExtractResponse
from services.extractor import get_extractor
from services.extraction_service import ExtractionService

from models.classification import ClassifyRequest, ClassifyResponse
from services.classification_service import ClassificationService
from services.rule_based_classifier import RuleBasedClassifier

from models.summarization import SummarizeRequest, SummarizeResponse
from services.rule_based_summarizer import RuleBasedSummarizer
from services.summarization_service import SummarizationService

from models.answering import AnswerRequest, AnswerResponse
from services.answering_service import AnsweringService
from services.rule_based_answerer import RuleBasedAnswerer

from models.document_qa import (
    DocumentAskRequest,
    DocumentAskResponse,
    DocumentIngestionJobResponse,
    DocumentUploadResponse,
)

from services.document_answering_service import DocumentAnsweringService
from services.retrieval_service import RetrievalService
from providers.embedding_provider import embedding_provider

from models.chat import ChatRequest, ChatResponse
from services.chat_service import ChatService
from services.rule_based_chatbot import RuleBasedChatbot

from services.sqlite_document_store import sqlite_document_store

from services.document_ingestion_service import DocumentIngestionService
from services.ingestion_job_store import SQLiteIngestionJobStore, sqlite_ingestion_job_store
from services.document_ingestion_worker import DocumentIngestionWorker

from models.tool_assistant import ToolAssistantRequest, ToolAssistantResponse
from services.tool_assistant_service import ToolAssistantService

from models.evaluation import (
    DocumentQAEvalLatestRunResponse,
    DocumentQAEvalStoredCaseResultResponse,
)

from services.evaluation_result_store import (
    SQLiteEvaluationResultStore,
    sqlite_evaluation_result_store,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", uuid4().hex[:12])
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.exception(
            "Request failed method=%s path=%s duration_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            duration_ms,
            request_id,
        )

        raise

    duration_ms = (time.perf_counter() - start_time) * 1000

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "Request completed method=%s path=%s status_code=%s duration_ms=%.2f request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )

    return response

class UserInput(BaseModel):
    name: str = Field(min_length=1)
    age: int = Field(ge=0, le=120)


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class TextAnalysisResponse(BaseModel):
    original_text: str
    character_count: int
    word_count: int
    sentence_count: int
    unique_words: int
    preview: str

def get_routing_service() -> RoutingService:
    router = RuleBasedRouter()
    return RoutingService(router)


RoutingServiceDependency = Annotated[
    RoutingService,
    Depends(get_routing_service)
]

def get_extraction_service() -> ExtractionService:
    extractor = get_extractor()
    return ExtractionService(extractor)


ExtractionServiceDependency = Annotated[
    ExtractionService,
    Depends(get_extraction_service)
]

def get_classification_service() -> ClassificationService:
    classifier = RuleBasedClassifier()
    return ClassificationService(classifier)


ClassificationServiceDependency = Annotated[
    ClassificationService,
    Depends(get_classification_service)
]

def get_summarization_service() -> SummarizationService:
    summarizer = RuleBasedSummarizer()
    return SummarizationService(summarizer)


SummarizationServiceDependency = Annotated[
    SummarizationService,
    Depends(get_summarization_service)
]

def get_answering_service() -> AnsweringService:
    answerer = RuleBasedAnswerer()
    return AnsweringService(answerer)


AnsweringServiceDependency = Annotated[
    AnsweringService,
    Depends(get_answering_service)
]

def get_tool_assistant_service() -> ToolAssistantService:
    return ToolAssistantService()

def get_document_ingestion_service() -> DocumentIngestionService:
    return DocumentIngestionService(
        store=sqlite_document_store,
        embedding_provider=embedding_provider,
    )

DocumentIngestionServiceDependency = Annotated[
    DocumentIngestionService,
    Depends(get_document_ingestion_service),
]

def get_ingestion_job_store() -> SQLiteIngestionJobStore:
    return sqlite_ingestion_job_store

IngestionJobStoreDependency = Annotated[
    SQLiteIngestionJobStore,
    Depends(get_ingestion_job_store),
]

def get_evaluation_result_store() -> SQLiteEvaluationResultStore:
    return sqlite_evaluation_result_store


EvaluationResultStoreDependency = Annotated[
    SQLiteEvaluationResultStore,
    Depends(get_evaluation_result_store),
]

def get_document_ingestion_worker(
    ingestion_service: DocumentIngestionServiceDependency,
    job_store: IngestionJobStoreDependency,
) -> DocumentIngestionWorker:
    return DocumentIngestionWorker(
        ingestion_service=ingestion_service,
        job_store=job_store,
    )


DocumentIngestionWorkerDependency = Annotated[
    DocumentIngestionWorker,
    Depends(get_document_ingestion_worker),
]

def get_document_answering_service() -> DocumentAnsweringService:
    return DocumentAnsweringService(
        store=sqlite_document_store,
        retrieval_service=RetrievalService(embedding_provider),
        answerer=RuleBasedAnswerer(),
    )

DocumentAnsweringServiceDependency = Annotated[
    DocumentAnsweringService,
    Depends(get_document_answering_service),
]

def get_chat_service() -> ChatService:
    chatbot = RuleBasedChatbot()
    return ChatService(chatbot)


ChatServiceDependency = Annotated[
    ChatService,
    Depends(get_chat_service),
]


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/greet")
def greet(user: UserInput) -> dict[str, str]:
    return {"message": f"Hello {user.name}, age {user.age}"}


@app.post("/analyze", response_model=TextAnalysisResponse)
def analyze_text(request: TextRequest) -> TextAnalysisResponse:
    text = request.text.strip()

    words = re.findall(r"\b\w+\b", text.lower())
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]

    return TextAnalysisResponse(
        original_text=text,
        character_count=len(text),
        word_count=len(words),
        sentence_count=len(sentences),
        unique_words=len(set(words)),
        preview=text[:80],
    )

@app.post("/route", response_model=RouteResponse)
async def route_request(
    request: RouteRequest,
    routing_service: RoutingServiceDependency,
) -> RouteResponse:
    try:
        return await routing_service.route(request.user_input)
    except AppServiceError as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex
    
@app.post(
    "/extract",
    response_model=ExtractResponse,
    dependencies=[Depends(require_api_key)],
)
async def extract_fields(
    request: ExtractRequest,
    extraction_service: ExtractionServiceDependency,
) -> ExtractResponse:
    try:
        return await extraction_service.extract(request.text)
    except AppServiceError as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex

@app.post("/classify", response_model=ClassifyResponse)
async def classify_text(
    request: ClassifyRequest,
    classification_service: ClassificationServiceDependency,
) -> ClassifyResponse:
    try:
        return await classification_service.classify(request.text)
    except AppServiceError as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_text(
    request: SummarizeRequest,
    summarization_service: SummarizationServiceDependency,
) -> SummarizeResponse:
    try:
        return await summarization_service.summarize(
            request.text,
            request.max_sentences,
        )
    except AppServiceError as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex

@app.post(
    "/answer",
    response_model=AnswerResponse,
    dependencies=[Depends(require_api_key)],
)
async def answer_question(
    request: AnswerRequest,
    answering_service: AnsweringServiceDependency,
) -> AnswerResponse:
    try:
        return await answering_service.answer(
            request.question,
            request.context,
        )
    except AppServiceError as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex


@app.post(
    "/documents/upload",
    response_model=DocumentIngestionJobResponse,
    dependencies=[Depends(require_api_key)],
)
async def upload_document(
    background_tasks: BackgroundTasks,
    ingestion_worker: DocumentIngestionWorkerDependency,
    file: UploadFile = File(...),
) -> DocumentIngestionJobResponse:
    filename = file.filename or "uploaded.txt"

    if not filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported.")

    raw_bytes = await file.read()

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as ex:
        raise HTTPException(
            status_code=400,
            detail="Document must be valid UTF-8 text.",
        ) from ex

    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded document is empty.")

    queued_job = ingestion_worker.create_text_upload_job(filename)

    background_tasks.add_task(
        ingestion_worker.process_existing_text_upload_job_safely,
        queued_job.job_id,
        filename,
        text,
    )

    return DocumentIngestionJobResponse(
        job_id=queued_job.job_id,
        filename=queued_job.filename,
        status=queued_job.status,
        document_id=queued_job.document_id,
        chunk_count=queued_job.chunk_count,
        error_message=queued_job.error_message,
        created_at=queued_job.created_at,
        updated_at=queued_job.updated_at,
    )

@app.get(
    "/documents/jobs/{job_id}",
    response_model=DocumentIngestionJobResponse,
    dependencies=[Depends(require_api_key)],
)
async def get_document_ingestion_job(
    job_id: str,
    job_store: IngestionJobStoreDependency,
) -> DocumentIngestionJobResponse:
    job = job_store.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Ingestion job not found.")

    return DocumentIngestionJobResponse(
        job_id=job.job_id,
        filename=job.filename,
        status=job.status,
        document_id=job.document_id,
        chunk_count=job.chunk_count,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@app.post(
    "/documents/ask",
    response_model=DocumentAskResponse,
    dependencies=[Depends(require_api_key)],
)
async def ask_document_question(
    request: DocumentAskRequest,
    document_answering_service: DocumentAnsweringServiceDependency,
) -> DocumentAskResponse:
    try:
        return await document_answering_service.answer(
            document_id=request.document_id,
            question=request.question,
            top_k=request.top_k,
        )
    except AppServiceError as ex:
        if str(ex) == "Document not found.":
            raise HTTPException(status_code=404, detail=str(ex)) from ex

        raise HTTPException(status_code=500, detail=str(ex)) from ex
@app.post(
    "/tool-assistant",
    response_model=ToolAssistantResponse,
    dependencies=[Depends(require_api_key)],
)
async def tool_assistant(
    request: ToolAssistantRequest,
    service: ToolAssistantService = Depends(get_tool_assistant_service),
) -> ToolAssistantResponse:
    result = await service.answer(request.message)
    return ToolAssistantResponse(**result)

@app.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(require_api_key)],
)
async def chat(
    request: ChatRequest,
    chat_service: ChatServiceDependency,
) -> ChatResponse:
    try:
        return await chat_service.chat(request.message)
    except AppServiceError as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex

@app.get(
    "/evals/document-qa/latest",
    response_model=DocumentQAEvalLatestRunResponse,
    dependencies=[Depends(require_api_key)],
)
async def get_latest_document_qa_eval(
    evaluation_result_store: EvaluationResultStoreDependency,
) -> DocumentQAEvalLatestRunResponse:
    latest_run = evaluation_result_store.get_latest_run()

    if latest_run is None:
        raise HTTPException(
            status_code=404,
            detail="No document QA evaluation runs found.",
        )

    case_results = evaluation_result_store.get_case_results(latest_run.run_id)

    return DocumentQAEvalLatestRunResponse(
        run_id=latest_run.run_id,
        total_cases=latest_run.total_cases,
        passed=latest_run.passed,
        failed=latest_run.failed,
        average_latency_ms=latest_run.average_latency_ms,
        created_at=latest_run.created_at,
        results=[
            DocumentQAEvalStoredCaseResultResponse(
                name=result.name,
                passed=result.passed,
                answer=result.answer,
                citation_count=result.citation_count,
                checks=result.checks,
                failures=result.failures,
                latency_ms=result.latency_ms,
                document_id=result.document_id,
            )
            for result in case_results
        ],
    )