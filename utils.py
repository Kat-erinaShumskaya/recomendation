import pandas as pd
import numpy as np


def prefilter_items(df, take_n_popular=5000, price=5, item_features=None, list_department=None):
    count_users = df['user_id'].nunique()
    # print(count_users)
    popularity = df.groupby('item_id')['user_id'].nunique().reset_index()
    popularity.rename(columns={'user_id': 'share_unique_users'}, inplace=True)
    popularity.share_unique_users = popularity.share_unique_users / count_users
    #     print(popularity.share_unique_users)

    # Уберем самые популярные товары (их и так купят)
    top_popular = popularity[popularity['share_unique_users'] > 0.5].item_id.tolist()
    # print(popularity.sort_values('share_unique_users', ascending=False).head(10))
    # print('top_popular', top_popular[:5])
    df = df[~df['item_id'].isin(top_popular)]
    #     print(df.head())
    # print('размерность без самых популярных', df.shape)

    # Уберем самые НЕ популярные товары (их и так НЕ купят)
    top_not_popular = popularity[popularity['share_unique_users'] < 0.01].item_id.tolist()
    # print(popularity.sort_values('share_unique_users').head(10))
    df = df[~df['item_id'].isin(top_not_popular)]
    # print('размерность без самых не популярных', df.shape)

    # Уберем товары, которые не продавались за последние 12 месяцев
    last_day_12_months_ago = df.day.max() - 365
    data_last_12_months = df[df.day > last_day_12_months_ago]
    item_sales_last_12_months = data_last_12_months.item_id.unique()
    df = df[df['item_id'].isin(item_sales_last_12_months)]
    # print('размерность продажи за последние 12 мес', df.shape)

    # Уберем не интересные для рекоммендаций категории (department)
    if item_features is not None:
        if list_department is not None:
            df = df[~df['item_id'].isin(list_department)]
        else:
            department_df = \
                item_features.groupby('department')['item_id'].count().reset_index().sort_values('item_id',
                                                                                                 ascending=False)
            department_list = department_df['department'].tolist()[:-22]
            item_ids_list = item_features[item_features['department'].isin(department_list)].item_id.tolist()
            df = df[~df['item_id'].isin(item_ids_list)]
        # print('размерность без самых непопулярных категорий', df.shape)

    # Уберем слишком дешевые товары (на них не заработаем). 1 покупка из рассылок стоит 60 руб.
    data_sales = df.groupby('item_id')['quantity', 'sales_value'].sum().reset_index()
    data_sales['price'] = data_sales['sales_value'] / data_sales['quantity']
    data_sales.dropna(axis=0, how='any', thresh=None, subset=None, inplace=True)
    data_sales = data_sales[data_sales['price'] != np.inf]
    # print(data_sales.sort_values('price', ascending=False).head(10))
    not_cheap_products = data_sales[data_sales['price'] > price]['item_id'].unique()
    df = df[df['item_id'].isin(not_cheap_products)]
    # print('размерность без самых дешевых', df.shape)

    # Уберем слишком дорогие товары

    expensive_goods = data_sales.sort_values('price', ascending=False).head(
        int(data_sales.shape[0] * 0.01)).item_id.tolist()
    # print('самые дорогие', data_sales.sort_values('price', ascending=False).head(int(data_sales.shape[0] * 0.01)))
    df = df[~df['item_id'].isin(expensive_goods)]
    # print('размерность без слишком дорогих', df.shape)

    # Возьмем топ по популярности
    popularity = df.groupby('item_id')['quantity'].sum().reset_index()
    popularity.rename(columns={'quantity': 'n_sold'}, inplace=True)
    # print('самых популярных', popularity.shape)
    top_take_n_popular = popularity.sort_values('n_sold', ascending=False).head(take_n_popular).item_id.tolist()
    # Заведем фиктивный item_id (если юзер не покупал товары из топ-5000, то он "купил" такой товар)
    df.loc[~df['item_id'].isin(top_take_n_popular), 'item_id'] = 999999
    # print('размерность топа самых популярных', df.shape)

    return df


def postfilter_items(user_id, recommednations):
    print("hello!")