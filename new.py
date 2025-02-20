import pygame
import sys
import os
import random
import serial

#SERIAL SETUP
try:
    ser = serial.Serial('COM6', 9600, timeout=0.1)  
except serial.SerialException as e:
    print(f"Error: Could not connect to Arduino - {e}")
    ser = None

#  SOUND
pygame.mixer.init()
fruit_cut_sound = pygame.mixer.Sound("./sounds/cut.mp3")
bomb_cut_sound = pygame.mixer.Sound("./sounds/bomb.mp3")

# VARIABLES 
player_lives = 3
score = 0
fruits = ['melon', 'orng', 'app', 'guava', 'bomb']

def reset_game():
    global player_lives, score, game_over
    player_lives = 3
    score = 0
    game_over = False

def show_start_screen():
    gameDisplay.blit(background, (0, 0))
    font_large = pygame.font.Font(None, 90)
    font_small = pygame.font.Font(None, 64)
    
    gameDisplay.blit(font_large.render("FRUIT NINJA", True, WHITE), (WIDTH // 2 - 200, HEIGHT // 4))
    gameDisplay.blit(font_small.render("Press any key to start!", True, WHITE), (WIDTH // 2 - 200, HEIGHT // 2))
    
    pygame.display.flip()
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYUP:
                waiting = False

def show_gameover_screen():
    gameDisplay.blit(background, (0, 0))
    font_large = pygame.font.Font(None, 90)
    font_small = pygame.font.Font(None, 64)
    
    gameDisplay.blit(font_large.render("GAME OVER!", True, WHITE), (WIDTH // 2 - 200, HEIGHT // 4))
    gameDisplay.blit(font_small.render(f"Score: {score}", True, WHITE), (WIDTH // 2 - 100, HEIGHT // 2))
    gameDisplay.blit(font_small.render("Press any key to restart!", True, WHITE), (WIDTH // 2 - 200, HEIGHT * 3 // 4))
    gameDisplay.blit(font_small.render("Press 'E' to exit", True, WHITE), (WIDTH // 2 - 100, HEIGHT * 3 // 4 + 50))  # Exit button text

    pygame.display.flip()
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_e:  #exit the game
                    pygame.quit()
                    sys.exit()
                else:
                    reset_game()
                    waiting = False

# display set
WIDTH, HEIGHT = 1000, 500  # Screen size
FPS = 30  

pygame.init()
pygame.display.set_caption('Fruit Ninja')
gameDisplay = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

try:
    background = pygame.image.load('./img/bg.jpg')
    sword_img = pygame.image.load('./img/sword1.png')  # Sword image
    sword_img = pygame.transform.scale(sword_img, (75, 150))  # Resize sword
except pygame.error as e:
    print(f"Error loading images: {e}")
    sys.exit()

# Load fonts
try:
    font = pygame.font.Font('./fonts/PDBI.ttf', 42)
except:
    font = pygame.font.Font(None, 42)

score_text = font.render('Score : ' + str(score), True, (255, 255, 255))
lives_icon = pygame.image.load('./img/w_h.png')

# Colors
WHITE = (255, 255, 255)

#  Gyro Position
prev_x, prev_y = WIDTH // 2, HEIGHT // 2
alpha = 0.9  # Low-pass filter strength
dead_zone = 500  # Ignore small movements

def get_gyro_position():
    global prev_x, prev_y
    
    if ser:
        try:
            data = ser.readline().decode('utf-8').strip()
            if data:
                parts = data.split(',')
                if len(parts) != 2:
                    return prev_x, prev_y  

                raw_x, raw_y = map(int, parts)

                if abs(raw_x) < dead_zone: raw_x = 0
                if abs(raw_y) < dead_zone: raw_y = 0

                sensitivity_factor = 32768 / (WIDTH * 0.5)  
                mapped_x = WIDTH // 2 + (raw_x / sensitivity_factor)
                mapped_y = HEIGHT // 2 + (raw_y / sensitivity_factor)

                filtered_x = alpha * prev_x + (1 - alpha) * mapped_x
                filtered_y = alpha * prev_y + (1 - alpha) * mapped_y

                filtered_x = max(0, min(WIDTH, filtered_x))
                filtered_y = max(0, min(HEIGHT, filtered_y))

                prev_x, prev_y = filtered_x, filtered_y
                return filtered_x, filtered_y
        except Exception as e:
            print(f"Error reading gyro data: {e}")
    
    return prev_x, prev_y

data = {}
def generate_random_fruits(fruit):
    fruit_path = f"img/{fruit}.png"
    data[fruit] = {
        'img': pygame.image.load(fruit_path),
        'x': random.randint(100, 500),
        'y': 800,
        'speed_x': random.randint(-10, 10),
        'speed_y': random.randint(-80, -60),
        'throw': random.random() >= 0.75,
        't': 0,
        'hit': False,
    }

for fruit in fruits:
    generate_random_fruits(fruit)

show_start_screen()

def draw_lives(display, x, y, lives, image):
    for i in range(lives):
        img = pygame.image.load(image)
        display.blit(img, (x + 35 * i, y))

#MAIN GAME LOOP
game_over = False

while True:
    if game_over:
        show_gameover_screen()

    gameDisplay.blit(background, (0, 0))
    gameDisplay.blit(score_text, (0, 0))
    draw_lives(gameDisplay, 690, 5, player_lives, './img/r_h.png')

    current_position = get_gyro_position()
    gameDisplay.blit(sword_img, (current_position[0] - 25, current_position[1] - 50))  
    
    for key, value in data.items():
        if value['throw']:
            value['x'] += value['speed_x']
            value['y'] += value['speed_y']
            value['speed_y'] += (1 * value['t'])
            value['t'] += 1

            if value['y'] <= 800:
                gameDisplay.blit(value['img'], (value['x'], value['y']))
            else:
                generate_random_fruits(key)

            if not value['hit'] and value['x'] < current_position[0] < value['x'] + 60 \
                    and value['y'] < current_position[1] < value['y'] + 60:
                
                if key == 'bomb':  
                    if key == 'bomb':  
                        bomb_cut_sound.play()
                        player_lives -= 1
                        if player_lives == 0:
                            game_over = True
                        value['img'] = pygame.image.load("img/ex.png")  # Use explosion effect
                        continue

                else:
                    fruit_cut_sound.play()
 
                half_fruit_path = "img/" + "h_" + key + ".png"

                value['img'] = pygame.image.load(half_fruit_path)
                value['speed_x'] += 10
                if key != 'bomb' :
                    score += 1
                score_text = font.render('Score : ' + str(score), True, (255, 255, 255))
                value['hit'] = True
        else:
            generate_random_fruits(key)

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
