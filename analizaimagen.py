import os
import base64
import io
import requests
from PIL import Image
import telebot
from groq import Groq
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de tokens y claves API
TOKEN_BOT_TELEGRAM = os.getenv('TELEGRAM_BOT_TOKEN')
CLAVE_API_GROQ = os.getenv('GROQ_API_KEY')

if not TOKEN_BOT_TELEGRAM:
    raise ValueError("TELEGRAM_BOT_TOKEN no está configurado en las variables de entorno")
if not CLAVE_API_GROQ:
    raise ValueError("GROQ_API_KEY no está configurado en las variables de entorno")

bot = telebot.TeleBot(TOKEN_BOT_TELEGRAM)
cliente_groq = Groq(api_key=CLAVE_API_GROQ)

def imagen_a_base64(ruta_o_bytes_imagen):
    """
    Convierte una imagen a base64 para enviarla a Groq.
    
    Args:
        ruta_o_bytes_imagen: Ruta del archivo o bytes de la imagen
        
    Returns:
        str: Imagen codificada en base64 o None si hay error
    """
    try:
        if isinstance(ruta_o_bytes_imagen, bytes):
            return base64.b64encode(ruta_o_bytes_imagen).decode('utf-8')
        else:
            with open(ruta_o_bytes_imagen, "rb") as archivo_imagen:
                return base64.b64encode(archivo_imagen.read()).decode('utf-8')
    except Exception as e:
        print(f"Error al convertir imagen a base64: {e}")
        return None

def analizar_problema_tecnico_con_groq(imagen_base64):
    """
    Envía la imagen a Groq para analizar problemas técnicos y obtener soluciones.
    
    Args:
        imagen_base64: Imagen codificada en base64
        
    Returns:
        str: Análisis del problema y soluciones o None si hay error
    """
    try:
        prompt_tecnico = """
Eres un técnico especialista en diagnóstico de problemas informáticos. Analiza esta imagen y proporciona:

ANALISIS DEL PROBLEMA:
- Identifica el tipo de problema (pantallazo azul, error de sistema, problema hardware, etc.)
- Describe qué está mostrando la imagen específicamente
- Explica las posibles causas del problema

SOLUCIONES RECOMENDADAS:
Proporciona pasos específicos y prácticos para resolver el problema, organizados por nivel de dificultad:

Solución Básica (Usuario):
1. Primer paso simple que puede hacer cualquier usuario
2. Segundo paso accesible
3. Tercera acción recomendada

Solución Avanzada (Técnico):
1. Pasos para usuarios avanzados
2. Herramientas necesarias
3. Verificaciones técnicas

PRECAUCIONES:
- Advertencias importantes de seguridad
- Riesgos potenciales
- Cuándo contactar a un profesional

PREVENCION:
- Cómo evitar que vuelva a ocurrir
- Mantenimiento recomendado

Responde en español, con un tono profesional pero accesible.
"""

        completado_chat = cliente_groq.chat.completions.create(
            messages=[{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": prompt_tecnico
                }, {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{imagen_base64}"
                    }
                }]
            }],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.3,
            max_tokens=2500
        )
        return completado_chat.choices[0].message.content
    except Exception as e:
        print(f"Error al analizar problema técnico con Groq: {e}")
        return None

# Manejadores de comandos
@bot.message_handler(commands=['start'])
def enviar_bienvenida(mensaje):
    """Envía mensaje de bienvenida al usuario."""
    texto_bienvenida = (
        "Hola! Soy tu Asistente Técnico de Diagnóstico\n\n"
        "Como funciono?\n"
        "Enviamé una imagen de cualquier problema técnico y te ayudaré a diagnosticarlo:\n"
        "- Pantallazos azules\n"
        "- Mensajes de error\n"
        "- Problemas de hardware\n"
        "- Fallos del sistema\n\n"
        
        "Que recibiras:\n"
        "- Analisis profesional del problema\n"
        "- Soluciones paso a paso\n"
        "- Niveles de dificultad\n"
        "- Precauciones importantes\n\n"
        
        "Envía una imagen de tu problema técnico y empecemos!\n\n"
        "Usa /help para más información"
    )
    bot.reply_to(mensaje, texto_bienvenida)

@bot.message_handler(commands=['help'])
def enviar_ayuda(mensaje):
    """Envía mensaje de ayuda al usuario."""
    texto_ayuda = (
        "Asistente Técnico de Diagnóstico\n\n"
        "Que tipos de imágenes puedo analizar?\n"
        "- Pantallazos azules (BSOD)\n"
        "- Mensajes de error del sistema\n"
        "- Problemas de hardware visibles\n"
        "- Fallos de arranque\n"
        "- Errores de aplicaciones\n"
        "- Luces indicadoras de dispositivos\n\n"
        
        "Proceso de analisis:\n"
        "1. Envía la imagen del problema\n"
        "2. Analizo visualmente el error\n"
        "3. Identifico las posibles causas\n"
        "4. Proporciono soluciones paso a paso\n\n"
        
        "Niveles de solucion:\n"
        "- Basico (para cualquier usuario)\n"
        "- Avanzado (para técnicos)\n"
        "- Profesional (cuando contactar expertos)\n\n"
        
        "Importante:\n"
        "Este es un asistente de diagnóstico. Para problemas críticos siempre recomiendo contactar con un técnico profesional.\n\n"
        "Envía tu imagen y empecemos!"
    )
    bot.reply_to(mensaje, texto_ayuda)

@bot.message_handler(commands=['ejemplos'])
def enviar_ejemplos(mensaje):
    """Envía ejemplos de problemas que puede analizar."""
    texto_ejemplos = (
        "Ejemplos de problemas que puedo analizar:\n\n"
        "Pantallazos Azules:\n"
        "- Códigos de error STOP\n"
        "- Mensajes de sistema corrupto\n"
        "- Fallos de drivers\n\n"
        
        "Errores de Sistema:\n"
        "- Mensajes de aplicación fallida\n"
        "- Problemas de arranque\n"
        "- Errores de Windows/Linux/Mac\n\n"
        
        "Hardware Visible:\n"
        "- Luces de error en dispositivos\n"
        "- Pantallas de diagnóstico\n"
        "- Códigos POST\n\n"
        
        "Problemas de Software:\n"
        "- Mensajes de error específicos\n"
        "- Fallos de instalación\n"
        "- Conflictos de programas\n\n"
        
        "No dudes en enviar cualquier imagen de problema técnico!"
    )
    bot.reply_to(mensaje, texto_ejemplos)

@bot.message_handler(content_types=['photo'])
def manejar_foto(mensaje):
    """
    Procesa las imágenes de problemas técnicos enviadas por el usuario.
    
    Args:
        mensaje: Objeto mensaje de Telegram que contiene la foto
    """
    try:
        # Notificar recepción de imagen
        bot.reply_to(mensaje, "Imagen recibida. Analizando el problema técnico...")

        # Obtener y procesar la imagen
        foto = mensaje.photo[-1]  # Obtener la versión de mayor calidad
        info_archivo = bot.get_file(foto.file_id)
        archivo_descargado = bot.download_file(info_archivo.file_path)
        imagen_base64 = imagen_a_base64(archivo_descargado)

        if not imagen_base64:
            bot.reply_to(mensaje, "Error al procesar la imagen. Por favor, intenta enviar la imagen nuevamente.")
            return

        # Analizar el problema técnico con Groq
        analisis = analizar_problema_tecnico_con_groq(imagen_base64)
        
        if analisis:
            respuesta = f"DIAGNOSTICO TECNICO\n\n{analisis}"
            bot.reply_to(mensaje, respuesta)
        else:
            bot.reply_to(mensaje, "No pude analizar la imagen. Por favor, asegurate de que la imagen sea clara y muestre el problema técnico visiblemente.")
    
    except Exception as e:
        print(f"Error al procesar la imagen técnica: {e}")
        bot.reply_to(mensaje, "Error en el analisis. Ocurrio un problema al procesar tu imagen. Por favor, intenta con otra imagen o más tarde.")

@bot.message_handler(func=lambda mensaje: True)
def manejar_otros_mensajes(mensaje):
    """
    Maneja mensajes que no son comandos ni imágenes.
    
    Args:
        mensaje: Objeto mensaje de Telegram
    """
    texto_respuesta = (
        "Asistente Técnico de Diagnóstico\n\n"
        "Para recibir ayuda con un problema técnico, envía una imagen del problema:\n"
        "- Pantallazo azul\n"
        "- Mensaje de error\n"
        "- Problema visible de hardware\n"
        "- Cualquier fallo del sistema\n\n"
        
        "Consejo: Asegurate de que la imagen sea clara y se vea bien el texto/error.\n\n"
        "Usa /help para ver todos los comandos disponibles\n"
        "Usa /ejemplos para ver tipos de problemas que puedo analizar"
    )
    bot.reply_to(mensaje, texto_respuesta)

def main():
    """Función principal que inicia el bot."""
    print("Bot de Diagnóstico Técnico iniciado...")
    print("Esperando imágenes de problemas técnicos...")
    print("Listo para analizar pantallazos azules, errores y fallos del sistema...")
    
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Error al iniciar el bot: {e}")

if __name__ == '__main__':
    main()