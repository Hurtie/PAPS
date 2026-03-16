import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:pass@db:5432/ticketdb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модели
class Concert(db.Model):
    __tablename__ = 'concerts'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    hall = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'date': self.date.isoformat(),
            'hall': self.hall,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    concert_id = db.Column(db.String(36), db.ForeignKey('concerts.id', ondelete='CASCADE'), nullable=False)
    seat = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Numeric(10,2), nullable=False)
    status = db.Column(db.String(20), default='available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('concert_id', 'seat', name='unique_concert_seat'),)

    def to_dict(self):
        return {
            'id': self.id,
            'concert_id': self.concert_id,
            'seat': self.seat,
            'price': float(self.price),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

with app.app_context():
    db.create_all()

# ---------- API для концертов ----------
@app.route('/api/v1/concerts', methods=['GET'])
def get_concerts():
    concerts = Concert.query.all()
    return jsonify([c.to_dict() for c in concerts]), 200

@app.route('/api/v1/concerts/<concert_id>', methods=['GET'])
def get_concert(concert_id):
    concert = Concert.query.get(concert_id)
    if not concert:
        abort(404, description="Concert not found")
    return jsonify(concert.to_dict()), 200

@app.route('/api/v1/concerts', methods=['POST'])
def create_concert():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('date') or not data.get('hall'):
        abort(400, description="Missing required fields: title, date, hall")
    concert = Concert(
        title=data['title'],
        date=datetime.fromisoformat(data['date']),
        hall=data['hall']
    )
    db.session.add(concert)
    db.session.commit()
    return jsonify(concert.to_dict()), 201

@app.route('/api/v1/concerts/<concert_id>', methods=['PUT'])
def update_concert(concert_id):
    concert = Concert.query.get(concert_id)
    if not concert:
        abort(404, description="Concert not found")
    data = request.get_json()
    if not data or not data.get('title') or not data.get('date') or not data.get('hall'):
        abort(400, description="Missing required fields: title, date, hall")
    concert.title = data['title']
    concert.date = datetime.fromisoformat(data['date'])
    concert.hall = data['hall']
    db.session.commit()
    return jsonify(concert.to_dict()), 200

@app.route('/api/v1/concerts/<concert_id>', methods=['DELETE'])
def delete_concert(concert_id):
    concert = Concert.query.get(concert_id)
    if not concert:
        abort(404, description="Concert not found")
    db.session.delete(concert)
    db.session.commit()
    return '', 204

# ---------- API для билетов ----------
@app.route('/api/v1/tickets', methods=['GET'])
def get_tickets():
    concert_id = request.args.get('concert_id')
    query = Ticket.query
    if concert_id:
        query = query.filter_by(concert_id=concert_id)
    tickets = query.all()
    return jsonify([t.to_dict() for t in tickets]), 200

@app.route('/api/v1/tickets/<ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        abort(404, description="Ticket not found")
    return jsonify(ticket.to_dict()), 200

@app.route('/api/v1/tickets', methods=['POST'])
def create_ticket():
    data = request.get_json()
    required = ['concert_id', 'seat', 'price']
    if not data or any(field not in data for field in required):
        abort(400, description=f"Missing required fields: {required}")
    # Проверка существования концерта
    concert = Concert.query.get(data['concert_id'])
    if not concert:
        abort(400, description="Concert not found")
    # Проверка уникальности места (ограничение на уровне БД, но дополнительно проверим)
    existing = Ticket.query.filter_by(concert_id=data['concert_id'], seat=data['seat']).first()
    if existing:
        abort(400, description="Seat already taken")
    ticket = Ticket(
        concert_id=data['concert_id'],
        seat=data['seat'],
        price=data['price']
    )
    db.session.add(ticket)
    db.session.commit()
    return jsonify(ticket.to_dict()), 201

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': str(error.description)}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': str(error.description)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)