import tkinter as tk
import csv
import Shaker_comport as ffcom
from tkinter import ttk
import Condor2_udp_com as udp
import os
from tkinter import messagebox
from tkinter import filedialog


class Prof_window(tk.Frame):
    def __init__(self, master, q_data, lock):
        tk.Frame.__init__(self, master)
        # tk.Toplevel.__init__(self, master)
        # self.frame = tk.Frame(self)
        #  ------------------
        self.master = master
        # self.master.ser = ser
        # self.init_window()
        self.lock = lock
        self.q_data = q_data
        status =  True
        status = self.q_data.empty
        self. lock.acquire()
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

        # --- get and read default.init file ----------
        if not os.path.isfile('default.ini'):   # --- this function is not done yet (27.12.2019)
            pass
        self.filename_table = self.read_init_file('default.ini')
        self.all_parameters_list = self.load_all_parameters()
        self.profile_parameter_list = self.profile.load_profile_file(self.filename_table[1][1])

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
        file.add_command(label="Exit", command=self.client_exit)
        # added "file" to our menu
        menu.add_cascade(label="File", menu=file)
        # create the file object)
        edit = tk.Menu(menu, tearoff=False)
        # adds a command to the menu option, calling it exit, and the
        # command it runs on event is client_exit
        edit.add_command(label="Undo")
        # added "Edit" to our menu
        menu.add_cascade(label="Edit", menu=edit)

        self.mon_frame = tk.Frame(self)
        self.mon_frame.grid(column=0, row=0, rowspan=8, padx=5, pady=5)
        self.profile_frame = tk.Frame(self)
        self.profile_frame.grid(column=2, row=0, padx=5, pady=5, sticky='N')

        # ---- add label to frame -------
        lbl_select_monwin_file = tk.Label(self.mon_frame, text='Select monitor parameters')
        lbl_select_monwin_file.grid(column=0, row=0, columnspan=2, sticky='W')
        # ------ add Combobox to frame -------
        # monwin_table = ['all_parameters.ini', 'new.mon']
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
        no_columns = len(prof_param_name_list)
        no_rows = len(self.profile_parameter_list)
        start_column = 0
        start_row = 5
        width = [25, 10, 10, 10, 10, 10, 17]
        self.lbl_prof_param_names = []
        self.text_prof_param = []
        for col in range(0, no_columns):
            self.lbl_prof_param_names.append(tk.Label(self.profile_frame, text=prof_param_name_list[col],
                                                      width=width[col]))
            self.lbl_prof_param_names[col].grid(column=start_column + col, row=start_row, sticky='W', padx=2, pady=2)
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
        self.prof_edit_frame.grid(column=2, row=1, sticky='N', padx=5, pady=5)
        lbl_edit_prof_names = []
        #  create parameter name labels
        for col in range(no_columns - 1):
            lbl_edit_prof_names.append(tk.Label(self.prof_edit_frame, text=prof_param_name_list[col],
                                                width=width[col]))
            lbl_edit_prof_names[col].grid(column=col, row=0, sticky='W', padx=2, pady=2)
        # create edit list row
        self.profile_parameter = tk.StringVar()
        self.lbl_profile_parameter = tk.Label(self.prof_edit_frame, textvariable=self.profile_parameter,
                                              width=width[0])
        self.lbl_profile_parameter.grid(column=0, row=1, sticky='W', padx=2, pady=2)
        # --- create entry cells ---
        width = [25, 15, 15, 15, 15, 15, 8]
        self.edit_profile_entries = []
        self.edit_profile_var_list = []
        for col in range(no_columns - 2):
            self.edit_profile_var_list.append(tk.StringVar())
            self.edit_profile_entries.append(tk.Entry(self.prof_edit_frame,
                                                      textvariable=self.edit_profile_var_list[col],
                                                      width=width[col + 1]))
            self.edit_profile_entries[col].grid(column=col + 1, row=1, sticky='W', padx=2, pady=2)
        # -- create motor selection checklists
        lbl_motor = tk.Label(self.prof_edit_frame, text=' Motors', width=width[no_columns - 1])
        lbl_motor.grid(column=(no_columns - 1), row=0, columnspan=2, sticky='W', padx=2, pady=2)
        self.motor_check_btn_list = []
        self.motor_check_varlist = []
        str_help = ''
        for mot in range(8):
            self.motor_check_varlist.append(tk.IntVar())
            if mot % 2 == 0:
                str_help = str(mot + 1)
            elif mot % 2 == 1:
                str_help = str(mot - 1)
            self.motor_check_btn_list.append(tk.Checkbutton(self.prof_edit_frame, text=('M' + str_help),
                                                            variable=self.motor_check_varlist[mot], onvalue=True,
                                                            offvalue=False, height=1, width=4))
            self.motor_check_btn_list[mot].grid(column=(no_columns + mot % 2), row=(1 + int(mot / 2)), sticky='W')
        # ------- Add Ok and Remove buttons
        self.prof_Ok_btn = tk.Button(self.prof_edit_frame, text='Ok', width=4, command=self.prof_ok)
        self.prof_Ok_btn.grid(column=4, row=4, sticky='E', padx=2, pady=2)
        self.prof_del_btn = tk.Button(self.prof_edit_frame, text='Remove', width=8, command=self.prof_del)
        self.prof_del_btn.grid(column=5, row=4, sticky='W', padx=2, pady=2)
        # hide this grid as default
        self.prof_edit_frame.grid_remove()
    # ------------- end of class Prof_window(tk.Frame) init ------------------------------------------

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
        self.edit_remove_prof_para()

    def callback_add_profFunc(self, event):
        self.prof_edit_or_del = False
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
        no_columns = len(self.profile_parameter_list[0])
        for col in range(no_columns - 2):
            value = self.edit_profile_var_list[col].get()
            self.profile_parameter_list[index + 1][col + 1] = value
        str_motor = self.motor_checkboxes_to_str()
        self.profile_parameter_list[index + 1][no_columns - 1] = str_motor
        self.update_profwin()
        self.prof_edit_frame.grid_remove()
        self.prof_edit_or_del = False

    def prof_del(self):
        index = self.combo_del_prof_par.current()
        str_temp = self.combo_del_prof_par.get()
        self.new_prof_param_list.append(str_temp)
        self.profile_parameter_list.pop(index + 1)
        self.profile_param_names.pop(index)
        self.update_profwin()
        self.prof_edit_frame.grid_remove()

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
        no_columns = len(self.profile_parameter_list[0])
        for col in range(no_columns - 2):
            value = '0'
            if self.prof_edit_or_del:
                value = self.profile_parameter_list[index + 1][col + 1]
            self.edit_profile_var_list[col].set(value)
        # update motor checkboxes
        motor_str = ''
        motor_list = 0
        if self.prof_edit_or_del:
            motor_str = self.profile_parameter_list[index + 1][no_columns - 1]
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
        datadict = udp.CondorUDP.condor_udp_data_arrays(self.master)
        parameter_list = list(datadict.keys())
        return parameter_list

    def update_profwin(self):
        no_rows = len(self.profile_parameter_list)
        no_columns = len(self.profile_parameter_list[0])
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
            ok_or_not = messagebox.askokcancel(title=filename, message='Do you like to update this file?')
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
        directory = filedialog.asksaveasfile(initialdir=this_dir, filetypes=[('Profile', '*.prof')],
                                             defaultextension='.prof')
        filename = os.path.basename(directory.name)
        self.save_as_or_not = True
        self.save_prof(filename)

    def save_mon(self, filee=None):
        filename = ''
        ok_or_not = False
        if not self.save_as_or_not:
            filename = self.combo_select_monwin.get()
            # ---- confirm overwrite -----------
            ok_or_not = messagebox.askokcancel(title=filename, message='Do you like to update this file?')
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
        directory = filedialog.asksaveasfile(initialdir=this_dir, filetypes=[('Monitoring', '*.mon')],
                                             defaultextension='.mon')
        filename = os.path.basename(directory.name)
        self.save_as_or_not = True
        self.save_mon(filename)

    def del_monfile(self):
        filename = self.combo_select_monwin.get()
        # ---- confirm deleting !!
        ok_or_not = messagebox.askokcancel(title=filename, message='Do you like to delete this file?')
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
        ok_or_not = messagebox.askokcancel(title=filename, message='Do you like to delete this file?')
        if ok_or_not:
            os.remove(filename)
            # -- update prof file list --
            self.get_proffile_list()
            # --- refresh comboboxes also --
            self.combo_select_profile.config(values=self.proffile_list)
            self.combo_select_profile.current(0)
            self.combo_select_profile.grid()
            self.combo_select_profile.focus()

    def update_default_ini(self):
        filename_table = self.read_init_file('default.ini')
        filename_table[0][1] = self.combo_select_monwin.get()
        filename_table[1][1] = self.combo_select_profile.get()
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
        self.lock.acquire()
        self.q_data.put(True)
        self.lock.release()
        self.master.destroy()

    def window_name(self, window_name):
        self.master.title(window_name)

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
# --------- end of class Prof_window(tk.Frame) ------------------------------------


class Profiler:
    def __init__(self):
        self.profile_table = self.load_profile_file('default.prof')
        self.monitor_table = self.load_monitor_window('default.mon')

    def load_monitor_window(self, load_filename):
        with open(load_filename, 'r') as filee:
            parameter_csv = csv.reader(filee)
            for row in parameter_csv:
                pass
        return row

    def load_profile_file(self, load_filename):
        data_table = []
        data_temp = self.load_window_new(load_filename)
        rows = len(data_temp)
        for row in range(rows):
            line_table = list(data_temp[row].split(','))
            data_table.append(line_table)
        return data_table

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
                # str_temp = ''
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


if __name__ == '__main__':
    root = tk.Tk()
    # root.geometry("1350x750+500+300")
    app = Prof_window(root)
    app.window_name('Profile window')
    root.mainloop()
