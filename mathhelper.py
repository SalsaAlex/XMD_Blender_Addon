import mathutils

def getColumn(mat : mathutils.Matrix, index : int):
        assert index >= 0 and index < len(mat.col)
        return mat.col[index]
    
    
def getRow(mat : mathutils.Matrix, index : int):
        assert index >= 0 and index < len(mat.row)
        return mat.row[index]
    
#vec from

def Vec2FromStrList(floatlist : list[str]):
    assert len(floatlist) == 2
    return mathutils.Vector([
        float(floatlist[0]), 
        float(floatlist[1])])

def Vec3FromStrList(floatlist : list[str]):
    assert len(floatlist) == 3
    return mathutils.Vector([
        float(floatlist[0]), 
        float(floatlist[1]),
        float(floatlist[2])])

def Vec4FromStrList(floatlist : list[str]):
    assert len(floatlist) == 4
    return mathutils.Vector([
        float(floatlist[0]), 
        float(floatlist[1]),
        float(floatlist[2]),
        float(floatlist[3])])


def Vec2FromFloatList(floatlist : list[float]):
    assert len(floatlist) == 2
    return mathutils.Vector([
        floatlist[0], 
        floatlist[1]])

def Vec3FromFloatList(floatlist : list[float]):
    assert len(floatlist) == 3
    return mathutils.Vector([
        floatlist[0], 
        floatlist[1],
        floatlist[2]])

def Vec4FromFloatList(floatlist : list[float]):
    assert len(floatlist) == 4
    return mathutils.Vector([
        floatlist[0], 
        floatlist[1],
        floatlist[2],
        floatlist[3]])


#vec to

def Vec2ToStrList(vec : mathutils.Vector):
    assert len(vec) == 2
    return [
        str(vec.x), 
        str(vec.y)]

def Vec3ToStrList(vec : mathutils.Vector):
    assert len(vec) == 3
    return [
        str(vec.x), 
        str(vec.y),
        str(vec.z)]

def Vec4ToStrList(vec : mathutils.Vector):
    assert len(vec) == 4
    return [
        str(vec.x), 
        str(vec.y),
        str(vec.z),
        str(vec.w)]


def Vec2ToFloatList(vec : mathutils.Vector):
    assert len(vec) == 2
    return [
        vec.x, 
        vec.y]

def Vec3ToFloatList(vec : mathutils.Vector):
    assert len(vec) == 3
    return [
        vec.x, 
        vec.y,
        vec.z]

def Vec4ToFloatList(vec : mathutils.Vector):
    assert len(vec) == 4
    return [
        vec.x, 
        vec.y,
        vec.z,
        vec.w]