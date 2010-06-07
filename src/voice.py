import imp
import logging
from conf import conf

def create_voice_synthetizer():
    try:
        import speech

        class SpeechSynthetizer:
            def say(self, txt):
                speech.say(txt)
                
        return SpeechSynthetizer()
    except ImportError:
        pass
    
    try:
        import flite

        class FLiteSynthetizer:
            def __init__(self):
                flite.init()

            def say(self, txt):
                flite.say(txt)
                
        return FLiteSynthetizer()

    except ImportError:
        logging.error("Could not find any voice synthetizer")
        return None
