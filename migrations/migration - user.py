from sqlalchemy import create_engine, MetaData
from sqlalchemy import Column, Integer, String, Table, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Engine to the database to query the data from
# (postgresql)
source_engine = create_engine("sqlite:///bot.sqlite", echo=False)
SourceSession = sessionmaker(source_engine)

# Engine to the database to store the results in
# (sqlite)
dest_engine = create_engine("mysql://bot:nKUZCzcm$LK!nffvpCEu8@66.23.234.43/rmrbot", echo=True)
DestSession = sessionmaker(dest_engine)
session = DestSession()

# Create some toy table and fills it with some data
base = declarative_base()
class user (base):

   __tablename__ = 'user'

   uid = Column(BigInteger, primary_key=True)
   dob = Column(String(10))

   def __init__(self, uid, dob):
       self.uid = uid
       self.dob = dob

class config(base):

    __tablename__ = 'config'

    guild = Column(BigInteger, primary_key=True)
    lobby = Column(BigInteger)
    agelog = Column(BigInteger)
    modlobby = Column(BigInteger)
    general = Column(BigInteger)

    def __init__(self, guild, lobby, agelog, modlobby, general):
        self.guild = guild
        self.lobby = lobby
        self.agelog = agelog
        self.modlobby = modlobby
        self.general = general
#commits it to the databse
class permissions (base):

   __tablename__ = 'permissions'

   guild = Column(BigInteger, primary_key=True)
   admin = Column(BigInteger, default=None)
   mod = Column(BigInteger, default=None)
   trial = Column(BigInteger, default=None)
   lobbystaff = Column(BigInteger, default=None)

   def __init__(self,guild, admin, mod, trial, lobbystaff):
       self.guild = guild
       self.admin = admin
       self.mod = mod
       self.trial = trial
       self.lobbystaff = lobbystaff

class warnings (base):

   __tablename__ = 'warnings'

   uid = Column(BigInteger, primary_key=True)
   swarnings = Column(BigInteger)


   def __init__(self, uid, swarnings):
       self.uid = uid
       self.swarnings = swarnings
base.metadata.create_all(source_engine)
sourceSession = SourceSession()
base.metadata.create_all(dest_engine)
sourceSession = SourceSession()




# Moving data from the old database to the new

uid= sourceSession.query(user.uid).all()
for users in uid:
    try:
        userid1 = str(users).replace(",","")
        userid2 = userid1.replace(")", "")
        userid3 = userid2.replace("(", "")
        exists = sourceSession.query(user).filter_by(uid=userid3).first()
        intuid = int(exists.uid)
        tr = user(intuid, exists.dob)
        session.add(tr)
        session.commit()
        print(f"{userid3} added")
    except:
        print(f"{users} failed")

