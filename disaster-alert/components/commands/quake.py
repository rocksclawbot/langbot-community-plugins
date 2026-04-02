from langbot_plugin.api.definition.component import Command
from langbot_plugin.api.entities.builtin.pipeline import context
from langbot_plugin.api.entities.builtin.platform import message as platform_message


class QuakeCommand(Command):

    async def initialize(self):
        pass

    async def execute(self, event_context: context.EventContext, args: list):
        result = await self.plugin.get_recent_quakes()
        await event_context.reply(
            platform_message.MessageChain([platform_message.Plain(text=result)])
        )
