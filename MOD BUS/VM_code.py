import pika
import csv
import requests
import time




bucket_name = "MODBUS"
measurement_name = "Modbus_data"
influx_url = "https://us-east-1-1.aws.cloud2.influxdata.com/api/v2/write?org=your_org_id&bucket=" + bucket_name
token = "v6yyfWMqraoHsYdAp7CAngZUOheySCIlkqe0nfmsFHoqLM8B9TLaWBimOBZjrSxUzAi5pSH5xbtxGPagDxBqzA=="

QUEUE_NAME = "MODBUS_DATA"

user = "Bhargav"
password = "admin"
    
def send_data_to_influxdb(data):
    print("data:" + data)
    headers = {
        "Authorization": "Token " + token,
        "Content-Type": "text/plain"
    }
    url = influx_url + "&precision=s"
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 204:
       print("Data sent successfully.")
    else:
        print("Failed to send data. Status code:", response.status_code)
	

def line_protocol_maker(csv_line):
    # Split the CSV line into individual values
    row = csv_line.split(',')
    
    # Extract the values from the CSV line
    gateway_id = row[0]
    master_id = row[1]
    slave_id = row[2]
    voltage = row[3]
    current = row[4]
    
    # Construct the line protocol
    line_protocol = f"Modbus_data,GatewayID={gateway_id},MasterID={master_id},SlaveID={slave_id} voltage={voltage},current={current}"
    
    return line_protocol




def send_data_of_a_gateway_to_influx():
    def send_to_rabbitmq():
        credentials = pika.PlainCredentials(user, password)
        connection = pika.BlockingConnection(pika.ConnectionParameters("127.0.0.1", credentials=credentials))
        channel = connection.channel()
        method_frame, header_frame, body = channel.basic_get(queue=QUEUE_NAME, auto_ack=True)
        if method_frame:
            return body.decode()
        else:
            return "NO DATA!"

    while True:
        queue_content = send_to_rabbitmq()
        if queue_content!="NO DATA!":
            send_data_to_influxdb(line_protocol_maker(queue_content))
    




    
    
def simulate_Rabbit_to_cloud_sender():
    while True:
        send_data_of_a_gateway_to_influx()



#first wait until data is sent to the server or else we will misss some gateway ids
print("VM HANDLER RUNNING")
simulate_Rabbit_to_cloud_sender()
