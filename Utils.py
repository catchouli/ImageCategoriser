# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import ( QMessageBox, QInputDialog )

# Show warning box
def warningBox(message):
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