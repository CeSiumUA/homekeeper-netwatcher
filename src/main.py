import logging
from os import environ, system
from apscheduler.schedulers.blocking import BlockingScheduler
from paho.mqtt import client as mqtt_client
import topics
import random

device_states = {}
MQTT_CLIENT_INSTANCE = None

def notify_connection_changed(ip_addr: str, state: bool, name: str):
    logging.info("notify device connected/disconnected")
    state_str = "connected" if state else "disconnected"
    MQTT_CLIENT_INSTANCE.publish(topic=topics.SEND_MESSAGE, payload=f"device {name} ({ip_addr}) {state_str}!")

def process_device_state(res: bool, ip_addr: str, name: str):
    if ip_addr not in device_states:
        device_states[ip_addr] = {
            "state": res,
            "counter": 0
        }

    if device_states[ip_addr] != res:
        counter_threshold = 5 if not res else 1
        if device_states[ip_addr]["counter"] >= counter_threshold:
            notify_connection_changed(ip_addr, res, name)
            device_states[ip_addr]["state"] = res
            device_states[ip_addr]["counter"] = 0
            logging.info("device state counter resetted")
        else:
            logging.info("device state counter incremented")
            device_states[ip_addr]["counter"] += 1

def ping_devices():
    with open("clients.list", "r") as fd:
        for device_str in fd:
            device = device_str.split("=")
            device_name = device[0]
            ip_addr = device[1]
            logging.info(f"processing {device_name}")
            response = system("ping -c 1 " + ip_addr)
            process_device_state(response == 0, ip_addr, device_name)

def on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT")
    else:
        logging.fatal("Failed to connect to MQTT, return code: %d\n", rc)

def start_mqtt():
    global MQTT_CLIENT_INSTANCE
    broker_host = environ.get("MQTT_HOST")
    if broker_host is None:
        logging.fatal("broker host is empty")
    broker_port = environ.get("MQTT_PORT")
    if broker_port is None:
        broker_port = 1883
    else:
        broker_port = int(broker_port)

    client_id = "netwatcher-{}".format(random.randint(0, 1000))

    MQTT_CLIENT_INSTANCE = mqtt_client.Client(client_id=client_id)
    MQTT_CLIENT_INSTANCE.on_connect = on_mqtt_connect
    MQTT_CLIENT_INSTANCE.connect(broker_host, broker_port)
    MQTT_CLIENT_INSTANCE.loop_start()

def start_scheduler():
    ping_interval = environ.get("PING_INTERVAL")

    if ping_interval is None:
        ping_interval = 10
        logging.info("ping interval is not specified, defaulted to: {}".format(ping_interval))
    else:
        ping_interval = int(ping_interval)

    scheduler = BlockingScheduler()
    scheduler.add_job(ping_devices, 'interval', seconds=ping_interval)

    try:
        logging.info("starting scheduler...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

def main():
    start_mqtt()
    start_scheduler()

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

    main()