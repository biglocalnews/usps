from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import declarative_base

Base: DeclarativeMeta = declarative_base()


class Address(Base):

    __tablename__ = "addresses"

    hash = Column(String)
    number = Column(String)
    street = Column(String)
    unit = Column(String)
    city = Column(String)
    district = Column(String)
    region = Column(String)
    postcode = Column(String)
    id = Column(String)
