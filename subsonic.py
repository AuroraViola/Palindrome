import hashlib
import json
import random
import string
import requests
import xmltodict
import os

class API():
    def __init__(self):
        self.configPath = (os.path.expanduser("~") + "/.config/Palindrome")
        # It opens the config file.
        if not os.path.exists(self.configPath):
            os.mkdir(self.configPath)

        if not os.path.exists((self.configPath + "/auth.json")):
            auth = {
                "hostname": "",
                "username": "",
                "password": ""
            }
            jsonObj = json.dumps(auth, indent=4)
            with open(self.configPath + "/auth.json", "w") as f:
                f.write(jsonObj)


        with open((self.configPath + "/auth.json"), "r") as f:
            info = json.load(f)

            # create the salt and token
            salt = self.getSalt()
            token = (hashlib.md5(str(info["password"]+salt).encode())).hexdigest()

            self.url = info["hostname"] + "/rest/"
            self.par = {
                "u": info["username"],
                "t": token,
                "s": salt,
                "v": "1.16.1",
                "c": "Palindrome"
            }

    def getSalt(self):
        # Returns a random string of 10 chars. This will be the salt
        return ''.join((random.choice(string.ascii_letters + string.digits) for i in range(10)))

    def updatePar(self, host, username, password):
        auth = {
            "hostname": host,
            "username": username,
            "password": password
        }

        jsonObj = json.dumps(auth, indent=4)
        with open(self.configPath + "/auth.json", "w") as f:
            f.write(jsonObj)

        self.url = host + "/rest/"
        salt = self.getSalt()
        token = (hashlib.md5(str(password + salt).encode())).hexdigest()
        self.par = {
            "u": username,
            "t": token,
            "s": salt,
            "v": "1.16.1",
            "c": "Palindrome"
        }

    def ping(self):
        try:
            request = xmltodict.parse(requests.get(self.url + "ping", params=self.par).content)["subsonic-response"]
            if request["@status"] == "ok":
                return "ok"
            elif request["error"]["@code"] == "10" or request["error"]["@code"] == "40":
                return "Wrong username or password"
            else:
                return "generic error"
        except:
            return "Invalid URL"

    def getArtists(self):
        # Return a list of all artists (an artist is a dict)
        par2 = self.par.copy()
        try:
            indexes = xmltodict.parse(requests.get(self.url + "getArtists", params=par2).content)["subsonic-response"]["artists"]["index"]
            finalList = []
            for index in indexes:
                if isinstance(index["artist"], list):
                    finalList.extend(index["artist"])
                elif isinstance(index["artist"], dict):
                    finalList.append(index["artist"])
            return finalList
        except:
            return []

    def getAlbumsList(self):
        # Return a list of all albums (an album is a dict)
        par2 = self.par.copy()
        par2['type'] = "alphabeticalByArtist"
        par2["size"] = 0
        try:
            albums = xmltodict.parse(requests.get(self.url + "getAlbumList", params=par2).content)["subsonic-response"]["albumList"]["album"]
            if isinstance(albums, list):
                return albums
            else:
                return [albums]
        except:
            return []

    def getPlaylists(self):
        # Return a list of all playlist (a playlist is a dict)
        par2 = self.par.copy()
        try:
            playlists = xmltodict.parse(requests.get(self.url + "getPlaylists", params=par2).content)["subsonic-response"]["playlists"]["playlist"]
            if isinstance(playlists, list):
                return playlists
            else:
                return [playlists]
        except:
            return []

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
