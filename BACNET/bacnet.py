import random
import pika
import time

rabbitmq_host = '127.0.0.1'  # Replace with your RabbitMQ host on Azure
username = 'Bhargav'  # Replace with your RabbitMQ username
password = 'admin'  # Replace with your RabbitMQ password
port = 5672
ssl = False
flag = 0

QUEUE_NAME = "BACNET_DATA"
slaves = 0


def generate_mac_addresses(n):
    mac_addresses = set()
    while len(mac_addresses) < n + 2:
        mac = ':'.join(['{:02x}'.format(random.randint(0x00, 0xff)) for _ in range(6)])
        mac_addresses.add(mac)
    return list(mac_addresses)


def bacnet_slave(slave_id):
    """Simulates a BACnet slave device that returns a random temperature in a BACnet APDU format."""
    temperature = random.randint(18, 28)
    print(f"BACnet APDU (Simulated): Slave {slave_id}, Temperature: {temperature}°C")
    apdu = {
        "service_choice": 0x00,
        "object_type": 0x05,
        "object_instance": slave_id,
        "property_id": 8,
        "data": temperature
    }

    return apdu


def bacnet_master(slave_id_list, master_id):
    """Simulates a BACnet master device that reads temperature from slaves and formats data as CSV."""
    data_rows = [["Slave ID", "Temperature (°C)"]]

    for slave_id in slave_id_list:
        slave_data = bacnet_slave(slave_id)

        try:
            temperature = slave_data["data"]
        except (KeyError, TypeError):
            temperature = "N/A"
            print(f"Warning: Error processing data from slave {slave_id}")

        data_rows.append([slave_id, temperature])

    csv_data = "\n".join([",".join(map(str, row)) for row in data_rows])
    print(f"Master {master_id} - Received Data (CSV):\n{csv_data}")
    return data_rows


def gateway(gateway_mac, master_mac, slave_mac_address_list):
    def send_to_rabbitmq(line, queue_name, rabbitmq_host, username, password, port=5672, ssl=False):
        credentials = pika.PlainCredentials(username, password)

        if ssl:
            connection_params = pika.ConnectionParameters(
                host=rabbitmq_host,
                port=port,
                credentials=credentials,
                ssl_options=pika.SSLOptions()
            )
        else:
            connection_params = pika.ConnectionParameters(
                host=rabbitmq_host,
                port=port,
                credentials=credentials
            )

        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        # Declare the queue
        channel.queue_declare(queue=queue_name)

        channel.basic_publish(exchange='', routing_key=queue_name, body=line)

        connection.close()

    while True:
        data = bacnet_master(slave_mac_address_list, master_mac)
        for row in data[1:]:  # Skip the header row
            slave_mac = row[0]
            temperature = row[1]
            line = f"{gateway_mac},{master_mac},{slave_mac},{temperature}"
            send_to_rabbitmq(line, QUEUE_NAME, rabbitmq_host, username, password, port, ssl)

        print("Data sent to RabbitMQ")
        print("One set of values sent")
        time.sleep(slaves * 2)


n = int(input("Enter the number of slaves: "))
mac_address_list = generate_mac_addresses(n)
gateway_mac = mac_address_list[0]
master_mac = mac_address_list[1]
slave_mac_address_list = mac_address_list[2:]

print("Generated MAC Addresses:")
print(f"- Gateway MAC: {gateway_mac}")
print(f"- Master MAC: {master_mac}")
print("- Slave MACs:")
for idx, mac in enumerate(slave_mac_address_list, start=1):
    print(f"  Slave {idx}: {mac}")
print()
slaves = n
print("Initiating BACnet Simulation...\n")
gateway(gateway_mac, master_mac, slave_mac_address_list)