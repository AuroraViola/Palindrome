import sys
import gi
import urllib.parse
import subsonic
import player

gi.require_version('Adw', '1')
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gtk, GLib, Gdk

class Palindrome(Adw.Application):
    player = player.Player()
    api = subsonic.API()
    # The main window as a builder
    mainWindow = Gtk.Builder.new_from_file("data/ui/mainWindow.xml")
    # The progressbar is an annimation
    progressBarAnimation = Adw.TimedAnimation.new(mainWindow.get_object("progressBar"), 0, 1, 5000, Adw.PropertyAnimationTarget.new(mainWindow.get_object("progressBar"), "fraction"))

    def __init__(self):
        super().__init__(application_id="org.auroraviola.palindrome")
        GLib.set_application_name("Palindrome")
        self.progressBarAnimation.set_easing(0)

    def formatTextForSongInfo(self, string):
        # This is used to short a string that is too long. It's used in updateSongInfo()
        if len(string) > 30:
            return string[:28] + "..."

        return string

    def updateSongInfo(self):
        # This method is called everytime a new song is playing
        # It updates the songName, artistName and albumName labels. It also updated the coverArt and the Favourite Button
        currentSong = self.player.getCurrentSong()
        self.mainWindow.get_object("songName").set_label(self.formatTextForSongInfo(currentSong["@title"]))
        self.mainWindow.get_object("artistName").set_label(self.formatTextForSongInfo(currentSong["@artist"]))
        self.mainWindow.get_object("albumName").set_label(self.formatTextForSongInfo(currentSong["@album"]))

        image = Gdk.Texture.new_from_bytes(GLib.Bytes.new(self.api.getCoverArt(self.player.getCurrentSong()["@id"])))
        self.mainWindow.get_object("coverArt").set_paintable(image)

        if "@starred" in currentSong:
            self.mainWindow.get_object("FavouriteBtn").props.active = True
        else:
            self.mainWindow.get_object("FavouriteBtn").props.active = False

        self.mainWindow.get_object("nowPlaying_list").unselect_all()
        self.mainWindow.get_object("nowPlaying_list").select_row(self.mainWindow.get_object("nowPlaying_list").get_row_at_index(self.player.queueSelector))

    def updateNowPlaying(self):
        # This method is called everytime self.player.queue is modified

        # This empty the nowPlaying_list (NEED TO BE REWORKED)
        while True:
            try:
                self.mainWindow.get_object("nowPlaying_list").remove(self.mainWindow.get_object("nowPlaying_list").get_row_at_index(0))
            except:
                break

        # This recreates the nowPlaying_list based on self.player.queue (should somehow be reworked)
        for i in range(len(self.player.queue)):
            song = self.player.queue[i]
            thing = Adw.ActionRow().new()
            thing.props.title = str(song["@title"]).replace("&", "&amp;")
            thing.props.subtitle = str(song["@artist"]).replace("&", "&amp;")

            playSongBtn = Gtk.Button().new()
            playSongBtn.props.icon_name = "media-playback-start-symbolic"
            playSongBtn.connect("clicked", self.playSelectedSong, i)
            playSongBtn.props.margin_top = 10
            playSongBtn.props.margin_bottom = 10
            thing.add_prefix(playSongBtn)

            songDuration = Gtk.Label().new()
            songDuration.props.label = self.convertSecToMin(song["@duration"])
            songDuration.props.margin_top = 10
            songDuration.props.margin_bottom = 10
            thing.add_suffix(songDuration)

            self.mainWindow.get_object("nowPlaying_list").append(thing)


    def convertSecToMin(self, duration):
        # This funcion convert seconds to minutes
        # If you give "132" to this function it will returns "2:12"
        secs = int(duration)
        mins = 0

        while secs >= 60:
            mins += 1
            secs -= 60

        sep = ":" if secs >= 10 else ":0"

        return str(mins) + sep + str(secs)

    def addPlaylistToQueue(self, button, playlistId):
        # Add songs from a playlist to the queue
        songlist = self.api.getPlaylistSongs(playlistId)
        if isinstance(songlist, list):
            for song in songlist:
                self.player.queue.append(song)
        elif isinstance(songlist, dict):
            self.player.queue.append(songlist)

        self.updateNowPlaying()

    def addAlbumToQueue(self, button, album_id):
        # Add songs from an album to the queue
        songlist = self.api.getAlbumSongs(album_id)
        if isinstance(songlist, list):
            for song in songlist:
                self.player.queue.append(song)
        elif isinstance(songlist, dict):
            self.player.queue.append(songlist)

        self.updateNowPlaying()

    def playSelectedSong(self, button, index):
        # This function is called everytime you play a selected song
        self.progressBarAnimation.reset()
        self.player.queueSelector = index
        self.mainWindow.get_object("playBtn").props.icon_name = "media-playback-pause-symbolic"
        self.progressBarAnimation.set_duration(int(self.player.getCurrentSong()["@duration"]) * 1000 + 1000)
        self.player.play(self.getPlayUrl())
        self.progressBarAnimation.play()
        self.player.unpause()
        self.updateSongInfo()

    def getPlayUrl(self):
        # Get the url of the current song for playing it with mpv
        par2 = self.api.par.copy()
        par2["id"] = self.player.getCurrentSong()["@id"]
        return self.api.url + "stream?" + urllib.parse.urlencode(par2)

    def playBtnPressed(self, button):
        if len(self.player.queue) > 0:
            if not self.player.isPlaying:
                button.props.icon_name = "media-playback-pause-symbolic"
                self.progressBarAnimation.set_duration(int(self.player.getCurrentSong()["@duration"])*1000+1000)
                self.player.play(self.getPlayUrl())
                self.progressBarAnimation.play()
                self.player.unpause()
                self.updateSongInfo()
            else:
                if button.props.icon_name == "media-playback-start-symbolic":
                    button.props.icon_name = "media-playback-pause-symbolic"
                    self.player.unpause()
                    self.progressBarAnimation.resume()
                else:
                    button.props.icon_name = "media-playback-start-symbolic"
                    self.player.pause()
                    self.progressBarAnimation.pause()

    def stopBtnPressed(self, button, playBtn):
        self.player.stop()
        self.progressBarAnimation.reset()
        self.mainWindow.get_object("nowPlaying_list").unselect_all()
        playBtn.props.icon_name = "media-playback-start-symbolic"
        self.mainWindow.get_object("songName").set_label("-")
        self.mainWindow.get_object("artistName").set_label("-")
        self.mainWindow.get_object("albumName").set_label("-")
        self.mainWindow.get_object("FavouriteBtn").props.active = False
        self.mainWindow.get_object("coverArt").set_paintable()

    def prevBtnPressed(self, button):
        if self.player.queueSelector > 0:
            self.player.queueSelector -= 1
            self.progressBarAnimation.reset()
            self.progressBarAnimation.set_duration(int(self.player.getCurrentSong()["@duration"]) * 1000 + 1000)
            self.progressBarAnimation.play()
            self.player.unpause()
            playBtn = self.mainWindow.get_object("playBtn")
            if playBtn.props.icon_name == "media-playback-start-symbolic":
                playBtn.props.icon_name = "media-playback-pause-symbolic"
            self.player.play(self.getPlayUrl())
            self.updateSongInfo()

    def nextBtnPressed(self, button):
        if self.player.queueSelector < len(self.player.queue)-1:
            self.player.queueSelector += 1
            self.progressBarAnimation.reset()
            self.progressBarAnimation.set_duration(int(self.player.getCurrentSong()["@duration"]) * 1000 + 1000)
            self.progressBarAnimation.play()
            self.player.unpause()
            playBtn = self.mainWindow.get_object("playBtn")
            if playBtn.props.icon_name == "media-playback-start-symbolic":
                playBtn.props.icon_name = "media-playback-pause-symbolic"
            self.player.play(self.getPlayUrl())
            self.updateSongInfo()

    def finishedProgressBar(self, bar):
        bar.reset()
        self.api.scrobble(self.player.getCurrentSong()["@id"], "True")
        if (self.player.queueSelector < len(self.player.queue)-1) or (self.mainWindow.get_object("loopBtn").props.active):
            if not self.mainWindow.get_object("loopBtn").props.active:
                self.player.queueSelector += 1
                self.player.play(self.getPlayUrl())
                bar.set_duration(int(self.player.getCurrentSong()["@duration"])*1000+1000)
                bar.play()
                self.updateSongInfo()
            else:
                self.player.play(self.getPlayUrl())
                bar.play()

    def favouriteBtnPressed(self, button):
        if self.player.isPlaying:
            if button.props.active:
                self.api.starSong(self.player.getCurrentSong()["@id"])
                self.player.queue[self.player.queueSelector]["@starred"] = "placeholder"
            else:
                self.api.unstarSong(self.player.getCurrentSong()["@id"])
                if "@starred" in self.player.queue[self.player.queueSelector]:
                    del self.player.queue[self.player.queueSelector]["@starred"]
        else:
            self.mainWindow.get_object("FavouriteBtn").props.active = False


    def emptyQueueBtnPressed(self, button):
        # This function empty the queue
        self.player.queue = []
        self.player.queueSelector = 0
        while True:
            try:
                self.mainWindow.get_object("nowPlaying_list").remove(self.mainWindow.get_object("nowPlaying_list").get_row_at_index(0))
            except:
                break

    def setVolume(self, slider):
        # This function set volume using a sqrt scale
        self.player.setVolume(int((slider.get_value()**0.5)*100))

    def do_activate(self):
        # This create the Artist list
        for artist in self.api.getArtists():
            thing = Adw.ActionRow().new()
            thing.props.title = str(artist["@name"]).replace("&", "&amp;")
            if artist["@albumCount"] != "1":
                thing.props.subtitle = str(artist["@albumCount"]) + " Albums"
            else:
                thing.props.subtitle = str(artist["@albumCount"]) + " Album"

            self.mainWindow.get_object("artists_list").append(thing)

        # This create the Album list
        for album in self.api.getAlbumsList():
            thing = Adw.ActionRow().new()
            thing.props.title = str(album["@title"]).replace("&", "&amp;")
            thing.props.subtitle = str(album["@artist"]).replace("&", "&amp;")

            # This add a button at the end of the ActionRow
            addQueueBtn = Gtk.Button().new()
            addQueueBtn.props.icon_name = "list-add-symbolic"
            addQueueBtn.connect("clicked", self.addAlbumToQueue, album["@id"])
            addQueueBtn.props.margin_top = 10
            addQueueBtn.props.margin_bottom = 10
            thing.add_suffix(addQueueBtn)

            self.mainWindow.get_object("albums_list").append(thing)

        # This create the playlist list
        for playlist in self.api.getPlaylists():
            thing = Adw.ActionRow().new()
            thing.props.title = str(playlist["@name"]).replace("&", "&amp;")
            if playlist["@songCount"] != "1":
                thing.props.subtitle = str(playlist["@songCount"]) + " Songs"
            else:
                thing.props.subtitle = str(playlist["@songCount"]) + " Song"

            # This add a button at the end of the ActionRow
            addQueueBtn = Gtk.Button().new()
            addQueueBtn.props.icon_name = "list-add-symbolic"
            addQueueBtn.connect("clicked", self.addPlaylistToQueue, playlist["@id"])
            addQueueBtn.props.margin_top = 10
            addQueueBtn.props.margin_bottom = 10
            thing.add_suffix(addQueueBtn)

            self.mainWindow.get_object("playlists_list").append(thing)

        # Assign the function to buttons and similar thing
        self.progressBarAnimation.connect("done", self.finishedProgressBar)

        self.mainWindow.get_object("playBtn").connect("clicked", self.playBtnPressed)
        self.mainWindow.get_object("stopBtn").connect("clicked", self.stopBtnPressed, self.mainWindow.get_object("playBtn"))
        self.mainWindow.get_object("prevBtn").connect("clicked", self.prevBtnPressed)
        self.mainWindow.get_object("nextBtn").connect("clicked", self.nextBtnPressed)
        self.mainWindow.get_object("FavouriteBtn").connect("clicked", self.favouriteBtnPressed)

        self.mainWindow.get_object("emptyQueueBtn").connect("clicked", self.emptyQueueBtnPressed)

        self.mainWindow.get_object("volumeChanger").connect("value-changed", self.setVolume)

        # Creates the window itself
        window = self.mainWindow.get_object("window")
        window.set_title("Palindrome")
        window.set_application(self)

        window.present()


app = Palindrome()
exit_status = app.run(sys.argv)
sys.exit(exit_status)

