import os
import sys
import logging
import shutil
import time
import urllib
from gettext import gettext as _

from models import NotFoundError, MissingBinaryError, \
                   create_engine, metadata, session, \
                   Photo, Tag, Meta


DEFAULT_DB_FILE = os.path.join(os.path.expanduser('~'), '.config', 'f-spot', 'photos.db')
DB_VERSION_ENCODED = 18

logger = logging.getLogger(__name__)


def backupdb(*args):
    def wrapper(func):
        def wrapped(self, *args, **kwargs):
            self.create_backup()
            return func(self, *args, **kwargs)
        return wrapped
    return wrapper


def normalize(*args):
    def wrapper(func):
        def wrapped(self, *args, **kwargs):
            self.normalize_paths()
            return func(self, *args, **kwargs)
        return wrapped
    return wrapper


class FSpotController(object):

    def __init__(self, **kwargs):
        self.backup = kwargs.get('backup', True)
        self.normalize = kwargs.get('normalize', True)
        self.dbpath = kwargs.get('dbpath')
        if not self.dbpath:
            self.dbpath = DEFAULT_DB_FILE
        logger.debug(_("Using database file '%s'") % self.dbpath)
        
        engine = kwargs.get('engine')
        if not engine:
            engine = create_engine('sqlite:///%s' % self.dbpath)
            metadata.bind = engine
            session.configure(bind=engine)

        self._photoset = None
        self._db_version = None

    @property
    def photoset(self):
        if not self._photoset:
            return session.query(Photo)
        return self._photoset

    @photoset.setter
    def photoset(self, p):
        self._photoset = p

    def create_backup(self):
        if self.backup:
            new = self.dbpath + '~%s' % time.strftime("%Y%m%d%H%M%S")
            shutil.copyfile(self.dbpath, new)
            logger.info(_("Database backup created '%s'") % new)
            # Do it once.
            self.backup = False

    @property
    def fspot_version(self):
        m = session.query(Meta).filter_by(name="F-Spot Version").one()
        return m.data

    @property
    def db_version(self):
        if not self._db_version:
            m = session.query(Meta).filter_by(name="F-Spot Database Version").one()
            self._db_version = int(m.data)
        return self._db_version

    def normalize_paths(self):
        if self.normalize:
            queryset = self.photoset.filter(~Photo.base_uri.endswith(os.sep)).all()
            if len(queryset):
                self.create_backup()
                for p in queryset:
                    p.base_uri += os.sep
                session.commit()
                logger.info(_("Normalized path separator on %s photos.") % len(queryset))
            
            if self.db_version >= DB_VERSION_ENCODED:
                total = 0
                # Look for photo without '%' in their path (i.e. not encoded)
                queryset = self.photoset.filter(~Photo.base_uri.like('%\\%%', escape="\\")).all()
                if len(queryset):
                    self.create_backup()
                    for p in queryset:
                        # Compare encoded version of base_uri to actual version
                        base_uri_encoded = urllib.quote(p.base_uri[7:].encode('utf-8'))  # (slice file:// part)
                        filename_encoded = urllib.quote(p.filename.encode('utf-8'))
                        if base_uri_encoded != p.base_uri[7:] or \
                           filename_encoded != p.filename:
                            p.filename = filename_encoded
                            p.base_uri = p.base_uri[:7] + base_uri_encoded
                    session.commit()
                    logger.info(_("Normalized path encoding on %s photos.") % total)
            self.normalize = False

    def find_by_tag(self, tag):
        if isinstance(tag, basestring):
            t = session.query(Tag).filter(Tag.name.like(tag)).first()
        if not t:
            raise NotFoundError(Tag, tag)
        return self.photoset.filter(Photo.tags.any(id=t.id))

    @normalize()
    def find_by_path(self, path):
        if self.db_version >= DB_VERSION_ENCODED:
            condition = urllib.quote(path)
            condition = condition.replace('%', "\\%")  # encoding char is not wildchar
            condition = condition.replace('_', "\\_")  # underscore neither
            condition = condition.replace("\\%2A", '%')  # Replace * by %
            condition = condition.replace("\\%3F", '_')  # Replace ? by _
        else:
            condition = path
            condition = condition.replace("*", '%')
            condition = condition.replace("?", '_')
        return self.photoset.filter(Photo.uri.like(condition, escape="\\"))

    @backupdb()
    def change_rating(self, rating, safe=False):
        total = 0
        for p in self.photoset:
            if safe and rating < p.rating:
                continue
            p.rating = rating
            total += 1
        logger.info(_("Set rating %s to %s photos.") % (rating, total))
        session.commit()

    def find_missing_on_disk(self):
        # Cannot use hybrid attributes yet.
        missing = [p.id for p in self.photoset if not p.exists()]
        return self.photoset.filter(Photo.id.in_(missing or [-1]))

    @backupdb()
    def apply_tag(self, tagname):
        total = 0
        for p in self.photoset:
            p.add_tag(tagname)
            total += 1
        logger.info(_("Added tag '%s' on %s photos.") % (tagname, total))

    @backupdb()
    def remove_tag(self, tagname):
        total = 0
        for p in self.photoset:
            try:
                p.remove_tag(tagname)
                total += 1
            except Exception, e:
                logger.error(e)
        logger.info(_("Removed tag '%s' of %s photos.") % (tagname, total))

    def find_missing_in_catalog(self):
        raise NotImplementedError

    def find_corrupted(self):
        try:
            corrupted = [p.id for p in self.photoset if p.is_corrupted()]
        except MissingBinaryError, e:
            corrupted = []
            logger.exception(e)
            logger.info(_("Try installing with: sudo apt-get install %s") % e.cmd)
        return self.photoset.filter(Photo.id.in_(corrupted or [-1]))

    def find_by_time(self):
        raise NotImplementedError

    def find_duplicates(self):
        raise NotImplementedError

    def change_path(self, old, new):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError


