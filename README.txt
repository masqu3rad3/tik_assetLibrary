#####################################################################################################################
## Asset Library - Python Script
## Copyright (C) Arda Kutlu
## Title: Asset Library
## AUTHOR:	Arda Kutlu
## e-mail: ardakutlu@gmail.com
## Web: http://www.ardakutlu.com
## VERSION:1.2(beta)
## CREATION DATE: 11.07.2017
## LAST MODIFIED DATE: 26.07.2017
##
## DESCRIPTION: Asset Library which will hold the frequently used product models.
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
