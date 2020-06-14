from pydub import AudioSegment

from audio_analytics import help_utils
from audio_analytics.demo_pitch import *
import pandas as pd


def compress_data_frame(df):
    # receives a dataframe and returns it without duplicated notes and with another column of duration of the note

    # add_column = pd.DataFrame({"Duration": [0] * df.shape[0]})
    # df = df.join(add_column)
    duration = []
    interval_start = 0
    interval_end = 0
    remove_counter = 0
    start_index = 0

    df.loc[:, 'notes'] = df.loc[:, 'notes'].round(decimals=1)

    for i, _ in enumerate(df.iterrows()):
        # print(i)
        if i != 0:
            if df.loc[i, 'notes'] != df.loc[start_index, 'notes']:
                interval_end = df.loc[i, 'time_of_notes']
                duration.append(interval_end - interval_start)
                interval_start = df.loc[i, 'time_of_notes']
                start_index = i
            else:
                # print("removed row number: ", i)
                remove_counter = remove_counter + 1
                df = df.drop(i)
        else:
            interval_start = df.iloc[0, df.columns.get_loc('time_of_notes')]
            start_index = 0
    df.reset_index(inplace=True)
    df['duration'] = pd.Series(duration)
    df.drop('index', axis=1, inplace=True)
    return df


def find_identical_notes_in_other_table(table, specific_note, accuracy=1):
    # receives note and dataframe. returns the rows with matching notes

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

    specific_notes_1 = table1[table1["time_of_notes"] > 3 * time_first_table]  # last 1/4 notes in 1st song

    specific_notes_2 = table2[table2["time_of_notes"] < time_second_table]  # first 1/4 notes in The_Bot song

    return specific_notes_1, specific_notes_2


def find_matching_notes_in_a_small_part_of_songs(table1, table2):
    # receives two dataframes and returns a dictionery of the matching notes of only part of the files
    updated_table1, updated_table2 = creating_2_tables_for_small_matching(table1, table2)
    note_and_matches = dict()
    notes = updated_table1.loc[:, 'notes']

    for i, note in enumerate(notes):
        result = find_identical_notes_in_other_table(updated_table2, note)

        if not result.empty:
            # print("Note number ", i, " is:", note, " was found.")
            note_and_matches[updated_table1.index[i]] = (table1.loc[updated_table1.index[i]], result)

    # If dictionary is empty it means there were no matching notes
    if not bool(note_and_matches):
        print("oof 1/4 is rly not matching")
        note_and_matches = find_matching_notes_in_full_songs(table1, table2)

    return note_and_matches


def find_matching_notes_in_full_songs(table1, table2):
    # receives two dataframes and returns a dictionery of the matching notes of the files
    notes = table1.loc[:, 'notes']
    note_and_matches = dict()
    for i, note in enumerate(notes):
        result = find_identical_notes_in_other_table(table2, note)
        if not result.empty:
            # print("Note number ", i, " is:", note, " was found.")
            note_and_matches[i] = (table1.loc[i], result)
            # print("*********************")
            # print("row number: ", i, "Friend_A.wav")
            # print(table1.iloc[i, :])
            # print("Found match in file: pirate_of_the_caribian.wav")
            # print(result)
            # print("*********************")
    return note_and_matches


def get_timestamp_of_matching(df, index):
    # receives a dataframe and an index of a note and returns the time that the note place
    timestamp_in_sec = df.iloc[int(index), 0]  # 0 is the index of the column "time_of_notes"
    timestamp_in_msec = timestamp_in_sec * 1000
    return timestamp_in_msec


def merge_songs(timestamp1, timestamp2, first_path, second_path):
    # receiving timestamps of two songs and their path,
    # saves the combined file and send its path
    before_merge_path = r'..\audio_files\before_combining'
    output_merge_path_wav = r"..\audio_files\output\the_merged_file.wav"

    # saving the cut part of the song that we need
    song1 = AudioSegment.from_wav(first_path)
    song1 = song1[0:timestamp1]
    song1.export(before_merge_path + r"\1.wav", format="wav")

    # saving the cut part of the song that we need
    song2 = AudioSegment.from_wav(second_path)
    song2 = song2[timestamp2:]
    song2.export(before_merge_path + r"\2.wav", format="wav")

    result = song1 + song2
    result.export(output_merge_path_wav, format="wav")  # combining the two wav sounds into one and saving it

    # deleting the cut part of the song that we save for combining
    os.remove(before_merge_path + r"\1.wav")
    os.remove(before_merge_path + r"\2.wav")

    output_merge_path_mp3 = help_utils.convert_wav_to_mp3(output_merge_path_wav)  # converting file to mp3 from wav
    return output_merge_path_mp3


def find_closest_amplitude(first_amp, df):
    # receives amp of note and a dataframe,
    # returns 1. the index of the note from the second table that is closest in its amp to the first note
    #         2. the diff between these notes
    series_of_amp_diffs = abs(df['list_of_amplitudes'] - first_amp)
    index_min = series_of_amp_diffs.idxmin()
    return index_min, series_of_amp_diffs[index_min]  # index_of_chosen_one


def final_decision(first, second, diff):
    # receives 3 lists of notes and their amp diff,
    # returns the index of the pair of notes with the least diff and their diff
    d = {'first': first, 'second': second, 'diff': diff}
    df = pd.DataFrame(d)
    row = df.loc[df['diff'].idxmin()]
    return row[0], row[1], row[2]


def begin_the_merge(filename1, filename2):  # receives two path of audio files, creat the new merged file and returns it path
    list_files = [filename1, filename2]
    files_meta_data = dict()
    for filename in list_files:
        # returning list of: time_of_notes, notes, confidences, list_of_amplitudes
        raw_data_table = get_meta_data_for_song(filename)
        # print(raw_data_table)
        files_meta_data[filename] = compress_data_frame(raw_data_table)

    matching_dict = find_matching_notes_in_a_small_part_of_songs(files_meta_data[filename1], files_meta_data[filename2])
    index_of_closest_from_first = list(matching_dict.keys())  # notes from first file
    index_of_closest_from_second = []  # notes from second file
    diff_of_amp = []  # different of notes
    for index in index_of_closest_from_first:  # going over the notes from the first file that have matches
        table = matching_dict[index][1]  # the matching table of the note
        amp_of_first = files_meta_data[filename1].loc[index, 'list_of_amplitudes']  # amp of the  note

        # sending amp of note from first song and get the index of the matching table that has the closest amp,
        # and the two notes amp different
        idx_min, min_diff = find_closest_amplitude(amp_of_first, table)
        index_of_closest_from_second.append(idx_min)  # add to the list of the notes from the second song the most
        # matching note in its amp
        diff_of_amp.append(min_diff)

    final_index_of_first, final_index_of_second, final_diff = final_decision(index_of_closest_from_first,
                                                                             index_of_closest_from_second, diff_of_amp)

    if bool(matching_dict):  # if there are matching notes

        t1_end = get_timestamp_of_matching(files_meta_data[filename1], final_index_of_first)

        t2_start = get_timestamp_of_matching(files_meta_data[filename2], final_index_of_second)

        output_path = merge_songs(t1_end, t2_start, filename1, filename2)
        return output_path
    else:  # if there no matching notes
        print("no matching tabs at all")
        return -1
