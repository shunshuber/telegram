import os
import shutil
from telethon import TelegramClient, errors
import asyncio

# Replace with your own API ID and API HASH
API_ID = '21495656'  # Replace with your actual API ID
API_HASH = '2685e5cd80c6421cca806d598c624ca4'  # Replace with your actual API HASH

sessions_dir = 'n3rz4/sessions'
deactivated_dir = 'n3rz4/deactivated'

if not os.path.exists(deactivated_dir):
    os.makedirs(deactivated_dir)

session_files = os.listdir(sessions_dir)

async def check_session(session_file):
    session_path = os.path.join(sessions_dir, session_file)
    client = TelegramClient(session_path, API_ID, API_HASH)
    move_file = False
    try:
        await client.connect()
        if not await client.is_user_authorized():
            # Not authorized
            print(f"Session {session_file} is not authorized.")
            move_file = True
        else:
            # Authorized, do nothing
            print(f"Session {session_file} is valid.")
    except errors.UserDeactivatedBanError:
        print(f"Account for session {session_file} is banned.")
        move_file = True
    except Exception as e:
        print(f"Failed to login with session {session_file}: {e}")
        move_file = True
    finally:
        await client.disconnect()
        if move_file:
            dest_path = os.path.join(deactivated_dir, session_file)
            shutil.move(session_path, dest_path)
            print(f"Moved {session_file} to deactivated folder.")

async def main():
    tasks = []
    for session_file in session_files:
        tasks.append(check_session(session_file))
    await asyncio.gather(*tasks)

asyncio.run(main())
