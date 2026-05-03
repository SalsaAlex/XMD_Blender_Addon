from .. import FileIO

def WriteInfo(fileio : FileIO.TextFileIO):
    fileio.WriteLine("|XMD_004A#BLENDER|\n")
    fileio.WriteLine("INFO info\n")
    fileio.WriteLine("{\n")
    fileio.WriteLine("\tuser \" \"\n")
    fileio.WriteLine("\thost \" \"\n")
    fileio.WriteLine("\ttexture_file \"none\"\n")
    fileio.WriteLine("\tformat_version XMD_004A\n")
    fileio.WriteLine("\tsend_bug_reports_to jeevacation@gmail.com\n")
    fileio.WriteLine("\tapplication \"Blender\"\n")
    fileio.WriteLine("\toriginal_file \" \"\n")
    fileio.WriteLine("\tdate 12/2/2010\n")
    fileio.WriteLine("\ttime 9.54:27\n")
    fileio.WriteLine("}\n")