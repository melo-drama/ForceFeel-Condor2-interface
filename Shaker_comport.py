import serial
import sys
import csv
import serial.tools.list_ports
import os


class SerialPort:
    def __init__(self):
        self.comportName = ''
        self.comport = ''
        self.baud = 0
        self.timeout = None
        self.ReceiveCallback = None
        self.isopen = False
        self.receivedMessage = None
        self.serialport = serial.Serial()

        # ---- load ff comport data from default
        data = load_ff_port_data()
        self.comportName, self.baud, self.comport = data
        self.serialport.port = self.comportName
        self.serialport.baudrate = self.baud

    def __del__(self):
        try:
            if self.isopen:
                self.serialport.close()
        except:
            print("Destructor error closing COM port: ", sys.exc_info()[0])

    def IsOpen(self):
        return self.isopen

    def Open(self, portname, baudrate):
        if not self.isopen:
            self.serialport.port = portname
            self.serialport.baudrate = baudrate
            try:
                self.serialport.open()
                self.isopen = True
            except:
                print("Error opening COM port: ", sys.exc_info()[0])

    def Close(self):
        if self.isopen:
            try:
                self.serialport.close()
                self.isopen = False
            except:
                print("Close error closing COM port: ", sys.exc_info()[0])

    def Send(self, message):
        if not self.isopen:
            self.Open(self.comport, self.baud)
        if self.isopen:
            try:
                self.serialport.write(message.encode('utf-8'))
            except:
                print("Error sending message: ", sys.exc_info()[0])
                self.Close()
            else:
                return True
        else:
            return False


def get_COM_port(x):
    ff_com_port = "FF COM port not founded"
    com_port_founded = False
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if x in p.description:
            ff_com_port = p.device
            com_port_founded = True
    return ff_com_port, com_port_founded


def list_COM_ports():
    descriptions = []
    com_ports = []
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        descriptions.append(p.description)
        com_ports.append(p.device)
    # ------- [::-1] => this swaps the list from end to begin
    return descriptions[::-1], com_ports[::-1]


def save_ff_port_data(portname, baudrate, comport):
    with open('ff_port_data.ini','w',newline='') as new_file:
        csv_writer = csv.writer(new_file)
        csv_writer.writerow(['portname', 'baudrate','comport'])
        csv_writer.writerow([portname, baudrate, comport])


def load_ff_port_data():
    filename_table = read_init_file('default.ini')
    if not filename_table == 'N/A':
        ff_port_filename = filename_table[2][1]
    else:
        ff_port_filename = 'ff_port_data.ini'
    with open(ff_port_filename,'r') as filee:
        csv_reader = csv.reader(filee)
        next(csv_reader)
        for row in csv_reader:
            port_name = row[0]
            baudrate = row[1]
            comport = row[2]
    return port_name, baudrate, comport


def read_init_file(filename):
    if os.path.isfile(filename):
        name_table = []
        filename_table =[]
        try:
            with open(filename, 'r') as csv_file:
                filecontent = csv_file.readlines()
                for line in filecontent:
                    current_line = line[:-1]
                    name_table.append(current_line)
        except IOError:
            print("I/O error")
        no_rows = len(name_table)
        for row in range(no_rows):
            filename_table.append(list(name_table[row].split('=')))
        return filename_table
    else:
        return 'N/A'
