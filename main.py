from pydub import AudioSegment
from demo_pitch import *
import pandas as pd
import numpy as np


def compress_data_frame(df):
    # add_column = pd.DataFrame({"Duration": [0] * df.shape[0]})
    # df = df.join(add_column)
    duration = []
    interval_start = 0
    interval_end = 0
    remove_counter = 0
    start_index = 0

    df.loc[:, 'notes'] = df.loc[:, 'notes'].round(decimals=1)

    for i, _ in enumerate(df.iterrows()):
        print(i)
        if i != 0:
            if df.loc[i, 'notes'] != df.loc[start_index, 'notes']:
                interval_end = df.loc[i, 'time_of_notes']
                duration.append(interval_end - interval_start)
                interval_start = df.loc[i, 'time_of_notes']
                start_index = i
            else:
                print("removed row number: ", i)
                remove_counter = remove_counter + 1
                df = df.drop(i)
        else:
            interval_start = df.iloc[0, df.columns.get_loc('time_of_notes')]
            start_index = 0
    df.reset_index(inplace=True)
    df['duration'] = pd.Series(duration)
    df.drop('index', axis=1, inplace=True)
    return df


def find_identical_note_in_other_table(table, specific_note, accuracy=1):
    # Step #1. Round decimal values of notes
    updated_table = table.loc[:, 'notes'].round(decimals=accuracy)

    # Step #2. find the relevant rows with the matching note
    constraints = updated_table == round(specific_note, accuracy)
    matching_note_rows = table.loc[constraints, :]

    return matching_note_rows


def creating_2_tables_for_small_matching(table1, table2):
    # i want to hear the first one till at least 3/4 of it so im gonna check when i can cut i cut it
    # for the second one im gonna check the first 1/4
    # for these two i need the length of the song
    # im gonna check in o(n^2) matching notes and

    time_first_table = table1.tail(1).iloc[0, 0]
    time_first_table = time_first_table / 4

    time_second_table = table2.tail(1).iloc[0, 0]
    time_second_table = time_second_table / 4

    specific_notes_1 = table1[table1["time_of_notes"] > 3*time_first_table]  # last 1/4 notes in 1st song

    specific_notes_2 = table2[table2["time_of_notes"] < time_second_table]  # first 1/4 notes in 2nd song

    return specific_notes_1, specific_notes_2


def find_matching_notes_in_a_small_part_of_songs(table1, table2):
    updated_table1, updated_table2 = creating_2_tables_for_small_matching(table1, table2)
    note_and_matches = dict()
    notes = updated_table1.loc[:, 'notes']
    for i, note in enumerate(notes):
        result = find_identical_note_in_other_table(updated_table2, note)
        if not result.empty:
            # print("Note number ", i, " is:", note, " was found.")
            note_and_matches[i] = result
            print(" ")
            print("row number: ", i, "Friend_A.wav")
            print(updated_table1.iloc[i, :])
            print("Found match in file: pirate_of_the_caribian.wav")
            print(result)
            print(" ")

    # If dictionary is empty which means there were no matching notes
    if not bool(note_and_matches):
        print("wwwwwwwwwwwwwwwwwwwwowwww 1/4 is rly not matching")
        note_and_matches=find_matching_notes_in_full_songs(table1,table2)
    return note_and_matches

def find_matching_notes_in_full_songs(table1, table2):
    notes = table1.loc[:, 'notes']
    note_and_matches = dict()
    for i, note in enumerate(notes):
        result = find_identical_note_in_other_table(table2, note)
        if not result.empty:
            # print("Note number ", i, " is:", note, " was found.")
            note_and_matches[i] = result
            print("*********************")
            print("row number: ", i, "Friend_A.wav")
            print(table1.iloc[i, :])
            print("Found match in file: pirate_of_the_caribian.wav")
            print(result)
            print("*********************")
    return note_and_matches


def get_timestamp_of_matching(df, index):
    timestamp_in_sec = df.iloc[index, 0]  # 0 means "time_of_notes"
    timestamp_in_msec = timestamp_in_sec * 1000
    return timestamp_in_msec


def merge_songs(timestamp1, timestamp2):
    song1 = AudioSegment.from_wav("audio_files/Friend_A.wav")
    song1 = song1[0:timestamp1]
    song1.export('./new_audio/Friend_A_short.wav', format="wav")

    song2 = AudioSegment.from_wav("./audio_files/pirate_of_the_caribian.wav")
    song2 = song2[timestamp2:]
    song2.export('./new_audio/pirate_of_the_caribian_short.wav', format="wav")

    result = song1 + song2

    result.export("./new_audio/merged_result.wav", format="wav")

#def the_chosen_ones():
#TODO: picking which note will ne the one i merge on

if __name__ == '__main__':
    first = './audio_files/Friend_A.wav'
    second = './audio_files/pirate_of_the_caribian.wav'
    list_files = [first, second]
    files_meta_data = dict()
    for filename in list_files:
        # returning list of: time_of_notes, notes, confidences, list_of_amplitudes
        raw_data_table = get_meta_data_for_song(filename)
        print(raw_data_table)
        files_meta_data[filename] = compress_data_frame(raw_data_table)

    matching_dict = find_matching_notes_in_a_small_part_of_songs(files_meta_data[first], files_meta_data[second])

    if bool(matching_dict):
        print(matching_dict.keys())
        print("For the first song time stamp:")
        t1_end = get_timestamp_of_matching(files_meta_data[first], list(matching_dict.keys())[0])

        print("\nFor the second song time stamp:")
        t2_start = get_timestamp_of_matching(files_meta_data[second], 38)

        merge_songs(t1_end, t2_start)

    else:
        print("no matching tabs at all")