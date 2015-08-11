# entry point from `run_game.py`

from cocos import collision_model
from cocos.director import director

import cocos
import pyglet

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

        self.dat = Data((200, 50))
        self.add(self.dat)

        self.ourCollider = PlayerCollider()

        '''self.collisionManager = collision_model.CollisionManagerBruteForce()'''

    def update(self, deltaTime):
        keyNames = [pyglet.window.key.symbol_string(k) for k in self.keysPressed]

        '''# re-add in all the sprites to the `collisionManager`
        self.collisionManager.clear()
        for sprite in self.get_children():
            self.collisionManager.add(sprite)

        # handle collisions
        collisions = self.collisionManager.objs_colliding(self.bob)
        if collisions:
            # collided downwards with "platform"
            if self.dat in collisions and self.bob.velocity.y < 0:
                self.bob.doGravity = False
                self.bob.velocity.y = 0

            # move up out of the "platform"
            elif self.dat in collisions and self.bob.velocity.y == 0:
                self.bob.moveBy((0, 1))'''

        ######################################################

        if "W" in keyNames:
            if self.bob.velocity.y == 0:
                self.bob.doJump = True
                self.bob.doGravity = True

        if "A" in keyNames:
            self.bob.velocity.x -= self.bob.WALK_SPEED * deltaTime

        if "D" in keyNames:
            self.bob.velocity.x += self.bob.WALK_SPEED * deltaTime

        if "A" not in keyNames and "D" not in keyNames:
            self.bob.velocity.x = 0

        ######################################################

        lastBob = self.bob.get_rect()
        newBob = lastBob.copy()


        self.bob.update(deltaTime)

    def on_key_press(self, key, modifiers):
        self.keysPressed.add(key)

    def on_key_release(self, key, modifiers):
        self.keysPressed.discard(key)


class Player(OurSprite):
    def __init__(self, position, image = pyglet.image.load(data.getPath("dude.png"))):
        super(Player, self).__init__(image)
        self.position = position

        self.cshape = collision_model.AARectShape(self.position, self.width // 2, self.height // 2)

        self.doGravity = True
        self.GRAVITY = 500

        self.doJump = False
        self.JUMP_SPEED = 20000

        self.WALK_SPEED = 1000

        self.velocity = cocos.euclid.Vector2()

    '''def update(self, deltaTime):
        if self.doGravity:
            self.gravitate(self.GRAVITY * deltaTime)

        if self.doJump:
            self.jumpUp(self.JUMP_SPEED * deltaTime)
            self.doJump = False

        self.moveBy(self.velocity * deltaTime)
        self.cshape.center = self.position'''

    def getDo(self, deltaTime, this = None):
        if this:
            pass

        else:
            if self.doGravity:
                self.gravitate(self.GRAVITY * deltaTime)

            if self.doJump:
                self.jumpUp(self.JUMP_SPEED * deltaTime)
                self.doJump = False

        return velocity.x, velocity.y

    def gravitate(self, gravity):
        self.velocity.y -= gravity

    def jumpUp(self, jumpSpeed):
        self.velocity.y += jumpSpeed

    def checkBelow(self, ):
        pass


class Data(OurSprite):
    def __init__(self, position, image = pyglet.image.load(data.getPath("data.png"))):
        super(Data, self).__init__(image)
        self.position = position

        self.cshape = collision_model.AARectShape(self.position, self.width // 2, self.height // 2)


class PlayerCollider(cocos.tiles.RectMapCollider):
   def __init__(self, player):
       self.player = player

   def collide_bottom(self, doY):
       if self.player.velocity.y:
           print("landed")

   def collide_left(self, doX):
       print("stop walking")

   def collide_right(self, doX):
       print("stop walking")

   def collide_top(self, doY):
       if self.player.velocity.y:
           print("ouch")


def main():

    director.init(width = config.SCREEN_WIDTH, height = config.SCREEN_HEIGHT, resizable = False, caption = "Platformy.py")

    # ONLY FOR DEV
    director.show_FPS = True

    mapLayer = cocos.tiles.load(data.getPath("map.tmx"))["Tile Layer 1"]
    mapLayer.set_view(0, 0, mapLayer.px_width, mapLayer.px_height)

    ourScene = cocos.scene.Scene(mapLayer, MainGameLayer())

    director.run(ourScene)
