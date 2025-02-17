# -*- coding: utf-8 -*-

'''
	Bubbles Add-on
	Copyright (C) 2016 Bubbles

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from resources.lib.externals import pyperclip
from resources.lib.extensions import interface

class Clipboard(object):

	@classmethod
	def __message(self, id, value, type = None):
		message = ''
		if not type: type = interface.Translation.string(33035)
		if not id == None: message += (interface.Translation.string(id) % type) + ':' + interface.Format.newline()
		message += interface.Format.italic(interface.Format.split(value))
		return message

	@classmethod
	def copy(self, value, notify = False, type = None):
		if not value:
			return False

		try:
			pyperclip.copy(value)
			id = 33033
		except:
			id = None

		if notify == True:
			title = interface.Translation.string(33032)
			message = self.__message(id = id, value = value, type = type)
			interface.Dialog.confirm(title = title, message = message)
		return True

	@classmethod
	def paste(self, notify = False, type = None):
		value = pyperclip.paste()
		if notify == True:
			title = interface.Translation.string(33032)
			message = self.__message(id = 33034, value = value, type = type)
			interface.Dialog.confirm(title = title, message = message)
		return value

	@classmethod
	def copyLink(self, value, notify = False):
		type = interface.Translation.string(33036)
		return self.copy(value = value, notify = notify, type = type)

	@classmethod
	def pasteLink(self, notify = False):
		type = interface.Translation.string(33036)
		return self.paste(notify = notify, type = type)
