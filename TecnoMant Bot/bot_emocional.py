import os
import sys
import logging
import telebot
from transformers import pipeline
import random

# Configuración del bot de Telegram
TOKEN_BOT_TELEGRAM = os.getenv("TOKEN_BOT_TELEGRAM")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Logging básico
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Inicializar el bot de Telegram
if not TOKEN_BOT_TELEGRAM:
    logging.error("La variable de entorno TOKEN_BOT_TELEGRAM no está definida. Define TOKEN_BOT_TELEGRAM y reinicia.")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN_BOT_TELEGRAM)

# Modelo de análisis de sentimiento en español ya entrenado
# Cargar modelo de análisis de sentimiento
try:
    analizador = pipeline(
        "sentiment-analysis",
        model="pysentimiento/robertuito-sentiment-analysis"
    )
except Exception as e:
    logging.error(f"No se pudo cargar el modelo de sentimiento: {e}")
    analizador = None

# Funciones 
def generar_respuesta(sentimiento, texto_usuario):
    """Genera respuesta empática según sentimiento y palabras clave"""
    texto_lower = texto_usuario.lower()

    # Chequeo de palabras clave antes de usar el sentimiento
    if "estresado" in texto_lower or "frustrado" in texto_lower or "mal" in texto_lower:
        return "Tranquilo, todos empezamos asi. Proba hacer una pausa y volver con otra mirada. Si queres, puedo explicarte paso a paso como seguir."
    elif "enojado" in texto_lower or "molesto" in texto_lower or "fastidioso" in texto_lower:
        return "Uf, entiendo que da bronca. Respira un segundo y contame que parte te esta complicando, seguro lo resolvemos juntos."
    elif "feliz" in texto_lower or "contento" in texto_lower or "alegre" in texto_lower:
        return "¡Genial! Me alegra que te haya salido. Segui asi, vas a aprender un monton."
    elif "no sé" in texto_lower or "confundido" in texto_lower or "nada" in texto_lower:
        return "Esta bien no saberlo todavia. Podemos repasarlo paso a paso si queres, y lo vas a entender mejor."

    # Si no hay palabras clave, usar el sentimiento del modelo
    if sentimiento == "POS":
        return "¡Genial! Me alegra que te haya salido. Segui asi, vas a aprender un monton."
    elif sentimiento == "NEG":
        return "Tranquilo, todos empezamos asi. Proba hacer una pausa y volver con otra mirada. Si queres, puedo explicarte paso a paso como seguir."
    else:  # NEU
        return "Esta bien no saberlo todavia. Podemos repasarlo paso a paso si queres, y lo vas a entender mejor"


def _normalizar_label(label, score=None):
    """Normaliza etiquetas de salida del pipeline a 'POS','NEG' o 'NEU'.

    label: cadena tal como la devuelve el pipeline (ej: 'POS', 'NEG', 'NEU', 'POSITIVE', 'NEGATIVE', 'LABEL_0'...)
    score: puntuación asociada (opcional) para decidir en casos ambiguos.
    """
    if not label:
        return None
    lab = str(label).lower()
    if "pos" in lab or "positive" in lab:
        return "POS"
    if "neg" in lab or "negative" in lab:
        return "NEG"
    if "neu" in lab or "neutral" in lab:
        return "NEU"

    # Caso LABEL_N o etiquetas numéricas: usar score si está disponible
    try:
        if lab.startswith("label_") and score is not None:
            # asumimos que score es probabilidad de la etiqueta devuelta; si es alta y la etiqueta no da pistas, usar umbral
            return "POS" if score >= 0.55 else "NEG"
    except Exception:
        pass

    # fallback: neutro
    return "NEU"


#Respuestas del bot
@bot.message_handler(commands=['start', 'help'])
def bienvenida(message):
    bot.send_message(
        message.chat.id,
        "¡Hola! Soy tu bot que te acompaña mientras trabajás con tu computadora 💻\n"
        "Escribí cómo te sentís y te voy a responder con apoyo y consejos.\n\n"
        "Ejemplos:\n"
        "- 'Estoy re feliz porque me salió'\n"
        "- 'No tengo ganas de nada, me frustro'\n"
        "- 'No sé ni por dónde empezar'"
    )

@bot.message_handler(func=lambda message: True)
def analizar_mensaje(message):
    texto = message.text
    bot.send_chat_action(message.chat.id, "typing")

    try:
        if analizador is None:
            # modelo no disponible
            raise RuntimeError("Modelo de análisis no disponible")

        resultado = analizador(texto)[0]
        # Normalizar la etiqueta a POS/NEG/NEU
        sentimiento = _normalizar_label(resultado.get("label"), resultado.get("score"))
        respuesta = generar_respuesta(sentimiento, texto)
    except Exception as e:
        logging.exception("Error al analizar mensaje")
        respuesta = "Disculpá, no pude analizar tu mensaje ahora. Intentá más tarde."

    bot.reply_to(message, respuesta)


# Inicio del bot

if __name__ == "__main__":
    print("Bot emocional de soporte iniciado. Esperando mensajes...")
    bot.infinity_polling()
