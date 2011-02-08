# -*- coding: utf8 -*-
import os
import unittest

from fixture import DataSet, DataTestCase, SQLAlchemyFixture

from models import create_engine, metadata, session, Photo, Tag
from controller import FSpotController


# Setup temporary database
DB_PATH = ':memory:'
engine = create_engine('sqlite:///' + DB_PATH)
metadata.bind = engine
session.configure(bind=engine)
metadata.create_all()

BASE_PATH=os.path.abspath(os.path.dirname(__file__))

"""
Fixtures
"""
dbfixture = SQLAlchemyFixture(env={'PhotoData': Photo, 'TagData': Tag},
                              engine=metadata.bind)

class PhotoData(DataSet):
    class on_disk:
        base_uri = os.path.join('file://', BASE_PATH, 'tests')
        filename = 'bee.jpg'
    class encoded:
        base_uri = os.path.join('file://', u'éΩƂ', 'spa ce')
        filename = 'file1.jpg'
    class normalized:
        base_uri = os.path.join('file://', '%C3%A9%CE%A9%C6%82', 'spa%20ce')
        filename = 'file2.jpg'
    class file_encoded:
        base_uri = os.path.join('file://', 'Photos', '2011')
        filename = u"file3 éè with spaces.jpg"

"""
Actual tests
"""
class TestPhoto(DataTestCase, unittest.TestCase):
    fixture = dbfixture
    datasets = [PhotoData]
    
    def test_path(self):
        p = Photo(base_uri = "file:///Your%20photos/", filename = "file.jpg")
        self.assertEqual(p.path, '/Your photos/file.jpg')
        p = Photo(base_uri = "file:///Your photos/", filename = "file.jpg")
        self.assertEqual(p.path, '/Your photos/file.jpg')
        p = Photo(base_uri = "file:///Your photos", filename = "file.jpg")
        self.assertEqual(p.path, '/Your photos/file.jpg')

    def test_exists(self):
        p = session.query(Photo).filter_by(filename='bee.jpg').one()
        assert p
        self.assertTrue(p.exists())
        p = Photo(base_uri = "file:///Your%20photos/", filename = "file.jpg")
        self.assertFalse(p.exists())

    def test_corrupted(self):
        p = session.query(Photo).filter_by(filename='bee.jpg').one()
        assert p
        self.assertFalse(p.is_corrupted())
        p = Photo(base_uri = os.path.join('file://', BASE_PATH, 'tests'),
                  filename = 'bee-corrupted.jpg')
        self.assertTrue(p.is_corrupted())

    def test_add_tag(self):
        p = session.query(Photo).filter_by(filename='bee.jpg').one()
        self.assertEqual(p.tags, [])
        p.add_tag('Family')
        self.assertEqual(p.tags, [session.query(Tag).filter_by(name='Family').one()])
        self.assertEqual(p.tagnames, ['Family'])
        p.add_tag('family')
        self.assertEqual(len(p.tags), 1)

    def test_remove_tag(self):
        p = session.query(Photo).filter_by(filename='bee.jpg').one()
        self.assertEqual(p.tagnames, [])
        self.assertRaises(Exception, p.remove_tag, ('Landscape'))
        p.add_tag('Landscape')
        self.assertEqual(p.tagnames, ['Landscape'])
        p.remove_tag('Landscape')
        self.assertEqual(p.tagnames, [])


class TestController(DataTestCase, unittest.TestCase):
    fixture = dbfixture
    datasets = [PhotoData]

    def setUp(self):
        super(TestController, self).setUp()
        self.fm = FSpotController(dbpath=DB_PATH, 
                                  engine=engine,
                                  backup=False)

    def test_normalize(self):
        pass

    def test_find_by_path(self):
        self.fm.normalize = False
        p = self.fm.find_by_path("tests").all()
        self.assertFalse(len(p) > 0)
        p = self.fm.find_by_path("*tests*").all()
        self.assertTrue(len(p) > 0)
        p = self.fm.find_by_path(BASE_PATH+'*').all()
        self.assertTrue(len(p) > 0)
        p = self.fm.find_by_path('*tests/bee*').all()
        self.assertFalse(len(p) > 0)
        p = self.fm.find_by_path('file*').all()
        self.assertEqual(len(p), 3)
        p = self.fm.find_by_path('*file?.jpg').all()
        self.assertEqual(len(p), 2)
        p = self.fm.find_by_path('*spa ce*').all()
        self.assertEqual(len(p), 1)
        p = self.fm.find_by_path(u'*Ω*'.encode('utf-8')).all()
        self.assertEqual(len(p), 1)
        # Now normalize the paths
        self.fm.normalize = True
        p = self.fm.find_by_path('*tests/bee*').all()
        self.assertTrue(len(p) > 0)
        p = self.fm.find_by_path('*spa ce*').all()
        self.assertEqual(len(p), 2)
        p = self.fm.find_by_path(u'*Ω*'.encode('utf-8')).all()
        self.assertEqual(len(p), 2)

    def test_change_rating(self):
        p = session.query(Photo).filter_by(filename='bee.jpg').one()
        assert p
        self.assertEqual(0, p.rating)
        self.fm.change_rating(1)
        self.assertEqual(1, p.rating)
        # Safe
        self.fm.change_rating(0, safe=True)
        self.assertEqual(1, p.rating)
        # Not safe
        self.fm.change_rating(0, safe=False)
        self.assertEqual(0, p.rating)

    def test_find_missing_on_disk(self):
        n = self.fm.photoset.count()
        p = self.fm.find_missing_on_disk().all()
        self.assertEqual(len(p), n - 1)

if __name__ == '__main__':
    unittest.main()
