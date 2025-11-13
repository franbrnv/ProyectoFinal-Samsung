import os
import json
import base64
import telebot
from groq import Groq
from dotenv import load_dotenv
from transformers import pipeline
import random

# Cargar variables de entorno
load_dotenv()

# Configuración
TOKEN_BOT_TELEGRAM = os.getenv("TOKEN_BOT_TELEGRAM")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Validación
if not TOKEN_BOT_TELEGRAM:
    raise ValueError("Token de Telegram no encontrado")
if not GROQ_API_KEY:
    raise ValueError("API Key de Groq no encontrada")

# Inicialización
bot = telebot.TeleBot(TOKEN_BOT_TELEGRAM)
groq_client = Groq(api_key=GROQ_API_KEY)

# Cargar datos de la empresa
def load_company_data():
    try:
        with open("dataset.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar dataset: {e}")
        return None

company_data = load_company_data()

# Modelo de análisis de sentimientos
analizador_sentimientos = pipeline(
    "sentiment-analysis",
    model="pysentimiento/robertuito-sentiment-analysis"
)

def get_groq_response(user_message: str) -> str:
    """Obtiene respuesta del asistente corporativo"""
    try:
        system_prompt = f"""Eres el asistente virtual de TecnoMant. Responde preguntas basándote ÚNICAMENTE en esta información:

{json.dumps(company_data, ensure_ascii=False, indent=2)}

Reglas:
1. Solo información del dataset
2. No inventes datos
3. Para información no disponible, sugerir contacto
4. No datos sensibles del staff
5. Tono profesional y cercano
6. Sin saludos repetitivos
7. Usa emojis moderadamente
8. Para ejemplos, usar lista completa del dataset
9. Para temas fuera de ámbito, seguir reglas de off_topic_handling
"""
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=500
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error en Groq: {e}")
        return None

def transcribir_audio(message) -> str:
    """Transcribe mensajes de voz a texto"""
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open("temp_audio.ogg", "wb") as f:
            f.write(downloaded_file)
        
        with open("temp_audio.ogg", "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
                language="es"
            )
        
        os.remove("temp_audio.ogg")
        return transcription.text
    except Exception as e:
        print(f"Error en transcripción: {e}")
        return None

def analizar_imagen(imagen_bytes) -> str:
    """Analiza y describe imágenes"""
    try:
        imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
        
        chat_completion = groq_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": "Describe esta imagen detalladamente en español. Incluye elementos, colores, objetos, acciones y emociones relevantes."
                }, {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{imagen_base64}"
                    }
                }]
            }],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.7,
            max_tokens=2000
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error en análisis de imagen: {e}")
        return None

def generar_respuesta_emocional(sentimiento, texto_usuario):
    """Genera respuesta empática según sentimiento"""
    texto_lower = texto_usuario.lower()
    
    # Palabras clave específicas
    palabras_clave = {
        "estresado": "Tranquilo, todos empezamos asi. Proba hacer una pausa y volver con otra mirada.",
        "frustrado": "Tranquilo, todos empezamos asi. Proba hacer una pausa y volver con otra mirada.",
        "enojado": "Uf, entiendo que da bronca. Respira un segundo y contame que parte te esta complicando.",
        "feliz": "¡Genial! Me alegra que te haya salido. Segui asi, vas a aprender un monton.",
        "no sé": "Esta bien no saberlo todavia. Podemos repasarlo paso a paso si queres."
    }
    
    for palabra, respuesta in palabras_clave.items():
        if palabra in texto_lower:
            return respuesta
    
    # Análisis por sentimiento del modelo
    if sentimiento == "POS":
        return "¡Genial! Me alegra que te haya salido. Segui asi, vas a aprender un monton."
    elif sentimiento == "NEG":
        return "Tranquilo, todos empezamos asi. Proba hacer una pausa y volver con otra mirada."
    else:
        return "Esta bien no saberlo todavia. Podemos repasarlo paso a paso si queres."


@bot.message_handler(commands=['start', 'help'])
def comando_inicio(message):
    """Mensaje de bienvenida y ayuda"""
    welcome_text = """
 **Bienvenido al Asistente TecnoMant** 

Soy tu asistente multifuncional con estas capacidades:

 **Asistente Corporativo** - Consultas sobre TecnoMant
 **Soporte Emocional** - Análisis de sentimientos  
 **Procesamiento de Voz** - Transcripción de audio
 **Análisis de Imágenes** - Descripción detallada

**Comandos disponibles:**
/start - Este mensaje de bienvenida
/help - Ayuda y funcionalidades
/corporativo - Modo consultas empresariales
/emocional - Modo soporte emocional

**¡Simplemente escribe o envía lo que necesites!** 
"""
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['corporativo'])
def modo_corporativo(message):
    """Activa modo consultas corporativas"""
    response = """**Modo Corporativo Activado**

Ahora puedes hacerme preguntas sobre:
• Servicios de TecnoMant
• Información de la empresa  
• Precios y planes
• Proyectos actuales
• Contacto y ubicación

¿En qué puedo ayudarte hoy? """
    bot.reply_to(message, response)

@bot.message_handler(commands=['emocional'])
def modo_emocional(message):
    """Activa modo soporte emocional"""
    response = """ **Modo Soporte Emocional Activado**

Compartí cómo te sentís y te acompañaré con:
• Empatía y comprensión
• Consejos prácticos  
• Apoyo motivacional
• Escucha activa

¿Cómo estás hoy? """
    bot.reply_to(message, response)

@bot.message_handler(content_types=['text'])
def manejar_texto(message):
    """Procesa mensajes de texto"""
    bot.send_chat_action(message.chat.id, "typing")
    
    # Análisis de sentimiento para respuestas emocionales
    try:
        resultado_sentimiento = analizador_sentimientos(message.text)[0]
        sentimiento = resultado_sentimiento["label"]
        confianza = resultado_sentimiento["score"]
        
        # Si es muy emocional, responder con soporte
        if confianza > 0.8 and sentimiento in ["NEG", "POS"]:
            respuesta = generar_respuesta_emocional(sentimiento, message.text)
            bot.reply_to(message, respuesta)
            return
    except Exception as e:
        print(f"Error en análisis emocional: {e}")
    
    # Respuesta corporativa por defecto
    respuesta = get_groq_response(message.text)
    if respuesta:
        bot.reply_to(message, respuesta)
    else:
        bot.reply_to(message, " Error al procesar tu consulta. Intenta nuevamente.")

@bot.message_handler(content_types=['voice'])
def manejar_voz(message):
    """Procesa mensajes de voz"""
    bot.send_chat_action(message.chat.id, "typing")
    
    transcripcion = transcribir_audio(message)
    if not transcripcion:
        bot.reply_to(message, " No pude transcribir el audio. Intenta de nuevo.")
        return
    
    # Mostrar transcripción
    bot.reply_to(message, f" **Transcripción:** {transcripcion}")
    
    # Procesar con Groq
    respuesta = get_groq_response(transcripcion)
    if respuesta:
        bot.reply_to(message, respuesta)
    else:
        bot.reply_to(message, " Error al procesar tu consulta.")

@bot.message_handler(content_types=['photo'])
def manejar_imagen(message):
    """Procesa imágenes"""
    bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Obtener imagen
        foto = message.photo[-1]
        file_info = bot.get_file(foto.file_id)
        imagen_bytes = bot.download_file(file_info.file_path)
        
        # Analizar imagen
        descripcion = analizar_imagen(imagen_bytes)
        
        if descripcion:
            respuesta = f" **Descripción de la imagen:**\n\n{descripcion}"
            bot.reply_to(message, respuesta)
        else:
            bot.reply_to(message, " No pude analizar la imagen.")
            
    except Exception as e:
        print(f"Error procesando imagen: {e}")
        bot.reply_to(message, " Error al procesar la imagen.")

if __name__ == "__main__":
    if company_data:
        print(f" Bot Unificado TecnoMant iniciado...")
        print(f" Empresa: {company_data['company_info']['name']}")
        print(" Esperando mensajes...")
        
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error en el bot: {e}")
    else:
        print(" Error: No se pudo cargar dataset.json")