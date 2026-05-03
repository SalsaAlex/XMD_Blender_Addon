from .. import FileIO
import string

class XMD_basenodeinfo:
    def __init__(self, nodeheader, fileio : FileIO.TextFileIO):
        self.nodename = nodeheader[1]
        self.nodetypenme = nodeheader[0]
        assert fileio.ReadLine().split(' ')[0].count('{') == 1
        nodeid_keyvalue = fileio.ReadLine().split(' ') # id x
        assert nodeid_keyvalue[0].count("id") == 1
        self.nodeid = int(nodeid_keyvalue[1])
    
    def getNodeID(self):
        return self.nodeid
    

def skipNodeEntry(fileio : FileIO.TextFileIO):
    assert fileio.ReadLine().find("{") != -1
    bracketcount = 1
    while bracketcount != 0:
        curline = fileio.ReadLine()
        if curline.find("}") != -1:
            bracketcount = bracketcount - 1
        elif curline.find("{") != -1:
            bracketcount = bracketcount + 1
        
        if bracketcount == 0:
            break
    