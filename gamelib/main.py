# entry point from `run_game.py`

from cocos import collision_model
from cocos.director import director

import cocos
import pyglet
import time

# my modules
import config
import data
from sprite import OurSprite


class MainGameLayer(cocos.layer.Layer):

    is_event_handler = True

    def __init__(self):
        super(MainGameLayer, self).__init__()

        self.keysPressed = set()

        self.schedule(self.update)

        self.bob = Player((200, 200))
        self.add(self.bob)

        '''self.dat = Data((200, 50))
        self.add(self.dat)'''

        self.mapCollider = PlayerMapCollider(self.bob)

        self.collisionManager = collision_model.CollisionManagerBruteForce()

    def update(self, deltaTime):
        keyNames = [pyglet.window.key.symbol_string(k) for k in self.keysPressed]

        # re-add in all the sprites to the `collisionManager`
        self.collisionManager.clear()
        for sprite in self.get_children():
            self.collisionManager.add(sprite)

        # handle collisions
        collisions = self.collisionManager.objs_colliding(self.bob)
        if collisions:
            for sprite in self.get_children():
                if isinstance(sprite, Bullet):
                    if sprite in collisions:
                        print("BULLET COLLISION!")

        ######################################################

        if "W" in keyNames:
            if self.bob.doY == 0:
                # jump!
                self.bob.doY += self.bob.JUMP_SPEED
                self.bob.doGravity = True

        if "A" in keyNames:
            # move left
            self.bob.doX -= self.bob.WALK_SPEED * deltaTime

            self.bob.direction = "left"

        if "D" in keyNames:
            # move right
            self.bob.doX += self.bob.WALK_SPEED * deltaTime

            self.bob.direction = "right"

        if "A" not in keyNames and "D" not in keyNames:
            # stop moving left-right

            # MAGIC NUMBER ALERT!!!
            if self.bob.doX > -.5 and self.bob.doX < .5:
                self.bob.doX = 0

            else:
                self.bob.doX *= self.bob.WALK_SMOOTH

        if "SPACE" in keyNames:
            # shoot bullet
            if (time.time() - self.bob.lastShot) >= self.bob.FIRE_RATE:
                self.add(Bullet(self.bob.position, self.bob.direction, self.bob.BULLET_OFFSET))
                self.bob.lastShot = time.time()

        ######################################################

        # update the player

        self.bob.doY -= self.bob.GRAVITY_SPEED * deltaTime

        last = self.bob.get_rect()
        new = last.copy()
        new.x += self.bob.doX
        new.y += self.bob.doY
        #         BAD GLOBAL!!!          \/
        self.mapCollider.collide_map(ourMapLayer, last, new, self.bob.doY, self.bob.doX)

        self.bob.update()

        # update all the `Bullet` instances
        for sprite in self.get_children():
            if isinstance(sprite, Bullet):
                if sprite.killMe:
                    self.remove(sprite)

                else:
                    sprite.update()

    def on_key_press(self, key, modifiers):
        self.keysPressed.add(key)

    def on_key_release(self, key, modifiers):
        self.keysPressed.discard(key)


class Player(OurSprite):
    def __init__(self, position, image = pyglet.image.load(data.getPath("dude.png"))):
        super(Player, self).__init__(image)
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

        self.BULLET_OFFSET = (self.width // 2) + 4
        self.FIRE_RATE = .25
        self.lastShot = time.time() - self.FIRE_RATE

    def update(self):
        self.moveBy((self.doX, self.doY))
        self.cshape.center = self.position


class Data(OurSprite):
    def __init__(self, position, image = pyglet.image.load(data.getPath("data.png"))):
        super(Data, self).__init__(image)
        self.position = position

        self.cshape = collision_model.AARectShape(self.position, self.width // 2, self.height // 2)


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
            self.doX = -self.OFFSET
            self.update()
            self.doX = -self.SPEED * config.DELTA_TIME

        elif self.DIRECTION == "right":
            self.doX = self.OFFSET
            self.update()
            self.doX = self.SPEED * config.DELTA_TIME

    def update(self):
        if (time.time() - self.spawnTime) >= self.LIFETIME:
            self.killMe = True

        else:
            self.moveBy((self.doX, self.doY))
            self.cshape.center = self.position


class PlayerMapCollider(cocos.tiles.RectMapCollider):
   def __init__(self, player):
       self.player = player

   def collide_bottom(self, doY):
       if self.player.doY:
           self.player.doY = doY
           self.player.update()
           self.player.doY = 0

   def collide_left(self, doX):
       print("stop walking")

   def collide_right(self, doX):
       print("stop walking")

   def collide_top(self, doY):
       if self.player.doY:
           print("ouch")


def main():

    director.init(width = config.SCREEN_WIDTH, height = config.SCREEN_HEIGHT, resizable = False, caption = "Platformy.py")

    # ONLY FOR DEV
    director.show_FPS = True

    global ourMapLayer

    ourMapLayer = cocos.tiles.load(data.getPath("map.tmx"))["Tile Layer 1"]
    ourMapLayer.set_view(0, 0, ourMapLayer.px_width, ourMapLayer.px_height)

    ourScene = cocos.scene.Scene(ourMapLayer, MainGameLayer())

    director.run(ourScene)
