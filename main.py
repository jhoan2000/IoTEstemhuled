import flet as ft
import paho.mqtt.client as mqtt
import json
import threading
import time
# Configuración MQTT (usa el mismo broker que la ESP32)
MQTT_BROKER = "mqtt.eclipseprojects.io"
MQTT_TOPIC_SENSOR = "sensor/dht11"  # Tópico donde ESP32 publica datos
MQTT_TOPIC_LED = "control/led"      # Tópico para controlar el LED

# Variables globales para los datos
temperatura = "---"
humedad = "---"
led_status = False
page = None

# Conexión MQTT
def on_connect(client, userdata, flags, rc):
    print("Conectado al broker MQTT")
    client.subscribe(MQTT_TOPIC_SENSOR)

def on_message(client, userdata, msg):
    global temperatura, humedad, led_status
    try:
        data = json.loads(msg.payload.decode())
        temperatura = data["temp"]
        humedad = data["hum"]
        led_status = data["sled"]
        print(f"Datos recibidos: Temp={temperatura}°C, Hum={humedad}% ,Estado del Led = {led_status}" )
        update_ui()
    except Exception as e:
        #print(f"Error al procesar mensaje: {e}")
        pass

def update_ui():
    page.update()

def toggle_led(e):
    global led_status        
    led_status = not led_status
    command = "ON" if led_status else "OFF"
    mqtt_client.publish(MQTT_TOPIC_LED, command)
    btn_led.text = f"LED: {'ENCENDIDO' if led_status else 'APAGADO'}"
    page.update()

# Configura cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    mqtt_client.connect(MQTT_BROKER, 1883, 60)
    mqtt_client.loop_forever()

# Interfaz Flet
def main(page: ft.Page):
    global btn_led
    page.title = "IoT Estemhuled"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT

    # Elementos UI
    txt_temp = ft.Text(f"Temperatura: {temperatura}°C", size=24)
    txt_hum = ft.Text(f"Humedad: {humedad}%", size=24)
    btn_led = ft.ElevatedButton(
        "LED: APAGADO",
        on_click=toggle_led,
        color="white",
        bgcolor="blue",
        width=200
    )
    
    page.add(
        ft.Column([
            ft.Icon(name=ft.icons.THERMOSTAT, size=50),
            txt_temp,
            ft.Divider(),
            ft.Icon(name=ft.icons.WATER_DROP, size=50),
            txt_hum,
            ft.Divider(),
            btn_led
        ], alignment=ft.MainAxisAlignment.CENTER)
    )

    # Actualización periódica de UI
    def update_task():
        while True:
            txt_temp.value = f"Temperatura: {temperatura}°C"
            txt_hum.value = f"Humedad: {humedad}%"
            btn_led.text = f"LED: {'ENCENDIDO' if led_status else 'APAGADO'}"

            page.update()
            time.sleep(2)

    threading.Thread(target=update_task, daemon=True).start()

# Iniciar MQTT en segundo plano
threading.Thread(target=start_mqtt, daemon=True).start()

ft.app(target=main)

