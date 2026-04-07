import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Game Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 150, 255)
DARK_BLUE = (30, 80, 150)
YELLOW = (255, 255, 50)
ORANGE = (255, 150, 50)
BROWN = (139, 69, 19)
GRAY = (100, 100, 100)
LIGHT_GRAY = (150, 150, 150)
DARK_GRAY = (50, 50, 50)
SKIN = (255, 200, 150)
SKIN_DARK = (200, 150, 100)

class HumanCharacter(pygame.sprite.Sprite):
    """Base class for human characters (player and enemies)"""
    def __init__(self, x, y, color, is_player=False):
        super().__init__()
        self.is_player = is_player
        self.color = color
        
        # Create human sprite (40x40 pixel art style)
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # Stats
        self.health = 100
        self.max_health = 100
        self.speed = 4
        self.damage = 20
        
        # Cover system - MUST be defined BEFORE draw_human()
        self.in_cover = False
        self.cover_object = None
        self.cover_direction = None
        
        # Combat
        self.last_shot = 0
        self.shoot_delay = 400  # milliseconds
        self.ammo = 30
        self.max_ammo = 30
        self.is_reloading = False
        self.reload_start = 0
        
        # Movement
        self.target_x = x
        self.target_y = y
        self.moving = False
        
        # Draw human character (AFTER all attributes are defined)
        self.draw_human()
        
    def draw_human(self):
        """Draw a detailed human character"""
        self.image.fill((0, 0, 0, 0))  # Clear
        
        # Body (torso)
        body_rect = pygame.Rect(12, 15, 16, 20)
        pygame.draw.rect(self.image, self.color, body_rect)
        
        # Head
        head_center = (20, 12)
        pygame.draw.circle(self.image, SKIN, head_center, 8)
        
        # Helmet/hat for soldiers
        if not self.is_player:
            pygame.draw.rect(self.image, DARK_GRAY, (12, 4, 16, 8))
        
        # Eyes
        eye_color = BLACK if self.is_player else RED
        pygame.draw.circle(self.image, eye_color, (16, 11), 2)
        pygame.draw.circle(self.image, eye_color, (24, 11), 2)
        
        # Arms
        pygame.draw.line(self.image, SKIN, (12, 20), (8, 28), 4)
        pygame.draw.line(self.image, SKIN, (28, 20), (32, 28), 4)
        
        # Gun (if not in cover or aiming)
        if not self.in_cover:
            pygame.draw.rect(self.image, GRAY, (28, 22, 12, 4))
            pygame.draw.rect(self.image, DARK_GRAY, (36, 20, 6, 8))
        
        # Legs
        pygame.draw.line(self.image, DARK_BLUE, (15, 35), (12, 40), 4)
        pygame.draw.line(self.image, DARK_BLUE, (25, 35), (28, 40), 4)
        
    def update(self):
        if self.moving and not self.in_cover:
            # Move towards target
            dx = self.target_x - self.rect.centerx
            dy = self.target_y - self.rect.centery
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > self.speed:
                if distance > 0:
                    self.rect.centerx += (dx / distance) * self.speed
                    self.rect.centery += (dy / distance) * self.speed
            else:
                self.rect.centerx = self.target_x
                self.rect.centery = self.target_y
                self.moving = False
                
        # Update reload
        if self.is_reloading:
            if pygame.time.get_ticks() - self.reload_start > 2000:
                self.ammo = self.max_ammo
                self.is_reloading = False
                
    def move_to(self, x, y):
        if not self.in_cover:
            self.target_x = max(20, min(x, SCREEN_WIDTH - 20))
            self.target_y = max(20, min(y, SCREEN_HEIGHT - 20))
            self.moving = True
            
    def take_cover(self, cover):
        """Take cover behind an object"""
        if not self.in_cover:
            self.in_cover = True
            self.cover_object = cover
            # Move behind cover
            self.rect.centerx = cover.rect.centerx
            self.rect.centery = cover.rect.top - 20
            self.cover_direction = "down"
            # Redraw with gun hidden
            self.draw_human()
            
    def leave_cover(self):
        """Leave cover position"""
        self.in_cover = False
        self.cover_object = None
        self.cover_direction = None
        # Redraw with gun visible
        self.draw_human()
        
    def shoot(self, target_x, target_y):
        if self.ammo > 0 and not self.is_reloading:
            now = pygame.time.get_ticks()
            if now - self.last_shot > self.shoot_delay:
                self.last_shot = now
                self.ammo -= 1
                
                # Calculate direction
                dx = target_x - self.rect.centerx
                dy = target_y - self.rect.centery
                distance = math.sqrt(dx**2 + dy**2)
                if distance > 0:
                    dx /= distance
                    dy /= distance
                    
                return Bullet(self.rect.centerx, self.rect.centery, dx, dy, self.damage)
        return None
        
    def reload(self):
        if self.ammo < self.max_ammo and not self.is_reloading:
            self.is_reloading = True
            self.reload_start = pygame.time.get_ticks()
            
    def take_damage(self, amount):
        # Reduce damage if in cover
        if self.in_cover:
            amount *= 0.5
        self.health -= amount
        return self.health <= 0
        
    def draw_health_bar(self, screen):
        bar_width = 40
        bar_height = 6
        health_percentage = self.health / self.max_health
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - 10
        
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, bar_width * health_percentage, bar_height))
        
        # Draw name/rank
        if self.is_player:
            font = pygame.font.Font(None, 16)
            name_text = font.render("OPERATOR", True, WHITE)
            screen.blit(name_text, (self.rect.centerx - 25, self.rect.bottom + 2))
            
    def draw(self, screen):
        """Draw the character on screen"""
        screen.blit(self.image, self.rect)
        self.draw_health_bar(screen)

class EnemySoldier(HumanCharacter):
    """Enemy AI soldier"""
    def __init__(self, x, y):
        super().__init__(x, y, RED, is_player=False)
        self.agro_range = 300
        self.shoot_range = 250
        self.patrol_points = []
        self.current_patrol = 0
        self.state = "patrol"  # patrol, chase, attack, cover
        self.last_known_player_pos = None
        
    def update_ai(self, player_pos, covers):
        if self.health <= 0:
            return None
            
        distance_to_player = math.sqrt((player_pos[0] - self.rect.centerx)**2 + 
                                      (player_pos[1] - self.rect.centery)**2)
        
        # State machine
        if distance_to_player < self.agro_range:
            self.state = "attack"
            self.last_known_player_pos = player_pos
            
            # Try to take cover if available and not in cover
            if not self.in_cover and distance_to_player < 200:
                nearest_cover = self.find_nearest_cover(covers)
                if nearest_cover:
                    self.take_cover(nearest_cover)
                    
            # Shoot at player
            if distance_to_player < self.shoot_range:
                bullet = self.shoot(player_pos[0], player_pos[1])
                if bullet:
                    return bullet
                    
            # Move towards player if not in cover
            if not self.in_cover:
                self.move_to(player_pos[0], player_pos[1])
        else:
            self.state = "patrol"
            if self.in_cover:
                self.leave_cover()
                
        # Update movement
        self.update()
        return None
        
    def find_nearest_cover(self, covers):
        nearest = None
        min_distance = float('inf')
        for cover in covers:
            distance = math.sqrt((cover.rect.centerx - self.rect.centerx)**2 + 
                               (cover.rect.centery - self.rect.centery)**2)
            if distance < min_distance and distance < 150:
                min_distance = distance
                nearest = cover
        return nearest

class Cover(pygame.sprite.Sprite):
    """Cover objects like walls, crates, barriers"""
    def __init__(self, x, y, width, height, cover_type="crate"):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.cover_type = cover_type
        self.hp = 200 if cover_type == "wall" else 100
        
        # Draw cover based on type
        if cover_type == "crate":
            self.image.fill(BROWN)
            # Wood texture
            for i in range(3):
                pygame.draw.line(self.image, (100, 50, 20), (0, i*15), (width, i*15), 2)
        elif cover_type == "wall":
            self.image.fill(DARK_GRAY)
            pygame.draw.rect(self.image, GRAY, (0, 0, width, height), 3)
        elif cover_type == "barrier":
            self.image.fill(LIGHT_GRAY)
            # Sandbag effect
            for i in range(4):
                pygame.draw.ellipse(self.image, (180, 180, 150), (i*20, 0, 15, height))
                
    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.kill()
            return True
        return False

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy, damage):
        super().__init__()
        self.image = pygame.Surface((6, 3))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.dx = dx
        self.dy = dy
        self.damage = damage
        self.speed = 20
        self.trail = []
        
    def update(self):
        # Store trail for effect
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 5:
            self.trail.pop(0)
            
        self.rect.x += self.dx * self.speed
        self.rect.y += self.dy * self.speed
        
        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
            self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()
            
    def draw_trail(self, screen):
        for i, pos in enumerate(self.trail):
            alpha = 255 - (i * 50)
            try:
                pygame.draw.circle(screen, (255, 255, 100), pos, 2)
            except:
                pass

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.images = []
        for i in range(8):
            img = pygame.Surface((30, 30), pygame.SRCALPHA)
            radius = 15 - i
            if radius > 0:
                pygame.draw.circle(img, ORANGE, (15, 15), radius)
                pygame.draw.circle(img, RED, (15, 15), radius-2)
            self.images.append(img)
        self.index = 0
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.counter = 0
        
    def update(self):
        self.counter += 1
        if self.counter % 3 == 0:
            self.index += 1
            if self.index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.index]

class TacticalGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("COVER FIRE - Tactical Shooter")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 24)
        
        # Game state
        self.score = 0
        self.wave = 1
        self.kills = 0
        
        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.covers = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        
        # Create player
        self.player = HumanCharacter(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, BLUE, is_player=True)
        self.all_sprites.add(self.player)
        
        # Create cover objects
        self.create_map()
        
        # Create enemies
        self.spawn_enemies()
        
        # Crosshair
        pygame.mouse.set_visible(False)
        
        # UI
        self.show_controls = True
        self.control_timer = 300  # Show controls for 5 seconds
        
    def create_map(self):
        """Create tactical map with cover positions"""
        # Left side cover
        cover1 = Cover(100, SCREEN_HEIGHT - 150, 80, 40, "crate")
        cover2 = Cover(100, SCREEN_HEIGHT - 250, 80, 40, "crate")
        cover3 = Cover(100, SCREEN_HEIGHT - 350, 80, 40, "crate")
        
        # Right side cover
        cover4 = Cover(SCREEN_WIDTH - 180, SCREEN_HEIGHT - 150, 80, 40, "crate")
        cover5 = Cover(SCREEN_WIDTH - 180, SCREEN_HEIGHT - 250, 80, 40, "crate")
        cover6 = Cover(SCREEN_WIDTH - 180, SCREEN_HEIGHT - 350, 80, 40, "crate")
        
        # Center cover
        cover7 = Cover(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2, 100, 50, "barrier")
        cover8 = Cover(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 - 100, 100, 50, "barrier")
        
        # Walls for side protection
        left_wall = Cover(20, 100, 30, SCREEN_HEIGHT - 200, "wall")
        right_wall = Cover(SCREEN_WIDTH - 50, 100, 30, SCREEN_HEIGHT - 200, "wall")
        
        covers = [cover1, cover2, cover3, cover4, cover5, cover6, cover7, cover8, left_wall, right_wall]
        for cover in covers:
            self.all_sprites.add(cover)
            self.covers.add(cover)
            
    def spawn_enemies(self):
        """Spawn enemy soldiers based on wave"""
        enemy_count = min(3 + self.wave // 2, 8)
        
        for i in range(enemy_count):
            # Spawn from top or sides
            side = random.choice(['top', 'left', 'right'])
            if side == 'top':
                x = random.randint(50, SCREEN_WIDTH - 50)
                y = random.randint(50, 200)
            elif side == 'left':
                x = random.randint(20, 150)
                y = random.randint(100, SCREEN_HEIGHT - 200)
            else:
                x = random.randint(SCREEN_WIDTH - 150, SCREEN_WIDTH - 20)
                y = random.randint(100, SCREEN_HEIGHT - 200)
                
            enemy = EnemySoldier(x, y)
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)
            
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.player.reload()
                elif event.key == pygame.K_c:
                    # Toggle cover (if near cover)
                    nearest_cover = self.get_nearest_cover()
                    if nearest_cover and not self.player.in_cover:
                        self.player.take_cover(nearest_cover)
                    elif self.player.in_cover:
                        self.player.leave_cover()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_h:
                    self.show_controls = not self.show_controls
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    bullet = self.player.shoot(event.pos[0], event.pos[1])
                    if bullet:
                        self.all_sprites.add(bullet)
                        self.bullets.add(bullet)
                        
        # Handle movement
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        
        if not self.player.in_cover:
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx += 1
                
            if dx != 0 or dy != 0:
                # Normalize diagonal
                if dx != 0 and dy != 0:
                    dx *= 0.707
                    dy *= 0.707
                self.player.move_to(self.player.rect.centerx + dx * 50, 
                                   self.player.rect.centery + dy * 50)
                                   
    def get_nearest_cover(self):
        """Find nearest cover to player"""
        nearest = None
        min_distance = float('inf')
        for cover in self.covers:
            distance = math.sqrt((cover.rect.centerx - self.player.rect.centerx)**2 +
                               (cover.rect.centery - self.player.rect.centery)**2)
            if distance < min_distance and distance < 100:
                min_distance = distance
                nearest = cover
        return nearest
        
    def update(self):
        # Update player
        self.player.update()
        
        # Update enemies AI
        new_bullets = []
        for enemy in self.enemies:
            bullet = enemy.update_ai((self.player.rect.centerx, self.player.rect.centery), self.covers)
            if bullet:
                new_bullets.append(bullet)
                
        for bullet in new_bullets:
            self.all_sprites.add(bullet)
            self.bullets.add(bullet)
            
        # Update bullets
        self.bullets.update()
        
        # Check bullet collisions with player
        hits = pygame.sprite.spritecollide(self.player, self.bullets, True)
        for hit in hits:
            if self.player.take_damage(hit.damage):
                self.game_over()
                return
                
        # Check bullet collisions with enemies
        for enemy in self.enemies.copy():
            hits = pygame.sprite.spritecollide(enemy, self.bullets, True)
            for hit in hits:
                if enemy.take_damage(hit.damage):
                    self.kills += 1
                    self.score += 100
                    explosion = Explosion(enemy.rect.centerx, enemy.rect.centery)
                    self.all_sprites.add(explosion)
                    self.explosions.add(explosion)
                    enemy.kill()
                    self.enemies.remove(enemy)
                    
        # Check bullet collisions with cover
        hits = pygame.sprite.groupcollide(self.covers, self.bullets, False, True)
        for cover, bullets in hits.items():
            cover.take_damage(sum(b.damage for b in bullets))
            
        # Update explosions
        self.explosions.update()
        
        # Check if wave is complete
        if len(self.enemies) == 0:
            self.wave += 1
            self.spawn_enemies()
            # Heal player between waves
            self.player.health = min(self.player.health + 20, self.player.max_health)
            self.player.ammo = self.player.max_ammo
            
        # Update control timer
        if self.control_timer > 0:
            self.control_timer -= 1
            
    def draw_crosshair(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Dynamic crosshair based on cover status
        color = GREEN if self.player.in_cover else WHITE
        size = 15 if self.player.in_cover else 10
        
        pygame.draw.circle(self.screen, color, (mouse_x, mouse_y), size, 2)
        pygame.draw.line(self.screen, color, (mouse_x - size, mouse_y), (mouse_x - 5, mouse_y), 2)
        pygame.draw.line(self.screen, color, (mouse_x + 5, mouse_y), (mouse_x + size, mouse_y), 2)
        pygame.draw.line(self.screen, color, (mouse_x, mouse_y - size), (mouse_x, mouse_y - 5), 2)
        pygame.draw.line(self.screen, color, (mouse_x, mouse_y + 5), (mouse_x, mouse_y + size), 2)
        
        # Center dot
        pygame.draw.circle(self.screen, RED, (mouse_x, mouse_y), 2)
        
    def draw_hud(self):
        # Score and wave
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        wave_text = self.font.render(f"Wave: {self.wave}", True, WHITE)
        self.screen.blit(wave_text, (10, 50))
        
        kills_text = self.font.render(f"Kills: {self.kills}", True, WHITE)
        self.screen.blit(kills_text, (10, 90))
        
        # Ammo
        if self.player.is_reloading:
            ammo_text = self.font.render("RELOADING...", True, RED)
        else:
            ammo_text = self.font.render(f"Ammo: {self.player.ammo}/{self.player.max_ammo}", True, WHITE)
        self.screen.blit(ammo_text, (SCREEN_WIDTH - 150, 10))
        
        # Health bar
        pygame.draw.rect(self.screen, RED, (SCREEN_WIDTH // 2 - 100, 10, 200, 25))
        health_percentage = self.player.health / self.player.max_health
        pygame.draw.rect(self.screen, GREEN, (SCREEN_WIDTH // 2 - 100, 10, 200 * health_percentage, 25))
        health_text = self.font.render(f"HP: {int(self.player.health)}", True, WHITE)
        self.screen.blit(health_text, (SCREEN_WIDTH // 2 - 30, 12))
        
        # Cover status
        if self.player.in_cover:
            cover_text = self.font.render("IN COVER - Damage Reduced", True, GREEN)
            self.screen.blit(cover_text, (SCREEN_WIDTH // 2 - 150, 45))
            
        # Controls hint
        if self.show_controls:
            controls = [
                "WASD: Move",
                "Mouse: Aim",
                "Left Click: Shoot",
                "R: Reload",
                "C: Take/Leave Cover",
                "H: Hide Controls"
            ]
            y_offset = SCREEN_HEIGHT - 120
            for i, control in enumerate(controls):
                text = self.small_font.render(control, True, LIGHT_GRAY)
                self.screen.blit(text, (10, y_offset + i * 20))
                
    def game_over(self):
        pygame.mouse.set_visible(True)
        self.screen.fill(BLACK)
        
        game_over_text = self.big_font.render("MISSION FAILED", True, RED)
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        kills_text = self.font.render(f"Enemies Eliminated: {self.kills}", True, WHITE)
        wave_text = self.font.render(f"Wave Reached: {self.wave}", True, WHITE)
        restart_text = self.font.render("Press R to restart or ESC to quit", True, WHITE)
        
        self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(kills_text, (SCREEN_WIDTH // 2 - kills_text.get_width() // 2, SCREEN_HEIGHT // 2 + 40))
        self.screen.blit(wave_text, (SCREEN_WIDTH // 2 - wave_text.get_width() // 2, SCREEN_HEIGHT // 2 + 80))
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 150))
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.__init__()
                        return
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                        return
                        
    def draw_background(self):
        # Fill background
        self.screen.fill(BLACK)
        
        # Draw tactical grid
        for x in range(0, SCREEN_WIDTH, 50):
            pygame.draw.line(self.screen, (30, 30, 30), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 50):
            pygame.draw.line(self.screen, (30, 30, 30), (0, y), (SCREEN_WIDTH, y))
            
        # Draw "danger zone" indicators
        if self.wave > 3:
            pygame.draw.rect(self.screen, (50, 0, 0), (0, 0, SCREEN_WIDTH, 50), 3)
            
    def draw(self):
        self.draw_background()
        
        # Draw covers
        for cover in self.covers:
            self.screen.blit(cover.image, cover.rect)
            
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)
            
        # Draw player
        self.player.draw(self.screen)
        
        # Draw explosions
        for explosion in self.explosions:
            self.screen.blit(explosion.image, explosion.rect)
            
        # Draw bullets
        for bullet in self.bullets:
            self.screen.blit(bullet.image, bullet.rect)
            bullet.draw_trail(self.screen)
        
        # Draw HUD
        self.draw_hud()
        
        # Draw crosshair
        self.draw_crosshair()
        
        pygame.display.flip()
        
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit()

# Run the game
if __name__ == "__main__":
    game = TacticalGame()
    game.run()