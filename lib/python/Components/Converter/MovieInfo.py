# -*- coding: utf-8 -*-
from os.path import basename, normpath
from Components.Converter.Converter import Converter
from Components.Element import cached, ElementError
from enigma import iServiceInformation, eServiceReference
from ServiceReference import ServiceReference
from Components.UsageConfig import dropEPGNewLines, replaceEPGSeparator
from Components.config import config
from time import localtime, strftime


class MovieInfo(Converter):
	MOVIE_SHORT_DESCRIPTION = 0 # meta description when available.. when not .eit short description
	MOVIE_META_DESCRIPTION = 1 # just meta description when available
	MOVIE_REC_SERVICE_NAME = 2 # name of recording service
	MOVIE_REC_FILESIZE = 3 # filesize of recording
	MOVIE_FULL_DESCRIPTION = 4 # short and exended description
	MOVIE_NAME = 5 # recording name
	FORMAT_STRING = 6 # it is formatted string based on parameter and with defined separator

	def __init__(self, type):
		Converter.__init__(self, type)
		self.parts = type.split(",")
		if len(self.parts) > 1:
			self.type = self.FORMAT_STRING
			self.separator = self.parts[0]
		else:
			if type == "ShortDescription":
				self.type = self.MOVIE_SHORT_DESCRIPTION
			elif type == "MetaDescription":
				self.type = self.MOVIE_META_DESCRIPTION
			elif type == "RecordServiceName":
				self.type = self.MOVIE_REC_SERVICE_NAME
			elif type == "FileSize":
				self.type = self.MOVIE_REC_FILESIZE
			elif type == "FullDescription":
				self.type = self.MOVIE_FULL_DESCRIPTION
			elif type == "Name":
				self.type = self.MOVIE_NAME
			else:
				raise ElementError("'%s' is not <ShortDescription|MetaDescription|RecordServiceName|FileSize|FullDescription|Name> for MovieInfo converter" % type)

	@cached
	def getText(self):
		service = self.source.service
		info = self.source.info
		event = self.source.event
		if info and service:
			isDirectory = bool(service.flags & eServiceReference.flagDirectory)
			if self.type == self.MOVIE_SHORT_DESCRIPTION:
				if isDirectory:
					# Short description for Directory is the full path
					return service.getPath()
				return (info.getInfoString(service, iServiceInformation.sDescription)
					or (event and dropEPGNewLines(event.getShortDescription()))
					or service.getPath())
			elif self.type == self.MOVIE_FULL_DESCRIPTION:
				if isDirectory:
					return ""
				description = (event and dropEPGNewLines(event.getShortDescription())
						or info.getInfoString(service, iServiceInformation.sDescription))
				extended = event and dropEPGNewLines(event.getExtendedDescription().rstrip())
				if description and extended:
					if description.replace('\n', '') == extended.replace('\n', ''):
						return extended
					description += replaceEPGSeparator(config.epg.fulldescription_separator.value)
				return description + (extended if extended else "")
			elif self.type == self.MOVIE_META_DESCRIPTION:
				return ((event and (dropEPGNewLines(event.getExtendedDescription()) or dropEPGNewLines(event.getShortDescription())))
					or info.getInfoString(service, iServiceInformation.sDescription)
					or service.getPath())
			elif self.type == self.MOVIE_NAME:
				if isDirectory:
					return basename(normpath(service.getPath()))
				return event and event.getEventName() or info and info.getName(service)
			elif self.type == self.MOVIE_REC_SERVICE_NAME:
				rec_ref_str = info.getInfoString(service, iServiceInformation.sServiceref)
				return ServiceReference(rec_ref_str).getServiceName()
			elif self.type == self.MOVIE_REC_FILESIZE:
				if isDirectory:
					return _("Directory")
				filesize = info.getInfoObject(service, iServiceInformation.sFileSize)
				if filesize is not None:
					if filesize >= 104857600000: #100000*1024*1024
						return "%.0f %s" % (filesize / 1073741824.0, _("GB"))
					elif filesize >= 1073741824: #1024*1024*1024
						return "%.2f %s" % (filesize / 1073741824.0, _("GB"))
					elif filesize >= 1048576:
						return "%.0f %s" % (filesize / 1048576.0, _("MB"))
					elif filesize >= 1024:
						return "%.0f %s" % (filesize / 1024.0, _("kB"))
					return "%d %s" % (filesize, _("B"))
			elif self.type == self.FORMAT_STRING:
				timeCreate =  strftime("%A %d %b %Y", localtime(info.getInfo(service, iServiceInformation.sTimeCreate)))
				duration = "%d min" % (info.getLength(service) / 60)
				filesize = "%d MB" % (info.getInfoObject(service, iServiceInformation.sFileSize) / (1024*1024))
				res_str = ""
				for x in self.parts[1:]:
					x = x.upper()
					if x == "TIMECREATED" and timeCreate:
						res_str = self.appendToStringWithSeparator(res_str, timeCreate)
					if x == "DURATION" and duration:
						res_str = self.appendToStringWithSeparator(res_str, duration)
					if x == "FILESIZE" and filesize:
						res_str = self.appendToStringWithSeparator(res_str, filesize)
				return res_str
		return ""

	text = property(getText)
