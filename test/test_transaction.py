from test.test_main import client
from main import app
from fastapi import status
from router.auth import get_current_user
from database import SessionLocal
from models import Transaction
from datetime import datetime

def override_get_current_user():
    return {
        'id': 1,
        'username': 'testuser'
    }

app.dependency_overrides[get_current_user] = override_get_current_user

def test_transaction():
    db = SessionLocal()
    try:
        db.query(Transaction).filter(Transaction.id == 99).delete()
        transaction = Transaction(
            id=99,
            title='Testing',
            amount=1.01,
            type='expense',
            category='Testing',
            owner_id=1,
            date=datetime.now()
        )
        db.add(transaction)
        db.commit()
    finally:
        db.close()

def test_read_transactions():
    response = client.get('/transactions')
    assert response.status_code == status.HTTP_200_OK

def test_read_specific_transactions():
    response = client.get('/transactions/99')
    assert response.status_code == status.HTTP_200_OK

def test_create_transaction():
    db = SessionLocal()
    db.query(Transaction).filter(Transaction.id == 0).delete()
    db.query()
    db.commit()

    request_data = {
        "id": 0,
        "title": "Test Transaction",
        "amount": 250.50,
        "type": "expense",
        "category": "Food",
        "date": "2026-08-24T14:00:00"
    }

    response = client.post('/transactions', json=request_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {'message': 'Transaction created successfully'}

def test_update_transaction():
    request_data = {
        "title": "Updated"
    }

    response = client.put('/transactions/99', json=request_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message': 'Transaction updated successfully'}

def test_delete_transaction():
    response = client.delete('/transactions/99')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message': 'Transaction deleted successfully'}