def game_loop():
    while True:
        socketio.sleep(0.05)  # 20 FPS
        
        # 1. Krok: Posun všetkých živých hadov
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
            
            # Kontrola jedla
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

        # 2. Krok: Kontrola kolízií (Smrť)
        dead_players = []

        for p_id, player in game_state["players"].items():
            head = player["body"][0]
            
            for other_id, other_player in game_state["players"].items():
                for index, part in enumerate(other_player["body"]):
                    # OPRAVA: Ak kontrolujeme vlastné telo, ignorujeme prvých 4 článkov (vrátane hlavy),
                    # aby čerstvo zjedené jedlo (nový článok) nespôsobilo okamžitú smrť.
                    if p_id == other_id and index < 4:
                        continue
                        
                    dist = math.hypot(head["x"] - part["x"], head["y"] - part["y"])
                    
                    if dist < 15:
                        dead_players.append(p_id)
                        break
                if p_id in dead_players:
                    break

        # 3. Krok: Respawn mŕtvych hadov
        for p_id in dead_players:
            if p_id in game_state["players"]:
                new_x = random.randint(100, MAP_WIDTH - 100)
                new_y = random.randint(100, MAP_HEIGHT - 100)
                
                game_state["players"][p_id]["score"] = 0
                game_state["players"][p_id]["body"] = [{"x": new_x, "y": new_y}]
                
                for _ in range(2):
                    game_state["players"][p_id]["body"].append({"x": new_x, "y": new_y})

        # Doplnenie jedla a odoslanie dát
        spawn_food()
        socketio.emit('game_tick', game_state)