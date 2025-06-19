import os
import sys
import random
import conf
import pygame
import re
from time import time, sleep, strftime
from trigger_cc import TriggerBase
from accessible_output2.outputs import auto

# Initialize the pygame mixer at the start of the script
pygame.mixer.init()

# Create an accessible output object for speech and braille
o = auto.Auto()
logpath = "logs"

def random_from_file(file):
    with open("text/" + file + ".txt", "rb") as f:
        data = f.read().decode()
    data2 = data.split("\n")
    return random.choice(data2)

def play(f):
    if os.path.exists(f):
        # Load the sound
        sound = pygame.mixer.Sound(f)
        # Play the sound; this allows overlapping sounds
        sound.play()

def speak(text, interrupt=False):
    o.braille(text)
    return o.output(text, interrupt)

def write_to_log(worklog, entry):
    with open(worklog, "a") as f:
        try:
            f.write(entry)
        except:
            pass

def log(name, data):
    if data == "" or data == " ":
        return
    if not os.path.exists("logs"):
        os.makedirs("logs")
    write_to_log(logpath + "/" + name + ".log", data + ". " + strftime("%c, %x") + "\n")

def output(server, text):
    doSpeak = True
    doLog = True
    doInterrupt = False
    speaking = ""
    interrupting = ""
    logging = ""
    for shortname, pairs in conf.conf.servers().items():
        if server.shortname == shortname:
            for k, v in pairs:
                if k == "speech":
                    speaking = v
                if k == "interrupt":
                    interrupting = v
                if k == "log":
                    logging = v
    if speaking.lower() == "false":
        doSpeak = False
    if interrupting.lower() == "true":
        doInterrupt = True
    if logging.lower() == "false":
        doLog = False

    if doSpeak:
        speak(server.shortname + " " + text, doInterrupt)
    if doLog:
        log(server.shortname, text)

class Trigger(TriggerBase):
    def __init__(self, *args, **kwargs):
        super(Trigger, self).__init__(*args, **kwargs)
        self.soundpack = ""
        self.blindyTrigger()

    def serverIsCurrent(self):
        """Returns True if this trigger is from the server that is current."""
        return self.server == self.server.parent.curServer

    def blindyTrigger(self):
        if not self.server.loggedIn:
            return
        self.soundpack = ""
        for shortname, pairs in conf.conf.servers().items():
            if self.server.shortname == shortname:
                for k, v in pairs:
                    if k == "soundpack":
                        self.soundpack = v
        if self.soundpack == "":
            self.soundpack = "default"
        if self.server.me.userid == self.event.parms.userid:
            return
        if self.event.event in ["loggedin"]:
            play("sounds/" + self.soundpack + "/in.wav")
            output(self.server, self.server.nonEmptyNickname(self.event.parms.userid, False, False) + " " + random_from_file("logins"))
        elif self.event.event in ["loggedout"]:
            play("sounds/" + self.soundpack + "/out.wav")
            output(self.server, self.server.nonEmptyNickname(self.event.parms.userid, False, False) + " " + random_from_file("logouts"))
            out = random_from_file("logouts")
        elif self.event.event in ["messagedeliver"] and not "typing" in self.event.parms.content:
            if self.event.parms.type == 1:
                play("sounds/" + self.soundpack + "/user.wav")
            else:
                play("sounds/" + self.soundpack + "/channel.wav")
            pmess = output(self.server, self.server.nonEmptyNickname(self.event.parms.srcuserid, False, False) + ": " + self.event.parms.content)
        elif self.event.event in ["adduser"]:
            play("sounds/" + self.soundpack + "/join.wav")
            output(self.server, self.server.nonEmptyNickname(self.event.parms.userid, False, False) + " joined " +
                   self.server.channelname(self.event.parms.channelid).strip("/"))
        elif self.event.event in ["removeuser"]:
            play("sounds/" + self.soundpack + "/leave.wav")
            output(self.server, self.server.nonEmptyNickname(self.event.parms.userid, False, False) + " left " +
                   self.server.channelname(self.event.parms.channelid).strip("/"))
        elif self.event.event in ["updateuser"]:
            play("sounds/" + self.soundpack + "/status.wav")
            what = "Unknown"
            if self.event.parms.statusmode in ["0", "256", "4096"]:
                what = "Online"
            elif self.event.parms.statusmode in ["1", "257", "4097"]:
                what = "Away"
            if self.event.parms.statusmsg != "":
                what += " (" + self.event.parms.statusmsg + ")"
            output(self.server, self.server.nonEmptyNickname(self.event.parms.userid, False, False) + " " + what)