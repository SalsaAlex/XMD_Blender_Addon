from .. import FileIO
from . import xmd_geometry
from .. import mathhelper
import mathutils

class polymesh_indexset:
    def __init__(self, fileio : FileIO.TextFileIO):
        self.name = fileio.ReadLine().split()[1].replace('\"', "")
        self.faces : list[list[int]] = []

        assert fileio.ReadLine().count('{') is 1 #opening bracket
        line = fileio.ReadLine()

        while line.count('}') is not 1:
            indexseq : list[int] = []
            indexes = line.split()
            for index in indexes:
                indexseq.append(int(index))
            self.faces.append(indexseq)
            line = fileio.ReadLine()

class polymesh_vertexset:
    def __init__(self, fileio : FileIO.TextFileIO):
        self.name = fileio.ReadLine().split()[1].replace('\"', "")
        self.elements : list[mathutils.Vector] = []
        
        assert fileio.ReadLine().count('{') is 1 #opening bracket
        
        num_elements = int(fileio.ReadLine().split()[1])
        element_size = int(fileio.ReadLine().split()[1])
        fileio.ReadLine() #usage
        self.default_indexset = fileio.ReadLine().split()[1].replace('\"', "")
        fileio.ReadLine() #elements

        if element_size == 4:
            while num_elements > 0:
                self.elements.append(mathhelper.Vec4FromStrList(fileio.ReadLine().split()))
                num_elements = num_elements -1
        elif element_size == 3:
            while num_elements > 0:
                self.elements.append(mathhelper.Vec3FromStrList(fileio.ReadLine().split()))
                num_elements = num_elements -1
        else:
            assert element_size == 2
            while num_elements > 0:
                self.elements.append(mathhelper.Vec2FromStrList(fileio.ReadLine().split()))
                num_elements = num_elements -1

        assert fileio.ReadLine().count('}') is 1 # closing bracket



class XMD_polygonmesh(xmd_geometry.XMD_geometry):
    def __init__(self, nodeheader, fileio : FileIO.TextFileIO):
        super().__init__(nodeheader, fileio, False)

        self.polycounts : list[int] = []
        self.indexsets : list[polymesh_indexset] = []
        self.vertexsets : list[polymesh_vertexset] = []

        self.default_pointindex_set = fileio.ReadLine().split()[1].replace('\"', "")

        fileio.ReadLine() # numpolycount
        fileio.ReadLine() # opening bracket

        
        while True:
            line = fileio.ReadLine()
            if line.count('}') is 1:
                break

            self.polycounts.append(int(line.split()[0]))

        num_indexsets = int(fileio.ReadLine().split()[1])
        while num_indexsets > 0:
            self.indexsets.append(polymesh_indexset(fileio))
            num_indexsets = num_indexsets - 1


        num_vertexsets = int(fileio.ReadLine().split()[1])
        while num_vertexsets > 0:
            self.vertexsets.append(polymesh_vertexset(fileio))
            num_vertexsets = num_vertexsets - 1


        fileio.ReadLine() # closing bracket for this node