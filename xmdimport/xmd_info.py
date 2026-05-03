from .. import FileIO
import string


class XMD_infoentry_info:
    def __init__(self, fileio : FileIO.TextFileIO):
        
        fileio.ReadLine() #first line is just something along lines of |XMD_004A#MAYA#0004.1.4|

        assert fileio.ReadLine().split(' ')[0].count('INFO') != 0
        assert fileio.ReadLine().split(' ')[0].count('{') != 0

        self.user = fileio.ReadLine().split(' ')[1].replace('\"', '')
        self.host = fileio.ReadLine().split(' ')[1].replace('\"', '')
        self.texture_file = fileio.ReadLine().split(' ')[1].replace('\"', '')
        self.format_version = fileio.ReadLine().split(' ')[1]
        assert self.format_version.count('XMD_004A') != 0
        
        lineskip = fileio.ReadLine()
        while lineskip.count('}') == 0:
            lineskip = fileio.ReadLine()

def parseXMDInfoEntry(fileio : FileIO.TextFileIO):
    return XMD_infoentry_info(fileio)