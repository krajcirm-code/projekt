import eventlet
eventlet.monkey_patch()  # Tento riadok musí byť úplne prvý pred všetkými ostatnými importami

import os
import math
import random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'snake_secret_123'
socketio = SocketIO(app, cors_allowed_origins="*")

MAP_WIDTH = 800
MAP_HEIGHT = 600

game_state = {
    "players": {},
    "foods": []
}

def spawn_food():
    while len(game_state["foods"]) < 30:
        game_state["foods"].append({
            "x": random.randint(10, MAP_WIDTH - 10),
            "y": random.randint(10, MAP_HEIGHT - 10),
            "color": random.choice(["#ff0000", "#00ff00", "#ffff00", "#ff00ff", "#00ffff"])
        })

spawn_food()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    p_id = request.sid
    new_x = random.randint(100, 700)
    new_y = random.randint(100, 500)
    
    game_state["players"][p_id] = {
        "id": p_id,
        "body": [{"x": new_x, "y": new_y}],
        "color": random.choice(["#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#f1c40f"]),
        "angle": 0,
        "score": 0
    }
    for _ in range(2):
        game_state["players"][p_id]["body"].append({"x": new_x, "y": new_y})

@socketio.on('disconnect')
def handle_disconnect():
    p_id = request.sid
    if p_id in game_state["players"]:
        del game_state["players"][p_id]

@socketio.on('update_input')
def handle_input(data):
    p_id = request.sid
    if p_id in game_state["players"]:
        game_state["players"][p_id]["angle"] = data["angle"]

def game_loop():
    while True:
        socketio.sleep(0.05)
        
        for p_id, player in list(game_state["players"].items()):
            body = player["body"]
            head = body[0]
            angle = player["angle"]
            
            speed = 5
            new_head = {
                "x": (head["x"] + math.cos(angle) * speed) % MAP_WIDTH,
                "y": (head["y"] + math.sin(angle) * speed) % MAP_HEIGHT
            }
            
            body.insert(0, new_head)
            
            ate_food = False
            for food in list(game_state["foods"]):
                dist = math.hypot(new_head["x"] - food["x"], new_head["y"] - food["y"])
                if dist < 15:
                    game_state["foods"].remove(food)
                    player["score"] += 1
                    ate_food = True
                    break
            
            if not ate_food:
                body.pop()

        dead_players = []

        for p_id, player in game_state["players"].items():
            head = player["body"][0]
            
            for other_id, other_player in game_state["players"].items():
                for index, part in enumerate(other_player["body"]):
                    if p_id == other_id:
                        if index < 6:
                            continue
                    else:
                        if index == 0:
                            continue

                    dist = math.hypot(head["x"] - part["x"], head["y"] - part["y"])
                    if dist < 12:
                        dead_players.append(p_id)
                        break
                if p_id in dead_players:
                    break

        for p_id in dead_players:
            if p_id in game_state["players"]:
                new_x = random.randint(100, MAP_WIDTH - 100)
                new_y = random.randint(100, MAP_HEIGHT - 100)
                game_state["players"][p_id]["score"] = 0
                game_state["players"][p_id]["body"] = [{"x": new_x, "y": new_y}]
                for _ in range(2):
                    game_state["players"][p_id]["body"].append({"x": new_x, "y": new_y})

        spawn_food()
        socketio.emit('game_tick', game_state)

socketio.start_background_task(game_loop)

if __name__ == '__main__':
    socketio.run(app, debug=True)