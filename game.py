import random
import os
from queue import PriorityQueue
import pygame

# Inicializando o Pygame
pygame.init()

# Definindo constantes
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 350
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
BLOCK_SIZE = 40
PACMAN_SIZE = 25
GHOST_SIZE = 40
FPS = 80

# Labirinto representado como uma matriz de caracteres
# W: Parede, E: Espaço vazio, .: Pontos brancos
LABYRINTH = [
    "WWWWWWWWWWWWWWWWWW",
    "W................W",
    "W.WWW..WWWWWW..W.W",
    "W.W............W.W",
    "W.WWWw.WWW..W....W",
    "W...........W..W.W",
    "WWWW...WWW.WW..W.W",
    "W................W",
    "WWWWWWWWWWWWWWWWWW"
]

# Diretório onde está a imagem do Pac-Man e dos fantasmas
IMAGE_DIR = os.path.join(os.getcwd(), "images")

# Criando a janela do jogo
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pac-Man")

# Carregando imagem do Pac-Man
pacman_img = pygame.image.load(os.path.join(IMAGE_DIR, "pacman.png"))
pacman_img = pygame.transform.scale(pacman_img, (PACMAN_SIZE, PACMAN_SIZE))

# Carregando imagem dos fantasmas
ghost_img = pygame.image.load(os.path.join(IMAGE_DIR, "ghost.png"))
ghost_img = pygame.transform.scale(ghost_img, (GHOST_SIZE, GHOST_SIZE))

# Carregando imagens de parede
wall_img = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
wall_img.fill(WHITE)

# Função para obter a dificuldade selecionada pelo jogador
def get_selected_difficulty():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if 275 < mouse_x < 425:
                    if 125 < mouse_y < 175:
                        return "Fácil"
                    elif 175 < mouse_y < 225:
                        return "Médio"
                    elif 225 < mouse_y < 275:
                        return "Difícil"

        pygame.display.flip()

# Definindo a classe do jogador (Pac-Man)
class Pacman(pygame.sprite.Sprite):
    def __init__(self, walls):  # Altere _init_ para __init__
        super().__init__()
        self.image = pacman_img
        self.rect = self.image.get_rect()
        self.rect.center = self.get_valid_start_position(walls)
        self.speed = 5
        self.direction = None
        self.score = 0
        self.font = pygame.font.Font(None, 24)

    def get_valid_start_position(self, walls):
        while True:
            x = random.randint(0, SCREEN_WIDTH - PACMAN_SIZE)
            y = random.randint(0, SCREEN_HEIGHT - PACMAN_SIZE)
            rect = pygame.Rect(x, y, PACMAN_SIZE, PACMAN_SIZE)
            if not any(rect.colliderect(wall_rect) for wall_rect in walls):
                return rect.center

    def update(self, walls):
        if self.direction == "UP":
            self.rect.y -= self.speed
        elif self.direction == "DOWN":
            self.rect.y += self.speed
        elif self.direction == "LEFT":
            self.rect.x -= self.speed
        elif self.direction == "RIGHT":
            self.rect.x += self.speed

        # Verificando colisões com as paredes e bordas da tela
        for wall_rect in walls:
            if self.rect.colliderect(wall_rect):
                if self.direction == "UP":
                    self.rect.top = wall_rect.bottom  # Ajuste para deslizar ao longo da parede
                elif self.direction == "DOWN":
                    self.rect.bottom = wall_rect.top  # Ajuste para deslizar ao longo da parede
                elif self.direction == "LEFT":
                    self.rect.left = wall_rect.right  # Ajuste para deslizar ao longo da parede
                elif self.direction == "RIGHT":
                    self.rect.right = wall_rect.left  # Ajuste para deslizar ao longo da parede

        # Impedindo que o Pac-Man saia da tela
        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - PACMAN_SIZE))
        self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT - PACMAN_SIZE))

        # Atualizando a pontuação com base no tempo de sobrevivência
        self.score += 1

    def draw_score(self, screen):
        # Desenhar o fundo da pontuação
        score_bg = pygame.Rect(10, 10, 150, 20)
        pygame.draw.rect(screen, BLACK, score_bg)

        score_text = self.font.render(f"Pontuação: {self.score}", True, YELLOW)
        screen.blit(score_text, (20, 15))

# Definindo a classe dos fantasmas
class Ghost(pygame.sprite.Sprite):
    def __init__(self, walls, target):
        super().__init__()
        self.image = ghost_img
        self.rect = self.image.get_rect()
        self.rect.center = self.get_valid_start_position(walls)
        self.speed = 1  # Velocidade reduzida para 1
        self.path = []
        self.target = target
        self.path_update_delay = 10  # Atraso antes de atualizar o caminho
        self.path_update_counter = 0

    def get_valid_start_position(self, walls):
        while True:
            x = random.randint(0, SCREEN_WIDTH - GHOST_SIZE)
            y = random.randint(0, SCREEN_HEIGHT - GHOST_SIZE)
            rect = pygame.Rect(x, y, GHOST_SIZE, GHOST_SIZE)
            if not any(rect.colliderect(wall_rect) for wall_rect in walls):
                return rect.center

    def update(self, walls):
        self.path_update_counter += 1
        if self.path_update_counter >= self.path_update_delay:
            self.move_towards_target(walls)
            self.path_update_counter = 0

    def move_towards_target(self, walls):
        if self.path:
            self.rect.center = self.path.pop(0)
        else:
            self.path = self.find_path(walls)

    def find_path(self, walls):
        start = (self.rect.centerx // BLOCK_SIZE, self.rect.centery // BLOCK_SIZE)
        end = (self.target.rect.centerx // BLOCK_SIZE, self.target.rect.centery // BLOCK_SIZE)
        open_set = PriorityQueue()
        open_set.put(start, 0)
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, end)}

        while not open_set.empty():
            current = open_set.get()

            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return [((x + 0.5) * BLOCK_SIZE, (y + 0.5) * BLOCK_SIZE) for x, y in path[::-1]]

            for neighbor in self.get_neighbors(current):
                tentative_g_score = g_score[current] + 1

                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, end)
                    open_set.put(neighbor, f_score[neighbor])

        return []

    def get_neighbors(self, pos):
        x, y = pos
        neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        return [neighbor for neighbor in neighbors if 0 <= neighbor[0] < len(LABYRINTH[0]) and
                0 <= neighbor[1] < len(LABYRINTH) and LABYRINTH[neighbor[1]][neighbor[0]] != 'W']

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

# Função para exibir o menu de seleção de dificuldade
def show_difficulty_menu():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        screen.fill(BLACK)
        font = pygame.font.Font(None, 36)
        title_text = font.render("Selecione a Dificuldade", True, YELLOW)
        screen.blit(title_text, (200, 50))

        # Desenhando opções de dificuldade
        easy_text = font.render("Fácil", True, YELLOW)
        screen.blit(easy_text, (300, 125))

        medium_text = font.render("Médio", True, YELLOW)
        screen.blit(medium_text, (300, 175))

        hard_text = font.render("Difícil", True, YELLOW)
        screen.blit(hard_text, (300, 225))

        pygame.display.flip()

        difficulty = get_selected_difficulty()
        if difficulty:
            return difficulty

# Criando o objeto Pac-Man
difficulty = show_difficulty_menu()
if difficulty == "Fácil":
    num_ghosts = 1
elif difficulty == "Médio":
    num_ghosts = 2
else:
    num_ghosts = 3

# Criando os objetos de parede
walls = []
points = []  # Lista para armazenar as posições dos pontos brancos
for y, row in enumerate(LABYRINTH):
    for x, char in enumerate(row):
        if char == 'W':
            wall_rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            walls.append(wall_rect)
        elif char == '.':
            points.append((x * BLOCK_SIZE + BLOCK_SIZE // 2, y * BLOCK_SIZE + BLOCK_SIZE // 2))

# Criando o objeto Pac-Man
pacman = Pacman(walls)

# Criando os fantasmas
ghosts = [Ghost(walls, pacman) for _ in range(num_ghosts)]

# Criando o loop principal do jogo
clock = pygame.time.Clock()
running = True
game_over = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Lidando com as entradas do teclado para mover o Pac-Man
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                pacman.direction = "UP"
            elif event.key == pygame.K_DOWN:
                pacman.direction = "DOWN"
            elif event.key == pygame.K_LEFT:
                pacman.direction = "LEFT"
            elif event.key == pygame.K_RIGHT:
                pacman.direction = "RIGHT"
            elif event.key == pygame.K_r and game_over:  # Reiniciar o jogo com a tecla R
                game_over = False
                pacman.score = 0  # Reiniciar a pontuação do Pac-Man
                # Restaurar os pontos brancos
                LABYRINTH = [
                    "WWWWWWWWWWWWWWWWWW",
                    "W................W",
                    "W.WWW..WWWWWW..W.W",
                    "W.W............W.W",
                    "W.WWWw.WWW..W....W",
                    "W...........W..W.W",
                    "WWWW...WWW.WW..W.W",
                    "W................W",
                    "WWWWWWWWWWWWWWWWWW"
                ]
                # Recolocar os pontos na matriz do labirinto
                points = []
                for y, row in enumerate(LABYRINTH):
                    for x, char in enumerate(row):
                        if char == '.':
                            points.append((x * BLOCK_SIZE + BLOCK_SIZE // 2, y * BLOCK_SIZE + BLOCK_SIZE // 2))

                # Reposicionar Pac-Man e fantasmas
                pacman.rect.center = pacman.get_valid_start_position(walls)
                for ghost in ghosts:
                    ghost.rect.center = ghost.get_valid_start_position(walls)

        elif event.type == pygame.KEYUP:
            pacman.direction = None

    if not game_over:
        pacman.update(walls)
        for ghost in ghosts:
            ghost.update(walls)

        # Verificando colisão entre Pac-Man e fantasmas
        for ghost in ghosts:
            if pacman.rect.colliderect(ghost.rect):
                game_over = True

        # Verificando colisão entre Pac-Man e pontos brancos
        for point in points[:]:  # Utilizamos uma cópia da lista para poder modificar a original
            point_rect = pygame.Rect(point[0] - 2, point[1] - 2, 4, 4)  # Bolinhas são consideravelmente menores
            if pacman.rect.colliderect(point_rect):
                pacman.score += 10  # Aumenta a pontuação
                # Remover ponto da lista de pontos e do labirinto
                points.remove(point)
                x, y = point[0] // BLOCK_SIZE, point[1] // BLOCK_SIZE
                row = LABYRINTH[y]
                LABYRINTH[y] = row[:x] + ' ' + row[x + 1:]

    screen.fill(BLACK)
    for y, row in enumerate(LABYRINTH):
        for x, char in enumerate(row):
            if char == 'W':
                pygame.draw.rect(screen, WHITE, (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
            elif char == '.':
                pygame.draw.circle(screen, WHITE, (x * BLOCK_SIZE + BLOCK_SIZE // 2, y * BLOCK_SIZE + BLOCK_SIZE // 2),
                                   2)
    screen.blit(pacman.image, pacman.rect)
    for ghost in ghosts:
        screen.blit(ghost.image, ghost.rect)

    # Exibindo a pontuação na tela
    pacman.draw_score(screen)

    if game_over:
        # Desenhar a caixa de diálogo do menu
        dialog_box = pygame.Rect(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        pygame.draw.rect(screen, BLACK, dialog_box)
        pygame.draw.rect(screen, YELLOW, dialog_box, 3)

        text = pacman.font.render("GAME OVER", True, YELLOW)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(text, text_rect)

        text = pacman.font.render(f"Pontuação: {pacman.score}", True, YELLOW)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(text, text_rect)

        text = pacman.font.render("Pressione 'R' para reiniciar.", True, YELLOW)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        screen.blit(text, text_rect)

    pygame.display.flip()
    clock.tick(FPS)

# Finalizando o Pygame
pygame.quit()
