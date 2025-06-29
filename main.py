import flet as ft
import paho.mqtt.client as mqtt
import json
import threading
import time
import hashlib
import base64
from Crypto.Cipher import AES

SECRET_KEY = b"claveAES128bits!"
PIN_AUTORIZADO = "1234"

# Variables globales
temperatura = "---"
humedad = "---"
bomba_riego = False
page = None

# Descifrado AES ECB
def descifrar_valor(valor_base64):
    cipher = AES.new(SECRET_KEY, AES.MODE_ECB)
    encrypted_bytes = base64.b64decode(valor_base64)
    decrypted = cipher.decrypt(encrypted_bytes).decode()
    return decrypted.strip()

# Validar firma
def validar_datos(data, firma):
    json_bytes = json.dumps(data).encode()
    h = hashlib.sha256()
    h.update(json_bytes + SECRET_KEY)
    return h.hexdigest() == firma

def on_connect(client, userdata, flags, rc):
    print("Conectado al broker MQTT")
    client.subscribe("sensor/dht11")

def on_message(client, userdata, msg):
    global temperatura, humedad, bomba_riego
    try:
        payload = json.loads(msg.payload)
        data = payload.get("data")
        firma = payload.get("firma")
        if not validar_datos(data, firma):
            print("⚠️ Firma inválida. Ignorando mensaje.")
            return

        pin_cifrado = data.get("pin")
        if descifrar_valor(pin_cifrado) != PIN_AUTORIZADO:
            print("⚠️ PIN no autorizado")
            return

        temperatura = descifrar_valor(data["temp"])
        humedad = descifrar_valor(data["hum"])
        bomba_riego = data["bomba_riego"]

        print(f"Datos recibidos: Temp={temperatura}°C, Hum={humedad}%, Riego={bomba_riego}")
        update_ui()
    except Exception as e:
        print("Error al procesar mensaje:", e)

def update_ui():
    page.update()

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    mqtt_client.connect("mqtt.eclipseprojects.io", 1883, 60)
    mqtt_client.loop_forever()

def main(p):
    global page
    page = p
    page.title = "Panel de Cultivo Seguro"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT

    txt_temp = ft.Text(f"Temperatura: {temperatura}°C", size=24)
    txt_hum = ft.Text(f"Humedad: {humedad}%", size=24)
    txt_riego = ft.Text(f"RIEGO DESACTIVADO", size=28, weight=ft.FontWeight.BOLD, color="blue")

    contenido_sensor = ft.Column([
        ft.Text("Estado del Sensor", size=40, weight=ft.FontWeight.BOLD),
        txt_temp,
        txt_hum,
        txt_riego
    ], alignment=ft.MainAxisAlignment.CENTER, visible=False)

    txt_usuario = ft.TextField(label="Usuario")
    txt_clave = ft.TextField(label="PIN", password=True)

    def autenticar(e):
        if txt_clave.value == PIN_AUTORIZADO:
            dlg.open = False
            contenido_sensor.visible = True
            page.update()
        else:
            txt_clave.error_text = "PIN incorrecto"
            page.update()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Inicio de Sesión"),
        content=ft.Column([
            txt_usuario,
            txt_clave,
        ]),
        actions=[
            ft.TextButton("Ingresar", on_click=autenticar)
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        open=True
    )

    page.dialog = dlg
    page.add(contenido_sensor)
    page.update()

    def update_task():
        while True:
            if contenido_sensor.visible:
                txt_temp.value = f"Temperatura: {temperatura}°C"
                txt_hum.value = f"Humedad: {humedad}%"
                txt_riego.value = "RIEGO ACTIVADO" if bomba_riego else "RIEGO DESACTIVADO"
                txt_riego.color = "green" if bomba_riego else "red"
                page.update()
            time.sleep(2)

    threading.Thread(target=update_task, daemon=True).start()

threading.Thread(target=start_mqtt, daemon=True).start()

ft.app(target=main)
