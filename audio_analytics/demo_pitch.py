from aubio import source, pitch
from numpy import zeros, hstack
import pandas as pd
import os.path
from numpy import array, ma
import matplotlib.pyplot as plt
from audio_analytics.demo_waveform_plot import get_waveform_plot, set_xlabels_sample2time


def get_wave_amplitude_list(filename, block_size=4096):
    # returns a list of amplitude of each note
    hop_s = block_size

    allsamples_max = zeros(0, )
    downsample = 1
    samplerate = 44100
    a = source(filename, samplerate, hop_s)  # source file

    total_frames = 0
    while True:
        samples, read = a()
        # keep some data to plot it later
        new_maxes = (abs(samples.reshape(hop_s // downsample, downsample))).max(axis=0)
        allsamples_max = hstack([allsamples_max, new_maxes])
        total_frames += read
        if read < hop_s: break
    allsamples_max = (allsamples_max > 0) * allsamples_max

    return allsamples_max


def array_from_text_file(filename, dtype='float'):
    filename = os.path.join(os.path.dirname(__file__), filename)
    return array([line.split() for line in open(filename).readlines()],
                 dtype=dtype)


# TODO: just make sure to call and fix the following function show_plots

def get_plots(pitches, confidences, hop_s, filename, samplerate, tolerance):
    # saves an image of the info of the audio file
    skip = 1
    pitches = array(pitches[skip:])
    confidences = array(confidences[skip:])
    times = [t * hop_s for t in range(len(pitches))]

    fig = plt.figure()

    ax1 = fig.add_subplot(311)
    ax1 = get_waveform_plot(filename, samplerate=samplerate, block_size=hop_s, ax=ax1)
    plt.setp(ax1.get_xticklabels(), visible=False)
    ax1.set_xlabel('power')

    ax2 = fig.add_subplot(312, sharex=ax1)
    ground_truth = os.path.splitext(filename)[0] + '.f0.Corrected'
    if os.path.isfile(ground_truth):
        ground_truth = array_from_text_file(ground_truth)
        true_freqs = ground_truth[:, 2]
        true_freqs = ma.masked_where(true_freqs < 2, true_freqs)
        true_times = float(samplerate) * ground_truth[:, 0]
        ax2.plot(true_times, true_freqs, 'r')
        ax2.axis(ymin=0.9 * true_freqs.min(), ymax=1.1 * true_freqs.max())
    # plot raw pitches
    ax2.plot(times, pitches, '.g')
    # plot cleaned up pitches
    cleaned_pitches = pitches
    # cleaned_pitches = ma.masked_where(cleaned_pitches < 0, cleaned_pitches)
    # cleaned_pitches = ma.masked_where(cleaned_pitches > 120, cleaned_pitches)
    cleaned_pitches = ma.masked_where(confidences < tolerance, cleaned_pitches)
    ax2.plot(times, cleaned_pitches, '.-')
    # ax2.axis( ymin = 0.9 * cleaned_pitches.min(), ymax = 1.1 * cleaned_pitches.max() )
    # ax2.axis( ymin = 55, ymax = 70 )
    plt.setp(ax2.get_xticklabels(), visible=False)
    ax2.set_ylabel('f0 (midi)')

    # plot confidence
    ax3 = fig.add_subplot(313, sharex=ax1)
    # plot the confidence
    ax3.plot(times, confidences)
    # draw a line at tolerance
    ax3.plot(times, [tolerance] * len(confidences))
    ax3.axis(xmin=times[0], xmax=times[-1])
    ax3.set_ylabel('condidence')
    set_xlabels_sample2time(ax3, times[-1], samplerate)
    # plt.show()
    directory_path_img_output = r'..\img_files'
    list_of_img_files = os.listdir(directory_path_img_output)
    current_image = str(len(list_of_img_files) + 1)
    full_path = os.path.join(directory_path_img_output, current_image + '.png')
    plt.savefig(full_path)
    return full_path


def get_meta_data_for_song(filename, plot_song=False):
    # receives path to audio file and returns- a dataframe of the data or an image of the information of the file
    downsample = 1
    samplerate = 44100 // downsample
    # if len(sys.argv) > 2:
    #     samplerate = int(sys.argv[2])

    win_s = 4096 // downsample  # fft size
    hop_s = 512 // downsample  # hop size

    s = source(filename, samplerate, hop_s)
    samplerate = s.samplerate

    tolerance = 0.8

    pitch_o = pitch("yin", win_s, hop_s, samplerate)
    pitch_o.set_unit("midi")
    pitch_o.set_tolerance(tolerance)

    pitches = []
    confidences = []
    relevant_amplitudes = []  # Above threshold

    # total number of frames read
    total_frames = 0
    index = 0
    counter_confidence = 0
    list_of_amplitudes = get_wave_amplitude_list(filename, block_size=hop_s)
    # print("(id) time note confidence amplitude")
    notes = list()
    time_of_notes = list()
    while True:
        samples, read = s()
        note = pitch_o(samples)[0]
        notes.append(note)
        # pitch = int(round(pitch))
        confidence = pitch_o.get_confidence()

        time_of_note = total_frames / float(samplerate)

        if confidence > 0.8 and note != 0.0:
            pitches += [note]
            relevant_amplitudes.append(list_of_amplitudes[index])
            confidences += [confidence]
            time_of_notes.append(time_of_note)

        total_frames += read
        #     print("(%d) %f %f %f %f" % (
        #         counter_confidence, time_of_note, note, confidence, list_of_amplitudes[counter]))
        #    counter_confidence += 1

        index += 1
        if read < hop_s: break

    if plot_song:
        img_path = get_plots(pitches, confidences, hop_s, filename, samplerate, tolerance)
        return img_path
    else:
        data = {'time_of_notes': time_of_notes,
                'notes': pitches,
                'confidences': confidences,
                'list_of_amplitudes': relevant_amplitudes
                }

        return pd.DataFrame(data)

    # plt.savefig(os.path.basename(filename) + '.svg')
