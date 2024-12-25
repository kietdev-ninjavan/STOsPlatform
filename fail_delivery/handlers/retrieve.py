import copy
import logging
import pandas as pd
from django.db.models import Q
from django.utils import timezone
from gql import gql
from simple_history.utils import bulk_create_with_history, bulk_update_with_history

from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
from opv2.base.order import GranularStatusChoices
from opv2.base.ticket import TicketTypeChoices
from opv2.services import GraphQLService, TicketService
from stos.utils import configs, chunk_list, check_record_change
from ..models import Source, FailOrders
logger = logging.getLogger(__name__)

def retrieve_rts_call():
    spreadsheet_id = "1K3Xy7SW12z7IIGi5xSWpkD4NGsLxbquZY9gLTLN6V3w"
    gsheet = GoogleSheetService(
        service_account= get_service_account(configs.get('GSA_BI')),
        spreadsheet_id= spreadsheet_id
    )
    data = gsheet.get_all_records("opv2")
    print(data)
    
    if not data:
        logger.info("No data found in the Google Sheet")
        return

    for chunk in chunk_list(data, 1000):
        tracking_ids = [row.get('tracking_id') for row in chunk]
        response_types = [row.get('response_type') for row in chunk]
        
        record = []
        
        already_exists = Source.objects.filter(
            Q(tracking_id__in=tracking_ids) &
            Q(response_type__in=response_types)
        ).values_list('tracking_id', 'response_type')
        
        for row in chunk:
            if (row.get('tracking_id'), row.get('response_type')) in already_exists:
                continue
            
            if not row.get('tracking_id'):
                logger.info("No tracking id found in row")
                continue
            
            record.append(Source(
                tracking_id = row.get('tracking_id'),
                shipper_name = row.get('shipper_name'),
                response_type = row.get('response_type'),
                customer_response = row.get('customer_response')
            ))
        
        if record: 
            success = bulk_create_with_history(record, Source, batch_size= 1000 , ignore_conflicts= True)
            logger.info(f"Successfully added {len(success)} new records to the database")
        else:
            logger.info("No new records to add to the database")
            
def retrieve_zns():
    spreadsheet_id = "1ol7zEyw611y0yBT_4tMu-kN1210Jlj4rGMsxaOTyRLo"
    gsheet = GoogleSheetService(
        service_account= get_service_account(configs.get('GSA_BI')),
        spreadsheet_id= spreadsheet_id
    )
    
    # Python Refresh Sheet / Collect from BigQuery need to add-in
    data_first_attempt = gsheet.get_all_records_as_dataframe("sysops")
    data_zns_backlog = gsheet.get_all_records_as_dataframe("zns_backlog")
    
    if not data_first_attempt.empty:
        # logger.info("No data first attempt found in the Google Sheet")
        data_first_attempt = data_first_attempt[['tracking_id', 'shipper_name', 'response_type', 'customer_response']]
        
    if data_zns_backlog.empty:
        logger.info("No data zns backlog found in the Google Sheet")
        
    data_zns_backlog = data_zns_backlog[['tracking_id', 'shipper_name', 'response_type', 'customer_response']]
    data = pd.concat([data_zns_backlog,data_first_attempt], ignore_index=True).to_dict() if not data_first_attempt.empty else data_zns_backlog.to_dict()
    for chunk in chunk_list(data, 1000):
        tracking_ids = [row.get('tracking_id') for row in chunk]
        response_types = [row.get('response_type') for row in chunk]
        
        record = []
        
        already_exists = Source.objects.filter(
            Q(tracking_id__in=tracking_ids) &
            Q(response_type__in=response_types)
        ).values_list('tracking_id', 'response_type')
        
        for row in chunk:
            if (row.get('tracking_id'), row.get('response_type')) in already_exists:
                continue
            
            if not row.get('tracking_id'):
                logger.info("No tracking id found in row")
                continue
            
            record.append(Source(
                tracking_id = row.get('tracking_id'),
                shipper_name = row.get('shipper_name'),
                response_type = row.get('response_type'),
                customer_response = row.get('customer_response')
            ))
        
        if record: 
            success = bulk_create_with_history(record, Source, batch_size= 1000 , ignore_conflicts= True)
            logger.info(f"Successfully added {len(success)} new records to the database")
        else:
            logger.info("No new records to add to the database")
            
