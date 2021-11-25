# pbooru-downloader
A downloader for The Permanent Booru

```
usage: download.py [-h] [--overwrite] [--url URL] [--proxy PROXY]
                   [--tor-browser] [--filenamer FILENAMER]
                   [--start-from START_FROM] [--disable-progressbar] [--tags]
                   [-a] [-o] [-f] [-u] [--mime] [--gateway GATEWAY]
                   [--gateway-proxy GATEWAY_PROXY]
                   path

The Permanent Booru Downloader

positional arguments:
  path                  data directory

optional arguments:
  -h, --help            show this help message and exit
  --overwrite           overwrite config file
  --url URL             default: http://owmvhpxyisu6fgd7r2fcswgavs7jly4znldaey
                        33utadwmgbbp4pysad.onion
  --proxy PROXY         default: socks5h://localhost:9050 use
                        socks5h://localhost:9150 for tor browser
  --tor-browser         alias for '--proxy socks5h://localhost:9150'
  --filenamer FILENAMER
                        filename compiler defenitions file
  --start-from START_FROM
                        offset the starting post
  --disable-progressbar
                        disables the progress bar
  --tags                save tags as .txt alongside files

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
