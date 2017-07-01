import pymel.core as pm
import json
import os, fnmatch
import pprint
from shutil import copyfile

DIRECTORY = os.path.normpath("M:\Projects\_easyacces")


def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


class assetLibrary(dict):

##### TEMPORARY #####
    # assetName = "test"

    def __init__(self, directory=DIRECTORY):
        if not os.path.exists(directory):
            pm.error("Cannot reach the easy access directory")

    def saveAsset(self, assetName, screenshot=True, directory=DIRECTORY, moveCenter=True, **info):

        assetDirectory = os.path.join(directory,assetName)
        print "assetDirectory", assetDirectory

        selection = pm.ls(sl=True, type="transform")
        if len(selection) == 0:
            return

        if not os.path.exists(assetDirectory):
            os.mkdir(assetDirectory)

        materialList=[]
        dupMaterialList=[]
        dupSgList=[]
        dupObjList=[]
        fileTextures=[]

        # TODO // Duplicate the shading network of selected object.
        for obj in selection:
            # TODO // Duplicate each selected object with the option of current state or non-deformed state
            # TODO // zero out deformer and skin bind envelopes for each object (optional)
            # TODO // duplicate and unlock the transformations if locked
            dupObj = pm.duplicate(obj)
            dupObjList.append(dupObj)
            objSG = obj.shadingGroups()

            # if there is no shading group, skip the iteration
            if objSG == []:
                continue
            objMaterial = pm.ls(pm.listConnections(objSG[0]),materials=True)

            ## if this material is not before duplicated:
            if not objMaterial in materialList:

                # find the file nodes used
                print objMaterial
                if objMaterial[0] == "lambert1":
                    continue # if it is the default material, skip that
                dupMaterial=pm.duplicate(objMaterial, ic=True)
                sg = pm.sets(renderable=1, noSurfaceShader=1, empty=1, name=dupMaterial[0] + '_SG')
                pm.connectAttr(dupMaterial[0] + ".outColor", sg + ".surfaceShader", force=1)
                fileNodes=pm.listConnections(dupMaterial, type="file")
                    # copy the files in filenode to the asset directory

                for file in fileNodes:
                    fullPath = os.path.normpath(pm.getAttr(file.fileTextureName))
                    filePath, fileBase = os.path.split(fullPath)
                    newLocation = os.path.join(assetDirectory, fileBase)

                    if fullPath == newLocation:
                        print "File Node copy skipped"
                        continue
                    # print "PATHS", fullPath, newLocation
                    copyfile(fullPath, newLocation)

                    pm.setAttr(file.fileTextureName,newLocation)
                    fileTextures.append(newLocation)

                materialList.append(objMaterial)
                dupMaterialList.append(dupMaterial)
                dupSgList.append(sg)
            ## if the same material is used before do not duplicate it again, use the previous one.
            else:
                materialIndex = materialList.index(objMaterial)
                dupMaterial = dupMaterialList[materialIndex]


            # testBlinn = pm.shadingNode('blinn', asShader=True)
            pm.select(dupObj)
            # pm.hyperShade(assign=dupMaterial)
            # pm.sets(dupMaterial, forceElement=True)


            pm.hyperShade(assign=dupMaterial[0])

        if moveCenter:
            pm.select(dupObjList)
            slGrp = pm.group(name=assetName)

            pm.xform(slGrp, cp=True)

            tempLoc = pm.spaceLocator()
            tempPo = pm.pointConstraint(tempLoc, slGrp)
            pm.delete(tempPo)
            pm.delete(tempLoc)

        pm.select(dupObjList)

        ssPaths = self.previewSaver(assetName, assetDirectory)

        pm.exportSelected(os.path.join(assetDirectory, assetName), type="OBJexport", force=True, options="groups=1;ptgroups=1;materials=1;smoothing=1;normals=1", pr=True, es=True)
        pm.exportSelected(os.path.join(assetDirectory, assetName), type="mayaAscii")

        ## Clean the dups
        pm.delete(slGrp)
        pm.delete(dupMaterialList)
        pm.delete(dupSgList)

        ## Json stuff

        info['assetName'] = assetName
        info['path'] = assetDirectory
        info['textureFiles'] = fileTextures

        propFile = os.path.join(assetDirectory, "%s.json" % assetName)

        with open (propFile, "w") as f:
            json.dump(info, f, indent=4)

        # TODO // Save the Screenshots and uv snapshots to the directory
        # TODO // Write the json file:
            # TODO // -- Library database name (will be the same with the obj file name)
            # TODO // -- Polygon count
            # TODO // -- Texture file (name and/or path)
            # TODO // -- Screenshot Path
            # TODO // -- Wireframe SS path
            # TODO // -- UVsnapShot Path
        # TODO // Delete the duplicated object and its dup shading network

        self[assetName] = info

    def scan(self, directory=DIRECTORY):
        if not os.path.exists(directory):
            return

        # first collect all the json files from second level subfolders
        subDirs = next(os.walk(directory))[1]
        allJson = []
        for d in subDirs:
            dir = os.path.join(directory, d)
            for file in os.listdir(dir):
                if file.endswith(".json"):
                    assetName, ext = os.path.splitext(file)
                    file = os.path.join(dir, file)
                    allJson.append(file)
                    with open(file, 'r') as f:
                        # The JSON module will read our file, and convert it to a python dictionary
                        data = json.load(f)
                        print data
                        self[assetName] = data


        # print allJson
        # self[assetName] = "HEDE"
        # self[assetName] = data
        # for j in allJson:
        #     with open(infoFile, 'r') as f:
        #         # The JSON module will read our file, and convert it to a python dictionary
        #         data = json.load(f)



    def importAsset(self, name):
        pass

    def previewSaver(self, name, assetDirectory):
        sel = pm.ls(sl=True)
        thumbPath = os.path.join(assetDirectory, '%s_thumb.jpg' % name)
        SSpath = os.path.join(assetDirectory, '%s_s.jpg' % name)
        WFpath = os.path.join(assetDirectory, '%s_w.jpg' % name)

        # make sure the viewport display is suitable
        panel = pm.getPanel(wf=1)
        pm.modelEditor(panel, e=1, allObjects=1)
        pm.modelEditor(panel, e=1, da="smoothShaded")
        pm.modelEditor(panel, e=1, displayTextures=1)
        pm.modelEditor(panel, e=1, wireframeOnShaded=0)
        pm.viewFit()

        currentPanel = pm.getPanel(wf=True)
        pm.isolateSelect(currentPanel, state=1)
        pm.isolateSelect(currentPanel, addSelected=True)
        #temporarily deselect
        pm.select(d=True)
        pm.setAttr("defaultRenderGlobals.imageFormat", 8)  # This is the value for jpeg

        # thumb
        pm.playblast(completeFilename=thumbPath, forceOverwrite=True, format='image', width=200, height=200,
                       showOrnaments=False, startTime=1, endTime=1, viewer=False)

        # screenshot
        pm.playblast(completeFilename=SSpath, forceOverwrite=True, format='image', width=1600, height=1600,
                       showOrnaments=False, startTime=1, endTime=1, viewer=False)

        # Wireframe
        pm.modelEditor(panel, e=1, displayTextures=0)
        pm.modelEditor(panel, e=1, wireframeOnShaded=1)
        pm.playblast(completeFilename=WFpath, forceOverwrite=True, format='image', width=1600, height=1600,
                       showOrnaments=False, startTime=1, endTime=1, viewer=False)

        pm.select(sel)
        # UV Snapshot -- It needs
        for i in range (0, len(sel)):
            objName = sel[i].name()
            UVpath = os.path.join(assetDirectory, '%s_uv.jpg' % objName)
            pm.select(sel[i])
            pm.uvSnapshot(o=True, ff="jpg", n=UVpath, xr=1600, yr=1600)


        pm.isolateSelect(currentPanel, state=0)
        pm.isolateSelect(currentPanel, removeSelected = True)

        # TODO // store the scene defaults (camera position, imageFormat, etc.

        return thumbPath


