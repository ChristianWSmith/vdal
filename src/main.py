#!/usr/bin/env python

import sys, gi, os, logging

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, Pango


XDG_DATA_DIRS = [ os.getenv('XDG_DATA_HOME') ] + \
        os.getenv('XDG_DATA_DIRS').split(':')
XDG_APPLICATION_DIRS = filter(os.path.isdir, [f"{directory}/applications" for directory in XDG_DATA_DIRS])


def parse_desktop_file(file):
    current_section = '[Desktop Entry]'
    config = {current_section: {}}
    for line in [line.strip() for line in open(file, 'r').readlines()]:
        try:
            if line.startswith('[') and line.endswith(']'):
                current_section = line
                config[current_section] = {}
            else:
                tokens = line.split('=')
                key = tokens[0]
                value = '='.join(tokens[1:])
                config[current_section][key] = value
        except Exception as e:
            logging.error(f"Failed to parse desktop file: {file}", e)
    return config


def get_desktop_entries():
    def is_desktop_file(file):
        return file.endswith(".desktop")
    entries = {}
    for directory in XDG_APPLICATION_DIRS:
        for entry in filter(is_desktop_file, os.listdir(directory)):
            try:
                if entry not in entries:
                    config = parse_desktop_file(f"{directory}/{entry}")
                    if 'NoDisplay' in config['[Desktop Entry]'] and config['[Desktop Entry]']['NoDisplay'] == "true":
                        logging.debug(f"NoDisplay: {entry}")
                    elif 'Hidden' in config['[Desktop Entry]'] and config['[Desktop Entry]']['Hidden'] == "true":
                        logging.debug(f"Hidden: {entry}")
                    else:
                        entries[entry] = (f"{directory}/{entry}", config)
                else:
                    logging.debug(f"Already have: {entry}")
            except Exception as e:
                logging.error(f"Failed to create entry: {entry}", e)
    return list(entries.values())


def make_button(entry):
    def on_button_clicked(widget):
        logging.debug(config['[Desktop Entry]']['Exec'])
    path, config = entry
    button = Gtk.Button(label=config['[Desktop Entry]']['Name'])
    button.connect("clicked", on_button_clicked)
    button.set_property("width-request", 100)
    button.set_property("height-request", 100)
    button.set_property("hexpand", False)
    button.set_property("vexpand", False)
    button.get_child().set_property("ellipsize", Pango.EllipsizeMode.END)
    button.get_child().set_property("max-width-chars", 8)
    return button


def make_scrolled_window():
    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    return scrolled_window


def make_flow_box():
    flow_box = Gtk.FlowBox()
    flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
    flow_box.set_column_spacing(6)
    flow_box.set_row_spacing(6)
    return flow_box


def make_box():
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    box.set_margin_start(12)
    box.set_margin_end(12)
    box.set_margin_top(12)
    box.set_margin_bottom(12)
    return box


class VdalWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        flow_box = make_flow_box()
        for entry in get_desktop_entries():
            button = make_button(entry)
            flow_box.append(button)
        box = make_box()
        box.append(flow_box)
        scrolled_window = make_scrolled_window()
        scrolled_window.set_child(box)
        self.set_child(scrolled_window)


class VdalApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.github.ChristianWSmith.vdal", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        window = VdalWindow(self)
        window.present()


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


def main():
    setup_logging()
    app = VdalApplication()
    exit_status = app.run(None)
    sys.exit(exit_status)


if __name__ == "__main__":
    main()

