import numpy as np
import matplotlib.pyplot as plt

from io import BytesIO
from pathlib import Path
from matplotlib.font_manager import FontProperties

font = Path().joinpath("font", "sarasa-mono-sc-regular.ttf")
zhfont1 = FontProperties(fname=font)


async def get_mapping(cpu, ram, max_ram):
    plt.figure(dpi=200, figsize=(12, 10))
    plt.subplots_adjust(hspace=0.5)

    x_range = range(1, 301, 1)
    x = np.array(x_range)

    plt.subplot(2, 1, 1)
    plt.title('CPU 占用率（%）', fontsize=20, fontproperties=zhfont1)
    plt.axis([0, 300, 0, 100])
    y_cpu = np.array(cpu)
    plt.plot(x, y_cpu)
    plt.grid()
    plt.xticks([])

    plt.subplot(2, 1, 2)
    plt.title('内存占用率（MB）', fontsize=20, fontproperties=zhfont1)
    plt.axis([0, 300, 0, max_ram])
    y_ram = np.array(ram)
    plt.plot(x, y_ram)
    plt.grid()
    plt.xticks([])

    bio = BytesIO()
    plt.savefig(bio)
    return bio
