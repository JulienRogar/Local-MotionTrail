# Local MotionTrail
Maya tool to create motion trails local from a camera and tracking from it's point of view

Last version: 1.0.0 - tested in Maya 2024-2026

For more details make sure to read the wiki! https://github.com/JulienRogar/Local-MotionTrail/wiki

Changelog: https://github.com/JulienRogar/Local-MotionTrail/wiki/Changelog

## How to use
The tool works with instances, each instance has it's own data and window allowing to have multiple usages in same time

## How to install
_Requires Maya's default Python package_

-Download the `Local_MotionTrail.py` file
\
\
-Move the file to one of Maya's script folders\
(Script folders in Maya preferences folder are by default at `C:\Users\...\Documents\maya\scripts` or for each Maya version `C:\Users\...\Documents\maya\VERSION\scripts` as `C:\Users\...\Documents\maya\2024\scripts`)
\
\
-Paste bottom code in a Python tab inside Maya's script editor
>import Local_MotionTrail\
Local_MotionTrail.Load( multi_windows=True, keep_win_pref=False, expanded=True )
<img width="631" height="327" alt="Script inside Script editor UI" src="https://github.com/user-attachments/assets/6af22717-35f3-49d3-8f91-971247412ae5" />


-Select all the code and press the excecute button or drag and drop it on the shelf to set it as a shelf button to create a new instance/window at each press
\
\
\
You can use similarly other [module's public commands](https://github.com/JulienRogar/Local-MotionTrail/wiki#public-commands) with only `Local_MotionTrail.command()` where **command()** is the command and it's argument(s) between parenthesis
