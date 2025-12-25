import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # Typically female (Zira)
engine.setProperty('rate', 150)
engine.say("I've analyzed the contract. There are 6 critical risks. How would you like to proceed?")
engine.runAndWait()
