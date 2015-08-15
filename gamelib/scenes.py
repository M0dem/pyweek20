
from cocos.scenes.transitions import *

import cocos

class Level():
    def __init__(self, mapLayer, mainGameLayer, playerHealthLayer, playerSpawn):
        self.mapLayer = mapLayer
        self.mainGameLayer = mainGameLayer
        self.playerHealthLayer = playerHealthLayer
        self.playerSpawn = playerSpawn

        self.scroller = cocos.layer.ScrollingManager()
        self.scroller.add(self.mainGameLayer)
        self.scroller.add(self.mapLayer)


class SceneManager():
    def __init__(self, director):
        self.director = director

    def run(self):
        if not self.director.scene:
            self.doMainMenuScene(run = True)

    def loadScenes(self, mainMenuScene, loserScene, winnerScene, levels):
        self.mainMenuScene = mainMenuScene
        self.loserScene = loserScene
        self.winnerScene = winnerScene

        self.loadLevels(levels)

    def loadLevels(self, levels):
        self.levels = levels

        self.currentLevelIndex = 0
        self.updateCurrentLevelStuff()

    def reloadLevels(self):
        self.currentLevel.mainGameLayer.reset()

    def updateCurrentLevelStuff(self):
        self.currentLevel = self.levels[self.currentLevelIndex]
        self.currentLevelScene = cocos.scene.Scene(self.currentLevel.scroller, self.currentLevel.playerHealthLayer)

    def doMainMenuScene(self, run = False):
        self.currentLevelIndex = 0
        if run:
            self.director.run(self.mainMenuScene)

        else:
            self.director.replace(FlipX3DTransition(self.mainMenuScene, duration = 1))

    def doLoserScene(self):
        self.currentLevelIndex = 0
        self.reloadLevels()
        self.director.replace(FlipX3DTransition(self.loserScene, duration = 1))

    def doWinnerScene(self):
        self.currentLevelIndex = 0
        self.director.replace(FlipX3DTransition(self.winnerScene, duration = 1))

    def doLevelScene(self, increment = True, reset = None):
        if reset:
            reset.dead = False
            
        if increment:
            j = 2

        else:
            j = 1

        if (self.currentLevelIndex + j) <= len(self.levels):
            if increment:
                self.currentLevelIndex += 1
                self.updateCurrentLevelStuff()

            self.director.replace(FlipX3DTransition(self.currentLevelScene, duration = 1))

        else:
            # has completed all the levels
            self.doWinnerScene()
