import os
import unittest

from fixture import DataSet, DataTestCase, SQLAlchemyFixture

from models import create_engine, metadata, session, Photo, Tag
from controller import FSpotController


# Setup temporary database
engine = create_engine('sqlite:///:memory')
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


class TestController(DataTestCase, unittest.TestCase):
    fixture = dbfixture
    datasets = [PhotoData]

    def setUp(self):
        super(TestController, self).setUp()
        self.fm = FSpotController(engine=engine)

    def test_find_by_path(self):
        p = self.fm.find_by_path("tests")
        self.assertTrue(len(p) > 0)

    def test_change_rating(self):
        p = session.query(Photo).filter_by(filename='bee.jpg').one()
        assert p
        self.assertEqual(0, p.rating)
        self.fm.change_rating(1)
        self.assertEqual(1, p.rating)
        # Safe
        self.fm.change_rating(0)
        self.assertEqual(1, p.rating)
        # Not safe
        self.fm.change_rating(0, safe=False)
        self.assertEqual(0, p.rating)


if __name__ == '__main__':
    unittest.main()
