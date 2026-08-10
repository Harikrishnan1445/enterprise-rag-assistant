import httpx

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "phi3:mini"


async def generate_answer(prompt: str, model: str = DEFAULT_MODEL) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["response"]