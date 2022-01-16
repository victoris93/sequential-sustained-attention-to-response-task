import time
import copy
import random
from psychopy import visual, core, data, event, gui
import numpy as np
import sys
import os

fb = False
fixed = True
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

win = visual.Window(fullscr=False, color="black", units='cm', monitor="testMonitor")
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
omitNum = 3

if fb == True:
	fontSizes=[1.20, 3.00]
else:
	fontSizes=[1.20, 1.80, 2.35, 2.50, 3.00]
	

if partInfo[5] == "Yes":
    eeg = True
 
thisDir = os.getcwd()
fileName = "/SART_" + str(partInfo[0]) + ".csv"
datafile = thisDir + "/data" + fileName
with open(datafile, "w") as outFile:
	outFile.write("part_num, part_gender, part_age, part_normal_vision, exp_initials, eeg_connected,  stimulation, trial, number, omit_num, resp_acc, resp_rt, trial_start_time, trial_end_time, probe,response\n")

outFile = open(datafile, "a")

def write_data(number, resp_acc, resp_rt, probe, trial_start_time, trial_end_time, response, ntrial, f = outFile, eeg = eeg, stimulation = stimulation, omitNum = omitNum):
	logtext="{part_num},{part_gender}, {part_age}, {part_normal_vision}, {exp_initials}, {eeg_connected}, {stimulation}, {trial}, {number}, {omit_num}, {resp_acc}, {resp_rt}, {trial_start_time}, {trial_end_time}, {probe},{response}\n".format(\
					part_num= partInfo[0],\
					part_gender=partInfo[1], \
					part_age=partInfo[2], \
					part_normal_vision=partInfo[3], \
					exp_initials=partInfo[4], \
					eeg_connected=eeg, \
					stimulation = stimulation, \
					trial = ntrial, \
					number = number , \
					omit_num = omitNum , \
					resp_acc = resp_acc, \
					resp_rt = resp_rt,
					trial_start_time = trial_start_time, \
					trial_end_time = trial_end_time, \
					probe  = probe, \
					response= response)
	f.write(logtext)
	f.flush()

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
   
sart_init_inst(win, omitNum)
mw_task_inst(win)
probe_warning_task_inst(win)
sart_act_task_inst(win)

def sart_trial(clock, fontSize, number, ntrial, win = win, fb = fb, omitNum = omitNum, xStim = xStim, circleStim = circleStim, numStim = numStim, correctStim = correctStim, 
               incorrectStim = incorrectStim, mouse = mouse, eeg = eeg):
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
    #totalTime = endTime - startTime
    write_data(ntrial = ntrial, number = number, resp_acc = respAcc, resp_rt = respRt, probe = "NA", trial_start_time = startTime, trial_end_time = endTime, response = "NA")

numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9]
if fb == True:
	fontSizes=[1.20, 3.00]
else:
	fontSizes=[1.20, 1.80, 2.35, 2.50, 3.00]

NumberSizeList= data.createFactorialTrialList({"number" : numbers, "fontSize" : fontSizes})
seqList = []
for i in range(len(fontSizes)):
	for number in numbers:
		random.shuffle(NumberSizeList)
		for trial in NumberSizeList:
			if trial["number"] == number and trial not in seqList:
				seqList.append(trial)
				break
if fixed == True:
	trials = data.TrialHandler(seqList, nReps=reps, method='sequential')
else:
	trials = data.TrialHandler(NumberSizeList, nReps=reps, method='random')    
	
clock = core.Clock()
startTime = time.process_time()
if stimulation == True:
	TMS_end_time_queue = queue.Queue()
	rTMS_interval_index = 1
	startTime = time.process_time()
	if __name__ == "__main__":
		rTMS_Thread = threading.Thread(target=rTMS, args=(TMS_device, pulse_intervals[0], startTime, TMS_output, partInfo[0], TMS_end_time_queue))
		rTMS_Thread.start()
ntrial = 1
for trial in trials:
	if ntrial in probe_trials:
		probe_trial = 1
		probe_start_time = time.process_time()
		response_task=show_probe(probe_task, task_probe_keys)
		probe_end_time = time.process_time()
		write_data(ntrial = ntrial, omitNum = "NA", number = "NA", resp_acc = "NA", resp_rt = "NA", probe = "probe_task", response = response_task, trial_start_time = probe_start_time, trial_end_time = probe_end_time)
		probe_start_time = time.process_time()
		response_intention=show_probe(probe_intention, binary_probe_keys)
		probe_end_time = time.process_time()
		write_data(ntrial = ntrial, omitNum = "NA", number = "NA", resp_acc = "NA", resp_rt = "NA", probe = "probe_intention", response = response_intention, trial_start_time = probe_start_time, trial_end_time = probe_end_time)
		if (stimulation == True and rTMS_interval_index < len(pulse_intervals)):
			if __name__ == "__main__":
				add_experiment_time = TMS_end_time_queue.get() + clock.getTime()
				rTMS_Thread = threading.Thread(target=rTMS, args=(TMS_device, pulse_intervals[rTMS_interval_index], add_experiment_time, TMS_output, partInfo[0], TMS_end_time_queue))
				rTMS_Thread.start()
			rTMS_interval_index += 1
	sart_trial(clock = clock, fontSize = trials.thisTrial['fontSize'], number = trials.thisTrial['number'], ntrial = ntrial)
	ntrial += 1

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
	
# probe_distraction=LikertScale(win, 2,
# 	instruction_text=u"Were you distracted by your surroundings?",
# 	scale_labels=["no", "yes"])
