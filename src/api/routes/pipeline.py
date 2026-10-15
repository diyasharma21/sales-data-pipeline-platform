from datetime import datetime
import math
from pathlib import Path
import shutil
from typing import Any, List, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from sqlalchemy import text

from main import run_pipeline
from src.api.schemas import (
    PaginatedResponse,
    PipelineOverviewSummary,
    PipelineRunItem,
    PipelineTriggerRequest,
    PipelineTriggerResponse,
    RemoteSyncRequest,
    RemoteSyncResponse,
)
from src.config import RAW_DATA_DIR
from src.connectors.remote_api import sync_from_remote_api
from src.connectors.remote_db import sync_from_remote_database
from src.load import get_db_engine

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])


def _parse_dt(val: Any) -> Optional[datetime]:
    """Helper to convert string or datetime to datetime object."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val))
    except Exception:
        return None


@router.get("/summary", response_model=PipelineOverviewSummary)
def get_pipeline_summary() -> PipelineOverviewSummary:
    """Retrieve operational pipeline health summary and run counts."""
    engine = get_db_engine()
    sql_counts = """
        SELECT 
            COUNT(*) AS total_runs,
            COALESCE(SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END), 0) AS successful_runs,
            COALESCE(SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END), 0) AS failed_runs,
            COALESCE(SUM(CASE WHEN status = 'PARTIAL_SUCCESS' THEN 1 ELSE 0 END), 0) AS partial_runs
        FROM pipeline_runs;
    """
    sql_last_success = """
        SELECT MAX(end_time) AS last_success
        FROM pipeline_runs
        WHERE status IN ('SUCCESS', 'PARTIAL_SUCCESS');
    """
    sql_latest_run = """
        SELECT 
            run_id, start_time, end_time, source_file,
            total_records_extracted, records_accepted, records_rejected,
            records_loaded, status, error_message
        FROM pipeline_runs
        ORDER BY start_time DESC
        LIMIT 1;
    """
    try:
        with engine.connect() as conn:
            counts = conn.execute(text(sql_counts)).mappings().first()
            raw_last_success = conn.execute(text(sql_last_success)).scalar()
            last_success = _parse_dt(raw_last_success)
            latest = conn.execute(text(sql_latest_run)).mappings().first()

            latest_item = None
            if latest:
                s_time = _parse_dt(latest["start_time"])
                e_time = _parse_dt(latest["end_time"])
                dur = None
                if s_time and e_time:
                    dur = round((e_time - s_time).total_seconds(), 2)

                latest_item = PipelineRunItem(
                    run_id=latest["run_id"],
                    start_time=s_time or datetime.now(),
                    end_time=e_time,
                    source_file=latest["source_file"],
                    total_records_extracted=int(latest["total_records_extracted"]),
                    records_accepted=int(latest["records_accepted"]),
                    records_rejected=int(latest["records_rejected"]),
                    records_loaded=int(latest["records_loaded"]),
                    status=latest["status"],
                    duration_seconds=dur,
                    error_message=latest["error_message"],
                )

            return PipelineOverviewSummary(
                total_runs=int(counts["total_runs"] or 0),
                successful_runs=int(counts["successful_runs"] or 0),
                failed_runs=int(counts["failed_runs"] or 0),
                partial_runs=int(counts["partial_runs"] or 0),
                last_successful_run=last_success,
                latest_run=latest_item,
            )
    finally:
        engine.dispose()


@router.get("/runs", response_model=PaginatedResponse[PipelineRunItem])
def get_pipeline_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
) -> PaginatedResponse[PipelineRunItem]:
    """Retrieve historical pipeline runs with execution metrics."""
    engine = get_db_engine()

    where_clauses = []
    params = {}

    if status and status.strip():
        where_clauses.append("status = :status")
        params["status"] = status.strip().upper()

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    offset = (page - 1) * page_size

    count_sql = f"SELECT COUNT(*) FROM pipeline_runs {where_sql};"
    data_sql = f"""
        SELECT 
            run_id, start_time, end_time, source_file,
            total_records_extracted, records_accepted, records_rejected,
            records_loaded, status, error_message
        FROM pipeline_runs
        {where_sql}
        ORDER BY start_time DESC
        LIMIT :limit OFFSET :offset;
    """
    params["limit"] = page_size
    params["offset"] = offset

    try:
        with engine.connect() as conn:
            total_count = conn.execute(text(count_sql), params).scalar() or 0
            rows = conn.execute(text(data_sql), params).mappings().fetchall()

            total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

            items = []
            for row in rows:
                s_time = _parse_dt(row["start_time"])
                e_time = _parse_dt(row["end_time"])
                dur = None
                if s_time and e_time:
                    dur = round((e_time - s_time).total_seconds(), 2)

                items.append(
                    PipelineRunItem(
                        run_id=row["run_id"],
                        start_time=s_time or datetime.now(),
                        end_time=e_time,
                        source_file=row["source_file"],
                        total_records_extracted=int(row["total_records_extracted"]),
                        records_accepted=int(row["records_accepted"]),
                        records_rejected=int(row["records_rejected"]),
                        records_loaded=int(row["records_loaded"]),
                        status=row["status"],
                        duration_seconds=dur,
                        error_message=row["error_message"],
                    )
                )

            return PaginatedResponse[PipelineRunItem](
                items=items,
                total=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )
    finally:
        engine.dispose()


@router.get("/files")
def get_available_raw_files():
    """List available raw CSV files in data/raw for triggering runs."""
    files = []
    for p in RAW_DATA_DIR.glob("*.csv"):
        files.append({
            "filename": p.name,
            "size_bytes": p.stat().st_size,
            "modified_at": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
        })
    return {"files": files}


@router.post("/run", response_model=PipelineTriggerResponse)
def trigger_pipeline_run(payload: PipelineTriggerRequest) -> PipelineTriggerResponse:
    """Securely execute the ETL pipeline against a specified raw data file.

    Sanitizes filename strictly against path traversal attacks.
    """
    safe_filename = Path(payload.filename).name
    target_path = RAW_DATA_DIR / safe_filename

    if not target_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Source file '{safe_filename}' not found in data/raw/",
        )

    exit_code = run_pipeline(
        input_file=target_path,
        export_csv=True,
    )

    if exit_code == 0:
        return PipelineTriggerResponse(
            status="SUCCESS",
            message=f"Pipeline executed successfully for '{safe_filename}'.",
            exit_code=exit_code,
            filename=safe_filename,
        )
    else:
        return PipelineTriggerResponse(
            status="FAILED",
            message=f"Pipeline execution encountered errors for '{safe_filename}'.",
            exit_code=exit_code,
            filename=safe_filename,
        )


@router.post("/upload")
async def upload_pipeline_file(file: UploadFile = File(...)):
    """Upload a new CSV file directly to data/raw/ directory for processing."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only .csv files are supported.",
        )

    safe_name = Path(file.filename).name
    target_path = RAW_DATA_DIR / safe_name

    try:
        with target_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {str(exc)}",
        )

    return {
        "status": "SUCCESS",
        "filename": safe_name,
        "size_bytes": target_path.stat().st_size,
        "message": f"File '{safe_name}' uploaded successfully to data/raw/.",
    }


@router.post("/sync", response_model=RemoteSyncResponse)
def trigger_remote_sync(payload: RemoteSyncRequest) -> RemoteSyncResponse:
    """Execute on-demand sync from a remote database server or REST API."""
    try:
        if payload.source_type == "db":
            loaded = sync_from_remote_database(
                remote_db_url=payload.remote_url,
                days_back=payload.days_back,
            )
            return RemoteSyncResponse(
                status="SUCCESS",
                message=f"Successfully extracted, validated and synced {loaded} records from remote database.",
                records_synced=loaded,
            )
        elif payload.source_type == "api":
            loaded = sync_from_remote_api(
                api_url=payload.remote_url,
                api_key=payload.api_key,
                days_back=payload.days_back,
            )
            return RemoteSyncResponse(
                status="SUCCESS",
                message=f"Successfully fetched, validated and synced {loaded} records from remote API.",
                records_synced=loaded,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source_type '{payload.source_type}'. Choose 'db' or 'api'.",
            )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Remote synchronization failed: {str(exc)}",
        )
