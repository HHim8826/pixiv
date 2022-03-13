#-*- coding: utf-8 -*
import os
import requests
import toml
import math
import asyncio
import aiohttp
import aiofiles
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor,as_completed


banner = '''  _                                                       
 |_)  o      o           /\    _      ._    _     ._      
 |    |  ><  |  \/      /--\  _>  \/  | |  (_  o  |_)  \/ 
                    __            /               |    /  
'''

def get_config():
    cfg = toml.load(os.path.expanduser('./pixiv_cookie.toml'))
    return cfg


def premium_search(name:str,order_num:int,mode_num:int,page_num:int,cfg:dict,only_illust=True):
    headers = {'referer' : "https://www.pixiv.net/ranking.php",'cookie' : f"{cfg['login']['cookie']}",'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",'Content-Type': 'application/json'}
    
    order = ['popular_d','popular_male_d','popular_female_d']
    mode = ['s_tag','safe','r18']

    params = {
        'word' : {name},
        'order' : {order[order_num]},
        'mode' : {mode[mode_num]},
        's_mode' : 's_tag',
    }

    if only_illust:
        params['type'] = 'illust_and_ugoira'
    else:
        params['type'] = 'all'
    
    for pages in range(page_num):
        
        params['p'] = pages+1
     
        url = f'https://www.pixiv.net/ajax/search/artworks/{name}'
        req = requests.get(url,headers=headers,params=params)
        
        json_data = req.json()
        target_data = json_data['body']['illustManga']['data']
        
        for data_info in target_data:
            illusts_id = data_info["id"]
            yield illusts_id

def pixiv_search(name:str,cfg:dict,mode=0) -> list:
    
    headers = {'referer' : "https://www.pixiv.net/",'cookie' : f"{cfg['login']['cookie']}",'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36"}
    
    url = f'https://www.pixiv.net/ajax/search/illustrations/{name}'
    
    params = {'word' : name}
    
    if mode == 0:
            params['mode'] = 'all'
    elif mode == 1:
            params['mode'] = 'safe'
    elif mode == 2:
            params['mode'] = 'r18'

    req = requests.get(url,headers=headers,params=params)
    req = req.json()
     
    try:
        # get id
        body_data = req['body']['illust']['data']
        for info in body_data:
            id_num = info['id']
            yield id_num
            
                        
    except KeyError:

        body_data = req['body']['popular']['permanent']
        
        for info in body_data: 
            id_num = info['id']
            yield id_num
        
                    
        body_data_1 = req['body']['popular']['recent']
        for info_2 in body_data_1:
            id_num_2 = info_2['id']
            yield id_num_2

def get_user_illusts(user_id,cfg:dict):
    headers = {'referer' : "https://www.pixiv.net/ranking.php",'cookie' : f"{cfg['login']['cookie']}",'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",'Content-Type': 'application/json'}
    url = f'https://www.pixiv.net/ajax/user/{user_id}/profile/all'

    req = requests.get(url,headers=headers)
    req = req.json()
    for illusts_ids in req['body']['illusts']:   
        yield illusts_ids

async def popular_search(search_name:str, bookmark:int, cfg:dict, page=100, mode=0):
    headers = {'referer' : "https://www.pixiv.net",'cookie' : f"{cfg['login']['cookie']}",'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",'Content-Type': 'application/json'}
    url = f'https://www.pixiv.net/ajax/search/illustrations/{search_name}'
    id_list = []
    dl_list = []
    payload = {
        'word' : search_name,
        'p' : 1 ,
        's_mode' : 's_tag',
        'type' : 'illust_and_ugoira'
    }

    if mode == 0:
            payload['mode'] = 'all'
    elif mode == 1:
            payload['mode'] = 'safe'
    elif mode == 2:
            payload['mode'] = 'r18'
    
    req_data = requests.get(url,params=payload,headers=headers).json()
    total_illust = req_data['body']['illust']['total']
    max_page = math.ceil(total_illust/60)
    
    if page > max_page:
        page = max_page
        
    with ThreadPoolExecutor(50) as th:
        th_ = []
        th2_ = []
        th3_ = []
        
        for page_num in range(1,page+1):
            payload['p'] = page_num
            reqs = th.submit(requests.get,url,headers=headers,params=payload)
            th_.append(reqs)

        for req in as_completed(th_):
            json_data = req.result().json()
            data = json_data['body']['illust']['data']
            for id_ in data:
                id_list.append(id_['id'])
        
        for id_ in id_list:
            illust_url = f'https://www.pixiv.net/ajax/illust/{id_}'
            illust_reqs = th.submit(requests.get,illust_url,headers=headers)
            th2_.append(illust_reqs)
        
        for illust_req in as_completed(th2_):
            json_data = illust_req.result().json()
            if json_data['body']['bookmarkCount'] > bookmark:
                dl_list.append(json_data['body']['urls']['original'])
        
        for dl_url in dl_list:
            dl_reqs = th.submit(requests.get,dl_url,headers=headers)
            th3_.append(dl_reqs)
        
        for dl_req in as_completed(th3_):
            img_data = dl_req.result()
            file_name = img_data.request.url.split('/')[-1]
            content_data = img_data.content
            async with aiofiles.open(f'./img/{file_name}','wb') as aiof:
                await aiof.write(content_data)
              
                
def ranking(page:int, cfg:dict,mode_num=0,r18mode=0,only_illust=False):
    headers = {'referer' : "https://www.pixiv.net/ranking.php",'cookie' : f"{cfg['login']['cookie']}",'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",'Content-Type': 'application/json'}
    url = f'https://www.pixiv.net/ranking.php'
    
    if mode_num == 0:
        mode = 'daily'
    elif mode_num == 1:
        mode = 'weekly'
    elif mode_num == 2:
        mode = 'monthly'
    elif mode_num == 3:
        mode = 'rookie'
    elif mode_num == 4:
        mode = 'original'
    elif mode_num == 5:
        mode = 'female'
    elif mode_num == 6:
        if r18mode == 0:
            mode = 'daily_r18'
        elif r18mode == 1:
            mode = 'weekly_r18'
        elif r18mode == 2:
            mode = 'male_r18'
        elif r18mode == 3:
            mode = 'female_r18'
    elif mode_num == 7:
        mode = 'male'
    
    params = {
        'format' : 'json',
        'mode' : mode
    }
    
    if mode == 'daily' or 'weekly' or 'monthly' or 'rookie' and only_illust:
        params['content'] = 'illust'

    with ThreadPoolExecutor(4) as th:
        ids = []
        th_ = []
        for page_num in range(page):
            params['p'] = page_num+1
            reqs = th.submit(requests.get,url,headers=headers,params=params)
            th_.append(reqs)

        for req in as_completed(th_):
            data = req.result().json()
            json_data = data['contents']
            for data_info in json_data:
                id_num = data_info['illust_id']
                ids.append(id_num)

    return ids


async def pixiv_get(id,cfg:dict,session):
    url = f'https://www.pixiv.net/ajax/illust/{id}/pages'
    headers = {'referer' : "https://www.pixiv.net/",'cookie' : f"{cfg['login']['cookie']}",'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36"} 
    async with session.get(url,headers=headers) as req:
        data = await req.json()
        return data['body']

async def dl_img(id,cfg:dict,session,pbar):
    headers = {'referer' : "https://www.pixiv.net/",'cookie' : f"{cfg['login']['cookie']}",'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36"}
    data = await pixiv_get(id,cfg,session)
    for data_info in data:
        img_url = data_info['urls']['original']
        name = img_url.split('/')[-1]
        async with session.get(img_url,headers=headers) as req:
            async with aiofiles.open(f'./img/{name}','wb') as aiof:
                await aiof.write(await req.content.read())
    pbar.update(1)

async def main():
    os.system('cls')
    print(banner)
    cfg = get_config()
    print('0:Pixiv_id mode\n1:Search mode\n2:Ranking mode\n3:User illusts\n4:Premium search(Need premium)\n5:popular_search(non premium)')
    mode = int(input('Mode:'))
    print(f"Mode:{mode}".center(50,'='))
     
    id_list = []
    tasks = []
    
    if mode == 0:
        id_list.append(int(input('Pixiv_id:')))
    elif mode == 1:
        search = input("Search:")
        print("".center(50,'='))
        print('0:All\n1:Safe\n2:R18(login)')
        mode_num = int(input('mode:'))
        print("".center(50,'='))
        ids = pixiv_search(search,cfg,mode=mode_num)
        id_list = [id for id in ids]
        
    elif mode == 2:
        print('0:daily\n1:weekly\n2:monthly\n3:rookie\n4:original\n5:for female\n6:r18(login)\n7:for male')     
        ranking_num = int(input('ranking_mode:'))
        print("".center(50,'='))
        page = int(input('Page:'))
        print("".center(50,'='))
        
        if ranking_num == 0 or 1 or 2 or 3:
            on_illust = input('Only illustration[y/n]:')
            if on_illust == 'y':
                ids = ranking(page,cfg,mode_num=ranking_num,only_illust=True)
                print("".center(50,'='))
            else:
                ids = ranking(page,cfg,mode_num=ranking_num)
        elif ranking_num == 6:
            print('0:daily_r18\n1:weekly_r18\n2:male_r18\n3:female_r18')
            r18mode = int(input("R18_mode:"))
            print("".center(50,'='))
            ids = ranking(page,cfg,mode_num=ranking_num,r18mode=r18mode)
        else:
            ids = ranking(page,cfg,mode_num=ranking_num)
            
        id_list = ids
        
    elif mode == 3:
        user_id = int(input('user_id:'))
        print("".center(50,'='))
        ids = get_user_illusts(user_id,cfg)
        id_list = [id for id in ids]
    
    elif mode == 4:
        search = input("Search:")
        print("".center(50,'='))
        print('0:All popular\n1:Popula for male\n2:Popula for female')
        order_num = int(input('order:'))
        print("".center(50,'='))
        print('0:r18 & safe\n1:safe\n2:R18')
        mode_4_num = int(input('mode:'))
        print("".center(50,'='))
        pages = int(input('pages:'))
        print("".center(50,'='))
        only_illust = input('only_illust[y/n]:')
        print("".center(50,'='))
        if only_illust == 'n':
            ids = premium_search(search,order_num,mode_4_num,pages,cfg,only_illust=False)
        else:
            ids = premium_search(search,order_num,mode_4_num,pages,cfg)
        id_list = [id for id in ids]
    
    elif mode == 5:
        search = input("Search:")
        print("".center(50,'='))
        collection = int(input("collection:"))
        print("".center(50,'='))
        print('0:All\n1:Safe\n2:R18(login)')
        r18mode = int(input("R18_mode:"))
        st_time = time.time()
        await popular_search(search,collection,cfg,mode=r18mode)
        print(f'總用時:{round(time.time() - st_time)}sec'.center(47,'='))
        exit()

    try:
        st_time = time.time()
        with tqdm(total=len(id_list)) as pbar:
            async with aiohttp.ClientSession() as session:
                for id in id_list:
                    tasks.append(asyncio.create_task(dl_img(id,cfg,session,pbar)))
                await asyncio.wait(tasks)
        print(f'總用時:{round(time.time() - st_time)}sec'.center(47,'='))
    except ValueError:
        pass

  
if __name__ == "__main__":
    asyncio.run(main())
