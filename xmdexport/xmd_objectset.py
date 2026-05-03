from .. import FileIO

def WriteObjectSet(fileio : FileIO.TextFileIO, objectlist : list[int], nodeid : int):
    fileio.WriteLine("OBJECT_SET objset\n")
    fileio.WriteLine("{\n")
    fileio.WriteLine("\tid " + str(nodeid) + "\n")
    fileio.WriteLine("\tnum_items " + str(len(objectlist)) + "\n")
    for objindex in objectlist:
        fileio.WriteLine("\t\t" + str(objindex) + "\n")
    fileio.WriteLine("\tannotation \"\"\n")
    fileio.WriteLine("}\n")