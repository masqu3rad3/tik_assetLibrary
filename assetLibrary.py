import pymel.core as pm
import json
import os, fnmatch
import pprint
from shutil import copyfile
import Qt
import logging
from Qt import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui

logging.basicConfig()
logger = logging.getLogger('AssetLibrary')
logger.setLevel(logging.DEBUG)

if Qt.__binding__ == "PySide":
    logger.debug('Using PySide with shiboken')
    from shiboken import wrapInstance
    from Qt.QtCore import Signal
elif Qt.__binding__.startswith('PyQt'):
    logger.debug('Using PyQt with sip')
    from sip import wrapinstance as wrapInstance
    from Qt.Core import pyqtSignal as Signal
else:
    logger.debug('Using PySide2 with shiboken')
    from shiboken2 import wrapInstance
    from Qt.QtCore import Signal

DIRECTORY = os.path.normpath("M:\Projects\_AssetLibrary")


def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


class assetLibrary(dict):
    """
    Asset Library Logical operations Class. This Class holds the main functions (save,import,scan)
    """

    ##### TEMPORARY #####
    # assetName = "test"

    def __init__(self, directory=DIRECTORY):
        if not os.path.exists(directory):
            pm.error("Cannot reach the easy access directory")

    def saveAsset(self, assetName, screenshot=True, directory=DIRECTORY, moveCenter=False, **info):
        """
        Saves the selected object(s) as an asset into the predefined library
        Args:
            assetName: (Unicode) Asset will be saved as with this name
            screenshot: (Bool) If true, screenshots (Screenshot, Thumbnail, Wireframe, UV Snapshots) will be taken with playblast. Default True
            directory: (Unicode) Default Library location. Default is predefined outside of this class
            moveCenter: (Bool) If True, selected object(s) will be moved to World 0 point. Pivot will be the center of selection. Default False
            **info: (Any) Extra information which will be hold in the .json file

        Returns:
            None

        """
        originalPath = pm.sceneName()
        # Save scene as to prevent fatal problems
        # if not originalPath == "":
        #     sceneFolder, sceneName = os.path.split(originalPath)
        #     sceneNameBase, sceneNameExt = os.path.splitext(sceneName)
        #     newSceneName = "{0}{1}{2}".format(sceneNameBase, "_TMP", sceneNameExt)
        #     newScenePath = os.path.join(sceneFolder, newSceneName)
        #     pm.saveAs(newScenePath)

        assetDirectory = os.path.join(directory, assetName)

        ## TODO // in a scenario where a group object selected, select all meshes under the group recursively (you did that before somewhere else)
        selection = pm.ls(sl=True, type="transform")
        if len(selection) == 0:
            pm.warning("No object selected, nothing to do")
            return

        if not os.path.exists(assetDirectory):
            os.mkdir(assetDirectory)

        possibleFileHolders = pm.listRelatives(selection, ad=True, type=["mesh", "nurbsSurface"])

        allFileTextures = []
        for obj in possibleFileHolders:
            fileNodes = self.findFileNodes(obj)
            fileTextures = self.filePass(fileNodes, assetDirectory)
            allFileTextures += fileTextures

        allFileTextures = self.makeUnique(allFileTextures)

        if moveCenter:
            pm.select(selection)
            slGrp = pm.group(name=assetName)

            pm.xform(slGrp, cp=True)

            tempLoc = pm.spaceLocator()
            tempPo = pm.pointConstraint(tempLoc, slGrp)
            pm.delete(tempPo)
            pm.delete(tempLoc)

        thumbPath, ssPath, swPath = self.previewSaver(assetName, assetDirectory)

        pm.select(selection)
        objName = pm.exportSelected(os.path.join(assetDirectory, assetName), type="OBJexport", force=True,
                                    options="groups=1;ptgroups=1;materials=1;smoothing=1;normals=1", pr=True, es=True)
        maName = pm.exportSelected(os.path.join(assetDirectory, assetName), type="mayaAscii")

        ## Json stuff

        info['assetName'] = assetName
        info['objPath'] = self.pathOps(objName, "basename")
        info['maPath'] = self.pathOps(maName, "basename")
        info['thumbPath'] = self.pathOps(thumbPath, "basename")
        info['ssPath'] = self.pathOps(ssPath, "basename")
        info['swPath'] = self.pathOps(swPath, "basename")
        info['textureFiles'] = allFileTextures
        info['Faces/Trianges'] = ("%s/%s" % (str(pm.polyEvaluate(f=True)), str(pm.polyEvaluate(t=True))))
        info['sourceProject'] = originalPath

        # query the number of faces
        pm.polyEvaluate(f=True)
        # Result: 16

        # query the number of triangles
        pm.polyEvaluate(t=True)

        propFile = os.path.join(assetDirectory, "%s.json" % assetName)

        with open(propFile, "w") as f:
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

        ## TODO // REVERT BACK
        # if not originalPath == "":
        #     pm.openFile(originalPath, force=True)
        #     os.remove(newScenePath)

    def scan(self, directory=DIRECTORY):
        """
        Scans the directory for .json files, and gather info.
        Args:
            directory: (Unicode) Default Library location. Default is predefined outside of this class

        Returns:
            None

        """
        if not os.path.exists(directory):
            return
        self.clear()
        # first collect all the json files from second level subfolders
        subDirs = next(os.walk(directory))[1]

        # subDirs= (subDirs.sort())
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
                        name = data["assetName"]
                        self[name] = data

                        # self[assetName] = "HEDE"
                        # self[assetName] = data
                        # for j in allJson:
                        #     with open(infoFile, 'r') as f:
                        #         # The JSON module will read our file, and convert it to a python dictionary
                        #         data = json.load(f)

    def importAsset(self, name, copyTextures, directory=DIRECTORY):
        """
        Imports the selected asset into the current scene
        
        Args:
            name: (Unicode) Name of the asset which will be imported 
            copyTextures: (Bool) If True, all texture files of the asset will be copied to the current project directory

        Returns:
            None

        """
        path = os.path.join(directory, self[name]['assetName'], self[name]['maPath'])

        textureList = self[name]['textureFiles']
        pm.importFile(path)

        ## if there are not textures files to handle, do not waste time
        if len(textureList) == 0 or copyTextures is False:
            return

        currentProjectPath = os.path.normpath(pm.workspace.path)
        sourceImagesPath = os.path.join(currentProjectPath, "sourceimages")
        ## check if the sourceimages folder exists:
        if not os.path.exists(sourceImagesPath):
            os.mkdir(sourceImagesPath)

        fileNodes = pm.ls(type="file")
        for texture in textureList:
            path = os.path.join(directory, self[name]['assetName'], texture)
            ## find the textures file Node
            for file in fileNodes:
                if os.path.normpath(pm.getAttr(file.fileTextureName)) == path:
                    filePath, fileBase = os.path.split(path)
                    newLocation = os.path.join(sourceImagesPath, name)
                    if not os.path.exists(newLocation):
                        os.mkdir(newLocation)
                    newPath = os.path.normpath(os.path.join(newLocation, fileBase))
                    print "path", path
                    print "newPath", newPath
                    copyfile(path, newPath)
                    pm.setAttr(file.fileTextureName, newPath)

    def previewSaver(self, name, assetDirectory):
        """
        Saves the preview files under the Asset Directory
        Args:
            name: (Unicode) Name of the Asset
            assetDirectory: (Unicode) Directory of Asset

        Returns:
            (Tuple) Thumbnail path, Screenshot path, Wireframe path

        """
        selection = pm.ls(sl=True)

        validShapes = pm.listRelatives(selection, ad=True, type=["mesh", "nurbsSurface"])
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
        # temporarily deselect
        pm.select(d=True)
        pm.setAttr("defaultRenderGlobals.imageFormat", 8)  # This is the value for jpeg

        frame = pm.currentTime(query=True)
        # thumb
        pm.playblast(completeFilename=thumbPath, forceOverwrite=True, format='image', width=200, height=200,
                     showOrnaments=False, frame=[frame], viewer=False)

        # screenshot
        pm.playblast(completeFilename=SSpath, forceOverwrite=True, format='image', width=1600, height=1600,
                     showOrnaments=False, frame=[frame], viewer=False)

        # Wireframe
        pm.modelEditor(panel, e=1, displayTextures=0)
        pm.modelEditor(panel, e=1, wireframeOnShaded=1)
        pm.playblast(completeFilename=WFpath, forceOverwrite=True, format='image', width=1600, height=1600,
                     showOrnaments=False, frame=[frame], viewer=False)

        pm.select(selection)
        # UV Snapshot -- It needs

        for i in range(0, len(validShapes)):
            transformNode = pm.listRelatives(validShapes[i], p=True, type="transform")[0]
            print "transformNode", transformNode
            objName = transformNode.name()
            UVpath = os.path.join(assetDirectory, '%s_uv.jpg' % objName)
            pm.select(transformNode)
            pm.uvSnapshot(o=True, ff="jpg", n=UVpath, xr=1600, yr=1600)

        pm.isolateSelect(panel, state=0)
        pm.isolateSelect(panel, removeSelected=True)

        # TODO // store the scene defaults (camera position, imageFormat, etc.

        return thumbPath, SSpath, WFpath

    def filePass(self, fileNodes, newPath):
        textures = []
        for file in fileNodes:
            fullPath = os.path.normpath(pm.getAttr(file.fileTextureName))
            filePath, fileBase = os.path.split(fullPath)
            newLocation = os.path.join(newPath, fileBase)
            if fullPath == newLocation:
                pm.warning("File Node copy skipped")
                textureName = self.pathOps(newLocation, "basename")
                textures.append(textureName)
                continue
            copyfile(fullPath, newLocation)
            pm.setAttr(file.fileTextureName, newLocation)
            textureName = self.pathOps(newLocation, "basename")
            textures.append(textureName)
        return textures

    def findFileNodes(self, shape):
        print "shape:", shape
        def checkInputs(node):
            inputNodes = node.inputs()
            if len(inputNodes) == 0:
                return []
            else:
                return inputNodes
        # geo = obj.getShape()
        # Get the shading group from the selected mesh
        try:
            sg = shape.outputs(type='shadingEngine')[0]
        except:
            # if there is no sg, return en empty list
            return []
        objMaterial = pm.ls(pm.listConnections(sg), materials=True)
        everyInput = []
        nextInputs = objMaterial
        # iterCount = 0
        while nextInputs != []:
            # iterCount += 1
            everyInput += nextInputs
            tempInputs = []
            for i in nextInputs:
                tempInputs += checkInputs(i)
            nextInputs = tempInputs
        everyInput = self.makeUnique(everyInput)
        fileNodes = pm.ls(everyInput, type="file")
        return fileNodes

    def makeUnique(self, fList):
        keys = {}
        for e in fList:
            keys[e] = 1
        return keys.keys()

    def pathOps(self, fullPath, mode):
        """
        performs basic path operations.
        Args:
            fullPath: (Unicode) Absolute Path
            mode: (String) Valid modes are 'path', 'basename', 'filename', 'extension', 'drive'

        Returns:
            Unicode

        """
        if mode == "drive":
            drive = os.path.splitdrive(fullPath)
            return drive

        path, basename = os.path.split(fullPath)
        if mode == "path":
            return path
        if mode == "basename":
            return basename
        filename, ext = os.path.splitext(basename)
        if mode == "filename":
            return filename
        if mode == "extension":
            return ext



def getMayaMainWindow():
    """
    Gets the memory adress of the main window to connect Qt dialog to it.
    Returns:
        (long) Memory Adress
    """
    ## This will give the memory adress of the main window
    win = omui.MQtUtil_mainWindow()
    ## put memory adress into a long integer and wrap it as QMainWindow
    ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr


class AssetLibraryUI(QtWidgets.QDialog):
    """
    UI Class for Asset Library
    """
    viewModeState = 1
    directory = DIRECTORY
    _instance = None
    # def __new__ (cls, force = False):
    #      if not force and AssetLibraryUI._instance:
    #          return AssetLibraryUI._instance
    #      AssetLibraryUI._instance = super (AssetLibraryUI, cls).__new__ (cls)
    #      return AssetLibraryUI._instance

    def __init__(self):


        # super is an interesting function
        # It gets the class that our class is inheriting from
        # This is called the superclass
        # The reason is that because we redefined __init__ in our class, we no longer call the code in the super's init
        # So we need to call our super's init to make sure we are initialized like it wants us to be
        # me=self
        for entry in QtWidgets.QApplication.allWidgets():
            if entry.objectName() == "assetLib":
                # print entry
                entry.close()

        parent = getMayaMainWindow()

        super(AssetLibraryUI, self).__init__(parent=parent)

        # We set our window title
        self.setWindowTitle('Asset Library UI')
        self.setObjectName("assetLib")

        # We store our library as a variable that we can access from inside us
        self.library = assetLibrary()

        # Finally we build our UI

        self.buildUI()


    def buildUI(self):
        """
        Main Dialog Window
        Returns:
            None
        """
        layout = QtWidgets.QVBoxLayout(self)

        # We want to make another widget to store our controls to save the controller
        # A widget is what we call a UI element
        searchWidget = QtWidgets.QWidget()
        # Every widget needs a layout. We want a Horizontal Box Layout for this one, and tell it to apply to our widget
        searchLayout = QtWidgets.QHBoxLayout(searchWidget)
        # Finally we add this widget to our main widget
        layout.addWidget(searchWidget)

        # Our first order of business is to have a text box that we can enter a name
        # In Qt this is called a LineEdit
        self.searchLabel = QtWidgets.QLabel("Seach Filter: ")
        searchLayout.addWidget(self.searchLabel)
        self.searchNameField = QtWidgets.QLineEdit()
        # We will then add this to our layout for our save controls
        self.searchNameField.textEdited.connect(self.populate)
        searchLayout.addWidget(self.searchNameField)

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
        self.size = 64
        # First we create a list widget, this will list all the items we give it
        self.listWidget = QtWidgets.QListWidget()
        # We want the list widget to be in IconMode like a gallery so we set it to a mode
        self.listWidget.setViewMode(QtWidgets.QListWidget.IconMode)
        self.listWidget.setMinimumSize(350, 600)
        # We set the icon size of this list
        self.listWidget.setIconSize(QtCore.QSize(self.size, self.size))
        # self.listWidget.setSortingEnabled(True)
        self.listWidget.setMovement(QtWidgets.QListView.Static)
        self.listWidget.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.listWidget.setGridSize(QtCore.QSize(self.size *1.2, self.size *1.4))
        # And finally, finally, we add it to our main layout
        layout.addWidget(self.listWidget)
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.on_context_menu)
        self.popMenu = QtWidgets.QMenu(self)

        ssAction = QtWidgets.QAction('Show Screenshot', self)
        self.popMenu.addAction(ssAction)
        ssAction.triggered.connect(lambda item='ssPath': self.actionTrigger(item))

        swAction = QtWidgets.QAction('Show Wireframe', self)
        self.popMenu.addAction(swAction)
        swAction.triggered.connect(lambda item='swPath': self.actionTrigger(item))

        self.popMenu.addSeparator()

        importWithCopyAction = QtWidgets.QAction('Import and Copy Textures', self)
        self.popMenu.addAction(importWithCopyAction)
        importWithCopyAction.triggered.connect(lambda item='importWithCopy': self.actionTrigger(item))

        importOnlyAction = QtWidgets.QAction('Import Model', self)
        self.popMenu.addAction(importOnlyAction)
        importOnlyAction.triggered.connect(lambda item='importOnly': self.actionTrigger(item))

        # sUvAction = QtWidgets.QAction('Show UV snapshot', self)
        # self.popMenu.addAction(sUvAction)
        # sUvAction.triggered.connect(lambda item=sUvAction.text(): self.actionTrigger(item))

        self.popMenu.addSeparator()

        self.viewAsListAction = QtWidgets.QAction('View As List', self)
        self.popMenu.addAction(self.viewAsListAction)
        self.viewAsListAction.triggered.connect(lambda item='viewModeChange': self.actionTrigger(item))


        self.popMenu.addSeparator()

        openFolderAction = QtWidgets.QAction('Open folder in explorer', self)
        self.popMenu.addAction(openFolderAction)
        openFolderAction.triggered.connect(lambda item='openFolder': self.actionTrigger(item))

        # Now we need a layout to store our buttons
        # So first we create a widget to store this layout
        btnWidget = QtWidgets.QWidget()
        # We create another horizontal layout and tell it to apply to our btn widdget
        btnLayout = QtWidgets.QHBoxLayout(btnWidget)
        # And we add this widget to our main UI
        layout.addWidget(btnWidget)

        # Similar to above we create three buttons
        importBtn = QtWidgets.QPushButton('Import')
        # And we connect it to the relevant functions
        importBtn.clicked.connect(lambda cp_txt=True: self.load(cp_txt))
        # And finally we add them to the button layout
        btnLayout.addWidget(importBtn)

        refreshBtn = QtWidgets.QPushButton('Refresh')
        refreshBtn.clicked.connect(self.populate)
        btnLayout.addWidget(refreshBtn)

        self.exportBtn = QtWidgets.QPushButton('Export')
        # exportBtn.clicked.connect(self.save)
        self.exportBtn.clicked.connect(self.export)
        btnLayout.addWidget(self.exportBtn)

        shortcutExport =Qt.QtWidgets.QShortcut(Qt.QtGui.QKeySequence("Ctrl+E"), self, self.export)
        shortcutImport = Qt.QtWidgets.QShortcut(Qt.QtGui.QKeySequence("Ctrl+I"), self, lambda val=True: self.load(val))
        scIncreaseIconSize = Qt.QtWidgets.QShortcut(Qt.QtGui.QKeySequence("Ctrl++"), self, lambda val=10: self.adjustIconSize(val))
        scDecreaseIconSize = Qt.QtWidgets.QShortcut(Qt.QtGui.QKeySequence("Ctrl+-"), self, lambda val=-10: self.adjustIconSize(val))

        self.populate()

    def adjustIconSize(self, value):
        self.size += value
        self.listWidget.setIconSize(QtCore.QSize(self.size, self.size))
        self.listWidget.setGridSize(QtCore.QSize(self.size *1.2, self.size *1.4))


    def actionTrigger(self, item):
        """
        Triggers certain tasks for right click menu items of assets
        Args:
            item: (Unicode) This may be custom commands (Currently only 'openFolder') or valid dictionary item keys (ssPath, swPath...)

        Returns:
            None

        """
        # logger.debug(item)
        currentItem = self.listWidget.currentItem()
        name = currentItem.text()
        info = self.library[name]

        if item == 'openFolder':
            asset = info.get('assetName')
            path = os.path.join(self.directory, asset)
            os.startfile(path)
        elif item == 'importWithCopy':
            self.load(True)
        elif item == 'importOnly':
            self.load(False)
        elif item == 'viewModeChange':
            self.viewModeState = self.viewModeState * -1
            if self.viewModeState == 1:
                self.viewAsListAction.setText("View As List")
                self.listWidget.setViewMode(QtWidgets.QListWidget.IconMode)
            elif self.viewModeState == -1:
                self.viewAsListAction.setText("View As Icons")
                self.listWidget.setViewMode(QtWidgets.QListWidget.ListMode)
        else:
            ss = info.get(item)
            asset = info.get('assetName')
            ssPath = os.path.join(self.directory, asset, ss)
            os.startfile(ssPath)

    def on_context_menu(self, point):
        # show context menu
        self.popMenu.exec_(self.listWidget.mapToGlobal(point))

    def export(self):
        """
        UI Export function - links to the assetLibrary.saveAsset()
        Returns:
            None

        """
        # self.exportWindow = QtWidgets.QDialog()
        # self.exportWindow.setWindowTitle('hoyt')
        # self.exportWindow.resize(200,150)
        exportWindow, ok = QtWidgets.QInputDialog.getText(self, 'Text Input Dialog',
                                                          'SAVE BEFORE PROCEED\n\nANY UNSAVED WORK WILL BE LOST\n\nEnter Asset Name:')
        if ok:
            name = str(exportWindow)
            logger.debug(name.strip())
            # assert name.strip() == False, "You must give a name!"
            if not name.strip():
                pm.warning("You must give a name!")
                return
            self.library.saveAsset(name)
            self.populate()
            # self.exportWindow.show()

    def load(self, copy_textures):
        """
        UI Import Function - links to the assetLibrary.importAsset()
        Returns:
            None

        """
        # We will ask the listWidget what our currentItem is
        currentItem = self.listWidget.currentItem()

        # If we don't have anything selected, it will tell us None is selected, so we can skip this method
        if not currentItem:
            return

        # We then get the text label of the current item. This will be the name of our control
        name = currentItem.text()
        # Then we tell our library to load it
        self.library.importAsset(name, copy_textures)

    def populate(self):
        """
        UI populate function - linkes to the assetLibrary.scan()
        Returns:

        """
        filterWord = self.searchNameField.text()

        self.listWidget.clear()
        self.library.scan()
        # Now we iterate through the dictionary
        for name, info in sorted(self.library.items()):

            # if there is a filterword, filter the item
            if filterWord != "" and filterWord.lower() not in name.lower():
                continue
            # We create an item for the list widget and tell it to have our controller name as a label
            item = QtWidgets.QListWidgetItem(name)

            # We set its tooltip to be the info from the json
            # The pprint.pformat will format our dictionary nicely
            item.setToolTip(pprint.pformat(info))

            # Finally we check if there's a screenshot available
            thumb = info.get('thumbPath')
            asset = info.get('assetName')
            thumbPath = os.path.join(self.directory, asset, thumb)
            # If there is, then we will load it
            if thumb:
                # So first we make an icon with the path to our screenshot
                icon = QtGui.QIcon(thumbPath)
                # then we set the icon onto our item
                item.setIcon(icon)

            # Finally we add our item to the list
            self.listWidget.addItem(item)

