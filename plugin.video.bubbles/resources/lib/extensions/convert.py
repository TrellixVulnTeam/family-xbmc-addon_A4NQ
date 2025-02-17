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

# No Bubbles imports, because it does not work during script execution of downloader.py. Or use relative imports as below.

import re
import math
import time
import datetime

try:
	from resources.lib.externals.pytimeparse import pytimeparse
except:
	# Allow relative imports for donwloader.py which is launched externally.
	import os
	import sys
	sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	from externals.pytimeparse import pytimeparse

class ConverterData(object):

	Unknown = None

	SpeedSymbol = '/s'
	SpeedLetter = 'ps'
	SpeedDefault = SpeedSymbol

	PlacesUnknown = Unknown
	PlacesSingle = 'single'
	PlacesDouble = 'double'
	PlacesTriple = 'triple'

	TypeUnknown = Unknown
	TypeSize = 'size'
	TypeSpeed = 'speed'

	Bit = 'bit'
	BitKilo = 'bitkilo'
	BitMega = 'bitmega'
	BitGiga = 'bitgiga'
	BitTera = 'bittera'
	BitPeta = 'bitpeta'

	Byte = 'byte'
	ByteKilo = 'bytekilo'
	ByteMega = 'bytemega'
	ByteGiga = 'bytegiga'
	ByteTera = 'bytetera'
	BytePeta = 'bytepeta'

	Units = {

		# BIT

		Bit : {
			'unit' : Bit,
			'multiplier' : 8,
			'name' : 'bit',
			'abbreviation' : 'b',
			'labels' : {
				'main' : ['bit', 'bits'],
				'case' : ['b'],
				'other' : ['bi', 'b'],
			},
		},
		BitKilo : {
			'unit' : BitKilo,
			'multiplier' : 0.0078125,
			'name' : 'kilobit',
			'abbreviation' : 'kb',
			'labels' : {
				'main' : ['kilobit', 'kbit', 'kibit', 'kibib', 'bitkilo', 'bitskilo', 'bitki', 'bitski'],
				'case' : ['kb', 'kilob', 'kib'],
				'other' : ['kb', 'kilob'],
			},
		},
		BitMega : {
			'unit' : BitMega,
			'multiplier' : 0.00000762939453125,
			'name' : 'megabit',
			'abbreviation' : 'mb',
			'labels' : {
				'main' : ['megabit', 'mbit', 'mebit', 'mebib', 'bitmega', 'bitsmega', 'bitme', 'bitsme'],
				'case' : ['mb', 'megab', 'mib'],
				'other' : ['mb', 'megab'],
			},
		},
		BitGiga : {
			'unit' : BitGiga,
			'multiplier' : 0.00000000745058059692383,
			'name' : 'gigabit',
			'abbreviation' : 'gb',
			'labels' : {
				'main' : ['gigabit', 'gbit', 'gibit', 'gibib', 'bitgiga', 'bitsgiga', 'bitgi', 'bitsgi'],
				'case' : ['gb', 'gigab', 'gib'],
				'other' : ['gb', 'gigab'],
			},
		},
		BitTera : {
			'unit' : BitTera,
			'multiplier' : 0.0000000000072759576141834,
			'name' : 'terabit',
			'abbreviation' : 'tb',
			'labels' : {
				'main' : ['terabit', 'tbit', 'tebit', 'tebib', 'bittera', 'bitstera', 'bitte', 'bitste'],
				'case' : ['tb', 'terab', 'teb'],
				'other' : ['tb', 'terab'],
			},
		},
		BitPeta : {
			'unit' : BitPeta,
			'multiplier' : 0.000000000000007105427357601,
			'name' : 'petabit',
			'abbreviation' : 'pb',
			'labels' : {
				'main' : ['petabit', 'pbit', 'pebit', 'pebib', 'bitpeta', 'bitspeta', 'bitpe', 'bitspe'],
				'case' : ['pb', 'petab', 'peb'],
				'other' : ['pb', 'petab'],
			},
		},

		# BYTES

		Byte : {
			'unit' : Byte,
			'multiplier' : 1,
			'name' : 'byte',
			'abbreviation' : 'B',
			'labels' : {
				'main' : ['byte', 'bytes'],
				'case' : ['B'],
				'other' : ['by', 'b'],
			},
		},
		ByteKilo : {
			'unit' : ByteKilo,
			'multiplier' : 0.0009765625,
			'name' : 'kilobyte',
			'abbreviation' : 'KB',
			'labels' : {
				'main' : ['kilobyte', 'kbyte', 'kibyte', 'bytekilo', 'byteskilo', 'byteki', 'byteski'],
				'case' : ['KB', 'kiloB', 'KiloB', 'KiB', 'Kib', 'KIB'],
				'other' : ['kb', 'kilob'],
			},
		},
		ByteMega : {
			'unit' : ByteMega,
			'multiplier' : 0.00000095367431640625,
			'name' : 'megabyte',
			'abbreviation' : 'MB',
			'labels' : {
				'main' : ['megabyte', 'mbyte', 'mebyte', 'bytemega', 'bytesmega', 'byteme', 'bytesme'],
				'case' : ['MB', 'megaB', 'MegaB', 'MiB', 'Mib', 'MIB'],
				'other' : ['mb', 'megab'],
			},
		},
		ByteGiga : {
			'unit' : ByteGiga,
			'multiplier' : 0.00000000093132257461548,
			'name' : 'gigabyte',
			'abbreviation' : 'GB',
			'labels' : {
				'main' : ['gigabyte', 'gbyte', 'gibyte', 'bytegiga', 'bytesgiga', 'bytegi', 'bytesgi'],
				'case' : ['GB', 'gigaB', 'GigaB', 'GiB', 'Gib', 'GIB'],
				'other' : ['gb', 'gigab'],
			},
		},
		ByteTera : {
			'unit' : ByteTera,
			'multiplier' : 0.00000000000090949470177293,
			'name' : 'terabyte',
			'abbreviation' : 'TB',
			'labels' : {
				'main' : ['terabyte', 'tbyte', 'tebyte', 'bytetera', 'bytestera', 'bytete', 'byteste'],
				'case' : ['TB', 'teraB', 'TeraB', 'TiB', 'Tib', 'TIB'],
				'other' : ['tb', 'terab'],
			},
		},
		BytePeta : {
			'unit' : BytePeta,
			'multiplier' : 0.00000000000000088817841970013,
			'name' : 'petabyte',
			'abbreviation' : 'PB',
			'labels' : {
				'main' : ['petabyte', 'pbyte', 'pebyte', 'bytepeta', 'bytespeta', 'bytepe', 'bytespe'],
				'case' : ['PB', 'petaB', 'PetaB', 'PiB', 'Pib', 'PIB'],
				'other' : ['pb', 'petab'],
			},
		},
	}

	UnitsBit = [Units[Bit], Units[BitKilo], Units[BitMega], Units[BitGiga], Units[BitTera], Units[BitPeta]]
	UnitsByte = [Units[Byte], Units[ByteKilo], Units[ByteMega], Units[ByteGiga], Units[ByteTera], Units[BytePeta]]
	UnitsAll = UnitsByte + UnitsBit

	# value: string, int, or float.
	def __init__(self, value, unit = Unknown, type = Unknown):
		self.mBytes = self.toBytes(value = value, unit = unit, type = type)
		self.mType = type

	@classmethod
	def _round(self, value, places = 0):
		value = round(value, places)
		if places <= 0:
			value = int(value)
		return value

	# Extracts number from string.
	@classmethod
	def _extractNumber(self, string):
		number = re.search('\d+\.*\d*', str(string))
		if not number == None:
			number = float(number.group(0))
		return number

	# Extracts number and unit from string.
	# labels: main or other
	@classmethod
	def _extractString(self, string, units, labels):
		regex = '\d+\.*\d*[\s,_]*'
		unit = self.Unknown
		value = -1
		stop = False
		for i in range(1, len(units)): # 1: Skip Byte/Nit and test later.
			for label in units[i]['labels'][labels]:
				value = re.search(regex + label, string)
				if not value == None:
					unit = units[i]['unit']
					value = value.group(0)
					stop = True
					break
			if stop:
				break

		if unit == self.Unknown:
			for label in units[0]['labels'][labels]:
				value = re.search(regex + label, string)
				if not value == None:
					unit = units[0]['unit']
					value = value.group(0)
					break

		if not unit == self.Unknown:
			value = self._extractNumber(value)
		try: value = float(value)
		except: value = -1
		return (value, unit)

	# unit: single or list of units. If None, search for all.
	@classmethod
	def extract(self, string, units = Unknown):
		stringLower = string.lower()
		unit = self.Unknown
		value = -1
		if units == self.Unknown:
			value, unit = self._extractString(stringLower, self.UnitsByte, 'main')
			if unit == self.Unknown:
				value, unit = self._extractString(stringLower, self.UnitsBit, 'main')
				if unit == self.Unknown:
					value, unit = self._extractString(string, self.UnitsByte, 'case')
					if unit == self.Unknown:
						value, unit = self._extractString(string, self.UnitsBit, 'case')
						if unit == self.Unknown:
							value, unit = self._extractString(stringLower, self.UnitsByte, 'other')
							if unit == self.Unknown:
								value, unit = self._extractString(stringLower, self.UnitsBit, 'other')
		else:
			if isinstance(units, basestring):
				units = self.Units[units]
			if isinstance(units, dict):
				units = [units]
			value, unit = self._extractString(stringLower, units, 'main')
			if unit == self.Unknown:
				value, unit = self._extractString(string, units, 'case')
				if unit == self.Unknown:
					value, unit = self._extractString(stringLower, units, 'other')

		return (value, unit)

	# value: string, int, or float.
	@classmethod
	def toBytes(self, value, unit = Unknown, type = Unknown):
		if isinstance(value, basestring):
			try:
				value = float(value)
			except:
				value, unit = self.extract(string = value, units = unit)

		if unit == self.Unknown:
			unit = self.Byte

		try: return value / float(self.Units[unit]['multiplier'])
		except: return -1

	@classmethod
	def fromBytes(self, value, unit = Unknown):
		if unit == self.Unknown:
			unit = self.Byte
		return value * float(self.Units[unit]['multiplier'])

	def value(self, unit = Byte, places = PlacesUnknown):
		value = self.fromBytes(self.mBytes, unit)
		if unit == self.Bit or unit == self.Byte:
			places = 0
		if not places == self.PlacesUnknown:
			value = self._round(value, places)
		return value

	def _string(self, unit = Unknown, places = PlacesUnknown, type = Unknown, optimal = False, notation = SpeedDefault):
		value = self.value()
		string = ''
		placesDigits = 0

		if type == self.Unknown:
			type = self.mType

		if unit == self.Unknown:
			unit = self.Byte

		if optimal:
			if self.mBytes >= 0:
				if unit in self.Units:
					unit = self.Units[unit]
				units = self.UnitsBit if unit in self.UnitsBit else self.UnitsByte

				for i in range(1, len(units)):
					if self.mBytes < 1.0 / units[i]['multiplier']:
						unit = units[i - 1]
						break

				unit = unit['unit']

				if isinstance(places, (int, long, float)):
					placesDigits = int(places)
				elif places in [self.PlacesUnknown, self.PlacesSingle, self.PlacesDouble, self.PlacesTriple]:
					placesDigits = 0

					if any(u == unit for u in [self.ByteGiga, self.BitGiga]):
						placesDigits = 1
					elif any(u == unit for u in [self.ByteTera, self.BitTera]):
						placesDigits = 2
					elif any(u == unit for u in [self.BytePeta, self.BitPeta]):
						placesDigits = 3

					if type == self.TypeSpeed:
						if placesDigits > 0:
							placesDigits += 1
						if any(u == unit for u in [self.ByteMega, self.BitMega]):
							placesDigits = 1

					if places == self.PlacesDouble: placesDigits += 1
					elif places == self.PlacesTriple: placesDigits += 2
		try:
			if places in [self.PlacesUnknown, self.PlacesSingle, self.PlacesDouble, self.PlacesTriple] and (unit == self.Byte or unit == self.Bit):
				placesDigits = 0

			value = self.value(unit = unit, places = placesDigits)
			speed = notation if type == self.TypeSpeed else ''
			if places == self.PlacesUnknown:
				string = '%f' % (value)
			else:
				string = '%.*f' % (placesDigits, value)

			# Sometimes float has trailing zeros.
			if places == self.PlacesUnknown:
				string = string.strip('0')
				if string.startswith('.'): string = '0' + string
				if string.endswith('.'):
					if placesDigits > 0: string = string + '0'
					else: string = string[:-1]

			string = '%s %s%s' % (string, self.Units[unit]['abbreviation'], speed)
		except:
			pass
		return string

	def string(self, unit = Unknown, places = PlacesUnknown, type = Unknown, optimal = False, notation = SpeedDefault): # Subclasses overwrite.
		return self._string(unit = unit, places = places, optimal = optimal, type = type, notation = notation)

	def stringSize(self, unit = Unknown, places = PlacesUnknown, optimal = False):
		return self._string(unit = unit, places = places, optimal = optimal, type = self.TypeSize)

	def stringSpeed(self, unit = Unknown, places = PlacesUnknown, optimal = False, notation = SpeedDefault):
		return self._string(unit = unit, places = places, optimal = optimal, type = self.TypeSpeed, notation = notation)

	def stringOptimal(self, unit = Unknown, places = PlacesUnknown, type = Unknown, notation = SpeedDefault):
		return self._string(unit = unit, places = places, optimal = True, type = type, notation = notation)

	def stringSizeOptimal(self, unit = Unknown, places = PlacesUnknown):
		return self.stringSize(unit = unit, places = places, optimal = True)

	def stringSpeedOptimal(self, unit = Unknown, places = PlacesUnknown, notation = SpeedDefault):
		return self.stringSpeed(unit = unit, places = places, optimal = True, notation = notation)

class ConverterSize(ConverterData):

	def __init__(self, value, unit = ConverterData.Unknown):
		ConverterData.__init__(self, value = value, unit = unit, type = ConverterData.TypeSize)

	def string(self, unit = ConverterData.Unknown, places = ConverterData.PlacesUnknown, optimal = False):
		return ConverterData.stringSize(self, unit = unit, places = places, optimal = optimal)

	def stringOptimal(self, unit = ConverterData.Unknown, places = ConverterData.PlacesUnknown):
		return ConverterData.stringSizeOptimal(self, unit = unit, places = places)

class ConverterSpeed(ConverterData):

	def __init__(self, value, unit = ConverterData.Unknown):
		ConverterData.__init__(self, value = value, unit = unit, type = ConverterData.TypeSpeed)

	def string(self, unit = ConverterData.Unknown, places = ConverterData.PlacesUnknown, optimal = False, notation = ConverterData.SpeedDefault):
		return ConverterData.stringSpeed(self, unit = unit, places = places, optimal = optimal, notation = notation)

	def stringOptimal(self, unit = ConverterData.Unknown, places = ConverterData.PlacesUnknown, notation = ConverterData.SpeedDefault):
		return ConverterData.stringSpeedOptimal(self, unit = unit, places = places, notation = notation)

class ConverterDuration(object):

	Unknown = 'unknwon'

	FormatFixed = 'formatfixed' # Fixed according to unit. Eg: 1523 ms or 1.6 hours

	FormatWordMinimal = 'formatwordminimal' # 4 minutes or 1.5 days
	FormatWordShort = 'formatwordshort' # 123 hours, 1 minute, 20 seconds
	FormatWordMedium = 'formatwordmedium' # 256 days, 2 hours, 1 minute, 20 seconds
	FormatWordLong = 'formatwordlong' # 1 year, 2 months, 16 days, 2 hours, 1 minute, 20 seconds

	FormatAbbreviationMinimal = 'formatabbreviationminimal' # 4 mins or 1.5 dys
	FormatAbbreviationShort = 'formatabbreviationshort' # 123 hrs, 1 min, 20 secs
	FormatAbbreviationMedium = 'formatabbreviationmedium' # 256 dys, 2 hrs, 1 min, 20 secs
	FormatAbbreviationLong = 'formatabbreviationlong' # 1 yr, 2 mths, 16 days, 2 hrs, 1 min, 20 secs

	FormatInitialMinimal = 'formatinitialminimal' # 4M or 1.5D
	FormatInitialShort = 'formatinitialshort' # 256H 12M 23S
	FormatInitialMedium = 'formatinitialmedium' # 105D 23H 45M 12S
	FormatInitialLong = 'formatinitiallong' # 1Y 2M 105D 23H 45M 12S

	FormatClockShort = 'formatclockshort' # HH:MM:SS - 256:12:23
	FormatClockMedium = 'formatclockmedium' # DD:HH:MM:SS - 105:23:45:12
	FormatClockLong = 'formatclocklong' # YY:MM:DD:HH:MM:SS - 01:11:28:14:20

	FormatDefault = FormatInitialMedium

	UnitNone = None
	UnitMillisecond = 'millisecond'
	UnitSecond = 'second'
	UnitMinute = 'minute'
	UnitHour = 'hour'
	UnitDay = 'day'
	UnitWeek = 'week'
	UnitMonth = 'month'
	UnitYear = 'year'

	Units = {
		UnitMillisecond : {
			'unit' : UnitMillisecond,
			'name' : {'single' : 'millisecond', 'multiple' : 'milliseconds'},
			'abbreviation' : {'single' : 'msec', 'multiple' : 'msecs'},
			'initial' : 'ms',
			'multiplier' : 1,
			'labels' : ['millisecond', 'ms', 'msec'],
		},
		UnitSecond : {
			'unit' : UnitSecond,
			'name' : {'single' : 'second', 'multiple' : 'seconds'},
			'abbreviation' : {'single' : 'sec', 'multiple' : 'secs'},
			'initial' : 's',
			'multiplier' : 1000,
			'labels' : ['second', 's', 'sec'],
		},
		UnitMinute : {
			'unit' : UnitMinute,
			'name' : {'single' : 'minute', 'multiple' : 'minutes'},
			'abbreviation' : {'single' : 'min', 'multiple' : 'mins'},
			'initial' : 'm',
			'multiplier' : 60000,
			'labels' : ['minute', 'm', 'min'],
		},
		UnitHour : {
			'unit' : UnitHour,
			'name' : {'single' : 'hour', 'multiple' : 'hours'},
			'abbreviation' : {'single' : 'hr', 'multiple' : 'hrs'},
			'initial' : 'h',
			'multiplier' : 3600000,
			'labels' : ['hour', 'h', 'hr'],
		},
		UnitDay : {
			'unit' : UnitDay,
			'name' : {'single' : 'day', 'multiple' : 'days'},
			'abbreviation' : {'single' : 'dy', 'multiple' : 'dys'},
			'initial' : 'd',
			'multiplier' : 86400000,
			'labels' : ['day', 'd', 'dy'],
		},
		UnitWeek : {
			'unit' : UnitWeek,
			'name' : {'single' : 'week', 'multiple' : 'weeks'},
			'abbreviation' : {'single' : 'wk', 'multiple' : 'wks'},
			'initial' : 'w',
			'multiplier' : 604800000,
			'labels' : ['week', 'w', 'wk'],
		},
		UnitMonth : {
			'unit' : UnitMonth,
			'name' : {'single' : 'month', 'multiple' : 'months'},
			'abbreviation' : {'single' : 'mth', 'multiple' : 'mths'},
			'initial' : 'm',
			'multiplier' : 2592000000,
			'labels' : ['month', 'mth', 'mon', 'mn'],
		},
		UnitYear : {
			'unit' : UnitYear,
			'name' : {'single' : 'year', 'multiple' : 'years'},
			'abbreviation' : {'single' : 'yr', 'multiple' : 'yrs'},
			'initial' : 'y',
			'multiplier' : 31536000000,
			'labels' : ['year', 'y', 'yr'],
		},
	}

	def __init__(self, value, unit = ConverterData.Unknown):
		self.mMilliseconds = self.toMilliseconds(value = value, unit = unit)

	@classmethod
	def _round(self, value, places = 0):
		value = round(value, places)
		if places <= 0:
			value = int(value)
		return value

	@classmethod
	def extract(self, string, units = Unknown):
		string = string.lower()
		string = string.replace('and', '')
		string = string.strip(' ').strip('.')
		result = pytimeparse.timeparse(string)
		if not result == None:
			result *= 1000
		else:
			result = 0
		return result

	@classmethod
	def toMilliseconds(self, value, unit = Unknown):
		if value == None:
			return 0
		elif isinstance(value, basestring):
			unit = self.UnitMillisecond
			try:
				value = float(value)
			except:
				value = self.extract(string = value, units = unit)
		elif unit == self.Unknown and isinstance(value, (float, int, long)):
			unit = self.UnitMillisecond

		try: return value * float(self.Units[unit]['multiplier'])
		except: return 0

	@classmethod
	def fromMilliseconds(self, value, unit = Unknown):
		if unit == self.Unknown:
			unit = self.UnitMillisecond
		return value / float(self.Units[unit]['multiplier'])

	def value(self, unit = UnitMillisecond, places = ConverterData.PlacesUnknown):
		value = self.fromMilliseconds(value = self.mMilliseconds, unit = unit)
		if unit == self.UnitMillisecond or unit == self.UnitSecond:
			places = 0
		if not places == ConverterData.PlacesUnknown:
			value = self._round(value, places)
		return value

	def _unit(self, total, unit):
		multiplier = self.Units[unit]['multiplier']
		value = int(math.floor(total / multiplier))
		total -= (value * multiplier)
		return (total, value)

	def _units(self, start = UnitYear):
		years = 0
		months = 0
		days = 0
		hours = 0
		minutes = 0
		seconds = 0
		total = self.mMilliseconds

		if any(unit == start for unit in [self.UnitYear]):
			total, years = self._unit(total, self.UnitYear)
		if any(unit == start for unit in [self.UnitYear, self.UnitMonth]):
			total, months = self._unit(total, self.UnitMonth)
		if any(unit == start for unit in [self.UnitYear, self.UnitMonth, self.UnitDay]):
			total, days = self._unit(total, self.UnitDay)
		if any(unit == start for unit in [self.UnitYear, self.UnitMonth, self.UnitDay, self.UnitHour]):
			total, hours = self._unit(total, self.UnitHour)
		if any(unit == start for unit in [self.UnitYear, self.UnitMonth, self.UnitDay, self.UnitHour, self.UnitMinute]):
			total, minutes = self._unit(total, self.UnitMinute)
		if any(unit == start for unit in [self.UnitYear, self.UnitMonth, self.UnitDay, self.UnitHour, self.UnitMinute, self.UnitSecond]):
			total, seconds = self._unit(total, self.UnitSecond)

		return (years, months, days, hours, minutes, seconds)

	def _unitsMinimal(self):
		values = [0, 0, 0, 0, 0, 0]
		units = [self.UnitYear, self.UnitMonth, self.UnitDay, self.UnitHour, self.UnitMinute, self.UnitSecond]
		for i in range(len(units)):
			value = self.mMilliseconds / float(self.Units[units[i]]['multiplier'])
			if value >= 1:
				values[i] = value
				break
		return (values[0], values[1], values[2], values[3], values[4], values[5])

	def _stringWord(self, value, unit, places = 0):
		word = self.Units[unit]['name']['single'] if unit == 1 else self.Units[unit]['name']['multiple']
		return '%0.*f %s' % (places, value, word)

	def _stringWords(self, years, months, days, hours, minutes, seconds, places = 0):
		units = []
		if years > 0: units.append(self._stringWord(years, self.UnitYear, places = places))
		if months > 0: units.append(self._stringWord(months, self.UnitMonth, places = places))
		if days > 0: units.append(self._stringWord(days, self.UnitDay, places = places))
		if hours > 0: units.append(self._stringWord(hours, self.UnitHour, places = places))
		if minutes > 0: units.append(self._stringWord(minutes, self.UnitMinute, places = places))
		if seconds > 0: units.append(self._stringWord(seconds, self.UnitSecond))
		result = ', '.join(filter(None, units)) # Join if not empty.
		if result == None or result == '':
			result = self._stringWord(0, self.UnitSecond)
		return result

	def _stringAbbreviation(self, value, unit, places = 0):
		abbreviation = self.Units[unit]['abbreviation']['single'] if unit == 1 else self.Units[unit]['abbreviation']['multiple']
		return '%0.*f %s' % (places, value, abbreviation)

	def _stringAbbreviations(self, years, months, days, hours, minutes, seconds, places = 0):
		units = []
		if years > 0: units.append(self._stringAbbreviation(years, self.UnitYear, places = places))
		if months > 0: units.append(self._stringAbbreviation(months, self.UnitMonth, places = places))
		if days > 0: units.append(self._stringAbbreviation(days, self.UnitDay, places = places))
		if hours > 0: units.append(self._stringAbbreviation(hours, self.UnitHour, places = places))
		if minutes > 0: units.append(self._stringAbbreviation(minutes, self.UnitMinute, places = places))
		if seconds > 0: units.append(self._stringAbbreviation(seconds, self.UnitSecond))
		result = ', '.join(filter(None, units)) # Join if not empty.
		if result == None or result == '':
			result = self._stringAbbreviation(0, self.UnitSecond)
		return result

	def _stringInitial(self, value, unit, places = 0):
		initial = self.Units[unit]['initial']
		initial = initial.upper()
		return '%0.*f%s' % (places, value, initial)

	def _stringInitials(self, years, months, days, hours, minutes, seconds, places = 0):
		units = []
		if years > 0: units.append(self._stringInitial(years, self.UnitYear, places = places))
		if months > 0: units.append(self._stringInitial(months, self.UnitMonth, places = places))
		if days > 0: units.append(self._stringInitial(days, self.UnitDay, places = places))
		if hours > 0: units.append(self._stringInitial(hours, self.UnitHour, places = places))
		if minutes > 0: units.append(self._stringInitial(minutes, self.UnitMinute, places = places))
		if seconds > 0: units.append(self._stringInitial(seconds, self.UnitSecond))
		result = ' '.join(filter(None, units)) # Join if not empty.
		if result == None or result == '':
			result = self._stringInitial(0, self.UnitSecond)
		return result

	def _stringClock(self, value):
		return '%02d' % value

	def _stringClocks(self, years, months, days, hours, minutes, seconds):
		units = []
		if years > 0: units.append(self._stringClock(years))
		if months > 0: units.append(self._stringClock(months))
		if days > 0: units.append(self._stringClock(days))
		units.append(self._stringClock(hours))
		units.append(self._stringClock(minutes))
		units.append(self._stringClock(seconds))
		result = ':'.join(filter(None, units)) # Join if not empty.
		if result == None or result == '':
			result = '00:00:00'
		return result

	def _stringFixed(self, unit, places = ConverterData.PlacesUnknown):
		if unit == None: return ''
		value = self.value(unit = unit, places = places)
		return str(value) + ' ' + self.Units[unit]['initial']

	def string(self, format = FormatDefault, unit = UnitNone, places = ConverterData.PlacesUnknown):
		places = 0
		if any(f == format for f in [self.FormatWordMinimal, self.FormatAbbreviationMinimal, self.FormatInitialMinimal]):
			places = 1
			years, months, days, hours, minutes, seconds = self._unitsMinimal()
		else:
			start = self.UnitYear
			if any(f == format for f in [self.FormatWordShort, self.FormatAbbreviationShort, self.FormatInitialShort, self.FormatClockShort]):
				start = self.UnitHour
			elif any(f == format for f in [self.FormatWordMedium, self.FormatAbbreviationMedium, self.FormatInitialMedium, self.FormatClockMedium]):
				start = self.UnitDay
			years, months, days, hours, minutes, seconds = self._units(start = start)

		if any(f == format for f in [self.FormatWordMinimal, self.FormatWordShort, self.FormatWordMedium, self.FormatWordLong]):
			return self._stringWords(years, months, days, hours, minutes, seconds, places = places)
		elif any(f == format for f in [self.FormatAbbreviationMinimal, self.FormatAbbreviationShort, self.FormatAbbreviationMedium, self.FormatAbbreviationLong]):
			return self._stringAbbreviations(years, months, days, hours, minutes, seconds, places = places)
		elif any(f == format for f in [self.FormatInitialMinimal, self.FormatInitialShort, self.FormatInitialMedium, self.FormatInitialLong]):
			return self._stringInitials(years, months, days, hours, minutes, seconds, places = places)
		elif any(f == format for f in [self.FormatClockShort, self.FormatClockMedium, self.FormatClockLong]):
			return self._stringClocks(years, months, days, hours, minutes, seconds)
		elif any(f == format for f in [self.FormatFixed]):
			return self._stringFixed(unit)

class ConverterTime(object):

	Unknown = 'unknwon'

	FormatDate = '%Y-%m-%d'
	FormatDateTime = '%Y-%m-%d %H:%M:%S'
	FormatDateTimeJson = '%Y-%m-%dT%H:%M:%S.%fZ'
	FormatTimestamp = 'timestamp'
	FormatDefault = FormatDateTime

	# value can be timestamp or time string.
	# offset is the difference in number of seconds from UTC. Hence, in France (UTC+1), the offset must be 3600.
	def __init__(self, value, format = None, offset = 0):
		if isinstance(value, basestring):
			if format == None:
				try:
					self.mDatetime = datetime.datetime.strptime(value, self.FormatDateTimeJson)
				except TypeError:
					self.mDatetime = datetime.datetime(*(time.strptime(value, self.FormatDateTimeJson)[0:6]))
				except:
					try: self.mDatetime = datetime.datetime.strptime(value, self.FormatDateTime)
					except TypeError: self.mDatetime = datetime.datetime(*(time.strptime(value, self.FormatDateTime)[0:6]))
			else:
				try: self.mDatetime = datetime.datetime.strptime(value, format)
				except TypeError: self.mDatetime = datetime.datetime(*(time.strptime(value, format)[0:6]))
		else:
			self.mDatetime = datetime.datetime.fromtimestamp(value)

		if not offset == 0:
			offsetLocal = datetime.datetime.now() - datetime.datetime.utcnow() # First adjust the local time to UTC. All datetime are by default in local timezone.
			self.mDatetime = self.mDatetime + offsetLocal + datetime.timedelta(seconds = offset)

		self.mTimestamp = int(time.mktime(self.mDatetime.timetuple()))

	def string(self, format = FormatDefault):
		if format == self.FormatTimestamp:
			return self.mTimestamp
		else:
			return self.mDatetime.strftime(format)

	def timestamp(self):
		return self.mTimestamp
