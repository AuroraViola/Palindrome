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
        self.player.pause = True

    def togglePause(self):
        self.player.pause = not self.player.pause

    def setVolume(self, volume : int):
        self.player.volume = volume

class Palindrome(Adw.Application):
    player = player()

    def __init__(self):
        super().__init__(application_id="org.auroraviola.palindrome")
        GLib.set_application_name("Palindrome")

    def do_activate(self):
        window = Adw.ApplicationWindow(application=self, title="Palindrome")
        mainWindow = Gtk.Builder()
        mainWindow.add_from_file("data/ui/mainWindow.xml")

        window = mainWindow.get_object("window")
        window.present()

app = Palindrome()
exit_status = app.run(sys.argv)
sys.exit(exit_status)

