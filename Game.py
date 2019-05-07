"""
Platformer Game
"""
import arcade

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Platformer"

# These numbers represent "states" that the game can be in.
INSTRUCTIONS_PAGE_0 = 0
INSTRUCTIONS_PAGE_1 = 1
GAME_RUNNING = 2
YOU_LOST = 3
YOU_WON = 4
MAX_LEVEL = 10

# Constants used to scale our sprites from their original size
CHARACTER_SCALING = 0.8
TILE_SCALING = 0.4
COIN_SCALING = 0.4
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = (SPRITE_PIXEL_SIZE * TILE_SCALING)

# Movement speed of player, in pixels per frame
PLAYER_MOVEMENT_SPEED = 8
GRAVITY = 1.2
PLAYER_JUMP_SPEED = 20

# How many pixels to keep as a minimum margin between the character
# and the edge of the screen.
LEFT_VIEWPORT_MARGIN = 200
RIGHT_VIEWPORT_MARGIN = 200
BOTTOM_VIEWPORT_MARGIN = 150
TOP_VIEWPORT_MARGIN = 100

PLAYER_START_X = 80
PLAYER_START_Y = 294

TEXTURE_LEFT = 0
TEXTURE_RIGHT = 1

class Player(arcade.Sprite):

    def __init__(self):
        super().__init__()

        # Load a left facing texture and a right facing texture.
        # mirrored=True will mirror the image we load.
        texture = arcade.load_texture("images/player_1/player_stand.png", mirrored=True, scale=CHARACTER_SCALING)
        self.textures.append(texture)
        texture = arcade.load_texture("images/player_1/player_stand.png", scale=CHARACTER_SCALING)
        self.textures.append(texture)

        # By default, face right.
        self.set_texture(TEXTURE_RIGHT)

    def update(self):
        self.center_x += self.change_x
        self.center_y += self.change_y

        # Figure out if we should face left or right
        if self.change_x < 0:
            self.set_texture(TEXTURE_LEFT)
        if self.change_x > 0:
            self.set_texture(TEXTURE_RIGHT)

        if self.left < 0:
            self.left = 0
        elif self.right > SCREEN_WIDTH - 1:
            self.right = SCREEN_WIDTH - 1

        if self.bottom < 0:
            self.bottom = 0
        elif self.top > SCREEN_HEIGHT - 1:
            self.top = SCREEN_HEIGHT - 1

class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self, width, height, title):

        # Call the parent class and set up the window
        super().__init__(width, height, title, resizable = True)

        # These are 'lists' that keep track of our sprites. Each sprite should
        # go into a list.
        self.hearts_list = None
        self.poisons_list = None
        self.coin_list = None
        self.wall_list = None
        self.foreground_list = None
        self.background_list = None
        self.dont_touch_list = None
        self.player_list = None

        # Separate variable that holds the player sprite
        self.player_sprite = None

        # Our physics engine
        self.physics_engine = None

        # STEP 1: Put each instruction page in an image. Make sure the image
        # matches the dimensions of the window, or it will stretch and look
        # ugly. You can also do something similar if you want a page between
        # each level.
        self.instructions = []
        texture = arcade.load_texture("images/instructions/1.png")
        self.instructions.append(texture)

        texture = arcade.load_texture("images/instructions/2.png")
        self.instructions.append(texture)
        
        texture = arcade.load_texture("images/instructions/GameOver.png")
        self.instructions.append(texture)
        
        texture = arcade.load_texture("images/instructions/YouWon.png")
        self.instructions.append(texture)
        
        # Used to keep track of our scrolling
        self.view_bottom = 0
        self.view_left = 0

        # Keep track of the score
        self.score = 0

        # Keep track of the Game State
        self.current_state = 0

        # Where is the right edge of the map?
        self.end_of_map = 0

        # Level
        self.level = 1

        # Load sounds
        self.collect_coin_sound = arcade.load_sound("sounds/coin1.wav")
        self.jump_sound = arcade.load_sound("sounds/jump1.wav")
        self.game_over = arcade.load_sound("sounds/gameover1.wav")

    def on_resize(self, width, height):
        """ This method is automatically called when the window is resized. """

        # Call the parent. Failing to do this will mess up the coordinates, and default to 0,0 at the center and the
        # edges being -1 to 1.
        super().on_resize(width, height)
        
    def setup(self, level):
        """ Set up the game here. Call this function to restart the game. """

        # Used to keep track of our scrolling
        self.view_bottom = 0
        self.view_left = 0

        # Keep track of the score
        if level == 1:
            self.score = 0
            self.health = 5
            self.level = 1

        # Create the Sprite lists
        self.player_list = arcade.SpriteList()
        self.foreground_list = arcade.SpriteList()
        self.background_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()
        self.poisons_list = arcade.SpriteList()
        self.hearts_list = arcade.SpriteList()
        
        # Set up the player, specifically placing it at these coordinates.
        self.player_sprite = Player()
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.player_list.append(self.player_sprite)

        # --- Load in a map from the tiled editor ---

        # Name of the layer in the file that has our platforms/walls
        platforms_layer_name = 'Platforms'
        # Name of the layer that has items for pick-up
        coins_layer_name = 'Coins'
        # Name of the layer that has items for foreground
        foreground_layer_name = 'Foreground'
        # Name of the layer that has items for background
        background_layer_name = 'Background'
        # Name of the layer that has items that poison us.
        poisons_layer_name = 'Poisons'
        # Name of the layer that has items we shouldn't touch
        dont_touch_layer_name = "Don't Touch"
        # Name of the layer that has items that increase health
        hearts_layer_name = 'Hearts'

        # Map name
        map_name = f"MapLevel{level}.tmx"
        # Read in the tiled map
        my_map = arcade.read_tiled_map(map_name, TILE_SCALING)

        # -- Walls
        # Grab the layer of items we can't move through
        map_array = my_map.layers_int_data[platforms_layer_name]

        # Calculate the right edge of the my_map in pixels
        self.end_of_map = len(map_array[0]) * GRID_PIXEL_SIZE

        # -- Background
        self.background_list = arcade.generate_sprites(my_map, background_layer_name, TILE_SCALING)

        # -- Foreground
        self.foreground_list = arcade.generate_sprites(my_map, foreground_layer_name, TILE_SCALING)

        # -- Platforms
        self.wall_list = arcade.generate_sprites(my_map, platforms_layer_name, TILE_SCALING)

        # -- Platforms
        self.wall_list = arcade.generate_sprites(my_map, platforms_layer_name, TILE_SCALING)

        # -- Coins
        self.coin_list = arcade.generate_sprites(my_map, coins_layer_name, TILE_SCALING)

        # -- Don't Touch Layer
        self.dont_touch_list = arcade.generate_sprites(my_map, dont_touch_layer_name, TILE_SCALING)

        # -- Hearts Layer
        self.hearts_list = arcade.generate_sprites(my_map, hearts_layer_name, TILE_SCALING)

        # -- Hearts Layer
        self.hearts_list = arcade.generate_sprites(my_map, hearts_layer_name, TILE_SCALING)

        # -- Poisons Layer
        self.poisons_list = arcade.generate_sprites(my_map, poisons_layer_name, TILE_SCALING)

        # -- Poisons Layer
        self.poisons_list = arcade.generate_sprites(my_map, poisons_layer_name, TILE_SCALING)

        self.end_of_map = (len(map_array[0]) - 1) * GRID_PIXEL_SIZE

        # --- Other stuff
        # Set the background color
        if my_map.backgroundcolor:
            arcade.set_background_color(my_map.backgroundcolor)

        # Create the 'physics engine'
        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite,
                                                             self.wall_list,
                                                             GRAVITY)
    # STEP 2: Add this function.
    def draw_instructions_page(self, page_number):
        """
        Draw an instruction page. Load the page as an image.
        """
        # This command should happen before we start drawing. It will clear
        # the screen to the background color, and erase what we drew last frame.
        arcade.start_render()
        page_texture = self.instructions[page_number]
        arcade.draw_texture_rectangle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                      page_texture.width,
                                      page_texture.height, page_texture, 0)

    # STEP 3: Add this function
    def draw_game_over(self):
        """
        Draw "Game over" across the screen.
        """
        # This command should happen before we start drawing. It will clear
        # the screen to the background color, and erase what we drew last frame.
        arcade.start_render()
        self.view_bottom = 0
        self.view_left = 0

        if self.current_state == YOU_LOST :
            page_texture = self.instructions[2] #arcade.load_texture("images/instructions/GameOver.png")
            arcade.draw_texture_rectangle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                          page_texture.width,
                                          page_texture.height, page_texture, 0)

        elif self.current_state == YOU_WON :
            page_texture = self.instructions[3] #arcade.load_texture("images/instructions/YouWon.png")
            arcade.draw_texture_rectangle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                          page_texture.width,
                                          page_texture.height, page_texture, 0)
            """
        output = "Game Over"
        arcade.draw_text(output, 240, 400, arcade.color.WHITE, 54)

        output = "Click to restart"
        arcade.draw_text(output, 310, 300, arcade.color.WHITE, 24)
        """
        
    def on_draw(self):
        """ Render the screen. """

        # Clear the screen to the background color
        arcade.start_render()

        if self.current_state == INSTRUCTIONS_PAGE_0:
            self.draw_instructions_page(0)

        elif self.current_state == INSTRUCTIONS_PAGE_1:
            self.draw_instructions_page(1)

        elif self.current_state == GAME_RUNNING:
            self.draw_game()

        else:
            self.draw_game()
            self.draw_game_over()

    def draw_game(self) :
        # Draw our sprites
        self.wall_list.draw()
        self.background_list.draw()
        self.wall_list.draw()
        self.coin_list.draw()
        self.dont_touch_list.draw()
        self.hearts_list.draw()
        self.poisons_list.draw()
        self.player_list.draw()
        self.foreground_list.draw()

        # Draw our score on the screen, scrolling it with the viewport
        score_text = f"Score: {self.score}"
        arcade.draw_text(score_text, 10 + self.view_left, 10 + self.view_bottom,
                         arcade.csscolor.BLACK, 18)

        # Draw our level on the screen, scrolling it with the viewport
        level_text = f"Level: {self.level}"
        arcade.draw_text(level_text, 150 + self.view_left, 10 + self.view_bottom,
                         arcade.csscolor.BLACK, 18)

        # Draw our health on the screen, scrolling it with the viewport
        level_text = f"Health: {self.health}"
        arcade.draw_text(level_text, 310 + self.view_left, 10 + self.view_bottom,
                         arcade.csscolor.BLACK, 18)

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """
            # Only move the user if the game is running.
        if self.current_state == GAME_RUNNING:

            if key == arcade.key.UP or key == arcade.key.W:
                if self.physics_engine.can_jump():
                    self.player_sprite.change_y = PLAYER_JUMP_SPEED
                    arcade.play_sound(self.jump_sound)
            elif key == arcade.key.LEFT or key == arcade.key.A:
                self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
            elif key == arcade.key.RIGHT or key == arcade.key.D:
                self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """
            # Only move the user if the game is running.
        if self.current_state == GAME_RUNNING:

            if key == arcade.key.LEFT or key == arcade.key.A:
                self.player_sprite.change_x = 0
            elif key == arcade.key.RIGHT or key == arcade.key.D:
                self.player_sprite.change_x = 0

    # STEP 6: Do something like adding this to your on_mouse_press to flip
    # between instruction pages.
    def on_mouse_press(self, x, y, button, modifiers):
        """
        Called when the user presses a mouse button.
        """

        # Change states as needed.
        if self.current_state == INSTRUCTIONS_PAGE_0:
            # Next page of instructions.
            self.current_state = INSTRUCTIONS_PAGE_1
        elif self.current_state == INSTRUCTIONS_PAGE_1:
            # Start the game
            self.setup(1)
            self.current_state = GAME_RUNNING
        elif self.current_state == YOU_WON:
            # Restart the game.
            self.setup(1)
            self.current_state = GAME_RUNNING
        elif self.current_state == YOU_LOST:
            # Restart the game.
            self.setup(1)
            self.current_state = GAME_RUNNING

    
    def update(self, delta_time):
        """ Movement and game logic """

        # Only move and do things if the game is running.
        if self.current_state == GAME_RUNNING:
            
            # Call update on all sprites (The sprites don't do much in this
            # example though.)
            self.physics_engine.update()

            # See if we hit any coins
            coin_hit_list = arcade.check_for_collision_with_list(self.player_sprite,
                                                                 self.coin_list)

            # See if we hit any hearts
            hearts_hit_list = arcade.check_for_collision_with_list(self.player_sprite,
                                                                 self.hearts_list)

            # See if we hit any poisons
            poisons_hit_list = arcade.check_for_collision_with_list(self.player_sprite,
                                                                 self.poisons_list)

            # Loop through each coin we hit (if any) and remove it
            for coin in coin_hit_list:
                # Remove the coin
                coin.remove_from_sprite_lists()
                # Play a sound
                arcade.play_sound(self.collect_coin_sound)
                # Add one to the score
                self.score += 1

            # Loop through each heart we hit (if any) and remove it
            for heart in hearts_hit_list:
                # Remove the heart
                heart.remove_from_sprite_lists()
                # Play a sound
                arcade.play_sound(self.collect_coin_sound)
                # Add one to the health
                self.health += 1

            # Loop through each heart we hit (if any) and remove it
            for poison in poisons_hit_list:
                # Remove the Poison
                poison.remove_from_sprite_lists()
                # Play a sound
                arcade.play_sound(self.collect_coin_sound)
                # Take one from the health
                self.health -= 1

            # Track if we need to change the viewport
            changed_viewport = False

            # Did the player fall off the map?
            if self.player_sprite.center_y < -100:
                self.player_sprite.center_x = PLAYER_START_X
                self.player_sprite.center_y = PLAYER_START_Y
                #self.current_state = YOU_LOST

                self.health -= 1
                # Set the camera to the start
                self.view_left = 0
                self.view_bottom = 0
                changed_viewport = True
                arcade.play_sound(self.game_over)

            # Did the player touch something they should not?
            if arcade.check_for_collision_with_list(self.player_sprite, self.dont_touch_list):
                #self.current_state = YOU_LOST #GAME_OVER

                self.player_sprite.center_x = PLAYER_START_X
                self.player_sprite.center_y = PLAYER_START_Y
                self.health -= 1
                # Set the camera to the start
                self.view_left = 0
                self.view_bottom = 0
                changed_viewport = True
                arcade.play_sound(self.game_over)

            # Did the player health run out ?
            if self.health < 0:
                self.current_state = YOU_LOST #GAME_OVER
                
                self.player_sprite.center_x = PLAYER_START_X
                self.player_sprite.center_y = PLAYER_START_Y

                # Set the camera to the start
                self.view_left = 0
                self.view_bottom = 0
                changed_viewport = True
                arcade.play_sound(self.game_over)

            # See if the user got to the end of the level
            if self.player_sprite.center_x >= self.end_of_map:
                # Advance to the next level
                if self.level == MAX_LEVEL:
                    self.current_state = YOU_WON
                else:
                    self.level += 1

                # Load the next level
                self.setup(self.level)

                # Set the camera to the start
                self.view_left = 0
                self.view_bottom = 0
                changed_viewport = True

            # --- Manage Scrolling ---
        
            # Scroll left
            left_boundary = self.view_left + LEFT_VIEWPORT_MARGIN
            if self.player_sprite.left < left_boundary:
                self.view_left -= left_boundary - self.player_sprite.left
                changed_viewport = True

            # Scroll right
            right_boundary = self.view_left + SCREEN_WIDTH - RIGHT_VIEWPORT_MARGIN
            if self.player_sprite.right > right_boundary:
                self.view_left += self.player_sprite.right - right_boundary
                changed_viewport = True

            # Scroll up
            top_boundary = self.view_bottom + SCREEN_HEIGHT - TOP_VIEWPORT_MARGIN
            if self.player_sprite.top > top_boundary:
                self.view_bottom += self.player_sprite.top - top_boundary
                changed_viewport = True

            # Scroll down
            bottom_boundary = self.view_bottom + BOTTOM_VIEWPORT_MARGIN
            if self.player_sprite.bottom < bottom_boundary:
                self.view_bottom -= bottom_boundary - self.player_sprite.bottom
                changed_viewport = True

            if changed_viewport:
                # Only scroll to integers. Otherwise we end up with pixels that
                # don't line up on the screen
                self.view_bottom = int(self.view_bottom)
                self.view_left = int(self.view_left)

                # Do the scrolling
                arcade.set_viewport(self.view_left,
                                    SCREEN_WIDTH + self.view_left,
                                    self.view_bottom,
                                    SCREEN_HEIGHT + self.view_bottom)


def main():
    """ Main method """
    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup(window.level)
    arcade.run()


if __name__ == "__main__":
    main()
