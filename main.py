#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import ( QApplication, QMainWindow, QWidget, QListView
                            , QToolTip, QPushButton, QMessageBox, QDesktopWidget
                            , QAction, QHBoxLayout, QGridLayout, QListWidget )
from PyQt5.QtGui import QFont

# The main window
class Img(QMainWindow):
  def __init__(self):
    super().__init__()
    self.initUI()

  def initUI(self):
    # Tooltip
    QToolTip.setFont(QFont('SansSerif', 10))
    self.setToolTip('this is a <b>widget</b>')
    
    # Menu
    menubar = self.menuBar()
    fileMenu = menubar.addMenu('File')
    
    refreshAction = QAction('Refresh', self)
    refreshAction.triggered.connect(self.refresh)
    fileMenu.addAction(refreshAction)
    
    # Main widget
    wid = QWidget(self)
    self.setCentralWidget(wid)
    
    # Layout
    layout = QHBoxLayout()
    wid.setLayout(layout)
    
    # Categories
    categories = QListWidget()
    categories.insertItem(0, "Red")
    categories.insertItem(1, "Orange")
    categories.insertItem(2, "Blue")
    categories.insertItem(3, "White")
    categories.insertItem(4, "Green")
    layout.addWidget(categories)
    
    # Images
    images = QListWidget()
    images.insertItem(0, "Red")
    images.insertItem(1, "Orange")
    images.insertItem(2, "Blue")
    images.insertItem(3, "White")
    images.insertItem(4, "Green")
    layout.addWidget(images)
    
    # Buttons
    btn = QPushButton('Buton A', self)
    btn.clicked.connect(QApplication.instance().quit)
    btn.setToolTip('butn')
    #btn.resize(btn.sizeHint())
    #btn.move(50, 50)
    layout.addWidget(btn)
    
    btn2 = QPushButton('Buton B', self)
    btn2.clicked.connect(QApplication.instance().quit)
    btn2.setToolTip('butn')
    #btn2.resize(btn2.sizeHint())
    #btn2.move(150, 50)
    layout.addWidget(btn2)
    
    # Window position and size
    self.resize(300, 300)
    self.center()
    self.setWindowTitle('tooltips')
    self.show()
    
  def center(self):
    qr = self.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    self.move(qr.topLeft())
  
  def refresh(self):
    print('refreshing')

  def closeEvent(self, event):
    # Prompt the user and then quit
    reply = QMessageBox.question(self, 'Quit',
      'Are you sure you want to quit?',
      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
      
    if reply == QMessageBox.Yes:
      event.accept()
    else:
      event.ignore()

if __name__ == '__main__':
  app = QApplication(sys.argv)
  img = Img()  
  sys.exit(app.exec_())