from langbot_plugin.api.definition.components.command.command import Command
from langbot_plugin.api.entities.builtin.command.context import ExecuteContext, CommandReturn
from langbot_plugin.api.entities.builtin.platform.message import MessageChain, Plain


class QuakeCommand(Command):

    async def initialize(self):

        @self.subcommand(
            name="list",
            help="查看最近地震",
            usage="quake list",
        )
        async def quake_list(self, ctx: ExecuteContext):
            result = await self.plugin.get_recent_quakes()
            yield CommandReturn(text=result)
