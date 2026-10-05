from .. import FileIO
import string
import ctypes
import bpy
import datetime

def win32_GetUserName() -> str:
    advapi32 = ctypes.windll.advapi32
    buf = ctypes.create_string_buffer(128 + 1)
    n = ctypes.c_int(128 + 1)
    if advapi32.GetUserNameA(buf, ctypes.byref(n)):
        string : str = bytes(buf.value).decode()
        return string

def win32_GetComputerName():
    kernel32 = ctypes.windll.kernel32
    buf = ctypes.create_string_buffer(128 + 1)
    n = ctypes.c_int(128 + 1)
    if kernel32.GetComputerNameA(buf, ctypes.byref(n)):
        string : str = bytes(buf.value).decode()
        return string


class XMD_infoentry_info:
    def __init__(self):
        self.user = ""
        self.host  = ""
        self.texture_file = ""
        self.format_version = ""
        self.send_bug_reports_to = ""
        self.application = ""
        self.original_file = ""
        self.date =  ""
        self.time = ""

    def construct(self):
        if win32_GetUserName():
            self.user = win32_GetUserName()
        if win32_GetComputerName():
            self.host = win32_GetComputerName()

        self.texture_file = "none"
        self.format_version = "XMD_004A"
        self.send_bug_reports_to = "support@naturalmotion.com"
        self.application = f"blender {bpy.app.version_string}"
        self.original_file = bpy.data.filepath
        date = datetime.datetime.now()
        self.date = f"{date.day}/{date.month}/{date.year}"
        self.time = f"{date.hour}.{date.minute}.{date.second}"

    def from_textfile(self, fileio : FileIO.TextFileIO):
        fileio.ReadLine() #first line is just something along lines of |XMD_004A#MAYA#0004.1.4|
        
        if fileio.ReadLine().split(' ')[0].count('INFO') == 0:
            fileio.Rewind_Line()
            return
    
        assert fileio.ReadLine().split(' ')[0].count('{') != 0
    
        self.user =                 fileio.ReadLine().split(' ')[1].replace('\"', '')
        self.host =                 fileio.ReadLine().split(' ')[1].replace('\"', '')
        self.texture_file =         fileio.ReadLine().split(' ')[1].replace('\"', '')
        self.format_version =       fileio.ReadLine().split(' ')[1]
        self.send_bug_reports_to =  fileio.ReadLine().split(' ')[1]
        self.application =          fileio.ReadLine().split(' ')[1].replace('\"', '')
        self.original_file =        fileio.ReadLine().split(' ')[1].replace('\"', '')
        self.date =                 fileio.ReadLine().split(' ')[1]
        self.time =                 fileio.ReadLine().split(' ')[1]

        
        assert self.format_version.count('XMD_004A') != 0
        
        lineskip = fileio.ReadLine()
        while lineskip.count('}') == 0:
            lineskip = fileio.ReadLine()

    def to_textfile(self, fileio : FileIO.TextFileIO):
        fileio.WriteLine("|XMD_004A#BLENDER|")
        fileio.WriteLine("INFO info")
        fileio.WriteLine("{")
        fileio.WriteLine(f"\tuser \"{self.user}\"")
        fileio.WriteLine(f"\thost \"{self.host}\"")
        fileio.WriteLine(f"\ttexture_file \"{self.texture_file}\"")
        fileio.WriteLine(f"\tformat_version {self.format_version}")
        fileio.WriteLine(f"\tsend_bug_reports_to {self.send_bug_reports_to}")
        fileio.WriteLine(f"\tapplication \"{self.application}\"")
        fileio.WriteLine(f"\toriginal_file \"{self.original_file}\"")
        fileio.WriteLine(f"\tdate {self.date}")
        fileio.WriteLine(f"\ttime {self.time}")
        fileio.WriteLine("}")