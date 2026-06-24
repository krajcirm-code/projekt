import os
import random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'snake_secret_123'
socketio = SocketIO(app, cors_allowed_origins="*")

# Konštanty mapy
MAP_WIDTH = 800
MAP_HEIGHT = 600

# Globálny stav hry
game_state = {
    "players": {},  # id: { name, body: [{x,y}], color, angle, score }
    "foods": []     # list of {x, y, color}
}

# Vygenerovanie počiatočného jedla
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
    # Inicializácia nového hada
    game_state["players"][p_id] = {
        "id": p_id,
        "body": [{"x": random.randint(100, 700), "y": random.randint(100, 500)}],
        "color": random.choice(["#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#f1c40f"]),
        "angle": 0,
        "score": 0
    }
    # Predĺžime hada na začiatok (3 články)
    start_x = game_state["players"][p_id]["body"][0]["x"]
    start_y = game_state["players"][p_id]["body"][0]["y"]
    for _ in range(2):
        game_state["players"][p_id]["body"].append({"x": start_x, "y": start_y})

@socketio.on('disconnect')
def handle_disconnect():
    p_id = request.sid
    if p_id in game_state["players"]:
        del game_state["players"][p_id]

@socketio.on('update_input')
def handle_input(data):
    p_id = request.sid
    if p_id in game_state["players"]:
        # Klient posiela uhol, ktorým smerom sa má had hýbať
        game_state["players"][p_id]["angle"] = data["angle"]

# Hlavná herná slučka (beží na pozadí)
def game_loop():
    while True:
        socketio.sleep(0.05)  # 20 FPS (každých 50ms)
        
        for p_id, player in list(game_state["players"].items()):
            body = player["body"]
            head = body[0]
            angle = player["angle"]
            
            # Výpočet nového pohybu hlavy
            import math
            speed = 5
            new_head = {
                "x": (head["x"] + math.cos(angle) * speed) % MAP_WIDTH,
                "y": (head["y"] + math.sin(angle) * speed) % MAP_HEIGHT
            }
            
            # Pridanie novej hlavy na začiatok tela
            body.insert(0, new_head)
            
            # Kontrola kolízie s jedlom
            ate_food = False
            for food in list(game_state["foods"]):
                # Vzdialenosť medzi hlavou a jedlom
                dist = math.hypot(new_head["x"] - food["x"], new_head["y"] - food["y"])
                if dist < 15:  # kolízia
                    game_state["foods"].remove(food)
                    player["score"] += 1
                    ate_food = True
                    break
            
            # Ak nezjedol jedlo, odstránime posledný článok (had sa len posunul)
            if not ate_food:
                body.pop()
                
        # Doplnenie jedla, ak nejaké chýba
        spawn_food()
        
        # Odoslanie stavu všetkým hráčom
        socketio.emit('game_tick', game_state)

# Spustenie hernej slučky hneď po štarte socketov
socketio.start_background_task(game_loop)

if __name__ == '__main__':
    # Render automaticky priraďuje port cez premennú prostredia PORT
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)