#####################################################################################################################
## Asset Library - Python Script
## Copyright (C) Arda Kutlu
## Title: Asset Library
## AUTHOR:	Arda Kutlu
## e-mail: ardakutlu@gmail.com
## Web: http://www.ardakutlu.com
## VERSION:1.0
## CREATION DATE: 11.07.2017
## LAST MODIFIED DATE: 11.07.2017
##
## DESCRIPTION: Asset Library which will hold the frequently used product models.
## INSTALL:
## Copy all files into user/maya/scripts folder(not folder, only files)
## Run these commands in python tab (or put them in a shelf:

import assetLibrary
assetLibrary.AssetLibraryUI().show()


##
## USAGE:

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

#####################################################################################################################
