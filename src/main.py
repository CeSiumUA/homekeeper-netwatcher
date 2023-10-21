import logging
from os import environ, system
from apscheduler.schedulers.blocking import BlockingScheduler

device_states = {}

def notify_connection_changed(ip_addr: str, state: bool, name: str):
    pass

def process_device_state(res: bool, ip_addr: str, name: str):
    if device_states[ip_addr] != res:
        notify_connection_changed(ip_addr, res, name)
    device_states[ip_addr] = res

def ping_devices():
    with open("clients.list") as fd:
        for device_str in fd:
            device = device_str.split("=")
            device_name = device[0]
            ip_addr = device[1]
            response = system("ping -c 1 " + ip_addr)
            process_device_state(response == 0, ip_addr, device_name)

def start_mqtt():
    broker_host = environ.get("MQTT_HOST")
    if broker_host is None:
        logging.fatal("broker host is empty")
    broker_port = environ.get("MQTT_PORT")
    if broker_port is None:
        broker_port = 1883
    else:
        broker_port = int(broker_port)

def main():
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

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

    main()