import os 
import urllib
import commands
from urlparse import urlparse
from gettext import gettext as _

import pexif

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base, synonym_for
from sqlalchemy.orm import relation, relationship, sessionmaker, column_property

from utils import which


# SQLAlchemy basic wiring
DeclarativeBase = declarative_base()
metadata = DeclarativeBase.metadata
Session = sessionmaker()
session = Session()


class ExifTagError(Exception):
    """Raised when an error occurs while accessing EXIF tags"""
    pass

class MissingBinaryError(Exception):
    """Raised when a binary is not found"""
    pass


class Roll(DeclarativeBase):
    __tablename__ = 'rolls'

    id = Column(Integer, primary_key=True)
    time = Column(BigInteger)

    def __init__(self, **kwargs):
        self.time = kwargs.get('time', 0)


"""Many-to-many association table between Photos and Tags"""
phototags = Table(
    'photo_tags', DeclarativeBase.metadata,
    Column('photo_id', Integer, ForeignKey('photos.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
    )


class Photo(DeclarativeBase):
    __tablename__ = 'photos'
    
    id = Column(Integer, primary_key=True)
    time = Column(BigInteger)
    base_uri = Column(String)
    filename = Column(String)
    description = Column(Text)
    rating = Column(Integer)
    uri = column_property(base_uri + os.sep + filename)
    tags = relationship('Tag', secondary=phototags)
    
    roll_id = Column('roll_id', Integer, ForeignKey('rolls.id'))
    #roll = relationship(Roll, remote_side='id')
    
    default_version_id = None # Foreign to version

    def __init__(self, **kwargs):
        self.time = kwargs.get('time', 0)
        self.base_uri = kwargs.get('base_uri', u'')
        self.filename = kwargs.get('filename', u'')
        self.description = kwargs.get('description', u'')
        self.rating = kwargs.get('rating', 0)

    @staticmethod
    def exif(self, filepath, tagname):
        """Returns EXIF tag value for tagname"""
        img = pexif.JpegFile.fromFile(filepath)
        try:
            value = getattr(img.exif.primary, tagname)
        except ValueError:
            raise ExifTagError(_("EXIF tag '%s' not found"), tagname)

    @property
    def path(self):
        """
        File system path (unquoted and unicode encoded)
        Example:
            file:///photos/2011/11.01.09.Your%20photos/179.jpg
          becomes
            /photos/2011/11.01.09.Your photos/179.jpg
        """
        base_uri = urllib.unquote(self.base_uri)
        base_uri = base_uri.encode('utf-8')
        base_uri = urlparse(base_uri)
        filename = urllib.unquote(self.filename)
        filename = filename.encode('latin-1')
        return os.path.join(base_uri.path, filename)

    def exists(self):
        """Exists on filesystem ?"""
        return os.path.exists(self.path)

    def file_mtime(self):
        """Modification time on disk"""
        return long(os.path.getmtime(self.path))
    
    def exif_mtime(self):
        """Modification time of EXIF"""
        date = self.exif(self.path, 'DateTimeOriginal')
        dt = datetime.strptime(str(date), "%Y:%m:%d %H:%M:%S")
        unix = mktime(dt.timetuple())
        return unix

    def add_tag(self, tagname):
        #TODO: test if already set ?
        self.tags.append(Tag.find_or_create(tagname))

    def is_corrupted(self):
        cmd = 'jpeginfo'
        if not which(cmd):
            raise MissingBinaryError(_("'%s' could not be found") % cmd)
        code, stdout = commands.getstatusoutput('%s -c "%s"' % (cmd, self.path))
        return code == 0 and "[OK]" not in stdout 

    def __unicode__(self):
        return u"<Photo('%s','%s')>" % (self.base_uri, self.filename)


class Tag(DeclarativeBase):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    is_category = Column(Integer)
    sort_priority = Column(Integer)
    icon = Column(Text)
    photos = relationship(Photo, secondary=phototags)

    # http://www.sqlalchemy.org/docs/orm/relationships.html?highlight=adjacency%20list#adjacency-list-relationships
    category_id = Column(Integer, ForeignKey('tags.id'))
    category = relationship('Tag', remote_side=[id])

    def __init__(self, **kwargs):
        self.name  = kwargs.get('name', '')
        self.is_category  = kwargs.get('is_category', 0)
        self.sort_priority = kwargs.get('sort_priority', 0)
        self.icon = kwargs.get('icon', '')

    @staticmethod
    def find_or_create(self, tagname):
        t = Tag.query.filter_by(name=tagname).first()
        if not t:
            t = Tag(tagname)
        return t

    @synonym_for('category')
    @property
    def parent(self):
        return self.category

    def __unicode__(self):
        return "<Tag('%s')>" % (self.name)
