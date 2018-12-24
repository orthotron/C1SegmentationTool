import os
import unittest
import vtk, qt, ctk, slicer
from vtk.util import numpy_support as nps
from slicer.ScriptedLoadableModule import *
import logging
import time
import numpy as np
from numpy import linalg as la
import sys
import os.path


refSkullNode = None


#Function to obtain numpy array of a vtkmrmlmodelnode
def obtainNpArray(ModelNode):
  points = ModelNode.GetPolyData().GetPoints().GetData()
  ModelArray = nps.vtk_to_numpy(points)
  return ModelArray


class DenseCorrespondenceFid(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "DenseCorrespondenceFid" # TODO make this more human readable by adding spaces
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
# DenseCorrespondenceFidWidget
#

class DenseCorrespondenceFidWidget(ScriptedLoadableModuleWidget):

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
        DenseCorr = qt.QTabWidget()
        self.mainTab.addTab(DenseCorr, "DenseCorrespondence")

        # Layouts for Libraries and Case Loading Dropdown
        layout_main = qt.QFormLayout(DenseCorr)
        layout_post = qt.QVBoxLayout()

        # Post
        self.postSelector = qt.QListWidget()
        self.postSelector.setSelectionMode(3) #Allows selection of multiple items in list by dragging mouse, holding ctrl, or shift
        self.postSelector.setDragDropMode(4) #Allows rearrangement of items in list via drag and drop

        # Buttons to Launch Dialog popup and delete selected models in medium resolution library list
        self.selectPost = qt.QPushButton("Select Target Fiducials")
        self.deletePost = qt.QPushButton("Delete Highlighted Fiducial")

        # Add above widgets to layout
        layout_post.addWidget(self.postSelector)
        layout_post.addWidget(self.selectPost)
        layout_post.addWidget(self.deletePost)

        # Create surrounding box to have a title for this medium resolution section
        postBox = qt.QGroupBox("Target")
        postBox.setLayout(layout_post)
        layout_main.addRow(postBox)

        # Individual model selector to set a model as being the "Case"
        self.refFidSelector = slicer.qMRMLNodeComboBox()
        self.refFidSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.refFidSelector.selectNodeUponCreation = False
        self.refFidSelector.addEnabled = False
        self.refFidSelector.removeEnabled = False
        self.refFidSelector.noneEnabled = True
        self.refFidSelector.showHidden = False
        self.refFidSelector.showChildNodeTypes = False
        self.refFidSelector.setMRMLScene(slicer.mrmlScene)
        self.refFidSelector.setToolTip("Select the fiducial that will be the reference:")
        layout_main.addRow("Reference Fiducial: ", self.refFidSelector)


        # Individual model selector to set a model as being the "Case"
        self.refSelector = slicer.qMRMLNodeComboBox()
        self.refSelector.nodeTypes = ["vtkMRMLModelNode"]
        self.refSelector.selectNodeUponCreation = False
        self.refSelector.addEnabled = False
        self.refSelector.removeEnabled = False
        self.refSelector.noneEnabled = True
        self.refSelector.showHidden = False
        self.refSelector.showChildNodeTypes = False
        self.refSelector.setMRMLScene(slicer.mrmlScene)
        self.refSelector.setToolTip("Select the C1 model that will be the reference:")
        layout_main.addRow("Reference C1: ", self.refSelector)


        self.selectPost.connect('clicked(bool)', self.onSelectPost)
        self.deletePost.connect('clicked(bool)', self.onDeletePost)

        self.findTransforms = qt.QPushButton("Establish Dense Correspondence")
        self.findTransforms.toolTip = "Establishes dense correspondence "
        self.findTransforms.setMinimumWidth(300)

        layout_main.addRow(self.findTransforms)
        self.findTransforms.connect('clicked(bool)', self.onRunButton)


    def onRunButton(self):
        logic = DenseCorrespondenceFidLogic(self.postSelector, self.refFidSelector.currentNode(), self.refSelector.currentNode())
        logic.guiRun()

    def onSelectPost(self):
        logic = ModelSelector()
        logic.runPostSelect(self.postSelector)


    def onDeletePost(self):
        toDelete = self.postSelector.currentRow
        self.postSelector.takeItem(toDelete)


class DenseCorrespondenceFidLogic(ScriptedLoadableModuleLogic):
    def __init__(self, postlistWidget=None, referenceFid = None, referenceModel=None):
        self.postlistWidget = postlistWidget
        self.referenceFid = referenceFid
        self.referenceModel = referenceModel


        #The naming convention referes to target and post as the same thing.  


    def guiRun(self):
        #run funcion when dealing with gui
        targetNameList = []
        targetFid = []


        for model in range(0,self.postlistWidget.count):
            targetNameList.append(self.postlistWidget.item(model).text())

        for target in targetNameList:
            target_node = slicer.util.getNode(target)
            targetFid.append(target_node)

        self.run(targetFid, self.referenceFid, self.referenceModel)

    def run(self, targetFidList, referenceFid, referenceModel):
        """Run the actual algorithm""" 
        scene = slicer.mrmlScene
        fidRegNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLFiducialRegistrationWizardNode')
        fidRegNode.SetUpdateModeToAuto()
        fidRegNode.SetRegistrationModeToWarping()

        for fid in targetFidList:
          #make a copy of the reference skull 
            transformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode')
            fidRegNode.SetAndObserveFromFiducialListNodeId(referenceFid.GetID())
            fidRegNode.SetAndObserveToFiducialListNodeId(fid.GetID())
            fidRegNode.SetOutputTransformNodeId(transformNode.GetID())

            refModelNode = slicer.vtkMRMLModelNode()
            refModelPolyData = vtk.vtkPolyData()
            refModelPolyData.DeepCopy(referenceModel.GetPolyData())
            refModelNode.SetAndObservePolyData(refModelPolyData)
            tag = fid.GetName()[0:3]
            name = tag+'_ref'
            refModelNode.SetName(name)
            slicer.mrmlScene.AddNode(refModelNode)

            refModelNode.SetAndObserveTransformNodeID(transformNode.GetID())
            refModelNode.HardenTransform()

            # slicer.mrmlScene.RemoveNode(preModel)
            # slicer.mrmlScene.RemoveNode(postModel)

        return True


class ModelSelector():



    # Handler for Select High Res Library Models button
    def runPostSelect(self, finalList):

        # Create list of models to choose from and select for dialog
        self.finalList = finalList
        self.list = qt.QListWidget()
        self.list.setSelectionMode(3)
        nodeDict = slicer.mrmlScene.GetNodesByClass('vtkMRMLMarkupsFiducialNode')

        for i in range(0, nodeDict.GetNumberOfItems()):
            self.list.addItem(nodeDict.GetItemAsObject(i).GetName())

        self.addButton = qt.QPushButton('Add Models')
        self.addButton.connect('clicked(bool)', self.onAddButton)

        # Create and launch dialog with list of models to choose from and select
        self.dialog = qt.QDialog()
        dialogLayout = qt.QFormLayout()
        dialogLayout.addWidget(self.list)
        dialogLayout.addWidget(self.addButton)
        self.dialog.setLayout(dialogLayout)
        self.dialog.exec_()

    # Handler for Select High Res Library Models button
    def runModelSelect(self, finalList):
        # Create list of models to choose from and select for dialog
        self.finalList = finalList
        self.list = qt.QListWidget()
        self.list.setSelectionMode(3)
        nodeDict = slicer.mrmlScene.GetNodesByClass('vtkMRMLModelNode')

        for i in range(0, nodeDict.GetNumberOfItems()):
            self.list.addItem(nodeDict.GetItemAsObject(i).GetName())

        self.addButton = qt.QPushButton('Add Models')
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

class DenseCorrespondenceFidTest(ScriptedLoadableModuleTest):
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
    self.test_DenseCorrespondenceFid1()

  def test_DenseCorrespondenceFid1(self):
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
    logic = DenseCorrespondenceFidLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
