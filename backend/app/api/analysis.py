from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import get_db
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, GeneratePatchRequest, GeneratePatchResponse
from app.services.conversation_service import ConversationService
from app.services.deepseek_service import DeepSeekService
from app.services.llm_service import LLMService
from app.services.mcp_service import MCPService
from app.services.patch_orchestrator import PatchOrchestrator
from app.services.repo_analyzer import RepoAnalyzer

router = APIRouter(prefix="/api", tags=["analysis"])

llm_service = LLMService()
deepseek_service = DeepSeekService()
patch_orchestrator = PatchOrchestrator(llm_service, deepseek_service)
mcp_service = MCPService()
repo_analyzer = RepoAnalyzer()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repo(request: AnalyzeRequest):
    repo_path, source = _resolve_repo_path(request.repo_path, request.github_url)
    summary = repo_analyzer.analyze(repo_path, focus=request.focus)
    return AnalyzeResponse(repo_summary=summary, repo_path=repo_path, source=source)


@router.post("/generate_patch", response_model=GeneratePatchResponse)
async def generate_patch(request: GeneratePatchRequest, db: AsyncSession = Depends(get_db)):
    repo_path, _ = _resolve_repo_path(request.repo_path, request.github_url)

    if request.conversation_id:
        conversation = await ConversationService.get_active_conversation(db, request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conversation_id = conversation.id
    else:
        conversation = await ConversationService.create_conversation(
            db, title=request.feature_request[:50]
        )
        conversation_id = conversation.id

    await ConversationService.add_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=request.feature_request,
        meta_info={"repo_path": repo_path},
    )

    history = await ConversationService.get_conversation_history(db, conversation_id)
    mcp_context = mcp_service.build_context(
        question=request.feature_request,
        conversation_history=history,
        user_profile={},
    )

    result = await patch_orchestrator.generate(
        request=request.feature_request,
        repo_path=repo_path,
        mcp_context=mcp_context,
    )

    await ConversationService.add_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=result.patch,
        meta_info={
            "intent": result.intent,
            "architecture": result.architecture,
            "repo_summary": result.repo_summary,
        },
    )

    return GeneratePatchResponse(
        conversation_id=conversation_id,
        patch=result.patch,
        intent=result.intent,
        architecture=result.architecture,
        repo_summary=result.repo_summary,
    )


def _resolve_repo_path(repo_path: str | None, github_url: str | None) -> tuple[str, str]:
    if repo_path:
        resolved = str(Path(repo_path).expanduser().resolve())
        return resolved, "local_path"

    if github_url:
        target_dir = Path(settings.QDRANT_PATH).parent / "uploads" / f"repo-{uuid.uuid4()}"
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", github_url, str(target_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to clone repository: {exc.stderr.strip() or exc.stdout.strip()}",
            ) from exc
        return str(target_dir), "github_url"

    raise HTTPException(status_code=400, detail="repo_path or github_url is required")
