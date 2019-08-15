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
    self._rootDir = Path(dir)
    self._categoryList = [ "Uncategorised", "All" ]
    self._files = {}
    
    # Saving
    self._saveTimer = None
    self._saveTime = 5 # The time after any changes to save
    
    # Load initial state
    self._load()

  # Save out to disk
  def save(self):
    self._clearSaveTimer()
    configPath = self._configFile().resolve()
    
    # save backup as -2 first
    if os.path.isfile(str(configPath)):
      backupPath = self._configFile('-2').resolve()
      print(f'saving old config file as {str(backupPath)}')
      os.replace(str(configPath), str(backupPath))
    
    print(f'saving config file to {str(configPath)}')
    cfg = { 'images': {} }
    for _, image in self._files.items():
      cfg['images'][str(image.fromRootDir)] = image.categories
    with open(str(configPath), 'w') as f:
      json.dump(cfg, f)
  
  # Refresh the folder, adding any new images
  def refresh(self):
    for subdir, dirs, files in os.walk(str(self._rootDir.resolve())):
        for file in files:
          # construct path
          path = Path(subdir) / Path(file)
          
          # trim rootDir
          fromRootDir = path.relative_to(self._rootDir)
          
          # get name
          name = path.parts[-1]
          
          # skip config files
          if path.suffix == '.json':
            continue
          
          # create image object
          image = Image(name, fromRootDir, self._rootDir)
          
          # add image
          if fromRootDir not in self._files:
            self._files[fromRootDir] = image
    
  # Get a list of categories
  def getCategories(self):
    return self._categoryList

  # Get all the images in a category
  def getCategory(self, category):
    images = set()
    
    for file, image in self._files.items():
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
    if image.fromRootDir in self._files:
      del self._files[image.fromRootDir]

  # Add an image to a category, and add the category to the list if it doesn't exist
  def addImageCategory(self, image, category):
    if category == 'All' or category == 'Uncategorised':
      return

    print(f'adding image {image.name} to category {category}')
  
    if image.fromRootDir in self._files:  
      if category not in self._categoryList:
        self._categoryList.append(category)
        self._sortCategoryList()
        
      if category not in self._files[image.fromRootDir].categories:
        self._files[image.fromRootDir].categories.append(category)

    self._setSaveTimer(self._saveTime)

  # Remove an image from a category
  def removeImageCategory(self, image, category):
    if category == 'All' or category == 'Uncategorised':
      return
      
    if image.fromRootDir in self._files:
      if category in self._files[image.fromRootDir].categories:
        self._files[image.fromRootDir].categories.remove(category)

  # Remove a category and make sure all images no longer list it
  def removeCategory(self, category):
    if category == 'All' or category == 'Uncategorised':
      return
      
    if category in self._categoryList:
      for pathFromBase, image in self._files.items():
        if category in image.categories:
          image.categories.remove(category)
      self._categoryList.remove(category)
      self._sortCategoryList()

  # Rename a category and make sure all images no longer list it
  def renameCategory(self, category, newName):
    if category == 'All' or category == 'Uncategorised':
      return
    if newName == 'All' or newName == 'Uncategorised':
      return
    
    if newName in self._categoryList:
      return
      
    if category in self._categoryList:
      for pathFromBase, image in self._files.items():
        if category in image.categories:
          image.categories.remove(category)
          image.categories.append(newName)
      
      self._categoryList.remove(category)
      self._categoryList.append(newName)
      self._sortCategoryList()
    
  # Load in from disk
  def _load(self):
    configPath = self._configFile().resolve()
    if os.path.isfile(str(configPath)):
      with open(str(configPath), 'r') as f:
        cfg = json.load(f)
        for path, categories in cfg['images'].items():
          fromRootDir = Path(path)
          name = fromRootDir.parts[-1]
          image = Image(name, fromRootDir, self._rootDir)
          image.categories = categories
          self._files[fromRootDir] = image
          for category in image.categories:
            if category not in self._categoryList:
              self._categoryList.append(category)
              self._sortCategoryList()
    else:
      print(f'no config file found at {str(configPath)}, starting from scratch')

  # Set an n second time after which if this function isn't called again a save will be triggered
  def _setSaveTimer(self, n):
    self._clearSaveTimer()

    # start new timer
    self._saveTimer = threading.Timer(n, self._saveTimerCallback)
    self._saveTimer.start()
    print('save timer set')
  
  # Clear the save timer started by _setSaveTimer
  def _clearSaveTimer(self):
    if self._saveTimer != None:
      self._saveTimer.cancel()
      self._saveTimer = None
      print('save timer cleared')

  # Handles the asve timer elapsing
  def _saveTimerCallback(self):
    print('save timer elapsed, saving')
    self._saveTimer = None
    self.save()

  # The config file path
  def _configFile(self, suffix=''):
    return self._rootDir / f"config{suffix}.json"
  
  # Sort the category list
  def _sortCategoryList(self):
    # Make sure it goes [Uncategorised, All, ...]
    self._categoryList.remove('Uncategorised')
    self._categoryList.remove('All')
    self._categoryList.sort()
    self._categoryList.insert(0, 'All')
    self._categoryList.insert(0, 'Uncategorised')