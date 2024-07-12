import random
import pika 
import time 

rabbitmq_host = '127.0.0.1'  # Replace with your RabbitMQ host on Azure
username = 'Bhargav'  # Replace with your RabbitMQ username
password = 'admin'  # Replace with your RabbitMQ password
port = 5672  
ssl = False
flag = 0

QUEUE_NAME = "PROFINET_DATA"
slaves = 0



def generate_mac_addresses(n):
    mac_addresses = set()
    while len(mac_addresses) < n + 2:
        mac = ':'.join(['{:02x}'.format(random.randint(0x00, 0xff)) for _ in range(6)])
        mac_addresses.add(mac)
    return list(mac_addresses)

def profinet_slave(request_message, slave_mac):

    rotor_speed = random.randint(0, 1000)
    vibration_levels = random.randint(0, 10)
    temperature_bearings = random.randint(0, 100)
    power_output = random.randint(0, 1000)

    response = {
        'rotor_speed': rotor_speed,
        'vibration_levels': vibration_levels,
        'temperature_bearings': temperature_bearings,
        'power_output': power_output
    }

    #print(f"Raw Response from Slave {slave_mac}:\n{response}")

    return response

def profinet_master(master_mac, slave_mac_address_list):
    data = []

    for slave_mac in slave_mac_address_list:

        broadcast_request = {
            'source_mac': master_mac,
            'destination_mac': 'FF:FF:FF:FF:FF:FF',  
            'ether_type': '0x8892',
            'service_id': '0x05',
            'service_type': '0x00',
            'xid': '<Transaction ID>',
            'response_delay': '<Time in ms>',
            'requesting_slave_mac': slave_mac
        }

        #print(f"Raw Broadcast Request from Master {master_mac} to Slave {slave_mac}:\n{broadcast_request}")

        response = profinet_slave(broadcast_request, slave_mac)

        rotor_speed = response['rotor_speed']
        vibration_levels = response['vibration_levels']
        temperature_bearings = response['temperature_bearings']
        power_output = response['power_output']

        # print("\nExtracted Fields from Response:")
        # print(f"- Rotor Speed: {rotor_speed}")
        # print(f"- Vibration Levels: {vibration_levels}")
        # print(f"- Temperature Bearings: {temperature_bearings}")
        # print(f"- Power Output: {power_output}")
        # print() 
        sensor_data = [slave_mac,rotor_speed,vibration_levels,temperature_bearings,power_output]
        data.append(sensor_data)

    return data

def gateway(gateway_mac,master_mac,slave_mac_address_list):
    
    
    def send_to_rabbitmq(line, queue_name, rabbitmq_host, username, password, port=5672, ssl=False):
        
        # Connect to RabbitMQ server
        credentials = pika.PlainCredentials(username, password)
        
        # Connection parameters with SSL if needed
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
        data = profinet_master(master_mac, slave_mac_address_list)
        for item in data:
                slave_mac=str(item[0])
                rotor_speed = str(item[1])
                vibration_levels = str(item[2])
                temperature_bearings = str(item[3])
                power_output = str(item[4])
                line = str(gateway_mac) + "," + str(master_mac) + "," + slave_mac + "," + rotor_speed + "," + vibration_levels + ","+temperature_bearings+","+power_output
                send_to_rabbitmq(line,QUEUE_NAME, rabbitmq_host, username, password, port, ssl)
              
        
        print("Data sent to RabbitMQ")
        print("One set of values sent")
        time.sleep(slaves * 2)
         




n = int(input("enter the number of slaves:"))
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
slaves=n
print("Initiating PROFInet Simulation...\n")
gateway(gateway_mac,master_mac,slave_mac_address_list)
    

