import pandas as pd
import folium
from coord_convert.transform import bd2wgs  # https://pypi.org/project/coord-convert/
from folium.plugins import AntPath

# 定义文件路径和车牌
files = [
    (
        "data/车辆名称++粤B21MW1-LFNA4LCA3KAX47404-有线++从20240701105605到20240711105605轨迹明细.xlsx",
        "粤B21MW1",
    ),
    (
        "data/车辆名称++粤S9X77P-LFNA4LCA9LAX13906-有线++从20240701000022到20240711102522轨迹明细 (1).xlsx",
        "粤S9X77P",
    ),
    (
        "data/车辆名称++粤SKE099-LS1D221B0L0618428-有线++从20240701000035到20240711103935轨迹明细.xlsx",
        "粤SKE099",
    ),
]

# 创建地图对象，初始位置设为第一个车辆的平均位置
m = folium.Map(location=[23.009697, 113.865723], zoom_start=13)

# 不同车辆使用不同颜色
colors = ["blue", "green", "red"]

# 读取每个文件，处理数据并绘制到地图上
for (file, plate), color in zip(files, colors):
    df = pd.read_excel(file, header=1)

    # 转换时间列为datetime类型
    df["时间"] = pd.to_datetime(df["时间"])

    # 进行坐标转换，从 BD-09(百度坐标系) 转换为 WGS-84(未偏移坐标)
    df[["WGS84经度", "WGS84纬度"]] = df.apply(
        lambda row: pd.Series(bd2wgs(row["经度"], row["纬度"])), axis=1
    )

    # 计算停留时间
    df["停留时间"] = (
        df.groupby(["WGS84经度", "WGS84纬度"])["时间"]
        .diff()
        .fillna(pd.Timedelta(seconds=0))
    )

    # 筛选停留时间超过阈值的地点，阈值设为10分钟
    threshold = pd.Timedelta(minutes=10)
    long_stays = df[df["停留时间"] > threshold]

    # 添加轨迹线到地图 (使用 AntPath 插件)
    coordinates = list(zip(df["WGS84纬度"], df["WGS84经度"]))
    AntPath(
        locations=coordinates,
        color=color,
        weight=2.5,
        opacity=1,
        delay=1000,
    ).add_to(m)

    # 添加停留时间较长的轨迹点到地图
    for index, row in long_stays.iterrows():
        popup_content = f"车牌: {plate}<br>时间: {row['时间']}<br>停留时间: {row['停留时间']}<br>位置: {row['位置']}"
        popup = folium.Popup(popup_content, max_width=300)
        folium.Marker(
            location=[row["WGS84纬度"], row["WGS84经度"]],
            popup=popup,
            icon=folium.Icon(color=color, icon="info-sign"),
        ).add_to(m)

# 保存地图到HTML文件
m.save("output/combined_vehicle_trajectory_map.html")

print("地图已保存到 output/combined_vehicle_trajectory_map.html")
