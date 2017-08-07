import sys

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship, backref

from sqlalchemy import create_engine


Base = declarative_base()


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key = True)
    name = Column(String(255), nullable = False)

    items = relationship(
        'Item',
        back_populates = 'category')


class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer, primary_key = True)
    path = Column(String, nullable = False)


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key = True)
    name = Column(String(255), nullable = False)
    description = Column(String)
    category_id = Column(Integer, ForeignKey('categories.id'))
    image_id = Column(Integer, ForeignKey('images.id'))
    created_on = Column(DateTime, default = func.now())

    category = relationship(
        'Category',
        back_populates = 'items')

    image = relationship('Image')


engine = create_engine('postgresql:///udacity_catalog')
Base.metadata.create_all(engine)
