from fastapi import APIRouter
from pydantic import BaseModel

from backend.models.responses import PatternEngineResponse
from backend.services.pattern_engine_runner import run_pattern_engine

router = APIRouter(prefix="/api/run", tags=["pattern_engine"])


class PatternEngineRequest(BaseModel):
    last_n: int = 500
    select_top: float = 0.3
    output_selected_only: bool = True


@router.post("/pattern-engine", response_model=PatternEngineResponse)
async def run_engine(payload: PatternEngineRequest) -> PatternEngineResponse:
    result = run_pattern_engine(
        last_n=payload.last_n,
        select_top=payload.select_top,
        output_selected_only=payload.output_selected_only,
    )
    return PatternEngineResponse(**result)
