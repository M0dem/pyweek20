
from cocos.scenes.transitions import *

import cocos

class Level():
    def __init__(self, mapLayer, bulletMapLayer, mainGameLayer, playerHealthLayer, playerSpawn, winBlockSpawn, badputerSpawns, levelDifficulty = 1):
        self.mapLayer = mapLayer
        self.bulletMapLayer = bulletMapLayer
        self.mainGameLayer = mainGameLayer
        self.playerHealthLayer = playerHealthLayer
        self.playerSpawn = playerSpawn
        self.winBlockSpawn = winBlockSpawn
        self.badputerSpawns = badputerSpawns
        self.levelDifficulty = levelDifficulty

        self.scroller = cocos.layer.ScrollingManager()
        self.scroller.add(self.mainGameLayer)
        self.scroller.add(self.mapLayer)


class SceneManager():
    def __init__(self, director):
        self.director = director

    def run(self):
        if not self.director.scene:
            self.doMainMenuScene(run = True)

    def loadScenes(self, mainMenuScene, loserScene, winnerScene, endScene, levels):
        self.mainMenuScene = mainMenuScene
        self.loserScene = loserScene
        self.winnerScene = winnerScene
        self.endScene = endScene

        self.currentLevelIndex = 0
        self.loadLevels(levels)

    def loadLevels(self, levels):
        self.levels = levels

        self.updateCurrentLevelStuff()

    def reloadLevels(self):
        self.currentLevel.mainGameLayer.reset()

    def updateCurrentLevelStuff(self):
        self.currentLevel = self.levels[self.currentLevelIndex]
        self.currentLevelScene = cocos.scene.Scene(self.currentLevel.scroller, self.currentLevel.playerHealthLayer)

    def doMainMenuScene(self, run = False):
        self.currentLevelIndex = 0
        self.reloadLevels()
        if run:
            self.director.run(self.mainMenuScene)

        else:
            self.director.replace(FlipX3DTransition(self.mainMenuScene, duration = 1))

    def doLoserScene(self):
        self.reloadLevels()
        self.director.replace(FlipX3DTransition(self.loserScene, duration = 1))

    def doWinnerScene(self):
        self.reloadLevels()
        self.director.replace(FlipX3DTransition(self.winnerScene, duration = 1))

    def doEndScene(self):
        self.director.replace(FlipX3DTransition(self.endScene, duration = 1))

    def doLevelScene(self, increment = True, reset = None):
        if reset:
            reset.dead = False

        if increment:
            j = 2

        else:
            j = 1

        print(self.currentLevelIndex)
        if (self.currentLevelIndex + j) <= len(self.levels):
            if increment:
                self.currentLevelIndex += 1
                self.updateCurrentLevelStuff()

            print(self.currentLevelIndex)
            print()

            self.director.replace(FlipX3DTransition(self.currentLevelScene, duration = 1))

        else:
            # has completed all the levels
            print("doEndScene")
            self.doEndScene()
