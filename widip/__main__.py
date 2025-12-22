import asyncio

# Stop starting a Matplotlib GUI
if __debug__:
    import matplotlib
    matplotlib.use('agg')

from .watch import main


if __name__ == "__main__":
    asyncio.run(main())
