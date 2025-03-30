import PIL.Image
from src.http.parser import Parser
from src.http.response import Response
from src.dao.dao import DAO

import keras
import tensorflow as tf
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import PIL
import cv2
from io import BytesIO
import os
import nltk
nltk.download('stopwords')

def tokenize_words(text : str):

    text = text.lower()
    tokenizer = nltk.tokenize.RegexpTokenizer(r"\w+")
    tokens = tokenizer.tokenize(text)

    filtered = filter(lambda token : token not in nltk.corpus.stopwords.words("english"),tokens)

    return " ".join(filtered)

class TextGenerator():

    def __init__(self, dao : DAO, parser : Parser):
        
        self.__map : dict[tuple[str,str],str] = {
            ("POST",r"text/train/(?P<filename_keras>.+)/batch/(?P<batch_size>\w+)/epochs/(?P<bepochs>\w+)"):"train_model",
            ("POST",r"text/answer/(?P<filename_keras>.+)/length/(?P<length>.+)/lines/(?P<lines>.+)"):"generate_text",
        }


        self.__dao = dao
        self.__parser = parser

    def train_model(self, filename_to_save : str, batch_size : str, epochs : str) -> Response:

        if not filename_to_save.endswith(".keras"):

            return Response(400,body="The filename in the request must end with .keras.")
        
        if not str.isnumeric(batch_size) or not str.isnumeric(epochs):

            return Response(400,body="Batch and epochs must be integer numbers.")
        
        headers = self.__parser.headers

        if not headers.get("Content-Type").startswith("multipart"):

            return Response(400,body="the body must be a multipart form data with one file containing the text to train.")
        
        body = self.__parser.body

        filename : str = ""
        extension : str = ""
        data : bytes = ""
        filename , extension, data = body.popitem()[1]

        if not filename.endswith(".txt") or not extension == "text/plain":

            return Response(400,body="The file is not a text a file")
        
        
        
        text = data.decode("UTF-8")

        with open(filename_to_save+".txt", "w") as writer:
            writer.write(text)

    
        data_text = text.splitlines()
        
        tokenizer = tf.keras.preprocessing.text.Tokenizer()
        tokenizer.fit_on_texts(data_text)

        vocab_size=len(tokenizer.word_counts)+1 

        encoded_text = tokenizer.texts_to_sequences(data_text)

        data_list = []

        for index in encoded_text:

            if len(index) > 1:
                
                for j in range(2,len(index)):

                    data_list.append(index[:j])

        max_len = 20

        sequences = keras.preprocessing.sequence.pad_sequences(data_list,maxlen=max_len,padding="pre")

        X=sequences[:,:-1]
        y=sequences[:,-1]
     

        model = keras.models.Sequential()
        model.add(keras.layers.Embedding(vocab_size,max_len,input_shape =(vocab_size,)))
        model.add(keras.layers.Conv1D(filters=32,kernel_size=3,padding="same",activation="relu"))
        model.add(keras.layers.Conv1D(filters=64,kernel_size=3,padding="same",activation="relu"))
        model.add(keras.layers.Conv1D(filters=128,kernel_size=3,padding="same",activation="relu"))
        model.add(keras.layers.MaxPool1D(pool_size=2))
        model.add(keras.layers.Dropout(0.3))
        model.add(keras.layers.LSTM(units=256,return_sequences=True))
        model.add(keras.layers.Dropout(0.3))
        model.add(keras.layers.LSTM(units=256,return_sequences=True))
        model.add(keras.layers.Dropout(0.3))
        model.add(keras.layers.LSTM(128))
        model.add(keras.layers.Dropout(0.4))
        model.add(keras.layers.Dense(vocab_size,activation="softmax"))
        
        #model.summary()

        model.compile(optimizer="adam",loss="sparse_categorical_crossentropy",metrics=["accuracy"])

        history = model.fit(X,y,batch_size=int(batch_size),epochs=int(epochs),verbose=1)

        self.__dao.almacenar_modelo(model,filename_to_save)

        plt.xlabel("Epochs/Tries")
        plt.ylabel("Loss")

        plt.plot(history.history["loss"])
        plt.savefig("Modelo.png")

        img = cv2.imread("Modelo.png")
        image = PIL.Image.fromarray(img)

        buffer = BytesIO()
        image.save(buffer,"PNG")
        img_bytes = buffer.getvalue()

        headers : dict[str,str] = {
            "Content-Length" : str(len(img_bytes)),
            "Content-Type" : "image/png"
        }

        os.remove("Modelo.png")


        return Response(200,headers=headers,body=img_bytes)
    

    def generate_text(self, model_name : str,length: str, lines : str) -> Response:


        max_len = 20

        if not model_name.endswith(".keras"):

            return Response(400, body="the name of the model to load must end in .keras")
        
        if not length.isnumeric() or not lines.isnumeric(): 

            return Response(400,body="length and lines paremeters must be a integer number")
        
        try:
           model = self.__dao.cargar_modelo(model_name)
        except ValueError:

            return Response(404,body="Unknow model")
        
        if self.__parser.headers.get("Content-Type") != "text/plain":

            return Response(400,body="The body must be plain text.")
        
        texto = self.__parser.body
        initial_length = len(texto)
        

        with open(model_name + ".txt" , "r") as reader:

            text = reader.read()


        tokenizer = tf.keras.preprocessing.text.Tokenizer()
        
        data = text.splitlines()

        tokenizer.fit_on_texts(data)
        
        for _ in range(int(lines)):
            for _ in range(int(length)):
            
                encoded = tokenizer.texts_to_sequences([texto])
                encoded=keras.preprocessing.sequence.pad_sequences(encoded,maxlen=max_len,padding="pre")
                prediction = model.predict(encoded,verbose=0)
                y_pred=np.argmax(prediction,axis=-1)
            
                for word, index in tokenizer.word_index.items():
                    if index == y_pred[0]:
            
                        texto = texto + " " + word
                        break

            texto = texto + "\n"

        texto = texto[initial_length:]
        
        return Response(200,body=texto)
    

    @property
    def map(self) -> dict[tuple[str,str],str]:

        return self.__map