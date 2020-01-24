import tkinter as tk
from tkinter import ttk
import Shaker_comport as ffcom
import Condor2_profile as ffprof
import os


class FF_window(tk.Frame):
    def __init__(self, master, ser):
        tk.Frame.__init__(self, master)
        self.master = master
        self.master.ser = ser
        self.var_1 = tk.StringVar()
        self.m0_btn_str = tk.StringVar()
        self.m1_btn_str = tk.StringVar()
        self.m2_btn_str = tk.StringVar()
        self.m3_btn_str = tk.StringVar()
        self.m4_btn_str = tk.StringVar()
        self.m5_btn_str = tk.StringVar()
        self.m6_btn_str = tk.StringVar()
        self.m7_btn_str = tk.StringVar()
        self.M0_activated = False
        self.M1_activated = False
        self.M2_activated = False
        self.M3_activated = False
        self.M4_activated = False
        self.M5_activated = False
        self.M6_activated = False
        self.M7_activated = False
        self.FF_active = False

        # changing the title of our master widget
        self.master.title("default")

        # allowing the widget to take the full space of the root window
        self.pack()
        self.place(relx=0.01, rely=0.01, relwidth=0.95, relheight=0.95)

        # creating a menu instance
        menu = tk.Menu(self.master)
        self.master.config(menu=menu)

        # create the file object)
        file = tk.Menu(menu, tearoff=False)

        # adds a command to the menu option, calling it exit, and the
        # command it runs on event is client_exit
        file.add_command(label="Save setups", command=self.save_setups)
        file.add_command(label="Exit", command=self.client_exit)

        # added "file" to our menu
        menu.add_cascade(label="File", menu=file)

        # add buttons and labels
        lbl_set_baudrate = tk.Label(master, text='Set baudrate:')
        lbl_set_baudrate.place(relx=0.02, rely=0.0)
        self.entry_baudrate = tk.StringVar()
        entr_set_baudrate = tk.Entry(master, textvariable=self.entry_baudrate, width=6)
        entr_set_baudrate.place(relx=0.12, rely=0.0)
        self.entry_baudrate.set(115200)

        self.com_port_name, self.com_ports = ffcom.list_COM_ports()
        lbl_select_COM_port = tk.Label(master, text='Select COM port:')
        lbl_select_COM_port.place(relx=0.0, rely=0.2)
        self.str_temp = tk.StringVar()
        self.cb_COM_ports = ttk.Combobox(master, value=self.com_port_name, textvariable=self.str_temp, width=25)
        self.cb_COM_ports.place(relx=0.12, rely=0.2)
        self.str_temp.set(self.com_port_name[0])

        self.load_ff_port_info()

        button_check_com = tk.Button(master, text='Check COM port', command=self.get_ff_com_port)
        button_check_com.place(relx=0.0, rely=0.4)

        label1 = tk.Label(master, textvariable=self.var_1)
        label1.place(relx=0.15, rely=0.4)

        btn_stop_all_motors = tk.Button(master, text='Stop all motors', command=self.stop_motors)
        btn_stop_all_motors.place(relx=0.0, rely=0.72)

        # create motor gain entries here
        self.motor_calib_list = []
        self.motor_gain_entry = []
        self.motor_entry_var = []
        width = [5, 5, 5, 5, 5, 5, 5, 5]
        for mot in range(8):
            self.motor_entry_var.append(tk.StringVar())
            self.motor_gain_entry.append(tk.Entry(master, textvariable=self.motor_entry_var[mot], width=width[mot],
                                                  justify='center'))
            self.motor_calib_list.append(1.0)

        # -- motor gain entry label
        lbl_motor_gains = tk.Label(master, text='Motor gain calibration entries:')
        lbl_motor_gains.place(relx=0.14, rely=0.8)

        # Motor 0 button, slider and gain entry
        self.button_M0 = tk.Button(master, textvariable=self.m0_btn_str, command=self.test_m0)
        self.button_M0.place(relx=0.33, rely=0.0)
        self.m0_btn_str.set('Start M0')
        self.slider_m0 = tk.Scale(master, label='M0',from_=100, to=0, resolution=1, command=self.run_m)
        self.slider_m0.place(relx=0.31, rely=0.22)
        self.slider_m0.set(0)
        self.motor_gain_entry[0].place(relx=0.34, rely=0.8)
        self.motor_entry_var[0].set(self.motor_calib_list[0])

        # Motor 1 button, slider and gain entry
        self.button_M1 = tk.Button(master, textvariable=self.m1_btn_str, command=self.test_m1)
        self.button_M1.place(relx=0.41, rely=0.0)
        self.m1_btn_str.set('Start M1')
        self.slider_m1 = tk.Scale(master, label='M1', from_=100, to=0, resolution=1, command=self.run_m)
        self.slider_m1.place(relx=0.39, rely=0.22)
        self.slider_m1.set(0)
        self.motor_gain_entry[1].place(relx=0.42, rely=0.8)
        self.motor_entry_var[1].set(self.motor_calib_list[0])

        # Motor 2 button, slider and gain entry
        self.button_M2 = tk.Button(master, textvariable=self.m2_btn_str, command=self.test_m2)
        self.button_M2.place(relx=0.49, rely=0.0)
        self.m2_btn_str.set('Start M2')
        self.slider_m2 = tk.Scale(master, label='M2', from_=100, to=0, resolution=1, command=self.run_m)
        self.slider_m2.place(relx=0.47, rely=0.22)
        self.slider_m2.set(0)
        self.motor_gain_entry[2].place(relx=0.50, rely=0.8)
        self.motor_entry_var[2].set(self.motor_calib_list[0])

        # Motor 3 button, slider and gain entry
        self.button_M3 = tk.Button(master, textvariable=self.m3_btn_str, command=self.test_m3)
        self.button_M3.place(relx=0.57, rely=0.0)
        self.m3_btn_str.set('Start M3')
        self.slider_m3 = tk.Scale(master, label='M3', from_=100, to=0, resolution=1, command=self.run_m)
        self.slider_m3.place(relx=0.55, rely=0.22)
        self.slider_m3.set(0)
        self.motor_gain_entry[3].place(relx=0.58, rely=0.8)
        self.motor_entry_var[3].set(self.motor_calib_list[0])

        # Motor 4 button, slider and gain entry
        self.button_M4 = tk.Button(master, textvariable=self.m4_btn_str, command=self.test_m4)
        self.button_M4.place(relx=0.65, rely=0.0)
        self.m4_btn_str.set('Start M4')
        self.slider_m4 = tk.Scale(master, label='M4', from_=100, to=0, resolution=1, command=self.run_m)
        self.slider_m4.place(relx=0.63, rely=0.22)
        self.slider_m4.set(0)
        self.motor_gain_entry[4].place(relx=0.66, rely=0.8)
        self.motor_entry_var[4].set(self.motor_calib_list[0])

        # Motor 5 button, slider and gain entry
        self.button_M5 = tk.Button(master, textvariable=self.m5_btn_str, command=self.test_m5)
        self.button_M5.place(relx=0.73, rely=0.0)
        self.m5_btn_str.set('Start M5')
        self.slider_m5 = tk.Scale(master, label='M5', from_=100, to=0, resolution=1, command=self.run_m)
        self.slider_m5.place(relx=0.71, rely=0.22)
        self.slider_m5.set(0)
        self.motor_gain_entry[5].place(relx=0.74, rely=0.8)
        self.motor_entry_var[5].set(self.motor_calib_list[0])

        # Motor 6 button, slider and gain entry
        self.button_M6 = tk.Button(master, textvariable=self.m6_btn_str, command=self.test_m6)
        self.button_M6.place(relx=0.81, rely=0.0)
        self.m6_btn_str.set('Start M6')
        self.slider_m6 = tk.Scale(master, label='M6', from_=100, to=0, resolution=1, command=self.run_m)
        self.slider_m6.place(relx=0.79, rely=0.22)
        self.slider_m6.set(0)
        self.motor_gain_entry[6].place(relx=0.82, rely=0.8)
        self.motor_entry_var[6].set(self.motor_calib_list[0])

        # Motor 7 button, slider and gain entry
        self.button_M7 = tk.Button(master, textvariable=self.m7_btn_str, command=self.test_m7)
        self.button_M7.place(relx=0.89, rely=0.0)
        self.m7_btn_str.set('Start M7')

        self.slider_m7 = tk.Scale(master, label='M7', from_=100, to=0, resolution=1, command=self.run_m)
        self.slider_m7.place(relx=0.87, rely=0.22)
        self.slider_m7.set(0)
        self.motor_gain_entry[7].place(relx=0.90, rely=0.8)
        self.motor_entry_var[7].set(self.motor_calib_list[0])

        for mot in range(8):
            self.motor_gain_entry[mot].bind('<Return>', self.update_motor_gain_list)

    def save_setups(self):
        self.save_ff_port_info()
        # --- save self.motor_calibration list also

    def update_motor_gain_list(self, event):
        for mot in range(8):
            self.motor_calib_list[mot] = float(self.motor_entry_var[mot].get())
        self.test_motors()

    def __del__(self):
        self.master.ser.Close()

    def window_name(self, window_name):
        self.master.title(window_name)

    def client_exit(self):
        self.master.ser.Close()
        self.master.destroy()

    def get_ff_com_port(self):
        x = self.com_ports[self.cb_COM_ports.current()]
        p, com_port_founded = ffcom.get_COM_port(x)
        self.var_1.set(p)


    def load_ff_port_info(self):
        data = ffcom.load_ff_port_data()
        port_name, baudrate, comport = data
        self.entry_baudrate.set(baudrate)
        self.var_1.set(comport)
        self.str_temp.set(port_name)

    def save_ff_port_info(self):
        index = self.cb_COM_ports.current()
        x = self.com_ports[index]
        comport, com_port_founded = ffcom.get_COM_port(x)
        baudrate = self.entry_baudrate.get()
        ffcom.save_ff_port_data(self.com_port_name[index], baudrate, comport)

    def run_m(self, v):
        self.test_motors()

    def stop_motors(self):
        if self.FF_active:
            self.master.ser.Send('M00\rM10\rM20\rM30\rM40\rM50\rM60\rM70\r')
            self.master.ser.Close()
            self.M0_activated = False
            self.M1_activated = False
            self.M2_activated = False
            self.M3_activated = False
            self.M4_activated = False
            self.M5_activated = False
            self.M6_activated = False
            self.M7_activated = False
            self.FF_active = False
            self.slider_m0.set(0)
            self.slider_m1.set(0)
            self.slider_m2.set(0)
            self.slider_m3.set(0)
            self.slider_m4.set(0)
            self.slider_m5.set(0)
            self.slider_m6.set(0)
            self.slider_m7.set(0)
            self.m0_btn_str.set('Start M0')
            self.m1_btn_str.set('Start M1')
            self.m2_btn_str.set('Start M2')
            self.m3_btn_str.set('Start M3')
            self.m4_btn_str.set('Start M4')
            self.m5_btn_str.set('Start M5')
            self.m6_btn_str.set('Start M6')
            self.m7_btn_str.set('Start M7')

    def check_ff_active(self):
        status = self.M0_activated + self.M1_activated + self.M2_activated + self.M3_activated + self.M4_activated \
                 + self.M5_activated + self.M6_activated + self.M7_activated
        return status

    def test_m0(self):
        self.M0_activated = not self.M0_activated
        self.FF_active = self.check_ff_active()
        if self.M0_activated:
            self.m0_btn_str.set('Pause M0')
            self.test_motors()
        if not self.M0_activated:
            self.master.ser.Send('M00\r')
            self.slider_m0.set(0)
            self.m0_btn_str.set('Start M0')

    def test_m1(self):
        self.M1_activated = not self.M1_activated
        self.FF_active = self.check_ff_active()
        if self.M1_activated:
            self.m1_btn_str.set('Pause M1')
            self.test_motors()
        if not self.M1_activated:
            self.master.ser.Send('M10\r')
            self.slider_m1.set(0)
            self.m1_btn_str.set('Start M1')

    def test_m2(self):
        self.M2_activated = not self.M2_activated
        self.FF_active = self.check_ff_active()
        if self.M2_activated:
            self.m2_btn_str.set('Pause M2')
            self.test_motors()
        if not self.M2_activated:
            self.master.ser.Send('M20\r')
            self.slider_m2.set(0)
            self.m2_btn_str.set('Start M2')

    def test_m3(self):
        self.M3_activated = not self.M3_activated
        self.FF_active = self.check_ff_active()
        if self.M3_activated:
            self.m3_btn_str.set('Pause M3')
            self.test_motors()
        if not self.M3_activated:
            self.master.ser.Send('M30\r')
            self.slider_m3.set(0)
            self.m3_btn_str.set('Start M3')

    def test_m4(self):
        self.M4_activated = not self.M4_activated
        self.FF_active = self.check_ff_active()
        if self.M4_activated:
            self.m4_btn_str.set('Pause M4')
            self.test_motors()
        if not self.M4_activated:
            self.master.ser.Send('M40\r')
            self.slider_m4.set(0)
            self.m4_btn_str.set('Start M4')

    def test_m5(self):
        self.M5_activated = not self.M5_activated
        self.FF_active = self.check_ff_active()
        if self.M5_activated:
            self.m5_btn_str.set('Pause M5')
            self.test_motors()
        if not self.M5_activated:
            self.master.ser.Send('M50\r')
            self.slider_m5.set(0)
            self.m5_btn_str.set('Start M5')

    def test_m6(self):
        self.M6_activated = not self.M6_activated
        self.FF_active = self.check_ff_active()
        if self.M6_activated:
            self.m6_btn_str.set('Pause M6')
            self.test_motors()
        if not self.M6_activated:
            self.master.ser.Send('M60\r')
            self.slider_m6.set(0)
            self.m6_btn_str.set('Start M6')

    def test_m7(self):
        self.M7_activated = not self.M7_activated
        self.FF_active = self.check_ff_active()
        if self.M7_activated:
            self.m7_btn_str.set('Pause M7')
            self.test_motors()
        if not self.M7_activated:
            self.master.ser.Send('M70\r')
            self.slider_m7.set(0)
            self.m7_btn_str.set('Start M7')

    def test_motors(self):
        if self.FF_active:
            x = self.com_ports[self.cb_COM_ports.current()]
            p, com_port_founded = ffcom.get_COM_port(x)
            if com_port_founded:
                if not self.master.ser.isopen:
                    self.master.ser.Open(p, 115200)
                motor_speed = int(self.slider_m0.get()*self.M0_activated * self.motor_calib_list[0])
                if motor_speed >= 100:
                    motor_speed = 100
                str_temp = 'M0' + str(motor_speed) + '\r'
                motor_speed = int(self.slider_m1.get() * self.M1_activated * self.motor_calib_list[1])
                if motor_speed >= 100:
                    motor_speed = 100
                str_temp = str_temp + 'M1' + str(motor_speed) + '\r'
                motor_speed = int(self.slider_m2.get() * self.M2_activated * self.motor_calib_list[2])
                if motor_speed >= 100:
                    motor_speed = 100
                str_temp = str_temp + 'M2' + str(motor_speed) + '\r'
                motor_speed = int(self.slider_m3.get() * self.M3_activated * self.motor_calib_list[3])
                if motor_speed >= 100:
                    motor_speed = 100
                str_temp = str_temp + 'M3' + str(motor_speed) + '\r'
                motor_speed = int(self.slider_m4.get() * self.M4_activated * self.motor_calib_list[4])
                if motor_speed >= 100:
                    motor_speed = 100
                str_temp = str_temp + 'M4' + str(motor_speed) + '\r'
                motor_speed = int(self.slider_m5.get() * self.M5_activated * self.motor_calib_list[5])
                if motor_speed >= 100:
                    motor_speed = 100
                str_temp = str_temp + 'M5' + str(motor_speed) + '\r'
                motor_speed = int(self.slider_m6.get() * self.M6_activated * self.motor_calib_list[6])
                if motor_speed >= 100:
                    motor_speed = 100
                str_temp = str_temp + 'M6' + str(motor_speed) + '\r'
                motor_speed = int(self.slider_m7.get() * self.M7_activated * self.motor_calib_list[7])
                if motor_speed >= 100:
                    motor_speed = 100
                str_temp = str_temp + 'M7' + str(motor_speed) + '\r'
                self.master.ser.Send(str_temp)
        if not self.FF_active:
            if self.master.ser.isopen:
                self.master.ser.Close()








