from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

concerts = {}
tickets = {}

def generate_id():
    return str(uuid.uuid4())

# Концерты
@app.route('/api/concerts', methods=['GET'])
def get_concerts():
    return jsonify(list(concerts.values())), 200

@app.route('/api/concerts/<concert_id>', methods=['GET'])
def get_concert(concert_id):
    concert = concerts.get(concert_id)
    if not concert:
        abort(404, description="Concert not found")
    return jsonify(concert), 200

@app.route('/api/concerts', methods=['POST'])
def create_concert():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('date') or not data.get('hall'):
        abort(400, description="Missing required fields: title, date, hall")
    concert_id = generate_id()
    concert = {
        'id': concert_id,
        'title': data['title'],
        'date': data['date'],
        'hall': data['hall'],
        'created_at': datetime.now().isoformat()
    }
    concerts[concert_id] = concert
    return jsonify(concert), 201

@app.route('/api/concerts/<concert_id>', methods=['PUT'])
def update_concert(concert_id):
    concert = concerts.get(concert_id)
    if not concert:
        abort(404, description="Concert not found")
    data = request.get_json()
    if not data or not data.get('title') or not data.get('date') or not data.get('hall'):
        abort(400, description="Missing required fields: title, date, hall")
    concert['title'] = data['title']
    concert['date'] = data['date']
    concert['hall'] = data['hall']
    concert['updated_at'] = datetime.now().isoformat()
    return jsonify(concert), 200

@app.route('/api/concerts/<concert_id>', methods=['DELETE'])
def delete_concert(concert_id):
    if concert_id not in concerts:
        abort(404, description="Concert not found")
    del concerts[concert_id]
    global tickets
    tickets = {tid: t for tid, t in tickets.items() if t['concert_id'] != concert_id}
    return '', 204

# Билеты
@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    concert_id = request.args.get('concert_id')
    if concert_id:
        filtered = [t for t in tickets.values() if t['concert_id'] == concert_id]
        return jsonify(filtered), 200
    return jsonify(list(tickets.values())), 200

@app.route('/api/tickets/<ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    ticket = tickets.get(ticket_id)
    if not ticket:
        abort(404, description="Ticket not found")
    return jsonify(ticket), 200

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    data = request.get_json()
    required = ['concert_id', 'seat', 'price']
    if not data or any(field not in data for field in required):
        abort(400, description=f"Missing required fields: {required}")
    if data['concert_id'] not in concerts:
        abort(400, description="Concert not found")
    for t in tickets.values():
        if t['concert_id'] == data['concert_id'] and t['seat'] == data['seat'] and t['status'] != 'cancelled':
            abort(400, description="Seat already taken")
    ticket_id = generate_id()
    ticket = {
        'id': ticket_id,
        'concert_id': data['concert_id'],
        'seat': data['seat'],
        'price': data['price'],
        'status': 'available',
        'created_at': datetime.now().isoformat()
    }
    tickets[ticket_id] = ticket
    return jsonify(ticket), 201

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': str(error.description)}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': str(error.description)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)