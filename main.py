#!/usr/bin/python
# -*- coding: utf-8 -*-

# TODO:
#  - implement all the context menu options
#  - save out the state of the DirectoryMonitor class to a file (what images there are and what categories they're in)
#  - QIcons are too slow for previewing all the images directly, we need to do something clever to speed it up

import sys
import subprocess
import os
from pathlib import Path
import PIL

from PyQt5 import QtCore
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import ( QFont, QIcon )
from PyQt5.QtWidgets import ( QApplication, QMainWindow, QWidget, QListView
                            , QToolTip, QPushButton, QMessageBox, QDesktopWidget
                            , QAction, QHBoxLayout, QGridLayout, QListWidget
                            , QListWidgetItem, QMenu, QInputDialog )

# The test directory
testDirectory = 'C:\\work\\sourcetrees\\img\\test'

# An image
class Image:
  def __init__(self, name, fromRootDir, rootDir):
    self.name = name
    self.fromRootDir = fromRootDir
    self.rootDir = rootDir
    self.absolutePath = (Path(rootDir) / self.fromRootDir).resolve()
    self.categories = []

# The directory watcher
class DirectoryMonitor:
  # Initialise the monitor
  def __init__(self, dir):
    self.rootDir = dir
    self.categoryList = set([ "Uncategorised", "All" ])
    self.files = {}
  
  # Refresh the folder
  def refresh(self):
    for subdir, dirs, files in os.walk(self.rootDir):
        for file in files:
          # construct path
          path = Path(subdir) / Path(file)
          
          # trim rootDir
          fromRootDir = path.relative_to(Path(self.rootDir))
          
          # get name
          name = path.parts[-1]
          
          # create image object
          image = Image(name, fromRootDir, self.rootDir)
          
          # add image
          if fromRootDir not in self.files:
            self.files[fromRootDir] = image

  # Get a list of categories
  def getCategories(self):
    return self.categoryList

  # Get all the images in a category
  def getCategory(self, category):
    images = set()
    
    for file, image in self.files.items():
      if category == "All":
        images.add(image)
      elif category == "Uncategorised":
        if len(image.categories) == 0:
          images.add(image)
      else:
        if category in image.categories:
          images.add(image)
    
    return images

  # Add an image to a category, and add the category to the list if it doesn't exist
  def addImageCategory(self, image, category):
    if category == 'All' or category == 'Uncategorised':
      return
  
    if image.fromRootDir in self.files:  
      if category not in self.categoryList:
        self.categoryList.add(category)
        
      if category not in self.files[image.fromRootDir].categories:
        self.files[image.fromRootDir].categories.append(category)

  # Remove an image from a category
  def removeImageCategory(self, image, category):
    if category == 'All' or category == 'Uncategorised':
      return
      
    if image.fromRootDir in self.files:
      if category in self.files[image.fromRootDir].categories:
        self.files[image.fromRootDir].categories.remove(category)

  # Remove a category and make sure all images no longer list it
  def removeCategory(self, category):
    if category == 'All' or category == 'Uncategorised':
      return
      
    if category in self.categoryList:
      for pathFromBase, image in self.files.items():
        if category in image.categories:
          image.categories.remove(category)
      self.categoryList.remove(category)

  # Rename a category and make sure all images no longer list it
  def renameCategory(self, category, newName):
    if category == 'All' or category == 'Uncategorised':
      return
    if newName == 'All' or newName == 'Uncategorised':
      return
    
    if newName in self.categoryList:
      return
      
    if category in self.categoryList:
      for pathFromBase, image in self.files.items():
        if category in image.categories:
          image.categories.remove(category)
          image.categories.append(newName)
      
      self.categoryList.remove(category)
      self.categoryList.add(newName)

# The main window
class Img(QMainWindow):
  def __init__(self):
    super().__init__()
    self.ready = False
    self.fileWatcher = DirectoryMonitor(testDirectory)
    self.currentCategory = None
    self.categories = {}
    self.images = {}
    self.initUI()

  def initUI(self):
    # Tooltip
    QToolTip.setFont(QFont('SansSerif', 10))
    self.setToolTip('this is a <b>widget</b>')
    
    # Menu
    menubar = self.menuBar()
    fileMenu = menubar.addMenu('File')
    
    refreshAction = QAction('Refresh', self)
    refreshAction.triggered.connect(self.fullRefresh)
    fileMenu.addAction(refreshAction)
    
    # Main widget
    wid = QWidget(self)
    self.setCentralWidget(wid)
    
    # Layout
    layout = QHBoxLayout()
    wid.setLayout(layout)
    
    # Categories
    self.categoryList = QListWidget()
    self.categoryList.setMaximumWidth(200)
    self.categoryList.currentItemChanged.connect(self.categoryChanged)
    self.categoryList.installEventFilter(self)
    layout.addWidget(self.categoryList)
    
    # Images
    self.imageList = QListWidget()
    self.imageList.installEventFilter(self)
    self.imageList.itemDoubleClicked.connect(self.imageDoubleClick)
    self.imageList.setViewMode(QListWidget.IconMode)
    self.imageList.setIconSize(QtCore.QSize(96, 96))
    layout.addWidget(self.imageList)
    
    # Window position and size
    self.resize(800, 600)
    self.center()
    self.setWindowTitle('Img')
    self.show()
    
    # Refresh
    self.refreshFiles()
    self.refreshUI()
    
    self.ready = True
  
  # Add an image to the ui
  def addImage(self, image):
    if image.name not in self.images:
      icon = QIcon(str(image.absolutePath))
      item = QListWidgetItem(icon, image.name)
      item.setSizeHint(QtCore.QSize(128, 128))
      item.setData(QtCore.Qt.UserRole, QVariant(image))
      self.images[image.name] = item
      self.imageList.insertItem(self.imageList.count(), item)

  # Remove an image from the ui
  def removeImage(self, image):
    if image.name in self.images:
      item = self.images.pop(image.name)
      self.imageList.removeItemWidget(item)

  # Remove all images from the ui
  def clearImages(self):
    self.images = {}
    self.imageList.clear()
  
  # Add a category to the ui
  def addCategory(self, name):
    if name not in self.categories:
      item = QListWidgetItem(name)
      self.categories[name] = item
      self.categoryList.insertItem(self.categoryList.count(), item)

  # Remove a category from the ui
  def removeCategory(self, name):
    if name in self.categories:
      item = self.categories.pop(name)
      self.categoryList.removeItemWidget(item)

  # Remove all categories from the ui
  def clearCategories(self):
    self.categories = {}
    self.categoryList.clear()

  # Center the window on the screen
  def center(self):
    qr = self.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    self.move(qr.topLeft())

  # Refresh the files, then the ui
  def fullRefresh(self):
    self.refreshFiles()
    self.refreshUI()

  # Refresh the ui categories and files based on fileWatcher and the current category
  def refreshUI(self):
    # Category list
    categories = self.fileWatcher.getCategories()
  
    # Update categories
    remove = []
    
    # Remove categories that have been deleted
    # todo: for some reason this doesn't actually remove them, maybe because they're selected
    for category in self.categories:
      if category not in categories:
        print(f'adding {category} to list')
        remove.append(category)
    for category in remove:
      print(f'removing {category}')
      self.removeCategory(category)
    
    # Add categories if not added already
    for category in categories:
      self.addCategory(category)
  
    # Clear the existing images from the view
    self.clearImages()
    
    # Get the current category's images and add them to the ui
    for image in self.fileWatcher.getCategory(self.currentCategory):
      self.addImage(image)

  # Refresh all files
  def refreshFiles(self):
    self.fileWatcher.refresh()

  # Refresh the ui when the category changes
  def categoryChanged(self, curr, prev):
    self.currentCategory = curr.text()
    self.refreshUI()

  # Event filter for QListWidget context menus
  def eventFilter(self, source, event):
    if not self.ready:
      return False
  
    # Handle context events for the categories list
    if event.type() == QtCore.QEvent.ContextMenu and source is self.categoryList:
      item = source.itemAt(event.pos())
      if item != None:
        self.createCategoryMenu(event.globalPos(), item)
      return True
    # Handle context events for the image list
    elif event.type() == QtCore.QEvent.ContextMenu and source is self.imageList:
      item = source.itemAt(event.pos())
      if item != None:
        self.createImageMenu(event.globalPos(), item)
      return True
    return False

  # Event handler for double click on image list
  def imageDoubleClick(self, item):
    image = item.data(QtCore.Qt.UserRole)
    self.openImage(image)

  # Open an image in the system default image viewer
  def openImage(self, image):
    imageViewerFromCommandLine = {'linux':'xdg-open',
                                  'win32':'explorer',
                                  'darwin':'open'}[sys.platform]
    subprocess.run([imageViewerFromCommandLine, str(image.absolutePath)])

  # Create the 'background' menu for the category list
  def createCategoryListMenu(self, pos):
    menu = QMenu()
    
    addCategoryAction = QAction(f'Add category...')
    addCategoryAction.triggered.connect(lambda _: self.contextAddCategory())
    menu.addAction(addCategoryAction)
      
    menu.show()
    menu.exec_(pos)
    return menu
  
  def contextDeleteCategory(self, category):
    self.fileWatcher.removeCategory(category)
    self.refreshUI()
  
  def contextRenameCategory(self, category):
    newName = self.promptCategoryName()
    if newName != None:
      self.fileWatcher.renameCategory(category, newName)
      self.refreshUI()

  # Create the 'background' menu for the category list
  def createCategoryMenu(self, pos, item):
    category = item.text()
    
    menu = QMenu()
    
    deleteCategoryAction = QAction(f'Delete {category}')
    deleteCategoryAction.triggered.connect(lambda _: self.contextDeleteCategory(category))
    menu.addAction(deleteCategoryAction)
    
    renameCategoryAction = QAction(f'Rename {category}')
    renameCategoryAction.triggered.connect(lambda _: self.contextRenameCategory(category))
    menu.addAction(renameCategoryAction)
    
    if category == 'All' or category == 'Uncategorised':
      deleteCategoryAction.setDisabled(True)
      renameCategoryAction.setDisabled(True)
    
    menu.show()
    menu.exec_(pos)
      
    return menu
  
  # Show warning box
  def warningBox(self, message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText(message)
    msg.setWindowTitle('Warning')
    msg.exec_()
  
  # Prompt the user for a category name
  def promptCategoryName(self):
    item, ok = QInputDialog.getText(self, 'Category name', 'Enter category name')
    if ok:
      if item != '':
        return item
      else:
        self.warningBox('No category name provided')
        return None
    else:
      return None
  
  # Add an image to a category and refresh the ui
  def addToCategory(self, image, category):
    if category == '':
      category = self.promptCategoryName()
      if category == None:
        return
        
    self.fileWatcher.addImageCategory(image, category)
    self.refreshUI()
  
  # Remove an image from a category and refresh the ui
  def removeFromCategory(self, image, category):
    self.fileWatcher.removeImageCategory(image, category)
    self.refreshUI()

  # Create the 'background' menu for the category list
  def createImageMenu(self, pos, item):
    image = item.data(QtCore.Qt.UserRole)
  
    menu = QMenu()
  
    # Remove from current category
    if self.currentCategory != 'All' and self.currentCategory != 'Uncategorised':
      removeCategoryAction = QAction(f'Remove from {self.currentCategory}')
      removeCategoryAction.triggered.connect(lambda _: self.removeFromCategory(image, self.currentCategory))
      menu.addAction(removeCategoryAction)
    
    # Main add action
    addCategoryAction = QAction('Add to category...')
    addCategoryAction.triggered.connect(lambda _: self.addToCategory(image, ''))
    menu.addAction(addCategoryAction)
    
    # List other categories
    for category in self.fileWatcher.getCategories():
      if category != 'All' and category != 'Uncategorised':
        action = QAction(category)
        action.triggered.connect(lambda _: self.addToCategory(image, category))
        menu.addAction(action)
        
        if category in image.categories:
          action.setDisabled(True)
    menu.show()
    menu.exec_(pos)
    return menu

# Entry, create the main window and then exit when it exits
if __name__ == '__main__':
  app = QApplication(sys.argv)
  img = Img()  
  sys.exit(app.exec_())