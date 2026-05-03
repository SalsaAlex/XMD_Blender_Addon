from .. import FileIO

def WriteDummyAnim(fileio : FileIO.TextFileIO):
    fileio.WriteLine("ANIM_CYCLE \"dummyanim\"\n")
    fileio.WriteLine("{\n")
    fileio.WriteLine("\tnum_bones 0\n")
    fileio.WriteLine("\tstart 0\n")
    fileio.WriteLine("\tend 1\n")
    fileio.WriteLine("\tnum_frames 2\n")
    fileio.WriteLine("\tfps 30\n")
    fileio.WriteLine("}\n")