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
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'data', 'R05_011.csv')

        try:
            # 1. ファイルを読み込み
            df = pd.read_csv(file_path, delimiter='\t', skiprows=3, header=None, engine='python')

            # 2. 必要な列（区分名、平均給与）のみを抽出
            df = df.iloc[:, [0, 7]]
            df.columns = ['group_raw', 'annual_salary']

            # 3. データクレンジング
            df.dropna(inplace=True)
            df = df[pd.to_numeric(df['annual_salary'].astype(str).str.replace(',', ''), errors='coerce').notna()]
            df['annual_salary'] = df['annual_salary'].astype(str).str.replace(',', '').astype(float).astype(int)

            # 4. 構造化データを作成
            structured_data = []
            current_category = None

            # 画像で確認したファイル構造に合わせた設定
            company_size_marker = '（資本金階級別）'
            industry_marker = '建設業'
            skip_keywords = ['計', 'その他']

            for index, row in df.iterrows():
                group_name = str(row['group_raw']).strip()
                if not group_name:
                    continue

                # カテゴリの切り替えを判定
                if company_size_marker in group_name:
                    current_category = '企業規模'
                    continue  # この行はヘッダーなのでデータ処理はしない

                # '建設業'は業種カテゴリの最初のデータなので、カテゴリを設定してから処理を続行
                if industry_marker in group_name:
                    current_category = '業種'

                # カテゴリが設定されていなければ、まだ処理対象のデータではない
                if not current_category:
                    continue

                # 除外キーワードが含まれる集計行はスキップ
                if any(keyword in group_name for keyword in skip_keywords):
                    continue

                # データ行を整形して追加
                clean_group = re.sub(r'[･,・、\n]', '', group_name).strip()
                
                structured_data.append({
                    'category': current_category,
                    'group': clean_group,
                    'annual_salary': row['annual_salary']
                })

            if not structured_data:
                logger.warning("No data was extracted. Check the markers in api/views.py against the CSV file.")

            final_data = pd.DataFrame(structured_data).replace({np.nan: None}).to_dict(orient='records')
            return Response(final_data)

        except FileNotFoundError:
            logger.error(f"CSV file not found at: {file_path}")
            return Response({"error": "Data file not found on server."}, status=404)
        except Exception as e:
            logger.error(f"An error occurred during data processing: {e}", exc_info=True)
            return Response({"error": "An error occurred on the server."}, status=500)