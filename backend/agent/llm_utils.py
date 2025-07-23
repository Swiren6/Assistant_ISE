from together import Together
import os
import logging
import os
logger = logging.getLogger(__name__)  # Logger spécifique au fichier/module

def ask_llm(prompt: str) -> str:
    logger.info("🔁 Envoi du prompt au LLM...")
    print(f"🧠 Prompt envoyé au LLM:\n{prompt}")

    try:
        client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2048
        )
        content = response.choices[0].message.content
        logger.info("✅ Réponse reçue du LLM")
        print(f"📥 Réponse LLM:\n{content}")
        return content
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'appel au LLM: {e}")
        print(f"❌ Erreur LLM: {str(e)}")
        return ""