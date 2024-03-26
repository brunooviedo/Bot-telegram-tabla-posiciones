import telebot
import requests
import pandas as pd
from dotenv import load_dotenv
import os
from unidecode import unidecode

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Token de tu bot de Telegram
bot_token = os.getenv("BOT_TOKEN")
bot_chatID = os.getenv("CHAT_ID")

# URL de la API para obtener la tabla de posiciones
url = "https://www.fotmob.com/api/tltable?leagueId=273"

# Cabeceras para la solicitud HTTP
headers = {
    "Alt-Svc": "h3=\":443\"; ma=86400",
    "Cache-Control": "max-age=40, public",
    "Content-Encoding": "gzip",
    "Content-Type": "application/json; charset=utf-8",
    "Etag": "\"yilauitbp219nm\"",
    "Server": "nginx/1.24.0",
    "Vary": "Accept-Encoding",
    "Via": "1.1 bbfc949357330db97a0f221a32a4d2e0.cloudfront.net (CloudFront)",
    "X-Amz-Cf-Id": "ioyxOTUsfDenOtMXt1PfklhDiypyERBjky7JY6Q1f8nVmcXTNebJXA==",
    "X-Amz-Cf-Pop": "SCL51-P3",
    "X-Asdf": "1",
    "X-Cache": "Miss from cloudfront",
    "X-Cf-Behavior": "api",
    "X-Client-Version": "4432",
    "X-Gg-Bundle-Version": "none",
    "X-Gg-Cache-Date": "Tue, 26 Mar 2024 04:05:48 GMT",
    "X-Gg-Cache-Key": "none/api/tltable?leagueId=273"
}

# Crear una instancia de telebot
bot = telebot.TeleBot(bot_token)

# Función para obtener los datos de un equipo específico
def obtener_datos_equipo(nombre_equipo):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        # Obtener los datos JSON
        json_data = response.json()
        
        # Extraer la tabla de datos del JSON
        table_data = json_data[0]['data']['table']['all']
        
        # Buscar los datos del equipo especificado
        for team in table_data:
            # Comparar el nombre del equipo con y sin tilde
            if nombre_equipo.lower() == team['name'].lower() or unidecode(nombre_equipo.lower()) == unidecode(team['name'].lower()):
                return team
        
        # Si no se encuentra el equipo
        return None
    else:
        return None

# Manejar el comando /tabla
@bot.message_handler(commands=['tabla'])
def enviar_tabla(message):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        # Obtener los datos JSON
        json_data = response.json()
        
        # Extraer la tabla de datos del JSON
        table_data = json_data[0]['data']['table']['all']
        
        # Crear una lista de diccionarios con los datos de la tabla
        table_list = []
        for team in table_data:
            team_dict = {
                'Posición': team['idx'],
                'Equipo': team['name'],
                'PJ': team['played'],
                'PG': team['wins'],
                'PE': team['draws'],
                'PP': team['losses'],
                'GF': int(team['scoresStr'].split('-')[0]),
                'GC': int(team['scoresStr'].split('-')[1]),
                'Puntos': team['pts']
            }
            table_list.append(team_dict)

        # Crear el DataFrame
        df = pd.DataFrame(table_list)

        # Convertir el DataFrame a formato de texto
        tabla_texto = df.to_string(index=False)

        # Enviar la tabla como mensaje
        bot.reply_to(message, tabla_texto)
    else:
        bot.reply_to(message, "Error al obtener la tabla de posiciones")
# Manejar el comando /equipos
@bot.message_handler(commands=['equipos'])
def listar_equipos(message):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        json_data = response.json()
        table_data = json_data[0]['data']['table']['all']
        equipos_disponibles = ', '.join([team['name'] for team in table_data])
        bot.reply_to(message, f"Equipos disponibles: {equipos_disponibles}")
    else:
        bot.reply_to(message, "Error al obtener la lista de equipos disponibles")


# Manejar el comando /equipo
@bot.message_handler(commands=['equipo'])
def enviar_datos_equipo(message):
    # Obtener el nombre del equipo desde el mensaje
    try:
        nombre_equipo_con_tilde = message.text.split('/equipo', 1)[1].strip()
        nombre_equipo = unidecode(nombre_equipo_con_tilde)
    except IndexError:
        bot.reply_to(message, "Debes especificar el nombre del equipo después del comando /equipo")
        return

    # Obtener los datos del equipo
    datos_equipo = obtener_datos_equipo(nombre_equipo)
    
    if datos_equipo:
        mensaje_respuesta = f"Datos del equipo {datos_equipo['name']}:\n" \
                            f"Posición: {datos_equipo['idx']}\n" \
                            f"PJ: {datos_equipo['played']}\n" \
                            f"PG: {datos_equipo['wins']}\n" \
                            f"PE: {datos_equipo['draws']}\n" \
                            f"PP: {datos_equipo['losses']}\n" \
                            f"GF-GC: {datos_equipo['scoresStr']}\n" \
                            f"Puntos: {datos_equipo['pts']}"
        bot.reply_to(message, mensaje_respuesta)
    else:
        # Si no se encuentra el equipo, responder con un mensaje indicando los nombres de equipos disponibles
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            table_data = json_data[0]['data']['table']['all']
            equipos_disponibles = ', '.join([team['name'] for team in table_data])
            bot.reply_to(message, "No se encontraron datos del equipo " + nombre_equipo_con_tilde + ".\nEquipos disponibles:\n" + equipos_disponibles.replace(', ', '\n'))
        else:
            bot.reply_to(message, "Error al obtener la lista de equipos disponibles")

# Ejecutar el bot
bot.polling()



