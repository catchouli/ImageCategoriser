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

# Show warning box
def warningBox( message):
  msg = QMessageBox()
  msg.setIcon(QMessageBox.Warning)
  msg.setText(message)
  msg.setWindowTitle('Warning')
  msg.exec_()

# Prompt the user for a category name
def promptCategoryName(win):
  item, ok = QInputDialog.getText(win, 'Category name', 'Enter category name')
  if ok:
    if item != '':
      return item
    else:
      warningBox('No category name provided')
      return None
  else:
    return None