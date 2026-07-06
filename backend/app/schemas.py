from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class BookBase(BaseModel):
    title: str
    author: str
    isbn: Optional[str] = None
    year: Optional[int] = None
    available: bool = True


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    year: Optional[int] = None
    available: Optional[bool] = None


class Book(BookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class LoanBase(BaseModel):
    book_id: int
    user_id: int
    loan_date: date
    due_date: date
    returned: bool = False


class LoanCreate(LoanBase):
    pass


class LoanUpdate(BaseModel):
    book_id: Optional[int] = None
    user_id: Optional[int] = None
    loan_date: Optional[date] = None
    due_date: Optional[date] = None
    returned: Optional[bool] = None


class Loan(LoanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book: Optional[Book] = None
    user: Optional[User] = None


class Metrics(BaseModel):
    total_books: int
    available_books: int
    loaned_books: int
    registered_users: int
    active_loans: int
