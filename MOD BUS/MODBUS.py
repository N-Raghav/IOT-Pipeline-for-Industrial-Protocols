import random
import time
import pika
import multiprocessing

rabbitmq_host = '127.0.0.1'  # Replace with your RabbitMQ host on Azure
username = 'Bhargav'  # Replace with your RabbitMQ username
password = 'admin'  # Replace with your RabbitMQ password
port = 5672  
ssl = False
flag = 0
n = 0

QUEUE_NAME = "MODBUS_DATA"

def calculate_lrc(data):
    lrc = 0
    for byte in data:
        lrc += byte
    lrc = ((lrc ^ 0xFF) + 1) & 0xFF
    return lrc


def generate_ids(n):
    if n > 255:
        print("Only 255 unique slave IDs are allowed. Generating 255 unique slave IDs instead.")
        n = 255

    slave_ids = set()  
    while len(slave_ids) < n:

        slave_id = '{:02X}'.format(random.randint(1, 255))  
        slave_ids.add(slave_id)

    slave_ids_list = list(slave_ids)

    gateway_id = random.randint(1, 255)
    master_id = random.randint(1, 255)

    return gateway_id, master_id, slave_ids_list

def decode_request(request):
    if request.startswith(':') and request.endswith('\r\n'):
        frame = request[1:-2]  
        slave_id = frame[0:2]
        function_code = frame[2:4]
        starting_address = frame[4:8]
        quantity_of_registers = frame[8:12]
        lrc = frame[12:14]

        message_without_lrc = bytearray.fromhex(frame[:-2])
        calculated_lrc = calculate_lrc(message_without_lrc)
        if calculated_lrc != int(lrc, 16):
            return None, None, "LRC Error"

        return slave_id, function_code, None
    else:
        return None, None, "Invalid frame"

def generate_response(slave_id, function_code):
    voltage = random.randint(1000, 65535)
    current = random.randint(0, 65535)

    voltage_bytes = voltage.to_bytes(2, byteorder='big')
    current_bytes = current.to_bytes(2, byteorder='big')

    data = voltage_bytes + current_bytes
    byte_count = len(data)

    response = bytearray()
    response.append(int(slave_id, 16))
    response.append(int(function_code, 16))
    response.append(byte_count)
    response.extend(data)

    lrc = calculate_lrc(response)
    response.append(lrc)

    ascii_response = ':' + ''.join(f'{byte:02X}' for byte in response) + '\r\n'
    return ascii_response

def create_request_frame(slave_id, start_address, quantity_of_registers):
    frame = [
        int(slave_id, 16),
        0x04,  
        (start_address >> 8) & 0xFF,  
        start_address & 0xFF,         
        (quantity_of_registers >> 8) & 0xFF,  
        quantity_of_registers & 0xFF,         
    ]

    lrc = calculate_lrc(frame)
    frame.append(lrc)

    ascii_frame = ':' + ''.join(f'{byte:02X}' for byte in frame) + '\r\n'
    return ascii_frame

def decode_response(response):
    if response.startswith(':') and response.endswith('\r\n'):
        frame = response[1:-2]  
        slave_id = frame[0:2]
        function_code = frame[2:4]
        byte_count = int(frame[4:6], 16)
        data = frame[6:6 + 2 * byte_count]
        lrc = frame[6 + 2 * byte_count:]

        message_without_lrc = bytearray.fromhex(frame[:-2])
        calculated_lrc = calculate_lrc(message_without_lrc)
        if calculated_lrc != int(lrc, 16):
            return None, "LRC Error"

        voltage = int.from_bytes(bytes.fromhex(data[0:4]), byteorder='big')
        current_raw = int.from_bytes(bytes.fromhex(data[4:8]), byteorder='big')

        current = current_raw / 100.0

        return {"slave_id": slave_id, "voltage": voltage, "current": current}, None
    else:
        return None, "Invalid frame"

def master(slave_ids):
    data = []
    start_address = 0x0000
    quantity_of_registers = 0x0002

    for slave_id in slave_ids:
            request_frame = create_request_frame(slave_id, start_address, quantity_of_registers)
            #print("Slave ID:", slave_id)
            #print("Request Frame:", request_frame)

            response_frame = generate_response(slave_id, '04')  
            #print("Response Frame:", response_frame)

            response_data, error = decode_response(response_frame)

            if error:
                print("Error:", error)
            #else:
                #print("Voltage:", response_data["voltage"])
                #print("Current: {:.2f}".format(response_data["current"]))  
            
            slave_data = [str(slave_id),str(response_data["voltage"]),("{:.2f}".format(response_data["current"]))]
            data.append(slave_data)
    return data
            
def gateway(gatewayid,masterid,slaveids):

    

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
        data = master(slaveids)
        for item in data:
            current = str(item[2])
            voltage = str(item[1])
            slaveid = str(item[0])

            line = str(gatewayid) + "," + str(masterid) + "," + slaveid + "," + voltage + "," + current
            send_to_rabbitmq(line,QUEUE_NAME, rabbitmq_host, username, password, port, ssl)
        
        print("Data sent to RabbitMQ")
        print("One set of values sent")
        time.sleep(n)
         

n = int(input("Enter the number of slaves: "))
gateway_id, master_id, slave_ids = generate_ids(n)
# print("Gateway ID:", gateway_id)
# print("Master ID:", master_id)
# print("slave ID:",slave_ids)
# print("starting")

gateway(gateway_id,master_id,slave_ids)

