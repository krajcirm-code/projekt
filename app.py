def game_loop():
    while True:
        socketio.sleep(0.05)  # 20 FPS
        
        # 1. KROK: Posun všetkých živých hadov
        for p_id, player in list(game_state["players"].items()):
            body = player["body"]
            head = body[0]
            angle = player["angle"]
            
            speed = 5
            new_head = {
                "x": (head["x"] + math.cos(angle) * speed) % MAP_WIDTH,
                "y": (head["y"] + math.sin(angle) * speed) % MAP_HEIGHT
            }
            
            # Pridáme novú hlavu
            body.insert(0, new_head)
            
            # Kontrola, či hlava zjedla jedlo
            ate_food = False
            for food in list(game_state["foods"]):
                dist = math.hypot(new_head["x"] - food["x"], new_head["y"] - food["y"])
                if dist < 15:
                    game_state["foods"].remove(food)
                    player["score"] += 1
                    ate_food = True
                    break  # Zjedol jedno jedlo v tomto ticku
            
            # AK NEZJEDOL JEDLO, odrežeme chvost (had sa len posunul)
            # AK ZJEDOL JEDLO, neodrežeme chvost (had narástol o 1 článok)
            if not ate_food:
                body.pop()

        # 2. KROK: Kontrola kolízií (SMRŤ - iba had vs had)
        dead_players = []

        for p_id, player in game_state["players"].items():
            head = player["body"][0]
            
            for other_id, other_player in game_state["players"].items():
                # Prechádzame články tela druhého hada
                for index, part in enumerate(other_player["body"]):
                    
                    # Ak kontrolujem seba samého:
                    # Ignorujeme hlavu a prvých 5 článkov, aby sa had nezabil pri raste alebo miernom otočení
                    if p_id == other_id:
                        if index < 6:
                            continue
                    
                    # Ak kontrolujem cudzieho hada:
                    # Ignorujeme jeho hlavu (index 0), aby z čelnej zrážky profitoval ten rýchlejší / nedošlo k bugu
                    else:
                        if index == 0:
                            continue

                    # Výpočet vzdialenosti medzi mojou hlavou a článkom tela
                    dist = math.hypot(head["x"] - part["x"], head["y"] - part["y"])
                    
                    if dist < 12:  # Jemne znížený rádius kolízie pre lepšiu hrateľnosť
                        dead_players.append(p_id)
                        break
                if p_id in dead_players:
                    break

        # 3. KROK: Respawn mŕtvych hadov
        for p_id in dead_players:
            if p_id in game_state["players"]:
                new_x = random.randint(100, MAP_WIDTH - 100)
                new_y = random.randint(100, MAP_HEIGHT - 100)
                
                game_state["players"][p_id]["score"] = 0
                game_state["players"][p_id]["body"] = [{"x": new_x, "y": new_y}]
                
                # Vytvoríme základné 3 články na rovnakej štartovacej pozícii
                for _ in range(2):
                    game_state["players"][p_id]["body"].append({"x": new_x, "y": new_y})

        # Doplnenie jedla na mapu a odoslanie dát klientom
        spawn_food()
        socketio.emit('game_tick', game_state)