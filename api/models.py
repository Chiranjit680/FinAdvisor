# models.py
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, TIMESTAMP
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

import uuid
class Profile(SQLModel, table=True):
    __tablename__ = "User"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    name: str = Field(index=True)
    age: int | None = Field(index=True, ge=18, le=120)  # Age must be between 18 and 120
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
            # Removed index=True - can't use with sa_column
        )
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            onupdate=func.now()
            # Removed nullable=True and index=True - can't use with sa_column
        )
    )
    
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
     
