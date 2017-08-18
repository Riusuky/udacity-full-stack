import sys

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy import CheckConstraint

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship, backref

from sqlalchemy import create_engine

# import logging
#
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key = True)
    email = Column(
        String,
        CheckConstraint("email <> ''"),
        index = True,
        unique = True)
    name = Column(
        String,
        CheckConstraint("name <> ''"),
        nullable = False)

    categories = relationship(
        'Category',
        back_populates = 'owner',
        cascade = 'all, delete-orphan')

    items = relationship(
        'Item',
        back_populates = 'owner',
        cascade = 'all, delete-orphan')

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key = True)
    name = Column(
        String(255),
        CheckConstraint("name <> ''"),
        nullable = False)
    owner_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable = False)

    items = relationship(
        'Item',
        back_populates = 'category',
        cascade = 'all, delete-orphan')

    owner = relationship(
        'User',
        back_populates = 'categories')

    def tojson(self):
        return {
            'id': self.id,
            'name': self.name,
            'owner_id': self.owner_id}


# TODO: handle orphan images
class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer, primary_key = True)
    path = Column(String, nullable = False)


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key = True)
    name = Column(String(255), CheckConstraint("name <> ''"), nullable = False)
    description = Column(String)
    category_id = Column(
        Integer,
        ForeignKey('categories.id', ondelete='CASCADE'),
        nullable = False)
    owner_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable = False)
    image_id = Column(Integer, ForeignKey('images.id'), nullable = True)
    created_on = Column(DateTime, default = func.now())

    category = relationship(
        'Category',
        back_populates = 'items')

    image = relationship('Image')

    owner = relationship(
        'User',
        back_populates = 'items')

    def tojson(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'image_id': self.image_id,
            'created_on': self.created_on,
            'owner_id': self.owner_id}


engine = create_engine('postgresql:///udacity_catalog')
Base.metadata.create_all(engine)
