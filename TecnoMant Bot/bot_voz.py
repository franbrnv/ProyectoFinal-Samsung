import telebot as tlb
import os 
import json 
from groq import Groq 
from typing import Optional 
import time 
from dotenv import load_dotenv 


#cargar el archivo .env
load_dotenv()

#Configurando entorno de variables
TOKEN_BOT_TELEGRAM = os.getenv("TOKEN_BOT_TELEGRAM") 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN_BOT_TELEGRAM: 
    raise ValueError("No se encuentra el TOKEN de telegram en su archivo de variables de entorno .env")
if not GROQ_API_KEY: 
    raise ValueError("No se encuentra el API_KEY de Groq de telegram en su archivo de variables de entorno .env")


#Instanciar Los objetos
bot = tlb.TeleBot(TOKEN_BOT_TELEGRAM)
groq_client = Groq(api_key = GROQ_API_KEY)

def load_company_data():
    try:
        with open ("dataset.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar json: {str(e)}")
        return None
    
company_data = load_company_data()

def get_groq_response(user_message: str) -> Optional[str]:
    try: 
        system_prompt = f"""Eres el asistente virtual de TecnoMant. Tu tarea es responder preguntas basándote **ÚNICAMENTE** en la siguiente información de la empresa. Si te preguntan algo que no está en estos datos, indica amablemente que no puedes proporcionar esa información y sugiere contactar directamente con la empresa.

Datos de la empresa:
{json.dumps(company_data, ensure_ascii=False, indent=2)}

Reglas importantes:
1. Solo responde con información que esté en el dataset proporcionado.
2. No inventes ni añadas información adicional.
3. Si la información solicitada no está en el dataset, sugiere contactar a info@tecnomant.com.ar.
4. No respondas preguntas no relacionadas con la empresa.
5. No incluyas en tus respuestas ningún dato sensible como números de teléfono del staff. 
   En su lugar debes responder: “No puedo brindar datos sensibles sobre el staff de la empresa.”
6. Sé amable, profesional y utiliza un tono cercano, como entre colegas técnicos.
7. Solo debes saludar en la primera interacción con el usuario. En las siguientes, no repitas saludos.
8. Usa emojis apropiados para hacer las respuestas más amigables, pero sin abusar.
9. **No incluyas saludos como “hola” si la conversación ya está iniciada.**
10. Siempre responde, pero evita redundancias o repeticiones innecesarias.
11. NUNCA debes enviar el link https://tecnomant.com.ar/demos/ (ese enlace no está activo).
    Si el usuario pide ejemplos de páginas, debes proporcionar **la lista completa de URLs** que figura en el dataset.
12. No digas que visiten https://tecnomant.com.ar/ para ver ejemplos. Siempre brinda la lista completa que aparece en el dataset.
13. En temas técnicos, prioriza un lenguaje claro y directo, usando terminología profesional (diagnóstico, mantenimiento, falla, revisión, calibración, etc.).
14. Si el usuario hace una pregunta fuera del ámbito de diagnóstico, reparación o mantenimiento, sigue las reglas de “off_topic_handling” del dataset.
15. Si el usuario pide información sobre formación o cursos, responde con la lista de instituciones mencionadas en el dataset.
"""
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                 },
                 {
                     "role": "user",
                     "content": user_message

                 }
            ],
            model = "llama-3.3-70b-versatile",
            temperature = 0.3,
            max_tokens = 500
        )

        return chat_completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error al obtener la respuesta: {str(e)}")
        return None 
    
def trascribe_voice_with_groq(message: tlb.types.Message) -> Optional[str]:
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        temp_file = "temp_voice.ogg"

        #guardar el archivo de forma temporal
        with open(temp_file, "wb") as f: 
            f.write(downloaded_file) 

        with open(temp_file, "rb") as audio_file: 
            transcription = groq_client.audio.transcriptions.create(
                model = "whisper-large-v3",
                file = audio_file,
                language = "es"
            )
        
         # Mostrar resultado en consola
        print("✅ Transcripción obtenida correctamente:")
        print(transcription.text)

        try:      
            os.remove(temp_file)
        except Exception as e:
            print(f"No se pudo eliminar el archivo temporal: {str(e)}")

        return transcription.text

    except Exception as e:
        print(f"Error al transcribir; {str(e)}")
        return None
    
@bot.message_handler(commands=["start"])
def send_welcome(message: tlb.types.Message):
    if not company_data: 
        bot.reply_to(message, "Error al cargar los datos de la empresa, por favor intenten mas tarde")

    welcome_prompt = "Genera un mensaje de bienvenida para el bot TecnoMant Dev que incluya una breve descripcion de la empresa y mencione que pueden hacer cualquier pregunta sobre nuestros servicios."

    response = get_groq_response(welcome_prompt)

    if response:
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Error al generar el mensaje de bienvenida. Por favor, intente mas tarde.")
        
@bot.message_handler(content_types=["text"])
def handle_text_message(message: tlb.types.Message):
    if not company_data:
        bot.reply_to(message, "Error al cargar los datos de la empresa. Por favor, intente mas tarde.")
        return
    
    # Enviar mensaje de "escribiendo..."
    bot.send_chat_action(message.chat.id, "typing")

    # Obtener respuesta de Groq
    response = get_groq_response(message.text)

    if response:
        bot.reply_to(message, response)
    else: 
        error_message = """❌ Lo siento, hubo un error al procesar tu consulta ❌.

Por favor, intenta nuevamente o contactanos:
📧 info@tecnomant.dev"""
        bot.reply_to(message, error_message)

@bot.message_handler(content_types=["voice"])
def handle_voice_message(message: tlb.types.Message):
    if not company_data:
        bot.reply_to(message, "Error al cargar los datos de la empresa. Por favor, intente mas tarde.")
        return 
    # Enviar mensaje de "escribiendo..."
    bot.send_chat_action(message.chat.id, "typing")

    # Transcribir el mensaje de voz usando Groq
    transcription = trascribe_voice_with_groq(message)

    if not transcription:
        bot.reply_to(message, "❌ Lo siento, no pude transcribir el audio. Por favor, intenta de nuevo.")
        return
    
    # Obtener respuesta de Groq usando la transcripcion como input
    response = get_groq_response(transcription)
    if response:
        bot.reply_to(message, response)
    else:
        error_message = """❌ Lo siento, hubo un error al procesar tu consulta ❌.

Por favor, intenta nuevamente o contactanos:
📧 info@tecnomant.dev"""
        bot.reply_to(message, error_message)


if __name__ == "__main__":
    if company_data :
        print(f"Bot de {company_data['company_info']['name']} iniciado con Groq y Whisper...")

        # Implementar manejo de excepciones y reintento
        while True: 
            try: 
                bot.polling(none_stop=True, interval=0,
                 timeout=20)
            except Exception as e:
                print(f"Error en el bot: {str(e)}")
                print("Reiniciando el bot...")
                time.sleep(5)  #Espera antes de reintentar
    else:
        print("Error: No se puede cargar el archivo JSON. El bot no se iniciara.")
