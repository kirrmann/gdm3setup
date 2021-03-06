#! /usr/bin/python2
# -*- coding: utf-8 -*-

import os
import gettext
import dbus
import subprocess
from lxml import etree

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GnomeDesktop
from gi.repository import GObject
from gi.repository import Gio
from gi.repository import GLib

gettext.install("gdm3setup")

GDM_BIN_PATH="/usr/sbin/gdm"

#-----------------------------------------------
class ImageChooserButton(Gtk.Button):
	__gtype_name__ = 'ImageChooserButton'

	def __init__(self):
		Gtk.Button.__init__(self)
		self.Label = Gtk.Label(_('(None)'))
		self.Image = Gtk.Image()
		self.Image.set_from_icon_name("fileopen",Gtk.IconSize.SMALL_TOOLBAR)
		self.Separator = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
		self.Box = Gtk.HBox.new(False,0)
		self.add(self.Box)
		self.Box.pack_start(self.Label,False,False,2)
		self.Box.pack_end(self.Image,False,False,2)
		self.Box.pack_end(self.Separator,False,False,2)
		self.Box.show_all()
		self.filterImage = Gtk.FileFilter()
		self.filterImage.add_pixbuf_formats()
		self.filterImage.set_name(_('Image'))
		self.filterXml = Gtk.FileFilter()
		self.filterXml.add_pattern("*.xml")
		self.filterXml.set_name(_('XML Background'))
		self.filterAll = Gtk.FileFilter()
		self.filterAll.add_pixbuf_formats()
		self.filterAll.add_pattern("*.xml")
		self.filterAll.set_name(_('All'))
		self.PreviewBox = Gtk.VBox.new(False, 16)
		self.PreviewBox.set_size_request(200,-1)
		self.LabelInfo = Gtk.Label("No Image")
		self.PreviewBox.pack_start(self.LabelInfo, False, False, 0)
		self.PreviewImage = Gtk.Image()
		self.PreviewBox.pack_start(self.PreviewImage, False, False, 0)
		self.PreviewImage.show()
		self.Label_Size = Gtk.Label("0 x 0")
		self.PreviewBox.pack_start(self.Label_Size, False, False, 0)
		self.Label_Size.show()
		self.xmlBox = Gtk.HBox.new(False, 16)
		self.PreviewBox.pack_start(self.xmlBox, False, False, 0)
		self.xmlButtonLeft = Gtk.Button.new()
		self.xmlButtonLeftImage = Gtk.Image.new_from_stock("gtk-go-back",Gtk.IconSize.BUTTON)
		self.xmlButtonLeft.set_image(self.xmlButtonLeftImage)
		self.xmlBox.pack_start(self.xmlButtonLeft, False, False, 0)
		self.xmlButtonLeft.show()
		self.xmlLabel = Gtk.Label("0/0")
		self.xmlBox.pack_start(self.xmlLabel, True, True, 0)
		self.xmlLabel.show()
		self.xmlButtonRight = Gtk.Button.new()
		self.xmlButtonRightImage = Gtk.Image.new_from_stock("gtk-go-forward",Gtk.IconSize.BUTTON)
		self.xmlButtonRight.set_image(self.xmlButtonRightImage)
		self.xmlBox.pack_end(self.xmlButtonRight, False, False, 0)
		self.xmlButtonRight.show()
		self.listImage = list()
		self.Filename = ""
		self.isWallpaper = False
		self.connect("clicked",self._Clicked)
		self.xmlButtonLeft.connect("clicked",self.change_pixbuf,-1)
		self.xmlButtonRight.connect("clicked",self.change_pixbuf,1)
		self.FileChooserDialog = None

	def _Clicked(self,e) :
		if self.FileChooserDialog == None :

			self.FileChooserDialog = Gtk.FileChooserDialog(title=_("Select a File"),action=Gtk.FileChooserAction.OPEN,buttons=(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL,Gtk.STOCK_CLEAR,Gtk.ResponseType.NONE,Gtk.STOCK_OPEN,Gtk.ResponseType.ACCEPT))
			self.FileChooserDialog.add_filter(self.filterImage)
			self._update_isWallpaper(True)
			self.FileChooserDialog.set_filename(self.Filename)
			self.FileChooserDialog.set_preview_widget(self.PreviewBox)
			self.FileChooserDialog.set_preview_widget_active(False)
			self.PreviewBox.show_all()
			self.FileChooserDialog.connect("update-preview",self._UpdatePreview)
			self.FileChooserDialog.connect("response",self.response_cb)
			self.FileChooserDialog.connect("destroy",self.dialog_destroy)
			self.FileChooserDialog.set_transient_for(self.get_ancestor(Gtk.Window))
		self.FileChooserDialog.present()

	def response_cb(self,dialog,response) :
		self.FileChooserDialog.hide()
		if response==Gtk.ResponseType.ACCEPT :
			self.Filename = self.FileChooserDialog.get_filename()
			self.Label.set_label(os.path.basename(self.Filename))
			self.emit("file-changed")
		elif response==Gtk.ResponseType.NONE :
			self.Filename = ""
			self.Label.set_label(_("(None)"))
			self.emit("file-changed")

	def dialog_destroy(self,data) :
		self.FileChooserDialog = None

	def get_filename(self):
		return self.Filename

	def set_filename(self,filename=""):
		self.Filename = filename
		if filename != "" :
			self.Label.set_label(os.path.basename(filename))
		else :
			self.Label.set_label(_("(None)"))

	def get_isWallpaper(self):
		return self.isWallpaper

	def set_isWallpaper(self,isWallpaper=False):
		if self.isWallpaper != isWallpaper :
			self.isWallpaper = isWallpaper
			if self.FileChooserDialog :
				self._update_isWallpaper(False)

	def _update_isWallpaper(self,creation) :

		if self.isWallpaper :
			self.FileChooserDialog.add_shortcut_folder('/usr/share/backgrounds')
			self.FileChooserDialog.add_filter(self.filterXml)
			self.FileChooserDialog.add_filter(self.filterAll)
			self.FileChooserDialog.set_filter(self.filterAll)
		elif not creation :
			self.FileChooserDialog.remove_shortcut_folder('/usr/share/backgrounds')
			self.FileChooserDialog.remove_filter(self.filterXml)
			self.FileChooserDialog.remove_filter(self.filterAll)
			self.FileChooserDialog.set_filter(self.filterImage)


	def _UpdatePreview(self,e) :
		PreviewURI = self.FileChooserDialog.get_preview_uri()
		PreviewFile = self.FileChooserDialog.get_preview_file()
		if PreviewURI!=None and PreviewFile !=None :
			if not GLib.file_test(PreviewFile.get_path(),GLib.FileTest.IS_DIR) :
				PreviewFileInfo = PreviewFile.query_info("*",Gio.FileQueryInfoFlags.NONE,None)
				mimetype = PreviewFileInfo.get_content_type();
				name = PreviewFile.get_basename()
				xml = name[len(name)-3:len(name)].lower() == 'xml'
				if not xml :
					mtime = PreviewFileInfo.get_modification_time().tv_sec
					ThumbnailFactory = GnomeDesktop.DesktopThumbnailFactory.new(GnomeDesktop.DesktopThumbnailSize.NORMAL)
					ThumbnailPath = ThumbnailFactory.lookup(PreviewURI,mtime)
					if ThumbnailPath != None :
						pixbuf = GdkPixbuf.Pixbuf.new_from_file(ThumbnailPath)
					else :
						pixbuf = ThumbnailFactory.generate_thumbnail(PreviewURI,mimetype)
						ThumbnailFactory.save_thumbnail(pixbuf,PreviewURI,mtime)
					self.PreviewImage.set_from_pixbuf(pixbuf)
					PreviewWidth = pixbuf.get_option("tEXt::Thumb::Image::Width")
					PreviewHeight = pixbuf.get_option("tEXt::Thumb::Image::Height")
					self.Label_Size.set_label( PreviewWidth + " x " + PreviewHeight)
					self.FileChooserDialog.set_preview_widget_active(True)
					self.LabelInfo.hide()
					self.PreviewImage.show()
					self.Label_Size.show()
					self.xmlBox.hide()

				else :
					xml_file_path = PreviewFile.get_path()
					xml_data = file(xml_file_path,'r').read()
					root = etree.fromstring(xml_data)
					if root.tag == "background" :
						nodeset = root.xpath('/background/static/file')
						for i in range(len(self.listImage)) :
							self.listImage.pop(0)
						if len(nodeset) :
							for i in range(len(nodeset)):
								background_path = nodeset[i].text
								gfile = Gio.File.new_for_path(background_path)
								fileInfo = gfile.query_info("*",Gio.FileQueryInfoFlags.NONE,None)
								mtime = fileInfo.get_modification_time().tv_sec
								mimetype = fileInfo.get_content_type()
								name = fileInfo.get_name()
								uri = gfile.get_uri()
								ThumbnailFactory = GnomeDesktop.DesktopThumbnailFactory.new(GnomeDesktop.DesktopThumbnailSize.NORMAL)
								ThumbnailPath = ThumbnailFactory.lookup(uri,mtime)
								if ThumbnailPath :
									pixbuf = GdkPixbuf.Pixbuf.new_from_file(ThumbnailPath)
								else :
									pixbuf = ThumbnailFactory.generate_thumbnail(uri,mimetype)
									ThumbnailFactory.save_thumbnail(pixbuf,uri,mtime)
								self.listImage.append(pixbuf)
								self.LabelInfo.hide()
								self.PreviewImage.show()
								self.Label_Size.show()
								self.xmlBox.show()
								self.listImageIndex = 0;
								self.change_pixbuf(self,0)
							self.FileChooserDialog.set_preview_widget_active(True)
						else :
							self.LabelInfo.set_text("No Image")
							self.LabelInfo.show()
							self.PreviewImage.hide()
							self.Label_Size.hide()
							self.xmlBox.hide()
							self.FileChooserDialog.set_preview_widget_active(True)
					else :
						self.LabelInfo.set_text("Invalid XML Background")
						self.LabelInfo.show()
						self.PreviewImage.hide()
						self.Label_Size.hide()
						self.xmlBox.hide()
						self.FileChooserDialog.set_preview_widget_active(True)
			else :
				self.FileChooserDialog.set_preview_widget_active(False)
		else :
			self.FileChooserDialog.set_preview_widget_active(False)

	def change_pixbuf(self,e,b) :
		if self.listImageIndex < len(self.listImage)-1 and b==1 :
			self.listImageIndex = self.listImageIndex +1
		if self.listImageIndex > 0 and  b==-1:
			self.listImageIndex = self.listImageIndex -1
		if self.listImageIndex == 0 :
			self.xmlButtonLeft.set_sensitive(False)
		else :
			self.xmlButtonLeft.set_sensitive(True)
		if self.listImageIndex == len(self.listImage)-1 :
			self.xmlButtonRight.set_sensitive(False)
		else :
			self.xmlButtonRight.set_sensitive(True)
		pixbuf = self.listImage[self.listImageIndex]
		self.PreviewImage.set_from_pixbuf(pixbuf)
		PreviewWidth = pixbuf.get_option("tEXt::Thumb::Image::Width")
		PreviewHeight = pixbuf.get_option("tEXt::Thumb::Image::Height")
		self.Label_Size.set_label( PreviewWidth + " x " + PreviewHeight)
		self.xmlLabel.set_text(str(self.listImageIndex+1) + "/" + str(len(self.listImage)))

GObject.signal_new("file-changed", ImageChooserButton, GObject.SIGNAL_RUN_FIRST,GObject.TYPE_NONE, ())
GObject.type_register(ImageChooserButton)

class AutologinButton (Gtk.Button) :
	__gtype_name__ = 'AutologinButton'

	def __init__(self):
		Gtk.Button.__init__(self)
		self.autologin=False
		self.username=""
		self.timed=False
		self.time=30
		self.box=Gtk.HBox.new(False,0)
		self.add(self.box)
		self.box.show()
		self.label_state=Gtk.Label(_("Disabled"))
		self.label_state.set_no_show_all(True)
		self.label_state.show()
		self.box.pack_start(self.label_state,True,True,2)
		self.label_user=Gtk.Label("USER")
		self.label_user.set_no_show_all(True)
		self.box.pack_start(self.label_user,False,False,2)
		self.label_time=Gtk.Label("TIME")
		self.label_time.set_no_show_all(True)
		self.box.pack_end(self.label_time,False,False,2)
		self.Separator = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
		self.Separator.set_no_show_all(True)
		self.box.pack_end(self.Separator,False,False,2)
		self.connect("clicked",self._clicked)
		self.Dialog = None 

	def update(self) :
		if self.autologin :
			self.label_state.hide()
			self.label_user.show()
			if self.timed :
				self.Separator.show()
				self.label_time.show()
			else :
				self.Separator.hide()
				self.label_time.hide()
		else :
			self.label_state.show()
			self.label_user.hide()
			self.Separator.hide()
			self.label_time.hide()
		self.label_user.set_text(self.username)
		self.label_time.set_text(str(self.time) + " s")

	def set_autologin(self,b) :
		self.autologin = b
		self.update()

	def get_autologin(self) :
		return self.autologin

	def set_timed(self,timed):
		self.timed=timed
		self.update()

	def get_timed(self):
		return self.timed

	def set_time(self,time):
		self.time=time
		self.update()

	def get_time(self):
		return self.time

	def set_username(self,username):
		self.username=username
		self.update()

	def get_username(self):
		return self.username

	def _clicked(self,e) :
		if self.Dialog == None :
			self.Dialog = AutoLoginDialog()
			self.Dialog.connect("response",self.response_cb)
			self.Dialog.connect("destroy",self.dialog_destroy)
			self.Dialog.set_transient_for(self.get_ancestor(Gtk.Window))
		self.Dialog.CheckButton_AutoLogin.set_active(self.get_autologin())
		self.Dialog.Entry_username.set_text(self.get_username())
		self.Dialog.CheckButton_Delay.set_active(self.get_timed())
		self.Dialog.SpinButton_Delay.set_value(self.get_time())
		self.Dialog.present()

	def response_cb(self,dialog,response) :
		if response == Gtk.ResponseType.OK :
			if self.Dialog.CheckButton_AutoLogin.get_active() and self.Dialog.Entry_username.get_text()=="" :
				MessageDialog = Gtk.MessageDialog(self.get_toplevel(),Gtk.DialogFlags.DESTROY_WITH_PARENT, 
										Gtk.MessageType.ERROR,
										Gtk.ButtonsType.CLOSE,
										_("User Name can't be empty !"));
				MessageDialog.run()
				MessageDialog.destroy()

			else :
				self.set_autologin(self.Dialog.CheckButton_AutoLogin.get_active())
				self.set_username(self.Dialog.Entry_username.get_text())
				self.set_timed(self.Dialog.CheckButton_Delay.get_active())
				self.set_time(self.Dialog.SpinButton_Delay.get_value_as_int())
				self.Dialog.hide()
				self.emit("changed")
		else :
			self.Dialog.hide()

	def dialog_destroy(self,data) :
		self.Dialog = None

GObject.signal_new("changed", AutologinButton, GObject.SIGNAL_RUN_FIRST,GObject.TYPE_NONE, ())
GObject.type_register(AutologinButton)

class AutoLoginDialog(Gtk.Dialog):
	def __init__(self):
		Gtk.Dialog.__init__(self)
		self.set_resizable(False)
		self.set_title(_("GDM AutoLogin Setup"))
		self.add_button(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL)
		self.add_button(Gtk.STOCK_OK,Gtk.ResponseType.OK)
		self.content_area = self.get_content_area()
		self.Box = Gtk.Box.new(Gtk.Orientation.VERTICAL,8)
		self.Box.set_border_width(8)
		self.content_area.add(self.Box)

		self.CheckButton_AutoLogin = Gtk.CheckButton(label=_("Enable Automatic Login"),use_underline=True)
		self.CheckButton_AutoLogin.connect("toggled",self.AutoLogin_toggled)
		self.Box.pack_start(self.CheckButton_AutoLogin, False, False, 0)

		self.HBox_username = Gtk.HBox.new(False, 0)
		self.HBox_username.set_sensitive(False)
		self.Box.pack_start(self.HBox_username, False, False, 0)

		self.Label_username = Gtk.Label(_("User Name"))
		self.Label_username.set_alignment(0,0.5)
		self.HBox_username.pack_start(self.Label_username, False, False, 0)

		self.Entry_username =  Gtk.Entry()
		self.HBox_username.pack_end(self.Entry_username, False, False, 0)

		self.HBox_Delay = Gtk.HBox.new(False, 8)
		self.HBox_Delay.set_sensitive(False)
		self.Box.pack_start(self.HBox_Delay, False, False, 0)

		self.CheckButton_Delay = Gtk.CheckButton(label=_("Enable Delay before autologin"),use_underline=True)
		self.CheckButton_Delay.connect("toggled",self.Delay_toggled)
		self.HBox_Delay.pack_start(self.CheckButton_Delay, False, False, 0)

		self.SpinButton_Delay = Gtk.SpinButton.new_with_range(1,60,1)
		self.SpinButton_Delay.set_value(10)
		self.SpinButton_Delay.set_sensitive(False)
		self.HBox_Delay.pack_end(self.SpinButton_Delay, False, False, 0)

		self.show_all()

	def AutoLogin_toggled(self,e):
		if self.CheckButton_AutoLogin.get_active():
			self.HBox_username.set_sensitive(True)
			self.HBox_Delay.set_sensitive(True)
		else:
			self.HBox_username.set_sensitive(False)
			self.HBox_Delay.set_sensitive(False)

	def Delay_toggled(self,e):
		if self.CheckButton_Delay.get_active():
			self.SpinButton_Delay.set_sensitive(True)
		else:
			self.SpinButton_Delay.set_sensitive(False)

class EditButton(Gtk.HBox) :
	__gtype_name__ = 'EditButton'

	def __init__(self):
		Gtk.HBox.__init__(self)
		self.Button = Gtk.Button('text')
		self.Button.connect("clicked",self.set_state_active)
		self.add(self.Button)
		self.Button.show()
		self.Entry = Gtk.Entry()
		self.Entry.connect("key-press-event",self.key_press)
		self.Entry.connect("button-press-event",self.button_press)
		self.Entry.connect("focus-in-event",self.focus_in)
		self.focus_out_event = None
		self.update_size()

	def update_size(self):
		entry_preferred_width = self.Entry.get_preferred_width()[0]
		entry_preferred_height = self.Entry.get_preferred_height()[0]
		button_preferred_width = self.Button.get_preferred_width()[0]
		if entry_preferred_width >= button_preferred_width :
			preferred_width = entry_preferred_width
		else :
			preferred_width = button_preferred_width
		self.set_size_request(preferred_width,entry_preferred_height)

	def set_state_active(self,w):
		self.Entry.set_text(self.Button.get_label())
		self.remove(self.Button)
		self.add(self.Entry)
		self.Entry.show()
		self.Entry.grab_focus()

	def set_state_inactive(self):
		self.Entry.disconnect(self.focus_out_event)
		self.remove(self.Entry)
		self.add(self.Button)

	def key_press(self,w,e):
		k = Gdk.keyval_name(e.keyval)
		if k == "Return" or k == "KP_Enter" :
			self.Button.set_label(self.Entry.get_text())
			self.set_state_inactive()
			self.Button.grab_focus()
			self.update_size()
			self.emit("changed")
		if k == "Escape" :
			self.set_state_inactive()
			self.Button.grab_focus()

	def button_press(self,w,e):
		b = e.button
		if b == 3:
			self.Entry.disconnect(self.focus_out_event)

	def focus_out(self,w,e):
		self.set_state_inactive()

	def focus_in(self,w,e):
		self.focus_out_event = self.Entry.connect("focus-out-event",self.focus_out)

	def get_text(self):
		return self.Button.get_label()

	def set_text(self,text):
		self.Button.set_label(text)
		self.update_size()

GObject.signal_new("changed", EditButton, GObject.SIGNAL_RUN_FIRST,GObject.TYPE_NONE, ())

class MainWindow(Gtk.Window) :
	def __init__(self) :
		Gtk.Window.__init__(self)
		self.connect("destroy",self._close)
		self.set_border_width(10)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.set_resizable(False)
		self.set_title(_("GDM3 Setup"))
		self.set_icon_name("preferences-desktop-theme")

		self.Builder = Gtk.Builder()
		self.Builder.set_translation_domain("gdm3setup")
		self.Builder.add_from_file("/usr/share/gdm3setup/ui/gdm3setup.ui")
		self.Box_Main = self.Builder.get_object("box_main")
		self.add(self.Box_Main)

		self.Button_font = self.Builder.get_object("Button_font")
		self.Button_wallpaper = self.Builder.get_object("Button_wallpaper")
		self.ComboBox_shell = self.Builder.get_object("ComboBox_shell")
		self.ComboBox_icon = self.Builder.get_object("ComboBox_icon")
		self.ComboBox_cursor = self.Builder.get_object("ComboBox_cursor")
		self.Entry_logo_icon = self.Builder.get_object("Entry_logo_icon")
		self.Button_fallback_logo = self.Builder.get_object("Button_fallback_logo")
		self.Button_shell_logo = self.Builder.get_object("Button_shell_logo")
		self.ComboBox_gtk = self.Builder.get_object("ComboBox_gtk")
		self.CheckButton_banner = self.Builder.get_object("CheckButton_banner")
		self.Entry_banner_text = self.Builder.get_object("Entry_banner_text")
		self.CheckButton_user = self.Builder.get_object("CheckButton_user")
		self.CheckButton_restart = self.Builder.get_object("CheckButton_restart")
		self.Button_autologin = self.Builder.get_object("Button_autologin")
		self.Switch_clock_date = self.Builder.get_object("Switch_clock_date")
		self.Switch_clock_seconds = self.Builder.get_object("Switch_clock_seconds")
		self.Button_wallpaper.set_isWallpaper(True)

		proxy = dbus.SystemBus().get_object('apps.nano77.gdm3setup','/apps/nano77/gdm3setup')
		self.SetUI = proxy.get_dbus_method('SetUI','apps.nano77.gdm3setup')
		self.GetUI = proxy.get_dbus_method('GetUI','apps.nano77.gdm3setup')
		self.SetAutoLogin = proxy.get_dbus_method('SetAutoLogin','apps.nano77.gdm3setup')
		self.GetAutoLogin = proxy.get_dbus_method('GetAutoLogin','apps.nano77.gdm3setup')
		self.StopDaemon = proxy.get_dbus_method('StopDaemon', 'apps.nano77.gdm3setup')

		self.load_gtk3_list()
		self.load_shell_list()
		self.load_icon_list()
		self.get_gdm()
		self.get_autologin()

		self.Button_font.connect("font-set",self.font_set)
		self.Button_wallpaper.connect("file-changed",self.wallpaper_filechanged)
		self.ComboBox_shell.connect("changed",self.shell_theme_changed)
		self.ComboBox_icon.connect("changed",self.icon_theme_changed)
		self.ComboBox_cursor.connect("changed",self.cursor_theme_changed)
		self.Entry_logo_icon.connect("changed",self.logo_icon_changed)
		self.Button_fallback_logo.connect("file-changed",self.fallback_logo_filechanged)
		self.Button_shell_logo.connect("file-changed",self.shell_logo_filechanged)
		self.ComboBox_gtk.connect("changed",self.gtk3_theme_changed)
		self.CheckButton_banner.connect("toggled",self.banner_toggled)
		self.Entry_banner_text.connect("changed",self.banner_text_changed)
		self.CheckButton_user.connect("toggled",self.user_list_toggled)
		self.CheckButton_restart.connect("toggled",self.menu_btn_toggled)
		self.Button_autologin.connect("changed",self.autologin_changed)
		self.Switch_clock_date.connect("notify::active",self.clock_date_toggled)
		self.Switch_clock_seconds.connect("notify::active",self.clock_seconds_toggled)
		self.AdaptVersion()

		#https://bugzilla.gnome.org/show_bug.cgi?id=653579
		self.ComboBox_icon.set_entry_text_column(0)
		self.ComboBox_icon.set_id_column(1)
		self.ComboBox_cursor.set_entry_text_column(0)
		self.ComboBox_cursor.set_id_column(1)
		self.ComboBox_shell.set_entry_text_column(0)
		self.ComboBox_shell.set_id_column(1)
		self.ComboBox_gtk.set_entry_text_column(0)
		self.ComboBox_gtk.set_id_column(1)

	def load_gtk3_list(self):
		lst_gtk_themes = os.listdir('/usr/share/themes')
		for i in range(len(lst_gtk_themes)) :
			if os.path.isdir('/usr/share/themes/'+lst_gtk_themes[i]+'/gtk-3.0') :
				self.ComboBox_gtk.append_text(lst_gtk_themes[i])

	def load_shell_list(self):

		lst_shell_themes = os.listdir('/usr/share/themes')
		self.ComboBox_shell.append_text("Adwaita")

		for i in range(len(lst_shell_themes)):
			if os.path.isdir('/usr/share/themes/'+lst_shell_themes[i]+'/gnome-shell') :
				if os.path.isfile('/usr/share/themes/'+lst_shell_themes[i]+'/gnome-shell/gdm.css') :
					self.ComboBox_shell.append_text(lst_shell_themes[i])

	def load_icon_list(self):
		lst_icons = os.listdir('/usr/share/icons')

		for i in range(len(lst_icons)):
			if os.path.isdir('/usr/share/icons/'+lst_icons[i]+'/') :
				if 	os.path.isdir('/usr/share/icons/'+lst_icons[i]+'/cursors/') :
					self.ComboBox_cursor.append_text(lst_icons[i])
				else :
					self.ComboBox_icon.append_text(lst_icons[i])

	def _close(self,e):
		try :
			self.StopDaemon()
		except dbus.exceptions.DBusException :
			pass
		Gtk.main_quit()

	def set_gdm(self,name,value):
		if self.SetUI(name,value)=="OK" :
			return True
		else :
			return False

	def get_gdm(self):
		settings = list(self.GetUI())
		self.GTK3_THEME = get_setting("GTK",settings)
		self.SHELL_THEME = get_setting("SHELL",settings)
		self.ICON_THEME = get_setting("ICON",settings)
		self.CURSOR_THEME = get_setting("CURSOR",settings)
		BKG = get_setting("WALLPAPER",settings)
		self.WALLPAPER = BKG[8:len(BKG)-1]
		self.LOGO_ICON = get_setting("LOGO_ICON",settings)
		self.FALLBACK_LOGO = unquote(get_setting("FALLBACK_LOGO",settings))
		self.SHELL_LOGO = unquote(get_setting("SHELL_LOGO",settings))
		self.USER_LIST = str_to_bool(get_setting("USER_LIST",settings))
		self.MENU_BTN = str_to_bool( get_setting("BTN" ,settings))
		self.BANNER = str_to_bool(get_setting("BANNER",settings))
		self.BANNER_TEXT = unquote(get_setting("BANNER_TEXT",settings))
		self.FONT_NAME = unquote(get_setting("FONT",settings))
		self.CLOCK_DATE = str_to_bool(get_setting("CLOCK_DATE",settings))
		self.CLOCK_SECONDS = str_to_bool(get_setting("CLOCK_SECONDS",settings))
		self.ComboBox_gtk.set_active_iter(get_iter(self.ComboBox_gtk.get_model(),self.GTK3_THEME))
		self.ComboBox_shell.set_active_iter(get_iter(self.ComboBox_shell.get_model(),self.SHELL_THEME))
		self.Button_wallpaper.set_filename(self.WALLPAPER) 
		self.ComboBox_icon.set_active_iter(get_iter(self.ComboBox_icon.get_model(),self.ICON_THEME))
		self.ComboBox_cursor.set_active_iter(get_iter(self.ComboBox_cursor.get_model(),self.CURSOR_THEME))
		self.Entry_logo_icon.set_text(self.LOGO_ICON)
		self.Button_fallback_logo.set_filename(self.FALLBACK_LOGO)
		self.Button_shell_logo.set_filename(self.SHELL_LOGO)
		self.CheckButton_banner.set_active(self.BANNER)
		self.Entry_banner_text.set_text(self.BANNER_TEXT)
		self.CheckButton_user.set_active(self.USER_LIST)
		self.CheckButton_restart.set_active(self.MENU_BTN)
		self.Entry_banner_text.set_sensitive(self.BANNER)
		self.Button_font.set_font_name(self.FONT_NAME)
		self.Switch_clock_date.set_active(self.CLOCK_DATE)
		self.Switch_clock_seconds.set_active(self.CLOCK_SECONDS)

	def set_autologin(self,autologin,username,timed,time):
		if self.SetAutoLogin(autologin,username,timed,time)=="OK" :
			return True
		else :
			return False

	def get_autologin(self):
		AUTOLOGIN,USERNAME,TIMED,TIMED_TIME = self.GetAutoLogin()
		self.AUTOLOGIN_ENABLED = str_to_bool(AUTOLOGIN)
		self.AUTOLOGIN_USERNAME = USERNAME
		self.AUTOLOGIN_TIMED = str_to_bool(TIMED)
		self.AUTOLOGIN_TIME = int(TIMED_TIME)
		self.Button_autologin.set_autologin(self.AUTOLOGIN_ENABLED) 
		self.Button_autologin.set_username(self.AUTOLOGIN_USERNAME)
		self.Button_autologin.set_timed(self.AUTOLOGIN_TIMED) 
		self.Button_autologin.set_time(self.AUTOLOGIN_TIME)

	def AdaptVersion(self) :
		p = subprocess.Popen(GDM_BIN_PATH+" --version",stdout=subprocess.PIPE, shell=True)
		GdmSubVersion =  int(p.stdout.read().split(" ")[1].split(".")[1])
		GSexists = os.path.exists("/usr/bin/gnome-shell")

		if GdmSubVersion >= 3 :
			self.Entry_logo_icon.hide()
			self.Builder.get_object("Label_logo_icon").hide()
			self.Button_fallback_logo.show()
			self.Builder.get_object("Label_fallback_logo").show()
		else :
			self.Entry_logo_icon.show()
			self.Builder.get_object("Label_logo_icon").show()
			self.Button_fallback_logo.hide()
			self.Builder.get_object("Label_fallback_logo").hide()
		if not GSexists or GdmSubVersion == 0:
			self.Builder.get_object("notebook1").remove_page(1)

	def gtk3_theme_changed(self,e):
		gtk_theme = unicode(self.ComboBox_gtk.get_active_text(),'UTF_8')
		if gtk_theme!=unquote(self.GTK3_THEME) :
			if self.set_gdm('GTK_THEME',gtk_theme) :
				self.GTK3_THEME = gtk_theme
				print("GTK3 Theme Changed : " + self.GTK3_THEME)
			else :
				self.ComboBox_gtk.set_active_iter(get_iter(self.ComboBox_gtk.get_model(),self.GTK3_THEME))

	def shell_theme_changed(self,e):
		shell_theme = unicode(self.ComboBox_shell.get_active_text(),'UTF_8')
		if shell_theme!=unquote(self.SHELL_THEME) :
			if self.set_gdm('SHELL_THEME',shell_theme) :
				self.SHELL_THEME = shell_theme
				print("SHELL Theme Changed : " + self.SHELL_THEME)
			else :
				self.ComboBox_shell.set_active_iter(get_iter(self.ComboBox_shell.get_model(),self.SHELL_THEME))

	def font_set(self,e):
		font_name = self.Button_font.get_font_name()
		if self.FONT_NAME != font_name : 
			if self.set_gdm('FONT',font_name) :
				self.FONT_NAME = font_name
				print("Font Changed : " + self.FONT_NAME)
			else :
				self.Button_font.set_font_name(self.FONT_NAME)

	def wallpaper_filechanged(self,e):
		wallpaper = unicode(self.Button_wallpaper.get_filename(),'UTF_8')
		if self.WALLPAPER != wallpaper :
			if self.set_gdm('WALLPAPER',wallpaper) :
				self.WALLPAPER = wallpaper 
				print("Wallpaper Changed : " + self.WALLPAPER)
			else :
				self.Button_wallpaper.set_filename(self.WALLPAPER)

	def icon_theme_changed(self,e):
		icon_theme = unicode(self.ComboBox_icon.get_active_text(),'UTF_8')
		if unquote(self.ICON_THEME) != icon_theme:
			if self.set_gdm('ICON_THEME',icon_theme) :
				self.ICON_THEME = icon_theme
				print ("Icon Theme Changed : " + self.ICON_THEME)
			else :
				self.ComboBox_icon.set_active_iter(get_iter(self.ComboBox_icon.get_model(),self.ICON_THEME))

	def cursor_theme_changed(self,e):
		cursor_theme = unicode(self.ComboBox_cursor.get_active_text(),'UTF_8')
		if unquote(self.CURSOR_THEME) != cursor_theme:
			if self.set_gdm('CURSOR_THEME',cursor_theme) :
				self.CURSOR_THEME = cursor_theme
				print ("Cursor Theme Changed : " + self.CURSOR_THEME)
			else :
				self.ComboBox_cursor.set_active_iter(get_iter(self.ComboBox_cursor.get_model(),self.CURSOR_THEME))

	def logo_icon_changed(self,e):
		logo_icon = unicode(self.Entry_logo_icon.get_text(),'UTF_8')
		if self.LOGO_ICON != logo_icon :
			if self.set_gdm('LOGO_ICON',logo_icon) :
				self.LOGO_ICON = logo_icon
				print ("Logo Icon Changed : " + self.LOGO_ICON)
			else:
				self.Entry_logo_icon.set_text(self.LOGO_ICON)

	def fallback_logo_filechanged(self,e):
		fallback_logo = unicode(self.Button_fallback_logo.get_filename(),'UTF_8')
		if self.FALLBACK_LOGO != fallback_logo :
			if self.set_gdm('FALLBACK_LOGO',fallback_logo) :
				self.FALLBACK_LOGO = fallback_logo
				print ("Fallback Logo Changed : " + self.FALLBACK_LOGO)
			else:
				self.Button_fallback_logo.set_filename(self.FALLBACK_LOGO)

	def shell_logo_filechanged(self,e):
		shell_logo = unicode(self.Button_shell_logo.get_filename(),'UTF_8')
		if self.SHELL_LOGO != shell_logo :
			if self.set_gdm('SHELL_LOGO',shell_logo) :
				self.SHELL_LOGO = shell_logo
				print ("Shell Logo Changed : " + self.SHELL_LOGO)
			else:
				self.Button_shell_logo.set_filename(self.SHELL_LOGO)

	def banner_toggled(self,e):
		banner = self.CheckButton_banner.get_active()
		if banner!=self.BANNER :
			if self.set_gdm('BANNER',str(banner).lower()) :
				self.BANNER = banner
				print ("Banner Changed : " + str(self.BANNER))
				if self.BANNER :
					self.Entry_banner_text.set_sensitive(True)
				else:
					self.Entry_banner_text.set_sensitive(False)
			else:
				self.CheckButton_banner.set_active(self.BANNER)

	def banner_text_changed(self,e):
		banner_text = unicode(self.Entry_banner_text.get_text(),'UTF_8')
		if banner_text!=self.BANNER_TEXT :
			if self.set_gdm('BANNER_TEXT',banner_text) :
				self.BANNER_TEXT = banner_text
				print ("Banner Text Changed : " + self.BANNER_TEXT)
			else :
				self.Entry_banner_text.set_text(self.BANNER_TEXT)

	def user_list_toggled(self,e):
		user_list = self.CheckButton_user.get_active()
		if self.USER_LIST != user_list :
			if self.set_gdm('USER_LIST',str(user_list).lower()) :
				self.USER_LIST = user_list
				print ("User List Changed : " + str(self.USER_LIST))
			else:
				self.CheckButton_user.set_active(self.USER_LIST)

	def menu_btn_toggled(self,e):
		menu_btn = self.CheckButton_restart.get_active()
		if self.MENU_BTN != menu_btn :
			if self.set_gdm('MENU_BTN',str(menu_btn).lower()) :
				self.MENU_BTN = menu_btn
				print ("Menu Btn Changed : " + str(self.MENU_BTN))
			else:
				self.CheckButton_restart.set_active(self.MENU_BTN)

	def autologin_changed(self,e) :
		autologin_enabled = self.Button_autologin.get_autologin()
		autologin_username = self.Button_autologin.get_username()
		autologin_timed = self.Button_autologin.get_timed()
		autologin_time = self.Button_autologin.get_time()
		if self.set_autologin(autologin_enabled,autologin_username,autologin_timed,autologin_time) :
			print("Autologin Changed : " + autologin_username)
			self.AUTOLOGIN_ENABLED = autologin_enabled
			self.AUTOLOGIN_USERNAME = autologin_username
			self.AUTOLOGIN_TIMED = autologin_timed
			self.AUTOLOGIN_TIME = autologin_time
		else :
			self.Button_autologin.set_autologin(self.AUTOLOGIN_ENABLED)
			self.Button_autologin.set_username(self.AUTOLOGIN_USERNAME)
			self.Button_autologin.set_timed(self.AUTOLOGIN_TIMED)
			self.Button_autologin.set_time(self.AUTOLOGIN_TIME)

	def clock_date_toggled(self,e,state) :
		clock_date = self.Switch_clock_date.get_active()
		if self.CLOCK_DATE != clock_date :
			if self.set_gdm('CLOCK_DATE',str(clock_date).lower()) :
				self.CLOCK_DATE = clock_date
				print ("Clock Date toggled : " + str(self.CLOCK_DATE))
			else:
				self.Switch_clock_date.set_active(self.CLOCK_DATE)

	def clock_seconds_toggled(self,e,state) :
		clock_seconds = self.Switch_clock_seconds.get_active()
		if self.CLOCK_SECONDS != clock_seconds :
			if self.set_gdm('CLOCK_SECONDS',str(clock_seconds).lower()) :
				self.CLOCK_SECONDS = clock_seconds
				print ("Clock Seconds toggled : " + str(self.CLOCK_SECONDS))
			else:
				self.Switch_clock_seconds.set_active(self.CLOCK_SECONDS)

#-----------------------------------------------

def get_setting(name,data):
	for line in data:
		line = unicode(line)
		if line[0:len(name)+1]==name+"=":
			value = line[len(name)+1:len(line)].strip()
			break
	return value

def unquote(value):
	if value[0:1] == "'"  and value[len(value)-1:len(value)] == "'" :
		value = value[1:len(value)-1]
	return value

def str_to_bool(state) :
	if state.capitalize()=="True" :
		b_state = True
	else :
		b_state = False

	return b_state

def get_iter(model,target):
	target_iter = None
	iter_test = model.get_iter_first()
	while iter_test!=None:
		name = model.get_value(iter_test,0)
		if "'"+name+"'" == target:
			target_iter = iter_test
			break 
		iter_test = model.iter_next(iter_test)
	return target_iter

#-----------------------------------------------

MainWindow().show()

Gtk.main()
