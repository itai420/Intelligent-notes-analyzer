from datetime import datetime
from telegram.ext import Updater, Dispatcher
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import logging
import os
from telegram import Bot

from audio_analytics.help_utils import convert_mp3_to_wav, delete_all_filles_in_dir
from audio_analytics.demo_pitch import get_meta_data_for_song
from audio_analytics.the_merger import begin_the_merge


class My_Brilliant_Bot:

    def __init__(self, token):
        self.token = token

        # status_merge:
        # (0) - waiting for files
        # (1) - recieved single file (waiting for another file)
        # (2) - recieved two files
        # (3) - Time is up, merge resquest was discarded

        self.status_merge = -1

        # status_info:
        # (0) - waiting for single
        # (1) - recieved single file

        self.status_info = -1
        self.merged_request_timestamp = ''
        self.info_request_timestamp = ''
        self.updater = Updater(token=self.token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.bot = Bot(token=self.token)
        # self.bot_is_running = True

        # Registering /start as a command
        # start_handler = CommandHandler('starting', self.starting)
        # self.dispatcher.add_handler(start_handler)

        help_handler = CommandHandler('help', self.help_handler)
        self.dispatcher.add_handler(help_handler)

        audio_file_handler = MessageHandler(Filters.audio, self.receive_audio_func_handler)
        self.dispatcher.add_handler(audio_file_handler)

        shutdown_handler = CommandHandler('shutdown', self.shutdown)
        self.dispatcher.add_handler(shutdown_handler)

        info_handler = CommandHandler('info', self.get_info)
        self.dispatcher.add_handler(info_handler)

        merge_handler = CommandHandler('merge', self.merging)
        self.dispatcher.add_handler(merge_handler)

        # In case the command is unknown
        unfamiliar_cmd_handler = MessageHandler(Filters.command, self.unfamiliar_func_handler)
        self.dispatcher.add_handler(unfamiliar_cmd_handler)

        #  Registering handler that listens for regular messages and returns
        echo_handler = MessageHandler(Filters.text, self.unfamiliar_message)
        self.dispatcher.add_handler(echo_handler)

        self.updater.start_polling()

    def help_handler(self, update, context):
        merge_command_description = "Description: You should send two mp3 files, and the Inteligent Bot will merge " \
                                    " the two songs and will send you back"

        info_command_description = "Description: You should send single mp3 file, and the Inteligent Bot will send " \
                                   "the statistics about the song"

        shutdown_command_description = "Description: Shutdown the brilliant bot"

        whole_message = 'The following commands are available:\n1. /merge\n' + merge_command_description + \
                        '\n2. /info\n' + info_command_description + '\n3. /shutdown\n' + shutdown_command_description

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=whole_message)

    def unfamiliar_func_handler(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Unfamiliar command,\nsend "/help" for getting the available commands')

    def unfamiliar_message(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Please enter a command starting with /')

    def i_flag(self):
        # -1 if no request
        # 0 if waiting
        # 1 if time is up
        # true if waiting for info and time is'nt over
        if self.status_info != 0:
            return -1
        if (datetime.now() - self.info_request_timestamp).seconds < 120:
            return 0
        return 1

    def m_flag(self):
        # -1 if no request
        # 0 if waiting
        # 1 if time is up
        # true if waiting for info and time is'nt over
        if self.status_merge != -1:
            if (datetime.now() - self.merged_request_timestamp).seconds < 120:
                return 0
            return 1
        return -1

    def receive_audio_func_handler(self, update, context):
        try:
            # true if waiting for merge and time is'nt over

            if self.status_info == 0 or self.status_merge == 0 or self.status_merge == 1:  # get in only after a com
                merge_flag = self.m_flag()
                info_flag = self.i_flag()
                directory_path_audio_input = r'..\audio_files\input'
                # We are downloading the audio file:
                check_time_isnt_over = (merge_flag != 1 and info_flag == -1) or (
                            info_flag != 1 and merge_flag == -1) or (info_flag != 1 and merge_flag != 1)
                if check_time_isnt_over:  # check if time isnt over so we dont dowload for nothing
                    list_of_audio_files = os.listdir(directory_path_audio_input)
                    audio_obj = context.bot.get_file(file_id=update.message.audio.file_id)
                    current_file = str(len(list_of_audio_files) + 1) + '.mp3'
                    full_current_file_path = os.path.join(directory_path_audio_input, current_file)

                    audio_obj.download(custom_path=full_current_file_path)
                    file_path_wav = convert_mp3_to_wav(input_path=full_current_file_path)
                    update.message.reply_text("Your audio has been processed.")

                    if info_flag == 0:
                        self.receive_audio_for_info(update, file_path_wav)
                    elif merge_flag == 0:
                        if self.status_merge == 0:
                            self.status_merge = 1
                            update.message.reply_text("please send another mp3 file :)")

                        else:
                            self.status_merge = -1  # 2
                            update.message.reply_text("Hii there is the second one! start merging :)")
                            self.receive_audio_for_merging(update, context, directory_path_audio_input)
                    else:
                        delete_all_filles_in_dir(directory_path_audio_input)
                else:
                    if self.status_merge != -1:
                        self.status_merge = -1
                    else:
                        self.status_info = -1
                    delete_all_filles_in_dir(directory_path_audio_input)
                    update.message.reply_text("Oops... time is up , please re-send the command☺")
            else:
                update.message.reply_text("Oops... i dont know what to do with that. please send a command first ☺")


        except Exception as e:
            delete_all_filles_in_dir(directory_path_audio_input)
            update.message.reply_text("error")

    def receive_audio_for_info(self, update, file_path):
        # recievs path of file, returns the info photo of the file and delete the file
        self.status_info = -1
        img_path = get_meta_data_for_song(filename=file_path, plot_song=True)

        self.bot.send_photo(chat_id=update.effective_chat.id,
                            photo=open(img_path, 'rb')
                            )
        os.remove(img_path)
        os.remove(file_path)

    def receive_audio_for_merging(self, update, context, dir_path):
        # receive path, returning the merged file and deletes the files
        directory_path_audio_output = os.path.join('audio_files', 'output')

        # dissect the audio files
        path_1 = os.path.join(dir_path, '1.wav')
        path_2 = os.path.join(dir_path, '2.wav')

        output_path = begin_the_merge(path_1, path_2)
        if type(output_path) is not str:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="no matching tabs at all")
        else:
            self.bot.send_audio(chat_id=update.effective_chat.id,
                                audio=open((output_path), 'rb'),
                                timeout=1000)
        os.remove(path_1)
        os.remove(path_2)
        os.remove(output_path)

    def get_info(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='I have registered info request,\nplease send single file in the next two minutes.')

        self.status_info = 0
        self.info_request_timestamp = datetime.now()

    def merging(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='I have registered merging request,\nplease send two files in the next two minutes.')
        self.status_merge = 0
        self.merged_request_timestamp = datetime.now()

        #
        #
        # #

        #
        #
        # # img_file_handler = MessageHandler(Filters.audio, receive_img_func_handler)
        # # dispatcher.add_handler(img_file_handler)
        #
        # # In case the command is unknown
        # unfamiliar_cmd_handler = MessageHandler(Filters.command, unfamiliar_func_handler)
        # dispatcher.add_handler(unfamiliar_cmd_handler)
        #
        # #  Registering handler that listens for regular messages and returns
        # echo_handler = MessageHandler(Filters.text, unfamiliar_message)
        # dispatcher.add_handler(echo_handler)

    # def starting(self, update, context):
    #     print("self.bot_is_running = ", self.bot_is_running)
    #     if not self.bot_is_running:
    #         self.bot_is_running = True
    #         self.updater.start_polling()
    #         context.bot.send_message(chat_id=update.effective_chat.id, text="Starting bot, please talk to me!")

    # def __del__(self):
    #     print('Destructor called')
    #     self.updater.stop()

    def shutdown(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Shuting down, See you next time!")
        # self.bot_is_running = False
        self.updater.stop()


if __name__ == '__main__':
    itai_bot = My_Brilliant_Bot('1288285979:AAH1vjbpdz48VkystMkp1K0BfjHlHGOdPnM')
