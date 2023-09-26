#!/usr/bin/env python

import sys, gi, os, logging, json

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, Pango, Gdk, GdkPixbuf, GLib

VDAL_CACHE_DIR = f"{os.getenv('XDG_CACHE_HOME')}/vdal"
ICON_CACHE_PATH = f"{VDAL_CACHE_DIR}/icons.json"
os.makedirs(VDAL_CACHE_DIR, mode=0o755, exist_ok=True)
XDG_DATA_DIRS = [ os.getenv('XDG_DATA_HOME') ] + \
        os.getenv('XDG_DATA_DIRS').split(':')
XDG_APPLICATION_DIRS = filter(os.path.isdir, [f"{directory}/applications" for directory in XDG_DATA_DIRS])
XDG_ICON_DIRS = list(filter(os.path.isdir, [f"{directory}/icons" for directory in XDG_DATA_DIRS]))
GDK_DISPLAY = Gdk.Display.get_default()
ICON_THEME = Gtk.IconTheme.get_for_display(GDK_DISPLAY)
ICON_SIZE_DIRS_ORDERED = [
    'scalable',
    '512', '512x512', 
    '256', '256x256', 
    '192', '192x192',
    '128', '128x28',
    '96', '96x96',
    '72', '72x72',
    '64', '64x64',
    '48', '48x48',
    '36', '36x36',
    '32', '32x32',
    '24', '24x24',
    '22', '22x22',
    '16', '16x16',
    'symbolic'
    ]
ICON_SIZE_DIRS = set(ICON_SIZE_DIRS_ORDERED)


def order_icon_size_dir(dirs):
    out = []
    for icon_size_dir in ICON_SIZE_DIRS_ORDERED:
        if icon_size_dir in dirs:
            out.append(icon_size_dir)
            dirs.remove(icon_size_dir)
            if len(dirs) == 0:
                break
    return out + dirs


def walk(top, below_size_dir=False):
    dirs = []
    nondirs = []
    walk_dirs = []
    try:
        scandir_it = os.scandir(top)
    except OSError as error:
        return
    with scandir_it:
        while True:
            try:
                try:
                    entry = next(scandir_it)
                except StopIteration:
                    break
            except OSError as error:
                return
            try:
                is_dir = entry.is_dir()
            except OSError:
                is_dir = False

            if is_dir:
                dirs.append(entry.name)
            else:
                nondirs.append(entry.name)
    yield top, dirs, nondirs

    # Recurse into sub-directories
    islink, join = os.path.islink, os.path.join
    if not below_size_dir and len(set(dirs).intersection(ICON_SIZE_DIRS)) != 0:
        below_size_dir = True
        dirs = order_icon_size_dir(dirs)
    for dirname in dirs:
        new_path = join(top, dirname)
        yield from walk(new_path, below_size_dir)


def get_icon_name_from_desktop_entry(entry):
    path, config = entry
    if 'Icon' in config['[Desktop Entry]']:
        icon_name = config['[Desktop Entry]']['Icon']
        logging.debug(f"Entry {path} has icon: {icon_name}")
    else:
        icon_name = ""
        logging.warning(f"Entry has no icon: {path}")
    return icon_name


def get_icons(desktop_entries):
    if os.path.isfile(ICON_CACHE_PATH):
        icons = json.loads(open(ICON_CACHE_PATH, "r").read())
        cache_stale = False
    else:
        icons = {}
        cache_stale = True

    requested_icons = set()
    for desktop_entry in desktop_entries:
        icon_name = get_icon_name_from_desktop_entry(desktop_entry)
        if icon_name not in icons:
            icons[icon_name] = ""
            cache_stale = True
        requested_icons.add(icon_name)
    requested_icons.remove('')

    if not cache_stale:
        return icons

    theme_name = ICON_THEME.get_theme_name()
    theme_dirs = []
    hicolor_dirs = []
    default_dirs = []
    other_dirs = []

    for path in ICON_THEME.get_search_path():
        if path.endswith("icons"):
            if os.path.isdir(f"{path}/{theme_name}"):
                theme_dirs.append(f"{path}/{theme_name}")
            if os.path.isdir(f"{path}/hicolor"):
                hicolor_dirs.append(f"{path}/hicolor")
            if os.path.isdir(f"{path}/default"):
                hicolor_dirs.append(f"{path}/default")
        else:
            other_dirs.append(path)
    
    icon_dirs = theme_dirs + hicolor_dirs  + default_dirs + other_dirs

    for icon_dir in icon_dirs:
        for root, dirs, files in walk(icon_dir):
            for name in files:
                icon_name = '.'.join(name.split('.')[:-1])
                if icon_name in requested_icons:
                    requested_icons.remove(icon_name)
                    path = os.path.join(root, name)
                    icons[icon_name] = path
                    if len(requested_icons) == 0:
                        open(ICON_CACHE_PATH, "w").write(json.dumps(icons))
                        return icons

    open(ICON_CACHE_PATH, "w").write(json.dumps(icons))
    return icons


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


def make_button(entry, icons):
    path, config = entry

    icon_name = get_icon_name_from_desktop_entry(entry)
    icon_path = icons[icon_name]

    image = Gtk.Image()

    if icon_path.endswith(".svg"):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_path)
        image.set_from_pixbuf(pixbuf)
    else:
        image.set_from_file(icon_path)
    image.set_property("hexpand", True)
    image.set_property("vexpand", True)

    label = Gtk.Label(label=config['[Desktop Entry]']['Name'])
    label.set_property("ellipsize", Pango.EllipsizeMode.END)
    label.set_property("max-width-chars", 8)
    
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    box.append(image)
    box.append(label)
    box.set_property("hexpand", True)
    box.set_property("vexpand", True)
    
    def on_button_clicked(widget):
        logging.debug(f"gio launch {path}")
        os.system(f"gio launch {path} & disown")

    button = Gtk.Button()
    button.set_child(box) 
    button.connect("clicked", on_button_clicked)
    button.set_property("width-request", 100)
    button.set_property("height-request", 100)
    button.set_property("hexpand", False)
    button.set_property("vexpand", False)
    
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
        desktop_entries = get_desktop_entries()
        icons = get_icons(desktop_entries)
        for entry in desktop_entries:
            button = make_button(entry, icons)
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

