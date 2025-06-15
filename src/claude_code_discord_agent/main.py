import os
import asyncio
import logging
import traceback
import yaml
import discord
import json
from discord.ext import commands
from dataclasses import asdict
from claude_code_sdk import (
    query,
    ClaudeCodeOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
)


class ClaudeDiscordBot(commands.Bot):
    """
    Discord bot that integrates with Claude Code SDK to respond to user mentions.
    Provides intelligent conversation capabilities through Claude AI.
    """

    def __init__(self, config):
        """
        Initialize the Discord bot with configuration settings.

        Args:
            config (dict): Configuration dictionary loaded from YAML file
        """
        # Set up Discord intents to receive message content
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=config["discord"]["prefix"], intents=intents)

        # Store configuration and set up logging
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize Claude Code SDK options with defaults
        bot_config = config.get("bot", {})
        self.claude_options = ClaudeCodeOptions(
            system_prompt=bot_config.get(
                "system_prompt", "You are a helpful Discord bot."
            ),
            allowed_tools=bot_config.get("allowed_tools", []),
            max_turns=bot_config.get("max_turns", None),
        )

    async def setup_hook(self):
        """Called when the bot is ready and logged in."""
        self.logger.info(f"Bot logged in as {self.user}")

    async def on_message(self, message):
        """
        Handle incoming messages from Discord.

        Args:
            message: Discord message object
        """
        # Ignore messages from the bot itself to prevent loops
        if message.author == self.user:
            return

        # Handle mentions of the bot
        if self.user in message.mentions:
            await self.handle_mention(message)

        # Process other bot commands
        await self.process_commands(message)

    async def handle_mention(self, message):
        """
        Handle messages that mention the bot and generate responses using Claude.

        Args:
            message: Discord message object that mentions the bot
        """
        try:
            # Extract user content by removing the bot mention
            user_content = message.content.replace(f"<@{self.user.id}>", "").strip()

            # Check if the message is empty after removing the mention
            if not user_content:
                await message.reply(self.config["messages"]["empty_message"])
                return

            # Show typing indicator while processing the request
            async with message.channel.typing():
                responses = []
                self.logger.info(f"User message: {user_content}")

                # Query Claude Code SDK for response
                async for response in query(
                    prompt=user_content, options=self.claude_options
                ):
                    self.logger.info(f"Received response type: {type(response)}")
                    self.logger.info(
                        f"Received response: {json.dumps(asdict(response), indent=2)}"
                    )
                    if isinstance(response, AssistantMessage):
                        for block in response.content:
                            if isinstance(block, TextBlock):
                                responses.append(block.text)
                            elif isinstance(block, ToolUseBlock):
                                if block.name == "Bash":
                                    responses.append(f"**{block.name}**")
                                    responses.append(
                                        f"```\n$ {block.input['command']} # {block.input.get('description')}\n```"
                                    )
                                else:
                                    responses.append(f"**{block.name}**")
                                    responses.append(
                                        f"```\n{json.dumps(block.input, indent=2, ensure_ascii=False)}\n```"
                                    )

                # Log the response and send it to Discord
                self.logger.info(
                    f"Claude response: {json.dumps(responses, indent=2, ensure_ascii=False)}"
                )
                responses = "\n".join(responses)
                if responses and len(responses) > 4000:
                    await message.reply(
                        self.config["messages"]["long_response_warning"]
                    )
                elif len(responses) == 0:
                    # If no responses were generated, send an empty response message
                    await message.reply(self.config["messages"]["empty_response"])
                else:
                    await message.reply("\n".join(responses))

        except* Exception as e_group:
            for e in e_group.exceptions:
                # Log error and send user-friendly error message
                tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
                self.logger.error(f"Unhandled exception:\n{tb}")
                await message.reply(self.config["messages"]["general_error"])


def setup_logging(config):
    """
    Configure logging system based on configuration settings.

    Args:
        config (dict): Configuration dictionary containing logging settings
    """
    logging.basicConfig(
        level=getattr(logging, config["logging"]["level"]),
        format=config["logging"]["format"],
    )


def load_config():
    """
    Load configuration from YAML file.

    Returns:
        dict: Configuration dictionary or None if loading fails
    """
    # Construct path to config.yaml in the project root
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.yaml"
    )
    logger = logging.getLogger(__name__)

    try:
        # Load YAML configuration file
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        # Log error if config file is not found
        logger.error(f"Configuration file not found: {config_path}")
        logger.error("Please create config.yaml based on config.example.yaml")
        return None
    except yaml.YAMLError as e:
        # Log error if YAML parsing fails
        logger.error(f"Failed to load YAML configuration file: {e}")
        return None


def main():
    """
    Main entry point for the Discord bot application.
    Loads configuration, sets up logging, and starts the bot.
    """
    # Load configuration from YAML file
    config = load_config()
    if not config:
        logger.error("Configuration is empty or could not be loaded. Exiting.")
        return

    # Set ANTHROPIC_API_KEY environment variable if configured
    if config.get("claude_code") is not None and config.get("claude_code").get(
        "api_key"
    ):
        os.environ["ANTHROPIC_API_KEY"] = config["claude_code"]["api_key"]

    # Initialize logging system
    setup_logging(config)
    logger = logging.getLogger(__name__)

    # Validate Discord bot token
    token = config["discord"]["bot_token"]
    if not token or token == "your_discord_bot_token_here":
        logger.error("Discord bot token is not configured in config.yaml")
        return

    # Create and start the bot
    bot = ClaudeDiscordBot(config)

    try:
        # Run the bot until interrupted
        asyncio.run(bot.start(token))
    except KeyboardInterrupt:
        # Handle graceful shutdown
        logger.info("Stopping bot...")
    except Exception as e:
        # Log any unexpected errors
        logger.error(f"Error occurred while running bot: {e}")


if __name__ == "__main__":
    main()
