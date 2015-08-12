# entry point from `run_game.py`

from cocos import collision_model
from cocos.director import director

import cocos
import pyglet
import sys
import time

# my modules
from sprite import OurSprite

import config
import data
import scenes


class MainGameLayer(cocos.layer.ScrollableLayer):

    is_event_handler = True

    def __init__(self, sceneManager):
        super(MainGameLayer, self).__init__()
        self.sceneManager = sceneManager

        self.keysPressed = set()

        self.schedule(self.update)

        self.player = Player((200, 500))
        self.add(self.player)

        self.badputer = Badputer((550, 200), (500, 700))
        self.add(self.badputer)

        self.mapCollider = PlayerMapCollider(self.player)

        self.collisionManager = collision_model.CollisionManagerBruteForce()

    def update(self, deltaTime):
        keyNames = [pyglet.window.key.symbol_string(k) for k in self.keysPressed]

        # re-add in all the sprites to the `collisionManager`
        self.collisionManager.clear()
        for sprite in self.get_children():
            self.collisionManager.add(sprite)

        # handle collisions
        collisions = self.collisionManager.objs_colliding(self.player)
        if collisions:
            for sprite in self.get_children():
                if isinstance(sprite, Bullet):
                    if sprite in collisions:
                        print("BULLET COLLISION!")

        ######################################################

        if "W" in keyNames:
            if self.player.doY == 0:
                # jump!
                self.player.doY += self.player.JUMP_SPEED
                self.player.doGravity = True

        if "A" in keyNames:
            # move left
            self.player.doX -= self.player.WALK_SPEED * deltaTime

            self.player.direction = "left"

        if "D" in keyNames:
            # move right
            self.player.doX += self.player.WALK_SPEED * deltaTime

            self.player.direction = "right"

        if "A" not in keyNames and "D" not in keyNames:
            # stop moving left-right

            # MAGIC NUMBER ALERT!!!
            if self.player.doX > -.5 and self.player.doX < .5:
                self.player.doX = 0

            else:
                self.player.doX *= self.player.WALK_SMOOTH

        if "SPACE" in keyNames:
            # shoot bullet
            if (time.time() - self.player.lastShot) >= self.player.FIRE_RATE:
                self.add(Bullet(self.player.position, self.player.direction, self.player.BULLET_OFFSET))
                self.player.lastShot = time.time()

        ######################################################

        # update the player
        self.player.doY -= self.player.GRAVITY_SPEED * deltaTime

        # check for player-platform collisions
        last = self.player.get_rect()
        new = last.copy()
        new.x += self.player.doX
        new.y += self.player.doY
        self.mapCollider.collide_map(self.sceneManager.currentLevel.mapLayer, last, new, self.player.doY, self.player.doX)

        self.player.update()

        # update all the `Bullet` instances
        for sprite in self.get_children():
            if isinstance(sprite, Bullet):
                if sprite.killMe:
                    self.remove(sprite)

                else:
                    sprite.update()

        # update the enemy `Badputer` instances
        self.badputer.update(deltaTime)

        # make the "camera" follow the player
        self.sceneManager.currentLevel.scroller.set_focus(self.player.position[0], self.player.position[1])

    def on_key_press(self, key, modifiers):
        self.keysPressed.add(key)

    def on_key_release(self, key, modifiers):
        self.keysPressed.discard(key)


class Player(OurSprite):
    def __init__(self, position, image = pyglet.image.load(data.getPath("rawr.png"))):
        self.imageSeq = pyglet.image.ImageGrid(image, 1, 2)
        super(Player, self).__init__(self.imageSeq[1])
        self.position = position

        self.cshape = collision_model.AARectShape(self.position, self.width // 2, self.height // 2)

        self.doX = 0
        self.doY = 0

        self.doGravity = True
        self.GRAVITY_SPEED = 10

        self.JUMP_SPEED = 7

        self.WALK_SPEED = 10
        self.WALK_SMOOTH = .85
        self.direction = "right"
        self.lastDirection = "right"

        self.BULLET_OFFSET = ((self.width // 2) + 4, -16)
        self.FIRE_RATE = .25
        self.lastShot = time.time() - self.FIRE_RATE

        self.thruster = Thruster((0, -32))
        self.add(self.thruster)

    def update(self):
        if self.lastDirection != self.direction:
            if self.direction == "left":
                self.image = self.imageSeq[0]

            elif self.direction == "right":
                self.image = self.imageSeq[1]

            self.lastDirection = self.direction

        self.moveBy((self.doX, self.doY))
        self.cshape.center = self.position

        # display the thruster animation
        if self.doY > 0:
            self.thruster.enable()

        else:
            self.thruster.disable()


class Badputer(OurSprite):
    def __init__(self, position, patrolX, image = pyglet.image.load(data.getPath("badputer.png"))):
        super(Badputer, self).__init__(image)
        self.position = position

        self.cshape = collision_model.AARectShape(self.position, self.width // 2, self.height // 2)

        self.SPEED = 50
        self.PATROL_X = patrolX

        self.direction = "left"
        self.doX = -self.SPEED * config.DELTA_TIME
        self.doY = 0

    def update(self, deltaTime):
        # change direction
        if self.direction == "left" and self.position[0] < self.PATROL_X[0]:
            self.direction = "right"
            self.doX = self.SPEED * deltaTime

        elif self.direction == "right" and self.position[0] > self.PATROL_X[1]:
            self.direction = "left"
            self.doX = -self.SPEED * deltaTime

        self.moveBy((self.doX, self.doY))
        self.cshape.center = self.position

    def die(self):
        pass


class Bullet(OurSprite):
    def __init__(self, position, direction, offset, image = pyglet.image.load(data.getPath("bam.png"))):
        super(Bullet, self).__init__(image)
        self.position = position
        self.DIRECTION = direction
        self.OFFSET = offset

        self.cshape = collision_model.AARectShape(self.position, self.width // 2, self.height // 2)

        self.spawnTime = time.time()
        self.killMe = False

        self.doX = 0
        self.doY = 0

        self.SPEED = 200
        self.LIFETIME = 3

        if self.DIRECTION == "left":
            self.doX = -self.OFFSET[0]
            self.doY = self.OFFSET[1]
            self.update()

            self.doX = -self.SPEED * config.DELTA_TIME
            self.doY = 0

        elif self.DIRECTION == "right":
            self.doX = self.OFFSET[0]
            self.doY = self.OFFSET[1]
            self.update()

            self.doX = self.SPEED * config.DELTA_TIME
            self.doY = 0

    def update(self):
        if (time.time() - self.spawnTime) >= self.LIFETIME:
            self.killMe = True

        else:
            self.moveBy((self.doX, self.doY))
            self.cshape.center = self.position


class Thruster(OurSprite):
    def __init__(self, offset, image = pyglet.image.load(data.getPath("flames.gif"))):
        super(Thruster, self).__init__(image)
        self._image = image

        self.moveBy(offset)

    def disable(self):
        self.opacity = 0

    def enable(self):
        self.opacity = 255


class PlayerMapCollider(cocos.tiles.RectMapCollider):
    def __init__(self, player):
        self.player = player

    def collide_bottom(self, doY):
        if self.player.doY:
            self.player.doY = doY
            self.player.update()
            self.player.doY = 0

    def collide_left(self, doX):
        self.player.doX = doX
        self.player.update()
        self.player.doX = 0

    def collide_right(self, doX):
        self.player.doX = doX
        self.player.update()
        self.player.doX = 0

    def collide_top(self, doY):
        if self.player.doY:
            self.player.doY = doY
            self.player.update()
            self.player.doY = 0


class MainMenu(cocos.menu.Menu):
    def __init__(self, sceneManager):
        super(MainMenu, self).__init__()
        self.sceneManager = sceneManager

        l = []
        l.append(cocos.menu.MenuItem("Start Game", self.onStartGame))
        l.append(cocos.menu.MenuItem("Options", self.onOptions))
        l.append(cocos.menu.MenuItem("Quit Game", self.onQuitGame))
        self.create_menu(l, cocos.menu.shake(), cocos.menu.shake_back())

    def onStartGame(self):
        self.sceneManager.doLevelScene(increment = False)

    def onOptions(self):
        pass

    def onQuitGame(self):
        # GOODBYE!!!  :)
        sys.exit()



def main():

    director.init(width = config.SCREEN_WIDTH, height = config.SCREEN_HEIGHT, resizable = False, caption = "Platformy.py")

    # ONLY FOR DEV
    director.show_FPS = True

    sceneManager = scenes.SceneManager(director)
    levels = [
        scenes.Level(cocos.tiles.load(data.getPath("map.tmx"))["Tile Layer 1"], MainGameLayer(sceneManager))
    ]
    sceneManager.loadScenes(cocos.scene.Scene(MainMenu(sceneManager)), None, None, levels)
    sceneManager.run()
