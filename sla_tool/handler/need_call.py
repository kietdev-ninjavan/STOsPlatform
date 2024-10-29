import logging

import pandas as pd
from django.db.models import Q
from django.utils import timezone

from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
from opv2.base.order import GranularStatusChoices
from stos.utils import Configs
from ..models import ShopeeBacklog, TiktokBacklog, RecordSLACall, BreachSLACall

configs = Configs()
logger = logging.getLogger(__name__)


def __get_breach_sla_shopee():
    qs = ShopeeBacklog.objects.filter(
        Q(aging_from_lost_threshold=0)
        & Q(rts=False)
        & ~Q(granular_status__in=[
            GranularStatusChoices.cancelled,
            GranularStatusChoices.completed,
            GranularStatusChoices.pending_pickup,
            GranularStatusChoices.pending_pickup_at_dp])
        & Q(return_sn__isnull=True)
    )

    # Extract tracking_id and granular_status as tuples
    tracking_ids_and_status = list(qs.values_list('tracking_id', 'granular_status'))

    return tracking_ids_and_status


def __get_breach_sla_tiktok():
    today = timezone.now().date()
    qs = TiktokBacklog.objects.filter(
        Q(date=today) &
        Q(rts=False) &
        ~Q(granular_status__in=[
            GranularStatusChoices.cancelled,
            GranularStatusChoices.completed,
            GranularStatusChoices.pending_pickup,
            GranularStatusChoices.pending_pickup_at_dp
        ])
    )

    # Extract tracking_id and granular_status as tuples
    tracking_ids_and_status = list(qs.values_list('tracking_id', 'granular_status'))

    return tracking_ids_and_status


def __check_called(tracking_ids_and_status):
    tracking_ids = [t_id for t_id, _ in tracking_ids_and_status]
    all_records = RecordSLACall.objects.filter(tracking_id__in=tracking_ids)
    called_ids = list(all_records.values_list('tracking_id', flat=True))

    # Get tracking IDs not called yet
    not_called_ids = list(set(tracking_ids) - set(called_ids))
    return not_called_ids


def __check_in_list_call(tracking_ids):
    all_calls = BreachSLACall.objects.filter(tracking_id__in=tracking_ids)
    all_call_ids = list(all_calls.values_list('tracking_id', flat=True))

    # Get tracking IDs not in the list
    not_in_list_ids = list(set(tracking_ids) - set(all_call_ids))
    return not_in_list_ids


def get_sla_need_call_filtered():
    # TikTok
    tt_tracking_ids_and_status = __get_breach_sla_tiktok()
    tt_tracking_ids = [t_id for t_id, _ in tt_tracking_ids_and_status]  # Extract tracking IDs only
    logger.info(f'Found {len(tt_tracking_ids)} TikTok tracking IDs to check.')

    tt_not_called_ids = __check_called(tt_tracking_ids_and_status)
    logger.info(f'Found {len(tt_not_called_ids)} TikTok tracking IDs not called.')

    tt_not_in_list_ids = __check_in_list_call(tt_not_called_ids)
    logger.info(f'Found {len(tt_not_in_list_ids)} TikTok tracking IDs not called today.')

    # Prepare DataFrame with both tracking_id and granular_status
    tiktok_df = pd.DataFrame(tt_tracking_ids_and_status, columns=['tracking_id', 'granular_status'])
    tiktok_df = tiktok_df[tiktok_df['tracking_id'].isin(tt_not_in_list_ids)]  # Filter by not_in_list_ids
    tiktok_df['date'] = timezone.now().date()
    tiktok_df['shipper_group'] = 'TikTok'

    # Shopee
    sp_tracking_ids_and_status = __get_breach_sla_shopee()
    sp_tracking_ids = [t_id for t_id, _ in sp_tracking_ids_and_status]  # Extract tracking IDs only
    logger.info(f'Found {len(sp_tracking_ids)} Shopee tracking IDs to check.')

    sp_not_called_ids = __check_called(sp_tracking_ids_and_status)
    logger.info(f'Found {len(sp_not_called_ids)} Shopee tracking IDs not called.')

    sp_not_in_list_ids = __check_in_list_call(sp_not_called_ids)
    logger.info(f'Found {len(sp_not_in_list_ids)} Shopee tracking IDs not called today.')

    # Prepare DataFrame with both tracking_id and granular_status
    shopee_df = pd.DataFrame(sp_tracking_ids_and_status, columns=['tracking_id', 'granular_status'])
    shopee_df = shopee_df[shopee_df['tracking_id'].isin(sp_not_in_list_ids)]  # Filter by not_in_list_ids
    shopee_df['date'] = timezone.now().date()
    shopee_df['shipper_group'] = 'Shopee'

    # Concatenate the TikTok and Shopee dataframes
    final_df = pd.concat([tiktok_df, shopee_df], ignore_index=True)

    return final_df


def get_sla_need_call():
    now = timezone.now().date()
    # TikTok
    tt_tracking_ids_and_status = __get_breach_sla_tiktok()
    tt_tracking_ids = [t_id for t_id, _ in tt_tracking_ids_and_status]

    tiktok_df = pd.DataFrame(tt_tracking_ids, columns=['TID'])
    tiktok_df['breach origin'] = now
    tiktok_df['day input'] = now
    tiktok_df['Shipper'] = 'Tiktok'

    # Shopee
    sp_tracking_ids_and_status = __get_breach_sla_shopee()
    sp_tracking_ids = [t_id for t_id, _ in sp_tracking_ids_and_status]

    shopee_df = pd.DataFrame(sp_tracking_ids, columns=['TID'])
    shopee_df['breach origin'] = now
    shopee_df['day input'] = now
    shopee_df['Shipper'] = 'Shopee'

    final_df = pd.concat([tiktok_df, shopee_df], ignore_index=True)

    return final_df


def out_to_stos_sheet():
    service_account = get_service_account(configs.get('GSA_WORKER01'))
    gsheet = GoogleSheetService(
        service_account,
        '1SmgayZSkqvIiT5VRgiEfhuWSTKgT6xS4sMYLQsdLI10',
        logger=logger
    )
    df = get_sla_need_call_filtered()
    gsheet.add_dataframe(df, 1200843790, append=True)


def out_to_bi_sheet():
    service_account = get_service_account(configs.get('GSA_BI'))
    gsheet = GoogleSheetService(
        service_account,
        '1h7KeEnCznjt-ms-uO-9KQUfpqXZ7ZnfANdx4bdh6-tU',
        logger=logger
    )
    df = get_sla_need_call()
    gsheet.add_dataframe(df, 132245029, append=True)
