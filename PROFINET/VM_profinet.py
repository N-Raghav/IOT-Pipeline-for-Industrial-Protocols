import pika
import csv
import requests
import time




bucket_name = "Profinet"
measurement_name = "Profinet_data"
influx_url = "https://us-east-1-1.aws.cloud2.influxdata.com/api/v2/write?org=bdeb9ddd4be33c75&bucket=" + bucket_name
token = "zoFb5ykKtRGhxeWWMQxMeIGA-pq3e2pH_O_OvWPofcfF_aRmFVkqYx6jxW47WIP-TSNkPZKiQNIEprV3OGGyFQ=="

QUEUE_NAME = "PROFINET_DATA"

user = 'newuser'  # Replace with your RabbitMQ username
password = 'password'  # Replace with your RabbitMQ password

def send_data_to_influxdb(data):
    #print("data:" + data)
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
    rotor_speed = row[3]
    vibration_levels = row[2]
    temperature_bearings = row[3]
    power_output = row[4]
    
def line_protocol_maker(csv_line):
    # Split the CSV line into individual values
    row = csv_line.split(',')
    
    # Extract the values from the CSV line
    gateway_id = row[0].strip()
    master_id = row[1].strip()
    slave_id = row[2].strip()
    rotor_speed = float(row[3].strip())  # Assuming rotor_speed is a float
    vibration_levels = float(row[4].strip())  # Correct index for vibration_levels
    temperature_bearings = float(row[5].strip())  # Correct index for temperature_bearings
    power_output = float(row[6].strip())  # Assuming power_output is a float
    
    # Construct the line protocol
    line_protocol = (
        f"{measurement_name},GatewayID={gateway_id},MasterID={master_id},SlaveID={slave_id} "
        f"RotorSpeed={rotor_speed},VibrationLevels={vibration_levels},TemperatureBearings={temperature_bearings},PowerOutput={power_output}"
    )

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
