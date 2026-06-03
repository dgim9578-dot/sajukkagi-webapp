"""사주 브리핑 REST API."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import saju_storage

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


class SajuBriefingRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=64)
    birth: dict[str, Any]
    gapja: list[str] = Field(..., min_length=3)
    consultation_type: str = "general"
    session_id: str | None = None


class SajuBriefingResponse(BaseModel):
    success: bool
    fingerprint: str = ""
    briefing: dict[str, Any] = Field(default_factory=dict)
    message: str = ""


class BriefingLoadResponse(BaseModel):
    success: bool
    briefing: dict[str, Any] = Field(default_factory=dict)
    message: str = ""


class MatchBriefingRequest(BaseModel):
    user_name: str = Field(..., min_length=1, max_length=64)
    user_birth: dict[str, Any]
    user_gapja: list[str] = Field(..., min_length=3)
    partner_name: str = Field(..., min_length=1, max_length=64)
    partner_birth: dict[str, Any]
    partner_gapja: list[str] = Field(..., min_length=3)
    match_score: int = Field(70, ge=0, le=100)
    day_branch_rel: str = ""


@router.post("/generate", response_model=SajuBriefingResponse)
async def generate_briefing(req: SajuBriefingRequest) -> SajuBriefingResponse:
    """사주 입력 후 인터랙티브 브리핑 데이터 생성."""
    try:
        briefing_data = saju_storage.generate_saju_briefing(
            display_name=req.display_name.strip(),
            birth=req.birth,
            gapja=list(req.gapja),
            consultation_type=req.consultation_type,
        )
        if req.session_id:
            saju_storage.archive_append_record(
                {
                    "session_id": req.session_id,
                    "type": "briefing_complete",
                    "display_name": req.display_name.strip(),
                    "consultation_type": req.consultation_type,
                    "briefing_result": briefing_data,
                    "briefing_summary": {
                        "day_master": (briefing_data.get("overview") or {}).get(
                            "day_master"
                        ),
                        "main_keywords": (briefing_data.get("overview") or {}).get(
                            "main_keywords"
                        ),
                    },
                }
            )
        return SajuBriefingResponse(
            success=True,
            fingerprint=str(briefing_data.get("fingerprint") or ""),
            briefing=briefing_data,
            message="브리핑이 성공적으로 생성되었습니다.",
        )
    except Exception:
        log.exception("Briefing generation failed")
        raise HTTPException(status_code=500, detail="브리핑 생성 실패") from None


@router.post("/get", response_model=SajuBriefingResponse)
async def get_briefing_body(req: SajuBriefingRequest) -> SajuBriefingResponse:
    """프론트엔드용 — 오류 시 최소 fallback 포함."""
    briefing_data = saju_storage.get_user_briefing(
        req.display_name.strip(),
        req.birth,
        list(req.gapja),
        consultation_type=req.consultation_type,
    )
    if briefing_data.get("error"):
        raise HTTPException(
            status_code=500,
            detail=str(briefing_data.get("error") or "브리핑 생성 실패"),
        )
    return SajuBriefingResponse(
        success=True,
        fingerprint=str(briefing_data.get("fingerprint") or ""),
        briefing=briefing_data,
        message="브리핑이 성공적으로 생성되었습니다.",
    )


@router.get("/sample", response_model=BriefingLoadResponse)
async def get_sample() -> BriefingLoadResponse:
    """개발/테스트용 샘플 브리핑."""
    return BriefingLoadResponse(
        success=True,
        briefing=saju_storage.get_sample_briefing(),
        message="샘플 브리핑입니다.",
    )


@router.get("/get/{fingerprint}", response_model=BriefingLoadResponse)
async def get_briefing(fingerprint: str) -> BriefingLoadResponse:
    """저장된 프로필 간지로 브리핑 재생성."""
    fp = str(fingerprint or "").strip()
    if not fp:
        raise HTTPException(status_code=400, detail="fingerprint가 비어 있습니다.")
    if fp == "test_sample_123":
        return BriefingLoadResponse(
            success=True,
            briefing=saju_storage.get_sample_briefing(),
            message="샘플 브리핑입니다.",
        )
    cached = saju_storage.load_cached_briefing(fp)
    briefing = cached or saju_storage.get_briefing_by_fingerprint(fp)
    if not briefing:
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")
    return BriefingLoadResponse(
        success=True,
        briefing=briefing,
        message="브리핑을 불러왔습니다.",
    )


@router.post("/generate/match", response_model=SajuBriefingResponse)
async def generate_match_briefing(req: MatchBriefingRequest) -> SajuBriefingResponse:
    """궁합(STEP4) 전용 브리핑 덱 생성."""
    try:
        briefing_data = saju_storage.generate_match_briefing(
            user_name=req.user_name.strip(),
            user_birth=req.user_birth,
            user_gapja=list(req.user_gapja),
            partner_name=req.partner_name.strip(),
            partner_birth=req.partner_birth,
            partner_gapja=list(req.partner_gapja),
            match_score=req.match_score,
            day_branch_rel=req.day_branch_rel,
        )
        return SajuBriefingResponse(
            success=True,
            fingerprint=str(briefing_data.get("fingerprint") or ""),
            briefing=briefing_data,
            message="궁합 브리핑이 생성되었습니다.",
        )
    except Exception:
        log.exception("Match briefing generation failed")
        raise HTTPException(status_code=500, detail="궁합 브리핑 생성 실패") from None


@router.get("/get/match/{fingerprint}", response_model=BriefingLoadResponse)
async def get_match_briefing(fingerprint: str) -> BriefingLoadResponse:
    """캐시된 궁합 브리핑 조회."""
    fp = str(fingerprint or "").strip()
    if not fp:
        raise HTTPException(status_code=400, detail="fingerprint가 비어 있습니다.")
    cached = saju_storage.load_cached_briefing(fp)
    if not cached or str(cached.get("consultation_type") or "") != "match":
        raise HTTPException(status_code=404, detail="궁합 브리핑을 찾을 수 없습니다.")
    return BriefingLoadResponse(
        success=True,
        briefing=cached,
        message="궁합 브리핑을 불러왔습니다.",
    )
