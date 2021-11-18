# pbooru-downloader
A downloader for The Permanent Booru

```
usage: download.py [-h] [--overwrite] [--url URL] [--proxy PROXY] [--filenamer FILENAMER] [--start-from START_FROM] [--disable-progressbar] [-a] [-o] [-f]
                   [-u] [--mime] [--gateway GATEWAY] [--gateway-proxy GATEWAY_PROXY]
                   path

The Permanent Booru Downloader

positional arguments:
  path                  data directory

optional arguments:
  -h, --help            show this help message and exit
  --overwrite           overwrite config file
  --url URL             default: http://owmvhpxyisu6fgd7r2fcswgavs7jly4znldaey33utadwmgbbp4pysad.onion
  --proxy PROXY         default: socks5h://localhost:9050 use socks5h://localhost:9150 for tor browser
  --filenamer FILENAMER
                        filename compiler defenitions file
  --start-from START_FROM
                        offset the starting post
  --disable-progressbar
                        disables the progress bar

search options:
  -a , --and            tags to download (AND)
  -o , --or             tags to download (OR)
  -f , --filter         tags to filter
  -u , --unless         filter only if none of these are present
  --mime                mimetype

gateway options:
  --gateway GATEWAY     IPFS gateway. Default http://localhost:8080
  --gateway-proxy GATEWAY_PROXY
                        proxy for the gateway
```
