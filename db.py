from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Boolean, BigInteger, ARRAY, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
import os
import pymysql
pymysql.install_as_MySQLdb()
load_dotenv('config.env')
DBTOKEN = os.getenv("DB")
os.system('tzutil /s "Eastern Standard Time')
#sqlalchemy
engine = create_engine(DBTOKEN, echo=False, pool_pre_ping=True, poolclass=QueuePool) #connects to the database
base = declarative_base()
#class creates table
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

base.metadata.create_all(engine)


