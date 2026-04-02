from langbot_plugin.api.definition.component import Command
from langbot_plugin.api.entities.builtin.pipeline import context
from langbot_plugin.api.entities.builtin.platform import message as platform_message


class KickCommand(Command):

    async def initialize(self):
        pass

    async def execute(self, event_context: context.EventContext, args: list):
        event = event_context.event
        sender_id = str(event.sender_id)

        if not self.plugin.is_admin(sender_id):
            await event_context.reply(
                platform_message.MessageChain(
                    [platform_message.Plain(text="⛔ 你没有权限执行此操作。")]
                )
            )
            return

        if len(args) < 1:
            await event_context.reply(
                platform_message.MessageChain(
                    [platform_message.Plain(text="用法: !kick @用户")]
                )
            )
            return

        target = args[0].strip("@").strip()

        try:
            await event_context.call_platform_api(
                "set_group_kick",
                group_id=event.launcher_id,
                user_id=target,
                reject_add_request=False,
            )
            await event_context.reply(
                platform_message.MessageChain(
                    [platform_message.Plain(text=f"👢 已将 {target} 踢出群聊。")]
                )
            )
        except Exception as e:
            await event_context.reply(
                platform_message.MessageChain(
                    [platform_message.Plain(text=f"❌ 踢出失败: {e}")]
                )
            )
