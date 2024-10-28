import json
import logging
from typing import Optional, Union
from uuid import uuid4

from django.utils import timezone
from google.api_core.exceptions import AlreadyExists, GoogleAPIError
from google.auth import jwt
from google.cloud import pubsub_v1
from google.pubsub_v1.types import pubsub

from ..models import ServiceAccount


class GooglePubSubService:
    """
    A service class to interact with Google Cloud Pub/Sub, allowing
    for topic creation, subscription management, and message publishing.

    Attributes:
        __service_account (ServiceAccount): The service account used for authentication.
        __logger (logging.Logger): Logger for recording Pub/Sub operations.
    """

    def __init__(self, service_account: ServiceAccount, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the GooglePubSubService using a GoogleServiceAccount model instance.

        Args:
            service_account (ServiceAccount): The service account containing project credentials.
            logger (logging.Logger, optional): Logger instance for logging messages. Defaults to the module logger.
        """
        self.__logger = logger
        self.__service_account = service_account
        self.__project_id = self.__service_account.project_id

        # Initialize publisher and subscriber clients
        self.__publisher = self._create_pubsub_client('Publisher')
        self.__subscriber = self._create_pubsub_client('Subscriber')

    def _create_pubsub_client(self, audience: str) -> Union[pubsub_v1.PublisherClient, pubsub_v1.SubscriberClient]:
        """
        Create a Pub/Sub client (Publisher or Subscriber) with appropriate credentials.

        Args:
            audience (str): Determines whether to create a Publisher or Subscriber client.

        Returns:
            Union[pubsub_v1.PublisherClient, pubsub_v1.SubscriberClient]: A Pub/Sub client for publishing or subscribing.
        """
        credentials = jwt.Credentials.from_service_account_info(
            self.__service_account.to_dict(),
            audience=f"https://pubsub.googleapis.com/google.pubsub.v1.{audience}"
        )
        if audience == 'Publisher':
            return pubsub_v1.PublisherClient(credentials=credentials)
        return pubsub_v1.SubscriberClient(credentials=credentials)

    def create_topic(self, topic_name: str) -> pubsub.Topic:
        """
        Create a Pub/Sub topic by the given name or return an existing one.

        Args:
            topic_name (str): The name of the Pub/Sub topic to create.

        Returns:
            pubsub.Topic: The created or existing Pub/Sub topic.

        Raises:
            AlreadyExists: If the topic already exists.
            GoogleAPIError: If there's a failure in creating the topic.
        """
        topic_path = self.__publisher.topic_path(self.__project_id, topic_name)
        try:
            topic = self.__publisher.create_topic(request={"name": topic_path})
            self.__logger.info(f"Topic created: {topic.name}")
            return topic
        except AlreadyExists:
            self.__logger.warning(f"Topic '{topic_name}' already exists.")
            raise
        except GoogleAPIError as e:
            self.__logger.error(f"Failed to create topic '{topic_name}': {e}")
            raise
        except Exception as e:
            self.__logger.error(f"An unexpected error occurred: {e}")
            raise

    def create_subscription(self, subscription_name: str, topic_name: str, push_endpoint: Optional[str] = None) -> pubsub.Subscription:
        """
        Create a Pub/Sub subscription for the given topic.

        Args:
            subscription_name (str): The name of the subscription to create.
            topic_name (str): The topic to subscribe to.
            push_endpoint (Optional[str], optional): The push endpoint for the subscription. Defaults to None.

        Returns:
            pubsub.Subscription: The created Pub/Sub subscription.

        Raises:
            AlreadyExists: If the subscription already exists.
            GoogleAPIError: If there's a failure in creating the subscription.
        """
        subscription_path = self.__subscriber.subscription_path(self.__project_id, subscription_name)
        topic_path = self.__publisher.topic_path(self.__project_id, topic_name)
        try:
            subscription = self.__subscriber.create_subscription(
                request={
                    "name": subscription_path,
                    "topic": topic_path,
                    "push_config": {"push_endpoint": push_endpoint} if push_endpoint else {}
                }
            )
            self.__logger.info(f"Subscription created: {subscription.name}")
            return subscription
        except AlreadyExists:
            self.__logger.warning(f"Subscription '{subscription_name}' already exists.")
            raise
        except GoogleAPIError as e:
            self.__logger.error(f"Failed to create subscription '{subscription_name}': {e}")
            raise
        except Exception as e:
            self.__logger.error(f"An unexpected error occurred: {e}")
            raise

    def publish_message(self, topic_name: str, message: dict) -> str:
        """
        Publish a message to a specified Pub/Sub topic.

        Args:
            topic_name (str): The name of the Pub/Sub topic to publish the message to.
            message (dict): The message payload to publish.

        Returns:
            str: The message ID of the published message.

        Raises:
            GoogleAPIError: If there's a failure in publishing the message.
            Exception: For any unexpected error during publishing.
        """
        topic_path = self.__publisher.topic_path(self.__project_id, topic_name)
        try:
            publish_data = {
                "uuid": str(uuid4()),
                "datetime": timezone.now().isoformat(),
                "topic": topic_name,
                "message": message
            }
            data_to_publish = json.dumps(publish_data).encode("utf-8")

            future = self.__publisher.publish(topic_path, data=data_to_publish)
            message_id = future.result()

            self.__logger.info(f"Published message '{message_id}' to topic '{topic_name}'")
            return message_id
        except GoogleAPIError as e:
            self.__logger.error(f"Failed to publish message to topic '{topic_name}': {e}")
            raise
        except Exception as e:
            self.__logger.error(f"An unexpected error occurred: {e}")
            raise

    def subscribe(self, subscription_name: str, callback):
        """
        Subscribes to a Pub/Sub subscription and processes messages with the provided callback.

        Args:
            subscription_name (str): The name of the Pub/Sub subscription to subscribe to.
            callback: The callback function to process messages.

        Raises:
            GoogleAPIError: If there's a failure in subscribing to the topic.
            Exception: For any unexpected error during subscription.
        """
        subscription_path = self.__subscriber.subscription_path(self.__project_id, subscription_name)
        try:
            self.__subscriber.subscribe(subscription_path, callback=callback)
            self.__logger.info(f"Subscribed to '{subscription_name}'")
        except GoogleAPIError as e:
            self.__logger.error(f"Failed to subscribe to '{subscription_name}': {e}")
            raise
        except Exception as e:
            self.__logger.error(f"An unexpected error occurred: {e}")
            raise
