class Player():
    import mpv
    player = mpv.MPV(ytdl=True)
    queue = []          # The list of the songs that are in the queue
    queueSelector = 0   # The index of the song that is currently playing
    isPlaying = False   # Indicates if the player is stopped (if the player is paused this will be still be True)

    def __init__(self):
        pass

    def play(self, url):
        self.isPlaying = True
        self.player.play(url)

    def stop(self):
        self.isPlaying = False
        self.player.stop()

    def isPaused(self):
        return self.player.pause

    def pause(self):
        self.player.pause = True

    def unpause(self):
        self.player.pause = False

    def togglePause(self):
        self.player.pause = not self.player.pause

    def setVolume(self, volume: int):
        self.player.volume = volume

    def isPaused(self):
        return self.player.pause

    def getCurrentSong(self):
        return self.queue[self.queueSelector]
