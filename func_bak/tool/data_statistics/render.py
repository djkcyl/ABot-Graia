import pyecharts.options as opts
from pyecharts.charts import Line
from pyecharts.commons.utils import JsCode

COLORFUL_JS_CODE = JsCode(
    "new echarts.graphic.LinearGradient(0, 0, 0, 1, "
    "[{offset: 0, color: '#eb64fb'}, {offset: 1, color: '#3fbbff0d'}], false)"
)


def render_message_line_chart(data: list[tuple[str, int]], subtitle: str):
    e = Line(
        init_opts=opts.InitOpts(
            width="100%", height="100%", animation_opts=opts.AnimationOpts(animation=False)
        )
    )
    e.add_xaxis([i[0] for i in data])
    e.add_yaxis(
        series_name="消息量",  # 系列名称，用于 tooltip 的显示
        y_axis=[i[1] for i in data],  # 系列数据
        is_smooth=True,  # 是否平滑曲线显示
        symbol_size=8,  # 标记的大小
        linestyle_opts=opts.LineStyleOpts(width=2),  # 线条样式配置
        # label_opts=opts.LabelOpts(),
        areastyle_opts=opts.AreaStyleOpts(opacity=0.7, color=COLORFUL_JS_CODE),
    )
    e.set_global_opts(title_opts=opts.TitleOpts(title="消息量统计", subtitle=subtitle))
    return e.render_embed()
