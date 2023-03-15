# -*- coding: UTF-8 -*-

import urllib.request
import urllib.parse
import re
import os
import json
import argparse
from multiprocessing import Pool
from tqdm import tqdm

class Pixiv_Downloader:

    def __init__(self, tag, output_dir, config_path, max_num=1000, max_page_num=100, process_num=10, use_vip=False, must_in_tags = [], must_out_tags = [], force_ai = 2, like_threshold=0):
        self.tag = tag
        self.output_dir = output_dir
        self.max_num = max_num
        self.max_page_num = max_page_num
        self.use_vip = use_vip
        self.must_in_tags = must_in_tags
        self.must_out_tags = must_out_tags
        self.force_ai = force_ai
        self.like_threshold = like_threshold
        self.process_num = process_num

        self.config = json.load(open(config_path, 'r'))
        self.headers = self.config['headers']
        self.version_id = self.config['version_id']

    def convert_info_to_dict(self, infos):
        infos = str(infos)[2:-1]
        formal_infos = re.sub("(?<=:)false(?=,)", "False", infos)
        formal_infos = re.sub("(?<=:)true(?=,)", "True", formal_infos)
        formal_infos = re.sub("(?<=:)null(?=(,|\}))", "None", formal_infos)
        infos_dict = eval(formal_infos)
        return infos_dict

    def download_one_img(self, url, save_path):
        req = urllib.request.Request(url=url, headers=self.headers, method='GET')
        with open(save_path, "wb") as fp:
            fp.write(urllib.request.urlopen(req, timeout=40).read())

    def work_download(self, work_info):
        must_in_tags = self.must_in_tags
        must_out_tags = self.must_out_tags
        output_dir = self.output_dir


        valid_flag = True
        for tag in must_in_tags:
            if tag not in work_info['tags']:
                valid_flag = False
                break
        for tag in must_out_tags:
            if tag in work_info['tags']:
                valid_flag = False
                break
        if not valid_flag:
            return 2      # not valid flag

        work_id = work_info['id']

        work_url = "https://www.pixiv.net/ajax/illust/{:s}/pages?lang=zh&version={:s}".format(work_id, self.version_id)
        work_main_url = "https://www.pixiv.net/artworks/{:s}".format(work_id)

        main_req = urllib.request.Request(url=work_main_url, headers=self.headers, method='GET')
        req = urllib.request.Request(url=work_url, headers=self.headers, method='GET')
        work_success = False
        for try_id in range(5):
            try:
                main_response = urllib.request.urlopen(main_req, timeout=40)
                response = urllib.request.urlopen(req, timeout=40)
                work_success = True
            except Exception as e:
                print("Exception in {:d}-th download of {:s}, work: {:s}".format(try_id+1, work_id, work_url), e)
            else:
                break
        if not work_success:
            return 4    # fail to connect work

        main_info = main_response.read()
        like_count = re.search('"likeCount":\d+', str(main_info)).group()[12:]
        like_count = re.sub(',', '', like_count)
        like_count = int(like_count)

        if like_count < self.like_threshold:
            return 3  # likes below threshold

        image_infos = response.read()
        image_infos_dict = self.convert_info_to_dict(image_infos)

        all_success = 0

        for image_i in range(len(image_infos_dict['body'])):
            image_info = image_infos_dict['body'][image_i]
            image_url = image_info['urls']['original']
            image_url = re.sub('\\\\/', '/', image_url)
            postfix = os.path.splitext(image_url)[1]
            output_path = os.path.join(output_dir, "{:s}-{:02d}{:s}".format(work_id, image_i, postfix))

            success = 1
            for try_id in range(5):
                try:
                    self.download_one_img(image_url, output_path)
                except Exception as e:
                    print("Exception in {:d}-th download of {:s}, img: {:s}".format(try_id+1, work_id, image_url), e)
                else:
                    success = 0
                    break
            all_success = all_success | success
        return all_success



    def __call__(self):
        tag = self.tag
        output_dir = self.output_dir
        max_num = self.max_num

        formal_tag = re.sub("\(", "%28", tag)
        formal_tag = re.sub("\)", "%29", formal_tag)

        work_data = []
        page_num = 0

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        while len(work_data) < max_num and page_num < self.max_page_num:

            page_num += 1

            url = "https://www.pixiv.net/ajax/search/artworks/{:s}?word={:s}&order=date_d&mode=all&p=2&s_mode=s_tag_full&type=all&lang=zh&version={:s}".format(tag, formal_tag, self.version_id)
            if page_num > 1:
                url += "&p={:d}".format(page_num)

            req = urllib.request.Request(url=url, headers=self.headers, method='GET')
            try:
                response = urllib.request.urlopen(req, timeout=40)
            except Exception as e:
                print("Exception in fetching page {:d}".format(page_num), e)
                return

            work_infos = response.read()

            work_infos_dict = self.convert_info_to_dict(work_infos)
            work_data_info = work_infos_dict['body']['illustManga']['data']
            if self.force_ai:
                work_data_info = [info for info in work_data_info if info['aiType']==self.force_ai]
            work_data += work_data_info

        work_data = work_data[:max_num]
        with Pool(processes=self.process_num) as pool:
            # pool.imap(self.work_download, work_data)
            download_result = list(tqdm(pool.imap(self.work_download, work_data), total=len(work_data)))

def start_download(args):

    downloader = Pixiv_Downloader(args.tag,
                                  config_path=args.config_path,
                                  output_dir=args.output_dir,
                                  max_num = args.max_num,
                                  max_page_num = args.max_page_num,
                                  process_num = args.process_num,
                                  use_vip = args.use_vip,
                                  must_in_tags = args.must_in_tags,
                                  must_out_tags = args.must_out_tags,
                                  force_ai = args.force_ai,
                                  like_threshold = args.like_threshold,
                                  )
    downloader()

if __name__  == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', type=str, help='specify the tag of images for crawling')
    parser.add_argument('--config_path', default='./default.json', type=str, help='specify the path of network configuration file')
    parser.add_argument('--output_dir', type=str, help='specify the directory for saving downloaded images')
    parser.add_argument('--max_num', type=int, default=1000, help='specify the max number of works for downloading')
    parser.add_argument('--max_page_num', type=int, default=100, help='specify the max number of pages for downloading')
    parser.add_argument('--process_num', type=int, default=10, help='set the number of processes for downloading, 10 is recommended, too high value may get banned by pixiv')
    parser.add_argument('--use_vip', action='store_true', help='use premium to sort images by popularaity')
    parser.add_argument('--force_ai', type=int, default=0, choices=[0, 1, 2],
                        help='specific whether downloading AI generated pics, 1 for no ai, 2 for only ai, and 0 for all')
    parser.add_argument('--like_threshold', type=float, default=0.,
                        help='filter works having likes less than threshold out')
    parser.add_argument('--must_in_tags', nargs='*', default=[], type=str,
                        help='only download works with specific tags')
    parser.add_argument('--must_out_tags', nargs='*', default=[], type=str,
                        help='filter works with specific tags out')
    args = parser.parse_args()

    start_download(args)