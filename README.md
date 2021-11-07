sequential-sustained-attention-to-response-task
=============

A Python version of the Sustained Attention to Response Task (SART) as detailed by Robertson et al. (1997). Requires [PsychoPy](http://www.psychopy.org/). TMS stimulation is integrated within the task via triggering of A.M.P.I. Master-8.

![SART task flow](/python-sustained-attention-to-response-task-sart.png?raw=true "SART Task Flow")

### To make sure TMS pulses are delivered
Device used: Magstim Rapid2 triggered via [A.M.P.I. Master-8](https://www.ampi.co.il/master-8).

1. Before plugging in Master-8 in a USB port, retrieve the list of addresses of all the devices associated with the Mac: `ls /dev`
2. Plug in Master-8.
3. Call the same command as in 1. to see whether a new address has been added to the list. The address you are looking for is of type `dev/cu.usbserial-xxxxxx`. Pass this address as an argument in line 107 of `python_sart.py` like so: `TMS_device = m.Master8('/dev/cu.usbserial-xxxxxx')`
4. Before starting`python_sart.py`, make sure the TMS device is ready.

### How to Use

1. Install PsychoPy if you haven't already.
2. Load this file and run it using PsychoPy. Participants will be run on the 
   classic SART task (Robertson et al, 1997) unless one of the sart()
   function parameters is changed.

### Task Details

The following task attributes can be easily modified (see the sart()
function documentation below for details):
    
1) Number of blocks (default is 1)
2) Number of font size by number repetitions per trial (default is 5)
3) Target number (default is 3)
4) The presentation order of the numbers. Specifically, the
   numbers can be presented randomly or in a fixed fashion. (default is random)
5) Whether or not practice trials should be presented at the beginning of the 
   task.

### Function Details

Self-Contained Functions (Argument=Default Value):

sart(monitor="testMonitor", blocks=1, reps=5, omitNum=3, practice=True, 
     path="", fixed=False)
     
* monitor: The monitor to be used for the task.
* blocks: The number of blocks to be presented.
* reps: The number of repetitions to be presented per block.  Each
             repetition equals 45 trials (5 font sizes X 9 numbers).
* omitNum: The number participants should withhold pressing a key on.
* practice: If the task should display 18 practice trials that contain 
             feedback on accuracy.
* path: The directory in which the output file will be placed. Defaults
             to the directory in which the task is placed.
* fixed: Whether or not the numbers should be presented in a fixed
             instead of random order (e.g., 1, 2, 3, 4, 5, 6, 7, 8 ,9,
             1, 2, 3, 4, 5, 6, 7, 8, 9...). 

### Reference

Robertson, H., Manly, T., Andrade, J.,  Baddeley, B. T., & Yiend, J. (1997). 
'Oops!': Performance correlates of everyday attentional failures in traumatic 
brain injured and normal subjects. Neuropsychologia, 35(6), 747-758.
