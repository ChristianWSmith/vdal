#!/usr/bin/env python

import sys
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk


class VdalApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.github.ChristianWSmith.vdal'")
        GLib.set_application_name('vdal')

    def do_activate(self):
        window = Gtk.ApplicationWindow(application=self, title="vdal")
        window.present()


def main():
    app = VdalApplication()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)


if __name__ == "__main__":
    main()

