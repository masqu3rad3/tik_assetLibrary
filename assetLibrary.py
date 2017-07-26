#####################################################################################################################
## Asset Library - Python Script
## Title: Asset Library
## AUTHOR:	Arda Kutlu
## e-mail: ardakutlu@gmail.com
## Web: http://www.ardakutlu.com
## VERSION:1.2(beta)
## CREATION DATE: 11.07.2017
## LAST MODIFIED DATE: 26.07.2017
##
## DESCRIPTION: Asset Library which will hold the frequently used product models. This Script are based on the Dhruv Govil's example code: controller Library
                ## (https://github.com/dgovil/PythonForMayaSamples/tree/master/controllerLibrary)
## INSTALL:
## Copy all files into user/maya/scripts folder(not folder, only files)
## Run these commands in python tab (or put them in a shelf:
## import assetLibrary
## assetLibrary.AssetLibraryUI().show()
##
## USAGE:
## TABS MENU:
## - At the first run, a pop up folder window will ask for the asset library. It can be a new one or an existing Asset Library folder.
                ## This action is one time only. A file called assetLibraryConfig.json will be created on the same folder with the script file.
## - Hit the "+" tab to add additional Libraries.
## - You can rename, re-path, or delete libraries from the right click menu on tabs.
                ## Please note that these actions will only affect on selected (viewing) tab
                ## Deleting the library does not delete the library folder, it only removes the tab and updates config file.
                ## At any time the removed library can be added again without any loss.

## MAIN MENU:
## - Top search filter can be used to filter assets.
## - Use the Export Import button to import selected asset. This will copy all texture files under the
                ## sourceimages/<assetname> directory of currently set project
## - Use Refresh Button to manually refresh the library.
## - Use Export button to put selected objects into the Library

## RIGHT CLICK MENU:
## - Right click on an asset opens the right click menu
## - Show screenshot: Opens the screenshot of the item with the default imageviewer defined by the os.
## - Show wireframe: Opens the wireframe of the item with the default imageviewer defined by the os.
## - Import and copy textures: Same command with the import button
## - Import Maya file: Only imports the ma file from the asset folder
## - Import Obj file: Imports the Obj file from the asset folder
## - Open File: Opens the Maya File THIS WILL FORCE TO OPEN THE FILE, ALL UNSAVED WORK WILL LOST ON CURRENT SCENE
## - View As List / View As Icons : Toggles between Icon and List View
## - Show Folder In Explorer: Opens the asset folder in windows explorer

## SHORTCUTS:
## - CTRL+i will import the file. Same action with the "import" button
## - CTRL+e will export selection. Same action with the "export" button
## - CTRL+PLUS(+) will increase the icon size
## - CTRL+MINUS(-) will decrease the icon size

## Version History:
## v1.2
## - Support for multiple Libraries added. Tabbed window allows to control multiple libraries at the same time
## - Directory path is not fixed therefore now it can be used anywhere for multiple purposes.
## - Added configuration database. AssetLibraryConfig.json file will hold the path configurations and tab names
##
## v1.0
## - Initial Release

#####################################################################################################################

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
logger.setLevel(logging.INFO)

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

    def __init__(self, directory):
        self.directory=directory
        if not os.path.exists(directory):
            logger.error("Cannot reach the library directory: \n" + directory)

    def saveAsset(self, assetName, screenshot=True, moveCenter=False, **info):
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
        logger.info("Saving the asset")
        originalPath = pm.sceneName()
        # Save scene as to prevent fatal problems
        # if not originalPath == "":
        #     sceneFolder, sceneName = os.path.split(originalPath)
        #     sceneNameBase, sceneNameExt = os.path.splitext(sceneName)
        #     newSceneName = "{0}{1}{2}".format(sceneNameBase, "_TMP", sceneNameExt)
        #     newScenePath = os.path.join(sceneFolder, newSceneName)
        #     pm.saveAs(newScenePath)

        assetDirectory = os.path.join(self.directory, assetName)

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

        # selection for poly evaluate
        pm.select(possibleFileHolders)
        polyCount = pm.polyEvaluate(f=True)
        tiangleCount = pm.polyEvaluate(t=True)

        ## Json stuff

        info['assetName'] = assetName
        info['objPath'] = self.pathOps(objName, "basename")
        info['maPath'] = self.pathOps(maName, "basename")
        info['thumbPath'] = self.pathOps(thumbPath, "basename")
        info['ssPath'] = self.pathOps(ssPath, "basename")
        info['swPath'] = self.pathOps(swPath, "basename")
        info['textureFiles'] = allFileTextures
        info['Faces/Trianges'] = ("%s/%s" % (str(polyCount), str(tiangleCount)))
        info['sourceProject'] = originalPath

        # query the number of faces
        pm.polyEvaluate(f=True)
        # Result: 16

        # query the number of triangles
        pm.polyEvaluate(t=True)

        propFile = os.path.join(assetDirectory, "%s.json" % assetName)

        with open(propFile, "w") as f:
            json.dump(info, f, indent=4)

        self[assetName] = info

        ## TODO // REVERT BACK
        # if not originalPath == "":
        #     pm.openFile(originalPath, force=True)
        #     os.remove(newScenePath)

    def scan(self):
        """
        Scans the directory for .json files, and gather info.
        Args:
            directory: (Unicode) Default Library location. Default is predefined outside of this class

        Returns:
            None

        """
        if not os.path.exists(self.directory):
            return
        self.clear()
        # first collect all the json files from second level subfolders
        subDirs = next(os.walk(self.directory))[1]

        # subDirs= (subDirs.sort())
        allJson = []
        for d in subDirs:
            dir = os.path.join(self.directory, d)
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

    def importAsset(self, name, copyTextures, mode="maPath"):
        """
        Imports the selected asset into the current scene
        
        Args:
            name: (Unicode) Name of the asset which will be imported 
            copyTextures: (Bool) If True, all texture files of the asset will be copied to the current project directory

        Returns:
            None

        """

        logger.info("Importing asset")
        path = os.path.join(self.directory, self[name]['assetName'], self[name][mode])

        textureList = self[name]['textureFiles']
        pm.importFile(path)

        ## if there are not textures files to handle, do not waste time
        if len(textureList) == 0 or copyTextures is False:
            return

        currentProjectPath = os.path.normpath(pm.workspace.path)
        sourceImagesPath = os.path.join(currentProjectPath, "sourceimages")
        logger.info("Copying Textures to %s" %sourceImagesPath)
        ## check if the sourceimages folder exists:
        if not os.path.exists(sourceImagesPath):
            os.mkdir(sourceImagesPath)

        fileNodes = pm.ls(type="file")
        for texture in textureList:
            path = os.path.join(self.directory, self[name]['assetName'], texture)
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
        logger.info("Saving Preview Images")
        selection = pm.ls(sl=True)

        validShapes = pm.listRelatives(selection, ad=True, type=["mesh", "nurbsSurface"])
        thumbPath = os.path.join(assetDirectory, '%s_thumb.jpg' % name)
        SSpath = os.path.join(assetDirectory, '%s_s.jpg' % name)
        WFpath = os.path.join(assetDirectory, '%s_w.jpg' % name)

        # make sure the viewport display is suitable
        panel = pm.getPanel(wf=True)

        if pm.getPanel(to=panel) != "modelPanel":
            logger.warning("The focus is not on a model panel, using the perspective view")
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
        logger.info("Saving UV Snapshots")
        for i in range(0, len(validShapes)):
            print "validShape", validShapes[i]
            # transformNode = validShapes[i].getParent()
            objName = validShapes[i].name()
            UVpath = os.path.join(assetDirectory, '%s_uv.jpg' % objName)
            pm.select(validShapes[i])
            try:
                pm.uvSnapshot(o=True, ff="jpg", n=UVpath, xr=1600, yr=1600)
            except:
                logger.warning("UV snapshot is missed for %s" %validShapes[i])

        pm.isolateSelect(panel, state=0)
        pm.isolateSelect(panel, removeSelected=True)

        # TODO // store the scene defaults (camera position, imageFormat, etc.

        return thumbPath, SSpath, WFpath

    def filePass(self, fileNodes, newPath, *args):
        textures = []
        for file in fileNodes:
            fullPath = os.path.normpath(pm.getAttr(file.fileTextureName))
            filePath, fileBase = os.path.split(fullPath)
            newLocation = os.path.normpath(os.path.join(newPath, fileBase))

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
                filteredNodes = [x for x in inputNodes if x.type() != "renderLayer"]
                return filteredNodes
        # geo = obj.getShape()
        # Get the shading group from the selected mesh
        try:
            sg = shape.outputs(type='shadingEngine')
        except:
            # if there is no sg, return en empty list
            return []
        everyInput = []
        for i in sg:
            everyInput += pm.listHistory(i)

        everyInput = self.makeUnique(everyInput)
        print "everyInput", everyInput

        fileNodes = pm.ls(everyInput, type="file")
        return fileNodes

    def makeUnique(self, fList):
        keys = {}
        for e in fList:
            keys[e] = 1
        return keys.keys()

    # def gatherAllinputs(self, node):
    #     allInputs = []
    #     currentInputs = node.inputs()
    #
    #     while len(allInputs) != len(currentInputs):
    #         print "allinputs", allInputs
    #         print "currentinputs", currentInputs
    #         tempInputs = []
    #         for i in currentInputs:
    #             tempInputs += i.inputs()
    #             print "temp", tempInputs
    #
    #         allInputs = currentInputs
    #         currentInputs += tempInputs
    #         currentInputs = self.makeUnique(currentInputs)
    #         allInputs = self.makeUnique(allInputs)
    #     return allInputs

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

class bufferUI(QtWidgets.QDialog):
    def __init__(self):
        # for entry in QtWidgets.QApplication.allWidgets():
        #     if entry.objectName() == windowName:
        #         entry.close()
        parent = getMayaMainWindow()
        super(bufferUI, self).__init__(parent=parent)
        self.superLayout = QtWidgets.QVBoxLayout(self)
        self.setWindowTitle("Asset Library")
        self.setObjectName("assetLib")
        self.show()

class AssetLibraryUI(QtWidgets.QTabWidget):
    tabID = 0
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            if entry.objectName() == "assetLib":
                # print entry
                entry.close()

        ## I use another QDialog as buffer since Tabs wont work when parented to the Maya Ui.
        self.buffer=bufferUI()
        super(AssetLibraryUI, self).__init__(parent=self.buffer)

        ## This will put the Tab Widget into the buffer layout
        self.buffer.superLayout.addWidget(self)

        ## This will zero out the margins caused by the bufferUI
        self.buffer.superLayout.setContentsMargins(0,0,0,0)

        self.setWindowTitle("Asset Library")
        self.setObjectName("assetLib")
        self.tabDialog()

    def tabDialog(self):

        # This is the default tab
        # tabA = libraryTab(DIRECTORY)


        # first create the libraries defined in the settings file
        libs = self.settings(mode="load")
        junkPaths=[]
        for item in libs:
            name = item[0]
            path = item[1]
            if not os.path.exists(path):
                logger.warning("Cannot reach library path: \n%s \n Removing from the database..." %(path))
                junkPaths.append(item)
                continue
            preTab = libraryTab(path)
            self.addTab(preTab, name)
            preTab.setLayout(preTab.layout)

        ## Remove the junk paths from the config file
        for x in junkPaths:
            self.settings(mode="remove", item=x)


        if len(libs) == 0:
            self.createNewTab()


        self.addNew = QtWidgets.QWidget()
        # self.addNew.installEventFilter(self.addNew)
        self.addTab(self.addNew, "+")

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        self.customContextMenuRequested.connect(self.on_context_menu)

        self.tabsRightMenu = QtWidgets.QMenu()

        renameTabAction = QtWidgets.QAction('Rename', self)
        self.tabsRightMenu.addAction(renameTabAction)
        # renameTabAction.triggered.connect(self.renameLibrary)
        renameTabAction.triggered.connect(lambda val="rename": self.settings(mode=val))

        repathTabAction = QtWidgets.QAction('Re-path', self)
        self.tabsRightMenu.addAction(repathTabAction)
        # renameTabAction.triggered.connect(self.renameLibrary)
        repathTabAction.triggered.connect(lambda val="repath": self.settings(mode=val))

        removeTabAction = QtWidgets.QAction('Remove Selected Library', self)
        self.tabsRightMenu.addAction(removeTabAction)
        removeTabAction.triggered.connect(self.deleteCurrentTab)




        self.currentChanged.connect(self.createNewTab)  # changed!
        # self.currentChanged(self.createNewTab)

    def on_context_menu(self, point):
        # show context menu
        self.tabsRightMenu.exec_(self.mapToGlobal(point))
        print (QtWidgets.QApplication.widgetAt(self.mapToGlobal(point)))

    def createNewTab(self):
        currentIndex=self.currentIndex()
        totalTabs=self.count()
        if currentIndex >= (totalTabs-1): ## if it is not the last tab (+)
            self.setCurrentIndex(currentIndex-1)
            ## ASK For the new direcory location:

            directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Asset Directory", QtCore.QDir.currentPath())
            if directory:
                tabName = str(os.path.basename(directory))

                self.tabID += 1
                testTab = libraryTab(directory)
                self.addTab(testTab, tabName)
                self.tabBar().moveTab(currentIndex, currentIndex+1)
                self.setCurrentIndex(currentIndex)
                self.settings(mode="add", name=tabName , path=directory)


    # def eventFilter(self, QObject, event):
    #     if event.type() == QtCore.Event.MouseButtonPress:
    #         if event.button() == Qt.RightButton:
    #             print("Right button clicked")
    #     return False

## TODO: FOOL PROOF config.json file. Test possible situations
## TODO: FOOL PROOF missing library folder (a re-path sub menu item within the right click menu?)

    def deleteCurrentTab(self):

        currentIndex=self.currentIndex()
        totalTabs=self.count()

        if currentIndex < (totalTabs): ## if it is not the last tab (+)
            widget = self.widget(currentIndex)
            if widget is not None:
                widget.deleteLater()
            self.setCurrentIndex(currentIndex - 1)
            self.removeTab(currentIndex)
            self.settings(mode="remove", itemIndex=currentIndex)

    def settings(self, mode, name=None, path=None, itemIndex=None, item=None):
        """
        Reads and write Library name and path information on/from config file (assetLibraryConfig.json)
        
        Add mode
        adds the name and path of the directory to the database. "name" and "path" arguments are required.
        Ex.
        settings(mode="add", name="NameOfTheLib", path="Absolute/path/of/the/library")
        
        Remove mode
        Removes the given item from the database. Either "itemIndex" or "item" arguments are required. If both given, "item" will be used.
        Ex.
        settings(mode="remove", itemIndex=2)
        or
        settings(mode="remove", item=["Name","Path"])
        
        Rename mode
        Opens a input dialog, renames the selected tab and updates database with the new name
        
        Repath mode
        Opens a folder selection dialog, updates database with the selected folder
        
        Load mode
        Returns the database list.
        
        Args:
            mode: (String) Valid values are "add", "remove", "load".
            name: (String) Tab Name of the Library to be added. Required by "add" mode
            path: (String) Absolute Path of the Library to be added. Required by "add" mode
            itemIndex: (Int) Index value of the item which will be removed from the database. Required by "remove" mode IF item flag is not set
            item: (Int) item which will be removed from the database. Required by "remove" mode IF itemIndex flag is not set.

        Returns:
            Load mode returns List

        """
        ## get the file location
        settingsFile = os.path.join(os.path.dirname(os.path.abspath( __file__ )),"assetLibraryConfig.json")
        def dump(data,file):
            with open(file, "w") as f:
                json.dump(data, f, indent=4)

        if mode == "add" and name is not None and path is not None:
            currentData = self.settings(mode="load")
            currentData.append([name, path])
            dump(currentData, settingsFile)
            return
        if mode == "remove":
            print "itemIndex", itemIndex
            print "item", item
            currentData = self.settings(mode="load")
            if itemIndex is not None:
                currentData.pop(itemIndex)
            elif item is not None:
                currentData.remove(item)
            else:
                logger.warning("You need to specify itemIndex or item for remove action")
                return
            dump(currentData, settingsFile)
            return


        if mode == "rename":
            currentIndex = self.currentIndex()
            if currentIndex == self.count():
                return
            currentData = self.settings(mode="load")
            exportWindow, ok = QtWidgets.QInputDialog.getText(self, 'Text Input Dialog','New Name:')
            if ok:
                newInput = str(exportWindow)
                if not newInput.strip():
                    logger.warn("You must give a name!")
                    return
                self.setTabText(currentIndex, newInput)
                ## update the settings file
                currentData[currentIndex][0] = newInput
                dump(currentData,settingsFile)
                return

        if mode == "repath":
            currentIndex = self.currentIndex()
            if currentIndex == self.count():
                return
            currentData = self.settings(mode="load")

            newDir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Asset Directory", QtCore.QDir.currentPath())
            if newDir:
                currentData[currentIndex][1] = newDir
                dump(currentData,settingsFile)
                return

        if mode == "load":
            if os.path.isfile(settingsFile):
                with open(settingsFile, 'r') as f:
                    # The JSON module will read our file, and convert it to a python dictionary
                    data = json.load(f)
                    return data
            else:
                return []
        logger.warning("Settings file not changed")


class libraryTab(QtWidgets.QWidget):
    viewModeState = 1
    def __init__(self, directory):
        self.directory = directory

        # super is an interesting function
        # It gets the class that our class is inheriting from
        # This is called the superclass
        # The reason is that because we redefined __init__ in our class, we no longer call the code in the super's init
        # So we need to call our super's init to make sure we are initialized like it wants us to be
        # me=self
        # for entry in QtWidgets.QApplication.allWidgets():
        #     if entry.objectName() == "assetLib":
        #         # print entry
        #         entry.close()

        # parent = getMayaMainWindow()

        super(libraryTab, self).__init__()

        self.library = assetLibrary(directory)
        self.buildTabUI()


    def buildTabUI(self):

        self.layout = QtWidgets.QVBoxLayout(self)

        searchWidget = QtWidgets.QWidget()
        searchLayout = QtWidgets.QHBoxLayout(searchWidget)

        self.layout.addWidget(searchWidget)

        self.searchLabel = QtWidgets.QLabel("Seach Filter: ")
        searchLayout.addWidget(self.searchLabel)
        self.searchNameField = QtWidgets.QLineEdit()

        self.searchNameField.textEdited.connect(self.populate)
        searchLayout.addWidget(self.searchNameField)
        self.size = 64
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setViewMode(QtWidgets.QListWidget.IconMode)
        self.listWidget.setMinimumSize(350, 600)
        self.listWidget.setIconSize(QtCore.QSize(self.size, self.size))
        self.listWidget.setMovement(QtWidgets.QListView.Static)
        self.listWidget.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.listWidget.setGridSize(QtCore.QSize(self.size *1.2, self.size *1.4))
        self.layout.addWidget(self.listWidget)
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.on_context_menu)
        self.popMenu = QtWidgets.QMenu()
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

        importOnlyAction = QtWidgets.QAction('Import Maya File', self)
        self.popMenu.addAction(importOnlyAction)
        importOnlyAction.triggered.connect(lambda item='importOnly': self.actionTrigger(item))

        importObjAction = QtWidgets.QAction('Import Obj', self)
        self.popMenu.addAction(importObjAction)
        importObjAction.triggered.connect(lambda item='importObj': self.actionTrigger(item))

        openFileAction = QtWidgets.QAction('Open File', self)
        self.popMenu.addAction(openFileAction)
        openFileAction.triggered.connect(lambda item='openFile': self.actionTrigger(item))
        self.popMenu.addSeparator()

        self.viewAsListAction = QtWidgets.QAction('View As List', self)
        self.popMenu.addAction(self.viewAsListAction)
        self.viewAsListAction.triggered.connect(lambda item='viewModeChange': self.actionTrigger(item))

        self.popMenu.addSeparator()

        openFolderAction = QtWidgets.QAction('Show folder in explorer', self)
        self.popMenu.addAction(openFolderAction)
        openFolderAction.triggered.connect(lambda item='openFolder': self.actionTrigger(item))

        btnWidget = QtWidgets.QWidget()
        btnLayout = QtWidgets.QHBoxLayout(btnWidget)
        self.layout.addWidget(btnWidget)

        importBtn = QtWidgets.QPushButton('Import')
        importBtn.clicked.connect(lambda cp_txt=True: self.load(cp_txt))
        btnLayout.addWidget(importBtn)

        refreshBtn = QtWidgets.QPushButton('Refresh')
        refreshBtn.clicked.connect(self.populate)
        btnLayout.addWidget(refreshBtn)

        self.exportBtn = QtWidgets.QPushButton('Export')
        self.exportBtn.clicked.connect(self.export)
        btnLayout.addWidget(self.exportBtn)

        shortcutExport = Qt.QtWidgets.QShortcut(Qt.QtGui.QKeySequence("Ctrl+E"), self, self.export)
        shortcutImport = Qt.QtWidgets.QShortcut(Qt.QtGui.QKeySequence("Ctrl+I"), self, lambda val=True: self.load(val))
        scIncreaseIconSize = Qt.QtWidgets.QShortcut(Qt.QtGui.QKeySequence("Ctrl++"), self, lambda val=10: self.adjustIconSize(val))
        scDecreaseIconSize = Qt.QtWidgets.QShortcut(Qt.QtGui.QKeySequence("Ctrl+-"), self, lambda val=-10: self.adjustIconSize(val))

        self.populate()


    def adjustIconSize(self, value):
        self.size += value
        self.listWidget.setIconSize(QtCore.QSize(self.size, self.size))
        self.listWidget.setGridSize(QtCore.QSize(self.size *1.2, self.size *1.4))


    def actionTrigger(self, item):
        currentItem = self.listWidget.currentItem()
        name = currentItem.text()
        info = self.library[name]

        if item == 'openFolder':
            asset = info.get('assetName')
            path = os.path.join(self.directory, asset)
            os.startfile(path)
        elif item == 'importWithCopy':
            self.load(True, mode="maPath")
        elif item == 'importOnly':
            self.load(False, mode="maPath")
        elif item == 'importObj':
            self.load(False, mode="objPath")
        elif item == 'openFile':

            filename = info.get('maPath')
            asset = info.get('assetName')
            filepath = os.path.join(self.directory, asset, filename)
            pm.openFile(filepath, force=True)

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

        exportWindow, ok = QtWidgets.QInputDialog.getText(self, 'Text Input Dialog',
                                                          'SAVE BEFORE PROCEED\n\nANY UNSAVED WORK WILL BE LOST\n\nEnter Asset Name:')
        if ok:
            name = str(exportWindow)
            logger.debug(name.strip())
            # assert name.strip() == False, "You must give a name!"
            if not name.strip():
                logger.warn("You must give a name!")
                return
            self.library.saveAsset(name)
            self.populate()
            # self.exportWindow.show()
            logger.info("Asset Exported")

    def load(self, copy_textures, mode="maPath"):
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
        self.library.importAsset(name, copy_textures, mode=mode)

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

