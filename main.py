import random
import string
import sys
import json
import hashlib

import xmltodict
import requests
import gi
import urllib.parse

gi.require_version('Adw', '1')
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gtk, GLib, Gdk

class SubsonicAPI():
    def __init__(self):
        with open("/home/aurora/.config/Palindrome/config.json", "r") as f:
            info = json.load(f)
            salt = self.getSalt()
            token = (hashlib.md5(str(info["auth"]["password"]+salt).encode())).hexdigest()
            self.url = "https://" + info["hostname"] + "/rest/"
            self.par = {
                "u": info["auth"]["username"],
                "t": token,
                "s": salt,
                "v": "1.16.1",
                "c": "Palindrome"
            }

    def getSalt(self):
        return ''.join((random.choice(string.ascii_letters + string.digits) for i in range(10)))

    def getArtists(self):
        par2 = self.par.copy()
        indexes = xmltodict.parse(requests.get(self.url + "getArtists", params=par2).content)["subsonic-response"]["artists"]["index"]
        finalList = []
        for index in indexes:
            if isinstance(index["artist"], list):
                finalList.extend(index["artist"])
            elif isinstance(index["artist"], dict):
                finalList.append(index["artist"])
        return finalList

    def getAlbumsList(self):
        par2 = self.par.copy()
        par2['type'] = "alphabeticalByArtist"
        par2["size"] = 0
        albums = xmltodict.parse(requests.get(self.url + "getAlbumList", params=par2).content)["subsonic-response"]["albumList"]["album"]
        if isinstance(albums, list):
            return albums
        else:
            return [albums]

    def getPlaylists(self):
        par2 = self.par.copy()
        playlists = xmltodict.parse(requests.get(self.url + "getPlaylists", params=par2).content)["subsonic-response"]["playlists"]["playlist"]
        if isinstance(playlists, list):
            return playlists
        else:
            return [playlists]

    def getSong(self, songId):
        par2 = self.par.copy()
        par2["id"] = songId
        return xmltodict.parse(requests.get(self.url + "getSong", params=par2).content)["subsonic-response"]["song"]

    def getAlbum(self, albumId):
        par2 = self.par.copy()
        par2["id"] = albumId
        return xmltodict.parse(requests.get(self.url + "getAlbum", params=par2).content)["subsonic-response"]["album"]["song"]

    def getPlaylist(self, playlistId):
        par2 = self.par.copy()
        par2["id"] = playlistId
        return xmltodict.parse(requests.get(self.url + "getPlaylist", params=par2).content)["subsonic-response"]["playlist"]["entry"]

    def starSong(self, songId):
        par2 = self.par.copy()
        par2["id"] = songId
        requests.get(self.url + "star", params=par2)

    def unstarSong(self, songId):
        par2 = self.par.copy()
        par2["id"] = songId
        requests.get(self.url + "unstar", params=par2)

    def getCoverArt(self, songId):
        par2 = self.par.copy()
        par2["id"] = songId
        return requests.get(self.url + "getCoverArt", params=par2).content


class Player():
    import mpv
    player = mpv.MPV(ytdl=True)
    queue = []
    queueSelector = 0
    isPlaying = False

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

    def setVolume(self, volume : int):
        self.player.volume = volume

    def isPaused(self):
        return self.player.pause

    def getCurrentSong(self):
        return self.queue[self.queueSelector]


class Palindrome(Adw.Application):
    player = Player()
    api = SubsonicAPI()
    mainWindow = Gtk.Builder.new_from_file("data/ui/mainWindow.xml")
    progressBarAnimation = Adw.TimedAnimation.new(mainWindow.get_object("progressBar"), 0, 1, 5000, Adw.PropertyAnimationTarget.new(mainWindow.get_object("progressBar"), "fraction"))

    def __init__(self):
        super().__init__(application_id="org.auroraviola.palindrome")
        GLib.set_application_name("Palindrome")
        self.progressBarAnimation.set_easing(0)

    def formatTextForSongInfo(self, string):
        if len(string) > 30:
            return string[:28] + "..."

        return string

    def updateSongInfo(self):
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

    def updateNowPlaying(self):
        while True:
            try:
                self.mainWindow.get_object("nowPlaying_list").remove(self.mainWindow.get_object("nowPlaying_list").get_row_at_index(0))
            except:
                break

        for song in self.player.queue:
            thing = Adw.ActionRow().new()
            thing.props.title = str(song["@title"]).replace("&", "&amp;")
            thing.props.subtitle = str(song["@artist"]).replace("&", "&amp;")

            self.mainWindow.get_object("nowPlaying_list").append(thing)

    def updateSelected(self):
        self.mainWindow.get_object("nowPlaying_list").unselect_all()
        self.mainWindow.get_object("nowPlaying_list").select_row(self.mainWindow.get_object("nowPlaying_list").get_row_at_index(self.player.queueSelector))

    def addPlaylistToQueue(self, button, playlistId):
        songlist = self.api.getPlaylist(playlistId)
        if isinstance(songlist, list):
            for song in songlist:
                self.player.queue.append(song)
        elif isinstance(songlist, dict):
            self.player.queue.append(songlist)

        self.updateNowPlaying()
        self.updateSelected()

    def addAlbumToQueue(self, button, album_id):
        songlist = self.api.getAlbum(album_id)
        if isinstance(songlist, list):
            for song in songlist:
                self.player.queue.append(song)
        elif isinstance(songlist, dict):
            self.player.queue.append(songlist)

        self.updateNowPlaying()
        self.updateSelected()

    def getPlayUrl(self):
        par2 = self.api.par.copy()
        par2["id"] = self.player.getCurrentSong()["@id"]
        return self.api.url + "download?" + urllib.parse.urlencode(par2)

    def playBtnPressed(self, button):
        if len(self.player.queue) > 0:
            if not self.player.isPlaying:
                button.props.icon_name = "media-playback-pause-symbolic"
                self.player.play(self.getPlayUrl())
                self.progressBarAnimation.set_duration(int(self.player.getCurrentSong()["@duration"])*1000+1000)
                self.progressBarAnimation.play()
                self.player.unpause()
                self.updateSelected()
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
            self.updateSelected()
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
            self.updateSelected()
            self.updateSongInfo()

    def finishedProgressBar(self, bar):
        bar.reset()
        if (self.player.queueSelector < len(self.player.queue)-1) or (self.mainWindow.get_object("loopBtn").props.active):
            if not self.mainWindow.get_object("loopBtn").props.active:
                self.player.queueSelector += 1
                self.player.play(self.getPlayUrl())
                bar.set_duration(int(self.player.getCurrentSong()["@duration"])*1000+1000)
                bar.play()
                self.updateSelected()
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
        self.player.queue = []
        self.player.queueSelector = 0
        while True:
            try:
                self.mainWindow.get_object("nowPlaying_list").remove(self.mainWindow.get_object("nowPlaying_list").get_row_at_index(0))
            except:
                break

    def setVolume(self, slider):
        self.player.setVolume(int((slider.get_value()**0.5)*100))

    def do_activate(self):
        window = Adw.ApplicationWindow(application=self, title="Palindrome")

        for artist in self.api.getArtists():
            thing = Adw.ActionRow().new()
            thing.props.title = str(artist["@name"]).replace("&", "&amp;")
            if artist["@albumCount"] != "1":
                thing.props.subtitle = str(artist["@albumCount"]) + " Albums"
            else:
                thing.props.subtitle = str(artist["@albumCount"]) + " Album"

            self.mainWindow.get_object("artists_list").append(thing)

        for album in self.api.getAlbumsList():
            thing = Adw.ActionRow().new()
            thing.props.title = str(album["@title"]).replace("&", "&amp;")
            thing.props.subtitle = str(album["@artist"]).replace("&", "&amp;")

            addQueueBtn = Gtk.Button().new()
            addQueueBtn.props.icon_name = "list-add-symbolic"
            addQueueBtn.connect("clicked", self.addAlbumToQueue, album["@id"])
            addQueueBtn.props.margin_top = 10
            addQueueBtn.props.margin_bottom = 10
            thing.add_suffix(addQueueBtn)

            self.mainWindow.get_object("albums_list").append(thing)

        for playlist in self.api.getPlaylists():
            thing = Adw.ActionRow().new()
            thing.props.title = str(playlist["@name"]).replace("&", "&amp;")
            if playlist["@songCount"] != "1":
                thing.props.subtitle = str(playlist["@songCount"]) + " Songs"
            else:
                thing.props.subtitle = str(playlist["@songCount"]) + " Song"

            addQueueBtn = Gtk.Button().new()
            addQueueBtn.props.icon_name = "list-add-symbolic"
            addQueueBtn.connect("clicked", self.addPlaylistToQueue, playlist["@id"])
            addQueueBtn.props.margin_top = 10
            addQueueBtn.props.margin_bottom = 10
            thing.add_suffix(addQueueBtn)

            self.mainWindow.get_object("playlists_list").append(thing)

        self.progressBarAnimation.connect("done", self.finishedProgressBar)

        self.mainWindow.get_object("playBtn").connect("clicked", self.playBtnPressed)
        self.mainWindow.get_object("stopBtn").connect("clicked", self.stopBtnPressed, self.mainWindow.get_object("playBtn"))
        self.mainWindow.get_object("prevBtn").connect("clicked", self.prevBtnPressed)
        self.mainWindow.get_object("nextBtn").connect("clicked", self.nextBtnPressed)
        self.mainWindow.get_object("FavouriteBtn").connect("clicked", self.favouriteBtnPressed)

        self.mainWindow.get_object("emptyQueueBtn").connect("clicked", self.emptyQueueBtnPressed)

        self.mainWindow.get_object("volumeChanger").connect("value-changed", self.setVolume)

        window = self.mainWindow.get_object("window")

        window.present()


app = Palindrome()
exit_status = app.run(sys.argv)
sys.exit(exit_status)

