
import socket
import ast
import queue
import Condor2_profile as ffprof
import Shaker_comport as ffcom

UDP_IP = "127.0.0.1"
UDP_SOCK_TIMEOUT = 0.2
UDP_PORT = 55278
UDP_DATA_LOOPS = 10
# main window loop timeout in ms
TIMEOUT = 250

FILTER_COEF = 1
FLT_MIN = 0.1
FLT_MAX = 0.2
MOT_MIN = 0
MOT_MAX = 0

# NO_ROWS_MAX = 34
# NO_NEW_FUNCTIONS = 13


class CondorUDP:

    def __init__(self, ser):
        self.sock = socket.socket()
        self.udp_com = False
        self.udp_binded = False
        self.profile = ffprof.Profiler()
        self.profile_table = self.profile.profile_table
        self.ser = ser
        self.ff_com_open = False
        self.com_pause = True
        self.udp_time_old = 0.0

    # ----- __init__(self) ends here ---------------------

    def check_udp(self):
        udp_transfer = False
        self.sock = socket.socket(socket.AF_INET,  # Internet
                                  socket.SOCK_DGRAM)  # UDP
        self.sock.bind((UDP_IP, UDP_PORT))
        if udp_transfer == False:
            self.sock.settimeout(UDP_SOCK_TIMEOUT)
            try:
                test_data = self.sock.recvfrom(1024)
                udp_transfer = True
                self.com_pause = False
                self.sock.close()
            except socket.timeout:
                udp_transfer = False
        return udp_transfer

    def condor_udp_data_arrays(self):
        # --------- Start create_data_arrays---------
        strdata = (
            'time=0.0\r\nairspeed=0.0\r\naltitude=0.0\r\nvario=-0.0\r\nevario=-0.0\r\nnettovario=-0.0\r\n'
            'integrator=0.0\r\ncompass=0.0\r\nslipball=-0.0\r\nturnrate=0.0\r\nyawstringangle=-0.0\r\n'
            'radiofrequency=0.0\r\nyaw=0.0\r\npitch=0.0\r\nbank=0.0\r\nquaternionx=-0.0\r\nquaterniony=0.0\r\n'
            'quaternionz=-0.0\r\nquaternionw=0.0\r\nax=-0.0\r\nay=0.0\r\naz=-0.0\r\nvx=-0.0\r\nvy=0.0\r\nvz=0.0\r\n'
            'rollrate=0.0\r\npitchrate=0.0\r\nyawrate=0.0\r\ngforce=0.0\r\nheight=0.0\r\nwheelheight=0.0\r\n'
            'turbulencestrength=0.0\r\nsurfaceroughness=0.0\r\n')
        str_len = len(strdata)
        no_lines = strdata.count('\r\n')
        data_dict = {}
        val_end = -2
        count = 0
        while count < no_lines:
            # update begin part
            new_start = val_end + 2
            val_beg = strdata.index('=', new_start)
            val_end = strdata.index('\r', new_start)
            float_value = float(strdata[(val_beg + 1):(val_end)])
            float_value = round(float_value, 5)
            str_temp = strdata[new_start:(val_beg + 1)]
            str_temp = str_temp[:-1]
            # --- create data dictionary
            data_dict[str_temp] = {'actual': float_value, 'flt_min': 0.0, 'flt_max': 0.0,
                                   'filtercoeff': FILTER_COEF, 'flt_min_limit': 0.0,
                                   'flt_max_limit': 0.0, 'mot_min_limit': 0,
                                   'mot_max_limit': 0, 'M_act': 0, 'Motors': ''}
            if count == 0:
                if str_temp == 'time':
                    data_dict[str_temp]['filtercoeff'] = 1
            count = count + 1
            # create new function rollrate_left, rollrate_right, pitch_up and pitch_down, Flutter and Turbulence
            data_dict['rollrate_left'] = {'actual': 0.0, 'flt_min': 0.0, 'flt_max': 0.0,
                                              'filtercoeff': FILTER_COEF, 'flt_min_limit': FLT_MIN,
                                              'flt_max_limit': FLT_MAX, 'mot_min_limit': MOT_MIN,
                                              'mot_max_limit': MOT_MAX, 'M_act': 0, 'Motors': ''}
            data_dict['rollrate_right'] = {'actual': 0.0, 'flt_min': 0.0, 'flt_max': 0.0,
                                              'filtercoeff': FILTER_COEF, 'flt_min_limit': FLT_MIN,
                                              'flt_max_limit': FLT_MAX, 'mot_min_limit': MOT_MIN,
                                              'mot_max_limit': MOT_MAX, 'M_act': 0, 'Motors': ''}
            data_dict['pitchrate_up'] = {'actual': 0.0, 'flt_min': 0.0, 'flt_max': 0.0,
                                              'filtercoeff': FILTER_COEF, 'flt_min_limit': FLT_MIN,
                                              'flt_max_limit': FLT_MAX, 'mot_min_limit': MOT_MIN,
                                              'mot_max_limit': MOT_MAX, 'M_act': 0, 'Motors': ''}
            data_dict['pitchrate_down'] = {'actual': 0.0, 'flt_min': 0.0, 'flt_max': 0.0,
                                              'filtercoeff': FILTER_COEF, 'flt_min_limit': FLT_MIN,
                                              'flt_max_limit': FLT_MAX, 'mot_min_limit': MOT_MIN,
                                              'mot_max_limit': MOT_MAX, 'M_act': 0, 'Motors': ''}
            data_dict['yawrate_left'] = {'actual': 0.0, 'flt_min': 0.0, 'flt_max': 0.0,
                                           'filtercoeff': FILTER_COEF, 'flt_min_limit': FLT_MIN,
                                           'flt_max_limit': FLT_MAX, 'mot_min_limit': MOT_MIN,
                                           'mot_max_limit': MOT_MAX, 'M_act': 0, 'Motors': ''}
            data_dict['yawrate_right'] = {'actual': 0.0, 'flt_min': 0.0, 'flt_max': 0.0,
                                         'filtercoeff': FILTER_COEF, 'flt_min_limit': FLT_MIN,
                                         'flt_max_limit': FLT_MAX, 'mot_min_limit': MOT_MIN,
                                         'mot_max_limit': MOT_MAX, 'M_act': 0, 'Motors': ''}
            data_dict['Flutter'] = {'actual': 0.0, 'flt_min': 0.0, 'flt_max': 0.0,
                                          'filtercoeff': FILTER_COEF, 'flt_min_limit': FLT_MIN,
                                          'flt_max_limit': FLT_MAX, 'mot_min_limit': MOT_MIN,
                                          'mot_max_limit': MOT_MAX, 'M_act': 0, 'Motors': ''}
            data_dict['Wheelshake'] = {'actual': 0.0, 'flt_min': 0.0, 'flt_max': 0.0,
                                          'filtercoeff': FILTER_COEF, 'flt_min_limit': FLT_MIN,
                                          'flt_max_limit': FLT_MAX, 'mot_min_limit': MOT_MIN,
                                          'mot_max_limit': MOT_MAX, 'M_act': 0, 'Motors': ''}
            data_dict['Turbulence'] = {'actual': 0.0, 'flt_min': 0.0, 'flt_max': 0.0,
                                       'filtercoeff': FILTER_COEF, 'flt_min_limit': FLT_MIN,
                                       'flt_max_limit': FLT_MAX, 'mot_min_limit': MOT_MIN,
                                       'mot_max_limit': MOT_MAX, 'M_act': 0, 'Motors': ''}
        return data_dict

    def parser_condor_telemetry(self, strdata, data_dict):
        # Start parsering
        temp_list2 = []
        data_dict_new = data_dict
        temp_list = list(strdata.split('\r\n'))
        for row in range(len(temp_list)):
            table = list(temp_list[row].split('='))
            temp_list2.append(table)
        for row_list in temp_list2:
            if row_list[0] in data_dict_new:
                float_value = float(row_list[1])
                data_dict_new[row_list[0]]['actual'] = float_value
        if 'time' in data_dict_new:
            data_dict_new['time']['filtercoeff'] = 1
        return data_dict_new

    def datafilter(self, data_dict_old, data_dict_parsered):
        data_dict_new = data_dict_parsered
        no_lines = len(data_dict_parsered)
        data_names = list(data_dict_parsered.keys())
        for row in range(1, no_lines):
            data_old = data_dict_old.get(data_names[row])['actual']
            data_parsered = data_dict_parsered.get(data_names[row])['actual']
            filter_coeff = data_dict_parsered.get(data_names[row])['filtercoeff']
            data_filtered = (1 - 1 / filter_coeff) * data_old + (1 / filter_coeff) * data_parsered
            data_dict_new[data_names[row]]['actual'] = data_filtered
        return data_dict_new

    def get_udp_data(self):
        # start looping UDP and sound creating tasks
        # default strdta_udp string => all values are 0.0
        strdata_udp = ''
        strdata_udp_temp = (
            'time=0.0\r\nairspeed=0.0\r\naltitude=0.0\r\nvario=-0.0\r\nevario=-0.0\r\nnettovario=-0.0\r\n'
            'integrator=0.0\r\ncompass=0.0\r\nslipball=-0.0\r\nturnrate=0.0\r\nyawstringangle=-0.0\r\n'
            'radiofrequency=0.0\r\nyaw=0.0\r\npitch=0.0\r\nbank=0.0\r\nquaternionx=-0.0\r\nquaterniony=0.0\r\n'
            'quaternionz=-0.0\r\nquaternionw=0.0\r\nax=-0.0\r\nay=0.0\r\naz=-0.0\r\nvx=-0.0\r\nvy=0.0\r\nvz=0.0\r\n'
            'rollrate=0.0\r\npitchrate=0.0\r\nyawrate=0.0\r\ngforce=0.0\r\nheight=0.0\r\nwheelheight= 0.0\r\n'
            'turbulencestrength=0.0\r\nsurfaceroughness=0.0\r\n')
        if not self.udp_com:
            self.udp_com = self.check_udp()
        if not self.udp_binded:
            try:
                if self.udp_com:
                    self.sock = socket.socket(socket.AF_INET,  # Internet
                                              socket.SOCK_DGRAM)  # UDP
                    self.sock.bind((UDP_IP, UDP_PORT))
                    self.udp_binded = True
            except:
                self.udp_binded = False
        if self.udp_com and self.udp_binded:
            try:
                data, addr = self.sock.recvfrom(1024)  # buffer size is 1024 bytes
                strdata_udp = data.decode('utf-8')
            except socket.timeout:
                self.udp_com = False
                self.sock.close()
        if strdata_udp == '':
            self.com_pause = True
            strdata_udp = strdata_udp_temp
            self.udp_com = False
        return strdata_udp

    def udp_and_motor(self, q_data, q_udp_status, q_startpause, lock, ser, portname, baudrate):
        data_dict = {}
        self.udp_binded = False
        startpause = False
        lock.acquire()
        #  Task 0: function init:  get and check q_param queue status
        if not q_startpause.empty():
            startpause = q_startpause.get()  # check start_stop status
        # # open q_data queue and get data_dict dictionary from there
        if not q_data.empty():
            data_dict = q_data.get()
        lock.release()
        # --------- start actual function loop -----------------------------
        # check udp communication
        self.udp_com = self.check_udp()
        lock.acquire()
        if not ser.isopen:
            ser.Open(portname, baudrate)
            ser.Send('M00\rM10\rM20\rM30\rM40\rM50\rM60\rM70\r')
            self.ff_com_open = True
        lock.release()
        datadict_old = data_dict
        strdata_old = ''
        while startpause:
            # ------------ get_udp_data(UDP_check) ---------------------------
            # start looping UDP and sound creating tasks
            for i in range(UDP_DATA_LOOPS):
                # -------------get_udp_data end, return strdata--------------------
                strdata = self.get_udp_data()
                # --  bypass data parsering if udp datastring strdata is longer than expected
                datadict_parsered = self.parser_condor_telemetry(strdata, datadict_old)
                strdata_old = strdata
                # --- datafiltering with filtercoeff table
                datadict_filtered = self.datafilter(datadict_old, datadict_parsered)
                #  add new functions that are not founded from the Condor UDP data string
                # create new datadict that contains these functions (= datadict_final)
                datadict_final = self.update_new_functions(datadict_filtered)
                datadict_old = datadict_final
                # ------ function3: data to motor control  conversion
                datadict_final = self.data_to_motor(datadict_final)
                # ----- optional control functions and filtering comes here -------
                # ------ function4:  ForceFeel motor control, create motor control command string
                # ------ as output (=motor_control_str)
                motor_control_str = self.create_ff_string(datadict_final)
                # ------ Send motor control string to ForceFeel comport and stop all motors if
                # ------ UDP communication or monitoring are paused. Prevent other functions to use
                # ------ Send function at the same time using lock.acquire() and lock.releese() functions
                lock.acquire()
                if startpause and self.udp_com:
                    ser.Send(motor_control_str)
                else:
                    ser.Send('M00\rM10\rM20\rM30\rM40\rM50\rM60\rM70\r')
                lock.release()
                #  Loop function1-4:  x times
            # ---------- function5:   update q_data => main function will use this queue
            lock.acquire()
            # clear q_data queue
            while not q_data.empty():
                x = q_data.get()
            q_data.put(datadict_final)
            # check q_startpause status
            if not q_startpause.empty():
                startpause = q_startpause.get()
            lock.release()
        if not startpause:
            lock.acquire()
            if ser.isopen:
                # ---- Stop all motors ---------------
                ser.Send('M00\rM10\rM20\rM30\rM40\rM50\rM60\rM70\r')
                ser.Close()
                self.ff_com_open = False
            lock.release()
        lock.acquire()
        while not q_udp_status.empty():
            temp = q_udp_status.get()
        q_udp_status.put(self.udp_com)
        lock.release()
        # ------------- start_stop loop end here ---------------------------

    def update_new_functions(self, datadict_filtered):
        rollrate_left = 0.0
        rollrate_right = 0.0
        pitchrate_up = 0.0
        pitchrate_down = 0.0
        yawrate_left = 0.0
        yawrate_right = 0.0
        flutter = 0.0
        wheelshake= 0.0
        turbulence = 0.0
        # search rollrate from datadict
        rollrate = datadict_filtered['rollrate']['actual']
        if rollrate >= 0:
            rollrate_right = rollrate
        elif rollrate < 0:
            rollrate_left = -rollrate
        pitchrate = datadict_filtered['pitchrate']['actual']
        if pitchrate >= 0:
            pitchrate_up = pitchrate
        elif pitchrate < 0:
            pitchrate_down = -pitchrate
        yawrate = datadict_filtered['yawrate']['actual']
        if yawrate >= 0.0:
            yawrate_left = yawrate
        elif yawrate < 0.0:
            yawrate_right = -yawrate
        flutter = datadict_filtered['airspeed']['actual']
        #  -- wheelshake and turbulence functions are not defined yet
        wheelshake = 0.0
        turbulence = 0.0
        datadict_filtered['rollrate_right']['actual'] = rollrate_right
        datadict_filtered['rollrate_left']['actual'] = rollrate_left
        datadict_filtered['pitchrate_up']['actual'] = pitchrate_up
        datadict_filtered['pitchrate_down']['actual'] = pitchrate_down
        datadict_filtered['yawrate_left']['actual'] = yawrate_left
        datadict_filtered['yawrate_right']['actual'] = yawrate_right
        datadict_filtered['Flutter']['actual'] = flutter
        datadict_filtered['Wheelshake']['actual'] = wheelshake
        datadict_filtered['Turbulence']['actual'] = turbulence

        return datadict_filtered

    def data_to_motor(self, datadict_final):
        new_time = 1.0
        # # get UDP parameter list => function call Condor_UDP_data_arrays() that returns dictionary
        no_lines = len(datadict_final)
        # motor_speed_list = []
        data_names = list(datadict_final.keys())
        for row in range(no_lines):
            flt_min_limit = datadict_final.get(data_names[row])['flt_min_limit']
            flt_max_limit = datadict_final.get(data_names[row])['flt_max_limit']
            mot_min_limit = datadict_final.get(data_names[row])['mot_min_limit']
            mot_max_limit = datadict_final.get(data_names[row])['mot_max_limit']
            actual = datadict_final.get(data_names[row])['actual']
            # ---- start conversion from actual signals to motor commands
            mot_maxmin_delta = mot_max_limit - mot_min_limit
            flt_maxmin_delta = flt_max_limit - flt_min_limit
            actual_delta = actual - flt_min_limit
            if not flt_maxmin_delta <= 0:
                mot_kk1 = mot_maxmin_delta/flt_maxmin_delta
                motor_speed = int(mot_min_limit + mot_kk1 * actual_delta)
            else:
                motor_speed = 0
            if actual < flt_min_limit:
                motor_speed = 0
            if actual > flt_max_limit:
                motor_speed = mot_max_limit
            datadict_final[data_names[row]]['M_act'] = motor_speed
        self.udp_time_old = new_time
        return datadict_final

    def create_ff_string(self, data_dict):
        no_rows = len(self.profile_table)
        m_act = []
        m_act.append('M_act')
        motors_table = []
        motor_max_table = []
        for cell in range(8):
            motor_max_table.append(0)
        for cell in range((8*no_rows+1)):
            motors_table.append(0)
        for row in range(1, no_rows):
            data_temp = 0
            # --  get actual motor command from the data_dict
            data_str = data_dict[self.profile_table[row][0]]['M_act']
            if not data_str == '-':
                data_temp = int(data_str)
            m_act.append(data_temp)
            # -- split motor speed M_act to individual motors
            motors_str = self.profile_table[row][6]
            no_motors = int(len(motors_str)/2)
            if no_motors > 0:
                for col in range(8):
                    str_temp = str(col)
                    data_index = motors_str.find(str_temp)
                    if data_index >= 0:
                        motors_table[row*8+col] = int(m_act[row])
                        # update individual motor max command list
                        if motor_max_table[col] <= motors_table[row*8+col]:
                            motor_max_table[col] = motors_table[row*8+col]
        # -- create motor command control string based on motor_max_table
        str_temp = ''
        for cell in range(8):
            str_temp = str_temp + 'M' + str(cell) + str(motor_max_table[cell]) + '\r'
        return str_temp

# ---------- CondorUDP class function definitions ends here ---------------------------------------------------
