import pyttsx3
engine = pyttsx3.init()

# For Mac, If you face error related to "pyobjc" when running the `init()` method :
# Install 9.0.1 version of pyobjc : "pip install pyobjc>=9.0.1"

text = input("Input the Text you would like to convert to audio:")
#engine.say("mae rohit hoo")
engine.say(text)
engine.runAndWait()