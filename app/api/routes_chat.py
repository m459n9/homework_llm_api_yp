from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_chat_usecase, get_current_user_id
from app.core.errors import ExternalServiceError
from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse
from app.usecases.chat import ChatUseCase

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    uc: Annotated[ChatUseCase, Depends(get_chat_usecase)],
):
    try:
        answer = await uc.ask(
            user_id=user_id,
            prompt=body.prompt,
            system=body.system,
            max_history=body.max_history,
            temperature=body.temperature,
        )
    except ExternalServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=exc.detail,
        )
    return ChatResponse(answer=answer)


@router.get("/history", response_model=ChatHistoryResponse)
async def history(
    user_id: Annotated[int, Depends(get_current_user_id)],
    uc: Annotated[ChatUseCase, Depends(get_chat_usecase)],
    limit: int = Query(default=50, ge=1, le=200),
):
    items = await uc.get_history(user_id, limit)
    return ChatHistoryResponse(items=items)


@router.delete("/history", status_code=status.HTTP_200_OK)
async def clear_history(
    user_id: Annotated[int, Depends(get_current_user_id)],
    uc: Annotated[ChatUseCase, Depends(get_chat_usecase)],
):
    deleted = await uc.clear_history(user_id)
    return {"deleted": deleted}
