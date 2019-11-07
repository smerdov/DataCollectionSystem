import asyncio
from lib.cortex import Cortex
import json
from config import headset_id2player_id, TIME_FORMAT
from datetime import datetime



async def do_stuff(cortex):
    # await cortex.inspectApi()
    print("** USER LOGIN **")
    await cortex.get_user_login()
    print("** GET CORTEX INFO **")
    await cortex.get_cortex_info()
    print("** HAS ACCESS RIGHT **")
    await cortex.has_access_right()
    print("** REQUEST ACCESS **")
    await cortex.request_access()
    print("** AUTHORIZE **")
    await cortex.authorize()
    print("** GET LICENSE INFO **")
    await cortex.get_license_info()
    print("** QUERY HEADSETS **")
    await cortex.query_headsets()
    print(f"HEADSETS: {cortex.headsets}")
    if len(cortex.headsets) > 0:
        print("** CREATE SESSION **")
        # await cortex.create_session(activate=True,
        #                             headset_id=cortex.headsets[0])
        # session_ids = []
        # session_id2player_id = {}
        for headset_id in cortex.headsets:
            await cortex.create_session(activate=True, headset_id=headset_id)
            # session_ids.append(new_session_id)

        # headset2session_id = cortex.headset2session_id
        session_id2headset = cortex.session_id2headset
        session_id2player_id = {session_id: headset_id2player_id[session_id2headset[session_id]] for session_id in session_id2headset}

        files = {}
        for player_id in session_id2player_id.values():
            filename = f'eeg_player_{player_id}.csv'
            file = open(filename, 'w')
            file.write('time;content\n')
            files[player_id] = file

        # print("** CREATE RECORD **")
        # record_titles = [f'record_{player_id}' for player_id in session_id2player_id.values()]
        # await cortex.create_record(titles=record_titles)
        print("** SUBSCRIBE POW & MET **")
        # await cortex.subscribe(['pow', 'met'])
        await cortex.subscribe(['mot', 'dev', 'pow', 'met'])
        # while cortex.packet_count < 100:
        while True:
            data_str = await cortex.get_data()
            data_json = json.loads(data_str)
            session_id = data_json.pop('sid')
            # session_id = data_json['sid']
            timestamp = float(data_json.pop('time'))
            current_time = datetime.fromtimestamp(timestamp).strftime(TIME_FORMAT)[:-2]  # Two last digits are zeros

            data_json_str = json.dumps(data_json)
            line2write = f'{current_time};{data_json_str}\n'

            player_id = session_id2player_id[session_id]
            file = files[player_id]

            file.write(line2write)
            file.flush()

        await cortex.close_session()

    file.close()



def test():
    cortex_1 = Cortex('./cortex_creds')
    # cortex_2 = Cortex('./cortex_creds')
    # cortex_1_thread = Thread(target=do_stuff, args=(cortex_1,))
    # cortex_2_thread = Thread(target=do_stuff, args=(cortex_2,))
    # cortex_1_thread.start()
    # cortex_2_thread.start()

    asyncio.run(do_stuff(cortex_1))
    # asyncio.run(do_stuff(cortex_2))
    cortex_1.close()
    # cortex_2.close()


if __name__ == '__main__':
    test()

with open('record.txt', 'r') as f:
    line = f.readlines()
    print(line)

import pandas as pd
pd.DataFrame([json.loads(x) for x in line])['met']

