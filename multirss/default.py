import xml.dom.minidom, urllib, os, os.path, xbmc, xbmcgui, string, traceback, time, re, htmlentitydefs

# script constants
__script__ = "Multirss cf"
__author__ = "CF2009,Affini(multirss 1.5)"
__url__    = "http://github.com/cf2009/multirss/tree/master"
__git_url__ = "git://github.com/cf2009/multirss.git"
__date__    = "31-07-2009"
__version__ = "0.9"

ACTION_EXIT_SCRIPT = ( 9, 10, )

# Current Working Directory
CWD = os.getcwd()
if CWD[-1] == ';': CWD = CWD[0:-1]
if CWD[-1] != '\\': CWD = CWD + '\\'

# RSS elements supported by RSSParser class
channelElements	= ['title','link','description']
itemElements = ['title','link','description','pubDate']

# dialog object for the whole app
dialog = xbmcgui.DialogProgress()

# control id's
CONTROL_CATEGORIES_LIST = 5053
CONTROL_FEED_LIST = 5052
CONTROL_RSSITEM_LIST = 5051
CONTROL_RSSITEM_DESC = 5005
CONTROL_RSSITEM_TITLE = 5004
CONTROL_RSSITEM_DATE = 5003
CONTROL_VERSION_DATE = 5100
CONTROL_BACKGROUND = 5010

class GUI(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs ):
        xbmcgui.WindowXML.__init__( self, *args, **kwargs )
        self.debug = ""
        # RSS parser
        self.parser = RSSParser()

        # Feeds from feedlist file
        self.categories = FeedListLoader("%s\\%s" % (CWD,"feedlist.xml")).getCategoryList()
        self.feeds = None

    def onInit(self):
        self.getControl( CONTROL_VERSION_DATE ).setLabel(__version__ + ' ' + __date__)
        self.updateCategoryList()

    def onAction(self, action):
        if ( action in ACTION_EXIT_SCRIPT ):
            self.exitScript()

    def onControl(self, control):
        pass

    def onClick(self, controlID):
        if(controlID == CONTROL_RSSITEM_LIST):
            pos = self.getControl(CONTROL_RSSITEM_LIST).getSelectedPosition()
            self.updateRSSItemInfo( pos )
        if(controlID == CONTROL_FEED_LIST):
            self.loadFeed()
        if(controlID == CONTROL_CATEGORIES_LIST):
            self.updateFeedList()

    def onFocus(self, controlID):
        pass

    def exitScript( self, restart=False ):
        self.close()

    def updateCategoryList(self):
        for category in self.categories:
            self.getControl( CONTROL_CATEGORIES_LIST ).addItem(category.getName())
        self.setFocus(self.getControl( CONTROL_CATEGORIES_LIST ))
        self.updateFeedList()

    def updateFeedList(self):
        self.getControl(CONTROL_FEED_LIST).reset()
        pos = self.getControl(CONTROL_CATEGORIES_LIST).getSelectedPosition()
        self.feeds = self.categories[pos].getFeeds()
        self.getControl(CONTROL_BACKGROUND).setImage(self.categories[pos].getBackground())
        self.feeds.sort(sort_feeds)
        for feed in self.feeds:
            self.getControl( CONTROL_FEED_LIST ).addItem(feed.getTitle())
        self.setFocus(self.getControl(CONTROL_FEED_LIST))
        self.loadFeed()	

    def loadFeed(self):
        dialog.create("MultiRSS","Loading and parsing RSS data...")
        pos = self.getControl(CONTROL_FEED_LIST).getSelectedPosition()
        self.parser.feed(self.feeds[pos].getLink())
        self.parser.parse()
        self.updateGUIElements()
        dialog.close()

    def updateGUIElements(self):
        self.updateRSSChannelTitle()
        self.updateRSSItemList()
        self.updateRSSItemInfo(0)

    def updateRSSChannelTitle(self):
        title = self.parser.getChannelInfo().getElement("title")
        #self.rssChannelTitle.setLabel(title)
    
    def updateRSSItemList(self):
        self.getControl(CONTROL_RSSITEM_LIST).reset()
        items = self.parser.getItems()
        for item in items:
            self.getControl( CONTROL_RSSITEM_LIST ).addItem(self.remove_extra_spaces(item.getElement("title")))
        self.setFocus(self.getControl( CONTROL_RSSITEM_LIST ))
        
    def updateRSSItemInfo(self, position):
        items = self.parser.getItems()
        if(items[position].hasElement("description")):
            self.description_clen = self.Clean_text(items[position].getElement("description"))
            self.getControl( CONTROL_RSSITEM_DESC ).setText(self.description_clen)
        else:
            self.getControl( CONTROL_RSSITEM_DESC ).setText("This item has no description.")
        self.getControl( CONTROL_RSSITEM_TITLE ).setLabel(self.remove_extra_spaces(items[position].getElement("title")))
        if(items[position].hasElement("pubDate")):
            self.getControl( CONTROL_RSSITEM_DATE ).setLabel(items[position].getElement("pubDate"))

    def Clean_text(self, data):
        data = self.remove_html_tags(data)
        data = htmlentitydecode(data)
        data = self.remove_newline(data)
        #data = self.remove_extra_spaces(data)
        return data

    def remove_extra_spaces(self,data):
        p = re.compile(r'\s+')
        return p.sub(' ', data)

    def remove_newline(self,data):
        return data.strip()

    def remove_html_tags(self,data):
        p = re.compile(r'<[^<]*?/?>')
        return p.sub(' ', data)

def htmlentitydecode(s):
    # code from http://snipplr.com/view.php?codeview&id=15261
    # First convert alpha entities (such as &eacute;)
    # (Inspired from http://mail.python.org/pipermail/python-list/2007-June/443813.html)
    def entity2char(m):
        entity = m.group(1)
        if entity in htmlentitydefs.name2codepoint:
            return unichr(htmlentitydefs.name2codepoint[entity])
        return u" "  # Unknown entity: We replace with a space.
    t = re.sub(u'&(%s);' % u'|'.join(htmlentitydefs.name2codepoint), entity2char, s)
  
    # Then convert numerical entities (such as &#233;)
    t = re.sub(u'&#(\d+);', lambda x: unichr(int(x.group(1))), t)
   
    # Then convert hexa entities (such as &#x00E9;)
    return re.sub(u'&#x(\w+);', lambda x: unichr(int(x.group(1),16)), t)

class RSSChannelInfo:
	def __init__(self, info):
		# dictionary that includes channel elements
		self.info = info
		
	def getElementNames(self):
		return self.info.keys()
		
	def hasElement(self, element):
		return self.info.has_key(element)
	
	def getElement(self, element):
		return self.info[element]
		
class RSSItem:
	def __init__(self, elements):
		# list that includes required item elements
		self.elements = elements
		
	def getElement(self, element):
		return self.elements[element]
		
	def getElementNames(self):
		return self.elements.keys()
		
	def hasElement(self, element):
		return self.elements.has_key(element)
	
class RSSParser:
	def __init__(self):
		# Document Object Model of the XML document
		self.dom = None
		# RSS channel information
		self.channelInfo = None
		# RSS items
		self.items = {}

	# feeds the xml document from given url to the parser
	def feed(self, url):
		self.dom = None
		self.channelInfo = None
		self.items = {}
		f = urllib.urlopen(url)
		xmlDocument = f.read()
		f.close()
		self.dom = xml.dom.minidom.parseString(xmlDocument)

	# parses the RSS document, for now it assumes that RSS document is valid
	def parse(self):
		self.channelInfo = self.__parseChannelInfo()
		self.items = self.__parseItems()

	# parses channel info and returns RSSChannelInfo object containing the info
	def __parseChannelInfo(self):
		channel = self.dom.getElementsByTagName("channel")[0]
		info = {}
		for channelElement in channelElements:
			try:
				info[channelElement] = channel.getElementsByTagName(channelElement)[0].childNodes[0].data
			except IndexError:
				pass
		return RSSChannelInfo(info)

	# parses RSS document items and returns an list containing RSSItem objects
	def __parseItems(self):
		items = self.dom.getElementsByTagName("item")
		itemObjects = []
		for item in items:
			elements = {}
			for itemElement in itemElements:
				try:
					elements[itemElement] = item.getElementsByTagName(itemElement)[0].childNodes[0].data
				except IndexError:
					pass
			itemObjects.append(RSSItem(elements))
		return itemObjects

	# returns the channelinfo on this parser
	def getChannelInfo(self):
		return self.channelInfo

	# returns items from this parser
	def getItems(self):
		return self.items

class RSSCategory:
	def __init__(self, name, feeds, background):
		self.name = name
		self.feeds	= feeds
		self.background	= background

	def getName(self):
		return self.name

	def getFeeds(self):
		return self.feeds

	def getBackground(self):
		return self.background

class RSSFeed:
	def __init__(self, title, link):
		self.title	= title
		self.link = link

	def getTitle(self):
		return self.title

	def getLink(self):
		return self.link

class FeedListLoader:
	def __init__(self, listFile):
		self.listFile = listFile
		self.listXML = None
		self.categoryList = []
		self.loadList()
		self.parseList()

	def loadList(self):
		try:
			f = open(self.listFile)
		except IOError:
			pass
		fl = f.read()
		f.close()
		self.listXML = xml.dom.minidom.parseString(fl)

	def parseList(self):
		categories = self.listXML.getElementsByTagName('category')
		for category in categories:
			feedList = []
			name = category.attributes [ 'name' ].nodeValue
			if(category.hasAttribute('background')):
				background = category.attributes [ 'background' ].nodeValue
			else:
				background = 'background.jpg'
			feeds = category.getElementsByTagName('feed')
			for feed in feeds:
				title = feed.childNodes [ 0 ].nodeValue
				link = feed.attributes [ 'link' ].nodeValue
				feedList.append(RSSFeed(title, link))
			self.categoryList.append(RSSCategory(name, feedList, background))

	def getCategoryList(self):
		return self.categoryList

def sort_feeds(first, second):
	return cmp(first.getTitle(), second.getTitle())

if ( __name__ == "__main__" ):
    ui = GUI( "script-XBMC_MULTIRSS-main.xml", os.getcwd(), "Default" )
    ui.doModal()
    del ui