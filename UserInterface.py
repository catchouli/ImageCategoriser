# -*- coding: utf-8 -*-

import sys
import subprocess
import threading
import time
import queue

from PyQt5 import QtCore
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import ( QFont, QIcon, QPixmap )
from PyQt5.QtWidgets import ( QApplication, QMainWindow, QWidget, QListView
                            , QToolTip, QPushButton, QMessageBox, QDesktopWidget
                            , QAction, QHBoxLayout, QGridLayout, QListWidget
                            , QListWidgetItem, QMenu, QInputDialog, QAbstractItemView )

from BackendData import DirectoryMonitor

# The test directory
testDirectory = 'C:\\Users\\nano\\Pictures\\art'
IconSize = 512

# The main window
class ImageCategoriserWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    
    self.ready = False
    self.imageIcons = {}
    self.fileWatcher = DirectoryMonitor(testDirectory)
    self.currentCategory = None
    self.categories = {}
    self.images = {}
    self.imagesLock = threading.Lock()
    
    # icon thread
    self.iconThread = None
    self.iconQueue = queue.Queue()
    
    # create the qt gui
    self.initUI()

  # Create the qt gui
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
    self.imageList.setIconSize(QtCore.QSize(IconSize, IconSize))
    self.imageList.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.imageList.setResizeMode(QListView.Adjust)
    layout.addWidget(self.imageList)
    
    # Window position and size
    self.resize(800, 600)
    self.center()
    self.setWindowTitle('Img')
    self.show()
    
    # Refresh
    self.refreshFiles()
    self.refreshUI()
    
    # Start icon load thread
    self.iconThread = threading.Thread(name='iconThread', target=self.iconTask)
    self.iconThread.daemon = True
    self.iconThread.start()
    
    # Indicate ready so we can handle events
    self.ready = True
  
  # Call on exit so we can clean up and save settings
  def exiting(self):
    self.fileWatcher.save()
  
  # Wait for icon tasks and load the icon
  def iconTask(self):
    while True:
      (image, icon) = self.iconQueue.get()
      # load file
      icon.addFile(str(image.absolutePath))
      # force refresh
      self.imagesLock.acquire(True)
      if image.fromRootDir in self.images:
        self.images[image.fromRootDir].setIcon(icon)
        self.images[image.fromRootDir].listWidget().update()
      self.imagesLock.release()
      # mark task as done
      self.iconQueue.task_done()
      # sleep so we don't block the main thread
      time.sleep(0.001)
  
  # Add an image to the ui
  def addImage(self, image):
    if image.fromRootDir not in self.images:
      icon = None
      if image.absolutePath in self.imageIcons:
        icon = self.imageIcons[image.absolutePath]
      else:
        icon = QIcon()
        self.iconQueue.put((image, icon))
        self.imageIcons[image.absolutePath] = icon
      item = QListWidgetItem(icon, image.name)
      item.setSizeHint(QtCore.QSize(IconSize, IconSize+32))
      item.setData(QtCore.Qt.UserRole, QVariant(image))
      
      self.imagesLock.acquire(True)
      self.images[image.fromRootDir] = item
      self.imageList.insertItem(self.imageList.count(), item)
      self.imagesLock.release()

  # Remove an image from the ui
  def removeImage(self, image):
    if image.fromRootDir in self.images:
      self.imagesLock.acquire(True)
      item = self.images.pop(image.fromRootDir)
      self.imageList.removeItemWidget(item)
      self.imagesLock.release()

  # Remove all images from the ui
  def clearImages(self):
    self.imagesLock.acquire(True)
    self.images = {}
    self.imageList.clear()
    self.imagesLock.release()
  
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
  
  # Remove an image from a category and refresh the ui
  def removeFromCategory(self, image, category):
    self.fileWatcher.removeImageCategory(image, category)
  
  # Add the selected images to the given category
  def contextAddImageCategory(self, category):
    print(f'context adding image to category {category}')
    selected = self.imageList.selectedItems()
    for item in selected:
      image = item.data(QtCore.Qt.UserRole)
      self.addToCategory(image, category)
    self.refreshUI()
  
  # Remove the selected images from the given category
  def contextRemoveImageCategory(self, category):
    selected = self.imageList.selectedItems()
    for item in selected:
      image = item.data(QtCore.Qt.UserRole)
      self.removeFromCategory(image, category)
    self.refreshUI()

  # Remove an image from the index
  def contextRemoveImage(self):
    selected = self.imageList.selectedItems()
    for item in selected:
      image = item.data(QtCore.Qt.UserRole)
      self.fileWatcher.removeImage(image)
    self.refreshUI()

  # Actually delete an image
  def contextDeleteImage(self):
    selected = self.imageList.selectedItems()
    toRemove = []
    for item in selected:
      image = item.data(QtCore.Qt.UserRole)
      toRemove.append(image)
    
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    msg.setText(f'This will <b>delete</b> {len(toRemove)} images <b>from disk</b>.')
    msg.setWindowTitle('Warning')

    if msg.exec_() == QMessageBox.Ok:
      print('actually deleting images')
      for image in toRemove:
        print(f'actually deleting image {image.name}')
        try:
          os.remove(str(image.absolutePath))
        except Exception:
          pass
        self.fileWatcher.removeImage(image)
      self.refreshUI()

  # Create the 'background' menu for the category list
  def createImageMenu(self, pos, item):
    menu = QMenu()
  
    # Remove from current category
    if self.currentCategory != 'All' and self.currentCategory != 'Uncategorised':
      removeCategoryAction = QAction(f'Remove from {self.currentCategory}')
      removeCategoryAction.triggered.connect(lambda _: self.contextRemoveImageCategory(self.currentCategory))
      menu.addAction(removeCategoryAction)
    
    # Main add action
    addCategoryAction = QAction('Add to category...')
    addCategoryAction.triggered.connect(lambda _: self.contextAddImageCategory(''))
    menu.addAction(addCategoryAction)
    
    # List other categories
    # We have to store the actions for some reason or they don't show up (raii?)
    actions = []
    for category in self.fileWatcher.getCategories():
      if category != 'All' and category != 'Uncategorised':
        # worst part of python. closures are bound by reference so if we don't trap it
        # inside another function first every time 'category' has the last iteration's value
        def gen(img, cat): return lambda _: img.contextAddImageCategory(cat)
        newAction = QAction(category)
        newAction.triggered.connect(gen(self, category))
        menu.addAction(newAction)
        actions.append(newAction)
    
    removeAction = QAction('Remove from index')
    removeAction.triggered.connect(self.contextRemoveImage)
    menu.addAction(removeAction)
    
    deleteAction = QAction('Delete from disk')
    deleteAction.triggered.connect(self.contextDeleteImage)
    menu.addAction(deleteAction)
    
    menu.show()
    menu.exec_(pos)
    return menu