"""
app/tasks/ingestion_tasks.py — Dataset ingestion background task.
"""
from __future__ import annotations

from app.tasks.celery_app import celery_app


@celery_app.task(name="tasks.process_dataset")
def process_dataset_task(dataset_id: str, file_path: str):
    """
    Parse uploaded CSV/JSON, validate schema, update Dataset record.
    """
    import json
    import asyncio
    from pathlib import Path
    from datetime import datetime

    path = Path(file_path)
    status = "ready"
    row_count = None
    schema_info = {}
    error_msg = None

    try:
        if path.suffix.lower() == ".csv":
            import pandas as pd
            df = pd.read_csv(path)
            row_count   = int(len(df))
            schema_info = {
                "columns": list(df.columns),
                "dtypes":  df.dtypes.astype(str).to_dict(),
            }
        elif path.suffix.lower() == ".json":
            data = json.loads(path.read_text())
            if isinstance(data, list):
                row_count = len(data)
                schema_info = {"type": "array", "keys": list(data[0].keys()) if data else []}
            else:
                row_count   = 1
                schema_info = {"type": "object", "keys": list(data.keys())}
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

    except Exception as exc:
        status    = "failed"
        error_msg = str(exc)

    # Update DB record (synchronous via asyncio.run)
    async def _update():
        from app.database import AsyncSessionLocal
        from app.models.dataset import Dataset
        from sqlalchemy import update
        import uuid
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Dataset)
                .where(Dataset.id == uuid.UUID(dataset_id))
                .values(
                    status=status,
                    row_count=row_count,
                    schema_info=schema_info,
                    error_msg=error_msg,
                    processed_at=datetime.utcnow(),
                )
            )
            await db.commit()

    try:
        asyncio.run(_update())
    except Exception:
        pass   # DB update best-effort

    return {"dataset_id": dataset_id, "status": status, "row_count": row_count}
