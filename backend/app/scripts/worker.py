import asyncio
from app.services.queue import start_background_workers

async def main():
    print("[worker] starting queue worker + periodic scanner")
    await start_background_workers()
    # Keep process alive
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
