import socket
import base64


def read_lines():
    global client_socket
    lines_buffer = ""
    data = True
    while data:
        try:
            data = client_socket.recv(4096)
            lines_buffer += data
        except socket.timeout:
            break
    return lines_buffer


print("thermeq3 delete device from MAX!Cube\n")
# please edit max cube address
max_ip = "192.168.0.200"
# please edit device for deletion
dev_id = "DEAD01"
print("Deleting device id: " + dev_id + "from MAX!Cube with IP: " + max_ip)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.settimeout(2)
client_socket.connect((max_ip, 62910))

result = read_lines()

dev_id_plain = bytearray.fromhex(dev_id).decode()
message = "t:01,1," + base64.b64encode(dev_id_plain) + "\r\n"
client_socket.sendall(message)

# result must be "A:"
print("Command issued. Please read result. Result must begin with A:\n----------")
print read_lines()
client_socket.close()
