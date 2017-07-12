from sqlalchemy import Column, ForeignKey, Integer, String, func, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    created_by = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    created_on = Column(DateTime, default=func.now())
    items = relationship("Item", cascade="all, delete-orphan")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        item_data = [item.serialize for item in self.items]
        return {
            'name': self.name,
            'category_id': self.id,
            'items': item_data,
            'created_by': self.user.name,
            'created_on': str(self.created_on),
        }


class Item(Base):
    __tablename__ = 'item'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(length=1000, convert_unicode=True))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    created_by = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    created_on = Column(DateTime, default=func.now())

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'item_id': self.id,
            'category': self.category.name,
            'name': self.name,
            'description': self.description,
            'created_by': self.user.name,
            'created_on': str(self.created_on),
        }


engine = create_engine('sqlite:///database.db')
Base.metadata.create_all(engine)

# print "Database created"
