import socket
import ast
import queue
import Condor2_profile as ffprof
import Shaker_comport as ffcom
import math
import time
import random

UDP_IP = "127.0.0.1"
UDP_SOCK_TIMEOUT = 0.2
UDP_PORT = 55278
UDP_DATA_LOOPS = 5
# main window loop timeout in ms
TIMEOUT = 250

FILTER_COEF = 1
ACT_MIN = 0.1
ACT_MAX = 0.2
MOT_MIN = 0
MOT_MAX = 0


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
        self.motor_calibration_table = []
        for row in range(8):
            self.motor_calibration_table.append(1.0)
        # ---- call motor calibration function here => add this table as a part of default.ini file
        self.filename_table = self.profile.read_init_file('default.ini')
        if len(self.filename_table) > 3:
            self.motor_calibration_table = self.profile.get_motor_calibration_table(self.filename_table)

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
            data_dict[str_temp] = {'actual': float_value, 'act_min': 0.0, 'act_max': 0.0,
                                   'filtercoeff': FILTER_COEF, 'act_min_limit': 0.0,
                                   'act_max_limit': 0.0, 'mot_min_limit': 0,
                                   'mot_max_limit': 0, 'M_act': 0, 'motors': ''}
            if count == 0:
                if str_temp == 'time':
                    data_dict[str_temp]['filtercoeff'] = 1
            count = count + 1
            # create new function rollrate_left, rollrate_right, pitch_up and pitch_down, Flutter and Turbulence2
            data_dict['rollrate_left'] = {'actual': 0.0, 'act_min': 0.0, 'act_max': 0.0,
                                          'filtercoeff': FILTER_COEF, 'act_min_limit': ACT_MIN,
                                          'act_max_limit': ACT_MAX, 'mot_min_limit': MOT_MIN,
                                          'mot_max_limit': MOT_MAX, 'M_act': 0, 'motors': ''}
            data_dict['rollrate_right'] = {'actual': 0.0, 'act_min': 0.0, 'act_max': 0.0,
                                           'filtercoeff': FILTER_COEF, 'act_min_limit': ACT_MIN,
                                           'act_max_limit': ACT_MAX, 'mot_min_limit': MOT_MIN,
                                           'mot_max_limit': MOT_MAX, 'M_act': 0, 'motors': ''}
            data_dict['pitchrate_up'] = {'actual': 0.0, 'act_min': 0.0, 'act_max': 0.0,
                                         'filtercoeff': FILTER_COEF, 'act_min_limit': ACT_MIN,
                                         'act_max_limit': ACT_MAX, 'mot_min_limit': MOT_MIN,
                                         'mot_max_limit': MOT_MAX, 'M_act': 0, 'motors': ''}
            data_dict['pitchrate_down'] = {'actual': 0.0, 'act_min': 0.0, 'act_max': 0.0,
                                           'filtercoeff': FILTER_COEF, 'act_min_limit': ACT_MIN,
                                           'act_max_limit': ACT_MAX, 'mot_min_limit': MOT_MIN,
                                           'mot_max_limit': MOT_MAX, 'M_act': 0, 'motors': ''}
            data_dict['yawrate_left'] = {'actual': 0.0, 'act_min': 0.0, 'act_max': 0.0,
                                         'filtercoeff': FILTER_COEF, 'act_min_limit': ACT_MIN,
                                         'act_max_limit': ACT_MAX, 'mot_min_limit': MOT_MIN,
                                         'mot_max_limit': MOT_MAX, 'M_act': 0, 'motors': ''}
            data_dict['yawrate_right'] = {'actual': 0.0, 'act_min': 0.0, 'act_max': 0.0,
                                          'filtercoeff': FILTER_COEF, 'act_min_limit': ACT_MIN,
                                          'act_max_limit': ACT_MAX, 'mot_min_limit': MOT_MIN,
                                          'mot_max_limit': MOT_MAX, 'M_act': 0, 'motors': ''}
            data_dict['Flutter'] = {'actual': 0.0, 'act_min': 0.0, 'act_max': 0.0,
                                    'filtercoeff': FILTER_COEF, 'act_min_limit': ACT_MIN,
                                    'act_max_limit': ACT_MAX, 'mot_min_limit': MOT_MIN,
                                    'mot_max_limit': MOT_MAX, 'M_act': 0, 'motors': ''}
            data_dict['Wheelshake'] = {'actual': 0.0, 'act_min': 0.0, 'act_max': 0.0,
                                       'filtercoeff': FILTER_COEF, 'act_min_limit': ACT_MIN,
                                       'act_max_limit': ACT_MAX, 'mot_min_limit': MOT_MIN,
                                       'mot_max_limit': MOT_MAX, 'M_act': 0, 'motors': ''}
            data_dict['Turbulence'] = {'actual': 0.0, 'act_min': 0.0, 'act_max': 0.0,
                                       'filtercoeff': FILTER_COEF, 'act_min_limit': ACT_MIN,
                                       'act_max_limit': ACT_MAX, 'mot_min_limit': MOT_MIN,
                                       'mot_max_limit': MOT_MAX, 'M_act': 0, 'motors': ''}
            data_dict['Turbulence2'] = {'actual': 0.0, 'act_min': 0.0, 'act_max': 0.0,
                                        'filtercoeff': FILTER_COEF, 'act_min_limit': ACT_MIN,
                                        'act_max_limit': ACT_MAX, 'mot_min_limit': MOT_MIN,
                                        'mot_max_limit': MOT_MAX, 'M_act': 0, 'motors': ''}
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
            data_old = float(data_dict_old.get(data_names[row])['actual'])
            data_parsered = float(data_dict_parsered.get(data_names[row])['actual'])
            filter_coeff = float(data_dict_parsered.get(data_names[row])['filtercoeff'])
            data_filtered = (1 - 1 / filter_coeff) * data_old + (1 / filter_coeff) * data_parsered
            data_dict_new[data_names[row]]['actual'] = str(data_filtered)
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

    def udp_and_motor(self, q_data, q_udp_status, q_startpause, lock, ser, portname, baudrate, q_motor_tables):
        data_dict = {}
        self.udp_binded = False
        startpause = False
        table_created = False
        start_time_table = []
        name_row = ['rand_start', 'rand_counter', 'rand_period', 'rand_ratio']
        for mot in range(8):
            name_row.append('rand_M' + str(mot))
        rand_start_table = [name_row]
        param_list_str = ''
        motors_table = []
        start_time = time.time()
        lock.acquire()
        #  Task 0: function init:  get and check q_param queue status
        if not q_startpause.empty():
            startpause = q_startpause.get()  # check start_stop status
        # # open q_data queue and get data_dict dictionary from there
        if not q_data.empty():
            data_dict = q_data.get()
            for row in range(len(data_dict)):
                if not table_created:
                    start_time_table.append(start_time)
                    rand_start_table.append([0.0, 0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            table_created = True
        lock.release()
        # --------- start actual function loop -----------------------------
        # check udp communication
        self.udp_com = self.check_udp()
        lock.acquire()
        if not ser.isopen:
            ser.Open(portname, baudrate)
            self.ff_com_open = True
        ser.Send('M00\rM10\rM20\rM30\rM40\rM50\rM60\rM70\r')
        lock.release()
        datadict_old = data_dict
        strdata_old = ''
        check = ser.isopen
        while startpause:
            # ------------ get_udp_data(UDP_check) ---------------------------
            # start looping UDP and sound creating tasks
            datadict_final = {}
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
                datadict_final = self.data_to_motor_ph1(datadict_final)
                motors_table, start_time_table, rand_start_table = \
                    self.data_to_motor_ph2(datadict_final, start_time_table, rand_start_table)
                # ------ function4:  ForceFeel motor control, create motor control command string
                # ------ as output (=motor_control_str)
                motor_control_str = self.create_ff_string(motors_table)
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
            no_rows = len(self.profile_table)
            param_list_str = ''
            for row in range(no_rows):
                param_list_str = param_list_str + self.profile_table[row][0] + ','
            param_list_str = param_list_str[:-1]
            lock.acquire()
            # clear q_data queue
            while not q_data.empty():
                x = q_data.get()
            q_data.put(datadict_final)
            while not q_motor_tables.empty():
                x = q_motor_tables.get()
            q_motor_tables.put(param_list_str)
            q_motor_tables.put(motors_table)
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
        wheelshake = 0.0
        turbulence = 0.0
        turbulence2 = 0.0
        # search rollrate from datadict
        rollrate = float(datadict_filtered['rollrate']['actual'])
        if rollrate >= 0:
            rollrate_right = rollrate
        elif rollrate < 0:
            rollrate_left = -rollrate
        pitchrate = float(datadict_filtered['pitchrate']['actual'])
        if pitchrate >= 0:
            pitchrate_up = pitchrate
        elif pitchrate < 0:
            pitchrate_down = -pitchrate
        yawrate = float(datadict_filtered['yawrate']['actual'])
        if yawrate >= 0.0:
            yawrate_left = yawrate
        elif yawrate < 0.0:
            yawrate_right = -yawrate
        flutter = float(datadict_filtered['airspeed']['actual'])
        wheelheight = float(datadict_filtered['wheelheight']['actual'])
        vx = float(datadict_filtered['vx']['actual'])
        vy = float(datadict_filtered['vy']['actual'])
        surf_rough = float(datadict_filtered['surfaceroughness']['actual'])
        vxy = math.sqrt(vx * vx + vy * vy)
        if wheelheight < 0.0:
            wheelshake = vxy * surf_rough
        az = math.fabs(float(datadict_filtered['az']['actual']))
        turbulence = 0.0
        if wheelheight > 0.2:
            turbulence = float(datadict_filtered['turbulencestrength']['actual'])
        turbulence2 = turbulence * az
        datadict_filtered['rollrate_right']['actual'] = str(rollrate_right)
        datadict_filtered['rollrate_left']['actual'] = str(rollrate_left)
        datadict_filtered['pitchrate_up']['actual'] = str(pitchrate_up)
        datadict_filtered['pitchrate_down']['actual'] = str(pitchrate_down)
        datadict_filtered['yawrate_left']['actual'] = str(yawrate_left)
        datadict_filtered['yawrate_right']['actual'] = str(yawrate_right)
        datadict_filtered['Flutter']['actual'] = str(flutter)
        datadict_filtered['Wheelshake']['actual'] = str(wheelshake)
        datadict_filtered['Turbulence']['actual'] = str(turbulence)
        datadict_filtered['Turbulence2']['actual'] = str(turbulence2)

        return datadict_filtered

    def data_to_motor_ph1(self, datadict):
        new_time = 1.0
        # # get UDP parameter list => function call Condor_UDP_data_arrays() that returns dictionary
        no_lines = len(datadict)
        data_names = list(datadict.keys())
        for row in range(no_lines):
            act_min_limit = float(datadict.get(data_names[row])['act_min_limit'])
            act_max_limit = float(datadict.get(data_names[row])['act_max_limit'])
            mot_min_limit = float(datadict.get(data_names[row])['mot_min_limit'])
            mot_max_limit = float(datadict.get(data_names[row])['mot_max_limit'])
            actual = float(datadict.get(data_names[row])['actual'])
            # ---- start conversion from actual signals to motor commands
            mot_maxmin_delta = mot_max_limit - mot_min_limit
            act_maxmin_delta = act_max_limit - act_min_limit
            actual_delta = actual - act_min_limit
            if not act_maxmin_delta <= 0:
                mot_kk1 = mot_maxmin_delta / act_maxmin_delta
                motor_speed = int(mot_min_limit + mot_kk1 * actual_delta)
            else:
                motor_speed = 0
            if actual < act_min_limit:
                motor_speed = 0
            if actual > act_max_limit:
                motor_speed = mot_max_limit
            datadict[data_names[row]]['M_act'] = str(motor_speed)
        self.udp_time_old = new_time
        return datadict

    def data_to_motor_ph2(self, datadict, start_time_table, rand_start_table, test_parameter=None):
        no_rows = len(self.profile_table)
        m_act = ['M_act']
        motors_table = []
        for row in range(no_rows + 1):
            motors_table.append([0, 0, 0, 0, 0, 0, 0, 0])
        motor_max_table = [0, 0, 0, 0, 0, 0, 0, 0]
        if test_parameter is None:
            motors_table, start_time_table, rand_start_table = self.create_modulator(datadict, motors_table,
                                                                                     start_time_table,
                                                                                     rand_start_table)
        if not test_parameter is None:
            motors_table, start_time_table, rand_start_table = self.create_modulator(datadict, motors_table,
                                                                                     start_time_table,
                                                                                     rand_start_table, test_parameter)

        #  --- add motor control gains to motor_table
        for row in range(1, no_rows):
            motor_gain = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
            # --  get actual motor command from the data_dict
            sub_dict = datadict[self.profile_table[row][0]]

            status = sub_dict.get('gain_M0', '0.0')
            if not status == '0.0':
                for mot in range(8):
                    motor_gain[mot] = float(datadict[self.profile_table[row][0]][('gain_M' + str(mot))])
            for mot in range(8):
                motors_table[row][mot] = int(motors_table[row][mot] * self.motor_calibration_table[mot] *
                                             motor_gain[mot])
                if motors_table[row][mot] > 100:
                    motors_table[row][mot] = 100

        return motors_table, start_time_table, rand_start_table

    def create_modulator(self, datadict, motors_table, start_time_table, rand_start_table, test_parameter=None):
        no_rows = len(self.profile_table)
        if not test_parameter is None:
            no_rows = 2
        # trigger = False
        actual_time = 0.0
        period, ratio, ampl = 0.0, 0.0, 0.0
        offset1, offset2, rand_ampl = 0.0, 0.0, 0.0
        motor_mod_gain = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        m_act, mot_min_limit, mot_max_limit = 0.0, 0.0, 0.0
        real_time = time.time()
        # test!!

        for row in range(1, no_rows):
            sub_dict = datadict[self.profile_table[row][0]]
            if not test_parameter is None:
                sub_dict = datadict[test_parameter]
            # name = self.profile_table[row][0]
            rand_range = 0
            rand_gain = 0.0
            m_act_diff = 0.0
            m_act = float(sub_dict['M_act'])
            mot_min_limit, mot_max_limit = float(sub_dict['mot_min_limit']), float(sub_dict['mot_max_limit'])
            mot_maxmin = mot_max_limit - mot_min_limit
            if m_act > mot_max_limit:
                m_act = mot_max_limit
            m_act_diff = m_act - mot_min_limit
            temp_mod_gain = 1.0
            status = sub_dict.get('mod_enabled', 9)
            if not status == 9:
                if int(sub_dict['mod_enabled']) == 1:
                    period, ratio = float(sub_dict['period']), float(sub_dict['ratio'])
                    ampl, offset1 = float(sub_dict['ampl']), float(sub_dict['offset1'])
                    offset2, rand_ampl = float(sub_dict['offset2']), float(sub_dict['rand_ampl'])
                    t_rand_start = float(rand_start_table[row + 1][rand_start_table[0].index('rand_start')])
                    rand_counter = int(rand_start_table[row + 1][rand_start_table[0].index('rand_counter')])
                    rand_period = float(rand_start_table[row + 1][rand_start_table[0].index('rand_period')])
                    rand_ratio = float(rand_start_table[row + 1][rand_start_table[0].index('rand_ratio')])
                    r_period = period * rand_period
                    r_ratio = ratio * rand_ratio
                    # start creation
                    if m_act_diff > 0.0:
                        actual_time = float(real_time - start_time_table[row])
                        if actual_time > r_period:
                            start_time_table[row] = float(real_time)
                            actual_time = float(real_time) - start_time_table[row]
                            if rand_counter < 0:
                                # generate random start time moment => Check table
                                trigger = True
                                if 'rand_start_enabled' in sub_dict:
                                    if sub_dict['rand_start_enabled'] == 1:
                                        rand_counter = random.randint(1, 2)
                                        rand_period = float((random.randint(88, 120) / 100))
                                        r_period = period * rand_period
                                        rand_start_table[row + 1][rand_start_table[0].index('rand_period')] = \
                                            rand_period
                                        rand_ratio = float(random.randint(70, 100) / 100)
                                        r_ratio = ratio * rand_ratio
                                        rand_start_table[row + 1][rand_start_table[0].index('rand_ratio')] = \
                                            rand_ratio
                                        t_rand_start = (1 - r_ratio) * r_period
                                        rand_start_table[row + 1][rand_start_table[0].index('rand_start')] = \
                                            t_rand_start
                                if rand_ampl > 0.0:
                                    rand_range = int(rand_ampl * mot_maxmin)
                                    rand_gain = random.randint(0, rand_range) / mot_maxmin
                                else:
                                    rand_gain = 0.0
                                    rand_ampl = 0.0
                                rand_m0_index = rand_start_table[0].index('rand_M0')
                                for mot in range(8):
                                    if int(sub_dict['rand_separately']) == 1:
                                        rand_gain = random.randint(0, rand_range) / mot_maxmin
                                    rand_start_table[row + 1][rand_m0_index + mot] = rand_gain

                            rand_counter = rand_counter - 1
                            rand_start_table[row + 1][rand_start_table[0].index('rand_counter')] = rand_counter

                        t_ratio = r_ratio * r_period
                        if actual_time <= t_rand_start:
                            temp_mod_gain = offset2
                        if t_rand_start < actual_time < (t_ratio + t_rand_start):
                            # ---- math function offset1 + ampl*sin(pi/t_ratio*actual_time) -----
                            temp_mod_gain = offset1 + ampl * math.sin((math.pi / t_ratio) * actual_time)
                        if (t_ratio + t_rand_start) <= actual_time < r_period:
                            temp_mod_gain = offset2
                        rand_m0_index = rand_start_table[0].index('rand_M0')
                        for mot in range(8):
                            motor_mod_gain[mot] = temp_mod_gain * (1 - rand_start_table[row + 1][rand_m0_index + mot])
            if m_act_diff <= 0.0:
                m_act_diff = 0.0

            # -- split motor speed M_act to individual motors
            motors_str = sub_dict['motors']
            no_motors = int(len(motors_str) / 2)
            if no_motors > 0:
                for mot in range(8):
                    str_temp = str(mot)
                    data_index = motors_str.find(str_temp)
                    if data_index >= 0:
                        if m_act_diff > 0.0:
                            motors_table[row][mot] = int(mot_min_limit + m_act_diff * motor_mod_gain[mot])
                            if motors_table[row][mot] >= 100:
                                motors_table[row][mot] = int(100)
                        elif m_act_diff <= 0.0:
                            motors_table[row][mot] = 0

        return motors_table, start_time_table, rand_start_table

    def create_ff_string(self, motors_table):

        # # update individual motor max command list
        no_rows = len(self.profile_table)
        motor_max_table = [0, 0, 0, 0, 0, 0, 0, 0]
        for col in range(8):
            mot_max = 0
            for row in range(1, no_rows):
                if motors_table[row][col] >= mot_max:
                    mot_max = motors_table[row][col]
                    if mot_max > 100:
                        mot_max = 100
                motor_max_table[col] = mot_max
        str_motor = ''
        for col in range(8):
            str_motor = str_motor + 'M' + str(col) + str(motor_max_table[col]) + '\r'
        return str_motor

# ---------- CondorUDP class function definitions ends here ---------------------------------------------------
