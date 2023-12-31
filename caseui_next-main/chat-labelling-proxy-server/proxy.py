import os
import requests
import pymysql
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import hashlib
import time


def generate_md5_hash(input_string):
    md5 = hashlib.md5()
    md5.update(input_string.encode('utf-8'))
    return md5.hexdigest()


app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8081",
    "http://0.0.0.0:8081",
    "http://8.130.29.207:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
RAINFOREST_URL = f'https://api.asindataapi.com/request?api_key=A6BB488F5501417A80664B413A7C08E8&' \
                 'type=search&amazon_domain=amazon.cn&search_term={query}&refinements={filters}'


@app.post("/login")
async def login(name, password, role, action):
    connection = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="joker",
        database='chat_labelling',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        if action == "signup":
            with connection:
                # get the num of users to set new id
                with connection.cursor() as cursor:
                    cursor.execute("SELECT count(`id`) AS ids FROM `user`")
                    result = cursor.fetchone()
                    new_id = result['ids'] + 1
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) AS sys_count FROM user WHERE role = 'sys'")
                    sys_count = cursor.fetchone()['sys_count']

                    # 查询 'cus' 的数量
                    cursor.execute("SELECT COUNT(*) AS cus_count FROM user WHERE role = 'cus'")
                    cus_count = cursor.fetchone()['cus_count']

                    print(f"Number of 'sys' roles: {sys_count}")
                    print(f"Number of 'cus' roles: {cus_count}")
                # create user
                if sys_count > cus_count :
                    role = 'cus'
                else:
                    role = 'sys'
                with connection.cursor() as cursor:
                    sql = "INSERT INTO `user` (`id`, `connection_count`, `name`, `password`, `role`) " \
                          "VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(sql, (new_id, 0, name, password, role))
                connection.commit()
            print(role)
            return {'result': 'Success', "role":role}
        elif action == "login":
            with connection:
                with connection.cursor() as cursor:
                    # I guess... check if user exists? this is not real authentication
                    sql = "SELECT `password`, `role` FROM `user` WHERE `name`=%s"
                    cursor.execute(sql, (name,))
                    result = cursor.fetchone()

                    # if user exists, check if password and role match the form data
                    if result and result["password"] == password:
                        return {"result": "Success", "role":result["role"]}
                    else:
                        return JSONResponse(status_code=401, content={"message": "Authorization failed"})
        else:
            return JSONResponse(status_code=400, content={"message": "Action not permitted; only login and signup are supported"})

    except:
        return JSONResponse(status_code=500, content={"message": "Something critical happened"})


@app.get("/")
async def search(query='ipod', refinements=''):
    first = time.time()
    url = RAINFOREST_URL.format(query=query, filters=refinements)
    res = requests.get(url)
    print(f'-- Searching for {query}')
    print(f'-- With refinements: {refinements}')

    if res.ok:
        data = res.json()
        print(data)
        search = {
            'Suggest': [],
            'Answer': [],
            'Filters': [],
            'Aspects': []
        }
        print(data)
        search_results = data['search_results']
        refinements = data.get('refinements')

        if len(search_results) == 0:
            return {'key': 'error'}
        print(f'-- Found {len(search_results)} results.')

        for i, item in enumerate(search_results):
            # print(item)
            # print("\n")
            title = item['title']
            search['Suggest'].append({
                'id': generate_md5_hash(title),  # 本项目中产品唯一id
                'title': title,
                'link': item['link'],
                'image': item['image'],
                'productId': item['asin'],  # 后序可能有用，亚马逊产品唯一id
                # 'is_prime': item['is_prime'],
                # 'rating': item['rating'],
                # 'ratings_total': item['ratings_total'],
                'from': 'rainforest',
            })

            search['Answer'].append({
                'title': item['title'],
                'link': item['link'],
                'from': 'rainforest',
                'id': f'answer-{i}',
                'content': 'empty',
                'image': item['image'],
                'selected': 'false'
            })

        for ref_category in refinements.keys():

            for ref in refinements[ref_category]:
                display_name = ref["refinement_display_name"]

                if 'value' in ref:

                    value = ref['value']
                    if not value.startswith('n:'):
                        modified_value = value
                    else:
                        modified_value = value.split('||')[1]
                else:
                    modified_value = "None"
                if modified_value == "undefined":
                    continue
                print(modified_value,"\n")
                search['Filters'].append({
                    'name': f'{display_name}: {ref["name"]}',
                    'value': modified_value
                })

                if display_name not in search['Aspects']:
                    search['Aspects'].append(f'{display_name}: {ref["name"]}')
        print(search['Aspects'])
        second = time.time()
        print(f"用时共计{second - first}")
        print(search)
        return JSONResponse(content=search)
    second = time.time()
    print(f"用时共计{second - first}")
    return ''


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=9191)
