from .. import FileIO
import string



class XMD_basenodeinfo:
    def __init__(self, nodetypename, writeid : bool = True):
        self.nodename = "unnamed"
        self.nodetypename = nodetypename
        self.nodeid = -1
        self.writeid = writeid

    def from_textfile(self, nodeheader, fileio : FileIO.TextFileIO):
        self.nodename = "".join(nodeheader[1:])
        assert self.nodetypename == nodeheader[0]
        
        assert fileio.ReadLine().split(' ')[0].count('{') == 1
        if self.writeid == True: 
            nodeid_keyvalue = fileio.ReadLine().split(' ') # id x
            assert nodeid_keyvalue[0].count("id") == 1
            self.nodeid = int(nodeid_keyvalue[len(nodeid_keyvalue)-1])

    def to_textfile(self, fileio : FileIO.TextFileIO):
        fileio.WriteLine(f"{self.nodetypename} {self.nodename}")
        fileio.WriteLine("{")
        if self.writeid is True: fileio.WriteLine(f"\tid {self.nodeid}")
        self._textfile_write(fileio)
        fileio.WriteLine("}")

    #override this
    def _textfile_write(self, fileio : FileIO.TextFileIO):
        assert 0 == 1, "textfile write unimplemented or accidentally called from inherited class !"

    

    def setNodeID(self, id):
        self.nodeid = id
    def getNodeID(self):
        return self.nodeid

    def setNodeName(self, name : str):
        self.nodename = name.split("\n")[0]
        self.nodename = self.nodename.replace(" ", "_")
    def getNodeName(self):
        return self.nodename

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