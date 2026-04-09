#!/usr/bin/env python3
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, GObject, Adw


import keyutils
import subprocess
from gi.repository import Gtk, GObject, Adw, Gio

class KeyItem(GObject.Object):
    __gtype_name__ = 'KeyItem'
    
    id = GObject.Property(type=str)
    desc = GObject.Property(type=str)

    def __init__(self, id, desc):
        super().__init__()
        self.id = id
        self.desc = desc

class AddKeyDialog(Gtk.Window):
    def __init__(self, parent, key_to_update=None):
        super().__init__(modal=True, transient_for=parent)
        self.main_window = parent

        self.set_default_size(450, 200)

        header = Adw.HeaderBar()
        self.set_titlebar(header)
        
        ok_button = Gtk.Button(label="OK")
        ok_button.add_css_class("suggested-action")
        ok_button.connect("clicked", self.on_ok_clicked)
        header.pack_end(ok_button)

        cancel_button = Gtk.Button(label="キャンセル")
        cancel_button.connect("clicked", lambda x: self.close())
        header.pack_start(cancel_button)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12, spacing=12)
        self.set_child(box)

        self.desc_row = Adw.EntryRow(title="名前")
        self.value_row = Adw.PasswordEntryRow(title="値")
        
        if key_to_update:
            self.set_title("キーの更新")
            self.desc_row.set_text(key_to_update.desc)
            self.desc_row.set_editable(False)
            self.value_row.grab_focus()
        else:
            self.set_title("キーの追加")

        box.append(self.desc_row)
        box.append(self.value_row)

    def on_ok_clicked(self, widget):
        desc = self.desc_row.get_text().strip()
        value = self.value_row.get_text()

        if not desc:
            self.main_window.show_error_dialog("名前は空にできません。")
            return

        try:
            keyutils.add_key(
                desc.encode(),
                value.encode(),
                keyutils.KEY_SPEC_USER_KEYRING
            )
            self.main_window._load_keys()
            self.close()
        except keyutils.Error as e:
            self.main_window.show_error_dialog(f"キーの追加/更新に失敗しました: {e}")


class KeyringWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("カーネルキーリング・マネージャー")
        self.set_default_size(600, 400)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.main_box)

        header = Adw.HeaderBar()
        self.set_titlebar(header)

        # --- Buttons ---
        add_button = Gtk.Button(label="追加")
        add_button.connect("clicked", self.on_add_clicked)
        header.pack_start(add_button)

        self.update_button = Gtk.Button(label="更新")
        self.update_button.connect("clicked", self.on_update_clicked)
        self.update_button.set_sensitive(False)
        header.pack_start(self.update_button)

        self.delete_button = Gtk.Button(label="削除")
        self.delete_button.connect("clicked", self.on_delete_clicked)
        self.delete_button.set_sensitive(False)
        header.pack_end(self.delete_button)

        # --- Key List ---
        self.store = Gio.ListStore(item_type=KeyItem)

        scrolled_window = Gtk.ScrolledWindow(vexpand=True)
        
        self.selection_model = Gtk.SingleSelection(model=self.store)
        list_view = Gtk.ColumnView(model=self.selection_model)
        self.selection_model.connect("selection-changed", self.on_selection_changed)
        scrolled_window.set_child(list_view)
        self.main_box.append(scrolled_window)

        for title, prop in [("ID", "id"), ("名前", "desc")]:
            factory = Gtk.SignalListItemFactory()
            factory.connect("setup", self._setup_list_item)
            factory.connect("bind", self._bind_list_item, prop)
            col = Gtk.ColumnViewColumn(title=title, factory=factory)
            list_view.append_column(col)
        
        self._load_keys()

    def _setup_list_item(self, factory, list_item):
        list_item.set_child(Gtk.Label(xalign=0))

    def _bind_list_item(self, factory, list_item, prop):
        label = list_item.get_child()
        item = list_item.get_item()
        label.set_text(item.get_property(prop))

    def _load_keys(self):
        self.store.remove_all()
        try:
            res = subprocess.run(
                ["keyctl", "list", "@u"], capture_output=True, text=True, check=True
            )
            lines = res.stdout.strip().split('\n')

            # Skip the summary line, if present
            if lines and "in keyring" in lines[0]:
                lines = lines[1:]

            for line in lines:
                line = line.strip()
                if not line: continue
                
                parts = line.split()
                if not parts: continue
                
                key_id_str_with_colon = parts[0]
                if not key_id_str_with_colon.endswith(':'):
                    continue

                key_id_str = key_id_str_with_colon.rstrip(':')

                try:
                    key_id = int(key_id_str)
                    desc_bytes = keyutils.describe_key(key_id)
                    desc_parts = desc_bytes.decode().split(';')
                    
                    if len(desc_parts) == 5 and desc_parts[0] == 'user':
                        description = desc_parts[4]
                        self.store.append(KeyItem(id=key_id_str, desc=description))
                except (keyutils.Error, ValueError, IndexError):
                    continue
        except subprocess.CalledProcessError as e:
            if "Required key not available" not in e.stderr:
                self.show_error_dialog(f"キーの読み込みに失敗しました: {e.stderr}")
        except FileNotFoundError:
            self.show_error_dialog("`keyctl`コマンドが見つかりません。keyutilsをインストールしてください。")

    def on_selection_changed(self, selection, position, n_items):
        is_selected = selection.get_selected() != Gtk.INVALID_LIST_POSITION
        self.update_button.set_sensitive(is_selected)
        self.delete_button.set_sensitive(is_selected)

    def on_add_clicked(self, widget):
        dialog = AddKeyDialog(self)
        dialog.present()
        
    def on_update_clicked(self, widget):
        key_item = self.get_selected_key_item()
        if not key_item:
            return
        dialog = AddKeyDialog(self, key_to_update=key_item)
        dialog.present()

    def get_selected_key_item(self):
        selected_pos = self.selection_model.get_selected()
        return self.store.get_item(selected_pos) if selected_pos != Gtk.INVALID_LIST_POSITION else None

    def on_delete_clicked(self, widget):
        key_item = self.get_selected_key_item()
        if not key_item: return

        dialog = Adw.MessageDialog(
            transient_for=self, modal=True,
            heading="削除の確認",
            body=f"キー '{key_item.desc}' を本当に削除しますか？",
        )
        dialog.add_response("cancel", "キャンセル")
        dialog.add_response("delete", "削除")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.on_delete_confirm, key_item)
        dialog.present()
        
    def on_delete_confirm(self, dialog, response_id, key_item):
        if response_id == "delete":
            try:
                keyutils.unlink(int(key_item.id), keyutils.KEY_SPEC_USER_KEYRING)
                self._load_keys()
            except (keyutils.Error, ValueError) as e:
                self.show_error_dialog(f"キーの削除に失敗しました: {e}")
        dialog.destroy()
        
    def show_error_dialog(self, message):
        dialog = Adw.MessageDialog(
            transient_for=self, modal=True,
            heading="エラー", body=message,
        )
        dialog.add_response("ok", "OK")
        dialog.present()



class KeyringApplication(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.win = None
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        if self.win:
            self.win.present()
            return

        self.win = KeyringWindow(application=app)
        self.win.connect("destroy", self.on_window_destroy)
        self.win.present()

    def on_window_destroy(self, window):
        self.win = None


if __name__ == "__main__":
    app = KeyringApplication(application_id="dev.gemini.keyring-manager")
    sys.exit(app.run(sys.argv))
