#!/usr/bin/env python
import threading
import time
import pyaudio
import numpy as np

class streamer(object):
    def __init__(self, sample_rate, chunk_size, stream_parser):
        self.sample_rate = sample_rate
        self.stream_parser = stream_parser
        self.decoding_chunk_size = chunk_size  # gets replaced automatically
        self.chunks_read_count = 0

        self.mic_device = None
        self.pyaudio = None
        self.keep_recording = None
        self.stream = None
        self.thread = None

    # SYSTEM TEST
    def __get_valid_input_devices__(self):
        def is_valid_device(device):
            """given a device ID and a rate, return TRUE/False if it's valid."""
            try:
                device_info = self.pyaudio.get_device_info_by_index(device)
                if device_info["maxInputChannels"] == 0:
                    return False

                stream = self.pyaudio.open(
                    format=pyaudio.paInt32,
                    channels=1,
                    input_device_index=device,
                    frames_per_buffer=self.decoding_chunk_size,
                    rate=self.sample_rate,
                    input=True
                )
                stream.close()
                return True
            except:
                return False

        mics = []
        for device in range(self.pyaudio.get_device_count()):
            if is_valid_device(device):
                mics.append(device)
        return mics

    def start(self):
        self.pyaudio = pyaudio.PyAudio()

        # Get an valid mic device
        if self.mic_device is None:
            mic_devices = self.__get_valid_input_devices__()
            if len(mic_devices) == 0:
                raise Exception("Cannot detect valid device, something went wrong.")
            self.mic_device = mic_devices[0]  # pick the first one

        self.keep_recording = True  # set this to False later to terminate stream
        self.stream =\
            self.pyaudio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.decoding_chunk_size
            )
        self.__stream_thread_new__()

    # STREAM HANDLING
    def __stream_thread_new__(self):
        self.thread = threading.Thread(target=self.__stream_read_chunk__)
        self.thread.start()

    def __stream_read_chunk__(self):
        """reads some audio and re-launches itself"""
        try:
            self.stream_parser(
                np.fromstring(self.stream.read(self.decoding_chunk_size), dtype=np.float32).tolist()
            )
        except Exception as E:
            print(" -- exception! terminating...")
            print(E, "\n" * 5)
            self.keep_recording = False

        if self.keep_recording:
            self.__stream_thread_new__()
        else:
            self.stream.close()
            self.pyaudio.terminate()
        self.chunks_read_count += 1

    def stop(self):
        self.keep_recording = False
        while (self.thread.isAlive()):  # wait for all threads to close
            time.sleep(.1)
        self.stream.stop_stream()
        self.pyaudio.terminate()
        self.mic_device = None

if __name__ == "__main__":
    audioStream =\
        streamer(
            sample_rate=48000,
            chunk_size=24000,
            stream_parser=lambda samples: print(len(samples), samples[0])
        )
    audioStream.start()
