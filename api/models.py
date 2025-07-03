# models.py
from sqlmodel import Field, SQLModel, Relationship, Session, create_engine
from typing import Optional, List, Union
from datetime import datetime
import uuid
from sqlalchemy import Column, String, TIMESTAMP, func
from pydantic import EmailStr, validator, BaseModel

# Create a single metadata instance
metadata = SQLModel.metadata

class Profile(SQLModel, table=True):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(sa_column=Column(String, unique=True, nullable=False))
    email: EmailStr = Field(sa_column=Column(String, unique=True, nullable=False))
    password_hash: str = Field(nullable=False)
    name: str = Field(nullable=False)
    age: Optional[int] = Field(default=None, nullable=True)

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
class PersonalInfo(SQLModel, table=True):
    __tablename__ = "personal_info"
    __table_args__ = {"extend_existing": True}  # Add this line

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    location: Optional[str] = Field(default="Ind", nullable=True)
    occupation: Optional[str] = Field(default=None, nullable=True)
    dependants: Optional[int] = Field(default=0, nullable=True)
    marital_status: Optional[str] = Field(default=None, nullable=True)
    income: Optional[float] = Field(default=None, nullable=True)
    

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
class Token(BaseModel):
    
    access_token: str
    token_type: str = "bearer"
class TokenData(BaseModel):
    id: Union[int, uuid.UUID]  # Use Union to allow both int and UUID types
    username: str
    email: EmailStr

    class Config:
        orm_mode = True  # Enable ORM mode for compatibility with SQLModel
        arbitrary_types_allowed = True  # Allow arbitrary types like UUID
        json_encoders = {
            uuid.UUID: str  # Ensure UUIDs are serialized as strings
        }


# Profile create request model
class ProfileCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    name: str
    age: Optional[int] = None

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
    def validate_age(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 18 or v > 120):
            raise ValueError("age must be between 18 and 120")
        return v


# Profile output model
class ProfileOut(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    name: str
    age: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]


class Chat(SQLModel, table=True):
    __tablename__ = "chat"
    __table_args__ = {"extend_existing": True}  # Add this line

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    human_message: str = Field()
    ai_message: str = Field()
    timestamp: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )


class UserLogin(SQLModel, table=True):
    __tablename__ = "user_login"
    __table_args__ = {"extend_existing": True}  # Add this line
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_name: str = Field(index=True)
    password: str = Field(index=True)
    login_time: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )


class Portfolio(SQLModel, table=True):
    __tablename__ = "portfolio"
    __table_args__ = {"extend_existing": True}  # Add this line
    
    portfolio_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    equity_amt: Optional[float] = Field(default=None, index=True)
    cash_amt: Optional[float] = Field(default=None, index=True)
    fd_amt: Optional[float] = Field(default=None, index=True)
    debt_amt: Optional[float] = Field(default=None, index=True)
    real_estate_amt: Optional[float] = Field(default=None, index=True)
    bonds_amt: Optional[float] = Field(default=None, index=True)
    crypto_amt: Optional[float] = Field(default=None, index=True)
    
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


class StockData(SQLModel, table=True):
    __tablename__ = "stock_data"
    __table_args__ = {"extend_existing": True}  # Add this line
    
    stock_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    stock_name: str = Field(index=True)
    stock_ticker: str = Field(sa_column=Column(String, unique=True, nullable=False))
    sector: Optional[str] = Field(default=None, index=True)
    current_price: float = Field(index=True)
    pe_ratio: Optional[float] = Field(default=None, index=True)
    pb_ratio: Optional[float] = Field(default=None, index=True)
    dividend_yield: Optional[float] = Field(default=None, index=True)
    eps: Optional[float] = Field(default=None, index=True)
    book_value: Optional[float] = Field(default=None, index=True)
    market_cap: Optional[float] = Field(default=None, index=True)
    volume: Optional[int] = Field(default=None, index=True)
    last_updated: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            onupdate=func.now()
        )
    )


# Additional response models for consistency
class ChatOut(BaseModel):
    id: int
    user_id: uuid.UUID
    human_message: str
    ai_message: str
    timestamp: datetime


class PortfolioOut(BaseModel):
    portfolio_id: uuid.UUID
    user_id: uuid.UUID
    equity_amt: Optional[float]
    cash_amt: Optional[float]
    fd_amt: Optional[float]
    debt_amt: Optional[float]
    real_estate_amt: Optional[float]
    bonds_amt: Optional[float]
    crypto_amt: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]


class StockDataOut(BaseModel):
    stock_id: uuid.UUID
    stock_name: str
    stock_ticker: str
    sector: Optional[str]
    current_price: float
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    dividend_yield: Optional[float]
    eps: Optional[float]
    book_value: Optional[float]
    market_cap: Optional[float]
    volume: Optional[int]
    last_updated: datetime