# for localized messages
from os import listdir, path

from . import _
from Components.config import config
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Components.MenuList import MenuList
from Components.SelectionList import SelectionList
from Components.Sources.StaticText import StaticText
from Components.Ipkg import IpkgComponent
from Screens.Screen import Screen
from Screens.Console import Console
from Screens.Ipkg import Ipkg
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop


class VIXIPKInstaller(Screen):
	def __init__(self, session, menu_path=""):
		Screen.__init__(self, session)
		screentitle =  _("IPK Installer")
		if config.usage.show_menupath.value == 'large':
			menu_path += screentitle
			title = menu_path
			self["menu_path_compressed"] = StaticText("")
			menu_path += ' / '
		elif config.usage.show_menupath.value == 'small':
			title = screentitle
			self["menu_path_compressed"] = StaticText(menu_path + " >" if not menu_path.endswith(' / ') else menu_path[:-3] + " >" or "")
			menu_path += " / " + screentitle
		else:
			title = screentitle
			self["menu_path_compressed"] = StaticText("")
		Screen.setTitle(self, title)

		self['lab1'] = Label()
		self.defaultDir = '/tmp'
		self.onChangedEntry = []
		self['myactions'] = ActionMap(['ColorActions', 'OkCancelActions', 'DirectionActions', "MenuActions"],
									  {
									  'cancel': self.close,
									  'red': self.close,
									  'green': self.keyInstall,
									  'yellow': self.changelocation,
									  'ok': self.keyInstall,
									  "menu": self.close,
									  }, -1)

		self["key_red"] = Button(_("Close"))
		self["key_green"] = Button(_("Install"))
		self["key_yellow"] = Button()

		self.list = []
		self['list'] = MenuList(self.list)
		self.populate_List()

		if not self.selectionChanged in self["list"].onSelectionChanged:
			self["list"].onSelectionChanged.append(self.selectionChanged)

	def createSummary(self):
		from Screens.PluginBrowser import PluginBrowserSummary

		return PluginBrowserSummary

	def selectionChanged(self):
		item = self["list"].getCurrent()
		if item:
			name = item
			desc = ""
		else:
			name = ""
			desc = ""
		for cb in self.onChangedEntry:
			cb(name, desc)

	def changelocation(self):
		if self.defaultDir == '/tmp':
			self["key_yellow"].setText(_("Extra IPK's"))
			self.defaultDir = config.backupmanager.xtraplugindir.value
			if not self.defaultDir:
				message = _("It seems you have not setup an extra location, please set it up in the Backup Manager setup menu ")
				ybox = self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
				ybox.setTitle(_("Change Location"))
			elif self.defaultDir and not path.exists(self.defaultDir):
				message = _("Sorry but that location does not exist or is not setup, please set it up in the Backup Manager setup menu ")
				ybox = self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
				ybox.setTitle(_("Change Location"))
			else:
				self.populate_List()
		else:
			self["key_yellow"].setText(_("Temp Folder"))
			self.defaultDir = '/tmp'
			self.populate_List()

	def populate_List(self):
		if self.defaultDir == '/tmp':
			self["key_yellow"].setText(_("Extra IPK's"))
		else:
			self["key_yellow"].setText(_("Temp Folder"))

		self['lab1'].setText(_("Select a package to install:"))

		del self.list[:]
		f = listdir(self.defaultDir)
		for line in f:
			if line.find('.ipk') != -1:
				self.list.append(line)

		if path.ismount('/media/usb'):
			f = listdir('/media/usb')
			for line in f:
				if line.find('.ipk') != -1:
					self.list.append(line)

		self.list.sort()
		self['list'].l.setList(self.list)

	def keyInstall(self):
		message = _("Are you ready to install ?")
		ybox = self.session.openWithCallback(self.Install, MessageBox, message, MessageBox.TYPE_YESNO)
		ybox.setTitle(_("Install Confirmation"))

	def Install(self, answer):
		if answer is True:
			sel = self['list'].getCurrent()
			if sel:
				self.defaultDir = self.defaultDir.replace(' ', '%20')
				cmd1 = "/usr/bin/opkg install " + path.join(self.defaultDir, sel)
				self.session.openWithCallback(self.installFinished(sel), Console, title=_("Installing..."), cmdlist=[cmd1], closeOnSuccess=True)

	def installFinished(self, sel):
		message = _("Do you want to restart GUI now ?")
		ybox = self.session.openWithCallback(self.restBox, MessageBox, message, MessageBox.TYPE_YESNO)
		ybox.setTitle(_("Restart Enigma2."))

	def restBox(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.populate_List()
			self.close()

	def myclose(self):
		self.close()


class IpkgInstaller(Screen):
	def __init__(self, session, list):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("IPK Installer"))
		self.list = SelectionList()
		self["list"] = self.list
		for listindex in range(len(list)):
			if not list[listindex].split('/')[-1].startswith('._'):
				self.list.addSelection(list[listindex].split('/')[-1], list[listindex], listindex, False)

		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Install"))
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText(_("Invert"))
		self["introduction"] = StaticText(_("Press OK to toggle the selection."))

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
									{
									"ok": self.list.toggleSelection,
									"cancel": self.close,
									"red": self.close,
									"green": self.install,
									"blue": self.list.toggleAllSelection
									}, -1)

	def install(self):
		list = self.list.getSelectionsList()
		cmdList = []
		for item in list:
			cmdList.append((IpkgComponent.CMD_INSTALL, {"package": item[1]}))
		self.session.open(Ipkg, cmdList=cmdList)

