# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
import time
import queue

from PyQt5 import QtCore
from PyQt5.QtCore import ( QVariant, pyqtSignal )
from PyQt5.QtGui import ( QFont, QIcon, QPixmap )
from PyQt5.QtWidgets import ( QApplication, QMainWindow, QWidget, QListView
                            , QToolTip, QPushButton, QMessageBox, QDesktopWidget
                            , QAction, QHBoxLayout, QGridLayout, QListWidget
                            , QListWidgetItem, QMenu, QInputDialog, QAbstractItemView )

import Utils

# A category list
class CategoryList(QListWidget):
  categoryChanged = pyqtSignal(str)

  def __init__(self, mainWindow, fileWatcher):
    super().__init__()
    
    self._mainWindow = mainWindow
    self._fileWatcher = fileWatcher
    
    self._currentCategory = None
    self._categories = {}
    
    self.setMaximumWidth(200)
    self.currentItemChanged.connect(self._categoryChanged)
    self.installEventFilter(self)
  
  # Add a category to the ui
  def addCategory(self, name):
    if name not in self._categories:
      item = QListWidgetItem(name)
      self._categories[name] = item
      self.insertItem(self.count(), item)

  # Remove a category from the ui
  def removeCategory(self, name):
    if name in self._categories:
      item = self._categories.pop(name)
      self.removeItemWidget(item)

  # Remove all categories from the ui
  def clearCategories(self):
    self._categories = {}
    self.clear()

  # Event filter for QListWidget context menus
  def eventFilter(self, source, event):  
    # Handle context events for the categories list
    if event.type() == QtCore.QEvent.ContextMenu:
      item = source.itemAt(event.pos())
      if item != None:
        self._createCategoryMenu(event.globalPos(), item)
      return True      
    return False
  
  # Called when a different category is selected in the list
  def _categoryChanged(self, curr, prev):
    self._currentCategory = curr.text()
    self.categoryChanged.emit(self._currentCategory)

  # Create the 'background' menu for the category list
  def _createCategoryMenu(self, pos, item):
    category = item.text()
    
    menu = QMenu()
    
    deleteCategoryAction = QAction(f'Delete {category}')
    deleteCategoryAction.triggered.connect(lambda _: self._contextDeleteCategory(category))
    menu.addAction(deleteCategoryAction)
    
    renameCategoryAction = QAction(f'Rename {category}')
    renameCategoryAction.triggered.connect(lambda _: self._contextRenameCategory(category))
    menu.addAction(renameCategoryAction)
    
    if category == 'All' or category == 'Uncategorised':
      deleteCategoryAction.setDisabled(True)
      renameCategoryAction.setDisabled(True)
    
    menu.show()
    menu.exec_(pos)
      
    return menu
  
  def _contextDeleteCategory(self, category):
    self._fileWatcher.removeCategory(category)
    self._mainWindow.refreshUI()
  
  def _contextRenameCategory(self, category):
    newName = Utils.promptCategoryName(self)
    if newName != None:
      self._fileWatcher.renameCategory(category, newName)
      self._mainWindow.refreshUI()