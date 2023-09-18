import sys
import json
import xmltodict
import requests
import gi
import urllib.parse

gi.require_version('Adw', '1')
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gtk, GLib

class SubsonicAPI():
    def __init__(self):
        with open("/home/aurora/.config/Palindrome/config.json", "r") as f:
            info = json.load(f)
            self.url = "https://" + info["hostname"] + "/rest/"
            self.par = {
                "u": info["auth"]["username"],
                "p": info["auth"]["password"],
                "v": "1.16.1",
                "c": "Palindrome"
            }

    def getArtistsList(self):
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

    def getPlaylistsList(self):
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


class Palindrome(Adw.Application):
    player = Player()
    api = SubsonicAPI()
    mainWindow = Gtk.Builder.new_from_file("data/ui/mainWindow.xml")

    def __init__(self):
        super().__init__(application_id="org.auroraviola.palindrome")
        GLib.set_application_name("Palindrome")

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
        par2 = self.api.par.copy()
        par2["id"] = playlistId
        songlist = xmltodict.parse(requests.get(self.api.url + "getPlaylist", params=par2).content)["subsonic-response"]["playlist"]["entry"]
        if isinstance(songlist, list):
            for song in songlist:
                self.player.queue.append(song)
        elif isinstance(songlist, dict):
            self.player.queue.append(songlist)

        self.updateNowPlaying()

    def addAlbumToQueue(self, button, albumId):
        par2 = self.api.par.copy()
        par2["id"] = albumId
        songlist = xmltodict.parse(requests.get(self.api.url + "getAlbum", params=par2).content)["subsonic-response"]["album"]["song"]
        if isinstance(songlist, list):
            for song in songlist:
                self.player.queue.append(song)
        elif isinstance(songlist, dict):
            self.player.queue.append(songlist)

        self.updateNowPlaying()

    def getPlayUrl(self):
        par2 = self.api.par.copy()
        par2["id"] = self.player.queue[self.player.queueSelector]["@id"]
        return self.api.url + "download?" + urllib.parse.urlencode(par2)

    def playBtnPressed(self, button):
        if len(self.player.queue) > 0:
            if not self.player.isPlaying:
                button.props.icon_name = "media-playback-pause-symbolic"
                self.player.play(self.getPlayUrl())
                self.player.unpause()
                self.updateSelected()
            else:
                if button.props.icon_name == "media-playback-start-symbolic":
                    button.props.icon_name = "media-playback-pause-symbolic"
                    self.player.unpause()
                else:
                    button.props.icon_name = "media-playback-start-symbolic"
                    self.player.pause()

    def stopBtnPressed(self, button, playBtn):
        self.player.stop()
        self.mainWindow.get_object("nowPlaying_list").unselect_all()
        playBtn.props.icon_name = "media-playback-start-symbolic"

    def prevBtnPressed(self, button):
        if self.player.queueSelector > 0:
            self.player.queueSelector -= 1
            self.player.play(self.getPlayUrl())
            self.updateSelected()

    def nextBtnPressed(self, button):
        if self.player.queueSelector < len(self.player.queue)-1:
            self.player.queueSelector += 1
            self.player.play(self.getPlayUrl())
            self.updateSelected()

    def do_activate(self):
        window = Adw.ApplicationWindow(application=self, title="Palindrome")

        for artist in self.api.getArtistsList():
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

            thing.add_suffix(addQueueBtn)

            self.mainWindow.get_object("albums_list").append(thing)

        for playlist in self.api.getPlaylistsList():
            thing = Adw.ActionRow().new()
            thing.props.title = str(playlist["@name"]).replace("&", "&amp;")
            if playlist["@songCount"] != "1":
                thing.props.subtitle = str(playlist["@songCount"]) + " Songs"
            else:
                thing.props.subtitle = str(playlist["@songCount"]) + " Song"

            addQueueBtn = Gtk.Button().new()
            addQueueBtn.props.icon_name = "list-add-symbolic"
            addQueueBtn.connect("clicked", self.addPlaylistToQueue, playlist["@id"])

            thing.add_suffix(addQueueBtn)

            self.mainWindow.get_object("playlists_list").append(thing)

        self.mainWindow.get_object("playBtn").connect("clicked", self.playBtnPressed)
        self.mainWindow.get_object("stopBtn").connect("clicked", self.stopBtnPressed, self.mainWindow.get_object("playBtn"))
        self.mainWindow.get_object("prevBtn").connect("clicked", self.prevBtnPressed)
        self.mainWindow.get_object("nextBtn").connect("clicked", self.nextBtnPressed)

        window = self.mainWindow.get_object("window")
        window.present()

app = Palindrome()
exit_status = app.run(sys.argv)
sys.exit(exit_status)

