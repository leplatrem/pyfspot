import os
import sys
import logging
import shutil
import time
from gettext import gettext as _

from models import create_engine, metadata, session, Photo, Tag


DEFAULT_DB_FILE = os.path.join(os.path.expanduser('~'), '.config', 'f-spot', 'photos.db')

logger = logging.getLogger(__name__)


class NotFoundError(Exception):
    def __init__(self, cls, name):
        self.cls = cls
        self.name = name
        super(NotFoundError, self).__init__(self, _("Cannot find %s '%s'") % (cls.__name__, name))


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
        self._normalize = False

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

    def normalize_paths(self):
        if self.normalize:
            queryset = self.photoset.filter(~Photo.base_uri.endswith(os.sep)).all()
            if len(queryset):
                self.create_backup()
                for p in queryset:
                    p.base_uri += os.sep
                session.commit()
                logger.info(_("Normalized path on %s photos.") % len(queryset))
            self.normalize = False

    def find_by_tag(self, tag):
        if isinstance(tag, basestring):
            t = session.query(Tag).filter(Tag.name.like(tag)).first()
        if not t:
            raise NotFoundError(Tag, tag)
        #return t.photos.intersect(self.photoset)
        return self.photoset.filter(Photo.tags.any(id=t.id))

    @normalize()
    def find_by_path(self, path):
        condition = path.replace('*', '%%')
        return self.photoset.filter(Photo.uri.like(condition))

    @backupdb()
    def change_rating(self, rating, safe=True):
        total = 0
        for p in self.photoset:
            if safe and rating < p.rating:
                continue
            p.rating = rating
            total += 1
        logger.info(_("Set rating %s to %s photos.") % (rating, total))
        session.commit()

    def find_missing_on_disk(self):
        raise NotImplementedError

    def find_missing_in_catalog(self):
        raise NotImplementedError

    def find_corrupted(self):
        raise NotImplementedError

    def find_by_time(self):
        raise NotImplementedError

    def find_duplicates(self):
        raise NotImplementedError

    def change_path(self, old, new):
        raise NotImplementedError

    def apply_tag(self):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError


