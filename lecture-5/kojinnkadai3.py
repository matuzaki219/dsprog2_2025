import os
import flet as ft
import requests
import sqlite3
from datetime import datetime

# DB設定
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "lecture-6", "weather.db")

def save_weather(area_code, area_name, date, weather):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO weather_forecast
        (area_code, area_name, date, weather, fetched_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (area_code, area_name, date, weather, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


# API設定
AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"


# アプリ本体
class WeatherApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.padding = 10

        self.area_data = self.load_area_data()

        self.content_area = ft.Column(
            controls=[],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        self.nav = self.create_navigation()

        self.content = ft.Row(
            [
                self.nav,
                ft.VerticalDivider(width=1),
                ft.Container(
                    self.content_area,
                    expand=True,
                    padding=20
                ),
            ],
            expand=True,
        )

    # 地域一覧取得
    def load_area_data(self):
        res = requests.get(AREA_URL)
        return res.json()["offices"]

    # 左ナビゲーション
    def create_navigation(self):
        return ft.NavigationRail(
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.LOCATION_ON,
                    label=info["name"],
                )
                for info in self.area_data.values()
            ],
            label_type=ft.NavigationRailLabelType.ALL,
            on_change=self.on_area_selected,
        )

    # 地域選択時
    def on_area_selected(self, e):
        area_code = list(self.area_data.keys())[e.control.selected_index]
        self.show_weather(area_code)

  # 天気表示 & DB保存
    def show_weather(self, area_code):
        area_name = self.area_data[area_code]["name"]

        self.content_area.controls.clear()
        self.content_area.controls.append(
            ft.Text(f"{area_name} の天気予報", size=24, weight="bold")
        )

        data = requests.get(FORECAST_URL.format(area_code)).json()
        ts = data[0]["timeSeries"][0]
        dates = ts["timeDefines"]
        weathers = ts["areas"][0]["weathers"]

        for i in range(min(3, len(weathers))):
            weather = weathers[i]
            date = dates[i][:10]

            # DB保存
            save_weather(area_code, area_name, date, weather)

            # 画面表示
            self.content_area.controls.append(
                ft.Text(f"{date}：{weather}", size=16)
            )

        self.update()


# エントリーポイント
def main(page: ft.Page):
    page.title = "気象庁 天気予報"

    app = WeatherApp()
    page.add(app)

    # 初期表示
    first_code = list(app.area_data.keys())[0]
    app.show_weather(first_code)


ft.app(target=main)