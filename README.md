# ForceFeel-Condor2-interface -(text updated 27.12.2019)
Realteus Forcefeel control interface for Condor 2 soaring simulator (might work with Jetseat cushion also)
This interface is programmed with Python 3.7 version.
System converts Condor2 UDP telemetry strings into Realteus Forcefeel cushion motor control command strings.
Usage:
- Activate Condor2 UDP telemetry interface => ~/Condor2/Settings/UDP.ini:
  [General] => Enabled=1, [Connection] => Host=127.0.0.1, Port=55278, [Misc] => SendIntervalMs=10, ExtendedData=1

- Check that ForceFeel connection and motors work as expected, find the correct COM-port also
  - Main window: Edit-Test ForceFeel controls =>
    - Turn ForceFeel ON, select PC mode
    - Leave baudrate to 115200, select COM port that you expect to be your ForceFeel COM port
    - Use sliders M0-M7 and buttons Start M0 - Start M7 => You should be control your motors individually with sliders and buttons if connection is Ok, change COM port if nothin happens. You can stop all motors with 'Stop all motors button'
    - When connection work as it should, save configuration: File-Save..
    - Exit this window: File-Exit
- Main window: 
    - Profile file: ***.prof => ForceFeel motor control file that system is using right now
    - Monitor file: ***.mon => Monitor parameter list of parameters that are showed here
    - Start button: This activates the motor control application. You can pause the app whenever you want, pause will reset the flt_min and flt_max monitoring parameters
 - Edit - Select and edit profile data and monitor window:
      -  You can select, edit and create new monitor window parameter lists and (plane specific?) profile files
      - NOTE! you can select the required monitor and profile files only with this way:
         - Select the required *.prof and *.mon  files with comboboxes
         - Exit like this: File - Exit (read: that X in the right up corner doesn't save the selected files into the default.ini file)
  - List of files you need:
    1) *.py files mentioned in the main branch  (if you use this app via python editor) or *.exe that is created with these *.py files
      - Main file is 'Condor2_shaker_main.py'
    2) *.ini files, stored under same folder that 1) files:
        - default.ini
        - ff_port_data.ini
    3) default.mon -file: this is default monitor file, you can modify this or create new ones. All ?.mon files should be located under same folder that 1) files are 
    4) default.prof -file: this is default profile file, you can modify this file also or create (each plane type?) dedicated files. These files should be also located under same folder that 1) files are 
    
The following new features added (30.12.2019):
- Updated wheelshake function (function added to default.prof file also)
- Motor calibration gain parameters added (motors might have different "butt"-feeling with same power setting => these can be balanced with motor gain parameters)
- UDP-Forcefeel-update time speeded up => faster response to telemetry changes (=less filtering before motor command updates.    
