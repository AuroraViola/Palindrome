import hashlib
import json
import random
import string
import requests
import xmltodict

class API():
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

    def scrobble(self, songId, submission):
        par2 = self.par.copy()
        par2["id"] = songId
        par2["submission"] = submission
        requests.get(self.url + "scrobble", params=par2)
