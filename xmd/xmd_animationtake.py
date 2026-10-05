from .. import FileIO
from . import xmd_base
import mathutils
from .. import mathhelper

class animnode_attribs:
    def __init__(self):
        self.name = "unnamed"
        self.num_streams = 0
        self.elements_per_sample = 0
        self.streams : list = [] #{"name":str, "elements":}

    #starts from the node name
    def from_textfile(self, fileio : FileIO.TextFileIO):
        line = fileio.ReadLine().split()
        assert len(line) > 1 and line[0].count("ATTR")
        self.name = line[1]
        assert fileio.ReadLine().count("{") == 1#open bracket
        self.num_streams = int(fileio.ReadLine().split()[1])
        self.elements_per_sample = int(fileio.ReadLine().split()[1])
        for i in range(self.num_streams):
            streamname = fileio.ReadLine().split()[0]
            fileio.ReadLine() #open bracket
            samples : list = []
            while True:
                line = fileio.ReadLine()
                if line.count("}"): break
                if len(line.split()) < 1: continue
                elements = line.split()
                if self.elements_per_sample == 3:
                    samples.append(mathhelper.Vec3FromStrList(elements))
                elif self.elements_per_sample == 4:
                    samples.append(mathhelper.Vec4FromStrList(elements))
            self.streams.append({"name":streamname, "elements":samples})
        assert fileio.ReadLine().count("}") == 1 #close bracket

class animnode:
    def __init__(self):
        self.num_animated_attrs = 0
        self.num_animated_attrs_user = 0
        self.attribs : list[animnode_attribs] = []

    #starts from the open bracket
    def from_textfile(self, fileio : FileIO.TextFileIO):
        fileio.ReadLine() #open bracket
        self.num_animated_attrs = int(fileio.ReadLine().split()[1])
        self.num_animated_attrs_user = int(fileio.ReadLine().split()[1])
        for _ in range(self.num_animated_attrs):
            attribs = animnode_attribs()
            attribs.from_textfile(fileio)
            self.attribs.append(attribs)
        fileio.ReadLine() #close bracket


    def getAttribSamples(self, attribname):
        for attrib in self.attribs:
            if attrib.name == attribname and len(attrib.streams) > 0:
                return attrib.streams[0]["elements"]
        return None
        

class XMD_animationtake(xmd_base.XMD_basenodeinfo):
    def __init__(self):
        super().__init__("ANIMATION_TAKE")
        self.start_time = 0
        self.end_time = 0
        self.fps = 0
        self.current_time = 0
        self.num_animated_nodes = 0
        self.num_event_tracks = 0
        self.animationnodes : dict[int, animnode] = {}

    def from_textfile(self, nodeheader, fileio : FileIO.TextFileIO):
        super().from_textfile(nodeheader, fileio)
        self.start_time = int(fileio.ReadLine().split()[1])
        self.end_time = int(fileio.ReadLine().split()[1])
        self.fps = int(fileio.ReadLine().split()[1])
        self.current_time = int(fileio.ReadLine().split()[1])
        self.num_animated_nodes = int(fileio.ReadLine().split()[1])
        self.num_event_tracks = int(fileio.ReadLine().split()[1])
        for _ in range(self.num_animated_nodes):
            animnodeindex = int(fileio.ReadLine().split()[1])
            animationnode = animnode()
            animationnode.from_textfile(fileio)
            self.animationnodes[animnodeindex] = animationnode
        assert fileio.ReadLine().count("}") == 1
        

    def _textfile_write(self, fileio : FileIO.TextFileIO):
        fileio.WriteLine(f"\tstart_time {self.start_time}")
        fileio.WriteLine(f"\tend_time {self.end_time}")
        fileio.WriteLine(f"\tfps {self.fps}")
        fileio.WriteLine(f"\tcurrent_time {self.current_time}")
        fileio.WriteLine(f"\tnum_animated_nodes {self.num_animated_nodes}")
        fileio.WriteLine(f"\tnum_event_tracks {self.num_event_tracks}")