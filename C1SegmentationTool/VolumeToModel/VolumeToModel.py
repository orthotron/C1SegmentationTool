import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# VolumeToModel
#

class VolumeToModel(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "VolumeToModel" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# VolumeToModelWidget
#

class VolumeToModelWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
      self.developerMode = True
      ScriptedLoadableModuleWidget.setup(self)


      ############################DENSE CORRESPONDENCE TAB############################
      ############################DENSE CORRESPONDENCE TAB############################
      ############################DENSE CORRESPONDENCE TAB############################
      #Adds a main tab
      self.mainTab = qt.QTabWidget()
      self.layout.addWidget(self.mainTab)

      # Libraries and Case Loading Tab
      CreateROI = qt.QTabWidget()
      self.mainTab.addTab(CreateROI, "CreateModel")

      # Layouts for Libraries and Case Loading Dropdown
      layout_main = qt.QFormLayout(CreateROI)
      layout_clipped = qt.QVBoxLayout()

      # Transforms
      self.clippedSelector = qt.QListWidget()
      self.clippedSelector.setSelectionMode(3) #Allows selection of multiple items in list by dragging mouse, holding ctrl, or shift
      self.clippedSelector.setDragDropMode(4) #Allows rearrangement of items in list via drag and drop

      # Buttons to Launch Dialog popup and delete selected models in medium resolution library list
      self.selectClipped = qt.QPushButton("Select Clipped Volumes")
      self.deleteClipped = qt.QPushButton("Delete Highlighted Clipped Volumes")

      # Add above widgets to layout
      layout_clipped.addWidget(self.clippedSelector)
      layout_clipped.addWidget(self.selectClipped)
      layout_clipped.addWidget(self.deleteClipped)

      # Create surrounding box to have a title for this medium resolution section
      clippedBox = qt.QGroupBox("Clipped Volumes")
      clippedBox.setLayout(layout_clipped)
      layout_main.addRow(clippedBox)

      self.selectClipped.connect('clicked(bool)', self.onSelectClipped)
      self.deleteClipped.connect('clicked(bool)', self.onDeleteClipped)


      self.thresholdminInput = qt.QLineEdit()
      self.thresholdminInput.toolTip = "Input the number of iterations to be performed"
      self.thresholdminInput.text = "150"
      self.threshold_min = float(self.thresholdminInput.text)
      layout_main.addRow("Min Threshold: ", self.thresholdminInput)

      self.thresholdmaxInput = qt.QLineEdit()
      self.thresholdmaxInput.toolTip = "Input the number of iterations to be performed"
      self.thresholdmaxInput.text = "150"
      self.threshold_max = float(self.thresholdmaxInput.text)
      layout_main.addRow("Max Threshold: ", self.thresholdmaxInput)


      self.holeFillInput = qt.QLineEdit()
      self.holeFillInput.toolTip = "Input the number of iterations to be performed"
      self.holeFillInput.text = "4.00"
      self.holeFill = float(self.holeFillInput.text)
      layout_main.addRow("Hole Fill Kernel Size(mm): ", self.holeFillInput)


      self.gaussianInput = qt.QLineEdit()
      self.gaussianInput.toolTip = "Input the number of iterations to be performed"
      self.gaussianInput.text = "3.00"
      self.gaussian = float(self.gaussianInput.text)
      layout_main.addRow("Gaussian Kernel Size(mm): ", self.gaussianInput)


      self.findModel = qt.QPushButton("Create Models from Segments")
      self.findModel.toolTip = "Creates models from segments"
      self.findModel.setMinimumWidth(300)

      layout_main.addRow(self.findModel)
      self.findModel.connect('clicked(bool)', self.onRunButton)


  def onRunButton(self):
      #runs DenseCorrespondence when run button is pressed
      logic = VolumeToModelLogic(self.threshold_min, self.threshold_max, self.holeFill, self.gaussian, self.clippedSelector)
      logic.run()

  def onSelectClipped(self):
      logic = ModelSelector()
      logic.runClippedSelect(self.clippedSelector)

  def onDeleteClipped(self):
      toDelete = self.clippedSelector.currentRow
      self.clippedSelector.takeItem(toDelete)


  #
  # CreateROILogic
  #
#
# VolumeToModelLogic
#

class VolumeToModelLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  def __init__(self, thresholdMin = 150.00, thresholdMax = 2034.00, holeFill = 4.00, gaussian = 3.00, clippedListWidget = None):
      self.clippedListWidget = clippedListWidget
      self.thresholdMin = thresholdMin
      self.thresholdMax = thresholdMax
      self.holeFill = holeFill
      self.gaussian = gaussian

      self.clippedNameList = []
      self.segmentationNameList = []

      self.clippedList = []
      self.segmentationList = []
  
  def pair(self):
        
        for node in range(self.clippedListWidget.count):
            clippedVol = self.clippedListWidget.item(node).text()
            self.clippedNameList.append(clippedVol)
            clippedVolNode = slicer.util.getNode(clippedVol)
            self.clippedList.append(clippedVolNode)
            segNode = self.addSegmentationNodes(clippedVolNode, clippedVol)
            self.segmentationList.append(segNode)        

      
  def addSegmentationNodes(self, volume=None, name=None):      
        # Create MRML transform node
        segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        segmentationNode.CreateDefaultDisplayNodes() # only needed for display
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(volume)
        addedSegmentID = segmentationNode.GetSegmentation().AddEmptySegment(str(name) + "_C1")
        return segmentationNode
    
  def run(self):
        #creates list  that contains clipped volume and segmentation nodes 
        self.pair()
        
        #zips the lists so they can be used for the for loop
        nodePair = zip(self.clippedList, self.segmentationList)
        
        for volume, segmentation in nodePair:
            # Create segment editor to get access to effects
            segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
            segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
            segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
            segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
            segmentEditorWidget.setSegmentationNode(segmentation)
            segmentEditorWidget.setMasterVolumeNode(volume)
            
            # Thresholding
            segmentEditorWidget.setActiveEffectByName("Threshold")
            effect = segmentEditorWidget.activeEffect()
            effect.setParameter("MinimumThreshold", self.thresholdMin)
            effect.setParameter("MaximumThreshold", self.thresholdMax)
            effect.self().onApply()
            
            # Islands
            segmentEditorWidget.setActiveEffectByName("Islands")
            effect = segmentEditorWidget.activeEffect()
            effect.setParameter("Operation", "KEEP_LARGEST_ISLAND")            
            effect.self().onApply()
            
            # Smoothing
            segmentEditorWidget.setActiveEffectByName("Smoothing")
            effect = segmentEditorWidget.activeEffect()
            effect.setParameter("SmoothingMethod", "GAUSSIAN")
            effect.setParameter("GaussianStandardDeviationMm", 4)
            effect.self().onApply()
            
            # Clean up
            segmentEditorWidget = None
            slicer.mrmlScene.RemoveNode(segmentEditorNode)
            
            # Make segmentation results visible in 3D
            segmentation.CreateClosedSurfaceRepresentation()
        return True

class ModelSelector():

  # Handler for Select Med Res Library Models
  def runClippedSelect(self, finalList):
      # Create list of models to choose from and select for dialog
      self.finalList = finalList
      self.list = qt.QListWidget()
      self.list.setSelectionMode(3)
      nodeDict = slicer.mrmlScene.GetNodesByClass('vtkMRMLScalarVolumeNode')

      for i in range(0, nodeDict.GetNumberOfItems()):
          self.list.addItem(nodeDict.GetItemAsObject(i).GetName())

      self.addButton = qt.QPushButton('Add Clipped Volumes')
      self.addButton.connect('clicked(bool)', self.onAddButton)

      # Create and launch dialog with list of models to choose from and select
      self.dialog = qt.QDialog()
      dialogLayout = qt.QFormLayout()
      dialogLayout.addWidget(self.list)
      dialogLayout.addWidget(self.addButton)
      self.dialog.setLayout(dialogLayout)
      self.dialog.exec_()



  def onAddButton(self):
      chosenOnes = self.list.selectedItems()
      for one in chosenOnes:
        self.finalList.addItem(one.text())
      self.dialog.close()


class VolumeToModelTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_VolumeToModel1()

  def test_VolumeToModel1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = VolumeToModelLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
