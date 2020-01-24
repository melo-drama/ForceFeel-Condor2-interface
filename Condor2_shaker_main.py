import tkinter as tk
import Shaker_test as ff_test
import tkinter.font as tkFont
import Shaker_comport as ffcom
import Condor2_udp_com as ffudp
import Condor2_profile as ffprof
import queue
import threading
# import ast
# import array
import os

UPDATE_RATE_IN_MS = 500


class Window(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master
        self.master.title("default")
        self.udp_data_dict = {}
        self.minmax_reset = False
        self.ff_test_activated = False
        self.condor2_game_pause = False
        self.update_main_window = False
        self.update_main_win_q = queue.Queue()
        self.update_main_win_q.put(self.update_main_window)
        self.motors_reseted = False

        # --- Create instance to ForceFeel COM port class named Serialport ----------
        self.ser = ffcom.SerialPort()
        port_name, baudrate, comport = ffcom.load_ff_port_data()
        self.ser.comport = comport
        self.ser.baud = baudrate

        # --- Create instance to Condor UDP class named CondorUDP -------------
        self.udp = ffudp.CondorUDP(self.ser)

        # ---- create instance to Profiler window -------------
        self.mon = ffprof.Profiler()

        # --- get and read default.init file ----------
        if not os.path.isfile('default.ini'):
            pass
            # --- define/create default.ini file if that is missing from the list (27.12.2019/not done)
        self.filename_table = self.read_init_file('default.ini')

        # -------- get monitor data window parameter name list --------------
        self.mon_parameter_list = self.mon.load_window_new(self.filename_table[0][1])

        # --------- load default (latest) ForceFeel motor control profile
        self.ff_profile = self.mon.load_profile_file(self.filename_table[1][1])
        self.act_min_list = []
        self.act_max_list = []
        self.monwin_table = []

        self.all_parameters_list = self.load_all_parameters()
        act_old = []
        act_new = []
        no_all_rows = len(self.all_parameters_list)
        for row in range(no_all_rows):
            act_new.append(0.000)
            act_old.append(0.001)

        self.actual_old_new = []
        self.actual_old_new.append(act_old)
        self.actual_old_new.append(act_new)

        # --- create monitoring table => fetch profile information -------------
        self.monwin_table = self.create_monwin_table()
        # initiate min and max monitoring values
        no_rows = len(self.monwin_table)
        for row in range(no_rows):
            self.act_min_list.append(0.0)
            self.act_max_list.append(0.0)

        # ------- Create thread status parameter -----------------
        self.thread_is_running = False

        # --------- Create queues to share information between Window class and thread function ------
        #  create lock
        self.lock = threading.Lock()
        # ---- self.q_data = telemetry data queue
        self.q_data = queue.Queue()

        # ---- Condor UDP status queue
        self.q_udp_status = queue.Queue()
        # ---- start vs pause status queue
        self.q_startpause = queue.Queue()

        # --- motor_table queue
        self.q_motor_tables = queue.Queue()
        self.motor_max_table = []
        for mot in range(8):
            self.motor_max_table.append(0)

        # ----------- Menu definitions ----------------------------------------------------
        # creating a menu instance
        self.menu = tk.Menu(self.master)
        self.master.config(menu=self.menu)

        # create the file object)
        file = tk.Menu(self.menu, tearoff=False)

        # adds a command to the menu option, calling it exit, and the
        # command it runs on event is client_exit
        file.add_command(label="Exit", command=self.client_exit)

        # added "file" to our menu
        self.menu.add_cascade(label="File", menu=file)
        # create the file object)
        self.edit = tk.Menu(self.menu, tearoff=False)

        # adds a command to the menu option, calling it exit, and the
        # command it runs on event is client_exit
        self.edit.add_command(label="Test ForceFeel controls", command=self.test_forcefeel_communication)
        self.edit.add_command(label="Select and edit profile data and monitor window",
                         command=self.select_monitor_parameters)
        # added "Edit" to our menu
        self.menu.add_cascade(label="Edit", menu=self.edit)

        self.hide_expand = tk.Menu(self.menu, tearoff=False)
        self.hide_expand.add_command(label="Expand/hide basic parameters", command=self.hide_open_basic_frame)
        self.hide_expand.add_command(label="Expand/hide modulator parameters", command=self.hide_open_modulator_frame)
        self.hide_expand.add_command(label="Expand/hide motor power table", command=self.hide_open_motortable_frame)

        self.menu.add_cascade(label="View", menu=self.hide_expand)
        self.basic_param_hided = False
        self.modulator_param_hided = False
        self.motortable_hided = True

        # ----------------- Menu definitions ended -----------------------------------
        # bg =  background colour (ascii code)
        bg = '#ccddff'
        #  bold first row text and set size
        self.headerFont = tkFont.Font(size=10, weight='bold')
        # define Start/Pause button and text variable
        btn_font = tkFont.Font(size=14, weight='bold')
        btn_font2 = tkFont.Font(size=10, weight='bold')
        #  --------------- Button Frame ---------------------------------------
        button_frame = tk.Frame()
        button_frame.grid(row=0, column=0, sticky='W', padx=2, pady=1)
        self.btn_startpause_var = tk.StringVar()
        self.btn_start_pause = tk.Button(button_frame, textvariable=self.btn_startpause_var,
                                         command=self.start_monitoring)
        self.btn_start_pause.grid(row=0, column=0, rowspan=2, sticky='W', padx=4, pady=2)
        self.btn_start_pause.configure(font=btn_font)
        self.btn_startpause_var.set('Start')
        self.startpause = False

        # -------------- Button frame ended ----------------------------------------

        # Create main header => shows the active motor shaking profile
        str_temp = 'Profile file: ' + self.filename_table[1][1]
        width_str = len(str_temp)
        self.lb_header_var = tk.StringVar()
        self.lb_header = tk.Label(button_frame, textvariable=self.lb_header_var, width=width_str)
        self.lb_header.grid(row=0, column=2, sticky='N')
        lb_header_font = tkFont.Font(size=12, weight='bold')
        self.lb_header.configure(font=lb_header_font, anchor='e',  justify='center')
        self.lb_header_var.set(str_temp)

        str_temp1 = 'Monitor file: ' + self.filename_table[0][1]
        width_str1 = len(str_temp1)
        self.lb_header_var1 = tk.StringVar()
        self.lb_header1 = tk.Label(button_frame, textvariable=self.lb_header_var1, width=width_str1)
        self.lb_header1.grid(row=1, column=2, sticky='N')
        lb_header_font = tkFont.Font(size=12, weight='bold')
        self.lb_header1.configure(font=lb_header_font, anchor='e', justify='center')
        self.lb_header_var1.set(str_temp)

        # ---------- add 10 row and 10 columns

        self.no_rows = len(self.mon_parameter_list)
        self.no_columns = 10

        # -----------Data Frame----------------------------------------------------

        # -------------Data Frame ended-----------------------------------------------------------
        # ------------ mon frame start -------------------
        self.mon_frame = tk.Frame()
        self.mon_frame.grid(column=0, row=3, columnspan=4, sticky='W', padx=10, pady=10)
        self.inputs_frame = tk.Frame(self.mon_frame)
        self.inputs_frame.grid(column=0, row=0, padx=2, pady=2)
        self.basic_param_frame = tk.Frame(self.mon_frame)
        self.basic_param_frame.grid(column=1, row=0, padx=2, pady=2)
        self.m_act_frame = tk.Frame(self.mon_frame)
        self.m_act_frame.grid(column=2, row=0, padx=2, pady=2)
        self.modulator_frame = tk.Frame(self.mon_frame)
        self.modulator_frame.grid(column=3, row=0, padx=2, pady=2)
        self.motors_frame = tk.Frame(self.mon_frame)
        self.motors_frame.grid(column=4, row=0, padx=2,  pady=2)
        self.monwin_str_table = []
        self.mon_lbl_param = []
        self.mon_lbl_stringvar = []
        self.mon_txt_param = []
        #  -- convert monwin_table to string table
        self.monwin_str_table = self.monwin_table_to_string_table(self.monwin_table)
        #  --- add labels and text windows -------------
        no_col = len(self.monwin_str_table)+8
        no_row = len(self.monwin_table[0])
        width_table = [20, 10, 7, 7, 8, 12, 12, 12, 12, 17, 7, 7, 7, 7, 7, 7, 7, 7, 12, 7, 5, 5, 7, 7, 10, 14, 16, 6]
        no_width = len(width_table)
        standard_width = 10
        motor_table_width = 3
        if no_width < no_col:
            for col in range(no_width, no_col-1):
                width_table.append(standard_width)
            for col in range(no_col-1, no_col+7):
                width_table.append(motor_table_width)
        # --- inputs_frame lbl and text lines
        for col in range(4):
            self.mon_lbl_stringvar.append(tk.StringVar())
            self.mon_lbl_param.append(tk.Label(self.inputs_frame, textvariable=self.mon_lbl_stringvar[col],
                                               width=width_table[col]))
            self.mon_lbl_param[col].grid(column=col, row=0, sticky='E', padx=2, pady=2)
            self.mon_txt_param.append(tk.Text(self.inputs_frame, height=self.no_rows-1, width=width_table[col], bg=bg))
            self.mon_txt_param[col].grid(column=col, row=1, sticky='W', padx=2, pady=2)
        # add separate Motor_max label
        lb_motor_max_font = tkFont.Font(size=10, weight='bold')
        self.mon_lbl_motor_max = tk.Label(self.inputs_frame, text='motor_max', width=width_table[0], bg=bg,
                                          borderwidth=1, relief='sunken')
        self.mon_lbl_motor_max.grid(column=0, row=2, sticky='W', padx=2, pady=2)
        self.mon_lbl_motor_max.configure(font=lb_motor_max_font, anchor='w', justify='center')

        # --- basic_param_frame lbl and text lines
        for col in range(4, 10):
            self.mon_lbl_stringvar.append(tk.StringVar())
            self.mon_lbl_param.append(tk.Label(self.basic_param_frame, textvariable=self.mon_lbl_stringvar[col],
                                               width=width_table[col]))
            self.mon_lbl_param[col].grid(column=col, row=0, sticky='NW', padx=2, pady=2)
            self.mon_lbl_param[col].configure(anchor='n')
            self.mon_txt_param.append(tk.Text(self.basic_param_frame, height=self.no_rows-1, width=width_table[col], bg=bg))
            self.mon_txt_param[col].grid(column=col, row=1, sticky='NW', padx=2, pady=2)

        self.mon_lbl_blancco = tk.Label(self.basic_param_frame, text='', width=width_table[4])
        self.mon_lbl_blancco.grid(column=4, row=2, sticky='W', padx=1, pady=1)
        # ---- modulator_frame lbl and text lines
        # for col in range(10, no_col-1):
        for col in range(10, 27):
            self.mon_lbl_stringvar.append(tk.StringVar())
            self.mon_lbl_param.append(tk.Label(self.modulator_frame, textvariable=self.mon_lbl_stringvar[col],
                                               width=width_table[col]))
            self.mon_lbl_param[col].grid(column=col, row=0, sticky='W', padx=2, pady=2)
            self.mon_txt_param.append(
                tk.Text(self.modulator_frame, height=self.no_rows - 1, width=width_table[col], bg=bg))
            self.mon_txt_param[col].grid(column=col, row=1, sticky='W', padx=2, pady=2)
        self.mon_lbl_blancco3 = tk.Label(self.modulator_frame, text='', width=1)
        self.mon_lbl_blancco3.grid(column=12, row=2, sticky='W', padx=1, pady=1)
        # --- M_act -----
        col = 27
        self.mon_lbl_stringvar.append(tk.StringVar())
        self.mon_lbl_param.append(tk.Label(self.m_act_frame, textvariable=self.mon_lbl_stringvar[col],
                                           width=width_table[col]))
        self.mon_lbl_param[col].grid(column=0, row=0, sticky='W', padx=2, pady=2)
        self.mon_txt_param.append(
            tk.Text(self.m_act_frame, height=self.no_rows, width=width_table[col], bg=bg))
        self.mon_txt_param[col].grid(column=0, row=1, sticky='W', padx=2, pady=2)
        self.mon_lbl_blancco2 = tk.Label(self.m_act_frame, text='', width=1)
        self.mon_lbl_blancco2.grid(column=10, row=2, sticky='W', padx=1, pady=1)
        for col in range(28, no_col-1):
            self.mon_lbl_stringvar.append(tk.StringVar())
            self.mon_lbl_param.append(tk.Label(self.modulator_frame, textvariable=self.mon_lbl_stringvar[col],
                                               width=width_table[col], justify='center'))
            self.mon_txt_param.append(tk.Text(self.modulator_frame, height=self.no_rows - 1,
                                              width=width_table[col], bg=bg))

        #  -- motors labels and text files
        self.mon_lbl_motmax_var = []
        self.mon_lbl_motmax = []
        for col in range(no_col-1, (no_col+7)):
            self.mon_lbl_stringvar.append(tk.StringVar())
            self.mon_lbl_param.append(tk.Label(self.motors_frame, textvariable=self.mon_lbl_stringvar[col],
                                               width=width_table[col]))
            self.mon_lbl_param[col].grid(column=col, row=0, sticky='W', padx=2, pady=2)
            self.mon_txt_param.append(
                tk.Text(self.motors_frame, height=self.no_rows - 1, width=width_table[col], bg=bg))
            self.mon_txt_param[col].grid(column=col, row=1, sticky='W', padx=2, pady=2)
        for mot in range(8):
            self.mon_lbl_motmax_var.append(tk.StringVar())
            self.mon_lbl_motmax.append(tk.Label(self.motors_frame, textvariable=self.mon_lbl_motmax_var[mot],
                                                width=3, bg=bg, borderwidth=1, relief='sunken'))
            self.mon_lbl_motmax[mot].grid(column=mot+43, row=3, sticky='W', padx=2, pady=2)
            self.mon_lbl_motmax[mot].configure(font=lb_motor_max_font, anchor='n', justify='center')
            self.mon_lbl_motmax_var[mot].set('0')


        for xx in range(no_col+7):
            self.mon_lbl_param[xx].configure(font=self.headerFont, anchor='w', justify='left')

        self.monwin_init()

        # ------------ mon frame ended --------------------
        # get UDP parameter list => function call Condor_UDP_data_arrays() that returns dictionary
        self.udp_data_dict = self.udp.condor_udp_data_arrays()
        # ------- update monitor data window => update ForceFeel motor control values to monitor parameter list
        # --- self.udp_data_dict
        self.update_monitor_frame(self.udp_data_dict, self.no_rows, self.no_columns)

        self.basic_param_frame.grid_remove()
        self.modulator_frame.grid_remove()
        # self.motors_frame.grid_remove()
    # ------------ class Window(tk.Frame) init ended --------------------

    def hide_open_basic_frame(self):
        self.basic_param_hided = not self.basic_param_hided
        if self.basic_param_hided:
            self.basic_param_frame.grid()
        if not self.basic_param_hided:
            self.basic_param_frame.grid_remove()

    def hide_open_modulator_frame(self):
        self.modulator_param_hided = not self.modulator_param_hided
        if self.modulator_param_hided:
            self.modulator_frame.grid()
        if not self.modulator_param_hided:
            self.modulator_frame.grid_remove()

    def hide_open_motortable_frame(self):
        self.motortable_hided = not self.motortable_hided
        if self.motortable_hided:
            self.motors_frame.grid()
            self.mon_lbl_motor_max.grid()
            self.mon_lbl_blancco.grid()
            self.mon_lbl_blancco2.grid()
            self.mon_lbl_blancco3.grid()
            for mot in range(8):
                self.mon_lbl_motmax[mot].grid()
        if not self.motortable_hided:
            self.motors_frame.grid_remove()
            self.mon_lbl_motor_max.grid_remove()
            self.mon_lbl_blancco.grid_remove()
            self.mon_lbl_blancco2.grid_remove()
            self.mon_lbl_blancco3.grid_remove()
            for mot in range(8):
                self.mon_lbl_motmax[mot].grid_remove()

    def read_init_file(self, filename):
        name_table = []
        filename_table = []
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

    def load_all_parameters(self):
        datadict = self.udp.condor_udp_data_arrays()
        parameter_list = list(datadict.keys())
        return parameter_list

    def monwin_init(self):
        no_columns = len(self.monwin_str_table)-8
        for col in range(no_columns):
            str_para, str_data = self.monwin_str_table[col].split(',')
            self.mon_lbl_stringvar[col].set(str_para)
            if not col == 0:
                self.mon_lbl_param[col].config(anchor='n')
            self.mon_txt_param[col].insert(tk.INSERT, str_data)
        # add motor fields
        for col in range(no_columns, (no_columns+8)):
            str_para, str_data = self.monwin_str_table[col].split(',')
            self.mon_lbl_stringvar[col+15].set(str_para)
            # self.mon_txt_param[col + 15].tag_configure('center', tk.CENTER)
            self.mon_lbl_param[col].config(anchor='n')
            self.mon_txt_param[col+15].insert(tk.INSERT, str_data)

    def update_new_monwin(self):
        str_temp = 'Profile file: ' + self.filename_table[1][1] + '\t\tMonitor file: ' \
                   + self.filename_table[0][1]
        self.lb_header_var.set(str_temp)
        no_columns = len(self.monwin_str_table)
        self.no_rows = len(self.mon_parameter_list)
        # for col in range(no_columns):
        for col in range(28):
            self.mon_txt_param[col].config(state=tk.NORMAL)
            self.mon_txt_param[col].delete('1.0', tk.END)
            str_para, str_data = self.monwin_str_table[col].split(',')
            if not col == 0:
                self.mon_txt_param[col].tag_config('cent', justify=tk.CENTER)
            if col == 0:
                self.mon_txt_param[col].tag_config('cent', justify=tk.LEFT)
            self.mon_txt_param[col].insert(tk.INSERT, str_data, 'cent')
            self.mon_txt_param[col].config(height=self.no_rows)
            self.mon_txt_param[col].grid()
            self.mon_txt_param[col].config(state=tk.DISABLED)
        for col in range(28, no_columns):
            self.mon_txt_param[col+15].config(state=tk.NORMAL)
            self.mon_txt_param[col+15].delete('1.0', tk.END)
            str_para, str_data = self.monwin_str_table[col].split(',')
            self.mon_txt_param[col + 15].tag_config('cent', justify=tk.CENTER)
            self.mon_txt_param[col+15].insert(tk.INSERT, str_data, 'cent')
            self.mon_txt_param[col+15].config(height=self.no_rows)
            self.mon_txt_param[col+15].grid()
            self.mon_txt_param[col+15].config(state=tk.DISABLED)
        for mot in range(8):
            self.mon_lbl_motmax_var[mot].set(str(self.motor_max_table[mot]))

    def monwin_table_to_string_table (self, monwin_table):
        temp_table = []
        no_rows = len(monwin_table)
        no_col = len(monwin_table[0])
        for col in range(no_col):
            # add parameter and use , as a separator
            str_row = monwin_table[0][col] + ','
            for row in range(1, no_rows):
                str_row = str_row + monwin_table[row][col] +'\n'
            temp_table.append(str_row)
        return temp_table

    def reset_maxmin(self):
        no_rows = len(self.mon_parameter_list)
        for row in range(no_rows):
            self.act_min_list[row] = 0.0
            self.act_max_list[row] = 0.0

    def load_profile_table(self, load_filename):
        # --- call load_profile_file function from Prof_Window class
        profile_table = self.mon.load_profile_file(load_filename)
        return profile_table

    def profile_to_datadict(self, profile_table):
        parameter_column_names = profile_table[0]
        no_rows = len(profile_table)
        for row in range(1, no_rows):
            filtercoeff = str(profile_table[row][1])
            act_min_limit = str(profile_table[row][2])
            act_max_limit = str(profile_table[row][3])
            mot_min_limit = str(profile_table[row][4])
            mot_max_limit = str(profile_table[row][5])
            motor_str = profile_table[row][6]
            mot_gains = []
            for mot in range(8):
                mot_gains.append(str(profile_table[row][7+mot]))
            start_col = 7 + 8
            mod_enabled = str(profile_table[row][start_col])
            period = str(profile_table[row][start_col+1])
            ratio = str(profile_table[row][start_col + 2])
            ampl = str(profile_table[row][start_col + 3])
            offset1 = str(profile_table[row][start_col + 4])
            offset2 = str(profile_table[row][start_col + 5])
            rand_ampl = str(profile_table[row][start_col + 6])
            rand_separately = str(profile_table[row][start_col + 7])
            rand_start_enabled = str(profile_table[row][start_col + 8])
            self.udp_data_dict[profile_table[row][0]]['filtercoeff'] = filtercoeff
            self.udp_data_dict[profile_table[row][0]]['act_min_limit'] = act_min_limit
            self.udp_data_dict[profile_table[row][0]]['act_max_limit'] = act_max_limit
            self.udp_data_dict[profile_table[row][0]]['mot_min_limit'] = mot_min_limit
            self.udp_data_dict[profile_table[row][0]]['mot_max_limit'] = mot_max_limit
            self.udp_data_dict[profile_table[row][0]]['motors'] = motor_str
            for mot in range(8):
                str_mot = 'gain_M' + str(mot)
                self.udp_data_dict[profile_table[row][0]][str_mot] = str(mot_gains[mot])
            self.udp_data_dict[profile_table[row][0]]['mod_enabled'] = mod_enabled
            self.udp_data_dict[profile_table[row][0]]['period'] = period
            self.udp_data_dict[profile_table[row][0]]['ratio'] = ratio
            self.udp_data_dict[profile_table[row][0]]['ampl'] = ampl
            self.udp_data_dict[profile_table[row][0]]['offset1'] = offset1
            self.udp_data_dict[profile_table[row][0]]['offset2'] = offset2
            self.udp_data_dict[profile_table[row][0]]['rand_ampl'] = rand_ampl
            self.udp_data_dict[profile_table[row][0]]['rand_separately'] = rand_separately
            self.udp_data_dict[profile_table[row][0]]['rand_start_enabled'] = rand_start_enabled

    def window_name(self, window_name):
        self.master.title(window_name)

    def client_exit(self):
        exit()

    def test_forcefeel_communication(self):
        # Create child window by using the Toplevel function
        self.ff_test_activated = True
        subroot = tk.Toplevel(self)
        subroot.geometry("900x200")
        subapp = ff_test.FF_window(subroot, self.ser)
        subapp.window_name('ForceFeel communication tests window')
        subapp.var_1.set("--")
        subapp.focus_force()
        subroot.mainloop()

    def select_monitor_parameters(self):
        subroot2 = tk.Toplevel(self)
        subapp2 = ffprof.Prof_window(subroot2, self.update_main_win_q, self.lock, self.ser)
        subapp2.window_name('Condor telemetry and function selection window')
        subapp2.focus_force()
        subroot2.mainloop()

    def start_monitoring(self):
        self.ff_test_activated = False
        #  check that if thread is alive or not, update self.thread_is_running accordingly
        try:
            if self.f1.is_alive():
                self.thread_is_running = True
        except AttributeError:
            self.thread_is_running = False
        self.startpause = not self.startpause
        if self.startpause:
            self.motors_reseted = False
            self.menu.entryconfig('Edit', state=tk.DISABLED)
            self.btn_startpause_var.set('Pause')
            self.minmax_reset = True
            self.reset_maxmin()
            # start updater
            self.window_updater()
            #  create new thread if that is missing,
            if not self.thread_is_running:
                port_name, baudrate, comport = ffcom.load_ff_port_data()
                self.ser.comport = comport
                self.ser.baud = baudrate
                self.ser.Close()
                self.start_udp_thread()
        else:
            self.btn_startpause_var.set('Start')
            self.menu.entryconfig('Edit', state=tk.NORMAL)
        self.lock.acquire()
        if not self.q_startpause.empty():
            start_stop = self.q_startpause.get()
        self.q_startpause.put(self.startpause)
        self.lock.release()

    def update_monitor_frame(self, data1, no_rows=None, no_columns=None):
        # separate parameters from the dictionary and create parameter name list
        names_temp2 = []
        no_rows2 = len(self.monwin_table)
        no_cols = len(self.monwin_table[0])
        for row in range(1, no_rows2):
            names_temp2.append(self.monwin_table[row][0])
    #    update new monitor window here
        no_names2 = len(names_temp2)
        act_actual = 0.0
        act_min_old = 0.0
        act_max_old = 0.0
        for row in range(0, no_names2):
            if not self.minmax_reset:
                act_min_old = self.act_min_list[row]
                act_max_old = self.act_max_list[row]
                act_actual = float(data1[names_temp2[row]]['actual'])
                act_actual = round(act_actual, 3)
                self.actual_old_new[1][row] = act_actual
                self.monwin_table[row+1][1] = str(act_actual)
                if act_actual >= act_max_old:
                    self.act_max_list[row] = act_actual
                elif act_actual < act_min_old:
                    self.act_min_list[row] = act_actual
            self.monwin_table[row+1][2] = str(self.act_min_list[row])
            self.monwin_table[row+1][3] = str(self.act_max_list[row])
            if not data1[names_temp2[row]]['M_act'] == '-':
                str_mot = '-'
                mot_act = int(float(data1[names_temp2[row]]['M_act']))
                if mot_act > 0:
                    str_mot = str(mot_act)
                # self.monwin_table[row+1][no_cols-1] = str(mot_act)
                self.monwin_table[row + 1][27] = str_mot
        self.minmax_reset = False
        # ----- refresh screens
        self.monwin_str_table = self.monwin_table_to_string_table(self.monwin_table)
        self.update_new_monwin()
        # self.mon_txt_param[1].grid()
        # check if Condor is paused or not => most of the telemetry datas are not changing
        self.condor2_game_pause = self.check_if_Condor2_pause(data1)
        if self.condor2_game_pause:
            if self.startpause:
                if not self.ff_test_activated and not self.motors_reseted:
                    self.lock.acquire()
                    self.ser.Send('M00\rM10\rM20\rM30\rM40\rM50\rM60\rM70\r')
                    self.lock.release()

    def check_if_Condor2_pause(self, data1):
        is_pause = False
        no_rows = len(self.actual_old_new[0])
        counter = 0
        for row in range(no_rows):
            act_actual = float(data1[self.all_parameters_list[row]]['actual'])
            act_actual = round(act_actual, 3)
            self.actual_old_new[1][row] = act_actual
            if self.actual_old_new[0][row] == self.actual_old_new[1][row]:
                counter = counter + 1
            self.actual_old_new[0][row] = self.actual_old_new[1][row]
        if counter > 15:
            is_pause = True
        return is_pause

    def start_udp_thread(self):
        #  update profile to datadict
        self.profile_to_datadict(self.ff_profile)
        try:
            if self.f1.is_alive():
                self.thread_is_running = True
            elif not self.f1.is_alive():
                self.thread_is_running = False
        except AttributeError:
            self.thread_is_running = False
        if not self.thread_is_running:
            self.lock.acquire()
            # update startpause status and put it to queue
            while not self.q_startpause.empty():
                x = self.q_startpause.get()
            self.q_startpause.put(self.startpause)
            # update udp status to queue
            while not self.q_udp_status.empty():
                x = self.q_udp_status.get()
            self.q_udp_status.put(False)
            # clear q_data queue and add udp_data dictionary
            while not self.q_data.empty():
                x = self.q_data.get()
            self.q_data.put(self.udp_data_dict)
            self.lock.release()

            #  ---- start the thread function udp_and_motor() --------------------------------------
            if not self.thread_is_running:
                self.f1 = threading.Thread(target=self.udp.udp_and_motor,
                                      args=(self.q_data, self.q_udp_status, self.q_startpause, self.lock,
                                            self.ser, self.ser.comport, self.ser.baud, self.q_motor_tables))
                self.f1.daemon = True
                self.f1.start()

    def window_updater(self):
        param_list = []
        motors_table = []
        self.lock.acquire()
        udp_status = False
        if not self.q_udp_status.empty():
            udp_status = self.q_udp_status.get()
        if not udp_status:
            self.thread_is_running = False
        if not self.q_data.empty():
            self.udp_data_dict = self.q_data.get()
        while not self.q_data.empty():
            x = self.q_data.get()
        if not self.q_motor_tables.empty():
            param_list = list(self.q_motor_tables.get().split(','))
            motors_table = self.q_motor_tables.get()
        while not self.q_motor_tables.empty():
            x = self.q_motor_tables.get()
        self.lock.release()
        if len(param_list) > 0:
            self.update_motors_to_monwin_table(param_list, motors_table)
            param_list.clear()
            motors_table.clear()
        self.update_monitor_frame(self.udp_data_dict, self.no_rows, self.no_columns)
        if self.startpause:
            self.after(UPDATE_RATE_IN_MS, self.window_updater)
        elif not self.startpause:
            # update all window
            self.update_window()
            self.after(1000, self.window_updater)

    def update_motors_to_monwin_table(self, param_list, motors_table):
        no_rows = len(self.monwin_table)
        no_para_list_rows = len(param_list)
        for row in range(1, no_rows):
            for row2 in range(no_para_list_rows):
                str_temp = param_list[row2]
                str_other = self.monwin_table[row][0]
                if self.monwin_table[row][0] == param_list[row2]:
                    for col in range(8):
                        self.monwin_table[row][col+27] = str(motors_table[row2][col])
        for col in range(8):
            self.motor_max_table[col] = 0
            for row in range(len(motors_table)):
                if int(motors_table[row][col]) >= self.motor_max_table[col]:
                    self.motor_max_table[col] = int(motors_table[row][col])

    def create_monwin_table(self):
        monwin_table_name_row = []
        monwin_table = []
        # -- first row => Parameter names
        monwin_table_name_row.append('Parameter')
        monwin_table_name_row.append('act')
        monwin_table_name_row.append('act_min')
        monwin_table_name_row.append('act_max')
        no_columns = len(self.ff_profile[0])
        for col in range(1, no_columns):
            monwin_table_name_row.append(self.ff_profile[0][col])
        monwin_table_name_row.append('M_act')
        for mot in range(8):
            monwin_table_name_row.append(('M' + str(mot)))
        no_col = len(monwin_table_name_row)
        str_temp = ''
        for colu in range(no_col):
            str_temp = str_temp + monwin_table_name_row[colu] + ','
        str_temp = str_temp[:-1]
        temp_table = list(str_temp.split(','))
        monwin_table.append(temp_table)
        # ---- next rows => parameter names and creating empty strings
        no_columns = len(monwin_table_name_row)+1
        # monwin_table_name_row.clear()
        no_rows = len(self.mon_parameter_list)
        param_names = self.mon_parameter_list
        str_lines = ''
        for row in range(no_rows):
            str_temp = param_names[row]
            for col in range(1, no_columns):
                str_temp = str_temp + ',-'
            str_temp = str_temp[:-2]
            str_lines = str_lines + str_temp + '\n'
            test = list(str_temp.split(','))
            if not row == no_rows:
                monwin_table.append(test)
        # --- add profile data into the table ---------
        no_mon_rows = len(self.mon_parameter_list)+1
        no_prof_rows = len(self.ff_profile)
        no_prof_columns = len(self.ff_profile[0])
        for row in range(1, no_mon_rows):
            mon_para = monwin_table[row][0]
            for row2 in range(1, no_prof_rows):
                prof_para = self.ff_profile[row2][0]
                if mon_para == prof_para:
                    for col in range(no_prof_columns):
                        check = self.ff_profile[row2][col]
                        monwin_table[row][col+3] = self.ff_profile[row2][col]
        return monwin_table

    def update_window(self):
        status = self.update_main_win_q.empty()
        if not status:
            self.lock.acquire()
            self.update_main_window = self.update_main_win_q.get()
            self.lock.release()
        if self.update_main_window:
            self.filename_table = self.read_init_file('default.ini')
            # -------- get monitor data window parameter name list --------------
            self.mon_parameter_list = self.mon.load_window_new(self.filename_table[0][1])
            # --------- load default (latest) ForceFeel motor control profile
            self.ff_profile = self.mon.load_profile_file(self.filename_table[1][1])
            act_old = []
            act_new = []
            no_all_rows = len(self.all_parameters_list)
            for row in range(no_all_rows):
                act_new.append(0.000)
                act_old.append(0.001)
            self.actual_old_new.clear()
            self.actual_old_new.append(act_old)
            self.actual_old_new.append(act_new)
            # --- create monitoring table => fetch profile information -------------
            self.monwin_table = self.create_monwin_table()
            # initiate min and max monitoring values
            no_rows = len(self.monwin_table)
            for row in range(no_rows):
                self.act_min_list.append(0.0)
                self.act_max_list.append(0.0)
            self.update_new_monwin()
            self.update_main_window = False


if __name__ == '__main__':
    root = tk.Tk()
    app = Window(root)
    app.window_name('Condor 2 ForceFeel interface')
    app.update_new_monwin()
    app.window_updater()
    root.mainloop()
