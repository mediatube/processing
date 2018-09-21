# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import mimetypes
import random
import shutil
import socket
import time

from moviepy.config import change_settings
from moviepy.editor import *

change_settings({"FFMPEG_BINARY": "ffmpeg"})
from rq import get_current_job

from ffmpeg_runner import FFMPegRunner

last_call_time = time.time()
path_home = './'  # os.path.abspath('.')
path_shared = './shared'
path_local = './local'
silence01s_path = os.path.join(path_home, 'Silence01s.mp3')


def process_status_handler(old, new):
    global last_call_time
    if time.time() - last_call_time < 0.5:
        return 0
    last_call_time = time.time()
    job = get_current_job()
    job.meta['percent'] = new
    job.save_meta()
    return 0
    # print("From {0} to {1}".format(old, new))


def speedx_audio(file_path: str, speedx_factor: str, output_ext: str, bitrate: str):
    try:
        job = get_current_job()
        job.meta['handled_by'] = socket.gethostname()
        job.save_meta()
        # print('Current job: %s' % (job.id))
        file_path = str(file_path)
        ext = file_path[len(file_path) - 3:]
        # print(file_path, spedx_factor, output_ext, bitrate)
        if ext in ['mp3', 'aac', 'ogg', 'm4a']:
            ext_dict = {'mp3': 'libmp3lame', 'aac': 'libfdk_aac', 'ogg': 'libopus', 'm4a': 'libfdk_aac'}
            opus_bitrate = {'320k': '128000', '192k': '64000', '128k': '32000', '96k': '16000'}
            output_file_path = file_path[:-4] + str(speedx_factor) + 'x.' + output_ext
            bitrate = opus_bitrate[bitrate] if output_ext == 'ogg' else bitrate
            process_call_str = 'ffmpeg -i {0} '.format(file_path)
            process_call_str += '' if speedx_factor == '1.0' else '-filter:a "atempo={0}" '.format(speedx_factor)
            process_call_str += '-acodec {0} ' \
                                '-b:a {1} ' \
                                '-vbr on ' \
                                '-compression_level 0 ' \
                                '-frame_duration 60 ' \
                                '-ac 1 -vn ' \
                                '{2}'.format(ext_dict[output_ext], opus_bitrate[bitrate], output_file_path)
            os.chdir(path_home)
            runner = FFMPegRunner()
            runner.run_session(process_call_str, status_handler=process_status_handler)
            return output_file_path
        else:
            return False
    except Exception:
        if os.path.exists(os.path.dirname(file_path)):
            shutil.rmtree(os.path.dirname(file_path))
        raise Exception


def extract_audio(file_path, output_ext: str, bitrate: str, split_duration=None, speedx_factor=1.0, t_start=None,
                  t_end=None, loudnorm=None):
    try:
        output_ext = 'mp3' if output_ext == 'aac' else output_ext
        mimetypes.add_type('audio/mp4', '.m4a')
        job = get_current_job()
        job.meta['handled_by'] = socket.gethostname()
        job.save_meta()
        # file_path = file_path.encode('utf-8')
        tmpdir = os.path.dirname(file_path)
        tmpdir = os.path.basename(tmpdir)
        tmpdir_shared = os.path.join(path_shared, tmpdir)
        tmpdir = os.path.join(path_local, tmpdir)
        output_filename = os.path.basename(file_path)
        if not os.path.exists(tmpdir):
            os.mkdir(tmpdir)
        # print('Current job: %s' % (job.id))
        # file_path = os.path.relpath(file_path)
        ext = file_path[len(file_path) - 3:]
        if not t_end is None:
            hh = int(t_end / 3600)
            mm = int((t_end - hh * 3600) / 60)
            ss = int(t_end - hh * 3600 - mm * 60)
            ms = int((t_end - int(t_end)) * 100)
            t = '{0}:{1}:{2}.{3}'.format(str(hh), str(mm), str(ss), str(ms))
        else:
            t = ''
        if not t_start is None:
            hh = int(t_start / 3600)
            mm = int((t_start - hh * 3600) / 60)
            ss = int(t_start - hh * 3600 - mm * 60)
            ms = int((t_start - int(t_start)) * 100)
            ss = '{0}:{1}:{2}.{3}'.format(str(hh), str(mm), str(ss), str(ms))
        else:
            ss = ''
        # print(file_path, split_duration, output_ext, bitrate)
        if ext in ['mp3', 'aac', 'ogg', 'm4a', 'mp4']:
            ext_dict = {'mp3': 'libmp3lame', 'aac': 'libfdk_aac', 'ogg': 'libopus', 'm4a': 'libfdk_aac'}
            opus_bitrate = {'320k': '128000', '192k': '64000', '128k': '32000', '96k': '16000'}
            aac_bitrate = {'320k': 320000, '192k': 192000, '128k': 128000, '96k': 96000}
            bitrate = opus_bitrate[bitrate] if output_ext == 'ogg' else bitrate
            output_filename = output_filename[:-4] + 'x' + str(speedx_factor) + '.' + output_ext
            output_file_path_local = os.path.join(tmpdir, output_filename)
            output_file_path_shared = os.path.join(tmpdir_shared, output_filename)
            # print(output_file_path)
            try:
                ss_to = (random.randrange(1, 100, 1) + random.randrange(1, 100, 1)) / 1000
                process_call_str = 'ffmpeg '
                # process_call_str += '-i {0} '.format(silence01s_path)
                process_call_str += '' if t_start is None else '-ss {0} '.format(str(ss))
                process_call_str += '' if t_end is None else '-to {0} '.format(str(t))
                process_call_str += '-i {0} '.format(file_path)
                # process_call_str += '-filter_complex '
                if speedx_factor == 1.0:
                    if loudnorm:
                        process_call_str += '-filter_complex "[0:a]loudnorm=I=-20:TP=-1.5[out]" -map "[out]" '
                else:
                    if loudnorm:
                        process_call_str += '-filter_complex '
                        process_call_str += '"[0:a]atempo={1}[b]; ' \
                                            '[b]loudnorm=I=-20:TP=-1.5[out]" '.format(str(ss_to), str(speedx_factor))
                        process_call_str += '-map "[out]" '
                    else:
                        process_call_str += '-filter_complex '
                        process_call_str += '"[0:a]atempo={1}[out]" '.format(str(ss_to), str(speedx_factor))
                        process_call_str += '-map "[out]" '
                # process_call_str += '-map "[out]" '
                # process_call_str += '' if speedx_factor == 1.0 else '-filter:a "atempo={0}" '.format(str(
                # speedx_factor))
                process_call_str += '-acodec {0} '.format(ext_dict[output_ext])
                process_call_str += '-b:a {0} '.format(bitrate)
                if output_ext == 'ogg':
                    process_call_str += '-vbr on '
                    process_call_str += '-compression_level 0 '
                    process_call_str += '-frame_duration 60 '
                    process_call_str += '-ac 1 '
                process_call_str += '-vn '
                # process_call_str += '-map 0:a:0 '
                if split_duration:
                    process_call_str += '-f segment -segment_time {0} '.format(str(split_duration))
                    process_call_str += '{0}_%02d.{1}'.format(output_file_path_local[:-4], output_ext)
                else:
                    process_call_str += '-avoid_negative_ts make_zero '
                    process_call_str += '{0}'.format(output_file_path_local)
                os.chdir(path_home)
                runner = FFMPegRunner()
                runner.run_session(process_call_str, status_handler=process_status_handler)
                try:
                    clip = VideoFileClip(file_path)
                    duration = clip.duration
                except Exception:
                    try:
                        if output_ext == 'aac':
                            filesize = os.path.getsize(output_file_path_local)
                            bitrate_int = aac_bitrate[bitrate]
                            duration = 8*filesize/bitrate_int
                            job.meta['duration'] = int(duration)
                            job.save_meta()
                            return output_file_path_shared
                        else:
                            clip = AudioFileClip(file_path)
                            duration = clip.duration
                    except Exception:
                        raise Exception
                if t_start is None and t_end is None:
                    duration = duration
                elif t_start is None and not t_end is None:
                    duration = t_end
                elif not t_start is None and t_end is None:
                    duration = duration - t_start
                elif not t_start is None and not t_end is None:
                    duration = t_end - t_start
                job.meta['duration'] = int(duration / speedx_factor)
                job.save_meta()
                return output_file_path_shared
            except Exception:
                print(Exception)
                raise Exception
        else:
            return False
    except Exception:
        if os.path.exists(os.path.dirname(output_file_path_shared)):
            shutil.rmtree(os.path.dirname(output_file_path_shared))
        if os.path.exists(os.path.dirname(output_file_path_local)):
            shutil.rmtree(os.path.dirname(output_file_path_local))
        raise Exception
