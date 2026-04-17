import pygame
from pygame.locals import *
from pygame import mixer
import pickle
from os import path
import time as pytime
import json

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
fps = 120

screen_width = 1000
screen_height = 1000

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Platformer")

#define font
font = pygame.font.SysFont('Bauhaus 93', 70)
font_score = pygame.font.SysFont('Bauhaus 93', 30)
title_font = pygame.font.SysFont('Bauhaus 93', 120)

#define game variables
tile_size = 50
game_over = 0
main_menu = True
leaderboard_menu = False
level = 1
max_levels = 7
score = 0
start_time = 0
final_time = 0
timer_running = False
entering_name = False
player_name = ""


#define colours
white = (255, 255, 255)
blue = (0, 0, 255)
black = (0, 0, 0)

#load images
sun_img = pygame.image.load('platformer_assets/img/sun.png')
bg_img = pygame.image.load('platformer_assets/img/sky.png')
restart_img = pygame.image.load('platformer_assets/img/restart_btn.png')
start_img = pygame.image.load('platformer_assets/img/start_btn.png')
exit_img = pygame.image.load('platformer_assets/img/exit_btn.png')
menu_bg = pygame.image.load('platformer_assets/img/main.menu.png')
menu_bg = pygame.transform.scale(menu_bg, (screen_width, screen_height))
leaderboard_img = pygame.image.load("platformer_assets/img/leaderboard_btn.png").convert_alpha()
rect = leaderboard_img.get_bounding_rect()  # finds non-transparent area
leaderboard_img = leaderboard_img.subsurface(rect).copy()


#scale leaderboard image
target_width = start_img.get_width() * 2  # or 1.5 if you want smaller

scale = target_width / leaderboard_img.get_width()

new_width = int(leaderboard_img.get_width() * scale)
new_height = int(leaderboard_img.get_height() * scale)

leaderboard_img = pygame.transform.scale(leaderboard_img, (new_width, new_height))
#have the buttons centered
center_x = screen_width // 2
button_y = screen_height // 2 - 50
spacing = 200     

#position leaderboard image
leaderboard_x = center_x - leaderboard_img.get_width() // 2
leaderboard_y = button_y + start_img.get_height() + 40


#load sounds
pygame.mixer.music.load('platformer_assets/img/music.wav')
pygame.mixer.music.play(-1, 0.0, 5000)
coin_fx = pygame.mixer.Sound('platformer_assets/img/coin.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('platformer_assets/img/jump.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('platformer_assets/img/game_over.wav')
game_over_fx.set_volume(0.5)



def draw_text(text, font, text_col, x, y, outline_col=None):
    if outline_col:
        outline = font.render(text, True, outline_col)

        # draw outline in 8 directions (smoother)
        for dx in [-2, 0, 1]:
            for dy in [-2, 0, 1]:
                if dx != 0 or dy != 0:
                    screen.blit(outline, (x + dx, y + dy))

    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

#function to reset level
def reset_level(level):
    player.reset(100, screen_height - 130)
    blob_group.empty()
    platform_group.empty()
    coin_group.empty()
    lava_group.empty()
    exit_group.empty()

    #load in level data and create world
    if path.exists(f'platformer_assets/level{level}_data'):
        pickle_in = open(f'platformer_assets/level{level}_data', 'rb')
        world_data = pickle.load(pickle_in)
    world = World(world_data)

    return world

def load_leaderboard():
    try:
        with open("leaderboard.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_leaderboard(data):
    with open("leaderboard.json", "w") as f:
        json.dump(data, f)


class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False
    
    def draw(self):
        action = False

        #get mouse position
        pos = pygame.mouse.get_pos()

        #check mouseover and clicked conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True
                
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False


        #draw button
        screen.blit(self.image, self.rect)

        return action


class Player():
    def __init__(self, x, y):
        self.reset(x, y)



    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 5
        col_tresh = 20

        if game_over == 0:
            # --- TIMER ---
            if timer_running:
                current_time = pytime.time() - start_time
            else:
                current_time = final_time

            draw_text(f'Time: {current_time:.2f}', font_score, white, screen_width - 200, 10)
            #get keypresses
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE] and self.jumped == False and self.in_air == False:
                jump_fx.play()
                self.vel_y = -15
                self.jumped = True
            if key[pygame.K_SPACE] == False:
                self.jumped = False

            if key[pygame.K_LEFT] or key[pygame.K_a]:
                dx -= 5
                self.counter += 1
                self.direction = -1

            if key[pygame.K_RIGHT] or key[pygame.K_d]:
                dx += 5
                self.counter += 1
                self.direction = 1

            if (key[pygame.K_LEFT] == False and key[pygame.K_a] == False) and (key[pygame.K_RIGHT] == False and key[pygame.K_d] == False):
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            #handle animation
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1                
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]


            #add gravity
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y
            
            #check for collision
            self.in_air = True
            for tile in world.tile_list:
                #check for collision in x direction
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                #check for collision in y direction
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #check if below the ground i.e. jumping
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    #check if above the ground i.e. falling
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False


            #check for collision with enemies
            if pygame.sprite.spritecollide(self, blob_group, False):
                game_over = -1
                game_over_fx.play()

            #check for collision with lava
            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over = -1
                game_over_fx.play()

            #check for collision with exit
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1

            #check for collision with moving platforms
            for platform in platform_group:
                #check collision in x direction
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                #check collision in y direction
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #check if below platform i.e. jumping
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_tresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    #check if above platform i.e. falling
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_tresh:
                        self.rect.bottom = platform.rect.top - 0.1
                        self.in_air = False
                        dy = 0
                        #move with the platform
                        if platform.move_x != 0:
                            self.rect.x += platform.move_direction * platform.move_x


            #update player coordinates
            self.rect.x += dx
            self.rect.y += dy


        elif game_over == -1:
            self.image = self.dead_image
            draw_text('GAME OVER!', font, blue, (screen_width // 2) - 150, screen_height // 2)
            if self.rect.y > 200:
                self.rect.y -= 5

        #draw player onto screen
        screen.blit(self.image, self.rect)

        return game_over


    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 5):
            img_right = pygame.image.load(f'platformer_assets/img/guy{num}.png')
            img_right = pygame.transform.scale(img_right, (40, 80))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.dead_image = pygame.image.load('platformer_assets/img/ghost.png')
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True



class World():
    def __init__(self, data):
        self.tile_list = []
        
        #load images
        dirt_img = pygame.image.load('platformer_assets/img/dirt.png')
        grass_img = pygame.image.load('platformer_assets/img/grass.png')

        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    blob = Enemy(col_count * tile_size, row_count * tile_size + 15)
                    blob_group.add(blob)
                if tile == 4:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                if tile == 5:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                if tile == 6:                    
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)
                if tile == 7:
                    coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    coin_group.add(coin)
                if tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])



class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('platformer_assets/img/blob.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('platformer_assets/img/platform.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_counter = 0
        self.move_direction = 1
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 64:
            self.move_direction *= -1
            self.move_counter *= -1


class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('platformer_assets/img/lava.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('platformer_assets/img/coin.png')
        self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('platformer_assets/img/exit.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y



player = Player(100, screen_height - 130)

blob_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()

#create dummy coin for showing the score
score_coin = Coin(tile_size // 2, tile_size // 2)
coin_group.add(score_coin)


#load in level data and create world
if path.exists(f'platformer_assets/level{level}_data'):
    pickle_in = open(f'platformer_assets/level{level}_data', 'rb')
    world_data = pickle.load(pickle_in)
world = World(world_data)

#create buttons
restart_button = Button(screen_width // 2 - 50, screen_height // 2 + 125, restart_img)
start_button = Button(
    center_x - spacing - start_img.get_width() // 2,
    button_y,
    start_img
)

exit_button = Button(
    center_x + spacing - exit_img.get_width() // 2,
    button_y,
    exit_img
)

leaderboard_button = Button(leaderboard_x, leaderboard_y, leaderboard_img)

exit_img_small = pygame.transform.scale(exit_img, (150, 60))
back_button = Button(screen_width // 2 - 75, screen_height - 150, exit_img_small)



run = True
while run:
    
    clock.tick(fps)

    if main_menu:
        screen.blit(menu_bg, (0, 0))

        # --- TITLE ---
        draw_text("PIXEL ASCENT", title_font, blue, center_x - 350, button_y - 260)

        # --- CONTROLS TEXT ---
        draw_text("Controls:", font_score, white, 20, screen_height - 180, black)
        draw_text("A / D or LEFT / RIGHT arrow keys = Move", font_score, white, 20, screen_height - 150, black)
        draw_text("SPACE = Jump", font_score, white, 20, screen_height - 120, black)
        draw_text("R = Restart", font_score, white, 20, screen_height - 90, black)
        draw_text("ESC = Menu", font_score, white, 20, screen_height - 60, black)

        # --- BUTTONS ---
        if exit_button.draw():
            run = False

        if start_button.draw():
            main_menu = False
            start_time = pytime.time()
            timer_running = True

        if leaderboard_button.draw():
            main_menu = False
            leaderboard_menu = True
    
    elif leaderboard_menu:
        screen.blit(menu_bg, (0, 0))

        leaderboard = load_leaderboard()

        draw_text("LEADERBOARD", font, blue, center_x - 200, 100)

        y = 200
        for entry in leaderboard:
            text = f"{entry['name']} - {entry['time']:.2f}"
            text_width = font_score.size(text)[0]

            draw_text(text, font_score, black,
                    center_x - text_width // 2, y)

            y += 40

        if back_button.draw():
            leaderboard_menu = False
            main_menu = True


    else:
        screen.blit(bg_img, (0, 0))
        screen.blit(sun_img, (100, 100))

        world.draw()

        if game_over == 0:
            blob_group.update()
            platform_group.update()
            #update score
            #check for collision with coins
            if pygame.sprite.spritecollide(player, coin_group, True):
                score += 1
                coin_fx.play()
            draw_text('X ' + str(score), font_score, white, tile_size - 10, 10)
            draw_text('Level ' + str(level), font_score, white, tile_size + 50, 10)

        
        blob_group.draw(screen)
        platform_group.draw(screen)
        lava_group.update()
        lava_group.draw(screen)
        exit_group.update()
        exit_group.draw(screen)
        coin_group.update()
        coin_group.draw(screen)

        game_over = player.update(game_over)

        #if player has died
        if game_over == -1:
            if timer_running:
                final_time = pytime.time() - start_time
                timer_running = False
            if not entering_name and restart_button.draw():
                world_data = []
                world = reset_level(level)
                game_over = 0
                score = 0

                start_time = pytime.time() - final_time
                timer_running = True

        #if player has completed the level
        if game_over == 1:
            #reset level and go to next level
            level += 1
            if level <= max_levels:
                #reset level
                world_data = []
                world = reset_level(level)
                game_over = 0
            else:
                if timer_running:
                    final_time = pytime.time() - start_time
                    timer_running = False

                    leaderboard = sorted(load_leaderboard(), key=lambda x: x["time"])
                    best_time = leaderboard[0]["time"] if leaderboard else None

                    if best_time is None or final_time < best_time:
                        entering_name = True

                draw_text('YOU WIN!', font, blue, (screen_width // 2) - 150, screen_height // 2)
                draw_text(f'Final Time: {final_time:.2f}', font_score, white, (screen_width // 2) - 100, screen_height // 2 + 80)
                if entering_name:
                    draw_text("NEW BEST TIME!", font, blue,
                            (screen_width // 2) - 200, screen_height // 2 - 100)

                    draw_text("Enter Name:", font_score, white,
                            (screen_width // 2) - 100, screen_height // 2 + 140)

                    draw_text(player_name, font_score, white,
                            (screen_width // 2) - 100, screen_height // 2 + 180)
                if not entering_name and restart_button.draw():
                    level = 1
                    #reset level
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0   

                    start_time = pytime.time()
                    timer_running = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        # --- NAME INPUT SYSTEM ---
        if entering_name and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                leaderboard = load_leaderboard()

                # remove ALL entries with same name
                leaderboard = [entry for entry in leaderboard if entry["name"] != player_name]

                # add the new score
                leaderboard.append({"name": player_name, "time": final_time})

                # sort and keep top 5
                leaderboard = sorted(leaderboard, key=lambda x: x["time"])[:5]

                save_leaderboard(leaderboard)

                entering_name = False
                player_name = ""


            elif event.key == pygame.K_BACKSPACE:
                player_name = player_name[:-1]

            else:
                if len(player_name) < 10:
                    if event.unicode.isalnum():
                        player_name += event.unicode
            

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                main_menu = True
                leaderboard_menu = False

                # reset game state
                level = 1
                world_data = []
                world = reset_level(level)
                game_over = 0
                score = 0

                timer_running = False
            if event.key == pygame.K_r and main_menu == False and not entering_name:

                # restart level
                world_data = []
                world = reset_level(level)
                game_over = 0
                score = 0

                # resume timer (only if it was stopped)
                if not timer_running:
                    start_time = pytime.time() - final_time
                    timer_running = True

    pygame.display.update()

pygame.quit()