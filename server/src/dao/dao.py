from threading import Semaphore
from keras import Sequential
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import keras

class DAO():

    def __init__(self):
        
        self.__semaforo = Semaphore()

    def almacenar_modelo(self, model : Sequential, nombre : str) -> None:

        self.__semaforo.acquire()
        keras.models.save_model(model,nombre)
        self.__semaforo.release()

    def cargar_modelo(self, nombre: str) -> Sequential:

        self.__semaforo.acquire()
        model : Sequential = keras.models.load_model(nombre)
        self.__semaforo.release()

        return model

