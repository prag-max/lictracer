def initialize(self, bot: "Bot", update_queue: asyncio.Queue, secret_token: str) -> None:
        """Initialize for each request - that's the interface provided by tornado"""
        # pylint: disable=attribute-defined-outside-init
        self.bot = bot
        self.update_queue = update_queue
        self.secret_token = secret_token
        if secret_token:
            _LOGGER.debug(
                "The webhook server has a secret token, expecting it in incoming requests now"
            )