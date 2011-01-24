import os
import unittest

from fixture import DataSet, DataTestCase, SQLAlchemyFixture

from models import create_engine, metadata, session, Photo, Tag


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

if __name__ == '__main__':
    unittest.main()
