import sys
import logging
import shutil
import time
from gettext import gettext as _

from models import create_engine, metadata, session, Photo, Tag


DEFAULT_DB_FILE = os.path.join(os.path.expanduser('~'), '.config', 'f-spot', 'photos.db')

logger = logging.getLogger("__name__")


class NotFoundError(Exception):
    pass


class FSpotController(object):

    def __init__(self, **kwargs):
        self.backup = kwargs.get('backup', True)
        self.dbpath = kwargs.get('dbpath', DEFAULT_DB_FILE)
        
        engine = create_engine('sqlite:///%s' % self.dbpath)
        metadata.bind = engine
        session.configure(bind=engine)

    def create_backup(self):
        if self.backup:
            new = self.dbpath + '~%s' % time.strftime("%Y%m%d%H%M%S")
            shutil.copyfile(self.dbpath, new)
            logger.info(_("Database backup created '%s'") % new)
            # Do it once.
            self.backup = False

    def find_by_tag(self, tag):
        if isinstance(tag, basestring):
            tag = session.query(Tag).filter(Tag.name.like(tag)).first()
        if not tag:
            raise NotFoundError()
        return tag.photos

    def find_by_path(self, path):
        return session.query(Photo).filter(Photo.uri.like("%%%s%%" % path))
    
    def find_missing_on_disk(self):
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

    def change_rating(self):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

