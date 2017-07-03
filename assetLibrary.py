import pymel.core as pm
import json
import os, fnmatch
import pprint
from shutil import copyfile
from Qt import QtWidgets, QtCore, QtGui

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

        ssPath = self.previewSaver(assetName, assetDirectory)

        objName = pm.exportSelected(os.path.join(assetDirectory, assetName), type="OBJexport", force=True, options="groups=1;ptgroups=1;materials=1;smoothing=1;normals=1", pr=True, es=True)
        maName = pm.exportSelected(os.path.join(assetDirectory, assetName), type="mayaAscii")

        print "objName", objName
        print "maName", maName
        ## Clean the dups
        pm.delete(slGrp)
        pm.delete(dupMaterialList)
        pm.delete(dupSgList)

        ## Json stuff

        info['assetName'] = assetName
        info['objPath'] = objName
        info['maPath'] = maName
        info['ssPath'] = ssPath
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
        self.clear()
        # first collect all the json files from second level subfolders
        subDirs = next(os.walk(directory))[1]
        allJson = []
        for d in subDirs:
            dir = os.path.join(directory, d)
            for file in os.listdir(dir):
                if file.endswith(".json"):
                    # assetName, ext = os.path.splitext(file)
                    file = os.path.join(dir, file)
                    allJson.append(file)
                    with open(file, 'r') as f:
                        # The JSON module will read our file, and convert it to a python dictionary
                        data = json.load(f)
                        print data
                        name = data["assetName"]
                        self[name] = data


        # print allJson
        # self[assetName] = "HEDE"
        # self[assetName] = data
        # for j in allJson:
        #     with open(infoFile, 'r') as f:
        #         # The JSON module will read our file, and convert it to a python dictionary
        #         data = json.load(f)

    def importAsset(self, name):
        # print "HERE"
        path = self[name]['maPath']
        # print path
        # We tell the file command to import, and tell it to not use any nameSpaces
        # pm.file(path, i=True, usingNamespaces=False)
        pm.importFile(path)

    def previewSaver(self, name, assetDirectory):
        sel = pm.ls(sl=True)
        thumbPath = os.path.join(assetDirectory, '%s_thumb.jpg' % name)
        SSpath = os.path.join(assetDirectory, '%s_s.jpg' % name)
        WFpath = os.path.join(assetDirectory, '%s_w.jpg' % name)

        # make sure the viewport display is suitable
        panel = pm.getPanel(wf=True)

        if pm.getPanel(to=panel) != "modelPanel":
            pm.warning("The focus is not on a model panel, using the perspective view")
            panel = pm.getPanel(wl="Persp View")
            # Somehot wl dont return a regular string, convert it to a regular string
            t = ""
            for z in panel:
                t += z
            panel = t

        pm.modelEditor(panel, e=1, allObjects=1)
        pm.modelEditor(panel, e=1, da="smoothShaded")
        pm.modelEditor(panel, e=1, displayTextures=1)
        pm.modelEditor(panel, e=1, wireframeOnShaded=0)
        pm.viewFit()

        pm.isolateSelect(panel, state=1)
        pm.isolateSelect(panel, addSelected=True)
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


        pm.isolateSelect(panel, state=0)
        pm.isolateSelect(panel, removeSelected = True)

        # TODO // store the scene defaults (camera position, imageFormat, etc.

        return thumbPath


class ControllerLibraryUI(QtWidgets.QDialog):

    def __init__(self):
        # super is an interesting function
        # It gets the class that our class is inheriting from
        # This is called the superclass
        # The reason is that because we redefined __init__ in our class, we no longer call the code in the super's init
        # So we need to call our super's init to make sure we are initialized like it wants us to be
        super(ControllerLibraryUI, self).__init__()

        # We set our window title
        self.setWindowTitle('Asset Library UI')

        # We store our library as a variable that we can access from inside us
        self.library = assetLibrary()

        # Finally we build our UI
        self.buildUI()

    def buildUI(self):
        # Just like we made a column layout in the last UI, in Qt we have a vertical box layout
        # We tell it that we want to apply the layout to this class (self)
        layout = QtWidgets.QVBoxLayout(self)

        # We want to make another widget to store our controls to save the controller
        # A widget is what we call a UI element
        saveWidget = QtWidgets.QWidget()
        # Every widget needs a layout. We want a Horizontal Box Layout for this one, and tell it to apply to our widget
        saveLayout = QtWidgets.QHBoxLayout(saveWidget)
        # Finally we add this widget to our main widget
        layout.addWidget(saveWidget)

        # Our first order of business is to have a text box that we can enter a name
        # In Qt this is called a LineEdit
        self.searchNameField = QtWidgets.QLineEdit()
        # We will then add this to our layout for our save controls
        self.searchNameField.textEdited.connect(self.populate)
        saveLayout.addWidget(self.searchNameField)

        # # We add a button to call the save command
        # saveBtn = QtWidgets.QPushButton('Save')
        # # When the button is clicked it fires a signal
        # # A signal can be connected to a function
        # # So when the button is called, it will call the function that is given.
        # # In this case, we tell it to call the save method
        # saveBtn.clicked.connect(self.save)
        # # and then we add it to our save layout
        # saveLayout.addWidget(saveBtn)

        # Now we'll set up the list of all our items
        # The size is for the size of the icons we will display
        size = 64
        # First we create a list widget, this will list all the items we give it
        self.listWidget = QtWidgets.QListWidget()
        # We want the list widget to be in IconMode like a gallery so we set it to a mode
        self.listWidget.setViewMode(QtWidgets.QListWidget.IconMode)
        # We set the icon size of this list
        self.listWidget.setIconSize(QtCore.QSize(size, size))
        # then we set it to adjust its position when we resize the window
        self.listWidget.setResizeMode(QtWidgets.QListWidget.Adjust)
        # Finally we set the grid size to be just a little larger than our icons to store our text label too
        self.listWidget.setGridSize(QtCore.QSize(size+12, size+12))
        # And finally, finally, we add it to our main layout
        layout.addWidget(self.listWidget)

        # Now we need a layout to store our buttons
        # So first we create a widget to store this layout
        btnWidget = QtWidgets.QWidget()
        # We create another horizontal layout and tell it to apply to our btn widdget
        btnLayout = QtWidgets.QHBoxLayout(btnWidget)
        # And we add this widget to our main UI
        layout.addWidget(btnWidget)

        # Similar to above we create three buttons
        importBtn = QtWidgets.QPushButton('Import!')
        # And we connect it to the relevant functions
        importBtn.clicked.connect(self.load)
        # And finally we add them to the button layout
        btnLayout.addWidget(importBtn)

        refreshBtn = QtWidgets.QPushButton('Refresh')
        refreshBtn.clicked.connect(self.populate)
        btnLayout.addWidget(refreshBtn)

        exportBtn = QtWidgets.QPushButton('Export')
        # exportBtn.clicked.connect(self.save)
        exportBtn.clicked.connect(self.export)
        btnLayout.addWidget(exportBtn)

        # After all that, we'll populate our UI
        self.populate()

    def export(self):
        # self.exportWindow = QtWidgets.QDialog()
        # self.exportWindow.setWindowTitle('hoyt')
        # self.exportWindow.resize(200,150)
        exportWindow, ok = QtWidgets.QInputDialog.getText(self, 'Text Input Dialog', 'Enter Asset Name:')
        if ok:
            name = str(exportWindow)
            if not name.strip():
                pm.warning("You must give a name!")
                return
            self.library.saveAsset(name)
            self.populate()
        # self.exportWindow.show()

    def load(self):
        # We will ask the listWidget what our currentItem is
        currentItem = self.listWidget.currentItem()

        # If we don't have anything selected, it will tell us None is selected, so we can skip this method
        if not currentItem:
            return

        # We then get the text label of the current item. This will be the name of our control
        name = currentItem.text()
        # Then we tell our library to load it
        self.library.importAsset(name)

    # def filter(self):
    #     filterWord = self.saveNameField.text()
    #     self.listWidget.clear()
    #     self.library.scan()

    def save(self):
        # We start off by getting the name in the text field
        name = self.searchNameField.text()

        # If the name is not given, then we will not continue and we'll warn the user
        # The strip method will remove empty characters from the string, so that if the user entered spaces, it won't be valid
        if not name.strip():
            pm.warning("You must give a name!")
            return

        # We use our library to save with the given name
        self.library.saveAsset(name)
        # Then we repopulate our UI with the new data
        self.populate()
        # And finally, lets remove the text in the name field so that they don't accidentally overwrite the file
        self.searchNameField.setText('')

    def populate(self):

        # use the word in saveNameField as the filter
        filterWord = self.searchNameField.text()



        # This function will be used to populate the UI. Shocking. I know.

        # First lets clear all the items that are in the list to start fresh
        self.listWidget.clear()

        # Then we ask our library to find everything again in case things changed
        self.library.scan()
        # Now we iterate through the dictionary
        # This is why I based our library on a dictionary, because it gives us all the nice tricks a dictionary has
        for name, info in self.library.items():

            # if there is a filterword, filter the item
            if filterWord != "" and filterWord not in name:
                continue


            # We create an item for the list widget and tell it to have our controller name as a label
            item = QtWidgets.QListWidgetItem(name)

            # We set its tooltip to be the info from the json
            # The pprint.pformat will format our dictionary nicely
            item.setToolTip(pprint.pformat(info))

            # Finally we check if there's a screenshot available
            screenshot = info.get('ssPath')
            # If there is, then we will load it
            if screenshot:
                # So first we make an icon with the path to our screenshot
                icon = QtGui.QIcon(screenshot)
                # then we set the icon onto our item
                item.setIcon(icon)

            # Finally we add our item to the list
            self.listWidget.addItem(item)

# This is a convenience function to display our UI
def showUI():
    # Create an instance of our UI
    ui = ControllerLibraryUI()
    # Show the UI
    ui.show()
    # Return the ui instance so people using this function can hold on to it
    return ui


