#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import ( QApplication )
from UserInterface import ImageCategoriserWindow

# The test directory
testDirectory = 'C:\\Users\\nano\\Pictures\\art'
IconSize = 512

# Entry, create the main window and then exit when it exits
if __name__ == '__main__':
  app = QApplication(sys.argv)
  img = ImageCategoriserWindow()  
  res = app.exec_()
  img.exiting()
  sys.exit(res)