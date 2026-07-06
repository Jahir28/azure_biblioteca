from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Azure Biblioteca API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


def commit_or_409(db: Session):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El registro viola una restriccion unica o de relacion.",
        ) from exc


def get_or_404(db: Session, model, item_id: int):
    item = db.get(model, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Registro no encontrado.")
    return item


def sync_book_availability(db: Session, book_id: int):
    book = db.get(models.Book, book_id)
    if book:
        active_loan = (
            db.query(models.Loan)
            .filter(models.Loan.book_id == book_id, models.Loan.returned.is_(False))
            .first()
        )
        book.available = active_loan is None


def sync_all_book_availability(db: Session):
    for book in db.query(models.Book).all():
        sync_book_availability(db, book.id)
    db.commit()


@app.get("/metrics", response_model=schemas.Metrics)
def read_metrics(db: Session = Depends(get_db)):
    sync_all_book_availability(db)
    total_books = db.query(models.Book).count()
    available_books = db.query(models.Book).filter(models.Book.available.is_(True)).count()
    active_loans = db.query(models.Loan).filter(models.Loan.returned.is_(False)).count()
    loaned_books = (
        db.query(models.Loan.book_id)
        .filter(models.Loan.returned.is_(False))
        .distinct()
        .count()
    )
    return {
        "total_books": total_books,
        "available_books": available_books,
        "loaned_books": loaned_books,
        "registered_users": db.query(models.User).count(),
        "active_loans": active_loans,
    }


@app.get("/books", response_model=list[schemas.Book])
def list_books(db: Session = Depends(get_db)):
    sync_all_book_availability(db)
    return db.query(models.Book).order_by(models.Book.id.desc()).all()


@app.post("/books", response_model=schemas.Book, status_code=status.HTTP_201_CREATED)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    book_data = book.model_dump()
    book_data["available"] = True
    db_book = models.Book(**book_data)
    db.add(db_book)
    commit_or_409(db)
    db.refresh(db_book)
    return db_book


@app.put("/books/{book_id}", response_model=schemas.Book)
def update_book(book_id: int, book: schemas.BookUpdate, db: Session = Depends(get_db)):
    db_book = get_or_404(db, models.Book, book_id)
    for field, value in book.model_dump(exclude_unset=True).items():
        setattr(db_book, field, value)
    commit_or_409(db)
    db.refresh(db_book)
    return db_book


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = get_or_404(db, models.Book, book_id)
    db.delete(db_book)
    commit_or_409(db)


@app.get("/users", response_model=list[schemas.User])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.id.desc()).all()


@app.post("/users", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    commit_or_409(db)
    db.refresh(db_user)
    return db_user


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = get_or_404(db, models.User, user_id)
    for field, value in user.model_dump(exclude_unset=True).items():
        setattr(db_user, field, value)
    commit_or_409(db)
    db.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = get_or_404(db, models.User, user_id)
    db.delete(db_user)
    commit_or_409(db)


@app.get("/loans", response_model=list[schemas.Loan])
def list_loans(db: Session = Depends(get_db)):
    return db.query(models.Loan).order_by(models.Loan.id.desc()).all()


@app.post("/loans", response_model=schemas.Loan, status_code=status.HTTP_201_CREATED)
def create_loan(loan: schemas.LoanCreate, db: Session = Depends(get_db)):
    book = get_or_404(db, models.Book, loan.book_id)
    get_or_404(db, models.User, loan.user_id)
    if not loan.returned and not book.available:
        raise HTTPException(status_code=409, detail="El libro no esta disponible.")
    db_loan = models.Loan(**loan.model_dump())
    db.add(db_loan)
    if not db_loan.returned:
        book.available = False
    commit_or_409(db)
    db.refresh(db_loan)
    return db_loan


@app.put("/loans/{loan_id}", response_model=schemas.Loan)
def update_loan(loan_id: int, loan: schemas.LoanUpdate, db: Session = Depends(get_db)):
    db_loan = get_or_404(db, models.Loan, loan_id)
    previous_book_id = db_loan.book_id
    for field, value in loan.model_dump(exclude_unset=True).items():
        setattr(db_loan, field, value)
    get_or_404(db, models.Book, db_loan.book_id)
    get_or_404(db, models.User, db_loan.user_id)
    sync_book_availability(db, previous_book_id)
    sync_book_availability(db, db_loan.book_id)
    commit_or_409(db)
    db.refresh(db_loan)
    return db_loan


@app.delete("/loans/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(loan_id: int, db: Session = Depends(get_db)):
    db_loan = get_or_404(db, models.Loan, loan_id)
    book_id = db_loan.book_id
    db.delete(db_loan)
    commit_or_409(db)
    sync_book_availability(db, book_id)
    db.commit()
