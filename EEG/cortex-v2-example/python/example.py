import asyncio
from lib.cortex import Cortex
import json
from config import headset_id2player_id, TIME_FORMAT, TIME_FORMAT4FILES
from datetime import datetime
import os

dev_info_timestep = 1

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
            if not headset_id.startswith('INSIGHT'):
                continue

            await cortex.create_session(activate=True, headset_id=headset_id)
            # session_ids.append(new_session_id)

        # headset2session_id = cortex.headset2session_id
        session_id2headset = cortex.session_id2headset
        session_id2player_id = {session_id: headset_id2player_id[session_id2headset[session_id]] for session_id in session_id2headset}

        if not os.path.exists('data'):
            os.mkdir('data')

        datetime_start = datetime.now().strftime(TIME_FORMAT4FILES)
        files = {}
        for player_id in session_id2player_id.values():
            filename = f'data/eeg_player_{player_id}_{datetime_start}.csv'
            file = open(filename, 'w')
            file.write('time;content\n')
            files[player_id] = file

        last_dev_timestamps = {player_id: 0 for player_id in session_id2player_id.values()}

        # print("** CREATE RECORD **")
        # record_titles = [f'record_{player_id}' for player_id in session_id2player_id.values()]
        # await cortex.create_record(titles=record_titles)
        print("** SUBSCRIBE POW & MET **")
        # await cortex.subscribe(['pow', 'met'])
        await cortex.subscribe(['mot', 'dev', 'pow', 'met'])  # 'fac' - facial expressions, probably useless
        # while cortex.packet_count < 100:
        while True:
            data_str = await cortex.get_data()
            data_json = json.loads(data_str)
            try:
                session_id = data_json.pop('sid')
            except:
                raise KeyError(f'sid key is not presented in {data_str}')
            player_id = session_id2player_id[session_id]
            file = files[player_id]
            # session_id = data_json['sid']
            timestamp = float(data_json.pop('time'))
            current_time = datetime.fromtimestamp(timestamp).strftime(TIME_FORMAT)[:-2]  # Two last digits are zeros

            if 'dev' in data_json:
                if (timestamp - last_dev_timestamps[player_id] > dev_info_timestep):
                    last_dev_timestamps[player_id] = timestamp # Record the data about the device
                else:
                    continue  # We don't need so much data about device status


            data_json_str = json.dumps(data_json)
            line2write = f'{current_time};{data_json_str}\n'

            file.write(line2write)
            file.flush()

        await cortex.close_session()

    # file.close()



def test():
    cortex = Cortex('./cortex_creds')

    asyncio.run(do_stuff(cortex))
    cortex.close()


if __name__ == '__main__':
    test()



