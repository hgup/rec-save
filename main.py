import os
import mysql.connector
from tkinter import ttk
from datetime import datetime
import datetime as dt
import cv2
import tkinter as tk
import config
from PIL import Image, ImageTk




class App(tk.Frame):
    def __init__(self, master=None):
        # an App frame
        super().__init__(master)
        self.master = master
        self.pack()
        # should be changed to 0,1,2... depending on capture device
        self._cam = cv2.VideoCapture(config.discourse)
        self._cam.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
        self._cam.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)

        # state for allowing the frames to be recorded
        self.is_recording = False;

        # creates all the text variables for accessing widget data
        self.create_vars()

        # creates all the widgets and puts them on the screen
        self.create_widgets()
        self.run_tests()
        self.preview_recorder()

    def run_tests(self):
        helper = DbHelper(self)
        if helper.ok:
            self.set_status("DB connected")
    
    def create_vars(self):
        self.id_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.source_var = tk.StringVar()
    
    def create_widgets(self):
    # STRUCTURE
    # - topFrame
    #     - inputFrame 
    #         - input_id
    #         - input_date
    #     - validateFrame / patientNotFound
    #         [contained in info as a list]
    #         - [0] Name (label)
    #         - [1] Age (label)
    #         - [2] Sex (label)
    # - bottomFrame
    #     - video_widget
    #     - choose_source - start - save - stop
    #     (stored as buttons [0]    [1]    [2])
    # - status_text

        # main frames
        self.topFrame = tk.Frame(self)
        self.bottomFrame = tk.Frame(self)
        self.topFrame.pack(fill=tk.X, expand=True)
        self.bottomFrame.pack()

        # TOP FRAME ----------------------------------------------------

        self.inputFrame = tk.Frame(self.topFrame)
        self.inputFrame.pack(side=tk.LEFT, fill=tk.BOTH)
        self.validateFrame = tk.Frame(self.topFrame)
        self.patientNotFound = tk.Label(self.topFrame,text="No Patient with this ID")

        # input_id
        tk.Label(self.inputFrame,text="ID").grid(row = 0, column=0)
        self.input_id = tk.Entry(self.inputFrame, textvariable=self.id_var, justify="center")
        self.input_id.grid(row = 0, column = 1)
        self.id_var.trace_add('write',self.check_id)

        # input_date
        # TODO datepicker
        tk.Label(self.inputFrame,text="Date").grid(row = 1, column=0)
        self.input_date = tk.Entry(self.inputFrame, textvariable=self.date_var, justify="center")
        self.input_date.insert(0,str(datetime.now()).split()[0])
        self.input_date.grid(row=1, column=1)

        ## validate
        self.info = [tk.Label(self.validateFrame,text=text) for text in ["\tName\t: ","\tAge\t: ", "\tSex\t:", "\tDOB\t:"]]
        for i in self.info:
            i.pack(expand=True, anchor="w")

        
        # BOTTOM FRAME -----------------------------------------------

        # video_widget
        self.video_widget = tk.Label(self.bottomFrame)
        self.video_widget.pack()

        # choose_source
        self.choose_source = ttk.Combobox(
            self.bottomFrame, state="readonly", textvariable=self.source_var,
            values = config.videoTypes)
        self.choose_source.current(config.last_source)
        self.choose_source.pack(side=tk.LEFT)
        print("DEV source var: ",self.source_var.get())

        # start stop save buttons
        self.buttons = {
            "start": tk.Button(self.bottomFrame,text="start recording", bg='#aaaaff'),
            "stop": tk.Button(self.bottomFrame,text="stop", bg = '#ffaaaa'),
            "save": tk.Button(self.bottomFrame,text="save",bg="#88ff88"),
        }

        self.buttons["start"]["command"] = self.start_recording
        self.buttons["stop"]["command"] = self.stop_recording
        self.buttons["save"]["command"] = self.save_recording

        self.buttons["start"].pack(side=tk.LEFT, )
        self.buttons["stop"].pack(side=tk.LEFT, )
        self.buttons["save"].pack(side=tk.RIGHT, expand = True )

        # status bar
        self.status_text = tk.Label(self,relief=tk.RAISED)
        # self.statusText["text"] = "this is just a test label"
        self.status_text.pack(side=tk.BOTTOM, fill=tk.X)
    
    def check_id(self, var: tk.StringVar, index, mode):
        val = self.id_var.get()
        
        if len(val) == 6: # what is id length
            self.validate_patient(val)
        else:
            self.patientNotFound.pack_forget()
            self.validateFrame.pack_forget()
    
        

    # callback for id
    
    def validate_patient(self, patient_id):
        self.helper = DbHelper(self)
        patient_data = self.helper.get_patient_data(patient_id)
        self.helper.close()

        if patient_data:
            print("DEV PRINT",patient_data)
            name = patient_data[1]
            age = patient_data[2].year
            sex = patient_data[3]
            dob = patient_data[2].strftime("%d/%m/%Y")

            self.patientNotFound.pack_forget()
            self.validateFrame.pack(side=tk.LEFT, anchor='e')
            self.info[0]["text"] = f"\tName\t:{name}"
            self.info[1]["text"] = f"\tAge\t:{age}"
            self.info[2]["text"] = f"\tSex\t:{sex}"
            self.info[3]["text"] = f"\tDOB\t:{dob}"
            return True
        else:
            self.validateFrame.pack_forget()
            self.patientNotFound.pack(side=tk.LEFT,fill=tk.BOTH, anchor='e')
            return False
            
    def preview_recorder(self):
    # self.frame to be used for all recording purposes

        # capture frame by frame
        self.ok, self.frame = self._cam.read()

        if self.is_recording:
            self._out.write(self.frame)

        # convert image colorspace
        self.opencv_img = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)

        # capture latest frame
        captured_img = Image.fromarray(self.opencv_img)

        # convert captured to photoimage
        self.photo_img = ImageTk.PhotoImage(image=captured_img)

        # Display photoimage in Label
        self.video_widget.configure(image=self.photo_img)


        # label_widget
        self.video_widget.after(10, self.preview_recorder) # 16 value needs testing
    
    def start_recording(self, filename = 'output.mp4'):
        if self.ok:
            self.set_status("STARTED RECORDING","DEFAULT")
            print("Started recording")
            # the resolution should be received from the VideoCapture module
            self._out= cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'mp4v'), 30, (int(self._cam.get(3)),int(self._cam.get(4))))
            self.is_recording = True
        else:
            self.set_status("Failed to start recording.","ERROR")
    
    def stop_recording(self):
        self.is_recording = False
        self._out.release()
        self.set_status("STOPPED RECORDING","DEFAULT")
        print("Stopped recording")
    
    def save_recording(self):

        if self.validate_patient(self.id_var.get()):
            self.helper = DbHelper(self)
            self.helper.save(int(self.id_var.get()), self.source_var.get(), self.date_var.get())
            self.helper.close()
        else:
            self.set_status("Invalid Patient ID. Could not find patient", "ERROR")
    
    def set_status(self, text="", type=""):
    # types = DEFAULT, SUCCESS, ERROR
    # just call set_status() to clear status
        if type == "ERROR":
            self.status_text["fg"] = "#ffffff"
            self.status_text["bg"] = "#ff3333"
        elif type == "SUCCESS":
            self.status_text["fg"] = "#000000"
            self.status_text["bg"] = "#11ff11"
        elif type == "DEFAULT":
            self.status_text["fg"] = "#ffffff"
            self.status_text["bg"] = "#8888ff"
        else:
            self.status_text["fg"] = "#000000"
            self.status_text["bg"] = "#ffffff"
        self.status_text["text"] = text

        


class DbHelper():
# should be instantiated, used and then cleaned by calling DbHelper().close()
    
    def __init__(self, app: App):
    
        # connect to the database, using .env file variables
        self.app = app # to access the tkinter app from here
        try:
            self.db = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST"),
                port=os.getenv("MYSQL_PORT"),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                database=os.getenv("MYSQL_DATABASE")
            )
            self.ok = True
            # put table names in environment variables for convenience
            self.video_table = os.getenv("MYSQL_VIDEO_TABLE")
            self.patient_table= os.getenv("MYSQL_PATIENT_TABLE")
            self.cursor = self.db.cursor()
            self.saved = False
        except Exception as e:
            self.ok = False
            self.app.set_status(f"[DB ERROR] {e}", "ERROR")

    
    def save(self, *args):
    # args = (patient_id, video_type, date_of_visit)

        filename = self.generate_filename(*args)
        status = self.save_to_server(*args,filename)

        if self.saved:
            self.update_db(*args,filename)
            self.app.set_status(f"Successfully saved as {filename} to the server!","SUCCESS")
        else:
            print(status) # write the status
            self.app.set_status(f"Failed to save with ERROR: {status}","ERROR")
    
    def save_to_server(self, patient_id, video_type, date_of_visit, filename):
        try:
            # TODO server saving logic
            self.saved = True
            return f"saved file as {filename} successfully"

        except Exception as e:
            # else
            return e

    def update_db(self, patient_id, video_type, date_of_visit, filename):
        self.saved = False
        try:
            self.cursor.execute(
                f"INSERT INTO `{self.video_table}` (patient_id, video_type, filename, date_of_visit) values (%s, %s, %s, %s)",
                (patient_id,video_type,filename, date_of_visit),)
            self.db.commit()
            print(self.cursor.rowcount, "rows inserted, ID:", self.cursor.lastrowid);
        except Exception as e:
            print("Dev Error:", e)
    
    def get_patient_data(self, patient_id):
        patient_id = int(patient_id)
        self.cursor.execute(f"SELECT * FROM {self.patient_table} where id={patient_id}")
        result = self.cursor.fetchall()
        print("FETCHED PATIENT DATA:", result)
        if result:
            return result[0]
        else:
            return False

    def generate_filename(self,*args):
        # get the latest filename form server
        patient_id, type, *_ = args
        self.cursor.execute(
            f""" select r.patient_id, r.video_type, r.filename, r.created from rec_save_videos r 
                inner join (
                    select patient_id, video_type, max(created) as MaxDate
                    from rec_save_videos
                    group by video_type, patient_id ) rm
                on  r.patient_id=rm.patient_id and
                    r.video_type=rm.video_type and
                    r.created=rm.MaxDate
                where r.patient_id=%s and r.video_type=%s
            """,(patient_id, type));  # date_of_visit argument not required
        result = self.cursor.fetchall()
        # extract last number and get next one (could have done better using regex)
        print("FETCHED FILENAME DATA:",result)
        if result:
            # increment and format (we use -1 to take the last entry to prevent redundency, but our app will take care of it anyway)
            formatted_number = "%03d" % (int(result[-1][2].split(type)[1].split(".")[0])+1)
        else:
            # first video of this type
            formatted_number = "%03d" % 1
        # change "%03d" to %04d% for 4 digits
        return f"/server/{patient_id}/{type}{formatted_number}.mp4"
    
    def close(self):
        # can't keep the connection open else, other instances won't be able to use it.
        self.db.close()
        
        

        



        





if __name__ == "__main__":
    root = tk.Tk()
    root.title("Rec Save")
    app = App(master=root)
    app.mainloop()
    app._cam.release()
