# -*- coding: utf-8 -*-

import os
import threading
import json
from pathlib import Path

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
    self.rootDir = Path(dir)
    self.categoryList = [ "Uncategorised", "All" ]
    self.files = {}
    self.saveTimer = None
    self.load()
    
  def load(self):
    configPath = self.configFile().resolve()
    if os.path.isfile(str(configPath)):
      with open(str(configPath), 'r') as f:
        cfg = json.load(f)
        for path, categories in cfg['images'].items():
          fromRootDir = Path(path)
          name = fromRootDir.parts[-1]
          image = Image(name, fromRootDir, self.rootDir)
          image.categories = categories
          self.files[fromRootDir] = image
          for category in image.categories:
            if category not in self.categoryList:
              self.categoryList.append(category)
              self.sortCategoryList()
    else:
      print(f'no config file found at {str(configPath)}, starting from scratch')

  def save(self):
    self.clearSaveTimer()
    configPath = self.configFile().resolve()
    
    # save backup as -2 first
    if os.path.isfile(str(configPath)):
      backupPath = self.configFile('-2').resolve()
      print(f'saving old config file as {str(backupPath)}')
      os.replace(str(configPath), str(backupPath))
    
    print(f'saving config file to {str(configPath)}')
    cfg = { 'images': {} }
    for _, image in self.files.items():
      cfg['images'][str(image.fromRootDir)] = image.categories
    with open(str(configPath), 'w') as f:
      json.dump(cfg, f)
  
  def setSaveTimer(self):
    self.clearSaveTimer()

    # start new timer
    self.saveTimer = threading.Timer(5, self.saveTimerCallback)
    self.saveTimer.start()
    print('save timer set')
  
  def clearSaveTimer(self):
    if self.saveTimer != None:
      self.saveTimer.cancel()
      self.saveTimer = None
      print('save timer cleared')

  def saveTimerCallback(self):
    print('save timer elapsed, saving')
    self.saveTimer = None
    self.save()

  def configFile(self, suffix=''):
    return self.rootDir / f"config{suffix}.json"
  
  # Refresh the folder
  def refresh(self):
    for subdir, dirs, files in os.walk(str(self.rootDir.resolve())):
        for file in files:
          # construct path
          path = Path(subdir) / Path(file)
          
          # trim rootDir
          fromRootDir = path.relative_to(self.rootDir)
          
          # get name
          name = path.parts[-1]
          
          # skip config files
          if path.suffix == '.json':
            continue
          
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
  
  # Remove an image from the index
  def removeImage(self, image):
    if image.fromRootDir in self.files:
      del self.files[image.fromRootDir]

  # Add an image to a category, and add the category to the list if it doesn't exist
  def addImageCategory(self, image, category):
    if category == 'All' or category == 'Uncategorised':
      return

    print(f'adding image {image.name} to category {category}')
  
    if image.fromRootDir in self.files:  
      if category not in self.categoryList:
        self.categoryList.append(category)
        self.sortCategoryList()
        
      if category not in self.files[image.fromRootDir].categories:
        self.files[image.fromRootDir].categories.append(category)

    self.setSaveTimer()

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
      self.sortCategoryList()

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
      self.categoryList.append(newName)
      self.sortCategoryList()
  
  # Sort the category list
  def sortCategoryList(self):
    # Make sure it goes [Uncategorised, All, ...]
    self.categoryList.remove('Uncategorised')
    self.categoryList.remove('All')
    self.categoryList.sort()
    self.categoryList.insert(0, 'All')
    self.categoryList.insert(0, 'Uncategorised')