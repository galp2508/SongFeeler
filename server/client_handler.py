import io
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # or any {'0', '1', '2'}
import cv2
import time
import socket
import numpy as np
from time import sleep
import PIL.Image as Image
from threading import Lock
from keras.preprocessing.image import img_to_array


class ClientHandler:
    def __init__(self, sock: socket.socket, db_manager: tuple, model_lock: Lock, model) -> None:
        self.__sock = sock
        self.__db_manager = db_manager
        self.__model_lock = model_lock
        self.__model = model
        self.__handle_client()

    def __send_message(self, message: str):
        try:
            full_message = bytearray()
            full_message.extend("1".encode())
            full_message.extend((len(message)).to_bytes(4, byteorder="little"))
            full_message.extend(message.encode())
            self.__sock.send(full_message)
        except:
            pass

    def __send_ping(self):
        try:
            self.__sock.send("2".encode())
            return True
        except:
            return False

    def __handle_client(self) -> None:
        options = {1: self.__login, 2: self.__signup, 3: self.__find_song}
        timeout = 30

        timeout_start = time.time()

        try:
            while True:
                packet = self.__sock.recv(5)

                if packet:
                    try:
                        # extracting code and length
                        code = int(packet[0])
                        if code != 4:
                            length = int.from_bytes(packet[1:5], byteorder="little")
                            # receive data using the length we got
                            data = self.__recvall(self.__sock, length)
                            options[code](data)
                        else:
                            raise ConnectionResetError
                    except KeyError:
                        pass
                    except Exception as e:
                        self.__send_message("3")
                        print(str(e))

                # every 30 seconds check if client still alive
                if time.time() >= timeout_start + timeout:
                    if not self.__send_ping():
                        raise ConnectionResetError

                    timeout_start = time.time()
        except ConnectionResetError:
            print("oh the clinet left boo hoo :(")
        except ConnectionAbortedError:
            print("oh the clinet left boo hoo :(")
        except KeyboardInterrupt:
            pass

    @staticmethod
    def __recvall(sock: socket.socket, length: int) -> str:
        data = bytearray()

        while len(data) < length:
            packet = sock.recv(1024)

            if not packet:
                pass

            data.extend(packet)

        return data

    def __wait_for_lock(self, lock: Lock):

        while lock.locked():
            sleep(0.1)

    def __login(self, data: bytearray) -> None:
        data = data.decode()
        email, password = data.split(",")
        is_login = 0

        while type(is_login) == int:

            self.__wait_for_lock(self.__db_manager[1])

            try:
                self.__db_manager[1].acquire()
                is_login = self.__db_manager[0].login(email, password)
            finally:
                self.__db_manager[1].release()

        self.__send_message(str(int(is_login)))

    def __signup(self, data: bytearray) -> None:
        data = data.decode()
        email, password = data.split(",")
        is_registered = 0

        while type(is_registered) == int:

            self.__wait_for_lock(self.__db_manager[1])

            try:
                self.__db_manager[1].acquire()
                is_registered = self.__db_manager[0].signup(email, password)
            finally:
                self.__db_manager[1].release()

        self.__send_message(str(int(is_registered)))

    def __find_song(self, data: bytearray):
        emotion = 0

        while type(emotion) == int:

            self.__wait_for_lock(self.__model_lock)

            try:
                self.__model_lock.acquire()
                emotion = self.__find_emotion(data)
            finally:
                self.__model_lock.release()

        song = self.__match_song_to_emotion(emotion)

        details = emotion + "," + ",".join(song)

        self.__send_message(details)

    def __match_song_to_emotion(self, emotion: str) -> list:
        songs = {
            "Angry": ["Metallica", "St. Anger", "https://www.youtube.com/watch?v=3rFoGVkZ29w&ab_channel=Metallica"],
            "Disgust": [
                "ADELE",
                "Cold Shoulder",
                "https://www.youtube.com/watch?v=uGwH-x4VoH8&ab_channel=XLRecordings",
            ],
            "Fear": ["Mariah Carey", "Hero", "https://www.youtube.com/watch?v=0IA3ZvCkRkQ&ab_channel=MariahCareyVEVO"],
            "Happy": [
                "Justin Timberlake",
                "CAN'T STOP THE FEELING!",
                "https://www.youtube.com/watch?v=ru0K8uYEZWw&ab_channel=justintimberlakeVEVO",
            ],
            "Sad": [
                "We The Kings",
                "Sad Song",
                "https://www.youtube.com/watch?v=BZsXcc_tC-o&ab_channel=WeTheKingsVEVO",
            ],
            "Surprise": [
                "The Rolling Stones",
                "Surprise, Surprise",
                "https://www.youtube.com/watch?v=whfzPSgUglk&ab_channel=ABKCOVEVO",
            ],
            "Neutral": [
                "The Weeknd",
                "Blinding Lights",
                "https://www.youtube.com/watch?v=fHI8X4OXluQ&ab_channel=TheWeekndVEVO",
            ],
        }

        return songs[emotion]

    def __find_emotion(self, image_bytes: bytearray) -> str:
        start = time.time()
        print("image received lets find some emotion!\n")
        # bytes array to image
        image = Image.open(io.BytesIO(image_bytes))
        test_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray_image = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray_image, 1.1, 4)

        # detect emotion
        emotions = []

        for x, y, w, h in faces:
            cv2.rectangle(test_image, (x, y), (x + w, y + h), (255, 0, 0))
            roi_gray = gray_image[y : y + h, x : x + h]
            roi_gray = cv2.resize(roi_gray, (48, 48))
            image_pixels = img_to_array(roi_gray)
            image_pixels = np.expand_dims(image_pixels, axis=0)
            image_pixels /= 255
            predictions = self.__model.predict(image_pixels)
            max_index = np.argmax(predictions[0])
            emotion_detection = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]
            emotion_prediction = emotion_detection[max_index]

            emotions.append(emotion_prediction)
            break

        # if there is more than one face we will take the first emotion
        if len(emotions) > 0:
            return emotions[0]

        return "Neutral"
