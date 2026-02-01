import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_FAST = "gpt-4o-mini"
MAX_INPUT_CHARS = 3000 # Truncate input to avoid token waste

async def get_json_completion(system_prompt: str, user_content: str):
    """
    Helper for cheap JSON mode analysis.
    """
    try:
        # Truncate content
        if len(user_content) > MAX_INPUT_CHARS:
            user_content = user_content[:MAX_INPUT_CHARS] + "...[TRUNCATED]"

        response = await client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.2, # Low temp for analytical consistency
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API Error: {e}")
        return None

async def get_text_completion(system_prompt: str, user_content: str):
    """
    Helper for narrative output.
    """
    try:
        if len(user_content) > MAX_INPUT_CHARS:
            user_content = user_content[:MAX_INPUT_CHARS] + "...[TRUNCATED]"
            
        response = await client.chat.completions.create(
            model=MODEL_FAST,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API Error: {e}")
        return None
