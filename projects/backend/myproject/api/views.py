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


from django.conf import settings



class ArticleViewSet(viewsets.ModelViewSet):
    """
    記事データを取得・作成・更新・削除するためのAPIビュー
    """
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleSerializer



class SalaryDataView(APIView):
    def get(self, request, *args, **kwargs):
        # 読み込むファイルを新しい 'R05_011.csv' に変更
        file_path = os.path.join(settings.BASE_DIR, 'data', 'R05_011.csv')

        try:
            # 1. ファイルを読み込み、不要なヘッダー（3行）をスキップ
            df = pd.read_csv(file_path, delimiter='\t', skiprows=3, header=None, engine='python')

            # 2. 必要な列（区分名、平均給与）のみを抽出
            df = df.iloc[:, [0, 2]]
            df.columns = ['group_raw', 'annual_salary']

            # 3. データクレンジング
            #    - 空の行を削除
            df.dropna(inplace=True)
            #    - 平均給与が数値（カンマ含む）の行のみを抽出
            df = df[df['annual_salary'].astype(str).str.match(r'^[0-9,]+$')]
            #    - 平均給与を数値型に変換
            df['annual_salary'] = df['annual_salary'].astype(str).str.replace(',', '').astype(int)

            # 4. カテゴリを特定し、構造化データを作成
            #    このファイルは「企業規模」と「業種」のカテゴリに分かれている
            category_markers = {
                '企業規模': '（資本金階級別）株式会社',
                '業種': '建設業'
            }
            
            structured_data = []
            current_category = ''
            for index, row in df.iterrows():
                group_name = str(row['group_raw']).strip()

                # カテゴリの開始を判定
                if category_markers['企業規模'] in group_name:
                    current_category = '企業規模'
                    continue # カテゴリ名自身の行はスキップ
                elif category_markers['業種'] in group_name:
                    current_category = '業種'
                
                # '計'を含む集計行は除外
                if '計' in group_name or 'その他' in group_name:
                    continue

                if current_category:
                    # '2,000万円未満' -> '2000万円未満'のように整形
                    clean_group = re.sub(r'[･,・、〃\n]', '', group_name).strip()
                    structured_data.append({
                        'category': current_category,
                        'group': clean_group,
                        'annual_salary': row['annual_salary']
                    })

            # NaNをNoneに変換してJSONコンプライアントにする
            final_data = pd.DataFrame(structured_data).replace({np.nan: None}).to_dict(orient='records')
            print("ffff", df)

            return Response(final_data)

        except FileNotFoundError:
            return Response({"error": "CSV file not found."}, status=404)
        except Exception as e:
            return Response({"error": f"An error occurred during data processing: {str(e)}"}, status=500)