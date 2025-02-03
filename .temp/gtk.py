#!/bin/python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os
import sys
from main import Merger
from io import StringIO
import contextlib

class SubtitleMergerGUI:
    def __init__(self):
        # Create builder and load UI
        self.builder = Gtk.Builder()
        
        # Main window
        self.window = Gtk.Window(title="Subtitle Merger")
        self.window.set_border_width(10)
        self.window.set_default_size(600, 400)
        self.window.connect("destroy", Gtk.main_quit)

        # Create main vertical box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.window.add(self.main_box)

        # File selection frames
        self.create_file_selection_frame("Subtitle 1:", "subtitle1")
        self.create_file_selection_frame("Subtitle 2:", "subtitle2")
        
        # Output file frame
        self.create_output_selection_frame()

        # Color selection
        self.create_color_selection()

        # Codec selection
        self.create_codec_selection()

        # Log window
        self.create_log_window()

        # Run button
        self.run_button = Gtk.Button(label="Merge Subtitles")
        self.run_button.connect("clicked", self.on_merge_clicked)
        self.main_box.pack_start(self.run_button, False, False, 0)

    def create_file_selection_frame(self, label_text, name):
        frame = Gtk.Frame(label=label_text)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        frame.add(box)

        entry = Gtk.Entry()
        setattr(self, f"{name}_entry", entry)
        box.pack_start(entry, True, True, 0)

        button = Gtk.Button(label="Browse")
        button.connect("clicked", self.on_file_chosen, name)
        box.pack_start(button, False, False, 0)

        self.main_box.pack_start(frame, False, False, 0)

    def create_output_selection_frame(self):
        frame = Gtk.Frame(label="Output File:")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        frame.add(box)

        self.output_entry = Gtk.Entry()
        box.pack_start(self.output_entry, True, True, 0)

        button = Gtk.Button(label="Browse")
        button.connect("clicked", self.on_output_chosen)
        box.pack_start(button, False, False, 0)

        self.main_box.pack_start(frame, False, False, 0)

    def create_color_selection(self):
        frame = Gtk.Frame(label="Subtitle 1 Color:")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        frame.add(box)

        self.color_combo = Gtk.ComboBoxText()
        colors = ["default", "yellow", "cyan", "red", "green", "blue", "magenta"]
        for color in colors:
            self.color_combo.append_text(color)
        self.color_combo.set_active(0)
        box.pack_start(self.color_combo, True, True, 0)

        self.main_box.pack_start(frame, False, False, 0)

    def create_codec_selection(self):
        frame = Gtk.Frame(label="Codec:")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        frame.add(box)

        self.codec_combo = Gtk.ComboBoxText()
        codecs = ["auto", "utf-8", "windows-1256"]
        for codec in codecs:
            self.codec_combo.append_text(codec)
        self.codec_combo.set_active(0)
        box.pack_start(self.codec_combo, True, True, 0)

        self.main_box.pack_start(frame, False, False, 0)

    def create_log_window(self):
        frame = Gtk.Frame(label="Log:")
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_size_request(-1, 150)

        self.log_buffer = Gtk.TextBuffer()
        self.log_view = Gtk.TextView(buffer=self.log_buffer)
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)

        scrolled_window.add(self.log_view)
        frame.add(scrolled_window)
        self.main_box.pack_start(frame, True, True, 0)

    def on_file_chosen(self, button, name):
        dialog = Gtk.FileChooserDialog(
            title="Choose a subtitle file",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        # Add file filters
        filter_srt = Gtk.FileFilter()
        filter_srt.set_name("SRT files")
        filter_srt.add_pattern("*.srt")
        dialog.add_filter(filter_srt)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            getattr(self, f"{name}_entry").set_text(dialog.get_filename())
        dialog.destroy()

    def on_output_chosen(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Choose output location",
            parent=self.window,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )

        # Add file filters
        filter_srt = Gtk.FileFilter()
        filter_srt.set_name("SRT files")
        filter_srt.add_pattern("*.srt")
        dialog.add_filter(filter_srt)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.output_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def log_message(self, message):
        GLib.idle_add(self._append_to_log, message + "\n")

    def _append_to_log(self, message):
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, message)
        # Scroll to the end
        self.log_view.scroll_to_iter(self.log_buffer.get_end_iter(), 0.0, False, 0.0, 0.0)
        return False

    def on_merge_clicked(self, button):
        subtitle1 = self.subtitle1_entry.get_text()
        subtitle2 = self.subtitle2_entry.get_text()
        output = self.output_entry.get_text()
        color = self.color_combo.get_active_text()
        codec = self.codec_combo.get_active_text()

        if not all([subtitle1, subtitle2]):
            self.log_message("Error: Please select both subtitle files.")
            return

        if not output:
            output = f"{os.path.splitext(subtitle1)[0]}_merged.srt"
            self.output_entry.set_text(output)

        if codec == "auto":
            codec = "windows-1256" if os.name == "nt" else "utf-8"

        try:
            self.log_message(f"Starting merger...")
            self.log_message(f"Subtitle 1: {subtitle1}")
            self.log_message(f"Subtitle 2: {subtitle2}")
            self.log_message(f"Output: {output}")
            self.log_message(f"Color: {color}")
            self.log_message(f"Codec: {codec}")

            merger = Merger(output_name=output)
            merger.add(subtitle1, color=color, codec=codec)
            merger.add(subtitle2)
            merger.merge()
            
            self.log_message("Subtitles merged successfully!")
        except Exception as e:
            self.log_message(f"Error during merging: {e}")

def main():
    app = SubtitleMergerGUI()
    app.window.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
