"""
app/routers/laws.py — Laws endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.exceptions import NotFoundError
from app.data.seed import get_registry

router = APIRouter()


@router.get("/")
async def list_laws():
    df = get_registry().df_laws
    return df.to_dict(orient="records")


@router.get("/category/{category}")
async def laws_by_category(category: str):
    df  = get_registry().df_laws
    out = df[df["category"].str.lower() == category.lower()]
    return out.to_dict(orient="records")


@router.get("/{law_id}")
async def get_law(law_id: str):
    df  = get_registry().df_laws
    row = df[df["law_id"] == law_id]
    if row.empty:
        raise NotFoundError("Law")
    return row.iloc[0].to_dict()
