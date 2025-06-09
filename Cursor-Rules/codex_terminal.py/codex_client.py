# codex_client.py
from openai import OpenAI
from retry_utils import retry_with_exponential_backoff

client = OpenAI()


@retry_with_exponential_backoff
def get_codex_completion(prompt: str) -> str:
    """Hämtar kodförslag från OpenAI:s API med exponentiell backoff.
    
    Args:
        prompt: Textprompt som ska skickas till API:et
        
    Returns:
        Genererad text från API:et
    """
    response = client.completions.create(
        model="gpt-4",  # Standardmodell, kan ändras vid behov
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()


# Kör som test
if __name__ == "__main__":
    test_prompt = "Skriv en Python-funktion som räknar Fibonacci-tal."
    response = get_codex_completion(test_prompt)
    print(response)
