""" Sustained Attention to Response Task (SART)

Author: Cary Stothart (cary.stothart@gmail.com)
Date: 05/11/2015
Version: 2.0
Tested on StandalonePsychoPy-1.82.01-win32

################################# DESCRIPTION #################################

This module contains the standard SART task as detailed by Robertson et al. 
(1997). 

The following task attributes can be easily modified (see the sart()
function documentation below for details):
    
1) Number of blocks (default is 1)
2) Number of font size by number repetitions per trial (default is 5)
3) Target number (default is 3)
4) The presentation order of the numbers. Specifically, the
   numbers can be presented randomly or in a fixed fashion. (default is random)
5) Whether or not practice trials should be presented at the beginning of the 
   task.
   
How to use:

1. Install PsychoPy if you haven't already.
2. Load this file and run it using PsychoPy. Participants will be run on the 
   classic SART task (Robertson et al, 1997) unless one of the sart()
   function parameters is changed.

Reference:

Robertson, H., Manly, T., Andrade, J.,  Baddeley, B. T., & Yiend, J. (1997). 
'Oops!': Performance correlates of everyday attentional failures in traumatic 
brain injured and normal subjects. Neuropsychologia, 35(6), 747-758.

################################## FUNCTIONS ##################################

Self-Contained Functions (Argument=Default Value):

sart(monitor="testMonitor", blocks=1, reps=5, omitNum=3, practice=True, 
     path="", fixed=False)
     
monitor......The monitor to be used for the task.
blocks.......The number of blocks to be presented.
reps.........The number of repetitions to be presented per block.  Each
             repetition equals 45 trials (5 font sizes X 9 numbers).
omitNum......The number participants should withhold pressing a key on.
practice.....If the task should display 18 practice trials that contain 
             feedback on accuracy.
path.........The directory in which the output file will be placed. Defaults
             to the directory in which the task is placed.
fixed........Whether or not the numbers should be presented in a fixed
             instead of random order (e.g., 1, 2, 3, 4, 5, 6, 7, 8 ,9,
             1, 2, 3, 4, 5, 6, 7, 8, 9...).     
             
################################### CITATION ##################################

How to cite this software in APA:

Stothart, C. (2015). Python SART (Version 2) [software]. Retrieved from 
https://github.com/cstothart/python-cog-tasks.  

For a DOI and other citation information, please see 
http://figshare.com/authors/Cary_Stothart/394277
     
################################## COPYRIGHT ##################################

The MIT License (MIT)

Copyright (c) 2015 Cary Robert Stothart

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.     

"""

import time
import copy
import random
from psychopy import visual, core, data, event, gui
import numpy as np
import sys
import threading
import master8 as m
import os
try:
   import queue
except ImportError:
   import Queue as queue
from pyfirmata import Arduino, util

stimulation = False
eeg = False
stimcolor = "white"
task_probe_keys=["1","2", "3", "4"]
binary_probe_keys = ["1", "2"]
quit_button="escape"

min_probe_interval=30 # in s
max_probe_interval=60 # in s
num_probes = 3
ISI = 1.15
reps = 2 #experiment: 17. this way ntrials = 1080, total duration = 1242 seconda, comparable to 1200 secs in Boaye et al. (2021)

ntrials = 45 * reps
probe_times=np.array(np.random.randint(min_probe_interval, max_probe_interval +1, num_probes-1)/ISI, dtype=np.int)
#probe_trials=np.cumsum(np.array(probe_times/sum(probe_times)*(ntrials-num_probes/ISI), dtype=np.int))
probe_trials = np.array((np.cumsum(probe_times)/ISI), dtype = int)
probe_trials=np.append(probe_trials, ntrials - 1)


def part_info_gui():
    info = gui.Dlg(title='SART')
    info.addText('Participant Info')
    info.addField('Part. Number: ')
    info.addField('Part. Gender: ', 
                  choices=["Please Select", "Male", "Female", "Other"])
    info.addField('Part. Age:  ')
    info.addField('Part. Year in School: ', 
                  choices=["Please Select", "Freshman", "Sophmore", "Junior", 
                           "Senior", "1st Year Graduate Student", 
                           "2nd Year Graduate Student", 
                           "3rd Year Graduate Student", 
                           "4th Year Graduate Student",
                           "5th Year Graduate Student", 
                           "6th Year Graduate Student"])
    info.addField('Do you have normal or corrected-to-normal vision?', 
                  choices=["Please Select", "Yes", "No"])
    info.addText('Experimenter Info')
    info.addField('DIS Initials:  ')
    info.addField('EEG connected: ', 
                  choices=["Please Select", "Yes", "No"])
    info.addField('Stimulation: ', 
                  choices=["Please Select", "Yes", "No"])
    info.show()
    if info.OK:
        infoData = info.data
    else:
        sys.exit()
    return infoData

partInfo = part_info_gui()

def make_interval_array(T, minInterval, maxInterval):
    interval_array = np.array((np.random.uniform(minInterval, maxInterval)))
    while np.cumsum(interval_array)[-1] <= T:
        nextInterval = np.random.uniform(minInterval, maxInterval)
        interval_array = np.append(interval_array, nextInterval)
    return interval_array[:-1]

if partInfo[-1] == "Yes":
    stimulation = True
    TMS_device = m.Master8('/dev/ttyUSB0')
    TMS_device.changeChannelMode(1, "G")
    
    stim_times = np.append(probe_trials[0], np.diff(probe_trials)) * ISI
    
    pulse_intervals = []		
    for task_period in stim_times:
	    pulse_intervals.append(make_interval_array(task_period, 3, 5)) # a list of arrays containing intervals: each array corresponds to a period before the following probe
    
    thisDir = os.getcwd()
    TMS_datafile =  thisDir + '/SART-rTMS_'  + str(partInfo[0]) + ".csv"
    TMS_output = open(TMS_datafile, "w")
    TMS_output.write("part_num,pulse,time\n")
    
    
if partInfo[-2] == "Yes":
    eeg = True
    ArduinoBoard = Arduino('/dev/cu.usbmodem141201')
    task_start_pin = [ArduinoBoard.digital[9]]
    cross_pin = [ArduinoBoard.digital[8]]
    space_pressed_pin = [ArduinoBoard.digital[7]]
    space_omit_pin = [ArduinoBoard.digital[9]]
    tms_pin = [ArduinoBoard.digital[4], ArduinoBoard.digital[5]]    
    probe_pin = [ArduinoBoard.digital[3], ArduinoBoard.digital[4]]
    probe_response_pin_1 = [ArduinoBoard.digital[2]]
    probe_response_pin_2 = [ArduinoBoard.digital[3]]
    probe_response_pin_3 = [ArduinoBoard.digital[4]]
    probe_response_pin_4 = [ArduinoBoard.digital[5]]
    
    stim_target_pin = [ArduinoBoard.digital[3]]
    stim_pin = [ArduinoBoard.digital[6]]
    
    def eeg_trigger(pins, value):
	    for pin in pins:
		    pin.write(value)

win = visual.Window(fullscr=False, color="black", units='cm', monitor="testMonitor")

def rTMS(tms, interval_array, starting_time, TMS_output, participant, out_queue, eeg = eeg):
    pulse_num = 1
    TMSclock = core.Clock()
    TMSclock.add(-1 * starting_time)
    for interval in interval_array:
        time.sleep(interval)
        tms.trigger(1)
        if eeg ==True:
            eeg_trigger(tms_pin, 1)
            eeg_trigger(tms_pin, 0)
        TMS_end_time =  TMSclock.getTime()
        logtext="{part_num},{pulse},{time}\n".format( \
        pulse=pulse_num,\
        part_num=participant, \
        time="%.10f"%(TMS_end_time))
        TMS_output.write(logtext)
        pulse_num +=1
    out_queue.put(TMS_end_time)
    
def sart(blocks, win = win, monitor="testMonitor", reps=reps, omitNum=3, practice=False, 
         path="", fixed=True, partInfo = partInfo):
    """ SART Task.
    
    monitor......The monitor to be used for the task.
    blocks.......The number of blocks to be presented.
    reps.........The number of repetitions to be presented per block.  Each
                 repetition equals 45 trials (5 font sizes X 9 numbers).
    omitNum......The number participants should withold pressing a key on.
    practice.....If the task should display 18 practice trials that contain 
                 feedback on accuracy.
    path.........The directory in which the output file will be placed. Defaults
                 to the directory in which the task is placed.
    fixed........Whether or not the numbers should be presented in a fixed
                 instead of random order (e.g., 1, 2, 3, 4, 5, 6, 7, 8 ,9,
                 1, 2, 3, 4, 5, 6, 7, 8, 9...).
    """
    mainResultList = []
    fileName = "SART_" + str(partInfo[0]) + ".csv"
    outFile = open(path + fileName, "w")
    sart_init_inst(win, omitNum)
    mw_task_inst(win)
    probe_task_inst(win)
    probe_warning_task_inst(win)
    if practice == True:
        sart_prac_inst(win, omitNum)
        mainResultList.extend(sart_block(win, fb=True, omitNum=omitNum, 
                              reps=reps, bNum=0, fixed=fixed, probe_trials = probe_trials))
    sart_act_task_inst(win)
    for block in range(1, blocks + 1):
        mainResultList.extend(sart_block(win, fb=False, omitNum=omitNum,
                              reps=reps, bNum=block, fixed=fixed, probe_trials = probe_trials))
        if (blocks > 1) and (block != blocks):
            sart_break_inst(win)
    outFile.write("part_num\tpart_gender\tpart_age\tpart_school_yr\t" +
                  "part_normal_vision\texp_initials\teeg_connected\tstimulation\tblock_num\ttrial_num\t" +
                  "number\tomit_num\tresp_acc\tresp_rt\ttrial_start_time_s" +
                  "\ttrial_end_time_s\tprobe_trial\tresponse_task\tresponse_intention\tresponse_confidence\tmean_trial_time_s\ttiming_function\n")
    for line in mainResultList:
        for item in partInfo:
            outFile.write(str(item) + "\t")
        for col in line:
            outFile.write(str(col) + "\t")
        outFile.write("time.process_time()\n")
    outFile.close()
    
def sart_init_inst(win, omitNum, eeg = eeg):
    inst = visual.TextStim(win, text=("In this task, a series of numbers will" +
                                      " be presented to you.  For every" +
                                      " number that appears except for the" +
                                      " number " + str(omitNum) + ", you are" +
                                      " to press the space bar as quickly as" +
                                      " you can.  That is, if you see any" +
                                      " number but the number " +
                                      str(omitNum) + ", press the space" +
                                      " bar.  If you see the number " +
                                      str(omitNum) + ", do not press the" +
                                      " space bar or any other key.\n\n" +
                                      "Please give equal importance to both" +
                                      " accuracy and speed while doing this" + 
                                      " task.\n\nPress the b key to continue."), 
                           color="white", height=0.7, pos=(0, 0))
    event.clearEvents()
    while 'b' not in event.getKeys():
        inst.draw()
        win.flip()
        
def sart_prac_inst(win, omitNum):
    inst = visual.TextStim(win, text=("We will now do some practice trials " +
                                      "to familiarize you with the task.\n" +
                                      "\nRemember, press the space bar when" +
                                      " you see any number except for the " +
                                      " number " + str(omitNum) + ".\n\n" +
                                      "Press the b key to start the " +
                                      "practice."), 
                           color="white", height=0.7, pos=(0, 0))
    event.clearEvents()
    while 'b' not in event.getKeys():
        inst.draw()
        win.flip()
        
def mw_task_inst(win):
    inst = visual.TextStim(win, text=("Try to stay as concentrated on the task as you can throughout the entire experiment. It is however, not unusual for your thoughts to start wandering.\nAt some point, you will be interrupted to answer the questions on the screen relative to your mind-wandering.\n\nPress the b key to continue."), 
                           color="white", height=0.7, pos=(0, 0))
    event.clearEvents()
    while 'b' not in event.getKeys():
        inst.draw()
        win.flip()
    
def probe_task_inst(win):
    inst = visual.TextStim(win, text=("The first question will ask you to evaluate your state of mind prior to the appearance of the question. You will have to choose a score on the scale of 1 ('Completely') to 4 ('Not at all'). Next, you will be asked whether you intentionally tried to concentrate or not. Finally, you will be asked whether you were distracted by your environment.\n\nPress the b key to continue."), 
                           color="white", height=0.7, pos=(0, 0))
    event.clearEvents()
    while 'b' not in event.getKeys():
        inst.draw()
        win.flip()

def probe_warning_task_inst(win):
    inst = visual.TextStim(win, text=("It is important to note that there are no right or wrong answers, and they have no consequences, so please answer as truthfully as possible.\n\nPress the b key to continue."), 
                           color="white", height=0.7, pos=(0, 0))
    event.clearEvents()
    while 'b' not in event.getKeys():
        inst.draw()
        win.flip()

def sart_act_task_inst(win):
    inst = visual.TextStim(win, text=("We will now start the actual task.\n" +
                                      "\nRemember, give equal importance to" +
                                      " both accuracy and speed while doing" +
                                      " this task.\n\nPress the b key to " +
                                      "start the actual task."), 
                           color="white", height=0.7, pos=(0, 0))
    event.clearEvents()
    while 'b' not in event.getKeys():
        inst.draw()
        win.flip()
    if eeg == True:
        eeg_trigger(task_start_pin, 1)
        eeg_trigger(task_start_pin, 0)
        
def sart_break_inst(win):
        inst = visual.TextStim(win, text=("You will now have a 60 second " +
                                          "break.  Please remain in your " +
                                          "seat during the break."),
                               color="white", height=0.7, pos=(0, 0))
        nbInst = visual.TextStim(win, text=("You will now do a new block of" +
                                            " trials.\n\nPress the b key " +
                                            "bar to begin."),
                                 color="white", height=0.7, pos=(0, 0))
        startTime = time.process_time()
        while 1:
            eTime = time.process_time() - startTime
            inst.draw()
            win.flip()
            if eTime > 60:
                break
        event.clearEvents()
        while 'b' not in event.getKeys():
            nbInst.draw()
            win.flip()

def sart_block(win, fb, omitNum, reps, bNum, fixed, probe_trials, stimulation = stimulation , eeg = eeg):
    mouse = event.Mouse(visible=0)
    xStim = visual.TextStim(win, text="X", height=3.35, color="white", 
                            pos=(0, 0))
    circleStim = visual.Circle(win, radius=1.50, lineWidth=8,
                               lineColor="white", pos=(0, -.2))
    numStim = visual.TextStim(win, font="Arial", color="white", pos=(0, 0))
    correctStim = visual.TextStim(win, text="CORRECT", color="green", 
                                  font="Arial", pos=(0, 0))
    incorrectStim = visual.TextStim(win, text="INCORRECT", color="red",
                                    font="Arial", pos=(0, 0))                                 
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    if fb == True:
        fontSizes=[1.20, 3.00]
    else:
        fontSizes=[1.20, 1.80, 2.35, 2.50, 3.00]
    list= data.createFactorialTrialList({"number" : numbers,
                                         "fontSize" : fontSizes})
    seqList = []
    for i in range(len(fontSizes)):
        for number in numbers:
            random.shuffle(list)
            for trial in list:
                if trial["number"] == number and trial not in seqList:
                    seqList.append(trial)
                    break
    if fixed == True:
        trials = data.TrialHandler(seqList, nReps=reps, method='sequential')
    else:
        trials = data.TrialHandler(list, nReps=reps, method='random')    
    clock = core.Clock()
    resultList =[]
    startTime = time.process_time()
    if stimulation == True:
        TMS_end_time_queue = queue.Queue()
        rTMS_interval_index = 1
        startTime = time.process_time()
        if __name__ == "__main__":
            rTMS_Thread = threading.Thread(target=rTMS, args=(TMS_device, pulse_intervals[0], startTime, TMS_output, partInfo[0], TMS_end_time_queue))
            rTMS_Thread.start()
    tNum = 0
    ntrial = 1
    for trial in trials:
        probe_trial = 0
        response_task = "NA"
        response_intention = "NA"
        response_confidence = "NA"
        if ntrial in probe_trials:
            probe_trial = 1
            response_task=show_probe(probe_task, task_probe_keys)
            response_intention=show_probe(probe_intention, binary_probe_keys)
            response_confidence=show_probe(probe_distraction, binary_probe_keys)
            if (stimulation == True and rTMS_interval_index < len(pulse_intervals)):
                if __name__ == "__main__":
                    add_experiment_time = TMS_end_time_queue.get() + clock.getTime()
                    rTMS_Thread = threading.Thread(target=rTMS, args=(TMS_device, pulse_intervals[rTMS_interval_index], add_experiment_time, TMS_output, partInfo[0], TMS_end_time_queue))
                    rTMS_Thread.start() 
                rTMS_interval_index += 1
        ntrial += 1
        tNum += 1
        resultList.append(sart_trial(win, fb, omitNum, xStim, circleStim,
                              numStim, correctStim, incorrectStim, clock, 
                              trials.thisTrial['fontSize'], 
                              trials.thisTrial['number'], tNum, bNum, mouse))
        resultList[-1].append(probe_trial)
        resultList[-1].append(response_task)
        resultList[-1].append(response_intention)
        resultList[-1].append(response_confidence)
    endTime = time.process_time()
    totalTime = endTime - startTime
    for row in resultList:
        row.append(totalTime/tNum)
    print ("\n\n#### Block " + str(bNum) + " ####\nDes. Time Per P Trial: " +
           str(2.05*1000) + " ms\nDes. Time Per Non-P Trial: " +
           str(1.15*1000) + " ms\nActual Time Per Trial: " +
           str((totalTime/tNum)*1000) + " ms\n\n")
    return resultList

def sart_trial(win, fb, omitNum, xStim, circleStim, numStim, correctStim, 
               incorrectStim, clock, fontSize, number, tNum, bNum, mouse, eeg = eeg):
    if eeg == True:
            if number == 3:
                eeg_trigger(stim_target_pin, 1)
            else:
                eeg_trigger(stim_pin, 1)               
    startTime = time.process_time()
    mouse.setVisible(0)
    respRt = "NA"
    numStim.setHeight(fontSize)
    numStim.setText(number)
    numStim.draw()
    event.clearEvents()
    clock.reset()
    stimStartTime = time.process_time()
    win.flip()
    if eeg == True:
            if number == 3:
                eeg_trigger(stim_target_pin, 0)
            else:
                eeg_trigger(stim_pin, 0)
    xStim.draw()
    circleStim.draw()
    waitTime = .25 - (time.process_time() - stimStartTime)
    core.wait(waitTime, hogCPUperiod=waitTime)
    maskStartTime = time.process_time()
    win.flip()
    waitTime = 0.9 - (time.process_time() - maskStartTime)
    core.wait(waitTime, hogCPUperiod=waitTime)
    win.flip()
    
    allKeys = event.getKeys(timeStamped=clock)
    if len(allKeys) != 0:
        if eeg == True:
            eeg_trigger(space_pressed_pin, 1)
            eeg_trigger(space_pressed_pin, 0)
        respRt = allKeys[0][1]
    if len(allKeys) == 0:
        if omitNum == number:
            respAcc = 1
        else:
            respAcc = 0
    else:
        if omitNum == number:
            respAcc = 0
        else:
            respAcc = 1
    if fb == True:
        if respAcc == 0:
            incorrectStim.draw()
        else:
            correctStim.draw()
        stimStartTime = time.process_time()
        win.flip()
        waitTime = .90 - (time.process_time() - stimStartTime) 
        core.wait(waitTime, hogCPUperiod=waitTime)
        win.flip()
    endTime = time.process_time()
    totalTime = endTime - startTime
    return [str(bNum), str(tNum), str(number), str(omitNum), str(respAcc),
            str(respRt), str(startTime), str(endTime)]

def show_probe(probe, probe_keys, eeg = eeg):
	probe.show_arrow=False
	if eeg == True:
	    eeg_trigger(probe_pin, 1)
	    eeg_trigger(probe_pin, 0)
	while(1):
		probe.draw()
		win.flip()
		keys=event.getKeys()
		if len(set(keys) & set(probe_keys))>0:
			if eeg == True:
				if "1" in keys:
					eeg_trigger(probe_response_pin_1, 1)
					eeg_trigger(probe_response_pin_1, 0)
				elif "2" in keys:
					eeg_trigger(probe_response_pin_2, 1)
					eeg_trigger(probe_response_pin_2, 0)
				elif "3" in keys:
					eeg_trigger(probe_response_pin_3, 1)
					eeg_trigger(probe_response_pin_3, 0)
				elif "4" in keys:
					eeg_trigger(probe_response_pin_4, 1)
					eeg_trigger(probe_response_pin_4, 0)
			k=int(list(set(keys) & set(probe_keys))[0])-1
			probe.set_arrow(k)
			probe.draw()
			win.flip()
			time.sleep(1.0)
			probe.show_arrow=False
			break
		elif quit_button in keys:
			sys.exit()
	return probe.current_pos

class LikertScale:
	def __init__(self, win, nposs=5, instruction_text=u"", scale_labels=[]):
		start,end=-.5, .5
		ypad=.05
		instru = visual.TextStim(win=win, ori=0, name='instru',units='norm',
			text=instruction_text,    font='Arial',
			pos=[0, 0.5], height=0.07, wrapWidth=None,
			color='white', colorSpace='rgb', opacity=1,
			depth=0.0)
		self.nposs=nposs
		self.show_arrow=False
		line=visual.Line(win, start=(start, 0), end=(end,0), units='norm', lineColor=stimcolor, lineWidth=5)
		ticks=start+np.arange(0,nposs)*(end-start)/float(nposs-1)
		poss=[visual.Line(win, start=(tick, -ypad), end=(tick,ypad), units='norm', lineColor=stimcolor,
						  lineWidth=3) for tick in ticks]
		lab=[visual.TextStim(win, pos=(ticks[i], -.1), units='norm', text=scale_labels[i], height=.05, color=stimcolor) for i in range(len(scale_labels))]

		self.arrow_v=0.4*np.array([ [0,0], [.2, .2], [.1, .2], [.1, .5], [-.1, .5], [-.1, .2], [-.2, .2], [0, 0]])
		self.arrow_v[:,1]+=ypad+.01
		self.ticks=ticks
		self.arrow=visual.ShapeStim(win, vertices=self.arrow_v, fillColor=stimcolor, units='norm')

		self.init_random()

		self.elements=[line]+poss+lab+[instru]

	def init_random(self):
		## initialize to either 0 or nposs-1
		initial_pos=np.random.choice([0,self.nposs-1])
		self.set_arrow(initial_pos)
	def init_middle(self):
		## initialize to either 0 or nposs-1
		initial_pos=int(self.nposs/2)
		self.set_arrow(initial_pos)

	def set_arrow(self, pos):
		self.current_pos=pos
		v=self.arrow_v.copy()
		try:
			v[:,0]+=self.ticks[pos]
		except:
			pass
		self.arrow.setVertices(v)
		self.show_arrow=True

	def arrow_left(self):
		if self.current_pos==0:
			return
		else:
			self.set_arrow(self.current_pos-1)

	def arrow_right(self):
		if self.current_pos==self.nposs-1:
			return
		else:
			self.set_arrow(self.current_pos+1)
	def draw(self):
		for el in self.elements:
			el.draw()
		if self.show_arrow:
			self.arrow.draw()

probe_task=LikertScale(win, 4,
	instruction_text=u"To what extent were your thoughts related to the task? Use keys 1 to 4 to respond.",
	scale_labels=["Not at all", "", "", "Completely"])

probe_intention=LikertScale(win, 2,
	instruction_text=u"Did you intend to stay on task? Use keys 1 or 2 to respond.",
	scale_labels=["no", "yes"])
	
probe_distraction=LikertScale(win, 2,
	instruction_text=u"Were you disteacted by your surroundings?",
	scale_labels=["no", "yes"])

def main():
    sart(blocks = 1)

if __name__ == "__main__":
    main()