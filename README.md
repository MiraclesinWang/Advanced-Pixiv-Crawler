

### Features

1. Downloading pictures with multi-processes quickly 
2. Specifying tags for crawling
3. Filtering works with unwanted tags out
4. Filtering works for downloading by number of likes
5. Choosing whether to download AI generated features

## Installation Steps

\1. Clone the project into your environment.
\2. Run `pip install -r requirements.txt`.
\3. Open your VPN and start global proxy to ensure the script can get access to pixiv.net. (this step is necessary for Chinese users)
\4. Open pixiv.net and . Place your cookie in the `${your cookie here}` in default.json.
\5. Specific a tag and output directory for downloading, and set other optional arguments as you need. Then run the script. Example:

```
python pixiv_crawler.py \
--tag %E5%88%BB%E6%99%B4 \
--output_dir ./output \
--max_num 300 \
--max_page_num 20 \
--force_ai 2 \
--process_num 10 \
--like_threshold 0 \
--must_in_tags loli \
--must_out_tags r18
```

Replace the tag with an existing tag of pixiv.net.

\6. Wait for downloading as enjoy pictures of your wife! 

## TODO

1. Add pyqt gui (maybe...)
2. Add implementation for sorting work by popularity with premium (which I still don't have yet)
