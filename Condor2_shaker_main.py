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
        self.flt_min_list = []
        self.flt_max_list = []
        self.monwin_table = []

        self.all_parameters_list = self.load_all_parameters()
        flt_old = []
        flt_new = []
        no_all_rows = len(self.all_parameters_list)
        for row in range(no_all_rows):
            flt_new.append(0.000)
            flt_old.append(0.001)

        self.actual_old_new = []
        self.actual_old_new.append(flt_old)
        self.actual_old_new.append(flt_new)

        # --- create monitoring table => fetch profile information -------------
        self.monwin_table = self.create_monwin_table()
        # initiate min and max monitoring values
        no_rows = len(self.monwin_table)
        for row in range(no_rows):
            self.flt_min_list.append(0.0)
            self.flt_max_list.append(0.0)

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

        # ----------- Menu definitions ----------------------------------------------------
        # creating a menu instance
        self.menu = tk.Menu(self.master)
        self.master.config(menu=self.menu)

        # create the file object)
        file = tk.Menu(self.menu, tearoff=False)

        # adds a command to the menu option, calling it exit, and the
        # command it runs on event is client_exit
        # file.add_command(label="Open")
        # file.add_command(label="Save")
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
        # edit.add_command(label="Select and edit monitor window parameters")
        self.edit.add_command(label="Undo")

        # added "Edit" to our menu
        self.menu.add_cascade(label="Edit", menu=self.edit)

        # ----------------- Menu definitions ended -----------------------------------

        # Create main header => shows the active motor shaking profile
        self.lb_header_var = tk.StringVar()
        self.lb_header = tk.Label(textvariable=self.lb_header_var, width=60)
        self.lb_header.grid(row=0, column=0, sticky='W')
        lb_header_font = tkFont.Font(size=12, weight='bold')
        self.lb_header.configure(font=lb_header_font,anchor='e',  justify='left')
        str_temp = 'Profile file: ' + self.filename_table[1][1] + 'Monitor file: ' \
                   + self.filename_table[0][1]
        self.lb_header_var.set(str_temp)
        # ---------- add 10 row and 10 columns
        self.lbl_table = []
        self.label = []
        self.no_rows = len(self.mon_parameter_list)
        self.no_columns = 10
        self.monitor_start_row = 15
        self.monitor_end_row = 32
        # -----------Data Frame----------------------------------------------------
        # bg =  background colour (ascii code)
        bg = '#ccddff'
        #  bold first row text and set size
        self.headerFont = tkFont.Font(size=10, weight='bold')

        # -------------Data Frame ended-----------------------------------------------------------
        # ------------ mon frame start -------------------
        self.mon_frame = tk.Frame()
        self.mon_frame.grid(column=0, row=2, columnspan=2, sticky='W', padx=10, pady=10)
        self.monwin_str_table = []
        self.mon_lbl_param = []
        self.mon_lbl_stringvar = []
        self.mon_txt_param = []
        #  -- convert monwin_table to string table
        self.monwin_str_table = self.monwin_table_to_string_table(self.monwin_table)
        #  --- add labels and text windows -------------
        no_col = len(self.monwin_str_table)
        no_row = len(self.monwin_table[0])
        width_table = [20, 10, 10, 10, 10, 12, 12, 13, 13, 17, 7]
        no_width = len(width_table)
        standard_width = 10
        if no_width < no_col:
            for col in range(no_width, no_col):
                width_table.append(standard_width)
        for col in range(no_col):
            self.mon_lbl_stringvar.append(tk.StringVar())
            self.mon_lbl_param.append(tk.Label(self.mon_frame, textvariable=self.mon_lbl_stringvar[col],
                                               width=width_table[col]))
            self.mon_lbl_param[col].grid(column=col, row=0, sticky='W', padx=2, pady=2)
            self.mon_txt_param.append(tk.Text(self.mon_frame, height=self.no_rows-1, width=width_table[col], bg=bg))
            self.mon_txt_param[col].grid(column=col, row=1, sticky='W', padx=2, pady=2)

        for xx in range(no_col):
            self.mon_lbl_param[xx].configure(font=self.headerFont, anchor='w', justify='left')

        self.monwin_init()

        # ------------ mon frame ended --------------------
        # get UDP parameter list => function call Condor_UDP_data_arrays() that returns dictionary
        self.udp_data_dict = self.udp.condor_udp_data_arrays()
        # ------- update monitor data window => update ForceFeel motor control values to monitor parameter list
        # --- self.udp_data_dict
        # self.profile_to_monitor(self.ff_profile)
        self.update_monitor_frame(self.udp_data_dict, self.no_rows, self.no_columns)
        # define Start/Pause button and text variable
        btn_font = tkFont.Font(size=14, weight='bold')
        #  --------------- Button Frame ---------------------------------------
        button_frame = tk.Frame()
        self.btn_startpause_var = tk.StringVar()
        self.btn_start_pause = tk.Button(button_frame, textvariable=self.btn_startpause_var, command=self.start_monitoring)
        self.btn_start_pause.grid(row=0, column=1, padx=2, pady=2)
        self.btn_start_pause.configure(font=btn_font)
        self.btn_startpause_var.set('Start')
        self.startpause = False
        button_frame.grid(row=0, column=1, sticky='N', padx=2, pady=2)
        # -------------- Button frame ended ----------------------------------------
    # ------------ class Window(tk.Frame) init ended --------------------

    def read_init_file(self, filename):
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

    def load_all_parameters(self):
        datadict = self.udp.condor_udp_data_arrays()
        parameter_list = list(datadict.keys())
        return parameter_list

    def monwin_init(self):
        no_columns = len(self.monwin_str_table)
        for col in range(no_columns):
            str_para, str_data = self.monwin_str_table[col].split(',')
            self.mon_lbl_stringvar[col].set(str_para)
            self.mon_txt_param[col].insert(tk.INSERT, str_data)

    def update_new_monwin(self):
        str_temp = 'Profile file: ' + self.filename_table[1][1] + '\t\tMonitor file: ' \
                   + self.filename_table[0][1]
        self.lb_header_var.set(str_temp)
        no_columns = len(self.monwin_str_table)
        self.no_rows = len(self.mon_parameter_list)
        for col in range(no_columns):
            self.mon_txt_param[col].config(state=tk.NORMAL)
            self.mon_txt_param[col].delete('1.0', tk.END)
            str_para, str_data = self.monwin_str_table[col].split(',')
            self.mon_txt_param[col].insert(tk.INSERT, str_data)
            self.mon_txt_param[col].config(height=self.no_rows)
            self.mon_txt_param[col].grid()
            self.mon_txt_param[col].config(state=tk.DISABLED)

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
            self.flt_min_list[row] = 0.0
            self.flt_max_list[row] = 0.0

    def load_profile_table(self, load_filename):
        # --- call load_profile_file function from Prof_Window class
        profile_table = self.mon.load_profile_file(load_filename)
        return profile_table

    def profile_to_datadict(self, profile_table):
        parameter_column_names = profile_table[0]
        no_rows = len(profile_table)
        for row in range(1, no_rows):
            filtercoeff = int(profile_table[row][1])
            flt_min_limit = float(profile_table[row][2])
            flt_max_limit = float(profile_table[row][3])
            mot_min_limit = int(profile_table[row][4])
            mot_max_limit = int(profile_table[row][5])
            motor_str = profile_table[row][6]
            str_temp = profile_table[row][0]
            self.udp_data_dict[profile_table[row][0]]['filtercoeff'] = filtercoeff
            self.udp_data_dict[profile_table[row][0]]['flt_min_limit'] = flt_min_limit
            self.udp_data_dict[profile_table[row][0]]['flt_max_limit'] = flt_max_limit
            self.udp_data_dict[profile_table[row][0]]['mot_min_limit'] = mot_min_limit
            self.udp_data_dict[profile_table[row][0]]['mot_max_limit'] = mot_max_limit
            self.udp_data_dict[profile_table[row][0]]['Motors'] = motor_str



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
        # subroot2.geometry("1350x750+500+300")
        subapp2 = ffprof.Prof_window(subroot2, self.update_main_win_q, self.lock)
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
        for row in range(1, no_rows2):
            names_temp2.append(self.monwin_table[row][0])
    #    update new monitor window here
        no_names2 = len(names_temp2)
        flt_actual = 0.0
        flt_min_old = 0.0
        flt_max_old = 0.0
        for row in range(0, no_names2):
            if not self.minmax_reset:
                flt_min_old = self.flt_min_list[row]
                flt_max_old = self.flt_max_list[row]
                flt_actual = data1[names_temp2[row]]['actual']
                flt_actual = round(flt_actual, 3)
                self.actual_old_new[1][row] = flt_actual
                self.monwin_table[row+1][1] = str(flt_actual)
                if flt_actual >= flt_max_old:
                    self.flt_max_list[row] = flt_actual
                elif flt_actual < flt_min_old:
                    self.flt_min_list[row] = flt_actual
            self.monwin_table[row+1][2] = str(self.flt_min_list[row])
            self.monwin_table[row+1][3] = str(self.flt_max_list[row])
            if self.monwin_table[row+1][9] != '-':
                mot_act = data1[names_temp2[row]]['M_act']
                self.monwin_table[row+1][10] = str(mot_act)
        self.minmax_reset = False
        # ----- refresh screens
        self.monwin_str_table = self.monwin_table_to_string_table(self.monwin_table)
        self.update_new_monwin()
        self.mon_txt_param[1].grid()
        # check if Condor is paused or not => most of the telemetry datas are not changing
        self.condor2_game_pause = self.check_if_Condor2_pause(data1)
        if self.condor2_game_pause:
            if not self.ff_test_activated and not self.motors_reseted:
                self.lock.acquire()
                self.ser.Send('M00\rM10\rM20\rM30\rM40\rM50\rM60\rM70\r')
                self.lock.release()
                # self.motors_reseted = True


    def check_if_Condor2_pause(self, data1):
        is_pause = False
        no_rows = len(self.actual_old_new[0])
        counter = 0
        for row in range(no_rows):
            flt_actual = data1[self.all_parameters_list[row]]['actual']
            flt_actual = round(flt_actual, 3)
            self.actual_old_new[1][row] = flt_actual
            if self.actual_old_new[0][row] == self.actual_old_new[1][row]:
                counter = counter + 1
            self.actual_old_new[0][row] = self.actual_old_new[1][row]
        if counter > 15:
            is_pause = True
        # print(counter)
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
                                            self.ser, self.ser.comport, self.ser.baud))
                self.f1.daemon = True
                self.f1.start()

    def window_updater(self):
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
        self.lock.release()
        self.update_monitor_frame(self.udp_data_dict, self.no_rows, self.no_columns)
        if self.startpause:
            self.after(UPDATE_RATE_IN_MS, self.window_updater)
        elif not self.startpause:
            # update all window
            self.update_window()
            self.after(1000, self.window_updater)

    def create_monwin_table(self):
        monwin_table_name_row = []
        monwin_table = []
        # -- first row => Parameter names
        monwin_table_name_row.append('Parameter')
        monwin_table_name_row.append('act')
        monwin_table_name_row.append('flt_min')
        monwin_table_name_row.append('flt_max')
        no_columns = len(self.ff_profile[0])
        for col in range(1, no_columns):
            monwin_table_name_row.append(self.ff_profile[0][col])
        monwin_table_name_row.append('M_act')
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
                    for col in range(1, no_prof_columns):
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
            flt_old = []
            flt_new = []
            no_all_rows = len(self.all_parameters_list)
            for row in range(no_all_rows):
                flt_new.append(0.000)
                flt_old.append(0.001)
            self.actual_old_new.clear()
            self.actual_old_new.append(flt_old)
            self.actual_old_new.append(flt_new)
            # --- create monitoring table => fetch profile information -------------
            self.monwin_table = self.create_monwin_table()
            # initiate min and max monitoring values
            no_rows = len(self.monwin_table)
            for row in range(no_rows):
                self.flt_min_list.append(0.0)
                self.flt_max_list.append(0.0)
            self.update_new_monwin()
            self.update_main_window = False


if __name__ == '__main__':
    root = tk.Tk()
    app = Window(root)
    app.window_name('Condor 2 ForceFeel interface')
    app.update_new_monwin()
    app.window_updater()
    root.mainloop()
