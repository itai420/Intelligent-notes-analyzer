import os

import pydub


def convert_mp3_to_wav(input_path):
    sound = pydub.AudioSegment.from_mp3(input_path)
    output_path = input_path[:-3] + 'wav'
    sound.export(output_path, format="wav")
    os.remove(input_path)
    return output_path

def convert_wav_to_mp3(input_path):
    sound= pydub.AudioSegment.from_wav(input_path)
    output_path = input_path[:-3] + 'mp3'
    sound.export(output_path, format="mp3")
    os.remove(input_path)
    return output_path
def delete_all_filles_in_dir(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            os.remove(os.path.join(root, file))
