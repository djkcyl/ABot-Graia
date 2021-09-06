# import time
# import psutil
# import asyncio
# import platform

# from graia.saya import Saya, Channel
# from graia.application import GraiaMiraiApplication
# from graia.saya.builtins.broadcast.schema import ListenerSchema
# from graia.application.event.lifecycle import ApplicationLaunched

# CPU_USAGE = []
# MEM_USAGE = []

# saya = Saya.current()
# channel = Channel.current()
# psutil.cpu_percent()

# @channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
# async def cpuStatus(app: GraiaMiraiApplication):
#     global CPU_USAGE
#     app.logger.info("已开始记录 CPU 占用率")
#     while True:
#         await asyncio.sleep(1)
#         if len(CPU_USAGE) > 200:
#             CPU_USAGE = CPU_USAGE[-200:]
#         CPU_USAGE.append(psutil.cpu_percent())
#         # print(CPU_USAGE)


# @channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
# async def cpuStatus(app: GraiaMiraiApplication):
#     global MEM_USAGE
#     app.logger.info("已开始记录内存占用率")
#     while True:
#         await asyncio.sleep(1)
#         if len(MEM_USAGE) > 200:
#             MEM_USAGE = MEM_USAGE[-200:]
#         MEM_USAGE.append(psutil.virtual_memory().used)
#         # print(MEM_USAGE)


# print(platform.platform())
