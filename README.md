# C1SegmentationTool

This tool was created for [Orthotron Lab]( https://orthotron.github.io/) to perform pipeline the segmentation process of C1 spine on 3D Slicer.

## Importing this tool on 3D Slicer
There are 4 Slicer modules present in this repository:
-  **CreateROI**: Creates bounding box around ROI (region of interest) and transforms them from C1 space to Slicer space for consistency
-  **DenseCorrespondenceFid**: Performs dense correspondence on the fiducial points of each spine ROI
-  **FiducialTransform**: Transforms the fiducial points from C1 Space to Slicer Space for consistency 
-  **VolumeClip**: Clips the scanned volume based on created bounding box around ROI
-  **VolumeToModel**: Changes slicer volume to slicer model to perform dense correspondence



## Appendix: Current Instruction for using SSMVisualization(Last Updated Jan 1st 2019)
Obtain Google Drive link from [Chad Paik](ckpaik@uwaterloo.ca)
1. Uncompress the zip file and execute the exe file. It will download custom build of Slicer 4.9. This is because while it technicall works on Slicer 4.8, there is less change of error happening using Slicer that already has PCA module built in. 
2. Replace the SSMVisualization file with the one inside the zip file as there were some errors that had to be fixed. Then, add all the modules from this repository to Slicer 4.9 and restart the program. If there are errors showing about nlopt not being included, you can ignore it as long SSMCalculation is not being done for implant fitting.
3. Load up the scene in the drive. If Mean.vtk and Model.vtk are not already there, add them in.
4. Go to SSMVisualization module, and move the slider around. Auto update is not implemented so every time the slider value is changed, scene must be clicked somewhere for the model to update visually in 3D view. 





