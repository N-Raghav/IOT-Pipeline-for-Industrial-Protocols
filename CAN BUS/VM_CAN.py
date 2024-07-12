import pika
import csv
import requests
import time


bucket_name = "CAN"
measurement_name = "Can_data"
influx_url = "https://us-east-1-1.aws.cloud2.influxdata.com/api/v2/write?org=your_org_id&bucket=" + bucket_name
token = "v6yyfWMqraoHsYdAp7CAngZUOheySCIlkqe0nfmsFHoqLM8B9TLaWBimOBZjrSxUzAi5pSH5xbtxGPagDxBqzA=="

    
def send_data_to_influxdb(data):
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


def line_protcol_maker(csv_line,gatewayid):
    row = csv_line.split(',')
    line_protocol = f"{measurement_name},Gateway_id={gatewayid} {row[0].replace(' ', '_')}={row[1]}\n"
    return line_protocol

def callback(ch, method, properties, body, queue_name):
    data = body.decode()
    print(data)
    data = line_protcol_maker(data,queue_name)
    send_data_to_influxdb(data)
    print("--------------------------------------")

def main():

    credentials = pika.PlainCredentials('newuser', 'password')


    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', credentials=credentials))
    channel = connection.channel()


    channel.queue_declare(queue=QUEUE_NAME)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

if __name__ == '__main__':
    main()


