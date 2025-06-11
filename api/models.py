# models.py
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, TIMESTAMP, String
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
from pydantic import validator
import emailvalidator
import uuid
from pydantic import BaseModel
from pydantic.networks import EmailStr
class Profile(SQLModel, table=True):
    __tablename__ = "user"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field( sa_column=Column(String, unique=True, nullable=False))
    email: EmailStr = Field( sa_column=Column(String, unique=True, nullable=False))
    password_hash: str = Field(nullable=False)
    name: str = Field(nullable=False)
    age: Optional[int] = Field(nullable=True)

    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            onupdate=func.now()
        )
    )

# validator for pydantic side → works only in basemodel (see below)

# profile create request model


class ProfileCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    name: str
    age: int | None

    @validator("email")
    def validate_email(cls, v: str) -> str:
        if not v or "@" not in v:
            raise ValueError("invalid email address")
        return v.lower()

    @validator("username")
    def validate_username(cls, v: str) -> str:
        if not v or len(v) < 3:
            raise ValueError("username must be at least 3 characters long")
        return v.strip()

    @validator("age")
    def validate_age(cls, v: int) -> int:
        if v is not None and (v < 18 or v > 120):
            raise ValueError("age must be between 18 and 120")
        return v

# profile out model
class ProfileOut(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    name: str
    age: int | None
    created_at: datetime
    updated_at: Optional[datetime]

class Chat(SQLModel, table=True):
    __tablename__ = "Chat"

    id: int | None = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="User.id", index=True)
    human_message: str = Field()
    ai_message: str = Field()
    timestamp: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
class UserLogin(SQLModel, table=True):
    __tablename__ = "UserLogin"


    user_name: str = Field(index=True)
    password: str = Field(index=True)
    login_time: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
class Portfolio(SQLModel, table=True):
    __tablename__ = "Portfolio"

    portfolio_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="User.id", index=True)
    equity_amt: float | None = Field(default=None, index=True)
    cash_amt: float | None = Field(default=None, index=True)
    fd_amt: float | None = Field(default=None, index=True)
    debt_amt: float | None = Field(default=None, index=True)

    real_estate_amt: float | None = Field(default=None, index=True)
    
    bonds_amt: float | None = Field(default=None, index=True)

    crypto_amt: float | None = Field(default=None, index=True)
     
class StockData(SQLModel, table=True):
    __tablename__ = "StockData"

    stock_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    stock_name: str = Field(index=True)
    stock_ticker: str = Field(index=True, sa_column=Column(String, unique=True, nullable=False))
    sector: str | None = Field(default=None, index=True)
    current_price: float = Field(index=True)
    pe_ratio: float | None = Field(default=None, index=True)
    pb_ratio: float | None = Field(default=None, index=True)
    dividend_yield: float | None = Field(default=None, index=True)
    eps: float | None = Field(default=None, index=True)
    book_value: float | None = Field(default=None, index=True)
    market_cap: float | None = Field(default=None, index=True)
    volume: int | None = Field(default=None, index=True)
    last_updated: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            onupdate=func.now()
        )
    )
