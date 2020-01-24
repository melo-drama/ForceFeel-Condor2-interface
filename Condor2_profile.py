import tkinter as tk
import csv
import Shaker_comport as ffcom
from tkinter import ttk
import Condor2_udp_com as udp
import os
from tkinter import messagebox
from tkinter import filedialog
import queue
import threading
import time
import math


class Prof_window(tk.Frame):
    def __init__(self, master, q_data, lock, ser):
        tk.Frame.__init__(self, master)

        #  ------------------
        self.master = master
        self.ser = ser
        self.q_data_out = queue.Queue()
        self.q_data_in = queue.Queue()
        self.test_lock = threading.Lock()

        self.lock = lock
        self.q_data = q_data

        status = self.q_data.empty
        self.lock.acquire()
        if not status:
            window_refresh_status = self.q_data.get()
        self.lock.release()
        self.profile = Profiler()
        self.monfile_list = []
        self.proffile_list = []
        self.monwin_parameter_list = []
        self.profile_parameter_list = []
        self.all_parameters_list = []
        self.add_mon_par_list = []
        self.del_mon_par_list = []
        self.profile_param_names = []
        self.new_prof_param_list = []
        self.prof_edit_or_del = False
        self.save_as_or_not = False
        self.get_monfile_list()
        self.get_proffile_list()

        self.instances_created = False
        self.test_thread_created = False
        self.motor_calibration_table = []
        for mot in range(8):
            self.motor_calibration_table.append(1.0)

        # --- get and read default.init file ----------
        if not os.path.isfile('default.ini'):   # --- this function is not done yet (27.12.2019)
            pass
        self.filename_table = self.profile.read_init_file('default.ini')
        self.all_parameters_list = self.load_all_parameters()
        self.profile_parameter_list = self.profile.load_profile_file(self.filename_table[1][1])
        if len(self.filename_table) > 3:
            self.motor_calibration_table = self.profile.get_motor_calibration_table(self.filename_table)

        for cell in range(len(self.all_parameters_list)):
            self.new_prof_param_list.append(self.all_parameters_list[cell])
            self.add_mon_par_list.append(self.all_parameters_list[cell])
        no_rows = len(self.profile_parameter_list)
        for row in range(1, no_rows):
            self.profile_param_names.append(self.profile_parameter_list[row][0])

        self.update_new_prof_parlist()

        # changing the title of our master widget
        self.master.title("default")
        self.grid(column=0, row=0)
        # creating a menu instance
        menu = tk.Menu(self.master)
        self.master.config(menu=menu)
        # create the file object)
        file = tk.Menu(menu, tearoff=False)
        # adds a command to the menu option, calling it exit, and the
        # command it runs on event is client_exit
        file.add_command(label="Open")
        file.add_command(label="Save as Profile", command=self.save_as_prof)
        file.add_command(label="Save as Monitor", command=self.save_as_mon)
        file.add_command(label="Exit and update main window", command=self.client_exit)
        # added "file" to our menu
        menu.add_cascade(label="File", menu=file)

        bg2 = '#3399ff'

        self.mon_frame = tk.Frame(self)
        self.mon_frame.grid(column=0, row=0, rowspan=8, sticky='NW', padx=5, pady=5)
        self.mon_frame.config(highlightbackground=bg2, highlightthickness=2)
        self.profile_frame = tk.Frame(self)
        self.profile_frame.grid(column=2, row=0, rowspan=2, padx=5, pady=5, sticky='NW')
        self.profile_frame.config(highlightbackground=bg2, highlightthickness=2)

        # ---- add label to frame -------
        lbl_select_monwin_file = tk.Label(self.mon_frame, text='Select monitor file')
        lbl_select_monwin_file.grid(column=0, row=0, columnspan=2, sticky='W')
        # ------ add Combobox to frame -------
        self.combo_select_monwin = ttk.Combobox(self.mon_frame, values=self.monfile_list, width=25)
        self.combo_select_monwin.grid(column=0, row=1, sticky='W', padx=4, pady=4)
        index = 0
        for row in range(len(self.monfile_list)):
            temp = self.monfile_list[row]
            if temp == self.filename_table[0][1]:
                index = row
        self.combo_select_monwin.current(index)
        self.combo_select_monwin.bind("<<ComboboxSelected>>", self.callback_monFunc)
        filename = self.combo_select_monwin.get()
        name_list = self.profile.load_window_new(filename)
        no_monwin_rows = len(name_list)
        self.del_mon_par_list = name_list
        self.update_add_mon_par_list()
        lbl_load_parameter = tk.Label(self.mon_frame, text='Add parameter')
        lbl_load_parameter.grid(column=0, row=2, sticky='W', padx=4, pady=2)
        self.combo_select_mon_par = ttk.Combobox(self.mon_frame, values=self.add_mon_par_list, width=25)
        self.combo_select_mon_par.grid(column=0, row=3, sticky='W', padx=4, pady=2)
        self.combo_select_mon_par.current(0)
        self.combo_select_mon_par.bind("<<ComboboxSelected>>", self.callback_add_monFunc)
        # --- add another label ---------------------
        lbl_monwin_text = tk.Label(self.mon_frame, text='Monitor parameter list')
        lbl_monwin_text.grid(column=0, row=4, sticky='W', padx=10)
        # ------- add multientry label (=text) to frame -------
        self.text_monwin = tk.Text(self.mon_frame, height=no_monwin_rows, width=35)
        self.text_monwin.grid(column=0, row=5, columnspan=2, rowspan=34, sticky='W', padx=10, pady=5)

        self.load_monwin_file()

        # ---- add Save monitor file button to mon_frame ---------
        self.btn_save_mon = tk.Button(self.mon_frame, text='Save monitor file', command=self.save_mon)
        self.btn_save_mon.grid(column=1, row=0, sticky='N', padx=2, pady=2)
        # ----- add delete monitor file button to mon_frame
        self.btn_del_mon = tk.Button(self.mon_frame, text='Delete monitor file', command=self.del_monfile)
        self.btn_del_mon.grid(column=2, row=0, sticky='N', padx=2, pady=2)
        # --- add del combobox to mon_frame ------------
        lbl_remove_parameter = tk.Label(self.mon_frame, text='Remove parameter')
        lbl_remove_parameter.grid(column=1, row=2, sticky='W', padx=4, pady=2)
        self.combo_del_mon_par = ttk.Combobox(self.mon_frame, values=self.del_mon_par_list, width=25)
        self.combo_del_mon_par.grid(column=1, row=3, sticky='W', padx=4, pady=2)
        self.combo_del_mon_par.current(0)
        self.combo_del_mon_par.bind("<<ComboboxSelected>>", self.callback_del_monFunc)

        # ----------- add profile combobox ------------------
        lbl_select_profile = tk.Label(self.profile_frame, text='Select profile')
        lbl_select_profile.grid(column=0, row=0, sticky='W', padx=10)
        self.combo_select_profile = ttk.Combobox(self.profile_frame, values=self.proffile_list)
        self.combo_select_profile.grid(column=0, row=1, sticky='W', padx=10, pady=2)
        index = 0
        for row in range(len(self.proffile_list)):
            temp = self.proffile_list[row]
            if temp == self.filename_table[1][1]:
                index = row
        self.combo_select_profile.current(index)
        self.combo_select_profile.bind("<<ComboboxSelected>>", self.callback_profileFunc)
        lbl_load_profile_parameter = tk.Label(self.profile_frame, text='Add profile parameter')
        lbl_load_profile_parameter.grid(column=0, row=2, sticky='W', padx=10, pady=2)
        self.combo_select_prof_par = ttk.Combobox(self.profile_frame, values=self.new_prof_param_list, width=25)
        self.combo_select_prof_par.grid(column=0, row=3, sticky='W', padx=10, pady=2)
        self.combo_select_prof_par.current(0)
        self.combo_select_prof_par.bind("<<ComboboxSelected>>", self.callback_add_profFunc)
        lbl_profile_text = tk.Label(self.profile_frame, text='Profile functions and values')
        lbl_profile_text.grid(column=0, row=4, sticky='W', padx=10)
        # --- add profile parameter label list here
        prof_param_name_list = self.profile_parameter_list[0]
        no_rows = len(self.profile_parameter_list)
        start_column = 0
        start_row = 5
        width = [25, 10, 10, 10, 10, 10, 17]
        no_columns = len(width)

        pos_list1 = ['E', 'W', 'W', 'W', 'W', 'W', 'W']
        self.lbl_prof_param_names = []
        self.text_prof_param = []
        for col in range(0, no_columns):
            self.lbl_prof_param_names.append(tk.Label(self.profile_frame, text=prof_param_name_list[col],
                                                      width=width[col]))
            self.lbl_prof_param_names[col].grid(column=start_column + col, row=start_row, sticky=pos_list1[col],
                                                padx=2, pady=2)
            self.text_prof_param.append(tk.Text(self.profile_frame, height=no_rows - 1, width=width[col]))
            self.text_prof_param[col].grid(column=col + start_column, row=start_row + 1, sticky='W', padx=2, pady=2)
        for col in range(no_columns):
            str_temp = ''
            for row in range(1, no_rows):
                str_temp = str_temp + self.profile_parameter_list[row][col] + '\n'
            self.text_prof_param[col].insert(tk.INSERT, str_temp)
            self.text_prof_param[col].config(state=tk.DISABLED)
        lbl_del_profile_parameter = tk.Label(self.profile_frame, text='Edit or remove profile parameter')
        lbl_del_profile_parameter.grid(column=1, row=2, columnspan=2, sticky='W', padx=4, pady=2)
        self.combo_del_prof_par = ttk.Combobox(self.profile_frame, values=self.profile_param_names, width=25)
        self.combo_del_prof_par.grid(column=1, row=3, columnspan=2, sticky='W', padx=4, pady=2)
        self.combo_del_prof_par.current(0)
        self.combo_del_prof_par.bind("<<ComboboxSelected>>", self.callback_edit_profFunc)
        # ---- add Save profile file button -----------------
        self.btn_save_prof = tk.Button(self.profile_frame, text='Save profile', command=self.save_prof)
        self.btn_save_prof.grid(column=2, row=0, sticky='W', padx=2, pady=2)
        # --------- add Delete profile button --------------
        self.btn_del_prof = tk.Button(self.profile_frame, text='Delete profile', command=self.del_proffile)
        self.btn_del_prof.grid(column=3, row=0, sticky='W', padx=2, pady=2)

        # --- create profile edit frame
        self.prof_edit_frame = tk.Frame(self)
        self.prof_edit_frame.grid(column=2, row=2, sticky='N', padx=4, pady=4)

        # --- create param_edit_frame (sub frame from prof edit frame)
        self.param_edit_frame = tk.Frame(self.prof_edit_frame)
        self.param_edit_frame.grid(column=0, row=0, sticky='W', padx=0, pady=0)
        self.param_edit_frame.config(highlightbackground=bg2, highlightthickness=2)
        lbl_edit_prof_names = []
        #  create parameter name labels
        for col in range(no_columns - 1):
            lbl_edit_prof_names.append(tk.Label(self.param_edit_frame, text=prof_param_name_list[col],
                                                width=width[col]))
            lbl_edit_prof_names[col].grid(column=col, row=0, sticky='W', padx=2, pady=2)
        # create edit list row
        self.profile_parameter = tk.StringVar()
        self.lbl_profile_parameter = tk.Label(self.param_edit_frame, textvariable=self.profile_parameter,
                                              width=width[0])
        self.lbl_profile_parameter.grid(column=0, row=1, sticky='W', padx=2, pady=2)
        # --- create entry cells ---
        width = [25, 15, 15, 15, 15, 15, 8]
        varlist_init_table = ['1', '0', '0', '10', '20']
        for col in (len(varlist_init_table),(no_columns-2)):
            varlist_init_table.append('0')
        self.edit_profile_entries = []
        self.edit_profile_var_list = []
        for col in range(no_columns - 2):
            self.edit_profile_var_list.append(tk.StringVar())
            self.edit_profile_entries.append(tk.Entry(self.param_edit_frame,
                                                      textvariable=self.edit_profile_var_list[col],
                                                      width=width[col + 1]))
            self.edit_profile_entries[col].grid(column=col + 1, row=1, sticky='W', padx=2, pady=2)
            self.edit_profile_var_list[col].set(varlist_init_table[col])
        # -- create motor selection checklists and motor gain entries
        lbl_gain1 = tk.Label(self.param_edit_frame, text='gain')
        lbl_gain1.grid(column=no_columns, row=0, padx=2, pady=2)
        lbl_motor = tk.Label(self.param_edit_frame, text=' Motors', justify='center')
        lbl_motor.grid(column=(no_columns+1), row=0, columnspan=2, sticky='N', padx=2, pady=2)

        lbl_gain2 = tk.Label(self.param_edit_frame, text='gain', justify='left', width=4)
        lbl_gain2.grid(column=(no_columns+3), row=0, sticky='W', padx=2, pady=2)
        self.motor_check_btn_list = []
        self.motor_check_varlist = []
        self.motor_gain_entr_list = []
        self.motor_gain_entr_varlist = []
        col_list = [3, 0, 3, 0, 3, 0, 3, 0]
        entr_col_list = [3, 0, 3, 0, 3, 0, 3, 0]
        pos_list = ['W', 'E', 'W', 'E', 'W', 'E', 'W', 'E']
        str_help = ''
        for mot in range(8):
            self.motor_check_varlist.append(tk.IntVar())
            self.motor_gain_entr_varlist.append(tk.StringVar())
            if mot % 2 == 0:
                str_help = str(mot + 1)
            elif mot % 2 == 1:
                str_help = str(mot - 1)
            self.motor_check_btn_list.append(tk.Checkbutton(self.param_edit_frame, text=('M' + str_help),
                                                            variable=self.motor_check_varlist[mot],
                                                            command=self.chk_motor_btn_and_gain,
                                                            onvalue=1, offvalue=0, height=1, width=2))
            self.motor_check_btn_list[mot].grid(column=(no_columns + 1 + mot % 2), row=(1 + int(mot / 2)), sticky='W')
            self.motor_gain_entr_list.append(tk.Entry(self.param_edit_frame,
                                                      textvariable=self.motor_gain_entr_varlist[mot],
                                                      width=4))
            self.motor_gain_entr_list[mot].grid(column=(no_columns+entr_col_list[mot]), row=(1+int(mot/2)),
                                                sticky=pos_list[mot], padx=3, pady=1)
            self.motor_gain_entr_varlist[mot].set(1.0)
            self.motor_gain_entr_list[mot].config(state=tk.DISABLED)
        # ----- Add resonance freq parameter entries
        #  -- res_enabled - checkbox -----------
        self.mod_check_var = tk.IntVar()
        self.mod_check_btn = tk.Checkbutton(self.param_edit_frame, text='Modulator', variable=self.mod_check_var,
                                            command=self.chk_motor_btn_and_gain, onvalue=True, offvalue=False)
        self.mod_check_btn.grid(column=1, row=2, rowspan=2, sticky='W', padx=2, pady=2)
        self.mod_check_var.set(False)
        self.mod_lbl_period = tk.Label(self.param_edit_frame, text='period [s]')
        self.mod_lbl_period.grid(column=2, row=2, sticky='N', padx=2, pady=2)
        self.mod_lbl_period.config(state=tk.DISABLED)
        self.mod_lbl_ratio = tk.Label(self.param_edit_frame, text='ratio [<1.0]')
        self.mod_lbl_ratio.grid(column=3, row=2, sticky='N', padx=2, pady=2)
        self.mod_lbl_ratio.config(state=tk.DISABLED)
        self.mod_lbl_ampl = tk.Label(self.param_edit_frame, text='ampl [<1.0]')
        self.mod_lbl_ampl.grid(column=4, row=2, sticky='N', padx=2, pady=2)
        self.mod_lbl_ampl.config(state=tk.DISABLED)

        self.mod_period_var = tk.StringVar()
        self.mod_entr_period = tk.Entry(self.param_edit_frame, textvariable=self.mod_period_var, width=4)
        self.mod_entr_period.grid(column=2, row=3, sticky='N', padx=2, pady=2)
        self.mod_period_var.set(0.0)
        self.mod_entr_period.config(state=tk.DISABLED)
        self.mod_ratio_var = tk.StringVar()
        self.mod_entr_ratio = tk.Entry(self.param_edit_frame, textvariable=self.mod_ratio_var, width=4)
        self.mod_entr_ratio.grid(column=3, row=3, sticky='N', padx=2, pady=2)
        self.mod_ratio_var.set(0.0)
        self.mod_entr_ratio.config(state=tk.DISABLED)
        self.mod_ampl_var = tk.StringVar()
        self.mod_entr_ampl = tk.Entry(self.param_edit_frame, textvariable=self.mod_ampl_var, width=4)
        self.mod_entr_ampl.grid(column=4, row=3, sticky='N', padx=2, pady=2)
        self.mod_ampl_var.set(0.0)
        self.mod_entr_ampl.config(state=tk.DISABLED)

        self.mod_lbl_offset1 = tk.Label(self.param_edit_frame, text='offset1 [<1.0]')
        self.mod_lbl_offset1.grid(column=2, row=4, sticky='N', padx=2, pady=2)
        self.mod_lbl_offset1.config(state=tk.DISABLED)
        self.mod_lbl_offset2 = tk.Label(self.param_edit_frame, text='offset2 [<1.0]')
        self.mod_lbl_offset2.grid(column=3, row=4, sticky='N', padx=2, pady=2)
        self.mod_lbl_offset2.config(state=tk.DISABLED)
        self.mod_lbl_rand_ampl = tk.Label(self.param_edit_frame, text='rand_ampl [<1.0]')
        self.mod_lbl_rand_ampl.grid(column=4, row=4, sticky='N', padx=2, pady=2)
        self.mod_lbl_rand_ampl.config(state=tk.DISABLED)
        # --- res - entries
        self.mod_offset1_var = tk.StringVar()
        self.mod_entr_offset1 = tk.Entry(self.param_edit_frame, textvariable=self.mod_offset1_var, width=4)
        self.mod_entr_offset1.grid(column=2, row=5, sticky='N', padx=2, pady=2)
        self.mod_offset1_var.set(0.0)
        self.mod_entr_offset1.config(state=tk.DISABLED)
        self.mod_offset2_var = tk.StringVar()
        self.mod_entr_offset2 = tk.Entry(self.param_edit_frame, textvariable=self.mod_offset2_var, width=4)
        self.mod_entr_offset2.grid(column=3, row=5, sticky='N', padx=2, pady=2)
        self.mod_offset2_var.set(0.0)
        self.mod_entr_offset2.config(state=tk.DISABLED)
        self.mod_rand_ampl_var = tk.StringVar()
        self.mod_entr_rand_ampl = tk.Entry(self.param_edit_frame, textvariable=self.mod_rand_ampl_var, width=4)
        self.mod_entr_rand_ampl.grid(column=4, row=5, sticky='N', padx=2, pady=2)
        self.mod_rand_ampl_var.set(0.0)
        self.mod_entr_rand_ampl.config(state=tk.DISABLED)

        self.rand_check_var = tk.IntVar()
        self.rand_check_btn = tk.Checkbutton(self.param_edit_frame, text='Rand motors\n separately',
                                             variable=self.rand_check_var, command=self.chk_motor_btn_and_gain,
                                             onvalue=True, offvalue=False)
        self.rand_check_btn.grid(column=4, row=6, rowspan=2, sticky='W', padx=2, pady=2)
        self.rand_check_var.set(False)
        self.rand_check_btn.config(state=tk.DISABLED)
        # random start time
        self.rand_starttime_check_var = tk.IntVar()
        self.rand_starttime_check_btn = tk.Checkbutton(self.param_edit_frame, text='Random\n start time',
                                                       variable=self.rand_starttime_check_var,
                                                       command=self.chk_motor_btn_and_gain,
                                                       onvalue=True, offvalue=False)
        self.rand_starttime_check_btn.grid(column=3, row=6, rowspan=2, sticky='W', padx=2, pady=2)
        self.rand_starttime_check_var.set(False)
        self.rand_starttime_check_btn.config(state=tk.DISABLED)

        # ---- Modulator - entry labels

        # ---- add function Start/stop test button, label text and entries
        self.test_lbl = tk.Label(self.param_edit_frame, text='actual')
        self.test_lbl.grid(column=0, row=2, sticky='N', padx=2, pady=2)
        self.test_entry_var = tk.StringVar()
        self.test_entry = tk.Entry(self.param_edit_frame, textvariable=self.test_entry_var, justify='center', width=6)
        self.test_entry.grid(column=0, row=3, sticky='N', padx=2, pady=2)
        self.test_entry.bind('<Return>', self.update_testing)
        self.test_entry_var.set(0.0)
        self.test_lbl2 = tk.Label(self.param_edit_frame, text='Test parameter')
        self.test_lbl2.grid(column=0, row=4, sticky='N', padx=2, pady=2)
        self.test_btn_startstop = tk.Button(self.param_edit_frame, text='Start', command=self.start_stop_test,
                                            width=5)
        self.test_btn_startstop.grid(column=0, row=5, sticky='N', padx=2, pady=2)

        self.test_startstop_status = False

        self.act_mot_frame = tk.Frame(self.prof_edit_frame)
        self.act_mot_frame.grid(column=1, row=0, columnspan=3, sticky='W', padx=0, pady=0)
        self.act_mot_frame.configure(highlightbackground=bg2, highlightthickness=2)
        # --- add actual motor speed entries and labels
        m_act_label = tk.Label(self.act_mot_frame, text='Motor speeds')
        m_act_label.grid(column=0, row=0, columnspan=4, padx=8, pady=2)
        # m_act_label.configure(bg=bg)
        col_list = [3, 0, 3, 0, 3, 0, 3, 0]
        entr_col_list = [2, 1, 2, 1, 2, 1, 2, 1]
        self.m_act_mot_var_list = []
        self.m_act_mot_list = []
        self.m_lbl_list = []
        for mot in range(8):
            self.m_lbl_list.append(tk.Label(self.act_mot_frame, text=('M' + str(mot))))
            self.m_lbl_list[mot].grid(column=col_list[mot], row=(1+int(mot/2)))

            self.m_act_mot_var_list.append(tk.StringVar())
            self.m_act_mot_list.append(tk.Entry(self.act_mot_frame,
                                                textvariable=self.m_act_mot_var_list[mot], width=3))
            self.m_act_mot_list[mot].grid(column=entr_col_list[mot], row=(1+int(mot/2)))
            self.m_act_mot_var_list[mot].set(0)
            self.m_act_mot_list[mot].config(state=tk.DISABLED)

        # ------- Add Ok, Cancel and Remove buttons
        self.prof_Ok_btn = tk.Button(self.param_edit_frame, text='Ok', width=4, command=self.prof_ok)
        self.prof_Ok_btn.grid(column=7, row=6, sticky='E', padx=2, pady=2)
        self.prof_Cancel_btn = tk.Button(self.param_edit_frame, text='Cancel', width=6, command=self.prof_cancel)
        self.prof_Cancel_btn.grid(column=8, row=6, sticky='E', padx=2, pady=2)
        self.prof_del_btn = tk.Button(self.param_edit_frame, text='Remove', width=8, command=self.prof_del)
        self.prof_del_btn.grid(column=9, row=6, columnspan=2, sticky='E', padx=2, pady=2)
        # hide this grid as default
        self.prof_edit_frame.grid_remove()
    # ------------- end of class Prof_window(tk.Frame) init ------------------------------------------

    def prof_cancel(self):
        self.prof_edit_frame.grid_remove()
        self.combo_select_profile.config(state=tk.NORMAL)
        self.combo_select_prof_par.config(state=tk.NORMAL)
        self.combo_del_prof_par.config(state=tk.NORMAL)

    def start_stop_test(self):
        self.test_startstop_status = not self.test_startstop_status
        if self.test_startstop_status:
            print(' Test started')
        self.update_testing()

    def update_testing(self, event=None):

        parameter_name = ''
        if self.test_startstop_status:
            if not self.instances_created:

                self.udp_instance = udp.CondorUDP(self.ser)
                self.instances_created = True
            self.test_btn_startstop.config(text='Stop')
          # --- gather all parameters from param_edit frame => call get_test_parameters function
            data_table = self.get_test_parameters()
            parameter_name = data_table[1][1]
            dict1 = self.udp_instance.condor_udp_data_arrays()
            dict1[data_table[1][1]][data_table[0][0]] = data_table[1][0]
            for col in range(2, len(data_table[1])):
                dict1[data_table[1][1]][data_table[0][col]] = data_table[1][col]
            self.test_lock.acquire()
            while not self.q_data_out.empty():
                x = self.q_data_out.get()
            self.q_data_out.put(self.test_startstop_status)
            self.q_data_out.put(dict1)
            self.q_data_out.put(parameter_name)
            self.test_lock.release()
            if not self.test_thread_created:
                self.t1 = threading.Thread(target=self.test_parameter_function)
                self.t1.daemon = True
                self.t1.start()
                self.test_thread_created = True

            if not self.q_data_in.empty():
                self.test_lock.acquire()
                motor_str = self.q_data_in.get()
                self.test_lock.release()
                motor_str_list = list(motor_str[:-1].split('\r'))
                motor_speed_list = []
                for mot in range(len(motor_str_list)):
                    motor_speed_list.append(motor_str_list[mot][2:])
                    self.m_act_mot_var_list[mot].set(motor_speed_list[mot])
                # start motor string here !

            self.after(50, self.update_testing)
        # --- stop test function ----------
        if not self.test_startstop_status:
            dict1 = {}
            print(' Test stopped')
            self.test_lock.acquire()
            while not self.q_data_out.empty():
                x = self.q_data_out.get()
            self.q_data_out.put(self.test_startstop_status)
            self.q_data_out.put(dict1)
            self.q_data_out.put(parameter_name)
            self.test_lock.release()
            for mot in range(8):
                self.m_act_mot_var_list[mot].set(0)
                self.test_btn_startstop.config(text='Start')
            # --- stop all motors and stop test function
            self.test_btn_startstop.config(text='Start')
            self.test_thread_created = False

    def test_parameter_function(self):
        test_startstop_status = True
        dict_founded = False
        table_created = False
        if self.ser.isopen:
            self.ser.Close()

        dict1 = {}
        start_time_table = []
        start_time = time.time()
        # start_time_table.append(start_time)
        name_row = ['rand_start', 'rand_counter', 'rand_period', 'rand_ratio']
        parameter_name = ''
        for mot in range(8):
            name_row.append('rand_M' + str(mot))
        rand_start_table = []
        rand_start_table.append(name_row)
        while test_startstop_status:
            self.test_lock.acquire()
            if not self.q_data_out.empty():
                test_startstop_status = self.q_data_out.get()
                dict1 = self.q_data_out.get()
                parameter_name = self.q_data_out.get()
                for row in range(len(dict1)):
                    if not table_created:
                        rand_start_table.append([0.0, 0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
                        start_time_table.append(start_time)
                if not table_created:
                    table_created = True
                dict_founded = True
            self.test_lock.release()

            if test_startstop_status and dict_founded:
                dict1 = self.udp_instance.data_to_motor_ph1(dict1)
                motors_table, start_time_table, rand_start_table = \
                    self.udp_instance.data_to_motor_ph2(dict1, start_time_table, rand_start_table, parameter_name)
                motor_str = self.udp_instance.create_ff_string(motors_table)
                if not self.ser.isopen:
                    self.ser.Open(self.ser.comport, self.ser.baud)
                if self.ser.isopen:
                    self.ser.Send(motor_str)

                self.test_lock.acquire()
                while not self.q_data_in.empty():
                    x = self.q_data_in.get()
                self.q_data_in.put(motor_str)
                self.test_lock.release()
                time.sleep(0.015)

        print('thread will stop')
        if self.ser.isopen:
            self.ser.Send('M00\rM10\rM20\rM30\rM40\rM50\rM60\rM70\r')
            self.ser.Close()


    def get_test_parameters(self):
        parameter_list = []
        parameter_names =[]
        parameter_table = []
        parameter_names.append('actual')
        parameter_list.append(self.test_entry_var.get())
        parameter_names.extend(self.profile_parameter_list[0])
        parameter_list.append(self.profile_parameter.get())
        for col in range(len(self.edit_profile_var_list)):
            parameter_list.append(self.edit_profile_var_list[col].get())
        str_motors = self.motor_checkboxes_to_str()
        parameter_list.append(str_motors)
        for mot in range(8):

            parameter_list.append(self.motor_gain_entr_varlist[mot].get())
        # --- Modulator parameters
        parameter_list.append(self.mod_check_var.get())
        parameter_list.append(self.mod_period_var.get())
        parameter_list.append(self.mod_ratio_var.get())
        parameter_list.append(self.mod_ampl_var.get())
        parameter_list.append(self.mod_offset1_var.get())
        parameter_list.append(self.mod_offset2_var.get())
        parameter_list.append(self.mod_rand_ampl_var.get())
        # ----- random function parameters
        parameter_list.append(self.rand_check_var.get())
        parameter_list.append(self.rand_starttime_check_var.get())
        # # --- add real True/False selection here later
        parameter_table.append(parameter_names)
        parameter_table.append(parameter_list)

        return parameter_table

    def chk_motor_btn_and_gain(self, event=None):
        mot_real = 0
        for mot in range(8):
            if mot % 2 == 0:
                mot_real = mot + 1
            elif mot % 2 == 1:
                mot_real = mot - 1
            status = self.motor_check_varlist[mot_real].get()
            if status:
                self.motor_gain_entr_list[mot].config(state=tk.NORMAL)
            elif not status:
                self.motor_gain_entr_list[mot].config(state=tk.DISABLED)
            status_mod = self.mod_check_var.get()
            status_rand = self.rand_check_var.get()
            if status_mod:
                self.set_mod('NORMAL')

            elif not status_mod:
                self.set_mod('DISABLED')

    def set_mod(self, state):
        if state == 'NORMAL':
            self.mod_check_var.set(True)
            self.mod_lbl_period.config(state=tk.NORMAL)
            self.mod_entr_period.config(state=tk.NORMAL)
            self.mod_lbl_ratio.config(state=tk.NORMAL)
            self.mod_entr_ratio.config(state=tk.NORMAL)
            self.mod_lbl_ampl.config(state=tk.NORMAL)
            self.mod_entr_ampl.config(state=tk.NORMAL)
            self.mod_lbl_offset1.config(state=tk.NORMAL)
            self.mod_entr_offset1.config(state=tk.NORMAL)
            self.mod_lbl_offset2.config(state=tk.NORMAL)
            self.mod_entr_offset2.config(state=tk.NORMAL)
            self.mod_lbl_rand_ampl.config(state=tk.NORMAL)
            self.mod_entr_rand_ampl.config(state=tk.NORMAL)
            self.rand_check_btn.config(state=tk.NORMAL)
            self.rand_starttime_check_btn.config(state=tk.NORMAL)

        elif state == 'DISABLED':
            self.mod_check_var.set(False)
            self.mod_lbl_period.config(state=tk.DISABLED)
            self.mod_entr_period.config(state=tk.DISABLED)
            self.mod_lbl_ratio.config(state=tk.DISABLED)
            self.mod_entr_ratio.config(state=tk.DISABLED)
            self.mod_lbl_ampl.config(state=tk.DISABLED)
            self.mod_entr_ampl.config(state=tk.DISABLED)
            self.mod_lbl_offset1.config(state=tk.DISABLED)
            self.mod_entr_offset1.config(state=tk.DISABLED)
            self.mod_lbl_offset2.config(state=tk.DISABLED)
            self.mod_entr_offset2.config(state=tk.DISABLED)
            self.mod_lbl_rand_ampl.config(state=tk.DISABLED)
            self.mod_entr_rand_ampl.config(state=tk.DISABLED)
            self.rand_check_btn.config(state=tk.DISABLED)
            self.rand_starttime_check_btn.config(state=tk.DISABLED)

    def set_random(self, state):
        if state == 'NORMAL':
            self.rand_check_var.set(True)
            self.mod_lbl_period.config(state=tk.NORMAL)
            self.mod_entr_period.config(state=tk.NORMAL)
            self.mod_lbl_ratio.config(state=tk.NORMAL)
            self.mod_entr_ratio.config(state=tk.NORMAL)
            self.mod_lbl_ampl.config(state=tk.NORMAL)
            self.mod_entr_ampl.config(state=tk.NORMAL)
            self.mod_check_btn.config(state=tk.DISABLED)
        elif state == 'DISABLED':
            self.rand_check_var.set(False)
            self.mod_lbl_period.config(state=tk.DISABLED)
            self.mod_entr_period.config(state=tk.DISABLED)
            self.mod_lbl_ratio.config(state=tk.DISABLED)
            self.mod_entr_ratio.config(state=tk.DISABLED)
            self.mod_lbl_ampl.config(state=tk.DISABLED)
            self.mod_entr_ampl.config(state=tk.DISABLED)
            self.mod_check_btn.config(state=tk.NORMAL)

    def callback_monFunc(self, event):
        self.load_monwin_file()
        self.combo_del_mon_par.config(value=self.del_mon_par_list)
        self.combo_del_mon_par.grid()
        self.combo_select_mon_par.config(value=self.add_mon_par_list)
        self.combo_select_mon_par.grid()

    def callback_add_monFunc(self, event):
        self.add_mon_par()
        self.combo_del_mon_par.config(value=self.del_mon_par_list)
        self.combo_del_mon_par.grid()
        self.combo_select_mon_par.config(value=self.add_mon_par_list)
        self.combo_select_mon_par.grid()

    def callback_del_monFunc(self, event):
        self.remove_mon_par()
        self.combo_del_mon_par.config(value=self.del_mon_par_list)
        self.combo_del_mon_par.grid()
        self.combo_select_mon_par.config(value=self.add_mon_par_list)
        self.combo_select_mon_par.grid()

    def callback_profileFunc(self, event):
        self.load_profwin_file()

    def callback_edit_profFunc(self, event):
        self.prof_edit_or_del = True
        self.combo_select_profile.config(state=tk.DISABLED)
        self.combo_select_prof_par.config(state=tk.DISABLED)
        self.combo_del_prof_par.config(state=tk.DISABLED)
        self.mod_check_var.set(False)
        self.edit_remove_prof_para()
        self.chk_motor_btn_and_gain()

    def callback_add_profFunc(self, event):
        self.prof_edit_or_del = False
        self.mod_check_var.set(False)
        self.combo_del_prof_par.config(state=tk.DISABLED)
        self.edit_remove_prof_para()

    def update_add_mon_par_list(self):
        del_list = []
        self.add_mon_par_list.clear()
        no_all_row = len(self.all_parameters_list)
        for cell in range(no_all_row):
            self.add_mon_par_list.append(self.all_parameters_list[cell])
        no_del_rows = len(self.del_mon_par_list)
        for row in range(no_del_rows):
            par_del_temp = self.del_mon_par_list[row]
            no_add_rows = len(self.add_mon_par_list)
            for row2 in range(no_add_rows):
                par_add_temp = self.add_mon_par_list[row2]
                if par_del_temp == par_add_temp:
                    del_list.append(row2)
            try:
                for cell in range(len(del_list)):
                    self.add_mon_par_list.pop(del_list[cell])
                del_list.clear()
            except IndexError:
                pass
            try:
                index = self.add_mon_par_list[0]
            except IndexError:
                self.add_mon_par_list.append('-')

    def update_new_prof_parlist(self):
        del_list = []
        self.new_prof_param_list.clear()
        no_all_row = len(self.all_parameters_list)
        for cell in range(no_all_row):
            self.new_prof_param_list.append(self.all_parameters_list[cell])
        no_prof_rows = len(self.profile_param_names)
        for row2 in range(no_prof_rows):
            prof_par_temp = self.profile_param_names[row2]
            no_new_prof_rows = len(self.new_prof_param_list)
            for row in range(no_new_prof_rows):
                new_prof_par_temp = self.new_prof_param_list[row]
                if new_prof_par_temp == prof_par_temp:
                    del_list.append(row)
            for cell in range(len(del_list)):
                self.new_prof_param_list.pop(del_list[cell])
            del_list.clear()

    def prof_ok(self):
        index = self.combo_del_prof_par.current()
        if not self.prof_edit_or_del:
            param_founded = False
            # move parameter from add list to edit/remove list
            str_temp = self.combo_select_prof_par.get()
            # # -- add parameter to edit_del namelist
            no_rows_new = len(self.new_prof_param_list)
            index2 = []
            for row in range(no_rows_new):
                if str_temp == self.new_prof_param_list[row]:
                    index2.append(row)
                    param_founded = True
            if param_founded:
                for cell in range(len(index2)):
                    str_temp = self.new_prof_param_list[index2[cell]]
                    self.new_prof_param_list.pop(index2[cell])
                param_founded = False
            #  create new list line
            temp_list = []
            no_columns = len(self.profile_parameter_list[0])
            for col in range(no_columns):
                temp_list.append('')
            self.profile_parameter_list.append(temp_list)
            #  set index to last line
            index = len(self.profile_parameter_list) - 2
            #  add parameter name to list
            self.profile_parameter_list[index + 1][0] = self.profile_parameter.get()
        no_columns = len(self.edit_profile_var_list)
        for col in range(no_columns):
            value = self.edit_profile_var_list[col].get()
            self.profile_parameter_list[index + 1][col + 1] = value
        str_motor = self.motor_checkboxes_to_str()
        self.profile_parameter_list[index + 1][no_columns + 1] = str_motor
        #  -----   motor gains
        start_col = no_columns + 2
        for mot in range(8):
            self.profile_parameter_list[index + 1][start_col + mot] = self.motor_gain_entr_varlist[mot].get()
        start_col = start_col + 8
        # mod_enabled
        self.profile_parameter_list[index + 1][start_col] = str(self.mod_check_var.get())
        self.profile_parameter_list[index + 1][start_col+1] = self.mod_period_var.get()
        self.profile_parameter_list[index + 1][start_col + 2] = self.mod_ratio_var.get()
        self.profile_parameter_list[index + 1][start_col + 3] = self.mod_ampl_var.get()
        self.profile_parameter_list[index + 1][start_col + 4] = self.mod_offset1_var.get()
        self.profile_parameter_list[index + 1][start_col + 5] = self.mod_offset2_var.get()
        self.profile_parameter_list[index + 1][start_col + 6] = self.mod_rand_ampl_var.get()
        self.profile_parameter_list[index + 1][start_col + 7] = str(self.rand_check_var.get())
        self.profile_parameter_list[index + 1][start_col + 8] = str(self.rand_starttime_check_var.get())
        self.update_profwin()
        self.prof_edit_frame.grid_remove()
        self.prof_edit_or_del = False
        self.combo_select_profile.config(state=tk.NORMAL)
        self.combo_select_prof_par.config(state=tk.NORMAL)
        self.combo_del_prof_par.config(state=tk.NORMAL)

    def prof_del(self):
        index = self.combo_del_prof_par.current()
        str_temp = self.combo_del_prof_par.get()
        self.new_prof_param_list.append(str_temp)
        self.profile_parameter_list.pop(index + 1)
        self.profile_param_names.pop(index)
        self.update_profwin()
        self.prof_edit_frame.grid_remove()
        self.combo_select_profile.config(state=tk.NORMAL)
        self.combo_select_prof_par.config(state=tk.NORMAL)
        self.combo_del_prof_par.config(state=tk.NORMAL)

    def motor_checkboxes_to_str(self):
        motor_list = []
        for mot in range(8):
            motor_list.append('')
        str_motor = ''
        for mot in range(8):
            self.motor_check_btn_list[mot].config(state=tk.NORMAL)
            status = self.motor_check_varlist[mot].get()
            if status == 1:
                if mot % 2 == 0:
                    mot = mot + 1
                elif mot % 2 == 1:
                    mot = mot - 1
                motor_list[mot] = 'M' + str(mot)
        for mot in range(8):
            str_motor = str_motor + motor_list[mot]
        return str_motor

    def add_mon_par(self):
        new_parameter = self.combo_select_mon_par.get()
        index = self.combo_select_mon_par.current()
        self.add_mon_par_list.pop(index)
        self.del_mon_par_list.append(new_parameter)
        self.update_monwin(self.del_mon_par_list)

    def remove_mon_par(self):
        index = self.combo_del_mon_par.current()
        str_temp = self.combo_del_mon_par.get()
        self.add_mon_par_list.append(str_temp)
        self.monwin_parameter_list.pop(index)
        self.update_monwin(self.monwin_parameter_list)
        self.combo_select_mon_par.config(value=self.add_mon_par_list)
        self.combo_select_mon_par.grid()

    def edit_remove_prof_para(self):
        # show profile edit frame
        self.load_selected_prof_par()
        self.prof_edit_frame.grid()

    def load_selected_prof_par(self):
        index = 0
        parameter = ''
        if self.prof_edit_or_del:
            index = self.combo_del_prof_par.current()
            # update parameter name
            parameter = self.combo_del_prof_par.get()
        elif not self.prof_edit_or_del:
            index = self.combo_select_prof_par.current()
            parameter = self.combo_select_prof_par.get()
            self.profile_param_names.append(parameter)
        self.profile_parameter.set(parameter)
        no_columns = len(self.edit_profile_var_list)
        value_list =['1', '0.0', '0.01', '10', '20']
        value_len = len(value_list)
        for col in range(value_len, no_columns):
            value_list.append('0')
        for col in range(no_columns):
            if self.prof_edit_or_del:
                value_list[col] = self.profile_parameter_list[index + 1][col + 1]
            self.edit_profile_var_list[col].set(value_list[col])
        if not self.prof_edit_or_del:
            self.mod_check_var.set('0')
            self.combo_select_profile.config(state=tk.DISABLED)
            self.combo_select_prof_par.config(state=tk.DISABLED)
        # update motor checkboxes
        motor_str = ''
        motor_list = 0
        if self.prof_edit_or_del:
            motor_str = self.profile_parameter_list[index + 1][no_columns + 1]
        no_motors = len(motor_str)
        if no_motors > 0:
            motor_list = list(motor_str.split('M'))
            motor_list.pop(0)
        for moto in range(8):
            self.motor_check_varlist[moto].set(False)
        if no_motors > 0:
            for mot in motor_list:
                mot_index = int(mot)
                if mot_index % 2 == 0:
                    mot_index = mot_index + 1
                elif mot_index % 2 == 1:
                    mot_index = mot_index - 1
                self.motor_check_varlist[mot_index].set(True)
        #  -- update motor gains
        start_col = no_columns + 2
        for mot in range(8):
            if self.prof_edit_or_del:
                self.motor_gain_entr_varlist[mot].set(self.profile_parameter_list[index+1][start_col+mot])
            if not self.prof_edit_or_del:
                self.motor_gain_entr_varlist[mot].set('1.0')
        start_col = start_col + 8
        # modulator selection
        if self.prof_edit_or_del:
            self.mod_check_var.set(self.profile_parameter_list[index+1][start_col])
            self.mod_period_var.set(self.profile_parameter_list[index+1][start_col+1])
            self.mod_ratio_var.set(self.profile_parameter_list[index + 1][start_col + 2])
            self.mod_ampl_var.set(self.profile_parameter_list[index + 1][start_col + 3])
            self.mod_offset1_var.set(self.profile_parameter_list[index + 1][start_col + 4])
            self.mod_offset2_var.set(self.profile_parameter_list[index + 1][start_col + 5])
            self.mod_rand_ampl_var.set(self.profile_parameter_list[index + 1][start_col + 6])
            self.rand_check_var.set(self.profile_parameter_list[index + 1][start_col + 7])
            self.rand_starttime_check_var.set(self.profile_parameter_list[index + 1][start_col + 8])
            # add rand_start_time value here
        if not self.prof_edit_or_del:
            self.mod_check_var.set(False)
            self.mod_period_var.set('0.0')
            self.mod_ratio_var.set('0.0')
            self.mod_ampl_var.set('0.0')
            self.mod_offset1_var.set('0.0')
            self.mod_offset2_var.set('0.0')
            self.mod_rand_ampl_var.set('0.0')
            self.rand_check_var.set(False)
            self.rand_starttime_check_var.set(False)

    def load_profwin_file(self):
        profile_list = []
        filename = self.combo_select_profile.get()
        name_list = self.profile.load_window_new(filename)
        for line in range(len(name_list)):
            name_temp = name_list[line]
            line_table = list(name_temp.split(','))
            profile_list.append(line_table)
        self.profile_parameter_list = profile_list
        no_rows = len(profile_list)
        self.profile_param_names.clear()
        for row in range(1, no_rows):
            self.profile_param_names.append(profile_list[row][0])
        self.update_new_prof_parlist()
        self.update_profwin()

    def load_monwin_file(self):
        filename = self.combo_select_monwin.get()
        name_list = self.profile.load_window_new(filename)
        self.del_mon_par_list = name_list
        self.monwin_parameter_list = name_list
        self.update_monwin(name_list)
        self.update_add_mon_par_list()

    def update_monwin(self, name_list):
        self.text_monwin.config(state=tk.NORMAL)
        self.text_monwin.delete('1.0', tk.END)
        str_temp = ''
        for line in range(len(name_list)):
            str_temp = str_temp + name_list[line] + '\n'
        self.text_monwin.insert(tk.INSERT, str_temp)
        self.text_monwin.config(state=tk.DISABLED)
        try:
            self.combo_del_mon_par.config(values=name_list)
            self.text_monwin.config(height=len(name_list))
        except AttributeError:
            pass

    def load_all_parameters(self):
        datadict = {}
        datadict = udp.CondorUDP.condor_udp_data_arrays(self.master)
        parameter_list = list(datadict.keys())
        return parameter_list

    def update_profwin(self):
        no_rows = len(self.profile_parameter_list)
        # no_columns = len(self.profile_parameter_list[0])
        no_columns = len(self.text_prof_param)
        for col in range(no_columns):
            self.text_prof_param[col].config(state=tk.NORMAL)
            self.text_prof_param[col].delete('1.0', tk.END)
            str_temp = ''
            for row in range(1, no_rows):
                str_temp = str_temp + self.profile_parameter_list[row][col] + '\n'
            str_temp = str_temp[:-1]
            self.text_prof_param[col].insert(tk.INSERT, str_temp)
            self.text_prof_param[col].config(state=tk.DISABLED)
            try:
                self.text_prof_param[col].config(height=(len(self.profile_parameter_list) - 1))
            except AttributeError:
                pass
        self.combo_select_prof_par.config(values=self.new_prof_param_list)
        self.combo_select_prof_par.grid()
        self.combo_del_prof_par.config(values=self.profile_param_names)
        self.combo_del_prof_par.grid()

    def get_proffile_list(self):
        self.proffile_list.clear()
        for file in os.listdir():
            data = os.path.splitext(file)[1]
            if os.path.splitext(file)[1] == '.prof':
                self.proffile_list.append(file)

    def get_monfile_list(self):
        self.monfile_list.clear()
        for file in os.listdir():
            if os.path.splitext(file)[1] == '.mon':
                self.monfile_list.append(file)

    def save_prof(self, filee=None):
        filename = ''
        ok_or_not = False
        if not self.save_as_or_not:
            filename = self.combo_select_profile.get()
            # ---- confirm overwrite -----------
            ok_or_not = messagebox.askokcancel(parent=self, title=filename, message='Do you like to update this file?')
        elif self.save_as_or_not:
            filename = filee
            ok_or_not = True
        if ok_or_not:
            data_list = self.profile_parameter_list[1:]
            param_list = self.profile_parameter_list[0]
            self.profile.save_profile_file(param_list, data_list, filename)
            # -- update prof file list --
            self.get_proffile_list()
            # --- refresh comboboxes also --
            self.combo_select_profile.config(values=self.proffile_list)
            self.combo_select_profile.grid()
        self.save_as_or_not = False

    def save_as_prof(self):
        this_dir = os.getcwd()
        directory = filedialog.asksaveasfile(parent=self, initialdir=this_dir, filetypes=[('Profile', '*.prof')],
                                             defaultextension='.prof')
        if not directory == None:
            filename = os.path.basename(directory.name)
            self.save_as_or_not = True
            self.save_prof(filename)
        elif directory == None:
            self.save_as_or_not = False


    def save_mon(self, filee=None):
        filename = ''
        ok_or_not = False
        if not self.save_as_or_not:
            filename = self.combo_select_monwin.get()
            # ---- confirm overwrite -----------
            ok_or_not = messagebox.askokcancel(parent=self, title=filename, message='Do you like to update this file?')
        elif self.save_as_or_not:
            filename = filee
            ok_or_not = True
        if ok_or_not:
            data_list = self.monwin_parameter_list
            self.profile.save_monitor_window(data_list, filename)
            # -- update mon file list --
            self.get_monfile_list()
            # --- refresh combobox also --
            self.combo_select_monwin.config(values=self.monfile_list)
            self.combo_select_monwin.grid()
        self.save_as_or_not = False

    def save_as_mon(self):
        this_dir = os.getcwd()
        directory = filedialog.asksaveasfile(parent=self, initialdir=this_dir, filetypes=[('Monitoring', '*.mon')],
                                             defaultextension='.mon')
        if not directory == None:
            filename = os.path.basename(directory.name)
            self.save_as_or_not = True
            self.save_mon(filename)
        elif directory == None:
            self.save_as_or_not = False

    def del_monfile(self):
        filename = self.combo_select_monwin.get()
        # ---- confirm deleting !!
        ok_or_not = messagebox.askokcancel(parent=self, title=filename, message='Do you like to delete this file?')
        if ok_or_not:
            os.remove(filename)
            # -- update mon file list --
            self.get_monfile_list()
            # --- refresh combobox also --
            self.combo_select_monwin.config(values=self.monfile_list)
            self.combo_select_monwin.current(0)
            self.combo_select_monwin.grid()
            self.combo_select_monwin.focus()

    def del_proffile(self):
        ok_or_not = False
        filename = self.combo_select_profile.get()
        # ---- confirm deleting !!
        ok_or_not = messagebox.askokcancel(parent=self, title=filename, message='Do you like to delete this file?')
        if ok_or_not:
            os.remove(filename)
            # -- update prof file list --
            self.get_proffile_list()
            # --- refresh comboboxes also --
            self.combo_select_profile.config(values=self.proffile_list)
            self.combo_select_profile.current(0)
            self.combo_select_profile.grid()
            self.combo_select_profile.focus()

    def update_default_ini(self, mot_calib_table=None):
        filename_table = self.profile.read_init_file('default.ini')
        filename_table[0][1] = self.combo_select_monwin.get()
        filename_table[1][1] = self.combo_select_profile.get()
        calibration_table = []
        if mot_calib_table == None:
            calibration_table = self.motor_calibration_table
        else:
            calibration_table = mot_calib_table
        mot_calib_str = '['
        for cell in calibration_table:
            mot_calib_str = mot_calib_str + str(cell) + ','
        mot_calib_str = mot_calib_str[:-1]
        mot_calib_str = mot_calib_str + ']'
        if len(filename_table) > 3:
            filename_table[3][1] = mot_calib_str
        elif len(filename_table) == 3:
            new_list = ['motor_calibration_gains', mot_calib_str]
            filename_table.append(new_list)
        file_list = []
        no_rows = len(filename_table)
        for row in range(no_rows):
            str_temp = filename_table[row][0] + '=' + filename_table[row][1]
            file_list.append(str_temp)
        self.profile.save_default_ini(file_list, 'default.ini')

    def __del__(self):
        pass

    def client_exit(self):
        self.update_default_ini()
        port_name, baudrate, comport = ffcom.load_ff_port_data()
        self.ser.comport = comport
        self.ser.baud = baudrate
        self.lock.acquire()
        self.q_data.put(True)
        self.lock.release()
        self.master.destroy()

    def window_name(self, window_name):
        self.master.title(window_name)


# --------- end of class Prof_window(tk.Frame) ------------------------------------


class Profiler:
    def __init__(self):
        self.profile_table = self.load_profile_file('default.prof')
        self.monitor_table = self.load_monitor_window('default.mon')

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

    def get_motor_calibration_table(self, filename_table):
        mot_gain_list = []
        motor_gain_str = filename_table[3][1]
        motor_gain_str = motor_gain_str[1:-1]
        mot_gain_str_list = list(motor_gain_str.split(','))
        for cell in mot_gain_str_list:
            mot_gain_list.append(float(cell))
        return mot_gain_list

    def load_monitor_window(self, load_filename):
        with open(load_filename, 'r') as filee:
            parameter_csv = csv.reader(filee)
            for row in parameter_csv:
                pass
        return row

    def load_profile_file(self, load_filename):
        data_table = []
        data_temp = self.load_window_new(load_filename)
        # check if new rows exist
        str_parameter_list = list(data_temp[0].split(','))
        if not 'gain_M0' in str_parameter_list:
            data_temp = self.add_new_columns_to_profilefile(load_filename)
        rows = len(data_temp)
        for row in range(rows):
            line_table = list(data_temp[row].split(','))
            data_table.append(line_table)
        return data_table

    def add_new_columns_to_profilefile(self, load_filename):
        data_table = []
        parameter_names = []
        str_list = []
        data_temp = self.load_window_new(load_filename)
        rows = len(data_temp)
        for row in range(rows):
            line_table = list(data_temp[row].split(','))
            data_table.append(line_table)
        parameter_names = list(data_temp[0].split(','))
        for col in range(8):
            parameter_names.append(('gain_M' + str(col)))
        parameter_names.append('mod_enabled')
        parameter_names.append('period')
        parameter_names.append('ratio')
        parameter_names.append('ampl')
        parameter_names.append('offset1')
        parameter_names.append('offset2')
        parameter_names.append('rand_ampl')
        parameter_names.append('rand_separately')
        parameter_names.append('rand_start_enabled')
        no_cols_old = len(data_table[0])
        no_cols_new = len(parameter_names)
        data_table[0] = parameter_names
        for row in range(1, len(data_table)):
            # set motor gains to 1.0
            for col in range(8):
                data_table[row].append('1.0')
            for col in range(8, (no_cols_new-no_cols_old)):
                data_table[row].append('0')
        len_check = len(data_table[5])
        # save data to load_file
        for row in range(len(data_table)):
            str_temp = ''
            str_temp = str(data_table[row][0])
            for col in range(1, len(data_table[row])):
                str_temp = str_temp + ',' + str(data_table[row][col])
            str_list.append(str_temp)
        try:
            with open(load_filename, 'w') as csvfile:
                for row in str_list:
                    csvfile.writelines("%s\n" % row)
        except IOError:
            print("I/O error")
        return str_list

    def load_window_new(self, load_filename):
        name_table = []
        try:
            with open(load_filename, 'r') as csv_file:
                filecontent = csv_file.readlines()
                for line in filecontent:
                    current_line = line[:-1]
                    name_table.append(current_line)
        except IOError:
            print("I/O error")
        return name_table

    def save_monitor_window(self, parameter_list, save_filename):
        try:
            with open(save_filename, 'w') as new_file:
                for row in parameter_list:
                    new_file.writelines("%s\n" % row)
        except IOError:
            print("I/O error")

    def save_profile_file(self, parameter_list, profile_list, save_profile):
        str_temp = ''
        for col in range(len(parameter_list) - 1):
            str_temp = str_temp + str(parameter_list[col]) + ','
        str_temp = str_temp + parameter_list[len(parameter_list)-1] +'\n'
        try:
            with open(save_profile, 'w') as csvfile:
                csvfile.writelines(str_temp)
                for row in range(len(profile_list)):
                    str_temp = ''
                    for col in range(len(profile_list[0])-1):
                        str_temp = str_temp + str(profile_list[row][col]) + ','
                    str_temp = str_temp + str(profile_list[row][len(profile_list[0])-1]) + '\n'
                    csvfile.writelines(str_temp)
        except IOError:
            print("I/O error")

    def save_default_ini(self, file_list, save_filename):
        try:
            with open(save_filename, 'w') as new_file:
                for row in file_list:
                    new_file.writelines("%s\n" % row)
        except IOError:
            print("I/O error")


# ---- this main function is just for testing purposes -------------
if __name__ == '__main__':
    q_data = queue.Queue()
    lock = threading.Lock()
    root = tk.Tk()
    ser = ffcom.SerialPort()
    app = Prof_window(root, q_data, lock, ser)
    app.window_name('Profile window')
    root.mainloop()
