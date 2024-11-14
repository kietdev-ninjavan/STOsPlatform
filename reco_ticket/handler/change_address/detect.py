import json
import logging
from typing import List

from django.db.models import Q
from simple_history.utils import bulk_create_with_history

from google_wrapper.services import GenminiAIService
from stos.utils import configs, chunk_list
from ...models import TicketChangeAddress, DetectChangeAddress

logger = logging.getLogger(__name__)


def gemini_detect(data: List[dict]):
    """
    This function is used to detect the address by Gemini
    """
    gemini = GenminiAIService(configs.get('AI_API_KEY_CHANGE_ADDRESS'))

    history = [
        {
            "role": "user",
            "parts": [
                "Given a list of data containing ticket IDs and texts, extract the Vietnamese address information to three levels: province_city, district, and ward_commune. Return the results in the specified JSON format, with null values for any missing address levels. Each address component is in Vietnam.\n\nInput JSON:\n[\n{\n\"ticket_id\": \"<ticket_id_1>\",\n\"text\": \"<content>\"\n},\n...\n]\n\nFor each entry, do the following:\n\nIdentify the address components in the text:\n\nProvince/City: Highest-level location.\n\nDistrict: Mid-level location within the province/city.\n\nWard/Commune: Lowest-level location within the district.\n\nFormat the extracted data into the following JSON structure:\n\nRemove prefixes of Province/City, District, and Ward/Commune from the extracted text.\n\nCorrect abbreviations to full.\n\nPlease replace '\"' by ''' in string output\n\nCorrect spelling errors according to Vietnamese administrative units.\n\nBe careful with Province/City names that are the same as District and District names that are the same as Ward/Commune.\n\nOutput JSON:\n{\n\"data\": [\n{\n\"ticket_id\": \"<ticket_id_1>\",\n\"input\": \"<Original Text>\",\n\"address\": \"<Formatted Address>\",\n\"province_city\": \"<Province/City or null>\",\n\"district\": \"<District or null>\",\n\"ward_commune\": \"<Ward/Commune or null>\"\n},\n...\n]\n}\n\nIf a component (e.g., ward_commune) is missing from the text, set it to null.\n\nExample:\nInput:\n[\n{\n\"ticket_id\": 180656084,\n\"text\": \"33 đường 16 khu phố 6 Hiệp Bình Chánh Thủ Đức, TP. Hồ Chí Minh\"\n},\n{\n\"ticket_id\": 180658724,\n\"text\": \"đổi địa chỉ giao sang: số 81 Trần Thái Tông, phường Dịch Vọng, quận Cầu Giấy, Hà Nội\"\n},\n{\n\"ticket_id\": 180662567,\n\"text\": \"493a/99 Cách Mạng Tháng 8, Phường 13, Quận 10, TP.HCM.\"\n},\n{\n\"ticket_id\": 180666154,\n\"text\": \"Nhà BMM, Tòa nhà Vietbuild, KĐT Xa La , Yên Xá , Tân Triều, Thanh Trì , Yên Xá , Thanh Trì Hà Nội VN\"\n},\n{\n\"ticket_id\": 180674871,\n\"text\": \"số 8, ngách 51 ngõ 207 đường Trương Định, phường tương mai,quận hoàng mai\"\n},\n{\n\"ticket_id\": 180674898,\n\"text\": \"số 39 phố Vọng Hà, phường chương dương, TP hà nội \"\n},\n{\n\"ticket_id\": 180658323,\n\"text\": \"Phan Chu Trinh 153/16a, Phan Chu Trinh , Buôn Ma Thuột , Dak lak|None|Buôn Ma Thuột|Dak lak\"\n},\n{\n\"ticket_id\": 184458323,\n\"text\": \"3123 QL1 Bình Chánh, Bình Chánh, HCM\"\n},\n{\n\"ticket_id\": 182430703,\n\"text\": \"Đội 2 thôn 6 xã Ea M'nang, Huyện Cư M'gar, Tỉnh Đắk Lắk\"\n}\n]\n\nExpected Output:\n{\n\"data\": [\n{\n\"ticket_id\": 180656084,\n\"input\": \"33 đường 16 khu phố 6 Hiệp Bình Chánh Thủ Đức, TP. Hồ Chí Minh\",\n\"address\": \"33 đường 16 khu phố 6, Phường Hiệp Bình Chánh, Thành Phố Thủ Đức, Thành Phố Hồ Chí Minh\",\n\"province_city\": \"Hồ Chí Minh\",\n\"district\": \"Thủ Đức\",\n\"ward_commune\": \"Hiệp Bình Chánh\"\n},\n{\n\"ticket_id\": 180658724,\n\"input\": \"đổi địa chỉ giao sang: số 81 Trần Thái Tông, phường Dịch Vọng, quận Cầu Giấy, Hà Nội\",\n\"address\": \"số 81 Trần Thái Tông, phường Dịch Vọng, quận Cầu Giấy, Hà Nội\",\n\"province_city\": \"Hà Nội\",\n\"district\": \"Cầu Giấy\",\n\"ward_commune\": \"Dịch Vọng\"\n},\n{\n\"ticket_id\": 180662567,\n\"input\": \"493a/99 Cách Mạng Tháng 8, Phường 13, Quận 10, TP.HCM.\",\n\"address\": \"493a/99 Cách Mạng Tháng 8, Phường 13, Quận 10, Thành Phố Hồ Chí Minh\",\n\"province_city\": \"Hồ Chí Minh\",\n\"district\": \"10\",\n\"ward_commune\": \"13\"\n},\n{\n\"ticket_id\": 180666154,\n\"input\": \"Nhà BMM, Tòa nhà Vietbuild, KĐT Xa La , Yên Xá , Tân Triều, Thanh Trì , Yên Xá , Thanh Trì Hà Nội VN\",\n\"address\": \"Nhà BMM, Tòa nhà Vietbuild, KĐT Xa La , Yên Xá, Xã Tân Triều, Huyện Thanh Trì, Hà Nội\",\n\"province_city\": \"Hà Nội\",\n\"district\": \"Thanh Trì\",\n\"ward_commune\": \"Tân Triều\"\n},\n{\n\"ticket_id\": 180674871,\n\"input\": \"số 8, ngách 51 ngõ 207 đường Trương Định, phường tương mai,quận hoàng mai\",\n\"address\": \"số 8, ngách 51 ngõ 207 đường Trương Định, phường Tương Mai, quận Hoàng Mai\",\n\"province_city\": null,\n\"district\": \"Hoàng Mai\",\n\"ward_commune\": \"Tương Mai\"\n},\n{\n\"ticket_id\": 180674898,\n\"input\": \"số 39 phố Vọng Hà, phường chương dương, TP hà nội\",\n\"address\": \"số 39 phố Vọng Hà, phường Chương Dương, Thành Phố Hà Nội\",\n\"province_city\": \"Hà Nội\",\n\"district\": null,\n\"ward_commune\": \"Chương Dương\"\n},\n{\n\"ticket_id\": 180658323,\n\"input\": \"Phan Chu Trinh 153/16a, Phan Chu Trinh , Buôn Ma Thuột , Dak lak|None|Buôn Ma Thuột|Dak lak\",\n\"address\": \"Phan Chu Trinh 153/16a, Phan Chu Trinh, Buôn Ma Thuột, Đắk Lắk\",\n\"province_city\": \"Đắk Lắk\",\n\"district\": \"Buôn Ma Thuột\",\n\"ward_commune\": \"Phan Chu Trinh\"\n},\n{\n\"ticket_id\": 184458323,\n\"input\": \"3123 QL1 Bình Chánh, Bình Chánh, HCM\",\n\"address\": \"3123 QL1,Xã Bình Chánh, Huyện Bình Chánh, Thành Phố Hồ Chí Minh\",\n\"province_city\": \"Hồ Chí Minh\",\n\"district\": \"Bình Chánh\",\n\"ward_commune\": \"Bình Chánh\"\n},\n{\n\"ticket_id\": 182430703,\n\"input\": \"Đội 2 thôn 6 xã Ea M'nang, Huyện Cư M'gar, Tỉnh Đắk Lắk\",\n\"address\": \"Đội 2 thôn 6, xã Ea M\"nang, Huyện Cư M\"gar, Tỉnh Đắk Lắk\",\n\"province_city\": \"Đắk Lắk\",\n\"district\": \"Cư M'gar\",\n\"ward_commune\": \"Ea M'nang\"\n}\n]\n}\n\nYou know what I mean? If you understand, answer yes and wait for me to provide the address json list.\nI will use python to convert your results into data so absolutely must be in json format.",
            ],
        },
        {
            "role": "model",
            "parts": [
                "Yes, I understand. I'll wait for you to provide the address JSON list. I will process each address and return the results in the specified JSON format.  \n",
            ],
        },
    ]
    logger.info(f"Detecting: {data}")
    detected = gemini.chat_session(history, f'{data}')
    logger.info(f"Detected: {detected}")
    return detected


def detect_address():
    """
    This function is used to detect the address of the ticket
    """
    tickets = TicketChangeAddress.objects.filter(
        Q(detect__isnull=True) &
        Q(action__isnull=True)
    ).filter(
        Q(comments__isnull=False)
        | Q(notes__isnull=False)
        | Q(exception_reason__isnull=False),
    )

    if not tickets.exists():
        logger.info("No tickets to detect address")

    logger.info(f"Found {tickets.count()} tickets to detect address")
    data = []
    for ticket in tickets:
        content = " ".join(filter(None, [ticket.notes, ticket.comments, ticket.exception_reason]))

        data.append({
            "ticket_id": ticket.ticket_id,
            "text": f"{content}".replace('"', "'"),
        })

    detected_data = []
    for chunk in chunk_list(data, 20):
        logger.info(f"Detecting {len(chunk)} tickets")
        detected = gemini_detect(chunk)

        if not detected:
            logger.error("Error getting response from Gemini")
            continue
        logger.debug(f"Detected: {detected}")
        try:
            json_response = json.loads(detected)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing response: {e}")
            continue

        detected_data.extend(json_response.get('data', []))

    logger.info(f"Got {len(detected_data)} responses from Gemini")

    ticket_id_map = {ticket.ticket_id: ticket for ticket in tickets}

    update_data = []
    for item in detected_data:
        ticket = ticket_id_map.get(item.get('ticket_id'))
        if ticket is None:
            continue

        new_detect = DetectChangeAddress(
            ticket=ticket,
            input=item.get('input'),
            address=item.get('address'),
            province=item.get('province_city'),
            district=item.get('district'),
            ward=item.get('ward_commune'),
        )

        update_data.append(new_detect)

    try:
        logger.info("Inserting detected address records")
        success = bulk_create_with_history(update_data, DetectChangeAddress, batch_size=1000, ignore_conflicts=True)
    except Exception as e:
        logger.error(f"Error saving detected address: {e}")
        raise e

    logger.info(f"Successfully inserted {len(success)}/{len(detected_data)} detected address records.")
