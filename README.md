# Rig o'matic  
A Maya python based rigging toolkit that helps support your day-to-day needs.  

## Requirements:
This tool requires the following PIP installs: Qt.py, six, numpy and scipy.  
On top of the following python packages: [dcc](https://github.com/bhsingleton/dcc) and [mpy](https://github.com/bhsingleton/mpy).  
The following plug-ins, are optional, but highly recommended: [pointHelper](https://github.com/bhsingleton/PointHelper), [pointOnCurveConstraint](https://github.com/bhsingleton/PointOnCurveConstraint) and [transformConstraint](https://github.com/bhsingleton/TransformConstraint).  

## Installing the PIP Dependencies
To install the required pip dependencies open a Command Prompt window.  
In this example I will be using Maya 2024. Be sure to adjust your code to whichever version of Maya you are using.  
Change the current working directory using:  
> cd %PROGRAMFILES%\Autodesk\Maya2024\bin  

Make sure you have pip installed using:  
> mayapy.exe -m ensurepip --upgrade --user  

Now you can install the necessary dependencies using:  
> mayapy.exe -m pip install Qt.py --user  

## How to open:

```
from rigomatic.ui import qrigomatic

window = qrigomatic.QRigomatic()
window.show()
```

### Modify Tab  
This tab offers support for alignments, freezing either pivots or offset-parent matrices, reseting transform components and finally an attribute spreadsheet.  
  
![image](https://github.com/bhsingleton/rigomatic/assets/11181168/5a2dd892-89e9-4c47-a918-4424cf83bf04)

### Rename Tab  
This tab provides both name concatenation and search and replace support.  
  
![image](https://github.com/bhsingleton/rigomatic/assets/11181168/20f8ac57-a837-414a-85af-1332da5e95e6)

### Shapes Tab  
This tab provides a custom shape library, on top of tools for colourizing shapes and manipulating custom shapes.  
Please keep in mind this tab makes use of point helpers which is an optional plug-in!
  
![image](https://github.com/bhsingleton/rigomatic/assets/11181168/f8e026c3-41be-4c2b-8089-34d525a3edd0)

### Attributes Tab  
This tab, unlike the builtin Maya tool, exposes all of the attribute data types that are only accessible through code.  
There is also the option to add proxy attributes as well since this can only be done through code.  
  
![image](https://github.com/bhsingleton/rigomatic/assets/11181168/bb1b748e-927a-48a5-8cb8-86d6d0887e29)

### Constraints Tab  
This tab provides support for both creating and editing constraints.  
Please keep in mind this tab makes use of transform and point-on-curve constraints which are optional plug-ins! 
It's also worth mentioning that the skin constraint is just a transform constraint but it uses the skin weights of the nearest vertex, from your selected mesh, for its constraint targets.
  
![image](https://github.com/bhsingleton/rigomatic/assets/11181168/bce3cca1-8d27-44be-976d-5c00b1f94520)

### Publish Tab  
This tab provides a series of rig validations to make sure your rig is ready to be sent to animation.  
At this time the `Fix` button has yet to be implemented!  
  
![image](https://github.com/bhsingleton/rigomatic/assets/11181168/42a3484c-453e-46de-8f0f-bb90ce12d47c)
