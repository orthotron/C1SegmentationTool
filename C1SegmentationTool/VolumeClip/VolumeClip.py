import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import VolumeClipWithRoi 
#
# VolumeClip
#

class VolumeClip(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "VolumeClip" # TODO make this more human readable by adding spaces
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
# VolumeClipWidget
#

class VolumeClipWidget(ScriptedLoadableModuleWidget):
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
        VolumeClip = qt.QTabWidget()
        self.mainTab.addTab(VolumeClip, "VolumeClip")

        # Layouts for Libraries and Case Loading Dropdown
        layout_main = qt.QFormLayout(VolumeClip)
        layout_vol = qt.QVBoxLayout()
        layout_roi = qt.QVBoxLayout()

        # Transforms
        self.volSelector = qt.QListWidget()
        self.volSelector.setSelectionMode(3) #Allows selection of multiple items in list by dragging mouse, holding ctrl, or shift
        self.volSelector.setDragDropMode(4) #Allows rearrangement of items in list via drag and drop

        # Buttons to Launch Dialog popup and delete selected models in medium resolution library list
        self.selectVol = qt.QPushButton("Select Volumes")
        self.deleteVol = qt.QPushButton("Delete Highlighted Volumes")

        # Add above widgets to layout
        layout_vol.addWidget(self.volSelector)
        layout_vol.addWidget(self.selectVol)
        layout_vol.addWidget(self.deleteVol)

        # Create surrounding box to have a title for this medium resolution section
        volBox = qt.QGroupBox("Volumes")
        volBox.setLayout(layout_vol)
        layout_main.addRow(volBox)


        # Fiducials
        self.roiSelector = qt.QListWidget()
        self.roiSelector.setSelectionMode(3) #Allows selection of multiple items in list by dragging mouse, holding ctrl, or shift
        self.roiSelector.setDragDropMode(4) #Allows rearrangement of items in list via drag and drop

        # Buttons to Launch Dialog popup and delete selected models in medium resolution library list
        self.selectRoi = qt.QPushButton("Select Roi")
        self.deleteRoi = qt.QPushButton("Delete Highlighted Roi")

        # Add above widgets to layout
        layout_roi.addWidget(self.roiSelector)
        layout_roi.addWidget(self.selectRoi)
        layout_roi.addWidget(self.deleteRoi)

        # Create surrounding box to have a title for this medium resolution section
        roiBox = qt.QGroupBox("ROIs")
        roiBox.setLayout(layout_roi)
        layout_main.addRow(roiBox)


        self.selectVol.connect('clicked(bool)', self.onSelectVol)
        self.selectRoi.connect('clicked(bool)', self.onSelectRoi)
        self.deleteVol.connect('clicked(bool)', self.onDeleteVol)
        self.deleteRoi.connect('clicked(bool)', self.onDeleteRoi)

        self.clipVol = qt.QPushButton("Clip Volume")
        self.clipVol.toolTip = "Clips volume with ROI boxes"
        self.clipVol.setMinimumWidth(300)

        layout_main.addRow(self.clipVol)
        self.clipVol.connect('clicked(bool)', self.onRunButton)


    def onRunButton(self):
        #runs DenseCorrespondence when run button is pressed
        logic = VolumeClipLogic(self.volSelector, self.roiSelector)
        logic.run()

    def onSelectVol(self):
        logic = ModelSelector()
        logic.runVolSelect(self.volSelector)

    def onSelectRoi(self):
        logic = ModelSelector()
        logic.runRoiSelect(self.roiSelector)

    def onDeleteVol(self):
        toDelete = self.volSelector.currentRow
        self.volSelector.takeItem(toDelete)

    def onDeleteRoi(self):
        toDelete = self.roiSelector.currentRow
        self.roiSelector.takeItem(toDelete)
        #
        # CreateROILogic
        #

#
# VolumeClipLogic
#

class VolumeClipLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  def __init__(self, volListWidget = None, roiListWidget = None):
    self.volListWidget = volListWidget
    self.roiListWidget = roiListWidget
    self.volNameList = []
    self.roiNameList = []

    self.volList = []
    self.roiList = []
  def pair(self):
    if(self.volListWidget.count == 0 or self.roiListWidget.count ==0):
      print("No Nodes in one or both lists!")
      return 0,[]

    if(self.volListWidget.count != self.roiListWidget.count):
      print("Number of transform and fiducial points does not match")
      return 0,[]

    for node in range(self.volListWidget.count):
      self.volNameList.append(self.volListWidget.item(node).text())
      self.roiNameList.append(self.roiListWidget.item(node).text())

    paired = zip(self.volNameList, self.roiNameList)

    for vol, roi in paired:
      vol_node = slicer.util.getNode(vol)
      roi_node = slicer.util.getNode(roi)
      self.volList.append(vol_node)
      self.roiList.append(roi_node)


  def run(self):
    self.pair()
    
    nodePair = zip(self.volList, self.roiList)

    for volume, roi in nodePair:
      name = "clipped" + roi.GetName()[-3:]
      clippedNode = slicer.vtkMRMLScalarVolumeNode()
      clippedNode.SetName(name)
      slicer.mrmlScene.AddNode(clippedNode)

      vcr = VolumeClipWithRoi.VolumeClipWithRoiLogic()


      vcr.clipVolumeWithRoi(roi, volume, 0.00, "1", clippedNode)



class ModelSelector():

    # Handler for Select Med Res Library Models
    def runVolSelect(self, finalList):
        # Create list of models to choose from and select for dialog
        self.finalList = finalList
        self.list = qt.QListWidget()
        self.list.setSelectionMode(3)
        nodeDict = slicer.mrmlScene.GetNodesByClass('vtkMRMLVolumeNode')

        for i in range(0, nodeDict.GetNumberOfItems()):
            self.list.addItem(nodeDict.GetItemAsObject(i).GetName())

        self.addButton = qt.QPushButton('Add Volumes')
        self.addButton.connect('clicked(bool)', self.onAddButton)

        # Create and launch dialog with list of models to choose from and select
        self.dialog = qt.QDialog()
        dialogLayout = qt.QFormLayout()
        dialogLayout.addWidget(self.list)
        dialogLayout.addWidget(self.addButton)
        self.dialog.setLayout(dialogLayout)
        self.dialog.exec_()

    # Handler for Select High Res Library Models button
    def runRoiSelect(self, finalList):

        # Create list of models to choose from and select for dialog
        self.finalList = finalList
        self.list = qt.QListWidget()
        self.list.setSelectionMode(3)
        nodeDict = slicer.mrmlScene.GetNodesByClass('vtkMRMLAnnotationROINode')

        for i in range(0, nodeDict.GetNumberOfItems()):
            self.list.addItem(nodeDict.GetItemAsObject(i).GetName())

        self.addButton = qt.QPushButton('Add ROI Boxes')
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



class VolumeClipTest(ScriptedLoadableModuleTest):
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
    self.test_VolumeClip1()

  def test_VolumeClip1(self):
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
    logic = VolumeClipLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
