import logging

import pandas as pd
from django.db.models import Q
from django.utils import timezone

from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
from stos.utils import configs
from ..models import ShopeeBacklog, TiktokBacklog

logger = logging.getLogger(__name__)


def __get_breach_sla_shopee():
    qs = ShopeeBacklog.objects.filter(
        Q(shipper_date=timezone.now().date())
    )

    # Extract tracking_id and granular_status as tuples
    data = list(qs.values_list('backlog_type', 'tracking_id', 'shipper_date', 'extend_days', 'extended_date'))

    return data


def __get_breach_sla_tiktok():
    qs = TiktokBacklog.objects.filter(
        Q(shipper_date=timezone.now().date())

    )

    # Extract tracking_id and granular_status as tuples
    data = list(qs.values_list('shipper_date', 'tracking_id'))

    return data


def get_out_extended_shopee_date():
    data = __get_breach_sla_shopee()

    # Prepare DataFrame with both tracking_id and granular_status
    shopee_df = pd.DataFrame(data, columns=['backlog_type', 'tracking_id', 'shipper_date', 'extend_days', 'extended_date'])
    shopee_df = shopee_df.drop(columns=['backlog_type'])

    shopee_df = shopee_df[['shipper_date', 'tracking_id', 'extend_days', 'extended_date']]

    return shopee_df


def get_breach_data():
    # TikTok
    tiktok_data = __get_breach_sla_tiktok()
    tiktok_df = pd.DataFrame(tiktok_data, columns=['shipper_date', 'tracking_id'])
    tiktok_df['backlog_type'] = 'Delivery'

    # Shopee
    sp_data = __get_breach_sla_shopee()
    shopee_df = pd.DataFrame(sp_data, columns=['backlog_type', 'tracking_id', 'shipper_date', 'extend_days', 'extended_date'])
    shopee_df = shopee_df.drop(columns=['extend_days', 'extended_date'])

    shopee_df = shopee_df[['shipper_date', 'tracking_id', 'backlog_type']]

    final_df = pd.concat([tiktok_df, shopee_df], ignore_index=True)

    return final_df


def out_shopee_extended_date():
    service_account = get_service_account(configs.get('GSA_WORKER01'))
    gsheet = GoogleSheetService(
        service_account,
        '1wbw_mHgwk1pzuPwujDyXpGwwh0SFUJS7Ku36uIwOpaw',
        logger=logger
    )
    df = get_out_extended_shopee_date()
    gsheet.add_dataframe(df, 1088321776, append=True)


def out_breach_data():
    service_account = get_service_account(configs.get('GSA_WORKER01'))
    gsheet = GoogleSheetService(
        service_account,
        '1wbw_mHgwk1pzuPwujDyXpGwwh0SFUJS7Ku36uIwOpaw',
        logger=logger
    )
    df = get_breach_data()
    gsheet.add_dataframe(df, 1173906394, append=True)
