import hashlib
import json
import random
import string
import requests
import xmltodict

class API():
    def __init__(self):
        # It opens the config file. THIS NEED TO BE REWORKED
        with open("/home/aurora/.config/Palindrome/config.json", "r") as f:
            info = json.load(f)

            # create the salt and token
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
        # Returns a random string of 10 chars. This will be the salt
        return ''.join((random.choice(string.ascii_letters + string.digits) for i in range(10)))

    def getArtists(self):
        # Return a list of all artists (an artist is a dict)
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
        # Return a list of all albums (an album is a dict)
        par2 = self.par.copy()
        par2['type'] = "alphabeticalByArtist"
        par2["size"] = 0
        albums = xmltodict.parse(requests.get(self.url + "getAlbumList", params=par2).content)["subsonic-response"]["albumList"]["album"]
        if isinstance(albums, list):
            return albums
        else:
            return [albums]

    def getPlaylists(self):
        # Return a list of all playlist (a playlist is a dict)
        par2 = self.par.copy()
        playlists = xmltodict.parse(requests.get(self.url + "getPlaylists", params=par2).content)["subsonic-response"]["playlists"]["playlist"]
        if isinstance(playlists, list):
            return playlists
        else:
            return [playlists]

    def getSong(self, songId):
        # Return information (as a dict) about the specified song
        par2 = self.par.copy()
        par2["id"] = songId
        return xmltodict.parse(requests.get(self.url + "getSong", params=par2).content)["subsonic-response"]["song"]

    def getAlbumSongs(self, albumId):
        # Return a list songs about the specified album
        par2 = self.par.copy()
        par2["id"] = albumId
        return xmltodict.parse(requests.get(self.url + "getAlbum", params=par2).content)["subsonic-response"]["album"]["song"]

    def getPlaylistSongs(self, playlistId):
        # Return a list of songs about the specified playlist
        par2 = self.par.copy()
        par2["id"] = playlistId
        return xmltodict.parse(requests.get(self.url + "getPlaylist", params=par2).content)["subsonic-response"]["playlist"]["entry"]

    def starSong(self, songId):
        # Star a specific song
        par2 = self.par.copy()
        par2["id"] = songId
        requests.get(self.url + "star", params=par2)

    def unstarSong(self, songId):
        # Unstar a specific song
        par2 = self.par.copy()
        par2["id"] = songId
        requests.get(self.url + "unstar", params=par2)

    def getCoverArt(self, songId):
        # Get the coverArt of a specific song
        par2 = self.par.copy()
        par2["id"] = songId
        return requests.get(self.url + "getCoverArt", params=par2).content

    def scrobble(self, songId, submission):
        # Scrobble a specific song
        par2 = self.par.copy()
        par2["id"] = songId
        par2["submission"] = submission
        requests.get(self.url + "scrobble", params=par2)
