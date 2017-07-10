#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_structure import Category, Base, Item, User

engine = create_engine('sqlite:///database.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create first user
user1 = User(name="Admin", email="admin@catalog.com",
             picture='http://gofiguremath.org/wp-content/uploads/2014/06/tumblr_le70xiJNBE1qzwj2fo1_500.jpg')
session.add(user1)
session.commit()

# Soccer category
soccer = Category(created_by=1, name="Soccer")
session.add(soccer)
session.commit()

# New item for Soccer category
cleat = Item(
    created_by=1,
    name="Nike Cleat",
    description="Ready to take to the pitch and here to create, the adidas Dust Storm Pack featuring the revolutionary NEMEZIZ 17, ACE 17, COPA 17 and new X 17 will swarm stadiums with flashes of radiant colour this summer.",
    category=soccer)
session.add(cleat)
session.commit()

goal = Item(
    created_by=1,
    name="Full size Goal",
    description="This full-size soccer goal is what you'll need for the next 90 minutes.",
    category=soccer)
session.add(goal)
session.commit()

# Football category
football = Category(created_by=1, name="Football")
session.add(football)
session.commit()

# New item for Football category
jersey = Item(
    created_by=1,
    name="Jerseys",
    description="Smooth, durable HeatGear fabric with open-hole mesh for the right ventilation.",
    category=football)
session.add(jersey)
session.commit()

# Adding more categories
golf = Category(created_by=1, name="Golf")
session.add(golf)
session.commit()

# New item for Golf category
putter = Item(
    created_by=1,
    name="Putter",
    description=u"Inspired by the beautiful setting of Cleveland Golf’s North America headquarters, these putters feature the classic designs that have been revered for generations with modern innovations that can help any golfer improve their scoring.",
    category=golf)
session.add(putter)
session.commit()

# Skating category
skating = Category(created_by=1, name="Skating")
session.add(skating)
session.commit()

# New item for Skating
skateboard = Item(
    created_by=1,
    name="Skateboard",
    description="Great combination of exercise and fun, totally portable, and ideal for Primary/Intermediate level",
    category=skating)
session.add(skateboard)
session.commit()

# Softball category
softball = Category(created_by=1, name="Softball")
session.add(softball)
session.commit()

# New softball item
glove = Item(
    created_by=1,
    name="Glove",
    description="Basket-Web forms a closed, deep pocket that is popular for infielders and pitchers",
    category=softball)
session.add(glove)
session.commit()

# Tennis category
tennis = Category(created_by=1, name="Tennis")
session.add(tennis)
session.commit()

# Tennis item
racquets = Item(
    created_by=1,
    name="Racquets",
    description="Babolat Pure Drive Tennis Racquet 2015 The new Babolat Pure Drive 2015 is a puncher' racquet!",
    category=tennis)
session.add(racquets)
session.commit()

# Volleyball category
volleyball = Category(created_by=1, name="Volleyball")
session.add(volleyball)
session.commit()

# Volleyball item
net = Item(
    created_by=1,
    name="Net",
    description="Includes a Soft Touch volleyball, which lessens the impact to wrists and arms, entire set fits inside a heavy-duty polyester zippered equipment bag with carrying handles",
    category=volleyball)
session.add(net)
session.commit()

# Fitness category
fitness = Category(created_by=1, name="Fitness")
session.add(fitness)
session.commit()

# Fitness item
treadmill = Item(
    created_by=1,
    name="Treadmill",
    description="Space saver design. This treadmill can fold up.",
    category=fitness)
session.add(treadmill)
session.commit()

# Swimming category
swimming = Category(created_by=1, name="Swimming")
session.add(swimming)
session.commit()

# Swimming item
swimsuit = Item(
    created_by=1,
    name="Swimsuit",
    description="Improve overall design to offer greater freedom of movement and better fit.",
    category=swimming)
session.add(swimsuit)
session.commit()

# Running category
running = Category(created_by=1, name="Running")
session.add(running)
session.commit()

#Running item
shoe = Item(
    created_by=1,
    name="Shoe",
    description="Outdoor-ready runner with mesh and brushstroke-patterned underlays",
    category=running)
session.add(shoe)
session.commit()


print "Database population complete."
