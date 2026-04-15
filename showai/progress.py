class TrackState:
    def __init__(self):
        self.message = "Initializing ShowAI Engine..."
        self.audio_tasks = []
        self.audio_progress = 0
        self.timeline_tasks = []
        self.timeline_progress = 0
        self.stitching = False
        
    def log(self, msgs):
        self.message = msgs

broker = TrackState()
