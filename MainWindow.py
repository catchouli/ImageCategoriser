# -*- coding: utf-8 -*-

import os
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

import Utils
from ImageList import ImageList
from CategoryList import CategoryList
from DirectoryMonitor import DirectoryMonitor

# The main window
class MainWindow(QMainWindow):
  def __init__(self, testDirectory):
    super().__init__()
    
    self._fileWatcher = DirectoryMonitor(testDirectory)
    
    # create the qt gui
    self._initUI()

  # Create the qt gui
  def _initUI(self):
    # Tooltip
    QToolTip.setFont(QFont('SansSerif', 10))
    self.setToolTip('this is a <b>widget</b>')
    
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
    self._categoryList = CategoryList(self, self._fileWatcher)
    self._categoryList.categoryChanged.connect(self._showCategory)
    layout.addWidget(self._categoryList)
    
    # Images
    self._imageList = ImageList(self, self._fileWatcher)
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
    print(f'changing category to {self._categoryList._currentCategory}')
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