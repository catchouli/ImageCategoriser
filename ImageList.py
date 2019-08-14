# -*- coding: utf-8 -*-

import os
import sys
import time
import queue
import threading
import subprocess

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import ( pyqtSignal, QVariant )
from PyQt5.QtWidgets import ( QListView, QMessageBox, QAction, QListWidget
                            , QListWidgetItem, QMenu, QAbstractItemView )

import Utils
from DirectoryMonitor import Image

# The image list
class ImageList(QListWidget):
  # Signal triggered when the user adds an image to a category (image, category)
  onAddImageCategory = pyqtSignal(Image, str)
  
  # Signal triggered when the user removes an image from a category (image, category)
  onRemoveImageCategory = pyqtSignal(Image, str)
  
  # Signal triggerde when the user attemps to remove an image from the index completely
  onRemoveImageIndex = pyqtSignal(Image)
  
  def __init__(self, getCategories, getCurrentCategory):
    super().__init__()
    
    self._getCategories = getCategories
    self._getCurrentCategory = getCurrentCategory
    
    # all images in the list currently
    self._images = {}
    
    # configuration
    self._iconSize = 256
    
    # icon thread
    self._imagesLock = threading.Lock()
    self._iconThread = None
    self._iconQueue = queue.Queue()
    
    # cached image icons
    self._imageIcons = {}
    
    # initialise QListWidget
    self.installEventFilter(self)
    self.itemDoubleClicked.connect(self._imageDoubleClick)
    self.setViewMode(QListWidget.IconMode)
    self.setIconSize(QtCore.QSize(self._iconSize, self._iconSize))
    self.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.setResizeMode(QListView.Adjust)
    
    # Start icon load thread
    self.iconThread = threading.Thread(name='iconThread', target=self._iconTask)
    self.iconThread.daemon = True
    self.iconThread.start()
  
  # Add an image to the ui
  def addImage(self, image):
    if image.fromRootDir not in self._images:
      icon = None
      if image.absolutePath in self._imageIcons:
        icon = self._imageIcons[image.absolutePath]
      else:
        icon = QIcon()
        self._iconQueue.put((image, icon))
        self._imageIcons[image.absolutePath] = icon
      item = QListWidgetItem(icon, image.name)
      item.setSizeHint(QtCore.QSize(self._iconSize, self._iconSize+32))
      item.setData(QtCore.Qt.UserRole, QVariant(image))
      
      self._imagesLock.acquire(True)
      self._images[image.fromRootDir] = item
      self.insertItem(self.count(), item)
      self._imagesLock.release()

  # Remove an image from the ui
  def removeImage(self, image):
    if image.fromRootDir in self._images:
      self._imagesLock.acquire(True)
      item = self._images.pop(image.fromRootDir)
      self.removeItemWidget(item)
      self._imagesLock.release()

  # Remove all images from the ui
  def clearImages(self):
    self._imagesLock.acquire(True)
    self._images = {}
    self.clear()
    self._imagesLock.release()

  # Event filter for right click menu on images
  def eventFilter(self, source, event):
    if event.type() == QtCore.QEvent.ContextMenu:
      item = source.itemAt(event.pos())
      if item != None:
        self._createImageMenu(event.globalPos(), item)
      return True
    return False
  
  # Wait for icon tasks and load the icon
  def _iconTask(self):
    while True:
      (image, icon) = self._iconQueue.get()
      # load file
      icon.addFile(str(image.absolutePath))
      # force refresh
      self._imagesLock.acquire(True)
      if image.fromRootDir in self._images:
        self._images[image.fromRootDir].setIcon(icon)
        self._images[image.fromRootDir].listWidget().update()
      self._imagesLock.release()
      # mark task as done
      self._iconQueue.task_done()
      # sleep so we don't block the main thread
      time.sleep(0.001)

  # Create the 'background' menu for the category list
  def _createImageMenu(self, pos, item):
    menu = QMenu()
    
    # Main add action
    addCategoryAction = QAction('Add to category...')
    addCategoryAction.triggered.connect(lambda _: self._contextAddImageCategory(''))
    menu.addAction(addCategoryAction)
  
    # Remove from current category
    currentCategory = self._getCurrentCategory()
    if currentCategory != 'All' and currentCategory != 'Uncategorised':
      removeCategoryAction = QAction(f'Remove from {currentCategory}')
      removeCategoryAction.triggered.connect(lambda _: self._contextRemoveImageCategory(currentCategory))
      menu.addAction(removeCategoryAction)
    
    # List other categories
    addListAction = QAction('Add to...')
    addListAction.setDisabled(True)
    menu.addAction(addListAction)
    
    # We have to store the actions for some reason or they don't show up (raii?)
    actions = []
    for category in self._getCategories():
      if category != 'All' and category != 'Uncategorised':
        # worst part of python. closures are bound by reference so if we don't trap it
        # inside another function first every time 'category' has the last iteration's value
        def gen(img, cat): return lambda _: img._contextAddImageCategory(cat)
        newAction = QAction(f'  {category}')
        newAction.triggered.connect(gen(self, category))
        menu.addAction(newAction)
        actions.append(newAction)
    
    removeAction = QAction('Remove from index')
    removeAction.triggered.connect(self._contextRemoveImage)
    menu.addAction(removeAction)
    
    deleteAction = QAction('Delete from disk')
    deleteAction.triggered.connect(self._contextDeleteImage)
    menu.addAction(deleteAction)
    
    menu.show()
    menu.exec_(pos)
    return menu
  
  # Add the selected images to the given category
  def _contextAddImageCategory(self, category):
    print(f'context adding image to category {category}')
    selected = self.selectedItems()
    for item in selected:
      image = item.data(QtCore.Qt.UserRole)
      if category == '':
        category = Utils.promptCategoryName(self)
        if category == None:
          return
      
      self.onAddImageCategory.emit(image, category)
  
  # Remove the selected images from the given category
  def _contextRemoveImageCategory(self, category):
    selected = self.selectedItems()
    for item in selected:
      image = item.data(QtCore.Qt.UserRole)
      self.onRemoveImageCategory.emit(image, category)

  # Remove an image from the index
  def _contextRemoveImage(self):
    selected = self.selectedItems()
    for item in selected:
      image = item.data(QtCore.Qt.UserRole)
      self.onRemoveImageIndex.emit(image)

  # Actually delete an image
  def _contextDeleteImage(self):
    selected = self.selectedItems()
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
          type, value, traceback = sys.exc_info()
          print(f'got exception deleting image {image.name}: {value}')
          pass
        self.onRemoveImageIndex.emit(image)

  # Open an image in the system default image viewer
  def _openImage(self, image):
    imageViewerFromCommandLine = {'linux':'xdg-open',
                                  'win32':'explorer',
                                  'darwin':'open'}[sys.platform]
    subprocess.run([imageViewerFromCommandLine, str(image.absolutePath)])

  # Event handler for double click on image list
  def _imageDoubleClick(self, item):
    image = item.data(QtCore.Qt.UserRole)
    self._openImage(image)