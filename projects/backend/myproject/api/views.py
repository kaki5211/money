from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets
from .models import Article
from .serializers import ArticleSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
import os
import re
import numpy as np # numpyをインポート

import pandas as pd

import os
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging

# ロガーの設定
logger = logging.getLogger(__name__)


class ArticleViewSet(viewsets.ModelViewSet):
    """
    記事データを取得・作成・更新・削除するためのAPIビュー
    """
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleSerializer



class SalaryDataView(APIView):
    def get(self, request):
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # 保険料データが含まれる R05_011.csv を読み込みます
            file_path = os.path.join(base_dir, 'data', '業種別データ.txt')
            print("file_path", file_path)

            # CSVの最初の行（ヘッダー）をスキップして読み込みます           


            # --- 修正点 1: ヘッダーを2行スキップ ---
            # これにより、データの行だけが正しく読み込まれます。
            df = pd.read_csv(
                file_path,
                delimiter=',',
                skiprows=2,  # 1行目と2行目のヘッダーを両方とも読み飛ばします
                header=None,
                engine='python',
                # 万が一データが欠けている行があってもエラーにならないように列数を指定します
            )

            print("df", df)

            # グラフのラベルとして1列目（等級）を取得
            labels = df.iloc[:, 0].tolist()

            print("labels", labels)


            # グラフのデータとして5列目（介護保険第２号被保険者に該当する場合）を取得
            premium_column = df.iloc[:, 4]

            # --- 修正点 2: データを安全に数値化する確実な処理 ---
            
            # 1. 念のため、すべてのデータを文字列として扱います
            series_as_string = premium_column.astype(str)

            # 2. 不要な文字（カンマ、円記号、空白）をすべて取り除きます
            cleaned_strings = series_as_string.str.replace(',', '', regex=False).str.replace('円', '', regex=False).str.strip()

            # 3. 文字列を数値に変換します。変換に失敗したものはすべて「NaN」になります
            numeric_data = pd.to_numeric(cleaned_strings, errors='coerce')

            # 4. エラーの直接原因である「NaN」を、JSONで扱える「0」にすべて置き換えます
            final_data_series = numeric_data.fillna(0)

            # 5. 最終的なデータをPythonのリスト形式に変換します
            # premium_data = final_data_series.tolist()
            premium_data = final_data_series.astype(int).tolist()

            print("premium_data", premium_data)

            return Response({
                "labels": labels,
                "data": premium_data
            })


            # APIレスポンスを返します
            return Response({
                "labels": labels,
                "data": premium_data
            })

        except FileNotFoundError:
            print(f"エラー: ファイルが見つかりません {file_path}")
            return Response({"error": "データファイルが見つかりません。"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            # サーバー側で具体的なエラー内容を確認できるようにログに出力します
            print(f"SalaryDataViewでのエラー: {e}")
            return Response({"error": "サーバーでエラーが発生しました。"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
