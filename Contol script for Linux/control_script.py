import curses
from rcute_cozmars import Robot
import rcute_ai as ai
from wsmprpc import RPCClient, RPCStream
from rcute_cozmars import util, env, screen, camera, microphone, sonar, lift, head, speaker, motor, eye_animation
from rcute_cozmars.animation import animations
import wave
import pyaudio
import time
import cv2
from PIL import Image

det = ai.ObjectDetector()
face = ai.FaceDetector()


def main(stdscr):
    # do not wait for input when calling getch
    stdscr.nodelay(1)
    with Robot('192.168.1.210') as robot:

        print('connected')
        robot.head.angle = 0
        robot.lift.default_speed = 3
        curses.noecho()
        mic_on = False
        face_on = False
        listen_on = False
        detect_on = False
        mic = robot.microphone
        robot.speaker.volume = 90
        face.memorize('Marcos', 'marcos.png')
        face.memorize('Zoe', 'zoe.png')
        robot.microphone.gain = 40

        def cb():  # Speech recognition what to do
            robot.say('Listening')
            speech = robot.listen(lang='en')
            # print(speech)
            if speech == 'up':
                robot.lift.set_height(1, speed=2)
            elif speech == 'down':
                robot.lift.set_height(0, speed=2)
        robot.when_called = cb

        while True:
            # get keyboard input, returns -1 if none available
            c = stdscr.getch()

            if c != -1:

                if c == ord('w'):  # W Drive forward
                    robot.motors.speed = (1, 1)
                elif c == ord('s'):  # S Drive backwards
                    robot.motors.speed = (-1, -1)
                elif c == ord('a'):  # A Turn left
                    robot.motors.speed = (-1, 1)
                elif c == ord('d'):  # D Turn right
                    robot.motors.speed = (1, -1)
                elif c == ord('r'):  # R Head up
                    if robot.head.angle <= 20:
                        robot.head.angle += 10
                elif c == ord('f'):  # F Head down
                    if robot.head.angle >= -20:
                        robot.head.angle -= 10
                elif c == ord('c'):  # c show camera
                    robot.show_camera_view()
                elif c == ord('v'):  # close camera cant find the close camera function dunno why
                    robot.close_camera_view()
                elif c == ord('z'):  # z lift arms up
                    robot.lift.height = 1
                elif c == ord('x'):  # x lift arms down
                    robot.lift.height = 0
                elif c == ord('t'):  # t talk
                    var_talk = user_input(stdscr, 'Text to speak: ')
                    stdscr.addstr('  Thinking...')
                    stdscr.refresh()
                    robot.say(var_talk)
                    stdscr.clear()
                elif c == ord('q'):  # q Disconnect
                    robot.disconnect()
                    exit()
                elif c == ord('y'):  # Record 5sec and play it back
                    FORMAT = pyaudio.paInt16
                    CHANNELS = 2
                    RATE = 44100
                    CHUNK = 1024
                    RECORD_SECONDS = 5

                    audio = pyaudio.PyAudio()
                    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                                        frames_per_buffer=CHUNK)
                    frames = []

                    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                        data = stream.read(CHUNK)
                        frames.append(data)
                    robot.speaker.play(data)

                elif c == ord('m'):  # Record a audio file to the raspberry pi
                    mic_on = not mic_on
                elif c == ord('g'):  # activate speech recognition (NOT FINISHED)
                    if listen_on:
                        robot.when_called = cb
                    else:
                        robot.when_called = None
                    # cb(robot)
                    listen_on = not listen_on
                    stdscr.clear()
                elif c == ord('o'):  # q recognize face
                    face_on = True
                elif c == ord('l'):  # q recognize face and do something. Save a face before using
                    with robot.camera.get_buffer() as cam_buf:
                        for image in cam_buf:
                            locations, names = face.detect(image)
                            str1 = ''
                            for x in names:
                                str1 += x
                            stdscr.addstr(1, 0, 'Face detected: ' + str1)
                            stdscr.refresh()
                            if str1 == 'Marcos':
                                robot.say('I see the king... King marcos... the very best')
                                break
                            if str1 == 'Zoe':
                                robot.say('I am looking at princess Zoe... The most pretty princess')
                                break
                            break

                elif c == ord('k'):  # q recognize face
                    detect_on = True
                elif c == ord('p'):  # PLay recorded audio
                    robot.speaker.play('record.wav')
                elif c == 32:  # Space to stop motors while moving or turning
                    robot.motors.speed = (0, 0)
            write_menu(stdscr, 0)

            if face_on:
                write_menu(stdscr, 1)  # Write face ai menu
                with robot.camera.get_buffer() as cam_buf:
                    for image in cam_buf:
                        c = stdscr.getch()

                        if c == ord('l'):  # Lists saved faces
                            stdscr.clear()
                            write_menu(stdscr, 1)
                            stdscr.addstr(1, 0, 'Saved faces:')
                            names = face.memory
                            str1 = ''
                            for x in names:
                                str1 = str1 + x + ', '
                            str1 += '\n'
                            stdscr.addstr(2, 0, str1)

                        if c == ord('r'):  # Must be called before the annotate processing takes place
                            stdscr.clear()
                            write_menu(stdscr, 1)
                            stdscr.addstr(1, 0, 'Saved faces:')
                            names = face.memory
                            str1 = ''
                            for x in names:
                                str1 = str1 + x + ', '
                            str1 += '\n'
                            stdscr.addstr(2, 0, str1)
                            face_mem = user_input(stdscr, 'Remove person: ')
                            stdscr.clear()
                            write_menu(stdscr, 1)
                            stdscr.addstr(2, 0, face.forget(face_mem) + '\n')  # remove face
                        if c == ord('m'):  # Must be called before the annotate processing takes place
                            stdscr.clear()
                            write_menu(stdscr, 1)
                            face_mem = user_input(stdscr, 'Name of the person: ')
                            stdscr.clear()
                            write_menu(stdscr, 1)
                            stdscr.addstr(2, 0, face.memorize(face_mem, image) + '\n')

                        locations, names = face.detect(image)
                        face.annotate(image, locations, names)

                        ai.imshow(image)

                        if c == ord('q'):  # Quit face detection
                            face_on = False
                            ai.imclose()
                            stdscr.clear()
                            break

            if detect_on:
                with robot.camera.get_buffer() as cam_buf:

                    for image in cam_buf:
                        c = stdscr.getch()
                        # 识别图像中的物体位置和物体名称
                        locations, names = det.detect(image)

                        # 将识别到的物体的信息画到图中
                        det.annotate(image, locations, names)

                        # 显示图像
                        ai.imshow(image)

                        # 按下按钮就结束程序
                        if c == ord('q'):
                            detect_on = False
                            ai.imclose()
                            break

            if mic_on:
                with mic.get_buffer() as mic_buf, wave.open('record.wav', 'wb') as file:
                    file.setnchannels(1)
                    file.setframerate(mic.sample_rate)
                    file.setsampwidth(mic.sample_width)

                    duration = 0
                    for segment in mic_buf:
                        file.writeframesraw(segment.raw_data)

                        # 麦克风输出流中每个数据块默认是 0.1 秒的音频，录制 5 秒后结束
                        duration += segment.duration_seconds
                        if duration >= 5:
                            mic_on = False
                            break


def user_input(stdscr, text):
    stdscr.nodelay(0)
    stdscr.addstr(text)
    curses.echo()
    temp = stdscr.getstr().decode()
    curses.noecho()
    stdscr.clear()
    write_menu(stdscr, 0)
    stdscr.nodelay(1)
    return temp


def write_menu(stdscr, x):
    if x == 1:
        stdscr.addstr(0, 0, 'Face ai - m: memorize face  r: remove face  q: quit interface')
    else:
        stdscr.addstr(0, 0, 'W:forward S:backward D:turn right A:turn left T:speak')
    stdscr.move(2, 0)
    stdscr.refresh()


def cbx(robot):

    speech = robot.listen(lang='en')
    # print(speech)
    if speech == 'up':
        robot.lift.set_height(1, speed=2)
    elif speech == 'down':
        robot.lift.set_height(0, speed=2)


if __name__ == '__main__':
    curses.wrapper(main)
