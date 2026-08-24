from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import models
from models import User, Transaction
from typing import Annotated, Optional, Literal
from database import engine, SessionLocal
from fastapi.responses import JSONResponse
from datetime import datetime
from router import auth
from router.auth import get_current_user

app = FastAPI()

class TransactionCreate(BaseModel):
    title: str
    amount: float = Field(gt=0)
    type: Literal["income", "expense"]
    category: str
    date: datetime

class TransactionUpdate(BaseModel):
    title: Optional[str] = Field(default=None)
    amount: Optional[float] = Field(default=None, gt=0)
    type: Optional[Literal["income", "expense"]] = Field(default=None)
    category: Optional[str] = Field(default=None)

models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@app.post('/transactions', status_code=status.HTTP_201_CREATED)
def create_transactions(
    user: user_dependency,
    db: db_dependency,
    new_transaction: TransactionCreate
):

    if user is None:
        raise HTTPException(
            status_code=401,
            detail='Failed Authentication'
        )

    transaction_model = Transaction(
        **new_transaction.model_dump(),
        owner_id=user.get('id')
    )

    db.add(transaction_model)
    db.commit()
    db.refresh(transaction_model)

    return transaction_model

@app.get('/transactions')
def get_all_transactions(user: user_dependency, db: db_dependency):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    return db.query(Transaction).filter(Transaction.owner_id == user.get('id')).all()

@app.get('/transactions/{transaction_id}')
def get_transaction_by_id(user: user_dependency, db: db_dependency, transaction_id: int):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    specific_transaction = db.query(Transaction).filter(Transaction.owner_id == user.get('id')).filter(Transaction.id == transaction_id).first()

    if specific_transaction is not None:
        return specific_transaction

    raise HTTPException(status_code=404, detail='Transaction not found')

@app.put('/transactions/{transaction_id}')
def update_transaction(user: user_dependency, db: db_dependency, transaction_id: int, update_transaction: TransactionUpdate):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    transaction = db.query(Transaction).filter(Transaction.owner_id == user.get('id')).filter(Transaction.id == transaction_id).first()

    if transaction is None:
        raise HTTPException(status_code=404, detail='Transaction not found')

    update_data = update_transaction.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(transaction, key, value)

    db.commit()

    return JSONResponse(status_code=200, content={'message': 'Transaction updated successfully'})

@app.delete('/transactions/{transaction_id}')
def delete_transactions(user: user_dependency, db: db_dependency, transaction_id: int):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    transaction = db.query(Transaction).filter(Transaction.owner_id == user.get('id')).filter(Transaction.id == transaction_id).first()

    if transaction is None:
        raise HTTPException(status_code=404, detail='Transaction not found')

    db.delete(transaction)
    db.commit()

    return JSONResponse(status_code=200, content={'message': 'Transaction deleted successfully'})

@app.get('/transactions/filter')
def filter_transactions(
    user: user_dependency, db: db_dependency, 
    type: Optional[str] = None, category: Optional[str] = None, 
    minimum_amount: Optional[float] = None, maximum_amount: Optional[float] = None
):
    if user is None: 
        raise HTTPException(status_code=401, detail='Failed Authentication')

    query = db.query(Transaction).filter(Transaction.owner_id == user.get('id'))

    if type is not None:
        query = query.filter(Transaction.type == type)

    if category is not None:
        query = query.filter(Transaction.category == category)

    if minimum_amount is not None:
        query = query.filter(Transaction.amount >= minimum_amount)

    if maximum_amount is not None:
        query = query.filter(Transaction.amount <= maximum_amount)

    return query.all()