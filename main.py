from fastapi import FastAPI,File,UploadFile,Depends
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy import Column, Integer, String, Float, create_engine
import aiofiles
import pytesseract
from pdf2image import convert_from_path


custom_config = r'--oem 3 --psm 6'

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app1.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class BookDB(Base):

    __tablename__ = "books"

    id = Column(Integer,primary_key=True,index=True)
    name = Column(String)
    file_path = Column(String)
    content = Column(String)

class TextDB(Base):

    __tablename__ = "text"

    id = Column(Integer,primary_key=True,index=True)
    text = Column(String)
    page_number = Column(Integer)


Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.post("/uploadfile")
async def create_upload_file(file:UploadFile,db:Session=Depends(get_db)):

    txt = ''
    tmp = ''

    async with aiofiles.open(f"data/{file.filename}",'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    pth = f"data/{file.filename}"
    pages = convert_from_path(pth)
    for count,page in enumerate(pages):
        txt += pytesseract.image_to_string(page,config=custom_config,lang='eng')
        tmp = pytesseract.image_to_string(page,config=custom_config,lang='eng')
        db_2 = TextDB(text=tmp,page_number=count)
        db.add(db_2)
        db.commit()
        db.refresh(db_2)

    db_item = BookDB(name=file.filename,file_path=pth,content=txt)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {
        "filename" : file.filename,
        "path" : pth,
        "text" : content
    }

