import httpx
import logging
from typing import AsyncGenerator
from models import ChatRequest, LLMRequest, LLMMessage, LLMResponse
from config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for communicating with LLM via ngrok"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def _build_system_prompt(self, request: ChatRequest) -> str:
        """Build the system prompt from request context and trigger"""
        
        # Build context section
        context_lines = "\n".join([f"- {item}" for item in request.context])
        
        system_prompt = f"""['Description of a Soccer Game']
축구는 두 팀이 공을 상대 골문에 넣어 득점하는 경기다.
경기 시간은 전반 45분 + 후반 45분(총 90분). 필요 시 추가시간(Added Time)이 부여될 수 있다.
한 팀은 보통 11명(골키퍼 포함)으로 구성된다.

['Current Soccer Game Situation']
**context**
{context_lines}

**trigger**
{request.trigger}

['과제(Task)']
현재 진행 중인 경기에 대해 A와 B 두 사람이 이야기하고 있다. 두 사람 모두 {request.selected_team}의 팬이며, B의 감정 표현은 매우 적극적이다(High arousal).
위의 축구 경기 설명과 현재 상황을 바탕으로, Person B의 대화 응답을 생성하라.

['Person B의 행동 가이드라인(Behavioral Guidelines for Person B)']
행동이 {request.selected_team}에 유리하면: B는 그 행동을 좋아한다.
행동이 {request.selected_team}에 불리하면: B는 거친 비속어를 표현한다.(쌍욕은 금지)
커뮤니티체(은어, 'ㅋ/ㅎ/ㅠ,?,!' 반복)를 사용하세요.
문법에 얽매이지 말고 짧고 강렬하게 반응하세요.
실제로 채팅을 치는 것 처럼 9단어 이내로 문장 을 완성하세요

fan_team: {request.selected_team}"""
        
        return system_prompt
    
    def _build_llm_request(self, request: ChatRequest) -> LLMRequest:
        """Transform ChatRequest to LLM request format"""
        
        # Build system message
        system_message = LLMMessage(
            role="system",
            content=self._build_system_prompt(request)
        )
        
        # Build chat history messages
        history_messages = [
            LLMMessage(role=msg.role, content=msg.message)
            for msg in request.chat_history
        ]
        
        # Add current user message
        current_message = LLMMessage(role="user", content=request.message)
        
        # Combine all messages
        all_messages = [system_message] + history_messages + [current_message]
        
        return LLMRequest(
            model=self.settings.llm_model,
            messages=all_messages,
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
            frequency_penalty=self.settings.llm_frequency_penalty
        )
    
    async def get_chat_completion(self, request: ChatRequest) -> str:
        """Get chat completion from LLM"""
        
        llm_request = self._build_llm_request(request)
        
        # Log request to vLLM
        logger.info("🚀 Sending request to vLLM:")
        logger.info(f"  Endpoint: {self.settings.llm_endpoint}")
        logger.info(f"  Model: {llm_request.model}")
        logger.info(f"  Temperature: {llm_request.temperature}")
        logger.info(f"  Max tokens: {llm_request.max_tokens}")
        logger.info(f"  Frequency penalty: {llm_request.frequency_penalty}")
        logger.info(f"  Messages count: {len(llm_request.messages)}")
        logger.info(f"  Full request payload:")
        logger.info(f"{llm_request.model_dump_json(indent=2)}")
        logger.info("-" * 80)
        
        async with httpx.AsyncClient(timeout=self.settings.llm_timeout) as client:
            response = await client.post(
                self.settings.llm_endpoint,
                json=llm_request.model_dump(),
                headers={
                    "Content-Type": "application/json",
                    "ngrok-skip-browser-warning": "true"
                },
                auth=(self.settings.llm_username, self.settings.llm_password)
            )
            
            # Log response status and body for debugging
            if response.status_code != 200:
                logger.error(f"❌ vLLM returned error status {response.status_code}")
                logger.error(f"Response body: {response.text}")
            
            response.raise_for_status()
            
            llm_response = LLMResponse(**response.json())
            
            # Extract content from first choice
            content = ""
            if llm_response.choices and len(llm_response.choices) > 0:
                content = llm_response.choices[0].message.content
            
            # Log response from vLLM
            logger.info("✅ Received response from vLLM:")
            logger.info(f"  Response ID: {llm_response.id}")
            logger.info(f"  Model: {llm_response.model}")
            logger.info(f"  Tokens used: {llm_response.usage.total_tokens}")
            logger.info(f"  Content: {content}")
            if llm_response.choices and len(llm_response.choices) > 0:
                logger.info(f"  Finish reason: {llm_response.choices[0].finish_reason}")
            logger.info(f"  Full response:")
            logger.info(f"{llm_response.model_dump_json(indent=2)}")
            logger.info("=" * 80)
            
            return content
    
    async def stream_chat_completion(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Stream chat completion character by character"""
        
        # Get the full response first
        content = await self.get_chat_completion(request)
        
        # Stream it character by character
        for char in content:
            yield char
