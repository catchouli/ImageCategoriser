# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import ( QMainWindow, QWidget, QDesktopWidget, QAction
                            , QHBoxLayout )

from ImageList import ImageList
from CategoryList import CategoryList
from DirectoryMonitor import DirectoryMonitor

# Todo: instead of having refreshUI just have the directory monitor tell us when there's new files and stuff

# The main window
class MainWindow(QMainWindow):
  def __init__(self, testDirectory):
    super().__init__()
    
    self._fileWatcher = DirectoryMonitor(testDirectory)
    
    # create the qt gui
    self._initUI()

  # Create the qt gui
  def _initUI(self):    
    # Menu
    menubar = self.menuBar()
    fileMenu = menubar.addMenu('File')
    
    refreshAction = QAction('Refresh', self)
    refreshAction.triggered.connect(self._fullRefresh)
    fileMenu.addAction(refreshAction)
    
    # Main widget
    wid = QWidget(self)
    self.setCentralWidget(wid)
    
    # Layout
    layout = QHBoxLayout()
    wid.setLayout(layout)
    
    # Categories
    self._categoryList = CategoryList()
    self._categoryList.onCategoryChanged.connect(self._showCategory)
    self._categoryList.onRenameCategory.connect(self._renameCategory)
    self._categoryList.onRemoveCategory.connect(self._removeCategory)
    layout.addWidget(self._categoryList)
    
    # Images
    getCategories = lambda: self._fileWatcher.getCategories()
    getCurrentCategory = lambda: self._categoryList._currentCategory
    self._imageList = ImageList(getCategories, getCurrentCategory)
    self._imageList.onAddImageCategory.connect(self._addImageCategory)
    self._imageList.onRemoveImageCategory.connect(self._removeImageCategory)
    self._imageList.onRemoveImageIndex.connect(self._removeImageIndex)
    layout.addWidget(self._imageList)
    
    # Window position and size
    self.resize(800, 600)
    self._centerWindow()
    self.setWindowTitle('Img')
    self.show()
    
    # Refresh
    self._fileWatcher.refresh()
    self.refreshUI()
  
  # Call on exit so we can clean up and save settings
  def exiting(self):
    self._fileWatcher.save()

  # Refresh the ui categories and files based on fileWatcher and the current category
  def refreshUI(self):
    # Category list
    categories = self._fileWatcher.getCategories()
    
    # Add categories if not added already
    for category in categories:
      self._categoryList.addCategory(category)
  
    # Clear the existing images from the view
    self._imageList.clearImages()
    
    # Get the current category's images and add them to the ui
    for image in self._fileWatcher.getCategory(self._categoryList._currentCategory):
      self._imageList.addImage(image)

  # Center the window on the screen
  def _centerWindow(self):
    qr = self.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    self.move(qr.topLeft())

  # Refresh the files, then the ui
  def _fullRefresh(self):
    self._fileWatcher.refresh()
    self.refreshUI()

  # Refresh the ui when the category changes
  def _showCategory(self, cat):
    self.refreshUI()
  
  # Rename a category
  def _renameCategory(self, old, new):
    self._fileWatcher.renameCategory(old, new)
    self.refreshUI()
  
  # Delete a category
  def _removeCategory(self, category):
    self._fileWatcher.removeCategory(category)
    self.refreshUI()
  
  # Add an image to a category
  def _addImageCategory(self, image, category):
    self._fileWatcher.addImageCategory(image, category)
    self.refreshUI()
  
  # Remove an image from a category
  def _removeImageCategory(self, image, category):
    self._fileWatcher.removeImageCategory(image, category)
    self.refreshUI()
  
  # Remove an image from the index
  def _removeImageIndex(self, image):
    self._fileWatcher.removeImage(image)
    self.refreshUI()