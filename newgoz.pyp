import c4d, sys, string, os
import struct
import time
import array
from c4d import documents, plugins
from c4d import storage as st, gui
from c4d import Matrix, Vector
from c4d import bitmaps, gui, plugins
from c4d.gui import MessageDialog

GoZ_TAG_END_OF_FILE                 =   0       #must be the last tag in the file

GoZ_TAG_BASE_ID_POINT               =   10000
GoZ_TAG_POINT_LIST                  =   10001           # 3 float values of x,y,z. each point takes 12 bytes exactly.

GoZ_TAG_BASE_ID_FACE                =   20000
GoZ_TAG_FACE4_LIST_FORMAT_1         =   20001       # first point is index 0, triangle represented by the 4th point set to -1. This is the preffered format for ZBrush. Each face takes 16 bytes exactly.
GoZ_TAG_FACE4_LIST_FORMAT_2         =   20002       # first point is index 0, triangle represented by the 4th point index equal to the 3rd point index. Each face takes 16 bytes exactly.
GoZ_TAG_FACE3_LIST                  =   20003       # first point is index 0, Only 3 points per face (triangles).

GoZ_TAG_BASE_UV                     =   25000
GoZ_TAG_UV4_LIST                    =   25001                   # 4 (U,V) values per face

GoZ_TAG_BASE_ID_TEXTURE_MAP         =   45000
GoZ_TAG_TEXTURE_MAP_PATH            =   45001                   # optional relative-path filename for texture   image . The default image format is  .tif 24 bits.

GoZ_TAG_BASE_ID_NORMAL_MAP          =   50000
GoZ_TAG_NORMAL_MAP_PATH             =   50001                   # optional relative-path filename for NormalMap image.  The default image format is  .tif 24 bits.

GoZ_TAG_BASE_ID_DISPLACEMENT_MAP    =   55000
GoZ_TAG_DISPLACEMENT_MAP_PATH       =   55001               # optional relative-path filename for DisplacementMap image. the modifier value contains the scaling factor for 16 bits displacement maps.  The default image format is .tif 16 bits. mid gray is zero displacement.

GoZ_CONTAINER_ID                    =   2000000

ZBRUSH_GOZ_R20_ID_FROMZB            =   1050561
ZBRUSH_GOZ_R20_ID_TOZB              =   1050854

def CreateObjectFromGoZb(objectPathStr, objectName, parentObj):
    fileOffset = 32
    vDoc = c4d.documents.GetActiveDocument()

    path = os.path.join(objectPathStr + ".GOZ")

    fileOffset = 32 
    vDoc = c4d.documents.GetActiveDocument()



    with open(path, "rb") as f:
        # Some initializations.
        global textureMapPath
        global normalMapPath
        global displacementMapPath
        global displacementFactor
        textureMapPath = ""
        normalMapPath = ""
        displacementMapPath = ""

        fileOffset = 32
        
        vObj = c4d.BaseObject(c4d.Opolygon)
        vDoc.StartUndo()
        vDoc.AddUndo(c4d.UNDO_OBJECT_NEW, vObj)
        vDoc.EndUndo()
        

        while 1:
            f.seek(fileOffset,0)
            partType = struct.unpack('@l', f.read(4))[0]
            partSize = struct.unpack('@l', f.read(4))[0]
            itemsCount = struct.unpack('@l', f.read(4))[0]
            modifier = struct.unpack('@f', f.read(4))[0]

            if partType == GoZ_TAG_POINT_LIST :
                c4d.StatusSetText(objectName + " Importing Points ")
                mat = Matrix()
                mat.Scale(Vector(100,100, -100))
                if parentObj != None:
                    tr = ~Matrix(parentObj.GetMg())
                    mat = mat*tr

                
                memOffset = 0;
                pt = Vector(0)
                vObj.ResizeObject(itemsCount, 0)
                for i in xrange(itemsCount):
                    c4d.StatusSetBar(i / float(itemsCount) * 100)
                    pt.x  = struct.unpack('@f',f.read(4))[0] 
                    pt.y  = struct.unpack('@f',f.read(4))[0]
                    pt.z  = struct.unpack('@f',f.read(4))[0]
                    pt = mat * pt;
                    vObj.SetPoint(i,pt)

            elif partType ==GoZ_TAG_FACE4_LIST_FORMAT_1:
                c4d.StatusSetText(objectName + " Importing Polys ")
                poly = c4d.CPolygon(0,0,0,0)
                ptcnt = vObj.GetPointCount()
                vObj.ResizeObject(ptcnt,itemsCount)
                for i in xrange (itemsCount):
                    c4d.StatusSetBar(i / float(itemsCount) * 100)
                    poly.a = struct.unpack('@l',f.read(4))[0]
                    poly.d = struct.unpack('@l',f.read(4))[0]
                    poly.c = struct.unpack('@l',f.read(4))[0]
                    poly.b = struct.unpack('@l',f.read(4))[0]
                    if poly.b == -1:
                        poly.b = poly.c
                        poly.c = poly.d
                    vObj.SetPolygon(i, poly)

            elif partType ==GoZ_TAG_FACE4_LIST_FORMAT_2:
                poly = c4d.CPolygon(0,0,0,0)
                ptcnt = vObj.GetPointCount()
                vObj.ResizeObject(ptcnt,itemsCount)
                for i in xrange (itemsCount):
                    poly.a = struct.unpack('@l',f.read(4))[0]
                    poly.d = struct.unpack('@l',f.read(4))[0]
                    poly.c = struct.unpack('@l',f.read(4))[0]
                    poly.b = struct.unpack('@l',f.read(4))[0]
                    if poly.c == poly.b:
                        poly.c = poly.d
                    vObj.SetPolygon(i, poly)
            elif partType ==GoZ_TAG_UV4_LIST:
                c4d.StatusSetText(objectName + " Importing UVs ")
                uvwtag = vObj.MakeVariableTag(c4d.Tuvw,itemsCount, None)
                vadr = vObj.GetAllPolygons()
                for i in xrange (itemsCount):
                    c4d.StatusSetBar(i / float(itemsCount) * 100)
                    if vadr[i].c == vadr[i].d:
                        a = Vector( struct.unpack('@f',f.read(4))[0], struct.unpack('@f',f.read(4))[0],0)
                        c = Vector( struct.unpack('@f',f.read(4))[0], struct.unpack('@f',f.read(4))[0],0)
                        b = Vector( struct.unpack('@f',f.read(4))[0], struct.unpack('@f',f.read(4))[0],0)
                        d = c
                        f.read(8) # still need to offset the file
                        
                    else:
                        a = Vector( struct.unpack('@f',f.read(4))[0], struct.unpack('@f',f.read(4))[0],0)
                        d = Vector( struct.unpack('@f',f.read(4))[0], struct.unpack('@f',f.read(4))[0],0)
                        c = Vector( struct.unpack('@f',f.read(4))[0], struct.unpack('@f',f.read(4))[0],0)
                        b = Vector( struct.unpack('@f',f.read(4))[0], struct.unpack('@f',f.read(4))[0],0)

                    uvwtag.SetSlow(i,a,b,c,d)

            elif partType ==GoZ_TAG_TEXTURE_MAP_PATH:
                textureMapPath = f.read(partSize-16-1)
            elif partType ==GoZ_TAG_NORMAL_MAP_PATH:
                normalMapPath = f.read(partSize-16-1)
            elif partType ==GoZ_TAG_DISPLACEMENT_MAP_PATH:
                displacementMapPath = f.read(partSize-16-1)
                displacementFactor=modifier* 0.5

            elif partType ==GoZ_TAG_END_OF_FILE:
                break
            #goto next block
            fileOffset += partSize          
        
        
        c4d.StatusClear()
        c4d.StatusSetText(objectName + "Insert Object")
        vDoc.InsertObject(vObj, parentObj,None)
        vObj.SetName(objectName)
        vObj.SetPhong(True,False,1)
        
        vObj[GoZ_CONTAINER_ID] = objectPathStr
        vObj.SetBit(c4d.BIT_ACTIVE)

    c4d.StatusClear()



    
def CreateMaterial(objectName):
    #should add other render engine material ? 
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return
    curMaterial = doc.SearchMaterial(objectName)
    if not curMaterial :
        c4d.CallCommand(13015) #new material
        curMat = doc.GetActiveMaterial()
        curMat.SetName(objectName)
    #apply mat to mesh
    c4d.CallCommand(12169)
    # Sets material properties.
    c4d.CallCommand(16725)  #load material textures
    c4d.CallCommand(16726)  # Unload Textures
    #do we have texture?
    print baseProjectPath, textureMapPath
    if len(textureMapPath) >0:
        curMat[c4d.MATERIAL_USE_COLOR] = True
        bitmap = c4d.BaseList2D(c4d.Xbitmap) 
        bitmap[c4d.BITMAPSHADER_FILENAME] = textureMapPath
        curMat[c4d.MATERIAL_COLOR_SHADER] = bitmap
        curMat.InsertShader(bitmap)


    else:
        sh = curMat[c4d.MATERIAL_COLOR_SHADER]
        sh[c4d.BITMAPSHADER_FILENAME] = ""
        sh.Remove()

    #do we have normal map?
    if len(normalMapPath) > 0:
        curMat[c4d.MATERIAL_USE_NORMAL] = True
        bitmapNormal = c4d.BaseList2D(c4d.Xbitmap) 
        bitmapNormal[c4d.BITMAPSHADER_FILENAME] = normalMapPath
        curMat[c4d.MATERIAL_NORMAL_SHADER] = bitmapNormal
        curMat.InsertShader(bitmapNormal)
        curMat[c4d.MATERIAL_NORMAL_REVERSEX] = False
        curMat[c4d.MATERIAL_NORMAL_REVERSEY] = True
        curMat[c4d.MATERIAL_NORMAL_REVERSEZ] = False
        curMat[c4d.MATERIAL_NORMAL_SWAP] = False
        curMat[c4d.MATERIAL_NORMAL_SPACE] = False
        
    else:
        curMat[c4d.MATERIAL_USE_NORMAL] = False
        sh = curMat[c4d.MATERIAL_NORMAL_SHADER]
        sh[c4d.BITMAPSHADER_FILENAME] = ""
        sh.Remove()

    #do we have disp map?
    if len(displacementMapPath) > 0:
        curMat[c4d.MATERIAL_USE_DISPLACEMENT] = True
        bitmapDisplacement = c4d.BaseList2D(c4d.Xbitmap) 
        bitmapDisplacement[c4d.BITMAPSHADER_FILENAME] = displacementMapPath
        curMat[c4d.MATERIAL_DISPLACEMENT_SHADER] = bitmapDisplacement
        curMat.InsertShader(bitmapDisplacement)
        curMat[c4d.MATERIAL_DISPLACEMENT_SUBPOLY] = True
        curMat[c4d.MATERIAL_DISPLACEMENT_SUBPOLY_ROUND] = True
        curMat[c4d.MATERIAL_DISPLACEMENT_HEIGHT] = displacementFactor * 100
    else:
        curMat[c4d.MATERIAL_USE_DISPLACEMENT] = False
        sh = curMat[c4d.MATERIAL_DISPLACEMENT_SHADER]
        sh[c4d.BITMAPSHADER_FILENAME] = ""
        sh.Remove()



    curMat.Message(c4d.MSG_UPDATE)
    curMat.Update(True, True)
    c4d.CallCommand(12113)  # Deselect All
    c4d.EventAdd(c4d.EVENT_FORCEREDRAW)





def ImportGoZObject(objectPathStr):
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return
    pos = objectPathStr.rfind("/") + 1
    objectName =  objectPathStr[pos:]
    global baseProjectPath
    baseProjectPath = objectPathStr[:pos]
    parentObj = None

    currentObject = doc.SearchObject(objectName)
    if currentObject:
        parentObj = currentObject.GetUp()
        currentObject.Remove()        

    #deselect all 
    c4d.CallCommand(12113);
    # create object from Goz Path
    CreateObjectFromGoZb(objectPathStr, objectName, parentObj)
    #create material for the object
    CreateMaterial(objectName)

def SaveObject(doc, obj , pathStr, file):
    foundPolys = 0
    c4d.StatusClear()
    c4d.StatusSetText(obj.GetName() + " Exporting Object")
    with open(file, "wb" ) as f:
        #f.write(b"GoZb1.0 ZBrush GoZ Binary format. www.ZBrush.com\n")
        st = "GoZb1.0 ZBrush GoZ Binary format. www.ZBrush.com\n"
        f.write( st.encode("raw_unicode_escape"))
        f.seek(32)
        if obj.IsInstanceOf(c4d.Opolygon):
            points = obj.GetAllPoints()
            pointsCount = obj.GetPointCount()
            f.write(struct.pack('@l', GoZ_TAG_POINT_LIST))      #partType
            f.write(struct.pack('@l', 16 + pointsCount*12))     #partSize 
            f.write(struct.pack('@l',pointsCount))              #itemsCount
            f.write(struct.pack('@f',0.0))                        #modifier

            mg = obj.GetMg()
            mat = Matrix()
            mat.Scale(Vector(0.01,0.01,-0.01))
            mat = mat * mg

            #write point list
            if pointsCount:
                foundPolys += 1
            for point in points:
                pt = mat * point
                f.write(struct.pack('@f',pt.x))
                f.write(struct.pack('@f',pt.y))
                f.write(struct.pack('@f',pt.z))
            #write poly list 
            vadr = obj.GetAllPolygons()
            polyCount = obj.GetPolygonCount()
            f.write(struct.pack('@l', GoZ_TAG_FACE4_LIST_FORMAT_1))             #partType
            f.write(struct.pack('@l', 16 + polyCount*16))                     #partSize 
            f.write(struct.pack('@l',polyCount))                                #itemsCount
            f.write(struct.pack('@f',0.0))                                        #modifier
            for poly in vadr:
                if poly.d == poly.c:
                    f.write(struct.pack ('@l',poly.a))
                    f.write(struct.pack ('@l',poly.c))
                    f.write(struct.pack ('@l',poly.b))
                    f.write(struct.pack ('@l',-1))
                else:
                    f.write(struct.pack ('@l',poly.a))
                    f.write(struct.pack ('@l',poly.d))
                    f.write(struct.pack ('@l',poly.c))
                    f.write(struct.pack ('@l',poly.b))
            #write uv
            uvTag = obj.GetTag(c4d.Tuvw)
            if uvTag:
                uvCount = uvTag.GetDataCount()
                polyCount = obj.GetPolygonCount()
                
                vect = Vector()

                f.write(struct.pack('@l', GoZ_TAG_UV4_LIST))                 #partType
                f.write(struct.pack('@l', 16 + uvCount*32))                  #partSize 
                f.write(struct.pack('@l',uvCount))                           #itemsCount
                f.write(struct.pack('@f',0.0))                               #modifier
                for i in xrange(polyCount):
                    uvwDict = uvTag.GetSlow(i)

                    if uvwDict["d"] == uvwDict["c"]:
                        f.write ( struct.pack ('@f',uvwDict["a"].x))
                        f.write ( struct.pack ('@f',uvwDict["a"].y))

                        f.write ( struct.pack ('@f',uvwDict["c"].x))
                        f.write ( struct.pack ('@f',uvwDict["c"].y))

                        f.write ( struct.pack ('@f',uvwDict["b"].x))
                        f.write ( struct.pack ('@f',uvwDict["b"].y))

                        f.write ( struct.pack ('@f',uvwDict["b"].x))
                        f.write ( struct.pack ('@f',uvwDict["b"].y))
                        
                        
                    else:
                        f.write ( struct.pack ('@f',uvwDict["a"].x))
                        f.write ( struct.pack ('@f',uvwDict["a"].y))

                        f.write ( struct.pack ('@f',uvwDict["d"].x))
                        f.write ( struct.pack ('@f',uvwDict["d"].y))

                        f.write ( struct.pack ('@f',uvwDict["c"].x))
                        f.write ( struct.pack ('@f',uvwDict["c"].y))

                        f.write ( struct.pack ('@f',uvwDict["b"].x))
                        f.write ( struct.pack ('@f',uvwDict["b"].y))

            #write texture
            curMaterial = doc.SearchMaterial(obj.GetName)
            if curMaterial:
                pass
                #look for texture
                #look for normal
                #look for displacement
                


        f.write(struct.pack ('@l',GoZ_TAG_END_OF_FILE))

        endFile = array.array('l', [0, 0, 0]) 
        f.write(endFile)
        


        if foundPolys == 0:
            MessageDialog("GoZ Note:\nPlease convert the select object to a polygonal object\nand then click the GoZ button.", c4d.GEMB_OK)
            return  False
        else:
            obj[GoZ_CONTAINER_ID] = pathStr

    return True

def ExportObject (doc, obj):
    if not doc:
        return False
    objectPath = ""
    objectPath = obj[GoZ_CONTAINER_ID]
    objectName = obj.GetName()

    #if the string exist the object is not new    
    if not objectPath:
        print "is new, not yet a Goz Object"
        if not obj.IsInstanceOf(c4d.Opolygon):
            ret = c4d.gui.MessageDialog("GoZ Note:\nThe selected object will be converted to \nan editable object and then sent to ZBrush.", c4d.GEMB_OKCANCEL|c4d.GEMB_ICONEXCLAMATION)
            if not ret:
                return False
            c4d.CallCommand(12113) #deselect all
            doc.SetActiveObject(obj)
            c4d.CallCommand(12236) #makeeditable
            obj = doc.GetActiveObject()

        
        filePath = os.path.join(gGoZBrushPath,"GoZ_ObjectPath.txt")

        with open (filePath , "w") as f :
            f.write(objectName)
        app = os.path.join (gGoZBrushPath, "GoZMakeObjectPath" + gGoZAppExt)
        c4d.storage.GeExecuteProgram(app , gGoZBrushPath)
        
        count = 0
        while 1:
            with open (filePath , "r") as f :
                objectPath = f.read()
            if objectPath and len(objectPath) > len(objectName):
                break
            time.sleep(0.01)
            count +=1
            if count > 10000:
                return False

    else:
        print " - is already an existing GoZ object!"
    

    #check if name changed
    pos = objectPath.rfind("\\") + 1
    objectName =  objectPath[pos:]

    print objectName, obj.GetName()

    if objectName != obj.GetName() : 
        result = MessageDialog ("GoZ Note:\n\""+obj.GetName()+"\" already exists in the current \nGoZBrush project.\nThe object will be renamed \""+objectName+"\"" , c4d.GEMB_OK)
        if result != c4d.GEMB_R_OK:
            return False
        obj.SetName(objectName)
    
    #Export the object to GOZ
    path = objectPath + ".GoZ"
    print "save object"
    if not SaveObject(doc, obj, objectPath, path) : 
        return False
    

    path = gGoZBrushPath +  "GoZ_ObjectList.txt"
    with open (path, "a") as f:
        f.write (objectPath + "\n")
    return True
   


    

def Import():
    start = c4d.GeGetTimer()
    doc =  c4d.documents.GetActiveDocument()
    if not doc:
        return
    path = os.path.join(gGoZBrushPath, "GoZ_ObjectList.txt")
    with open(path) as objectList : 
        for line in objectList:
            if line:
                ImportGoZObject(line.strip('\n\r'))
    print "time to import " , c4d.GeGetTimer() - start

def Export():
    c4d.StatusClear()
    c4d.StatusSetText("Exporting to ZBrush")
    
    doc =  c4d.documents.GetActiveDocument()
    if not doc:
        return
    #Clear the Goz Object List
    file = os.path.join (gGoZBrushPath, "Goz_ObjectList.txt")
    f = open(file, "w")
    f.close()
    

    objList = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_0)
    selCnt = 0
    exportedObjCnt = 0
    if objList:
        selCnt = len(objList)
    for obj in objList:
        if ExportObject(doc, obj):
            exportedObjCnt +=1

    if exportedObjCnt > 0:
        file = os.path.join(gGoZBrushPath, "Goz_Application.txt")
        with open(file, "w") as f:
            f.write ("Cinema4D");
        app = os.path.join (gGoZBrushPath, "GoZBrushFromApp" + gGoZAppExt)
        #command to launch Zbrush
        ##
        ##
        c4d.storage.GeExecuteProgram(app , "")
        ##
        ##


    else:
        MessageDialog("GoZ Note:\nPlease select one or several polygon object(s) and \nthen click the GoZ button.", type=c4d.GEMB_OK|c4d.GEMB_ICONEXCLAMATION)


def PluginMessage(id, data):
    if id == c4d.C4DPL_COMMANDLINEARGS:
        # Extend command line parsing, here
        # This is the last plugin message on Cinema 4D's start process
        if "GoZBrushToCinema4D.CSC" in sys.argv[0]:
            Import()

    return True

class GOZ_Cinema4D_Zbrush(plugins.CommandData):

    def Execute (self, doc):
        '''
        app = os.path.join (gGoZBrushPath, "GoZBrushFromApp" + gGoZAppExt)
        print app
        c4d.storage.GeExecuteProgram(app ,  app)
        return True
        '''

        shift = True
        msg = c4d.BaseContainer()      
        c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.BFM_INPUT_CHANNEL, msg)  
        #if shift is pressend, then force import
        if msg.GetLong(c4d.BFM_INPUT_QUALIFIER) & c4d.QSHIFT:
            #shift pressed
            Import()
        else:
            Export()
        return True


class GOZ_FROMZBRUSH(plugins.CommandData):
    def Execute(self, doc):
        Import()
        return True
        

if __name__ == "__main__":
    # check the cl parameter
    #
    #    main()
    global gGoZBrushPath
    global gGoZAppExt

    if c4d.GeGetCurrentOS() == c4d.OPERATINGSYSTEM_WIN:
        gGoZBrushPath ="C:/Users/Public/Pixologic/GoZBrush/"
        gGoZAppExt = ".exe"
    elif c4d.GeGetCurrentOS() == c4d.OPERATINGSYSTEM_OSX:
        gGoZBrushPath = "/Users/Shared/Pixologic/GoZBrush/"
        gGoZAppExt = ".app"
    else:
        gGoZBrushPath = ""
    
    if gGoZBrushPath != "":
        bmp = bitmaps.BaseBitmap()
        dir, file = os.path.split(__file__)
        fn = os.path.join(dir, "res", "icons", "tozbrush.tif")
        bmp.InitWith(fn) 
        plugins.RegisterCommandPlugin(id=ZBRUSH_GOZ_R20_ID_TOZB, 
                                  str="Export To Zbrush",
                                  info=0,
                                  help="A python goz version", 
                                  dat=GOZ_Cinema4D_Zbrush(),
                                  icon=bmp)

        fn = os.path.join(dir, "res", "icons", "fromzbrush.tif")
        bmp.InitWith(fn) 

        plugins.RegisterCommandPlugin(id=ZBRUSH_GOZ_R20_ID_FROMZB, 
                                  str="Import To ZBrush",
                                  info=0,
                                  help="A python goz version", 
                                  dat=GOZ_FROMZBRUSH(),
                                  icon=bmp)


