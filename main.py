import sys
import json
import xmltodict
import requests
import gi
import urllib.parse

gi.require_version('Adw', '1')
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gtk, GLib

class player():
    import mpv
    player = mpv.MPV(ytdl=True)

    def __init__(self):
        pass

    def pause(self):
        self.player.pause = True

    def unpause(self):
        self.player.pause = False

    def togglePause(self):
        self.player.pause = not self.player.pause

    def setVolume(self, volume : int):
        self.player.volume = volume

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

class Palindrome(Adw.Application):
    player = player()
    api = SubsonicAPI()

    def __init__(self):
        super().__init__(application_id="org.auroraviola.palindrome")
        GLib.set_application_name("Palindrome")

    def do_activate(self):
        window = Adw.ApplicationWindow(application=self, title="Palindrome")
        mainWindow = Gtk.Builder.new_from_file("data/ui/mainWindow.xml")

        for artist in self.api.getArtistsList():
            thing = Adw.ActionRow().new()
            thing.props.title = str(artist["@name"]).replace("&", "&amp;")
            if artist["@albumCount"] != "1":
                thing.props.subtitle = str(artist["@albumCount"]) + " Albums"
            else:
                thing.props.subtitle = str(artist["@albumCount"]) + " Album"

            mainWindow.get_object("artists_list").append(thing)

        for album in self.api.getAlbumsList():
            thing = Adw.ActionRow().new()
            thing.props.title = str(album["@title"]).replace("&", "&amp;")
            thing.props.subtitle = str(album["@artist"]).replace("&", "&amp;")

            mainWindow.get_object("albums_list").append(thing)

        for playlist in self.api.getPlaylistsList():
            thing = Adw.ActionRow().new()
            thing.props.title = str(playlist["@name"]).replace("&", "&amp;")
            if playlist["@songCount"] != "1":
                thing.props.subtitle = str(playlist["@songCount"]) + " Songs"
            else:
                thing.props.subtitle = str(playlist["@songCount"]) + " Song"

            mainWindow.get_object("playlists_list").append(thing)

        window = mainWindow.get_object("window")
        window.present()

app = Palindrome()
exit_status = app.run(sys.argv)
sys.exit(exit_status)

