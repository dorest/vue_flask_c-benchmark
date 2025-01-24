import re
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os


def extract_memory_summary(log):
    """从Valgrind的日志中提取堆内存和泄漏相关信息"""
    
    # 正则表达式提取每个PID的内存使用和泄漏相关信息
    heap_summary_pattern = r"==(\d+)==\s+HEAP SUMMARY:.*?in use at exit:\s*(\d{1,3}(?:,\d{3})*)\s+bytes.*?total heap usage:.*?(\d{1,3}(?:,\d{3})*)\s+allocs.*?(\d+)\s+frees.*?(\d{1,3}(?:,\d{3})*)\s+bytes allocated"
    leak_summary_pattern = r"==(\d+)==\s+LEAK SUMMARY:.*?definitely lost:\s*(\d{1,3}(?:,\d{3})*)\s+bytes.*?indirectly lost:\s*(\d{1,3}(?:,\d{3})*)\s+bytes.*?possibly lost:\s*(\d{1,3}(?:,\d{3})*)\s+bytes.*?still reachable:\s*(\d{1,3}(?:,\d{3})*)\s+bytes"

    # 匹配所有的HEAP SUMMARY和LEAK SUMMARY
    heap_matches = re.findall(heap_summary_pattern, log, re.DOTALL)
    leak_matches = re.findall(leak_summary_pattern, log, re.DOTALL)

    memory_info = {}

    for heap_match, leak_match in zip(heap_matches, leak_matches):
        pid = heap_match[0]
        in_use_at_exit = int(heap_match[1].replace(',', ''))
        total_allocated = int(heap_match[4].replace(',', ''))
        still_reachable = int(leak_match[4].replace(',', ''))
        definitely_lost = int(leak_match[1].replace(',', ''))
        indirectly_lost = int(leak_match[2].replace(',', ''))
        possibly_lost = int(leak_match[3].replace(',', ''))

        # 将数据存入字典
        memory_info[pid] = {
            'in_use_at_exit': in_use_at_exit,
            'total_allocated': total_allocated,
            'still_reachable': still_reachable,
            'definitely_lost': definitely_lost,
            'indirectly_lost': indirectly_lost,
            'possibly_lost': possibly_lost
        }

    return memory_info

def plot_memory_summary(memory_info, result_dir):
    """可视化内存使用信息，并保存为SVG"""
    
    # 颜色映射
    color_map = {
        'in_use_at_exit': 'skyblue',
        'total_allocated': 'lightgreen',
        'still_reachable': 'limegreen',
        'definitely_lost': 'red',
        'indirectly_lost': 'orange',
        'possibly_lost': 'purple'
    }

    # 设置图表
    fig, ax = plt.subplots(figsize=(10, 7))

    # 设置PID列表
    pids = list(memory_info.keys())

    # 设置堆叠的内存数据
    in_use_at_exit = [memory_info[pid]['in_use_at_exit'] for pid in pids]
    total_allocated = [memory_info[pid]['total_allocated'] for pid in pids]
    still_reachable = [memory_info[pid]['still_reachable'] for pid in pids]
    definitely_lost = [memory_info[pid]['definitely_lost'] for pid in pids]
    indirectly_lost = [memory_info[pid]['indirectly_lost'] for pid in pids]
    possibly_lost = [memory_info[pid]['possibly_lost'] for pid in pids]

    # 绘制堆叠条形图
    ax.bar(pids, in_use_at_exit, label="In Use at Exit", color=color_map['in_use_at_exit'])
    ax.bar(pids, total_allocated, label="Total Allocated", bottom=in_use_at_exit, color=color_map['total_allocated'])
    ax.bar(pids, still_reachable, label="Still Reachable", bottom=[i+j for i,j in zip(in_use_at_exit, total_allocated)], color=color_map['still_reachable'])
    ax.bar(pids, definitely_lost, label="Definitely Lost", bottom=[i+j+k for i,j,k in zip(in_use_at_exit, total_allocated, still_reachable)], color=color_map['definitely_lost'])
    ax.bar(pids, indirectly_lost, label="Indirectly Lost", bottom=[i+j+k+l for i,j,k,l in zip(in_use_at_exit, total_allocated, still_reachable, definitely_lost)], color=color_map['indirectly_lost'])
    ax.bar(pids, possibly_lost, label="Possibly Lost", bottom=[i+j+k+l+m for i,j,k,l,m in zip(in_use_at_exit, total_allocated, still_reachable, definitely_lost, indirectly_lost)], color=color_map['possibly_lost'])

    # 添加数字标签
    for i, pid in enumerate(pids):
        # 计算每个堆叠条形的顶部位置并添加数字
        bottom = 0
        for label, data in zip(
            ["in_use_at_exit", "total_allocated", "still_reachable", "definitely_lost", "indirectly_lost", "possibly_lost"],
            [in_use_at_exit, total_allocated, still_reachable, definitely_lost, indirectly_lost, possibly_lost]
        ):
            value = data[i]
            ax.text(
                pid, bottom + value / 2,  # text位置
                str(value),               # 显示的文本
                ha='center',              # 水平对齐方式
                va='center',              # 垂直对齐方式
                color='black'             # 字体颜色
            )
            bottom += value  # 更新顶部位置

    # 添加图例和标签
    ax.set_xlabel("PID")
    ax.set_ylabel("Memory (bytes)")
    ax.set_title("Memory Usage Summary by PID")
    ax.legend()

    # 显示图表
    plt.xticks(rotation=45)
    plt.tight_layout()
    #plt.draw()

    save_svg = os.path.join(result_dir, "heap.svg")
    try:
        plt.savefig(save_svg, format='svg')
    except Exception as e:
        print(f"======================ERROR saving fig {e} =================")
    #plt.show()


def generate_memory_svg(result_dir):

    #
    log_data = ''
    log_path = os.path.join(result_dir, "valgrind.log")
    # log_path = "/root/cpp_test/flask-vue/performance-tests/results/20250123_105003_11/profile/valgrind.log"
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            log_data = f.read()
    else:
        print(f"ERROR============not exits: {log_path}==========================")
        return


    memory_info = extract_memory_summary(log_data)
    plot_memory_summary(memory_info, result_dir)

generate_memory_svg("/root/cpp_test/flask-vue/performance-tests/results/20250123_164950_11/profile")
