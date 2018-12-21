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


#
# CreateROI
#

class CreateROI(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "CreateROI" # TODO make this more human readable by adding spaces
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
# CreateROIWidget
#

class CreateROIWidget(ScriptedLoadableModuleWidget):
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
        self.mainTab.addTab(CreateROI, "CreateROI")

        # Layouts for Libraries and Case Loading Dropdown
        layout_main = qt.QFormLayout(CreateROI)
        layout_vol = qt.QVBoxLayout()
        layout_fid = qt.QVBoxLayout()

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
        self.fidSelector = qt.QListWidget()
        self.fidSelector.setSelectionMode(3) #Allows selection of multiple items in list by dragging mouse, holding ctrl, or shift
        self.fidSelector.setDragDropMode(4) #Allows rearrangement of items in list via drag and drop

        # Buttons to Launch Dialog popup and delete selected models in medium resolution library list
        self.selectFid = qt.QPushButton("Select Fiducials")
        self.deleteFid = qt.QPushButton("Delete Highlighted Fiducials")

        # Add above widgets to layout
        layout_fid.addWidget(self.fidSelector)
        layout_fid.addWidget(self.selectFid)
        layout_fid.addWidget(self.deleteFid)

        # Create surrounding box to have a title for this medium resolution section
        fidBox = qt.QGroupBox("Fiducials")
        fidBox.setLayout(layout_fid)
        layout_main.addRow(fidBox)


        self.selectVol.connect('clicked(bool)', self.onSelectVol)
        self.selectFid.connect('clicked(bool)', self.onSelectFid)
        self.deleteVol.connect('clicked(bool)', self.onDeleteVol)
        self.deleteFid.connect('clicked(bool)', self.onDeleteFid)

        self.findROI = qt.QPushButton("Create ROI Boxes")
        self.findROI.toolTip = "Creates ROI Boxes"
        self.findROI.setMinimumWidth(300)

        layout_main.addRow(self.findROI)
        self.findROI.connect('clicked(bool)', self.onRunButton)


    def onRunButton(self):
        #runs DenseCorrespondence when run button is pressed
        logic = CreateROILogic(self.volSelector, self.fidSelector)
        logic.run()

    def onSelectVol(self):
        logic = ModelSelector()
        logic.runVolSelect(self.volSelector)

    def onSelectFid(self):
        logic = ModelSelector()
        logic.runFidSelect(self.fidSelector)

    def onDeleteVol(self):
        toDelete = self.volSelector.currentRow
        self.volSelector.takeItem(toDelete)

    def onDeleteFid(self):
        toDelete = self.fidSelector.currentRow
        self.fidSelector.takeItem(toDelete)
    #
    # CreateROILogic
    #

class CreateROILogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    def __init__(self, volListWidget = None, fidListWidget = None):
        self.volListWidget = volListWidget
        self.fidListWidget = fidListWidget
        self.volumeNameList = []
        self.fiducialNameList = []

        self.volumeList = []
        self.fiducialList = []

    def pair(self):

        if(self.volListWidget.count == 0 or self.fidListWidget.count == 0):
            print("No nodes in one or both lists!")
            return 0,[]

        if(self.volListWidget.count != self.fidListWidget.count):
            print("Number of transform and fiducial points does not match")
            return 0,[]

        for node in range(self.volListWidget.count):
            self.volumeNameList.append(self.volListWidget.item(node).text())
            self.fiducialNameList.append(self.fidListWidget.item(node).text())

        paired = zip(self.volumeNameList, self.fiducialNameList)

        for vol, fid in paired:
            vol_node = slicer.util.getNode(vol)
            fid_node = slicer.util.getNode(fid)
            self.volumeList.append(vol_node)
            self.fiducialList.append(fid_node)

    def findCentreAndRad(self, fiducialPoints):
        f1 = [0,0,0]
        f2 = [0,0,0]
        f4 = [0,0,0]
        f5 = [0,0,0]
        f7 = [0,0,0]

        fiducialPoints.GetNthFiducialPosition(0,f1)
        fiducialPoints.GetNthFiducialPosition(1,f2)
        fiducialPoints.GetNthFiducialPosition(3,f4)
        fiducialPoints.GetNthFiducialPosition(4,f5)
        fiducialPoints.GetNthFiducialPosition(6,f7)

        x = (f1[0]+f2[0])/2
        y = (f1[1]+f7[1])/2
        z = f7[2]

        xRad = (abs(f2[0]-f1[0]))/2
        yRad = ((abs(f7[1]-f1[1]))/2)
        zRad = (abs(f5[2]-f4[2]))/2 + 2

        return [x,y,z], [xRad, yRad, zRad]

    def getMatrixToACPC(self, atu, ltp, rtp, ptu):
        # Anteroposterior axis
        # ac = atu, pc = ltp , ih = rtp
        mid = (ltp+rtp)/2
        pcAc = atu - ptu
        yAxis = pcAc / np.linalg.norm(pcAc)
        # Lateral axis
        acIhDir = rtp - ltp
        xAxis = acIhDir / np.linalg.norm(acIhDir)
        zAxis = np.cross(xAxis, yAxis)
        zAxis /= np.linalg.norm(zAxis)
        # Rostrocaudal axis
        yAxis = np.cross(zAxis, xAxis)
        # Rotation matrix
        rotation = np.vstack([xAxis, yAxis, zAxis])
        # AC in rotated space
        translation = -np.dot(rotation, mid)
        # Build homogeneous matrix
        matrix = np.eye(4)
        matrix[:3, :3] = rotation
        matrix[:3, 3] = translation
        return matrix

    def getTransformNodeFromNumpyMatrix(self, matrix, name=None):
        # Create VTK matrix object
        vtkMatrix = vtk.vtkMatrix4x4()
        for row in range(4):
            for col in range(4):
                vtkMatrix.SetElement(row, col, matrix[row, col])
        # Create MRML transform node
        transformNode = slicer.mrmlScene.AddNewNodeByClass(
            'vtkMRMLLinearTransformNode')
        if name is not None:
            transformNode.SetName(name)
        transformNode.SetAndObserveMatrixTransformToParent(vtkMatrix)
        return transformNode


    def run(self):
        #creates list  that contains volume and fiducial nodes 
        self.pair()

        #zips the lists so they can be used for the for loop
        nodePair = zip(self.volumeList, self.fiducialList)

        for volume, fiducial in nodePair:

            #obtains the coordinate system of f2,f0,f1,f6
            coord1 = [0,0,0]
            coord2 = [0,0,0]
            coord3 = [0,0,0]
            coord4 = [0,0,0]
            fiducial.GetNthFiducialPosition(2,coord1)
            fiducial.GetNthFiducialPosition(0,coord2)
            fiducial.GetNthFiducialPosition(1,coord3)
            fiducial.GetNthFiducialPosition(6,coord4)

            #creates transform that goes from C1 to Slicer world coordinate
            atu = np.array(coord1)
            ltp = np.array(coord2)
            rtp = np.array(coord3)
            ptu = np.array(coord4)
            matrix = self.getMatrixToACPC(atu, ltp, rtp, ptu)
            trans_name = 'C1toW'+fiducial.GetName()[-2:]
            transformNode = self.getTransformNodeFromNumpyMatrix(matrix, name=trans_name)
            
            #creates ROI
            roiNode = slicer.vtkMRMLAnnotationROINode()
            roi_name = "roi" + fiducial.GetName()[-2:] # name the ROI box _n like the fiducials
            roiNode.SetName(roi_name)
            slicer.mrmlScene.AddNode(roiNode)
            # #Transforms
            # roiNode.SetAndObserveTransformNodeID(transformNode.GetID())
            # roiNode.HardenTransform()

            #transforms fiducials and volumes which are in C1 space right now, to the Slicer space 
            fiducial.SetAndObserveTransformNodeID(transformNode.GetID())
            fiducial.HardenTransform()
            volume.SetAndObserveTransformNodeID(transformNode.GetID())
            volume.HardenTransform()



            #creates the centre and radius for the ROI using the new fiducials
            centre, rad = self.findCentreAndRad(fiducial)
            roiNode.SetXYZ(centre)
            roiNode.SetRadiusXYZ(rad)
            logging.info("Completed")
        # Capture screenshot

        logging.info('Processing completed')

        return True

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
    def runFidSelect(self, finalList):

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


class CreateROITest(ScriptedLoadableModuleTest):
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
    self.test_CreateROI1()

  def test_CreateROI1(self):
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
    logic = CreateROILogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
