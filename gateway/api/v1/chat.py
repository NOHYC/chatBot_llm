from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models import ChatRequest
from services.llm_service import LLMService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """
    Stream chat responses character by character.
    
    Args:
        request: ChatRequest containing message, context, trigger, chat history, and selected team
    
    Returns:
        StreamingResponse with text/event-stream content type
    """
    try:
        # Log received request from frontend
        logger.info("=" * 80)
        logger.info("📥 Received request from frontend:")
        logger.info(f"  Message: {request.message}")
        logger.info(f"  Team: {request.selected_team}")
        logger.info(f"  Trigger: {request.trigger}")
        logger.info(f"  Context items: {len(request.context)}")
        logger.info(f"  Chat history length: {len(request.chat_history)}")
        logger.info(f"  Full request: {request.model_dump_json(indent=2)}")
        logger.info("=" * 80)
        
        llm_service = LLMService()
        
        async def generate():
            """Generator function for streaming response"""
            try:
                async for char in llm_service.stream_chat_completion(request):
                    # Send each character as Server-Sent Event
                    yield f"data: {char}\n\n"
                
                # Send completion signal
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Error during streaming: {str(e)}")
                yield f"data: [ERROR]: {str(e)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable buffering in nginx
            }
        )
    
    except Exception as e:
        logger.error(f"Error in stream_chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
