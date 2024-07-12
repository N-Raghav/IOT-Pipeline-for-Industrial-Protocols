import pandas as pd
import time
import pika
import csv
import random
from io import StringIO
import multiprocessing

# Load data from CSV files
refer_table = pd.read_csv("ReferenceTableCAN.csv")
response_calculation = pd.read_csv("CANValueCalculation.csv")

rabbitmq_host = '4.144.199.251'  # Replace with your RabbitMQ host on Azure
username = 'newuser'  # Replace with your RabbitMQ username
password = 'password'  # Replace with your RabbitMQ password
port = 5672  
ssl = False
flag = 0



def slave(slaveid,binarydata):
    OBD_FRAME = ['Id', 'Bytes', 'Mode', 'PID', 'A', 'B', 'C', 'D', 'Unused']


    OBD_RESPONSE_BYTES_REFERENCE = {
        "13": "1",
        "12": "2",
        "4": "1",
        "17": "1",
        "3": "2",
        "6": "1",
        "7": "1",
        "8": "1",
        "9": "1",
        "20": "2",
        "21": "2",
        "22": "2",
        "23": "2",
        "24": "2",
        "25": "2",
        "26": "2",
        "27": "2",
        "11": "1",
        "15": "1",
        "16": "2",
        "5": "1",
        "14": "1",
        "10": "1",
        "60": "2",
        "61": "2",
        "50": "2",
        "51": "1",
        "66": "2",
        "44": "1",
        "76": "1",
        "33": "2"
    }


    OBD_PID_MIN_MAX_REFERENCE = {
        "13": [0,255],
        "12": [0,65535],
        "4":  [0,255],
        "17": [0,255],
        "3":  [0,65535],
        "6":  [0,255],
        "7":  [0,255],
        "8":  [0,255],
        "9":  [0,255],
        "20": [0,200],
        "21": [0,200],
        "22": [0,200],
        "23": [0,200],
        "24": [0,200],
        "25": [0,200],
        "26": [0,200],
        "27": [0,200],
        "11": [0,255],
        "15": [0,255],
        "16": [0,65500],
        "5":  [0,255],
        "14": [0,255],
        "10": [0,255],
        "60": [0,65240],
        "61": [0,65240],
        "50": [0,65536],
        "51": [0,255],
        "66": [0,65535],
        "44": [0,255],
        "76": [0,255],
        "33": [0,65535]

    }


    System_status = [0,1,2,4,8,16]



    ID = slaveid 

    unused = 170 #this is fixed to AA(hexa)

    mode = 65 #thsis is fixed to 65
    #convert raw data to request
    """
    take the rawdata sent by the master
    convert the 72bit raw binary data into 9 bytes as a list 
    the order of these 9bytes follows the obd2 frame format
    return this list
    """
    def raw_data_to_request(rawbits):
        decimal_values = []
        
        #handling can id
        first_11_bits = rawbits[:11]
        decimal_values.append(int(first_11_bits, 2))
        
        #handiling others
        remaining_bits = rawbits[11:]
        for i in range(0, len(remaining_bits), 8):
            block = remaining_bits[i:i+8]
            decimal_values.append(int(block, 2))
        
        #print("Request:")
        #print(decimal_values)
        return decimal_values
    


    #convert response into raw data
    """
    take the resposne list form the slave
    convert that into a binary string
    return the binary string
    """
    def response_to_raw_data(response):
        binary_list = []
        
        # Converting the canid into an 11-bit binary string
        first_binary_value = bin(response[0])[2:]
        first_binary_value = first_binary_value.zfill(11)
        binary_list.append(first_binary_value)
        
        # Converting the rest of the elements into 8-bit binary strings
        for decimal_value in response[1:]:
            binary_value = bin(decimal_value)[2:]
            binary_value = binary_value.zfill(8)
            binary_list.append(binary_value)
        
        
        result = ''.join(binary_list)
        
        return result

	
	
	
    #response generation logic
    """
    recive the raw binary data from the master,ie teh masters request
    pass that requst to raw_data_to_request funtion to get back the decimal value conversion list
    parse the pid value in the list and apply the logic to generate the response
    the response will be genarted based on the bytes refrence json
    afetr the respone list is generated the list is passed on to the response_to_raw_data funtion
    the resulting resposne as a binary data will be sent back to the master
    """	
    def generate_response(rawbits):
        request = raw_data_to_request(rawbits)

        # canid
        # bytes
        # mode
        pid = int(request[3])
        A = 170
        B = 170
        C = 170
        D = 170
        unused = 0

        #print("pid:" + str(pid))

        bytes = OBD_RESPONSE_BYTES_REFERENCE.get(str(pid))
        if bytes is None:
            #print(f"Warning: PID {pid} is not supported. Setting response to all 1's.")
            response = '1' * 56  
            return response

        bytes = int(bytes)
        
        if pid == 3:
            response_warning = random.choice(System_status)
            A = response_warning
            B = A
        else:
            if str(pid) in OBD_PID_MIN_MAX_REFERENCE:
                min_val, max_val = OBD_PID_MIN_MAX_REFERENCE[str(pid)]
                data = random.randint(min_val, max_val)
            
            if bytes == 1:
                A = data
            elif bytes == 2:
                binary_data = bin(data)[2:].zfill(16)
                first_8_bits = binary_data[:8]
                second_8_bits = binary_data[8:]
                A = int(first_8_bits, 2)
                B = int(second_8_bits, 2)
            elif bytes == 3:
                binary_data = bin(data)[2:].zfill(24)
                first_8_bits = binary_data[:8]
                second_8_bits = binary_data[8:16]
                third_8_bits = binary_data[16:]
                A = int(first_8_bits, 2)
                B = int(second_8_bits, 2)
                C = int(third_8_bits, 2)
            elif bytes == 4:
                binary_data = bin(data)[2:].zfill(32)
                first_8_bits = binary_data[:8]
                second_8_bits = binary_data[8:16]
                third_8_bits = binary_data[16:24]
                fourth_8_bits = binary_data[24:]
                A = int(first_8_bits, 2)
                B = int(second_8_bits, 2)
                C = int(third_8_bits, 2)
                D = int(fourth_8_bits, 2)

        response = [ID, bytes, mode, pid, A, B, C, D, unused]
        #print("response:")
        #print(response)

        result = response_to_raw_data(response)

        return result
        
    raw_data = binarydata
    #print("Request:", raw_data)
    response = generate_response(raw_data)
    #print("Response:", response)
    return response

def master(masterid,slaveid):
    MODE=1
    DEFAULT_VALUE=170
    df_response=[]
    response_binary = ""
    # Creating a PID value to number of bytes mapping using a dictionary
    PID_to_bytes_mapping = {refer_table['PID'][i]: refer_table['Bytes'][i] for i in range(len(refer_table['PID']))}

    # Converting the decimal values in the frame to a 72-bit long binary value for transfer
    def frame_decimal_to_binary_converter(frame):
        can_id_binary = format(frame[0], '011b')
        binary_strings = [format(value, '08b') for value in frame[1:]]
        combined_binary_string = can_id_binary + ''.join(binary_strings)
        return combined_binary_string

    # Converting the response binary value to decimal in the response frame packet structure
    def binary_to_decimal_frame_converter(binary):
        response_frame = []
        can_id = int(binary[:11], 2)
        response_frame.append(can_id)
        for i in range(11, len(binary), 8):
            block = binary[i:i+8]
            response_frame.append(int(block, 2))
        return response_frame

    # This is the main request function where requests are sent for each PID in the frame format of CAN
    def master_request():
        PID_values = refer_table['PID']

        def request(PID):
            request_frame = [masterid, PID_to_bytes_mapping[PID], MODE, PID, DEFAULT_VALUE, DEFAULT_VALUE, DEFAULT_VALUE, DEFAULT_VALUE, DEFAULT_VALUE]
            request_binary = frame_decimal_to_binary_converter(request_frame)
            response_binary=slave(slaveid,request_binary)
            master_response(response_binary)
        for pid in PID_values:
            request(pid)

    def master_response(response_binary):
        response_frame = binary_to_decimal_frame_converter(response_binary)
        response_PID = response_frame[3]
        response_Length = response_frame[1]
        
        if response_PID == 3:
            response_value = response_frame[4]
        else:
            if response_Length == 1:
                response_value = response_frame[4]
            elif response_Length == 2:
                response_value = response_frame[4:6]
            else:
                response_value = response_frame[4:4+response_Length]
        
        final_response_output(response_PID, response_value)



    def final_response_output(response_PID, response_value):
        
        if isinstance(response_value, list):
            x = ''.join(format(value, '08b') for value in response_value)
        else:
            x = format(response_value, '08b')
        
        response_output = int(x, 2)
        offset = response_calculation.loc[response_calculation['PID'] == response_PID, 'Offset'].values[0]
        scale = response_calculation.loc[response_calculation['PID'] == response_PID, 'Scale'].values[0]
        final_response_value = offset + scale * response_output
        

        
        parameter_name = refer_table.loc[refer_table['PID'] == response_PID, 'Parameter name'].values[0]
        units = refer_table.loc[refer_table['PID'] == response_PID, 'Units'].values[0]
        
    
            
        updated = False
        for i, entry in enumerate(df_response):
            if entry['Parameter Name'] == parameter_name and entry['Units'] == units:
                df_response[i]['Value'] = final_response_value
                updated = True
                break
        
        if not updated:
            df_response.append({
                'Parameter Name': parameter_name,
                'Value': final_response_value,
                'Units': units
            })

        #print(parameter_name, final_response_value, units)


    master_request()
    return df_response
            
def gateway(can_ids):
    gatewayid,masterid,slaveid=can_ids[0],can_ids[1],can_ids[2]
    data=pd.DataFrame(master(masterid,slaveid))
    #print(data)
    csv_buffer = StringIO()
    data.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    #print(csv_content)
    
    QUEUE_NAME = str(gatewayid)

    def send_csv_to_rabbitmq(csv_content, queue_name, rabbitmq_host, username, password, port=5672, ssl=False):
        
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

        # Send each line of the CSV file to RabbitMQ
        for line in csv_content.split('\n'):
            # Skip empty lines
            if not line.strip():
                continue
            channel.basic_publish(exchange='', routing_key=queue_name, body=line)

        connection.close()
    send_csv_to_rabbitmq(csv_content,QUEUE_NAME, rabbitmq_host, username, password, port, ssl)
    #print("Data sent to RabbitMQ")
    #print("One set of values sent")
    
def can_id_generation(n):
    def generate_random_numbers(n):
        can_ids = set()
        while len(can_ids) < 3 * n:
            can_ids.add(random.randint(1, 2000))
        return list(can_ids)

    def create_dataframe_and_convert_to_csv(random_numbers, n):
        data = {
            'gateway_id': random_numbers[:n],
            'master_id': random_numbers[n:2*n],
            'slave_id': random_numbers[2*n:3*n]
        }
        df = pd.DataFrame(data)
        
        return df
    
    return create_dataframe_and_convert_to_csv(generate_random_numbers(n), n)

def simulate_pipeline(n,canids_dataframe):
    global flag
    processes = []
    
    canids_list=canids_dataframe.values.tolist()
    gateway_ids_list = []
    
    for i in range(n):
        param_list = canids_list[i]
        gateway_ids_list.append(canids_list[i][0])
        
        process = multiprocessing.Process(target=gateway, args=(param_list,))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    #print("All sub processes have completed")
    
    if(flag == 0):
        #print("sending the gateway ids to rabbit")
        
        #send each element in thee gateway id list to rabbitmq
        def send_csv_to_rabbitmq(gateway_ids_list, queue_name, rabbitmq_host, username, password, port=5672, ssl=False):
            
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

            # Send each line of the CSV file to RabbitMQ
            for id in gateway_ids_list:
                channel.basic_publish(exchange='', routing_key=queue_name, body=str(id))

            connection.close()
        send_csv_to_rabbitmq(gateway_ids_list,"available_gateway_ids", rabbitmq_host, username, password, port, ssl)
        #print("gateway ids are sent to RabbitMQ")
        flag = 1
        

slaves = int(input("Enter the number of cars for which the data is to be simulated:"))
canids_dataframe = can_id_generation(slaves)
while True:
    simulate_pipeline(slaves,canids_dataframe)
    print("Data sent successfully!")
    time.sleep(slaves*10)
    
    