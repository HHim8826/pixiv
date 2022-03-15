<h1 align="center">- pixiv異步爬蟲 -</h1>
<p align="center">
<img src="https://raw.githubusercontent.com/HHim8826/pixiv_dl/main/img/c1.png" width="750">
</p>
<p align="center">
<img src="https://img.shields.io/badge/version-V2.1.1-green.svg?longCache=true&style=for-the-badge">
<img src="https://img.shields.io/pypi/pyversions/pixiv_dl?style=for-the-badge">
<img src="https://img.shields.io/badge/license-MIT-blue.svg?longCache=true&style=for-the-badge">
</p>

## 使用指南
### 編譯版本

從[Release頁面](https://github.com/HHim8826/pixiv_dl/releases)頁面下載並解壓壓縮包，修改配置文件pixiv_cookie.toml後運行.exe文件即可
### 源代碼版本

1.下載代碼倉庫，並修改配置文件pixiv_cookie.toml
```
git clone https://github.com/HHim8826/pixiv.git
cd pixiv
vim pixiv_cookie.toml
```
2.安裝Python 3.7或更高版本，並使用pip安裝依賴
```
pip install -r requirements.txt
```
3.啟動腳本
```
python pixiv_img_async.py
```
